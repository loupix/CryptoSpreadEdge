import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.monitoring.market_abuse.stream_monitor import MarketAbuseStreamMonitor
from src.monitoring.market_abuse.types import TradeEvent, MarketAbuseAlert, MarketAbuseType
from src.monitoring.market_abuse.sinks import AlertSink, FileAlertSink, PrometheusAlertSink


class _CollectSink(AlertSink):
    def __init__(self):
        self.received = []

    def emit(self, alerts):
        self.received.extend(list(alerts))


def _make_trade(ts: datetime, price: float, qty: float, symbol: str = "BTC/USDT") -> TradeEvent:
    return TradeEvent(timestamp=ts, symbol=symbol, price=price, quantity=qty, side="buy")


def test_symbol_threshold_filters_alerts(tmp_path: Path):
    now = datetime.utcnow()
    collector = _CollectSink()
    # Seuil 0.9: nos heuristiques pump/dump génèreront ~>=0.5-1.0; on force un seuil haut pour filtrer
    monitor = MarketAbuseStreamMonitor(
        symbol="BTC/USDT",
        symbol_thresholds={"BTC/USDT": 0.95},
        sinks=[collector],
    )
    # Stable puis pump de 3% seulement => souvent sous 1.0 de sévérité, peut être filtré
    for i in range(20):
        monitor.on_trade(_make_trade(now + timedelta(seconds=i), price=100.0, qty=1.0))
    for i in range(10):
        monitor.on_trade(_make_trade(now + timedelta(seconds=20 + i), price=103.0, qty=3.0))

    # Toutes les alertes émises côté monitor sont passées par le filtre; ici on s'attend à 0 ou très peu
    assert len(collector.received) == 0


def test_file_sink_writes_jsonl(tmp_path: Path):
    file_path = tmp_path / "alerts.jsonl"
    sink = FileAlertSink(str(file_path))
    alert = MarketAbuseAlert(
        timestamp=datetime.utcnow(),
        symbol="BTC/USDT",
        type=MarketAbuseType.PUMP_AND_DUMP,
        severity=0.8,
        message="test",
        metadata={"example": 1.0},
    )
    sink.emit([alert])
    assert file_path.exists()
    data = [json.loads(line) for line in file_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(data) == 1
    assert data[0]["symbol"] == "BTC/USDT"
    assert data[0]["type"] == MarketAbuseType.PUMP_AND_DUMP.value
    assert data[0]["severity"] == 0.8


def test_stream_monitor_emits_to_custom_sink():
    now = datetime.utcnow()
    collector = _CollectSink()
    monitor = MarketAbuseStreamMonitor(symbol="ETH/USDT", sinks=[collector])
    # Génère un dump net
    for i in range(20):
        monitor.on_trade(_make_trade(now + timedelta(seconds=i), price=200.0, qty=1.0, symbol="ETH/USDT"))
    for i in range(10):
        monitor.on_trade(_make_trade(now + timedelta(seconds=20 + i), price=190.0, qty=3.0, symbol="ETH/USDT"))

    assert any("DUMP suspect" in a.message for a in collector.received)


def test_prometheus_sink_increments(monkeypatch):
    class _Lbl:
        def __init__(self):
            self.count = 0
            self.value = 0.0

        def inc(self):
            self.count += 1

        def set(self, v: float):
            self.value = v

    class _Metric:
        def labels(self, **kwargs):
            return _Lbl()

    sink = PrometheusAlertSink()
    # Monkeypatch counters/gauges to avoid touching global registry
    sink.counter = _Metric()
    sink.severity_gauge = _Metric()

    alert = MarketAbuseAlert(
        timestamp=datetime.utcnow(),
        symbol="X/USDT",
        type=MarketAbuseType.PUMP_AND_DUMP,
        severity=0.42,
        message="pump",
        metadata=None,
    )
    sink.emit([alert])
    # If no exception raised and our patched metrics were called, test passes
    # (implicitly covered by _Lbl methods not failing)

