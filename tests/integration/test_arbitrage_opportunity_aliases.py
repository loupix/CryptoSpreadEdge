from src.arbitrage.arbitrage_engine import ArbitrageOpportunity


def test_arbitrage_opportunity_alias_mapping():
    # Construction avec alias
    opp = ArbitrageOpportunity(
        symbol="BTC",
        buy_platform="binance",
        sell_platform="okx",
        buy_price=100.0,
        sell_price=102.0,
        spread=2.0,
        expected_profit=2.0,
        confidence=0.9,
        execution_time=1.2,
        risk_score=0.2,
        spread_percentage=0.02,
        volume_available=1.0,
    )

    # Les alias doivent être mappés sur les champs officiels
    assert opp.buy_exchange == "binance"
    assert opp.sell_exchange == "okx"
    assert opp.max_profit >= 0
    assert opp.execution_time_estimate >= 0
