from __future__ import annotations

from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Deque, Dict


class AutoThresholdCalibrator:
    """
    Calibration simple sans labels: maintient un seuil par symbole pour viser
    une fréquence cible d'alertes dans une fenêtre glissante.

    - Si trop d'alertes: augmente le seuil
    - Si trop peu: diminue le seuil
    """

    def __init__(
        self,
        target_alerts_per_minute: float = 0.5,
        window_minutes: int = 30,
        min_threshold: float = 0.2,
        max_threshold: float = 0.95,
        adjust_step: float = 0.05,
    ) -> None:
        self.target = target_alerts_per_minute
        self.window = timedelta(minutes=window_minutes)
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.adjust_step = adjust_step
        self.symbol_thresholds: Dict[str, float] = defaultdict(lambda: 0.5)
        self.symbol_events: Dict[str, Deque[datetime]] = defaultdict(deque)

    def record_alerts(self, symbol: str, count: int, now: datetime) -> None:
        if count <= 0:
            return
        dq = self.symbol_events[symbol]
        for _ in range(count):
            dq.append(now)
        self._evict_old(symbol, now)
        self._maybe_adjust(symbol, now)

    def get_threshold(self, symbol: str) -> float:
        return float(self.symbol_thresholds[symbol])

    def _evict_old(self, symbol: str, now: datetime) -> None:
        dq = self.symbol_events[symbol]
        cutoff = now - self.window
        while dq and dq[0] < cutoff:
            dq.popleft()

    def _maybe_adjust(self, symbol: str, now: datetime) -> None:
        dq = self.symbol_events[symbol]
        minutes = max(self.window.total_seconds() / 60.0, 1.0)
        rate = len(dq) / minutes
        threshold = self.symbol_thresholds[symbol]
        if rate > self.target * 1.2:
            threshold = min(self.max_threshold, threshold + self.adjust_step)
        elif rate < self.target * 0.8:
            threshold = max(self.min_threshold, threshold - self.adjust_step)
        self.symbol_thresholds[symbol] = threshold

