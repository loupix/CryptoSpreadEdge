"""
Symbol normalization using Strategy pattern.

Given a list of exchanges and raw symbols (e.g., ["BTC", "ETH/USDT"]),
produce a normalized list (e.g., ["BTC/USDT", "ETH/USDT"]).
"""

from abc import ABC, abstractmethod
from typing import List


class SymbolNormalizationStrategy(ABC):
    """Interface for symbol normalization per exchange."""

    @abstractmethod
    def normalize(self, raw_symbol: str) -> str:
        """Return a normalized symbol string."""
        raise NotImplementedError


class DefaultUSDTStrategy(SymbolNormalizationStrategy):
    """Default strategy: append /USDT if quote is missing."""

    def normalize(self, raw_symbol: str) -> str:
        symbol = raw_symbol.strip().upper()
        if "/" in symbol:
            return symbol
        return f"{symbol}/USDT"


class SymbolNormalizer:
    """Coordinator that selects a strategy based on the exchange.

    For now, all exchanges use DefaultUSDTStrategy. This can be extended
    to specific strategies per exchange (e.g., futures mapping, aliases).
    """

    def __init__(self):
        self._default_strategy = DefaultUSDTStrategy()

    def normalize_for_exchanges(self, exchanges: List[str], raw_symbols: List[str]) -> List[str]:
        # For multi-exchange, return the union of normalized symbols using the most permissive rule.
        # Currently, same rule for all.
        return [self._default_strategy.normalize(sym) for sym in raw_symbols]


# Utilitaire simple pour compatibilité: normaliser un seul symbole
def normalize_symbol(raw_symbol: str) -> str:
    return DefaultUSDTStrategy().normalize(raw_symbol)

