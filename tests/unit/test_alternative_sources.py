import types
import pytest

from src.data_sources.alternative_sources import AlternativeDataSources


class DummySource:
    def __init__(self):
        self.called = 0

    async def get_market_data(self, symbols):
        self.called += 1
        return {}


@pytest.mark.asyncio
async def test_alternative_sources_apply_config(monkeypatch):
    alt = AlternativeDataSources()
    # Remplace une source par un dummy et vérifie l'appel
    alt.sources["coinmarketcap"] = DummySource()
    data = await alt.get_market_data(["BTC"], "coinmarketcap")
    assert data == {}
    assert isinstance(alt.sources["coinmarketcap"], DummySource)
