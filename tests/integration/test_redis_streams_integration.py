import asyncio
import os
import pytest
import pytest_asyncio

from datetime import datetime

from src.utils.messaging.redis_bus import RedisEventBus


pytestmark = pytest.mark.asyncio


async def _ensure_redis_available() -> bool:
    try:
        # Utiliser redis-py asyncio via le bus
        bus = RedisEventBus()
        await bus.connect()
        # ping indirect: publier sur un stream éphémère
        await bus.publish("test.stream.availability", {"ts": datetime.utcnow().isoformat()})
        await bus.close()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture
async def redis_available():
    if not await _ensure_redis_available():
        pytest.skip("Redis non disponible à REDIS_URL; skipper les tests d'intégration Streams")


async def _collect_messages(stream: str, group: str, consumer: str, expected: int, timeout_s: float = 5.0):
    collected = []
    bus = RedisEventBus()
    await bus.connect()

    async def handler(payload):
        collected.append(payload)

    task = asyncio.create_task(bus.consume(stream, group, consumer, handler, block_ms=200, batch_size=16))
    try:
        # Attendre jusqu'à réception des messages ou timeout
        start = asyncio.get_event_loop().time()
        while len(collected) < expected and (asyncio.get_event_loop().time() - start) < timeout_s:
            await asyncio.sleep(0.05)
    finally:
        bus.stop()
        await asyncio.sleep(0)  # yield
        task.cancel()
        try:
            await task
        except Exception:
            pass
        await bus.close()
    return collected


async def _publish_messages(stream: str, num: int = 1):
    bus = RedisEventBus()
    await bus.connect()
    for i in range(num):
        await bus.publish(stream, {"i": i, "timestamp": datetime.utcnow().isoformat()})
    await bus.close()


async def test_roundtrip_market_data_ticks(redis_available):
    stream = "market_data.ticks.itest"
    group = "itest-consumers"
    consumer = "worker-1"

    collector_task = asyncio.create_task(_collect_messages(stream, group, consumer, expected=2))
    await asyncio.sleep(0.1)
    await _publish_messages(stream, num=2)
    messages = await collector_task

    assert len(messages) >= 2
    assert all("timestamp" in m for m in messages)


async def test_roundtrip_indicators_computed(redis_available):
    stream = "indicators.computed.itest"
    group = "itest-consumers"
    consumer = "worker-1"

    collector_task = asyncio.create_task(_collect_messages(stream, group, consumer, expected=1))
    await asyncio.sleep(0.1)

    bus = RedisEventBus()
    await bus.connect()
    await bus.publish(stream, {"symbol": "BTC/USDT", "indicators": {"SMA_20": 1.0}, "timestamp": datetime.utcnow().isoformat()})
    await bus.close()

    messages = await collector_task
    assert messages and messages[0].get("symbol") == "BTC/USDT"
