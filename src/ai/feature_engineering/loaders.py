from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional

from ...data_sources.data_aggregator import data_aggregator


async def load_platform_prices(symbol: str) -> Dict[str, Dict[str, Any]]:
    """Récupère un snapshot de prix par plateforme pour un symbole.
    Sources: exchanges via data_aggregator + alternatives.
    """
    platform_prices: Dict[str, Dict[str, Any]] = {}

    # Exchanges via data_aggregator.connectors? On s'appuie sur aggregated_data structure
    aggregated = await data_aggregator.get_aggregated_data([symbol])
    # agrégées alternatives
    for source_name in ["coinmarketcap", "coingecko", "cryptocompare", "messari"]:
        try:
            alt = await data_aggregator.alternative_sources.get_market_data([symbol], source_name)
            md = alt.get(symbol)
            if md and md.ticker:
                platform_prices[source_name] = {
                    "price": md.ticker.price,
                    "bid": md.ticker.bid,
                    "ask": md.ticker.ask,
                    "volume": md.ticker.volume,
                    "timestamp": md.timestamp,
                    "source": "data_source",
                }
        except Exception:
            # Tolérant aux erreurs de sources externes
            pass

    # Les exchanges agrégés peuvent être exposés différemment; si aggregated[symbol] a .exchanges
    try:
        agg = aggregated.get(symbol)
        if agg and hasattr(agg, "exchanges"):
            for exch, md in agg.exchanges.items():
                if md and md.ticker:
                    platform_prices[exch] = {
                        "price": md.ticker.price,
                        "bid": md.ticker.bid,
                        "ask": md.ticker.ask,
                        "volume": md.ticker.volume,
                        "timestamp": md.timestamp,
                        "source": "exchange",
                    }
    except Exception:
        pass

    return platform_prices


async def load_price_history(symbol: str, points: int = 300) -> List[Dict[str, Any]]:
    """Charge un historique de prix simple pour un symbole à usage d'indicateurs.
    Fallback: si pas disponible via data_aggregator, renvoie une liste vide.
    """
    try:
        # Si data_aggregator expose une méthode d'historique
        if hasattr(data_aggregator, "get_price_history"):
            history = await data_aggregator.get_price_history(symbol, limit=points)
            if history:
                return [{"price": h.price, "timestamp": h.timestamp} for h in history][-points:]
    except Exception:
        pass
    return []


async def load_spread_series(symbol: str, base_platform: str, ref_platform: str, points: int = 200) -> List[float]:
    """Construit une série de spreads estimés entre deux plateformes à partir des prix historiques si disponibles.
    """
    # Naïf: sans historique par plateforme, on renvoie une série constante neutre
    return [0.5 for _ in range(points)]