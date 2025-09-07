import math

from src.portfolio.optimizer import PortfolioOptimizer


def test_mean_variance_basic_weights_sum_to_one():
    opt = PortfolioOptimizer()
    mu = {"BTC": 0.10, "ETH": 0.15, "BNB": 0.08}
    cov = {
        ("BTC", "BTC"): 0.04, ("BTC", "ETH"): 0.01, ("BTC", "BNB"): 0.008,
        ("ETH", "ETH"): 0.05, ("ETH", "BNB"): 0.012,
        ("BNB", "BNB"): 0.03,
    }
    w = opt.mean_variance_weights(mu, cov, risk_aversion=3.0, min_weight=0.0, max_weight=0.8, target_leverage=1.0)
    assert math.isclose(sum(w.values()), 1.0, rel_tol=1e-6)
    assert set(w.keys()) == set(mu.keys())


def test_risk_parity_basic_weights_sum_to_one():
    opt = PortfolioOptimizer()
    cov = {
        ("BTC", "BTC"): 0.04, ("BTC", "ETH"): 0.01, ("BTC", "BNB"): 0.008,
        ("ETH", "ETH"): 0.05, ("ETH", "BNB"): 0.012,
        ("BNB", "BNB"): 0.03,
    }
    w = opt.risk_parity_weights(cov, min_weight=0.0, max_weight=0.8, target_leverage=1.0, iterations=50, lr=0.2)
    assert math.isclose(sum(w.values()), 1.0, rel_tol=1e-5)
    assert {"BTC", "ETH", "BNB"} == set(w.keys())

