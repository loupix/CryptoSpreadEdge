# Indicateurs et Features

Cette page documente les indicateurs, les features multi-timeframes, les features carnet d'ordres, la vectorisation/normalisation et le mini-backtest.

## Indicateurs (price-only)

Module: `src/ai/feature_engineering/indicators.py`

- dispersion: dispersion des prix cross-plateformes (std/mean)
- skew: skew bid-ask local (bid-ask)/mid
- latency_risk: risque basé sur l'ancienneté des timestamps
- spread_stability: stabilité du spread (1/(1+instabilité))
- intraday_volatility: std/mean des prix
- order_pressure: ratio simple volume_sell / (buy+sell)
- momentum: (last-first)/first
- trend_consistency: proportion de hausses dans la fenêtre
- spread_ratio: (ask-bid)/mid
- vol_of_vol: écart-type des volatilities glissantes de retours
- outlier_score: score 0..1 basé sur |z-score| du dernier prix
- asymmetric_latency: décalage absolu entre timestamps buy/sell, mappé 0..1
- liquidity_concentration: HHI normalisé des volumes par exchange

## Multi-timeframes (MTF)

Module: `src/ai/feature_engineering/mtf_features.py`

- `compute_mtf_bundle(...)` recalcule certains indicateurs à différents nombres de points (ex: 20, 60, 120).
- Les clés sont suffixées: `metric.p20`, `metric.p60`, etc.

## Carnet d'ordres

Module: `src/ai/feature_engineering/orderbook_features.py`

- depth_N: somme des tailles des N premiers niveaux bid/ask
- imbalance_N: bid_depth / (bid_depth + ask_depth)
- expected_slippage_{buy|sell}: slippage estimé pour un notionnel
- market_impact: |slippage_buy| + |slippage_sell|

## Vectorisation et normalisation

Module: `src/ai/feature_engineering/feature_vector.py`

- `flatten_indicator_bundle` -> dict plat {feature: value}
- `apply_normalization` -> application de `FeatureSpec` (clip + standardisation)
- `to_ordered_vector` -> (liste_noms, vecteur_valeurs)

## Scoring

Module: `src/ai/feature_engineering/scoring.py`

- `aggregate_exchange_scores`: somme pondérée par exchange (support invert/clip)
- `aggregate_global_score`: mean/max/min

## Backtest

Module: `src/ai/feature_engineering/backtest_indicators.py`

- `backtest_price_only`: mini backtest utilisant un signal simple (momentum - dispersion)

## Exemples rapides

```python
from src.ai.feature_engineering.indicators import compute_indicator_bundle
from src.ai.feature_engineering.mtf_features import compute_mtf_bundle
from src.ai.feature_engineering.feature_vector import flatten_indicator_bundle, apply_normalization, to_ordered_vector, FeatureSpec

bundle = compute_indicator_bundle(symbol, platform_prices, buy_exchange, sell_exchange, spread_series, price_history)
mtf = compute_mtf_bundle(symbol, platform_prices, buy_exchange, sell_exchange, spread_series, price_history)

flat = flatten_indicator_bundle(bundle)
specs = [FeatureSpec(name="momentum", min_value=-0.1, max_value=0.1, center=0.0, scale=0.02)]
norm = apply_normalization(flat, specs)
names, vec = to_ordered_vector(norm)
```