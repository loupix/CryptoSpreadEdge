from datetime import datetime

from src.ai.feature_engineering.indicators import compute_indicator_bundle
from src.ai.feature_engineering.mtf_features import compute_mtf_bundle
from src.ai.feature_engineering.feature_vector import flatten_indicator_bundle, apply_normalization, to_ordered_vector, FeatureSpec
from src.ai.feature_engineering.scoring import aggregate_exchange_scores, aggregate_global_score, Weight
from src.ai.feature_engineering.backtest_indicators import backtest_price_only, BacktestConfig


def _platform_prices(mid: float):
    return {
        "binance": {"price": mid, "bid": mid - 0.1, "ask": mid + 0.1, "volume": 1200, "timestamp": datetime.utcnow(), "source": "exchange"},
        "okx": {"price": mid + 0.05, "bid": mid, "ask": mid + 0.15, "volume": 900, "timestamp": datetime.utcnow(), "source": "exchange"},
        "coingecko": {"price": mid + 0.02, "bid": mid + 0.01, "ask": mid + 0.03, "volume": 2000, "timestamp": datetime.utcnow(), "source": "data_source"},
    }


def test_full_indicator_pipeline():
    prices = _platform_prices(100.0)
    price_history = [{"price": 100 + i*0.1} for i in range(200)]
    spreads = [0.5 for _ in range(100)]

    # Bundle de base
    bundle_binance = compute_indicator_bundle("BTC", prices, "binance", "okx", spreads, price_history)
    bundle_okx = compute_indicator_bundle("BTC", prices, "okx", "binance", spreads, price_history)

    # MTF (smoke)
    mtf = compute_mtf_bundle("BTC", prices, "binance", "okx", spreads, price_history, timeframes_points=[20, 60, 120])
    assert "base" in mtf

    # Vectorisation + normalisation
    flat = flatten_indicator_bundle(bundle_binance)
    specs = [FeatureSpec(name="momentum", min_value=-0.1, max_value=0.1, center=0.0, scale=0.02)]
    norm = apply_normalization(flat, specs)
    names, vec = to_ordered_vector(norm)
    assert len(vec) == len(names)

    # Scoring
    weights = [Weight(name="momentum", weight=1.0), Weight(name="dispersion", weight=1.0, invert=True, min_clip=0.0, max_clip=0.02)]
    scores = aggregate_exchange_scores({"binance": bundle_binance, "okx": bundle_okx}, weights)
    global_score = aggregate_global_score(scores, method="mean")
    assert isinstance(global_score, float)

    # Backtest rapide
    seq_prices = [_platform_prices(100 + i * 0.2) for i in range(50)]
    price_history_seq = [price_history for _ in range(50)]
    spread_series_seq = [spreads for _ in range(50)]
    cfg = BacktestConfig(entry_threshold=-0.1, take_profit=0.01, stop_loss=0.01)
    res = backtest_price_only("BTC", seq_prices, "binance", "okx", price_history_seq, spread_series_seq, cfg)
    assert res.trades >= 0