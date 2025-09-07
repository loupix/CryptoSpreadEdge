import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from ..connectors.common.market_data_types import Balance, Position
from ..connectors.connector_factory import connector_factory
from ..utils.symbols.normalizer import normalize_symbol


class PortfolioAggregator:
    """
    Agrégateur de portefeuille multi-plateformes.

    - Agrège balances et positions depuis tous les connecteurs actifs
    - Normalise les symboles pour permettre une vue consolidée
    - Calcule des métriques simples d'équité et d'exposition
    """

    def __init__(self, base_currency: str = "USD"):
        self.logger = logging.getLogger(__name__)
        self.base_currency = base_currency.upper()
        self._last_refresh: Optional[datetime] = None
        self._balances_by_exchange: Dict[str, List[Balance]] = {}
        self._positions_by_exchange: Dict[str, List[Position]] = {}

    async def refresh(self) -> None:
        """Rafraîchit balances et positions pour tous les connecteurs actifs."""
        try:
            tasks: List[Tuple[str, asyncio.Task]] = []

            for exchange_id, connector in connector_factory.get_all_connectors().items():
                if not connector.is_connected():
                    continue
                tasks.append((exchange_id, asyncio.create_task(self._fetch_exchange_state(exchange_id, connector))))

            if tasks:
                await asyncio.gather(*(t for _, t in tasks))
            self._last_refresh = datetime.utcnow()
        except Exception as exc:
            self.logger.error(f"Erreur refresh portefeuille: {exc}")

    async def _fetch_exchange_state(self, exchange_id: str, connector: Any) -> None:
        balances: List[Balance] = []
        positions: List[Position] = []
        try:
            try:
                balances = await connector.get_balances()
            except Exception as exc:
                self.logger.debug(f"Balances indisponibles pour {exchange_id}: {exc}")

            try:
                positions = await connector.get_positions()
            except Exception as exc:
                self.logger.debug(f"Positions indisponibles pour {exchange_id}: {exc}")

        finally:
            self._balances_by_exchange[exchange_id] = balances or []
            # Normaliser la source pour chaque position
            for p in positions:
                p.source = exchange_id
            self._positions_by_exchange[exchange_id] = positions or []

    def get_balances(self) -> Dict[str, List[Balance]]:
        return self._balances_by_exchange

    def get_positions(self) -> Dict[str, List[Position]]:
        return self._positions_by_exchange

    def consolidate_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Agrège les positions par symbole normalisé.

        Retourne un dict: { symbol: { 'quantity': float, 'exchanges': {ex: qty}, 'sources': [str] } }
        """
        consolidated: Dict[str, Dict[str, Any]] = {}
        for exchange_id, positions in self._positions_by_exchange.items():
            for pos in positions:
                symbol_key = normalize_symbol(pos.symbol)
                entry = consolidated.setdefault(symbol_key, {
                    'quantity': 0.0,
                    'exchanges': {},
                    'sources': set(),
                })
                qty = getattr(pos, 'quantity', None)
                if qty is None and hasattr(pos, 'size'):
                    qty = getattr(pos, 'size')
                qty = float(qty or 0.0)
                entry['quantity'] += qty
                entry['exchanges'][exchange_id] = entry['exchanges'].get(exchange_id, 0.0) + qty
                entry['sources'].add(exchange_id)

        # Convertir les sets en listes pour la sérialisation
        for sym, entry in consolidated.items():
            entry['sources'] = list(entry['sources'])
        return consolidated

    def get_total_equity_estimate(self, price_lookup: Optional[Dict[str, float]] = None) -> float:
        """
        Estime l'équité totale en base currency à partir des positions (approx.).
        Si price_lookup est fourni: map symbol_normalized -> prix en base.
        """
        if not price_lookup:
            price_lookup = {}
        total_equity = 0.0
        consolidated = self.consolidate_positions()
        for symbol, data in consolidated.items():
            price = float(price_lookup.get(symbol, 0.0))
            total_equity += data['quantity'] * price
        return total_equity


# Instance simple réutilisable
portfolio_aggregator = PortfolioAggregator()

