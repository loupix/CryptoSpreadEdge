import json
from datetime import datetime

from src.monitoring.market_abuse.opportunities import Opportunity
from src.monitoring.market_abuse.opportunity_sinks import FileOpportunitySink, StrategyTriggerOpportunitySink


def test_file_opportunity_sink(tmp_path):
    sink = FileOpportunitySink(str(tmp_path / "opps.jsonl"))
    opp = Opportunity(timestamp=datetime.utcnow(), symbol="BTC/USDT", kind="volatility_breakout_long", confidence=0.8, rationale="test")
    sink.emit([opp])
    data = [json.loads(l) for l in (tmp_path / "opps.jsonl").read_text(encoding="utf-8").splitlines() if l]
    assert data[0]["symbol"] == "BTC/USDT"
    assert data[0]["kind"] == "volatility_breakout_long"


def test_strategy_trigger_opportunity_sink_calls_handler():
    captured = []

    def handler(opps):
        captured.extend(opps)

    sink = StrategyTriggerOpportunitySink(handler)
    opp = Opportunity(timestamp=datetime.utcnow(), symbol="ETH/USDT", kind="mean_reversion", confidence=0.5, rationale="test")
    sink.emit([opp])
    assert len(captured) == 1
    assert captured[0].symbol == "ETH/USDT"

