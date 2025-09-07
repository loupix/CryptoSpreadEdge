import types
import sys
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.rest.indicators_api import router as indicators_router


def test_get_indicator_bundle_smoke(monkeypatch):
    app = FastAPI()
    app.include_router(indicators_router)

    # Créer un faux module loaders avec les trois fonctions attendues
    fake_loaders = types.ModuleType("src.ai.feature_engineering.loaders")

    async def fake_load_platform_prices(symbol):
        from datetime import datetime
        return {
            "binance": {"price": 100.0, "bid": 99.9, "ask": 100.1, "volume": 1000, "timestamp": datetime.utcnow(), "source": "exchange"},
            "okx": {"price": 100.2, "bid": 100.1, "ask": 100.3, "volume": 900, "timestamp": datetime.utcnow(), "source": "exchange"},
        }

    async def fake_load_price_history(symbol, points: int = 300):
        return [{"price": 100 + 0.1 * i} for i in range(120)]

    async def fake_load_spread_series(symbol, base_platform, ref_platform, points: int = 200):
        return [0.5 for _ in range(60)]

    fake_loaders.load_platform_prices = fake_load_platform_prices
    fake_loaders.load_price_history = fake_load_price_history
    fake_loaders.load_spread_series = fake_load_spread_series

    # Injecter le faux module dans sys.modules pour que l'import tardif le prenne
    monkeypatch.setitem(sys.modules, "src.ai.feature_engineering.loaders", fake_loaders)

    client = TestClient(app)
    resp = client.get("/indicators/bundle", params={"symbol": "BTC", "buy_platform": "binance", "sell_platform": "okx"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert "momentum" in data["indicators"]