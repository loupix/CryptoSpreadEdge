"""
Provider registry for external alternative data sources.

Pattern: Factory + Registry + Null Object
"""

from typing import Dict, Protocol, Optional


class Provider(Protocol):
    async def fetch(self, *args, **kwargs):
        ...


class NullProvider:
    async def fetch(self, *args, **kwargs):
        return None


class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, Provider] = {}

    def register(self, name: str, provider: Provider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> Provider:
        return self._providers.get(name, NullProvider())

    def disable(self, name: str) -> None:
        self._providers[name] = NullProvider()

