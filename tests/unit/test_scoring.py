from src.ai.feature_engineering.scoring import aggregate_exchange_scores, aggregate_global_score, Weight
from src.ai.feature_engineering.indicators import IndicatorResult
from datetime import datetime


def test_aggregate_exchange_scores_simple():
    bundles = {
        "binance": {
            "momentum": IndicatorResult(0.02, {}, datetime.utcnow()),
            "dispersion": IndicatorResult(0.005, {}, datetime.utcnow()),
        },
        "okx": {
            "momentum": IndicatorResult(0.01, {}, datetime.utcnow()),
            "dispersion": IndicatorResult(0.003, {}, datetime.utcnow()),
        },
    }
    weights = [
        Weight(name="momentum", weight=1.0),
        Weight(name="dispersion", weight=1.0, invert=True, min_clip=0.0, max_clip=0.02),
    ]
    scores = aggregate_exchange_scores(bundles, weights)
    assert set(scores.keys()) == {"binance", "okx"}
    assert scores["binance"] > scores["okx"]  # momentum plus fort, dispersion similaire


def test_aggregate_global_score_methods():
    scores = {"a": 1.0, "b": 2.0, "c": 3.0}
    assert aggregate_global_score(scores, "mean") == 2.0
    assert aggregate_global_score(scores, "max") == 3.0
    assert aggregate_global_score(scores, "min") == 1.0