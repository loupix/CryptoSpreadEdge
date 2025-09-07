from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any, Optional

from .indicators import (
    compute_indicator_bundle,
    IndicatorResult,
    compute_intraday_volatility,
    compute_vol_of_vol,
    compute_momentum,
    compute_trend_consistency,
)


def _safe_suffix(points: int) -> str:
    return f"p{points}"


def compute_mtf_bundle(
    symbol: str,
    platform_prices: Dict[str, Dict[str, Any]],
    buy_platform: str,
    sell_platform: str,
    spread_series: Optional[List[float]] = None,
    price_history: Optional[List[Dict[str, Any]]] = None,
    timeframes_points: Optional[List[int]] = None,
) -> Dict[str, IndicatorResult | Dict[str, IndicatorResult]]:
    """
    Calcule un bundle multi-timeframes en utilisant différents nombres de points.
    Les timeframes sont exprimés en points d'historique (pas en minutes).
    """
    if timeframes_points is None:
        timeframes_points = [20, 60, 120, 240]

    # Bundle de base sans suffixe (lookback par défaut interne aux fonctions)
    base = compute_indicator_bundle(
        symbol,
        platform_prices,
        buy_platform,
        sell_platform,
        spread_series=spread_series,
        price_history=price_history,
    )

    mtf: Dict[str, Any] = {"base": base}

    # Déclinaisons multi-timeframes pour quelques indicateurs clés
    for points in timeframes_points:
        suffix = _safe_suffix(points)
        # Limiter les séries
        ph = (price_history or [])[-points:]
        ss = (spread_series or [])[-points:]

        # Recalcule sélectif pour certaines métriques sensibles au lookback
        vol = compute_intraday_volatility(ph, lookback_points=points)
        vov = compute_vol_of_vol(ph, lookback_points=points, subwindow=max(5, min(points // 4, 50)))
        mom = compute_momentum(ph, lookback_points=points)
        trend = compute_trend_consistency(ph, lookback_points=points)

        mtf[f"intraday_volatility.{suffix}"] = vol
        mtf[f"vol_of_vol.{suffix}"] = vov
        mtf[f"momentum.{suffix}"] = mom
        mtf[f"trend_consistency.{suffix}"] = trend

    return mtf