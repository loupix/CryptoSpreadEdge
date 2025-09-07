from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import math
import statistics


@dataclass
class IndicatorResult:
    value: float
    components: Dict[str, float]
    timestamp: datetime


def _safe_std(values: List[float]) -> float:
    clean = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    if len(clean) < 2:
        return 0.0
    try:
        return statistics.pstdev(clean)
    except Exception:
        return 0.0


def _safe_mean(values: List[float]) -> float:
    clean = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    if not clean:
        return 0.0
    try:
        return statistics.fmean(clean)
    except Exception:
        return sum(clean) / len(clean) if clean else 0.0


def compute_intraday_volatility(price_history: List[Dict[str, Any]], lookback_points: int = 120) -> IndicatorResult:
    series = price_history[-lookback_points:] if price_history else []
    prices = [p.get("price", 0.0) for p in series if p.get("price", 0.0) > 0]
    if len(prices) < 5:
        return IndicatorResult(0.0, {"std": 0.0, "mean": 0.0}, datetime.utcnow())
    mean_p = _safe_mean(prices)
    std_p = _safe_std(prices)
    vol = std_p / mean_p if mean_p > 0 else 0.0
    return IndicatorResult(vol, {"std": std_p, "mean": mean_p}, datetime.utcnow())


def compute_bid_ask_skew(buy_data: Dict[str, Any], sell_data: Dict[str, Any]) -> IndicatorResult:
    bid = sell_data.get("bid", 0.0)
    ask = buy_data.get("ask", 0.0)
    mid = (bid + ask) / 2 if bid > 0 and ask > 0 else 0.0
    if mid <= 0:
        return IndicatorResult(0.0, {"mid": 0.0}, datetime.utcnow())
    skew = (bid - ask) / mid
    return IndicatorResult(skew, {"mid": mid, "bid": bid, "ask": ask}, datetime.utcnow())


def compute_cross_platform_dispersion(platform_prices: Dict[str, Dict[str, Any]]) -> IndicatorResult:
    prices = [d.get("price", 0.0) for d in platform_prices.values() if d.get("price", 0.0) > 0]
    if len(prices) < 3:
        return IndicatorResult(0.0, {"std": 0.0, "mean": _safe_mean(prices)}, datetime.utcnow())
    mean_p = _safe_mean(prices)
    std_p = _safe_std(prices)
    dispersion = std_p / mean_p if mean_p > 0 else 0.0
    return IndicatorResult(dispersion, {"std": std_p, "mean": mean_p}, datetime.utcnow())


def compute_spread_stability(spread_series: List[float], lookback_points: int = 60) -> IndicatorResult:
    series = spread_series[-lookback_points:] if spread_series else []
    if len(series) < 5:
        return IndicatorResult(0.0, {"std": 0.0, "mean": 0.0}, datetime.utcnow())
    mean_s = _safe_mean(series)
    std_s = _safe_std(series)
    instability = std_s / abs(mean_s) if abs(mean_s) > 1e-9 else 1.0
    stability = 1.0 / (1.0 + instability)
    return IndicatorResult(stability, {"instability": instability, "mean": mean_s}, datetime.utcnow())


def compute_latency_risk(buy_timestamp: datetime, sell_timestamp: datetime) -> IndicatorResult:
    now = datetime.utcnow()
    age_buy = (now - buy_timestamp).total_seconds()
    age_sell = (now - sell_timestamp).total_seconds()
    age_max = max(age_buy, age_sell)
    # map 0s -> 0 risk, 60s or more -> 1 risk
    risk = max(0.0, min(1.0, age_max / 60.0))
    return IndicatorResult(risk, {"age_buy": age_buy, "age_sell": age_sell}, datetime.utcnow())


def compute_simple_order_pressure(buy_data: Dict[str, Any], sell_data: Dict[str, Any]) -> IndicatorResult:
    vol_buy = max(0.0, buy_data.get("volume", 0.0))
    vol_sell = max(0.0, sell_data.get("volume", 0.0))
    total = vol_buy + vol_sell
    if total <= 0:
        return IndicatorResult(0.5, {"buy": vol_buy, "sell": vol_sell}, datetime.utcnow())
    pressure = vol_sell / total  # 1 = pression vendeuse, 0 = acheteuse
    return IndicatorResult(pressure, {"buy": vol_buy, "sell": vol_sell}, datetime.utcnow())


def _extract_prices(price_history: List[Dict[str, Any]]) -> List[float]:
    return [p.get("price", 0.0) for p in price_history if p.get("price", 0.0) > 0]


def compute_momentum(price_history: List[Dict[str, Any]], lookback_points: int = 30) -> IndicatorResult:
    series = _extract_prices(price_history[-lookback_points:])
    if len(series) < 5:
        return IndicatorResult(0.0, {"start": 0.0, "end": 0.0}, datetime.utcnow())
    start = series[0]
    end = series[-1]
    roc = (end - start) / start if start > 0 else 0.0
    return IndicatorResult(roc, {"start": start, "end": end}, datetime.utcnow())


def compute_trend_consistency(price_history: List[Dict[str, Any]], lookback_points: int = 60) -> IndicatorResult:
    series = _extract_prices(price_history[-lookback_points:])
    if len(series) < 5:
        return IndicatorResult(0.5, {"ups": 0.0, "downs": 0.0}, datetime.utcnow())
    ups = 0
    downs = 0
    for i in range(1, len(series)):
        if series[i] > series[i - 1]:
            ups += 1
        elif series[i] < series[i - 1]:
            downs += 1
    total_moves = ups + downs
    consistency = ups / total_moves if total_moves > 0 else 0.5
    return IndicatorResult(consistency, {"ups": float(ups), "downs": float(downs)}, datetime.utcnow())


