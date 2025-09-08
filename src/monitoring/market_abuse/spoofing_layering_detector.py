from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Deque, List, Optional, Tuple

from .base import BaseDetector
from .types import MarketAbuseAlert, MarketAbuseType, OrderBookSnapshot


class SpoofingLayeringDetector(BaseDetector):
    """
    Heuristique:
    - Détecte un spike soudain de taille au meilleur bid/ask (> multiplier * moyenne)
    - Puis disparition rapide (< revert_seconds) du surplus de taille
    - Génère une alerte de spoofing/layering
    """

    def __init__(
        self,
        symbol: str,
        lookback: timedelta = timedelta(minutes=5),
        size_multiplier: float = 3.0,
        revert_seconds: int = 20,
        min_ob_points: int = 20,
    ) -> None:
        super().__init__(symbol, lookback)
        self.size_multiplier = size_multiplier
        self.revert_seconds = revert_seconds
        self.min_ob_points = min_ob_points
        self.spike_state: Optional[Tuple[str, float, datetime]] = None  # side, base_size, ts

    def detect(self, now: Optional[datetime] = None) -> List[MarketAbuseAlert]:
        if len(self.orderbooks) < self.min_ob_points:
            return []
        ob_list = list(self.orderbooks)
        avg_bid = sum(o.best_bid_size for o in ob_list) / len(ob_list)
        avg_ask = sum(o.best_ask_size for o in ob_list) / len(ob_list)
        latest = ob_list[-1]
        alerts: List[MarketAbuseAlert] = []
        current_ts = (now or latest.timestamp)

        # Spike detection
        if latest.best_bid_size >= self.size_multiplier * avg_bid:
            self.spike_state = ("bid", avg_bid, current_ts)
        elif latest.best_ask_size >= self.size_multiplier * avg_ask:
            self.spike_state = ("ask", avg_ask, current_ts)

        # Reversion detection
        if self.spike_state is not None:
            side, base_size, ts_spike = self.spike_state
            if (current_ts - ts_spike).total_seconds() <= self.revert_seconds:
                if side == "bid" and latest.best_bid_size <= 1.2 * base_size:
                    alerts.append(
                        MarketAbuseAlert(
                            timestamp=current_ts,
                            symbol=self.symbol,
                            type=MarketAbuseType.SPOOFING,
                            severity=0.7,
                            message="Spike bid size suivi d'une disparition rapide (spoofing/layering possible)",
                            metadata={"side": 0.0, "multiplier": self.size_multiplier},
                        )
                    )
                    self.spike_state = None
                if side == "ask" and latest.best_ask_size <= 1.2 * base_size:
                    alerts.append(
                        MarketAbuseAlert(
                            timestamp=current_ts,
                            symbol=self.symbol,
                            type=MarketAbuseType.SPOOFING,
                            severity=0.7,
                            message="Spike ask size suivi d'une disparition rapide (spoofing/layering possible)",
                            metadata={"side": 1.0, "multiplier": self.size_multiplier},
                        )
                    )
                    self.spike_state = None
            else:
                # Expire spike state
                self.spike_state = None

        return alerts

