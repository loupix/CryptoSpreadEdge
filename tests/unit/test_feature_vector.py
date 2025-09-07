from src.ai.feature_engineering.feature_vector import (
    flatten_indicator_bundle,
    apply_normalization,
    to_ordered_vector,
    FeatureSpec,
)
from src.ai.feature_engineering.indicators import IndicatorResult
from datetime import datetime


def test_flatten_and_normalize():
    bundle = {
        "a": IndicatorResult(10.0, {}, datetime.utcnow()),
        "b": IndicatorResult(0.5, {}, datetime.utcnow()),
    }
    flat = flatten_indicator_bundle(bundle)
    specs = [
        FeatureSpec(name="a", min_value=0.0, max_value=20.0),
        FeatureSpec(name="b", min_value=0.0, max_value=1.0, center=0.5, scale=0.25),
    ]
    norm = apply_normalization(flat, specs)
    names, vec = to_ordered_vector(norm)

    assert set(names) == {"a", "b"}
    # a normalisé 0..1 => 10 -> 0.5
    assert abs(norm["a"] - 0.5) < 1e-6
    # b centré/standardisé => (0.5-0.5)/0.25 -> 0
    assert abs(norm["b"] - 0.0) < 1e-6