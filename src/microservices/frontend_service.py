"""
Service frontend léger: agrège des événements Redis Streams et les diffuse via WebSocket
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.utils.messaging.redis_bus import RedisEventBus


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        text = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(text)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()
app = FastAPI(title="CryptoSpreadEdge Frontend Events", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index() -> HTMLResponse:
    html = (
        """
<!doctype html>
<html>
  <head>
    <meta charset='utf-8' />
    <title>CryptoSpreadEdge - Live Events</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 20px; }
      #status { margin-bottom: 10px; }
      .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
      .card { border: 1px solid #ddd; border-radius: 8px; padding: 12px; }
      pre { background: #111; color: #0f0; padding: 10px; height: 200px; overflow: auto; }
      .controls { margin: 10px 0; }
      label { margin-right: 8px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border-bottom: 1px solid #eee; padding: 6px 8px; font-size: 12px; }
      .pill { display: inline-block; padding: 2px 6px; border-radius: 6px; font-size: 11px; }
      .pill.high { background: #fee2e2; color: #991b1b; }
      .pill.medium { background: #fef3c7; color: #92400e; }
      .pill.low { background: #dcfce7; color: #166534; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  </head>
  <body>
    <h2>CryptoSpreadEdge - Live Events</h2>
    <div id="status">Connecting...</div>
    <div class="controls">
      <label><input type="checkbox" id="ticks" checked /> market_data.ticks</label>
      <label><input type="checkbox" id="indicators" checked /> indicators.computed</label>
      <label><input type="checkbox" id="signals" checked /> signals.generated</label>
      <label><input type="checkbox" id="alerts" checked /> alerts.general</label>
      <label><input type="checkbox" id="abuse" checked /> alerts.market_abuse</label>
      <label><input type="checkbox" id="opps" checked /> arbitrage.opportunities</label>
      <label><input type="checkbox" id="orders" checked /> orders.*</label>
      <label><input type="checkbox" id="positions" checked /> positions.*</label>
    </div>
    <div class="grid">
      <div class="card">
        <h3>Ticks (Close)</h3>
        <canvas id="ticksChart" height="120"></canvas>
      </div>
      <div class="card">
        <h3>Alertes</h3>
        <ul id="alertsList" style="list-style:none; padding-left:0; margin:0; max-height:220px; overflow:auto;"></ul>
      </div>
      <div class="card" style="grid-column: 1 / span 2;">
        <h3>Indicateurs récents</h3>
        <table>
          <thead>
            <tr><th>Symbole</th><th>Indicateur</th><th>Value</th><th>Ts</th></tr>
          </thead>
          <tbody id="indicatorsTable"></tbody>
        </table>
      </div>
      <div class="card" style="grid-column: 1 / span 2;">
        <h3>Opportunités d'arbitrage</h3>
        <table>
          <thead>
            <tr><th>Symbole</th><th>Acheter</th><th>Vendre</th><th>Spread %</th><th>Vol</th><th>Conf.</th><th>Ts</th></tr>
          </thead>
          <tbody id="oppsTable"></tbody>
        </table>
      </div>
      <div class="card">
        <h3>Ordres (live)</h3>
        <table>
          <thead>
            <tr><th>ID</th><th>Symbole</th><th>Side</th><th>Type</th><th>Qty</th><th>Prix</th><th>Statut</th><th>Ts</th></tr>
          </thead>
          <tbody id="ordersTable"></tbody>
        </table>
      </div>
      <div class="card">
        <h3>Positions (live)</h3>
        <table>
          <thead>
            <tr><th>Symbole</th><th>Type</th><th>Taille</th><th>Entrée</th><th>Prix</th><th>PNL (u)</th><th>Ts</th></tr>
          </thead>
          <tbody id="positionsTable"></tbody>
        </table>
      </div>
      <div class="card" style="grid-column: 1 / span 2;">
        <h3>Journal brut</h3>
        <pre id="log"></pre>
      </div>
    </div>
    <div id="toasts" style="position: fixed; right: 12px; bottom: 12px; display: flex; flex-direction: column; gap: 8px;"></div>
    <script>
      const ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');
      const logEl = document.getElementById('log');
      const statusEl = document.getElementById('status');
      const filters = {
        'market_data.ticks': document.getElementById('ticks'),
        'indicators.computed': document.getElementById('indicators'),
        'signals.generated': document.getElementById('signals'),
        'alerts.general': document.getElementById('alerts'),
        'alerts.market_abuse': document.getElementById('abuse'),
        'arbitrage.opportunities': document.getElementById('opps'),
        'orders.submitted': document.getElementById('orders'),
        'orders.executed': document.getElementById('orders'),
        'positions.opened': document.getElementById('positions'),
        'positions.closed': document.getElementById('positions'),
      };
      const ticksCtx = document.getElementById('ticksChart').getContext('2d');
      const ticksData = { labels: [], datasets: [{ label: 'Close', data: [], borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.2)', pointRadius: 0 }] };
      const ticksChart = new Chart(ticksCtx, { type: 'line', data: ticksData, options: { animation:false, responsive:true, scales:{ x:{display:false}, y:{ beginAtZero:false } } } });
      const alertsList = document.getElementById('alertsList');
      const indicatorsTable = document.getElementById('indicatorsTable');
      const oppsTable = document.getElementById('oppsTable');
      const toasts = document.getElementById('toasts');
      const ordersTable = document.getElementById('ordersTable');
      const positionsTable = document.getElementById('positionsTable');

      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }

      function notify(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
          try { new Notification(title, { body }); } catch {}
        } else {
          const el = document.createElement('div');
          el.style.cssText = 'background:#111;color:#fff;padding:10px 12px;border-radius:8px;min-width:220px;box-shadow:0 2px 8px rgba(0,0,0,0.2)';
          el.textContent = `${title} — ${body}`;
          toasts.prepend(el);
          setTimeout(() => { if (toasts.contains(el)) toasts.removeChild(el); }, 5000);
        }
      }
      ws.onopen = () => { statusEl.textContent = 'Connected'; };
      ws.onclose = () => { statusEl.textContent = 'Disconnected'; };
      ws.onerror = () => { statusEl.textContent = 'Error'; };
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg && msg.stream && filters[msg.stream] && !filters[msg.stream].checked) return;
          logEl.textContent += evt.data + '\n';
          logEl.scrollTop = logEl.scrollHeight;
          if (msg.stream === 'market_data.ticks' && msg.data && msg.data.length) {
            const last = msg.data[msg.data.length - 1];
            const ts = last.timestamp || new Date().toISOString();
            const close = Number(last.close || last.price || 0);
            if (!isNaN(close)) {
              ticksData.labels.push(ts);
              ticksData.datasets[0].data.push(close);
              if (ticksData.labels.length > 200) { ticksData.labels.shift(); ticksData.datasets[0].data.shift(); }
              ticksChart.update();
            }
          }
          if (msg.stream === 'alerts.general' || msg.stream === 'alerts.market_abuse') {
            const li = document.createElement('li');
            const sev = (msg.severity || 'medium').toString().toLowerCase();
            li.innerHTML = `<span class="pill ${sev}">${sev}</span> <strong>${msg.symbol || msg.name || ''}</strong> - ${msg.type || ''} <small>${msg.timestamp || ''}</small>`;
            alertsList.prepend(li);
            while (alertsList.children.length > 50) alertsList.removeChild(alertsList.lastChild);
            if (sev === 'high' || sev === 'critical') {
              notify('Alerte marché', `${msg.symbol || ''} ${msg.type || ''} sev=${sev}`);
            }
          }
          if (msg.stream === 'indicators.computed' && msg.indicators) {
            const sym = msg.symbol || '';
            const entries = Object.entries(msg.indicators).slice(0, 5);
            entries.forEach(([name, vals]) => {
              if (Array.isArray(vals) && vals.length) {
                const last = vals[vals.length - 1];
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${sym}</td><td>${name}</td><td>${(last.value ?? '').toString().slice(0,10)}</td><td><small>${last.timestamp || ''}</small></td>`;
                indicatorsTable.prepend(tr);
                while (indicatorsTable.children.length > 100) indicatorsTable.removeChild(indicatorsTable.lastChild);
              }
            });
          }
          if (msg.stream === 'arbitrage.opportunities') {
            const tr = document.createElement('tr');
            const spreadPct = (Number(msg.spread_pct || 0) * 100).toFixed(2);
            tr.innerHTML = `<td>${msg.symbol || ''}</td><td>${msg.buy_exchange || ''}</td><td>${msg.sell_exchange || ''}</td><td>${spreadPct}%</td><td>${msg.volume || msg.volume_available || ''}</td><td>${(msg.confidence ?? '').toString().slice(0,4)}</td><td><small>${msg.timestamp || ''}</small></td>`;
            oppsTable.prepend(tr);
            while (oppsTable.children.length > 100) oppsTable.removeChild(oppsTable.lastChild);
            if (Number(msg.confidence || 0) >= 0.8) {
              notify('Arbitrage', `${msg.symbol} ${msg.buy_exchange}→${msg.sell_exchange} spread=${spreadPct}%`);
            }
          }
          if (msg.stream === 'orders.executed') {
            notify('Ordre exécuté', `${msg.symbol || msg.order_id || ''} qty=${msg.quantity || ''} price=${msg.price || ''}`);
          }
          if (msg.stream === 'positions.opened' || msg.stream === 'positions.closed') {
            notify('Position', `${msg.stream.split('.')[1]} ${msg.symbol || ''} size=${msg.size || ''}`);
          }
          if (msg.stream && msg.stream.startsWith('orders.')) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${msg.order_id || ''}</td><td>${msg.symbol || ''}</td><td>${msg.side || ''}</td><td>${msg.type || ''}</td><td>${msg.quantity || ''}</td><td>${msg.price || ''}</td><td>${msg.status || msg.stream.split('.')[1] || ''}</td><td><small>${msg.timestamp || ''}</small></td>`;
            ordersTable.prepend(tr);
            while (ordersTable.children.length > 100) ordersTable.removeChild(ordersTable.lastChild);
          }
          if (msg.stream && msg.stream.startsWith('positions.')) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${msg.symbol || ''}</td><td>${msg.type || ''}</td><td>${msg.size || ''}</td><td>${msg.entry_price || ''}</td><td>${msg.current_price || ''}</td><td>${msg.unrealized_pnl || ''}</td><td><small>${msg.current_time || msg.entry_time || msg.timestamp || ''}</small></td>`;
            positionsTable.prepend(tr);
            while (positionsTable.children.length > 100) positionsTable.removeChild(positionsTable.lastChild);
          }
        } catch (e) {
          logEl.textContent += evt.data + '\n';
        }
      };
    </script>
  </body>
</html>
        """
    )
    return HTMLResponse(html)


async def stream_to_clients(stream_name: str, group: str, consumer: str) -> None:
    bus = RedisEventBus()
    await bus.connect()

    async def handler(payload: Dict[str, Any]) -> None:
        enriched = {"stream": stream_name, **payload}
        await manager.broadcast(enriched)

    try:
        await bus.consume(
            stream_name=stream_name,
            group_name=group,
            consumer_name=consumer,
            handler=handler,
            block_ms=1000,
            batch_size=64,
        )
    finally:
        bus.stop()
        await bus.close()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    # Démarrer des tâches d'abonnement aux streams
    group = "frontend-clients"
    tasks = [
        asyncio.create_task(stream_to_clients("market_data.ticks", group, "ws1")),
        asyncio.create_task(stream_to_clients("indicators.computed", group, "ws2")),
        asyncio.create_task(stream_to_clients("signals.generated", group, "ws3")),
        asyncio.create_task(stream_to_clients("alerts.general", group, "ws4")),
        asyncio.create_task(stream_to_clients("alerts.market_abuse", group, "ws5")),
        asyncio.create_task(stream_to_clients("arbitrage.opportunities", group, "ws6")),
    ]
    try:
        while True:
            # garder la connexion ouverte; on ignore les messages côté client
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.sleep(0)
        manager.disconnect(websocket)

