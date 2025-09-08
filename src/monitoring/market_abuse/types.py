from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class MarketAbuseType(Enum):
    PUMP_AND_DUMP = "pump_and_dump"
    SPOOFING = "spoofing"
    LAYERING = "layering"
    WASH_TRADING = "wash_trading"
    QUOTE_STUFFING = "quote_stuffing"


@dataclass
class TradeEvent:
    timestamp: datetime
    symbol: str
    price: float
    quantity: float
    side: str  # "buy" or "sell"
    exchange: Optional[str] = None
    trader_id: Optional[str] = None


@dataclass
class OrderBookSnapshot:
    timestamp: datetime
    symbol: str
    best_bid: float
    best_bid_size: float
    best_ask: float
    best_ask_size: float
    exchange: Optional[str] = None


@dataclass
class MarketAbuseAlert:
    timestamp: datetime
    symbol: str
    type: MarketAbuseType
    severity: float  # 0.0 - 1.0
    message: str
    metadata: Optional[Dict[str, float]] = None

