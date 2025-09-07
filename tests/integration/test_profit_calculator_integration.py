from src.arbitrage.arbitrage_engine import ArbitrageOpportunity
from src.arbitrage.profit_calculator import ProfitCalculator


def test_profit_calculator_end_to_end_basic():
    pc = ProfitCalculator()
    opp = ArbitrageOpportunity(
        symbol="ETH",
        buy_platform="binance",
        sell_platform="okx",
        buy_price=100.0,
        sell_price=101.0,
        spread=1.0,
        spread_percentage=0.01,
        volume_available=5.0,
        max_profit=5.0,
        confidence=0.8,
        execution_time=1.0,
        risk_score=0.1,
    )

    quantity = pc.calculate_optimal_quantity(opp, max_investment=200)
    assert quantity >= 0

    calc = pc.calculate_profit(opp, quantity=quantity)
    assert calc is not None
    assert calc.net_profit is not None
