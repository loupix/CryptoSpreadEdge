"""
Lightweight application container (simple DI) to assemble shared components.
"""

from typing import Optional

from utils.symbols.normalizer import SymbolNormalizer
from data_sources.provider_registry import ProviderRegistry


class AppContainer:
    def __init__(self):
        self._symbol_normalizer: Optional[SymbolNormalizer] = None
        self._provider_registry: Optional[ProviderRegistry] = None

    @property
    def symbol_normalizer(self) -> SymbolNormalizer:
        if self._symbol_normalizer is None:
            self._symbol_normalizer = SymbolNormalizer()
        return self._symbol_normalizer

    @property
    def provider_registry(self) -> ProviderRegistry:
        if self._provider_registry is None:
            self._provider_registry = ProviderRegistry()
        return self._provider_registry


# Global singleton for convenience (can be replaced in tests)
container = AppContainer()

