from datetime import datetime

from src.ai.feature_engineering.mtf_features import compute_mtf_bundle


def test_mtf_bundle_contains_suffixes():
    symbol = "BTC"
    platform_prices = {
        "binance": {"price": 100.0, "bid": 99.9, "ask": 100.1, "volume": 1000, "timestamp": datetime.utcnow(), "source": "exchange"},
        "okx": {"price": 100.2, "bid": 100.1, "ask": 100.3, "volume": 900, "timestamp": datetime.utcnow(), "source": "exchange"},
    }
    price_history = [{"price": 100 + 0.1 * i} for i in range(300)]
    spreads = [0.5 + 0.01 * (i % 3) for i in range(240)]

    mtf = compute_mtf_bundle(symbol, platform_prices, "binance", "okx", spreads, price_history, timeframes_points=[20, 60, 120])

    assert "base" in mtf
    assert "intraday_volatility.p20" in mtf
    assert "vol_of_vol.p60" in mtf
    assert "momentum.p120" in mtf