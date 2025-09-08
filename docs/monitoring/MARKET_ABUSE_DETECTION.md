## Détection d'abus de marché

Composants:
- `src/monitoring/market_abuse/types.py`: types forts (événements, alertes)
- `src/monitoring/market_abuse/base.py`: base commune
- `src/monitoring/market_abuse/pump_dump_detector.py`
- `src/monitoring/market_abuse/spoofing_layering_detector.py`
- `src/monitoring/market_abuse/wash_trading_detector.py`
- `src/monitoring/market_abuse/quote_stuffing_detector.py`
- `src/monitoring/market_abuse/stream_monitor.py`

Utilisation rapide (offline CSV):
```bash
python scripts/tools/market_abuse_cli.py --csv path.csv --symbol BTC/USDT
```

Intégration en code:
```python
from src.monitoring.market_abuse import MarketAbuseStreamMonitor, TradeEvent
monitor = MarketAbuseStreamMonitor(symbol="BTC/USDT")
# feed trades/orderbooks
```

Notes:
- Heuristiques simples, seuils à calibrer par marché.
- Pour wash trading, `trader_id` doit être fourni pour être utile.