def compute_spread_ratio(buy_data: Dict[str, Any], sell_data: Dict[str, Any]) -> IndicatorResult:
    bid = sell_data.get("bid", 0.0)
    ask = buy_data.get("ask", 0.0)
    if bid <= 0 or ask <= 0:
        return IndicatorResult(0.0, {"bid": bid, "ask": ask}, datetime.utcnow())
    mid = (bid + ask) / 2
    ratio = (ask - bid) / mid if mid > 0 else 0.0
    return IndicatorResult(ratio, {"mid": mid, "bid": bid, "ask": ask}, datetime.utcnow())


def compute_vol_of_vol(price_history: List[Dict[str, Any]], lookback_points: int = 120, subwindow: int = 20) -> IndicatorResult:
    series = _extract_prices(price_history[-lookback_points:])
    if len(series) < subwindow + 5:
        return IndicatorResult(0.0, {"vov": 0.0}, datetime.utcnow())
    # returns
    rets = []
    for i in range(1, len(series)):
        if series[i - 1] > 0:
            rets.append((series[i] - series[i - 1]) / series[i - 1])
    if len(rets) < subwindow + 2:
        return IndicatorResult(0.0, {"vov": 0.0}, datetime.utcnow())
    rolling_std = []
    for i in range(subwindow, len(rets) + 1):
        window = rets[i - subwindow:i]
        rolling_std.append(_safe_std(window))
    vov = _safe_std(rolling_std)
    return IndicatorResult(vov, {"rolling_std_mean": _safe_mean(rolling_std)}, datetime.utcnow())


def compute_outlier_score(price_history: List[Dict[str, Any]], lookback_points: int = 120) -> IndicatorResult:
    series = _extract_prices(price_history[-lookback_points:])
    if len(series) < 10:
        return IndicatorResult(0.0, {"z": 0.0}, datetime.utcnow())
    mean_p = _safe_mean(series)
    std_p = _safe_std(series)
    last = series[-1]
    z = (last - mean_p) / std_p if std_p > 1e-12 else 0.0
    # Map to 0..1 score via logistic-like squash of absolute z
    score = 1.0 - (1.0 / (1.0 + abs(z)))
    return IndicatorResult(score, {"z": z, "mean": mean_p, "std": std_p, "last": last}, datetime.utcnow())


def compute_asymmetric_latency(buy_timestamp: datetime, sell_timestamp: datetime) -> IndicatorResult:
    delta = abs((buy_timestamp - sell_timestamp).total_seconds())
    score = max(0.0, min(1.0, delta / 30.0))  # 30s -> score 1
    return IndicatorResult(score, {"delta_sec": delta}, datetime.utcnow())


def compute_liquidity_concentration(platform_prices: Dict[str, Dict[str, Any]]) -> IndicatorResult:
    # Only consider real exchanges
    vols = []
    for p, d in platform_prices.items():
        if d.get("source") == "exchange":
            vol = max(0.0, float(d.get("volume", 0.0)))
            if vol > 0:
                vols.append(vol)
    if len(vols) < 2:
        return IndicatorResult(0.0, {"hhi": 0.0, "n": float(len(vols))}, datetime.utcnow())
    total = sum(vols)
    shares = [v / total for v in vols if total > 0]
    hhi = sum(s * s for s in shares)
    # Normalize HHI to 0..1 given variable N: min ~1/N, max=1, map to 0..1
    n = len(shares)
    min_hhi = 1.0 / n
    norm = (hhi - min_hhi) / (1.0 - min_hhi) if 1.0 - min_hhi > 0 else 0.0
    return IndicatorResult(norm, {"hhi": hhi, "n": float(n)}, datetime.utcnow())

def compute_indicator_bundle(
    symbol: str,
    platform_prices: Dict[str, Dict[str, Any]],
    buy_platform: str,
    sell_platform: str,
    spread_series: Optional[List[float]] = None,
    price_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, IndicatorResult]:
    """Construit un bundle d'indicateurs de base + avancés pour un symbole et une paire de plateformes.

    Ne dépend pas d'une version antérieure du bundle; tout est calculé ici.
    """
    buy_data = platform_prices.get(buy_platform, {})
    sell_data = platform_prices.get(sell_platform, {})

    # Indicateurs de base
    dispersion = compute_cross_platform_dispersion(platform_prices)
    skew = compute_bid_ask_skew(buy_data, sell_data)
    latency = compute_latency_risk(
        buy_data.get("timestamp", datetime.utcnow()),
        sell_data.get("timestamp", datetime.utcnow()),
    )
    stability = compute_spread_stability(spread_series or [])
    intraday_vol = compute_intraday_volatility(price_history or [])
    pressure = compute_simple_order_pressure(buy_data, sell_data)

    # Indicateurs avancés
    momentum = compute_momentum(price_history or [])
    trend = compute_trend_consistency(price_history or [])
    spread_ratio = compute_spread_ratio(buy_data, sell_data)
    vov = compute_vol_of_vol(price_history or [])
    outlier = compute_outlier_score(price_history or [])
    asym_latency = compute_asymmetric_latency(
        buy_data.get("timestamp", datetime.utcnow()),
        sell_data.get("timestamp", datetime.utcnow()),
    )
    liq_conc = compute_liquidity_concentration(platform_prices)

    return {
        "dispersion": dispersion,
        "skew": skew,
        "latency_risk": latency,
        "spread_stability": stability,
        "intraday_volatility": intraday_vol,
        "order_pressure": pressure,
        "momentum": momentum,
        "trend_consistency": trend,
        "spread_ratio": spread_ratio,
        "vol_of_vol": vov,
        "outlier_score": outlier,
        "asymmetric_latency": asym_latency,
        "liquidity_concentration": liq_conc,
    }