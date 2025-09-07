import pytest
from datetime import datetime

from src.arbitrage.price_monitor import PriceMonitor, PriceData


@pytest.mark.asyncio
async def test_price_monitor_cache_update():
    pm = PriceMonitor()
    pm.is_running = True
    pd = PriceData(
        symbol="BTC",
        platform="test",
        price=100.0,
        bid=99.5,
        ask=100.5,
        volume=10.0,
        timestamp=datetime.utcnow(),
        confidence=0.9,
        source="test"
    )
    await pm._update_price_cache(pd)
    assert "BTC" in pm.price_cache
    assert "test" in pm.price_cache["BTC"]

    summary = pm.get_price_summary("BTC")
    assert summary is not None
    assert summary["min_price"] <= summary["max_price"]
