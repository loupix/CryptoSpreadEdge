from __future__ import annotations

from datetime import timedelta
from typing import Iterable, List, Optional

from .pump_dump_detector import PumpAndDumpDetector
from .quote_stuffing_detector import QuoteStuffingDetector
from .spoofing_layering_detector import SpoofingLayeringDetector
from .wash_trading_detector import WashTradingDetector
from .types import MarketAbuseAlert, OrderBookSnapshot, TradeEvent


class MarketAbuseStreamMonitor:
    def __init__(
        self,
        symbol: str,
        enable_pump_dump: bool = True,
        enable_spoofing: bool = True,
        enable_wash_trading: bool = True,
        enable_quote_stuffing: bool = True,
        lookback_minutes: int = 10,
    ) -> None:
        self.symbol = symbol
        lookback = timedelta(minutes=lookback_minutes)
        self.detectors = []
        if enable_pump_dump:
            self.detectors.append(PumpAndDumpDetector(symbol=symbol, lookback=lookback))
        if enable_spoofing:
            self.detectors.append(SpoofingLayeringDetector(symbol=symbol, lookback=lookback))
        if enable_wash_trading:
            self.detectors.append(WashTradingDetector(symbol=symbol, lookback=lookback))
        if enable_quote_stuffing:
            self.detectors.append(QuoteStuffingDetector(symbol=symbol, lookback=lookback))

    def on_trade(self, trade: TradeEvent) -> List[MarketAbuseAlert]:
        alerts: List[MarketAbuseAlert] = []
        for det in self.detectors:
            alerts.extend(det.update_trade(trade))
        return alerts

    def on_orderbook(self, ob: OrderBookSnapshot) -> List[MarketAbuseAlert]:
        alerts: List[MarketAbuseAlert] = []
        for det in self.detectors:
            alerts.extend(det.update_orderbook(ob))
        return alerts

    def run_offline_trades(self, trades: Iterable[TradeEvent]) -> List[MarketAbuseAlert]:
        all_alerts: List[MarketAbuseAlert] = []
        for t in trades:
            all_alerts.extend(self.on_trade(t))
        return all_alerts

