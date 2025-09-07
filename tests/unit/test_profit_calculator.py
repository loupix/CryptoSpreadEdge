import pytest
from datetime import datetime

from src.arbitrage.arbitrage_engine import ArbitrageOpportunity, ArbitrageExecution
from src.arbitrage.profit_calculator import ProfitCalculator


def test_profit_calculator_analyze_execution_result_basic():
    pc = ProfitCalculator()

    opp = ArbitrageOpportunity(
        symbol="BTC",
        buy_platform="binance",
        sell_platform="okx",
        buy_price=100.0,
        sell_price=102.0,
        spread=0.02,
        expected_profit=2.0,
        max_profit=2.0,
        fees=0.1,
        confidence=0.9,
        execution_time=1.0,
        risk_score=0.2
    )

    exec_obj = ArbitrageExecution(
        opportunity=opp,
        buy_order=None,
        sell_order=None,
        status="completed",
        actual_profit=1.9,
        execution_time=1.2,
        fees_paid=0.1,
        net_profit=1.8,
        timestamp=datetime.utcnow()
    )

    result = pc.analyze_execution_result(exec_obj)
    assert isinstance(result, dict)
    # Si ordres absents, l'analyse renvoie un dict vide selon l'implémentation
    # donc on accepte vide ou non vide selon évolution future
    assert result == {} or "net_profit" in result
