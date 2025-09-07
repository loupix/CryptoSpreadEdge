from datetime import datetime

from src.ai.feature_engineering.indicators import compute_indicator_bundle
from src.ai.feature_engineering.scoring import aggregate_exchange_scores, aggregate_global_score, Weight
from src.ai.feature_engineering.backtest_indicators import backtest_price_only, BacktestConfig


def _platform_prices(mid: float):
    return {
        "binance": {"price": mid, "bid": mid - 0.1, "ask": mid + 0.1, "volume": 1200, "timestamp": datetime.utcnow(), "source": "exchange"},
        "okx": {"price": mid + 0.05, "bid": mid, "ask": mid + 0.15, "volume": 900, "timestamp": datetime.utcnow(), "source": "exchange"},
        "coingecko": {"price": mid + 0.02, "bid": mid + 0.01, "ask": mid + 0.03, "volume": 2000, "timestamp": datetime.utcnow(), "source": "data_source"},
    }


def test_scoring_integration_flow():
    prices = _platform_prices(100.0)
    bundle_binance = compute_indicator_bundle("BTC", prices, "binance", "okx", [0.5]*60, [{"price": 100 + i*0.1} for i in range(120)])
    bundle_okx = compute_indicator_bundle("BTC", prices, "okx", "binance", [0.5]*60, [{"price": 100 + i*0.1} for i in range(120)])
    weights = [
        Weight(name="momentum", weight=1.0),
        Weight(name="dispersion", weight=1.0, invert=True, min_clip=0.0, max_clip=0.02),
    ]
    scores = aggregate_exchange_scores({"binance": bundle_binance, "okx": bundle_okx}, weights)
    assert set(scores.keys()) == {"binance", "okx"}
    global_score = aggregate_global_score(scores, method="mean")
    assert isinstance(global_score, float)


def test_backtest_integration_flow():
    seq_prices = [_platform_prices(100 + i * 0.2) for i in range(50)]
    price_history_seq = [[{"price": 100 + j} for j in range(100)] for _ in range(50)]
    spread_series_seq = [[0.5 for _ in range(60)] for _ in range(50)]

    cfg = BacktestConfig(entry_threshold=-0.1, take_profit=0.01, stop_loss=0.01)
    res = backtest_price_only(
        symbol="BTC",
        platform_prices_seq=seq_prices,
        buy_platform="binance",
        sell_platform="okx",
        price_history_seq=price_history_seq,
        spread_series_seq=spread_series_seq,
        config=cfg,
    )

    assert res.trades >= 0
    assert isinstance(res.pnl, float)