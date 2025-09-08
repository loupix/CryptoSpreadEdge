from __future__ import annotations

from datetime import timedelta
from typing import Iterable, List, Optional, Dict

from .pump_dump_detector import PumpAndDumpDetector
from .quote_stuffing_detector import QuoteStuffingDetector
from .spoofing_layering_detector import SpoofingLayeringDetector
from .wash_trading_detector import WashTradingDetector
from .types import MarketAbuseAlert, OrderBookSnapshot, TradeEvent
from .sinks import AlertSink, FileAlertSink, PrometheusAlertSink


class MarketAbuseStreamMonitor:
    def __init__(
        self,
        symbol: str,
        enable_pump_dump: bool = True,
        enable_spoofing: bool = True,
        enable_wash_trading: bool = True,
        enable_quote_stuffing: bool = True,
        lookback_minutes: int = 10,
        sinks: Optional[List[AlertSink]] = None,
        symbol_thresholds: Optional[Dict[str, float]] = None,
    ) -> None:
        self.symbol = symbol
        lookback = timedelta(minutes=lookback_minutes)
        self.detectors = []
        # Par défaut, écrire en fichier uniquement. Le sink Prometheus doit être injecté par l'appelant.
        self.sinks = sinks or [FileAlertSink()]
        self.symbol_thresholds = symbol_thresholds or {}
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
        alerts = self._apply_symbol_thresholds(alerts)
        self._emit(alerts)
        return alerts

    def on_orderbook(self, ob: OrderBookSnapshot) -> List[MarketAbuseAlert]:
        alerts: List[MarketAbuseAlert] = []
        for det in self.detectors:
            alerts.extend(det.update_orderbook(ob))
        alerts = self._apply_symbol_thresholds(alerts)
        self._emit(alerts)
        return alerts

    def run_offline_trades(self, trades: Iterable[TradeEvent]) -> List[MarketAbuseAlert]:
        all_alerts: List[MarketAbuseAlert] = []
        for t in trades:
            all_alerts.extend(self.on_trade(t))
        return all_alerts

    def _apply_symbol_thresholds(self, alerts: List[MarketAbuseAlert]) -> List[MarketAbuseAlert]:
        threshold = self.symbol_thresholds.get(self.symbol)
        if threshold is None:
            return alerts
        return [a for a in alerts if a.severity >= threshold]

    def _emit(self, alerts: List[MarketAbuseAlert]) -> None:
        if not alerts:
            return
        for sink in self.sinks:
            try:
                # File/Prometheus sinks sont sync; DB sink peut être async via méthode dédiée
                sink.emit(alerts)  # type: ignore[attr-defined]
            except AttributeError:
                # Sink async: ignore ici (utiliser explicitement DatabaseAlertSink.emit_async ailleurs)
                pass

