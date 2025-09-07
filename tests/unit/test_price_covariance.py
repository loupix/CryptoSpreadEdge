import asyncio
import numpy as np
import pytest

from src.portfolio.portfolio_service import PortfolioAggregator


@pytest.mark.asyncio
async def test_compute_price_covariance_synthetic(monkeypatch):
    agg = PortfolioAggregator()

    # Construire un loader synthétique
    async def fake_load_price_history(symbol: str, points: int = 300):
        # Série 1: trend + bruit
        rng = np.random.default_rng(42)
        base = np.linspace(100, 110, num=points)
        noise = rng.normal(0, 0.1, size=points)
        if symbol == 'AAA':
            prices = base + noise
        elif symbol == 'BBB':
            prices = base * 1.01 + noise * 1.5
        else:
            prices = base + rng.normal(0, 0.2, size=points)
        return [{"close": float(x)} for x in prices]

    # Monkeypatch le loader utilisé par compute_price_covariance
    from src.portfolio import portfolio_service as svc
    monkeypatch.setattr(svc, 'load_price_history', fake_load_price_history)

    cov = await agg.compute_price_covariance(['AAA', 'BBB'], points=100)
    assert ('AAA', 'AAA') in cov and ('BBB', 'BBB') in cov
    assert cov[('AAA', 'AAA')] > 0
    assert cov[('BBB', 'BBB')] > 0
    # Covariance croisée réaliste (pas NaN)
    assert np.isfinite(cov[('AAA', 'BBB')])