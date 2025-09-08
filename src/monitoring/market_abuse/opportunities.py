from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from .types import MarketAbuseAlert, MarketAbuseType


@dataclass
class Opportunity:
    timestamp: datetime
    symbol: str
    kind: str
    confidence: float
    rationale: str


def opportunities_from_alert(alert: MarketAbuseAlert) -> List[Opportunity]:
    opps: List[Opportunity] = []
    # Heuristique minimale: les manipulations peuvent annoncer une volatilité exploitable
    if alert.type == MarketAbuseType.PUMP_AND_DUMP:
        direction = "long" if "PUMP" in alert.message else "short"
        opps.append(
            Opportunity(
                timestamp=alert.timestamp,
                symbol=alert.symbol,
                kind=f"volatility_breakout_{direction}",
                confidence=min(1.0, 0.5 + 0.5 * alert.severity),
                rationale=f"Signal {alert.type.value} (sev={alert.severity:.2f})",
            )
        )
    elif alert.type == MarketAbuseType.SPOOFING:
        opps.append(
            Opportunity(
                timestamp=alert.timestamp,
                symbol=alert.symbol,
                kind="mean_reversion",
                confidence=min(1.0, 0.4 + 0.6 * alert.severity),
                rationale=f"Orderbook anomaly {alert.type.value}",
            )
        )
    elif alert.type == MarketAbuseType.QUOTE_STUFFING:
        opps.append(
            Opportunity(
                timestamp=alert.timestamp,
                symbol=alert.symbol,
                kind="latency_arbitrage",
                confidence=min(1.0, 0.3 + 0.7 * alert.severity),
                rationale=f"Microstructure stress {alert.type.value}",
            )
        )
    elif alert.type == MarketAbuseType.WASH_TRADING:
        opps.append(
            Opportunity(
                timestamp=alert.timestamp,
                symbol=alert.symbol,
                kind="liquidity_caution",
                confidence=min(1.0, 0.3 + 0.7 * alert.severity),
                rationale=f"Liquidity distortion {alert.type.value}",
            )
        )
    return opps

