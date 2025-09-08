from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from src.database.database import get_database_manager
from src.database.repositories import OpportunityRepository
from .opportunities import Opportunity


class OpportunitySink:
    def emit(self, opps: Iterable[Opportunity]) -> None:
        raise NotImplementedError


class FileOpportunitySink(OpportunitySink):
    def __init__(self, file_path: str = "logs/opportunities.jsonl") -> None:
        self.path = Path(file_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, opps: Iterable[Opportunity]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            for o in opps:
                f.write(
                    json.dumps(
                        {
                            "timestamp": o.timestamp.isoformat(),
                            "symbol": o.symbol,
                            "kind": o.kind,
                            "confidence": o.confidence,
                            "rationale": o.rationale,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )


class DatabaseOpportunitySink(OpportunitySink):
    async def emit_async(self, opps: Iterable[Opportunity]) -> None:
        db = get_database_manager()
        async with db.get_session() as session:
            repo = OpportunityRepository(session)
            for o in opps:
                await repo.create(
                    {
                        "symbol": o.symbol,
                        "kind": o.kind,
                        "confidence": o.confidence,
                        "rationale": o.rationale,
                        "meta_data": {},
                    }
                )


class StrategyTriggerOpportunitySink(OpportunitySink):
    """
    Exemple: brancher une stratégie (pseudo)
    Ici on se contente d'exposer un hook appelant une fonction fournie.
    """

    def __init__(self, handler):
        self.handler = handler

    def emit(self, opps: Iterable[Opportunity]) -> None:
        self.handler(list(opps))

