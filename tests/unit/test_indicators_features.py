import math
from datetime import datetime, timedelta

from src.ai.feature_engineering.indicators import (
    compute_indicator_bundle,
    compute_intraday_volatility,
    compute_bid_ask_skew,
    compute_cross_platform_dispersion,
    compute_spread_stability,
    compute_latency_risk,
    compute_simple_order_pressure,
    compute_momentum,
    compute_trend_consistency,
    compute_spread_ratio,
    compute_vol_of_vol,
    compute_outlier_score,
    compute_asymmetric_latency,
    compute_liquidity_concentration,
)


def _now():
    return datetime.utcnow()


def test_intraday_volatility_basic():
    ph = [{"price": 100 + i} for i in range(50)]
    res = compute_intraday_volatility(ph, lookback_points=50)
    assert res.value >= 0.0
    assert "std" in res.components


def test_bid_ask_skew_mid():
    buy = {"ask": 101.0}
    sell = {"bid": 99.0}
    res = compute_bid_ask_skew(buy, sell)
    assert math.isfinite(res.value)


def test_cross_platform_dispersion():
    platforms = {
        "binance": {"price": 100.0},
        "okx": {"price": 100.5},
        "bybit": {"price": 99.8},
    }
    res = compute_cross_platform_dispersion(platforms)
    assert res.value >= 0.0


def test_spread_stability():
    spreads = [0.5 + 0.01 * (i % 3) for i in range(60)]
    res = compute_spread_stability(spreads, 60)
    assert 0.0 <= res.value <= 1.0


def test_latency_risk_mapping():
    ts_old = _now() - timedelta(seconds=30)
    res = compute_latency_risk(ts_old, _now())
    assert 0.0 <= res.value <= 1.0


def test_order_pressure_bounds():
    buy = {"volume": 1000.0}
    sell = {"volume": 500.0}
    res = compute_simple_order_pressure(buy, sell)
    assert 0.0 <= res.value <= 1.0


def test_momentum_sign():
    ph_up = [{"price": 100 + i} for i in range(30)]
    up = compute_momentum(ph_up, 30)
    assert up.value > 0


def test_trend_consistency_range():
    ph = [{"price": 100 + (i % 2)} for i in range(20)]
    res = compute_trend_consistency(ph, 20)
    assert 0.0 <= res.value <= 1.0


def test_spread_ratio_mid():
    buy = {"ask": 101.0}
    sell = {"bid": 100.5}
    res = compute_spread_ratio(buy, sell)
    assert res.value >= 0.0


def test_vol_of_vol_nonnegative():
    ph = [{"price": 100 + (i % 5)} for i in range(200)]
    res = compute_vol_of_vol(ph, 120, 20)
    assert res.value >= 0.0


def test_outlier_score_bounds():
    ph = [{"price": 100.0} for _ in range(100)]
    ph[-1] = {"price": 110.0}
    res = compute_outlier_score(ph, 100)
    assert 0.0 <= res.value <= 1.0


def test_asymmetric_latency_bounds():
    t1 = _now()
    t2 = t1 - timedelta(seconds=10)
    res = compute_asymmetric_latency(t1, t2)
    assert 0.0 <= res.value <= 1.0


def test_liquidity_concentration_range():
    platforms = {
        "binance": {"source": "exchange", "volume": 1000},
        "okx": {"source": "exchange", "volume": 800},
        "coingecko": {"source": "data_source", "volume": 2000},
    }
    res = compute_liquidity_concentration(platforms)
    assert 0.0 <= res.value <= 1.0


def test_indicator_bundle_smoke():
    platforms = {
        "binance": {"price": 100.0, "bid": 99.9, "ask": 100.1, "volume": 1000, "timestamp": _now(), "source": "exchange"},
        "okx": {"price": 100.2, "bid": 100.1, "ask": 100.3, "volume": 900, "timestamp": _now(), "source": "exchange"},
    }
    ph = [{"price": 100 + 0.1 * i} for i in range(120)]
    spreads = [0.5 + 0.01 * (i % 3) for i in range(60)]
    bundle = compute_indicator_bundle("BTC", platforms, "binance", "okx", spreads, ph)
    assert "momentum" in bundle and "dispersion" in bundle