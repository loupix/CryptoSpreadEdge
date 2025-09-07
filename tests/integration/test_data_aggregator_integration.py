import asyncio
from src.data_sources.data_aggregator import data_aggregator


def test_data_aggregator_sources_and_overview_do_not_crash():
    # get_available_sources ne dépend pas d'E/S externes
    sources = data_aggregator.get_available_sources()
    assert isinstance(sources, dict)
    assert "alternative_sources" in sources

    # get_market_overview peut tourner même si aucune source ne répond
    # on appelle la version async via asyncio.run pour éviter les marqueurs
    symbols = ["BTC", "ETH"]
    overview = asyncio.run(data_aggregator.get_market_overview(symbols))
    assert isinstance(overview, dict)
    assert "market_summary" in overview
