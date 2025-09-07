from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List
import math

from .indicators import IndicatorResult


@dataclass
class Weight:
    name: str
    weight: float
    invert: bool = False  # si True, on utilise -valeur normalisée
    min_clip: float = -math.inf
    max_clip: float = math.inf


def _get_value(obj: Any) -> float:
    if isinstance(obj, IndicatorResult):
        return float(obj.value)
    try:
        return float(getattr(obj, "value", 0.0))
    except Exception:
        return 0.0


def aggregate_exchange_scores(exchange_to_bundle: Dict[str, Dict[str, Any]], weights: List[Weight]) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for exch, bundle in exchange_to_bundle.items():
        score = 0.0
        for w in weights:
            val = _get_value(bundle.get(w.name))
            # clamp
            if math.isfinite(w.min_clip) and val < w.min_clip:
                val = w.min_clip
            if math.isfinite(w.max_clip) and val > w.max_clip:
                val = w.max_clip
            if w.invert:
                val = -val
            score += w.weight * val
        scores[exch] = score
    return scores


def aggregate_global_score(exchange_scores: Dict[str, float], method: str = "mean") -> float:
    if not exchange_scores:
        return 0.0
    vals = list(exchange_scores.values())
    if method == "max":
        return max(vals)
    if method == "min":
        return min(vals)
    # mean par défaut
    return sum(vals) / len(vals)