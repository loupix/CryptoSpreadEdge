from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional

from .base import BaseDetector
from .types import MarketAbuseAlert, MarketAbuseType, TradeEvent


class WashTradingDetector(BaseDetector):
    """
    Heuristique:
    - Pour chaque trader_id, détecte des alternances rapides buy/sell avec tailles quasi égales
    - Si N alternances dans window_seconds, alerte de wash trading
    """

    def __init__(
        self,
        symbol: str,
        lookback: timedelta = timedelta(minutes=10),
        window_seconds: int = 60,
        min_alternations: int = 3,
        size_tolerance: float = 0.05,
    ) -> None:
        super().__init__(symbol, lookback)
        self.window_seconds = window_seconds
        self.min_alternations = min_alternations
        self.size_tolerance = size_tolerance
        self.per_trader_events: Dict[str, Deque[TradeEvent]] = defaultdict(deque)

    def update_trade(self, trade: TradeEvent):
        alerts: List[MarketAbuseAlert] = super().update_trade(trade)
        if trade.trader_id:
            dq = self.per_trader_events[trade.trader_id]
            dq.append(trade)
            cutoff = trade.timestamp - timedelta(seconds=self.window_seconds)
            while dq and dq[0].timestamp < cutoff:
                dq.popleft()
        return alerts + self.detect(trade.timestamp)

    def detect(self, now: Optional[datetime] = None) -> List[MarketAbuseAlert]:
        alerts: List[MarketAbuseAlert] = []
        current_ts = now or (self.trades[-1].timestamp if self.trades else None)
        if current_ts is None:
            return alerts
        for trader_id, dq in self.per_trader_events.items():
            if len(dq) < self.min_alternations * 2:
                continue
            alternations = 0
            for i in range(1, len(dq)):
                a, b = dq[i - 1], dq[i]
                if a.side == b.side:
                    continue
                # tailles proches
                if a.quantity == 0:
                    continue
                rel_diff = abs(b.quantity - a.quantity) / a.quantity
                if rel_diff <= self.size_tolerance:
                    alternations += 1
            if alternations >= self.min_alternations:
                alerts.append(
                    MarketAbuseAlert(
                        timestamp=current_ts,
                        symbol=self.symbol,
                        type=MarketAbuseType.WASH_TRADING,
                        severity=min(1.0, alternations / (self.min_alternations * 2)),
                        message=f"Alternances rapides buy/sell avec tailles proches pour trader {trader_id}",
                        metadata={"alternations": float(alternations)},
                    )
                )
        return alerts

