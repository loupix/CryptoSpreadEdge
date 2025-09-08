from datetime import datetime, timedelta

from src.monitoring.market_abuse.stream_monitor import MarketAbuseStreamMonitor
from src.monitoring.market_abuse.types import TradeEvent


def test_opportunities_callback_receives_items():
    now = datetime.utcnow()
    received = []

    def on_opps(opps):
        received.extend(opps)

    monitor = MarketAbuseStreamMonitor(symbol="BTC/USDT", on_opportunities=on_opps)

    # Génère un pump
    for i in range(20):
        monitor.on_trade(TradeEvent(timestamp=now + timedelta(seconds=i), symbol="BTC/USDT", price=100.0, quantity=1.0, side="buy"))
    for i in range(10):
        monitor.on_trade(TradeEvent(timestamp=now + timedelta(seconds=20+i), symbol="BTC/USDT", price=105.0, quantity=3.0, side="buy"))

    assert len(received) >= 1
    assert any("volatility_breakout" in opp.kind for opp in received)

