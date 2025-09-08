from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from .base import BaseDetector
from .types import MarketAbuseAlert, MarketAbuseType


class PumpAndDumpDetector(BaseDetector):
    """
    Heuristique simple:
    - PUMP: hausse du prix > threshold_pct sur une courte fenêtre avec explosion de volume
    - DUMP: baisse du prix > threshold_pct dans la même logique
    - Score de sévérité basé sur z-scores de variation et volume
    """

    def __init__(
        self,
        symbol: str,
        lookback: timedelta = timedelta(minutes=10),
        threshold_pct: float = 0.03,
        min_trades: int = 20,
    ) -> None:
        super().__init__(symbol, lookback)
        self.threshold_pct = threshold_pct
        self.min_trades = min_trades

    def detect(self, now: Optional[datetime] = None) -> List[MarketAbuseAlert]:
        if len(self.trades) < self.min_trades:
            return []
        prices = [t.price for t in self.trades]
        vols = [t.quantity for t in self.trades]
        if not prices:
            return []
        p0 = prices[0]
        p1 = prices[-1]
        change = (p1 - p0) / p0 if p0 != 0 else 0.0
        total_vol = sum(vols)
        avg_vol = total_vol / len(vols) if vols else 0.0
        # Détection volume inhabituel: volume moyen sur dernière minute vs lookback
        recent_window = list(self.trades)[-max(5, len(self.trades) // 5):]
        recent_vol = sum(t.quantity for t in recent_window)
        recent_avg = recent_vol / len(recent_window)
        volume_spike = (recent_avg / avg_vol) if avg_vol > 0 else 0.0

        alerts: List[MarketAbuseAlert] = []
        timestamp = (now or self.trades[-1].timestamp)

        if change >= self.threshold_pct and volume_spike >= 2.0:
            severity = min(1.0, change / self.threshold_pct * 0.5 + (min(volume_spike, 5.0) / 5.0) * 0.5)
            alerts.append(
                MarketAbuseAlert(
                    timestamp=timestamp,
                    symbol=self.symbol,
                    type=MarketAbuseType.PUMP_AND_DUMP,
                    severity=severity,
                    message=f"PUMP suspect: +{change*100:.2f}% avec pic de volume x{volume_spike:.2f}",
                    metadata={"price_change": change, "volume_spike": volume_spike},
                )
            )

        if change <= -self.threshold_pct and volume_spike >= 2.0:
            severity = min(1.0, (-change) / self.threshold_pct * 0.5 + (min(volume_spike, 5.0) / 5.0) * 0.5)
            alerts.append(
                MarketAbuseAlert(
                    timestamp=timestamp,
                    symbol=self.symbol,
                    type=MarketAbuseType.PUMP_AND_DUMP,
                    severity=severity,
                    message=f"DUMP suspect: {change*100:.2f}% avec pic de volume x{volume_spike:.2f}",
                    metadata={"price_change": change, "volume_spike": volume_spike},
                )
            )

        return alerts

