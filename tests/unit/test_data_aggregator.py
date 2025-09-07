import pytest

from src.data_sources.data_aggregator import DataAggregator


@pytest.mark.asyncio
async def test_data_aggregator_basic(monkeypatch):
    agg = DataAggregator()

    # Mock des connecteurs: aucun connecté
    class DummyConnector:
        def is_connected(self):
            return False

    agg.exchange_connectors = {"dummy": DummyConnector()}

    # Mock des sources alternatives: retourner vide
    class DummyAlt:
        async def get_market_data(self, symbols, source):
            return {}

    agg.alternative_sources = DummyAlt()

    result = await agg.get_aggregated_data(["BTC"])
    assert isinstance(result, dict)
    assert "BTC" not in result or result["BTC"] is None or result["BTC"]
