from __future__ import annotations

import asyncio
import json
from typing import Iterable, List

from .types import MarketAbuseAlert
from .opportunities import opportunities_from_alert, Opportunity
from .sinks import AlertSink, OpportunitySink

try:
    from src.utils.messaging.redis_bus import RedisEventBus
except Exception:  # pragma: no cover
    RedisEventBus = None  # type: ignore


class RedisAlertSink(AlertSink):
    """Publie les alertes d'abus de marché dans Redis Streams."""

    def __init__(self, stream_name: str = "alerts.market_abuse") -> None:
        self.stream_name = stream_name
        self._bus: RedisEventBus | None = None
        self._connecting = False

    async def _ensure_bus(self):
        if self._bus is None and RedisEventBus is not None and not self._connecting:
            self._connecting = True
            self._bus = RedisEventBus()
            await self._bus.connect()
            self._connecting = False

    def emit(self, alerts: Iterable[MarketAbuseAlert]) -> None:
        # Interface sync exigée par AlertSink; dispatcher en tâche async
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(self._emit_async(list(alerts)))

    async def _emit_async(self, alerts: List[MarketAbuseAlert]) -> None:
        await self._ensure_bus()
        if self._bus is None:
            return
        for a in alerts:
            payload = {
                "symbol": a.symbol,
                "type": a.type.value,
                "severity": a.severity,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
                "metadata": a.metadata or {},
            }
            await self._bus.publish(self.stream_name, payload)


class RedisOpportunitySink(OpportunitySink):
    """Publie les opportunités dérivées dans Redis Streams."""

    def __init__(self, stream_name: str = "arbitrage.opportunities") -> None:
        self.stream_name = stream_name
        self._bus: RedisEventBus | None = None
        self._connecting = False

    async def _ensure_bus(self):
        if self._bus is None and RedisEventBus is not None and not self._connecting:
            self._connecting = True
            self._bus = RedisEventBus()
            await self._bus.connect()
            self._connecting = False

    def emit(self, alerts: Iterable[MarketAbuseAlert]) -> None:
        # Convertir en opportunités et publier
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(self._emit_async(list(alerts)))

    async def _emit_async(self, alerts: List[MarketAbuseAlert]) -> None:
        await self._ensure_bus()
        if self._bus is None:
            return
        opps: List[Opportunity] = []
        for a in alerts:
            opps.extend(opportunities_from_alert(a))
        for o in opps:
            payload = {
                "timestamp": o.timestamp.isoformat(),
                "symbol": o.symbol,
                "kind": o.kind,
                "confidence": o.confidence,
                "rationale": o.rationale,
            }
            await self._bus.publish(self.stream_name, payload)

