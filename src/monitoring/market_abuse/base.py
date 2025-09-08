from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timedelta
from statistics import mean, pstdev
from typing import Deque, List, Optional

from .types import MarketAbuseAlert, MarketAbuseType, TradeEvent, OrderBookSnapshot


class BaseDetector(ABC):
    def __init__(self, symbol: str, lookback: timedelta) -> None:
        self.symbol = symbol
        self.lookback = lookback
        self.trades: Deque[TradeEvent] = deque()
        self.orderbooks: Deque[OrderBookSnapshot] = deque()

    def _evict_old(self, now: datetime) -> None:
        cutoff = now - self.lookback
        while self.trades and self.trades[0].timestamp < cutoff:
            self.trades.popleft()
        while self.orderbooks and self.orderbooks[0].timestamp < cutoff:
            self.orderbooks.popleft()

    def update_trade(self, trade: TradeEvent) -> List[MarketAbuseAlert]:
        if trade.symbol != self.symbol:
            return []
        self.trades.append(trade)
        self._evict_old(trade.timestamp)
        return self.detect(trade.timestamp)

    def update_orderbook(self, ob: OrderBookSnapshot) -> List[MarketAbuseAlert]:
        if ob.symbol != self.symbol:
            return []
        self.orderbooks.append(ob)
        self._evict_old(ob.timestamp)
        return self.detect(ob.timestamp)

    @abstractmethod
    def detect(self, now: Optional[datetime] = None) -> List[MarketAbuseAlert]:
        raise NotImplementedError

    @staticmethod
    def robust_zscore(series: List[float]) -> List[float]:
        if not series:
            return []
        mu = mean(series)
        sigma = pstdev(series) if len(series) > 1 else 0.0
        if sigma == 0.0:
            return [0.0 for _ in series]
        return [(x - mu) / sigma for x in series]

