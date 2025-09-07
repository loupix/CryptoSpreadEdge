from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import math

from .indicators import compute_indicator_bundle


@dataclass
class BacktestConfig:
    entry_threshold: float = 0.0  # seuil de momentum pour entrer
    max_positions: int = 1
    take_profit: float = 0.005   # 0.5%
    stop_loss: float = 0.005     # 0.5%


@dataclass
class BacktestResult:
    trades: int
    wins: int
    losses: int
    pnl: float
    avg_return: float


def simple_signal_from_bundle(bundle: Dict[str, Any]) -> float:
    # Exemple: combinaison momentum - dispersion (on préfère momentum haut, dispersion basse)
    mom = float(bundle.get("momentum", 0.0).value if hasattr(bundle.get("momentum"), "value") else 0.0)
    disp = float(bundle.get("dispersion", 0.0).value if hasattr(bundle.get("dispersion"), "value") else 0.0)
    score = mom - disp
    return score


def backtest_price_only(
    symbol: str,
    platform_prices_seq: List[Dict[str, Dict[str, Any]]],
    buy_platform: str,
    sell_platform: str,
    price_history_seq: List[List[Dict[str, Any]]],
    spread_series_seq: List[List[float]],
    config: Optional[BacktestConfig] = None,
) -> BacktestResult:
    cfg = config or BacktestConfig()

    in_position = False
    entry_price = 0.0
    trades = 0
    wins = 0
    losses = 0
    pnl = 0.0
    returns: List[float] = []

    for t in range(len(platform_prices_seq)):
        platform_prices = platform_prices_seq[t]
        price_history = price_history_seq[t] if t < len(price_history_seq) else []
        spread_series = spread_series_seq[t] if t < len(spread_series_seq) else []

        bundle = compute_indicator_bundle(
            symbol=symbol,
            platform_prices=platform_prices,
            buy_platform=buy_platform,
            sell_platform=sell_platform,
            spread_series=spread_series,
            price_history=price_history,
        )
        score = simple_signal_from_bundle(bundle)

        mid_buy = (platform_prices.get(buy_platform, {}).get("bid", 0.0) + platform_prices.get(buy_platform, {}).get("ask", 0.0)) / 2.0
        mid_sell = (platform_prices.get(sell_platform, {}).get("bid", 0.0) + platform_prices.get(sell_platform, {}).get("ask", 0.0)) / 2.0
        mid = mid_sell if mid_sell > 0 else mid_buy
        if mid <= 0:
            continue

        if not in_position and score > cfg.entry_threshold:
            in_position = True
            entry_price = mid
            trades += 1
            continue

        if in_position:
            ret = (mid - entry_price) / entry_price
            # TP/SL
            if ret >= cfg.take_profit:
                pnl += ret
                returns.append(ret)
                wins += 1
                in_position = False
            elif ret <= -cfg.stop_loss:
                pnl += ret
                returns.append(ret)
                losses += 1
                in_position = False

    avg_ret = sum(returns) / len(returns) if returns else 0.0
    return BacktestResult(trades=trades, wins=wins, losses=losses, pnl=pnl, avg_return=avg_ret)