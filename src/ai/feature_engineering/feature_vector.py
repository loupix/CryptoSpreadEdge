from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import math

from .indicators import IndicatorResult


@dataclass
class FeatureSpec:
    name: str
    min_value: float = -math.inf
    max_value: float = math.inf
    center: float = 0.0
    scale: float = 1.0


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def normalize_value(value: float, min_value: float, max_value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    if not math.isfinite(min_value) or not math.isfinite(max_value) or max_value <= min_value:
        return value
    v = _clip(value, min_value, max_value)
    return (v - min_value) / (max_value - min_value)


def standardize_value(value: float, center: float = 0.0, scale: float = 1.0) -> float:
    if not math.isfinite(value) or scale == 0.0 or not math.isfinite(scale):
        return 0.0
    return (value - center) / scale


def flatten_indicator_bundle(bundle: Dict[str, IndicatorResult]) -> Dict[str, float]:
    flat: Dict[str, float] = {}
    for key, res in bundle.items():
        if isinstance(res, IndicatorResult):
            flat[key] = float(res.value)
        else:
            # Support d’objets nested type IndicatorResult
            try:
                flat[key] = float(getattr(res, "value", 0.0))
            except Exception:
                flat[key] = 0.0
    return flat


def apply_normalization(flat_features: Dict[str, float], specs: List[FeatureSpec]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    spec_map = {s.name: s for s in specs}
    for name, val in flat_features.items():
        spec = spec_map.get(name)
        if spec is None:
            out[name] = val
        else:
            # On applique d’abord un clip/normalization si bornes définies
            v = normalize_value(val, spec.min_value, spec.max_value) if math.isfinite(spec.min_value) and math.isfinite(spec.max_value) else val
            # Puis une standardisation optionnelle
            v = standardize_value(v, spec.center, spec.scale) if (spec.scale not in (0.0, math.inf, -math.inf)) else v
            out[name] = v
    return out


def to_ordered_vector(features: Dict[str, float]) -> Tuple[List[str], List[float]]:
    names = sorted(features.keys())
    vec = [features[n] for n in names]
    return names, vec