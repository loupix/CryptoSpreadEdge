from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any

from ...ai.feature_engineering.indicators import compute_indicator_bundle


router = APIRouter(prefix="/indicators", tags=["indicators"])


class IndicatorResponse(BaseModel):
    symbol: str
    buy_platform: str
    sell_platform: str
    indicators: Dict[str, float]


@router.get("/bundle", response_model=IndicatorResponse)
async def get_indicator_bundle(
    symbol: str = Query(..., description="Symbole, ex: BTC"),
    buy_platform: str = Query("binance"),
    sell_platform: str = Query("okx"),
):
    try:
        # Import tardif pour éviter les imports lourds au chargement du module
        from ...ai.feature_engineering.loaders import (
            load_platform_prices,
            load_price_history,
            load_spread_series,
        )

        platform_prices = await load_platform_prices(symbol)
        if buy_platform not in platform_prices or sell_platform not in platform_prices:
            raise HTTPException(404, detail="Plateformes non disponibles pour ce symbole")

        price_history = await load_price_history(symbol)
        spread_series = await load_spread_series(symbol, buy_platform, sell_platform)

        bundle = compute_indicator_bundle(
            symbol, platform_prices, buy_platform, sell_platform, spread_series, price_history
        )
        values = {k: float(v.value) for k, v in bundle.items()}
        return IndicatorResponse(symbol=symbol, buy_platform=buy_platform, sell_platform=sell_platform, indicators=values)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))