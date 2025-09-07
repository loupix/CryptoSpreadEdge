import pytest
from datetime import datetime

from src.arbitrage.arbitrage_engine import ArbitrageOpportunity, ArbitrageExecution
from src.arbitrage.profit_calculator import ProfitCalculator
from src.arbitrage.risk_manager import ArbitrageRiskManager


def test_basic_arbitrage_flow_integration():
    pc = ProfitCalculator()
    rm = ArbitrageRiskManager()

    opp = ArbitrageOpportunity(
        symbol="BTC",
        buy_platform="binance",
        sell_platform="okx",
        buy_price=100.0,
        sell_price=101.0,
        spread=1.0,
        spread_percentage=0.01,
        volume_available=10.0,
        max_profit=10.0,
        confidence=0.9,
        execution_time=1.0,
        risk_score=0.2,
    )

    # ProfitCalculator doit pouvoir calculer un profit attendu
    calc = pc.calculate_profit(opp, quantity=1.0)
    assert calc is not None
    assert calc.net_profit is not None

    # ArbitrageExecution pour une analyse basique
    exec_obj = ArbitrageExecution(
        opportunity=opp,
        buy_order=None,
        sell_order=None,
        status="completed",
        actual_profit=calc.net_profit,
        execution_time=1.0,
        fees_paid=calc.fees,
        net_profit=calc.net_profit,
        timestamp=datetime.utcnow(),
    )

    # L'analyse peut retourner un dict vide si ordres absents, on valide le type
    result = pc.analyze_execution_result(exec_obj)
    assert isinstance(result, dict)

    # Le risk manager expose un statut synchronement
    status = rm.get_risk_status()
    assert isinstance(status, dict)
