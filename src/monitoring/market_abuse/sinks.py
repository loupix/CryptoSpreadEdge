from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Dict

from prometheus_client import Counter, Gauge, CollectorRegistry

from src.database.database import get_database_manager
from src.database.repositories import MarketAbuseAlertRepository
from .types import MarketAbuseAlert

logger = logging.getLogger(__name__)


class AlertSink:
    def emit(self, alerts: Iterable[MarketAbuseAlert]) -> None:
        raise NotImplementedError


class FileAlertSink(AlertSink):
    def __init__(self, file_path: str = "logs/market_abuse_alerts.jsonl") -> None:
        self.path = Path(file_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, alerts: Iterable[MarketAbuseAlert]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            for a in alerts:
                line = {
                    "timestamp": a.timestamp.isoformat(),
                    "symbol": a.symbol,
                    "type": a.type.value,
                    "severity": a.severity,
                    "message": a.message,
                    "metadata": a.metadata or {},
                }
                f.write(json.dumps(line, ensure_ascii=False) + "\n")


class DatabaseAlertSink(AlertSink):
    async def emit_async(self, alerts: Iterable[MarketAbuseAlert]) -> None:
        db = get_database_manager()
        async with db.get_session() as session:
            repo = MarketAbuseAlertRepository(session)
            for a in alerts:
                await repo.create(
                    {
                        "symbol": a.symbol,
                        "alert_type": a.type.value,
                        "severity": a.severity,
                        "message": a.message,
                        "detector": None,
                        "exchange": None,
                        "timestamp": a.timestamp,
                        "meta_data": a.metadata or {},
                    }
                )


class PrometheusAlertSink(AlertSink):
    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        # Par défaut, utiliser un registre privé pour éviter les collisions en tests
        self.registry = registry or CollectorRegistry()
        self.counter = Counter(
            "market_abuse_alert_total",
            "Nombre d'alertes d'abus de marché",
            ["symbol", "type"],
            registry=self.registry,
        )
        self.severity_gauge = Gauge(
            "market_abuse_alert_severity",
            "Sévérité de la dernière alerte",
            ["symbol", "type"],
            registry=self.registry,
        )

    def emit(self, alerts: Iterable[MarketAbuseAlert]) -> None:
        for a in alerts:
            self.counter.labels(symbol=a.symbol, type=a.type.value).inc()
            self.severity_gauge.labels(symbol=a.symbol, type=a.type.value).set(a.severity)

