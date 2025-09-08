from datetime import datetime, timedelta

from src.monitoring.market_abuse.stream_monitor import MarketAbuseStreamMonitor
from src.monitoring.market_abuse.types import TradeEvent


def test_pump_and_dump_detector_triggers_on_strong_pump():
    now = datetime.utcnow()
    monitor = MarketAbuseStreamMonitor(symbol="BTC/USDT", lookback_minutes=10)

    # Génère une série stable puis un pump de 5%
    prices = [100.0] * 20 + [105.0] * 10
    quantities = [1.0] * 20 + [3.0] * 10

    alerts = []
    for i, (p, q) in enumerate(zip(prices, quantities)):
        t = TradeEvent(
            timestamp=now + timedelta(seconds=i),
            symbol="BTC/USDT",
            price=p,
            quantity=q,
            side="buy",
        )
        alerts.extend(monitor.on_trade(t))

    assert any("PUMP suspect" in a.message for a in alerts)


def test_pump_and_dump_detector_triggers_on_strong_dump():
    now = datetime.utcnow()
    monitor = MarketAbuseStreamMonitor(symbol="ETH/USDT", lookback_minutes=10)

    prices = [200.0] * 20 + [190.0] * 10
    quantities = [1.0] * 20 + [3.0] * 10

    alerts = []
    for i, (p, q) in enumerate(zip(prices, quantities)):
        t = TradeEvent(
            timestamp=now + timedelta(seconds=i),
            symbol="ETH/USDT",
            price=p,
            quantity=q,
            side="sell",
        )
        alerts.extend(monitor.on_trade(t))

    assert any("DUMP suspect" in a.message for a in alerts)

