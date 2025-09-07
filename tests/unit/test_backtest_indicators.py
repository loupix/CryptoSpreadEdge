from src.ai.feature_engineering.backtest_indicators import backtest_price_only, BacktestConfig
from src.ai.feature_engineering.indicators import compute_indicator_bundle
from datetime import datetime


def _platform_prices(mid: float):
    return {
        "binance": {"price": mid, "bid": mid - 0.1, "ask": mid + 0.1, "volume": 1000, "timestamp": datetime.utcnow(), "source": "exchange"},
        "okx": {"price": mid + 0.05, "bid": mid - 0.05, "ask": mid + 0.15, "volume": 900, "timestamp": datetime.utcnow(), "source": "exchange"},
    }


def test_backtest_runs_and_counts_trades():
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