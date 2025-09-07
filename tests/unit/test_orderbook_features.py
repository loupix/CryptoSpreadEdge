from datetime import datetime

from src.ai.feature_engineering.orderbook_features import (
    OrderBookSnapshot,
    compute_depth,
    compute_imbalance,
    compute_expected_slippage,
    compute_simple_market_impact,
    compute_orderbook_bundle,
)


def _ob():
    bids = [(100.0 - i * 0.1, 10.0 + i) for i in range(10)]
    asks = [(100.1 + i * 0.1, 9.0 + i) for i in range(10)]
    return OrderBookSnapshot(bids=bids, asks=asks, timestamp=datetime.utcnow())


def test_depth_positive():
    ob = _ob()
    res = compute_depth(ob, 5)
    assert res.value > 0


def test_imbalance_range():
    ob = _ob()
    res = compute_imbalance(ob, 5)
    assert 0.0 <= res.value <= 1.0


def test_expected_slippage_buy_sell():
    ob = _ob()
    buy = compute_expected_slippage(ob, "buy", notional=1000.0, max_levels=20)
    sell = compute_expected_slippage(ob, "sell", notional=1000.0, max_levels=20)
    assert buy.components["qty"] > 0
    assert sell.components["qty"] > 0


def test_market_impact_nonnegative():
    ob = _ob()
    res = compute_simple_market_impact(ob, 1000.0, 20)
    assert res.value >= 0.0


def test_orderbook_bundle_keys():
    ob = _ob()
    b = compute_orderbook_bundle(ob, 1000.0)
    for key in [
        "depth_5",
        "depth_10",
        "imbalance_5",
        "imbalance_10",
        "expected_slippage_buy",
        "expected_slippage_sell",
        "market_impact",
    ]:
        assert key in b