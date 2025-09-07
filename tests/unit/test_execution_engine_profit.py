import pytest
from datetime import datetime

from src.arbitrage.arbitrage_engine import ArbitrageOpportunity, ArbitrageExecution
from src.arbitrage.execution_engine import ExecutionEngine
from src.connectors.common.market_data_types import Order, OrderSide, OrderType, OrderStatus


@pytest.mark.asyncio
async def test_execution_engine_calculate_actual_profit():
    engine = ExecutionEngine()

    buy_order = Order(
        id="1",
        symbol="BTC",
        exchange="binance",
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        price=100.0,
        quantity=1.0,
        status=OrderStatus.FILLED,
        timestamp=datetime.utcnow(),
        filled_quantity=1.0,
        average_price=100.0
    )
    sell_order = Order(
        id="2",
        symbol="BTC",
        exchange="okx",
        side=OrderSide.SELL,
        type=OrderType.MARKET,
        price=102.0,
        quantity=1.0,
        status=OrderStatus.FILLED,
        timestamp=datetime.utcnow(),
        filled_quantity=1.0,
        average_price=102.0
    )

    opp = ArbitrageOpportunity(
        symbol="BTC",
        buy_platform="binance",
        sell_platform="okx",
        buy_price=100.0,
        sell_price=102.0,
        spread=0.02,
        expected_profit=2.0,
        max_profit=2.0,
        fees=0.0,
        confidence=0.9,
        execution_time=1.0,
        risk_score=0.2
    )

    exec_obj = ArbitrageExecution(
        opportunity=opp,
        buy_order=buy_order,
        sell_order=sell_order,
        status="completed",
        actual_profit=0.0,
        execution_time=1.0,
        fees_paid=0.0,
        net_profit=0.0,
        timestamp=datetime.utcnow()
    )

    profit = await engine._calculate_actual_profit(exec_obj)
    assert profit == pytest.approx(2.0, rel=1e-6)
