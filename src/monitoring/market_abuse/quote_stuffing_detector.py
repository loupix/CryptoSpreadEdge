from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Deque, List, Optional

from .base import BaseDetector
from .types import MarketAbuseAlert, MarketAbuseType, OrderBookSnapshot


class QuoteStuffingDetector(BaseDetector):
    """
    Heuristique:
    - Compte le nombre de mises à jour orderbook dans une fenêtre courte
    - Si le rythme dépasse un seuil, alerte quote stuffing
    """

    def __init__(
        self,
        symbol: str,
        lookback: timedelta = timedelta(minutes=5),
        window_seconds: int = 5,
        max_updates: int = 100,
    ) -> None:
        super().__init__(symbol, lookback)
        self.window_seconds = window_seconds
        self.max_updates = max_updates

    def detect(self, now: Optional[datetime] = None) -> List[MarketAbuseAlert]:
        if not self.orderbooks:
            return []
        current_ts = now or self.orderbooks[-1].timestamp
        window_start = current_ts - timedelta(seconds=self.window_seconds)
        updates = sum(1 for ob in self.orderbooks if ob.timestamp >= window_start)
        if updates > self.max_updates:
            return [
                MarketAbuseAlert(
                    timestamp=current_ts,
                    symbol=self.symbol,
                    type=MarketAbuseType.QUOTE_STUFFING,
                    severity=min(1.0, (updates - self.max_updates) / self.max_updates),
                    message=f"Rythme de mises à jour orderbook anormal: {updates}/{self.window_seconds}s",
                    metadata={"updates": float(updates)},
                )
            ]
        return []

