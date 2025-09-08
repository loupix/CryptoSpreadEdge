import asyncio
import pytest

from datetime import datetime, timedelta

from src.prediction.signal_generator import SignalGenerator, TradingSignal, SignalType
from src.arbitrage.arbitrage_engine import ArbitrageOpportunity, ArbitrageExecution
from src.position.position_manager import PositionManager
from src.backtesting.backtesting_engine import Position as BTPosition, PositionType as BTPositionType
from src.core.order_management.order_manager import OrderManager, OrderManagerConfig


class FakeBus:
    def __init__(self):
        self.published = []

    async def connect(self):  # signature compatible
        return None

    async def close(self):
        return None

    def stop(self):
        return None

    async def publish(self, stream_name, payload):
        self.published.append((stream_name, payload))


@pytest.mark.asyncio
async def test_signal_generator_publishes_signals():
    gen = SignalGenerator("TestSignalGen")
    gen._event_bus = FakeBus()

    signal = TradingSignal(
        signal_type=SignalType.BUY,
        strength=0.9,
        confidence=0.8,
        timestamp=datetime.utcnow(),
        symbol="BTC/USDT",
        price=50000.0,
        stop_loss=48000.0,
        take_profit=56000.0,
    )

    # Appel direct de la méthode async
    await gen._publish_signals_async("BTC/USDT", [signal])

    assert gen._event_bus.published, "Aucune publication détectée"
    stream, payload = gen._event_bus.published[-1]
    assert stream == "signals.generated"
    assert payload["symbol"] == "BTC/USDT"
    assert payload["signals"][0]["type"] == "buy"


@pytest.mark.asyncio
async def test_arbitrage_engine_publishes_opps_and_exec():
    from src.arbitrage.arbitrage_engine import ArbitrageEngine

    engine = ArbitrageEngine()
    engine._event_bus = FakeBus()

    opp = ArbitrageOpportunity(
        symbol="BTC",
        buy_exchange="binance",
        sell_exchange="coinbase",
        buy_price=50000.0,
        sell_price=50100.0,
        spread=100.0,
        spread_percentage=0.002,
        volume_available=1.0,
        max_profit=100.0,
        confidence=0.9,
        timestamp=datetime.utcnow(),
        execution_time_estimate=0.2,
        risk_score=0.3,
    )

    await engine._publish_opportunities([opp])
    assert engine._event_bus.published, "Aucune publication d'opportunité"
    stream, payload = engine._event_bus.published[-1]
    assert stream == "arbitrage.opportunities"
    assert payload["symbol"] == "BTC"

    exe = ArbitrageExecution(
        opportunity=opp,
        buy_order=None,
        sell_order=None,
        status="completed",
        actual_profit=95.0,
        execution_time=0.25,
        fees_paid=5.0,
        net_profit=90.0,
        timestamp=datetime.utcnow(),
    )

    await engine._publish_execution(exe)
    stream, payload = engine._event_bus.published[-1]
    assert stream == "arbitrage.executions"
    assert payload["status"] == "completed"


@pytest.mark.asyncio
async def test_position_manager_publishes_events():
    pm = PositionManager("TestPM")
    pm._event_bus = FakeBus()

    position = BTPosition(
        symbol="ETH/USDT",
        position_type=BTPositionType.LONG,
        size=1.5,
        entry_price=2000.0,
        entry_time=datetime.utcnow(),
        current_price=2000.0,
        current_time=datetime.utcnow(),
        stop_loss=1900.0,
        take_profit=2300.0,
    )

    await pm._publish_position_event("positions.opened", position)
    assert pm._event_bus.published, "Aucune publication de position"
    stream, payload = pm._event_bus.published[-1]
    assert stream == "positions.opened"
    assert payload["symbol"] == "ETH/USDT"
    assert payload["type"] == "long"


@pytest.mark.asyncio
async def test_order_manager_publishes_events():
    # Construire un ordre factice minimal
    class DummySide:
        value = "buy"

    class DummyType:
        value = "limit"

    class DummyStatus:
        value = "open"

    class DummyOrder:
        def __init__(self):
            self.order_id = "ORD_1"
            self.symbol = "BTC/USDT"
            self.side = DummySide()
            self.order_type = DummyType()
            self.price = 50000.0
            self.quantity = 0.1
            self.status = DummyStatus()

    om = OrderManager(OrderManagerConfig())
    om._event_bus = FakeBus()

    await om._publish_order_event("orders.submitted", DummyOrder())
    assert om._event_bus.published, "Aucune publication d'ordre"
    stream, payload = om._event_bus.published[-1]
    assert stream == "orders.submitted"
    assert payload["symbol"] == "BTC/USDT"


@pytest.mark.asyncio
async def test_backtesting_publishes_equity_and_results(event_loop):
    from src.backtesting.backtesting_engine import BacktestingEngine

    be = BacktestingEngine("TestBT")
    be._event_bus = FakeBus()

    # Publier un point d'équité
    be._publish_bt_event_sync("backtesting.equity", {
        "timestamp": datetime.utcnow().isoformat(),
        "equity": 100000.0,
        "capital": 100000.0,
    })
    # Laisser la task s'exécuter
    await asyncio.sleep(0)
    assert be._event_bus.published, "Aucune publication backtesting"
    stream, payload = be._event_bus.published[-1]
    assert stream == "backtesting.equity"
