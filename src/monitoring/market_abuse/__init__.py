"""
Market abuse detection module: pump & dump, spoofing, layering, wash trading, quote stuffing.

Public API:
- from .types import MarketAbuseAlert, MarketAbuseType, TradeEvent, OrderBookSnapshot
- from .stream_monitor import MarketAbuseStreamMonitor
"""

from .types import MarketAbuseAlert, MarketAbuseType, TradeEvent, OrderBookSnapshot
from .stream_monitor import MarketAbuseStreamMonitor

__all__ = [
    "MarketAbuseAlert",
    "MarketAbuseType",
    "TradeEvent",
    "OrderBookSnapshot",
    "MarketAbuseStreamMonitor",
]

