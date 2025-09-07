from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
import math


@dataclass
class OrderBookSnapshot:
    bids: List[Tuple[float, float]]  # [(price, size)] trié desc
    asks: List[Tuple[float, float]]  # [(price, size)] trié asc
    timestamp: datetime


@dataclass
class OBFeature:
    value: float
    components: Dict[str, float]
    timestamp: datetime


def _sum_sizes(levels: List[Tuple[float, float]], max_levels: Optional[int] = None) -> float:
    if max_levels is not None:
        levels = levels[:max_levels]
    return sum(max(0.0, float(sz)) for _, sz in levels)


def compute_depth(snapshot: OrderBookSnapshot, levels: int = 5) -> OBFeature:
    bid_depth = _sum_sizes(snapshot.bids, levels)
    ask_depth = _sum_sizes(snapshot.asks, levels)
    total = bid_depth + ask_depth
    return OBFeature(
        value=total,
        components={"bid_depth": bid_depth, "ask_depth": ask_depth},
        timestamp=snapshot.timestamp,
    )


def compute_imbalance(snapshot: OrderBookSnapshot, levels: int = 5) -> OBFeature:
    bid_depth = _sum_sizes(snapshot.bids, levels)
    ask_depth = _sum_sizes(snapshot.asks, levels)
    total = bid_depth + ask_depth
    if total <= 0:
        val = 0.5
    else:
        val = bid_depth / total  # 1 = fortement acheteur, 0 = fortement vendeur
    return OBFeature(
        value=val,
        components={"bid_depth": bid_depth, "ask_depth": ask_depth},
        timestamp=snapshot.timestamp,
    )


def compute_expected_slippage(snapshot: OrderBookSnapshot, side: str, notional: float, max_levels: int = 20) -> OBFeature:
    # side: "buy" -> on traverse le ask; "sell" -> on traverse le bid
    remaining = max(0.0, float(notional))
    cost = 0.0
    qty_accum = 0.0

    if side == "buy":
        levels = snapshot.asks[:max_levels]
    else:
        levels = snapshot.bids[:max_levels]

    for price, size in levels:
        level_notional = max(0.0, float(size)) * float(price)
        if level_notional >= remaining:
            trade_qty = remaining / float(price)
            cost += trade_qty * float(price)
            qty_accum += trade_qty
            remaining = 0.0
            break
        else:
            cost += level_notional
            qty_accum += float(size)
            remaining -= level_notional

    if qty_accum <= 0.0:
        return OBFeature(0.0, {"filled": 0.0, "mid": 0.0}, snapshot.timestamp)

    avg_fill_price = cost / qty_accum
    # mid approximatif
    best_bid = snapshot.bids[0][0] if snapshot.bids else 0.0
    best_ask = snapshot.asks[0][0] if snapshot.asks else 0.0
    mid = (best_bid + best_ask) / 2.0 if best_bid > 0 and best_ask > 0 else best_bid or best_ask

    slippage = (avg_fill_price - mid) / mid if mid > 0 else 0.0
    if side == "sell":
        slippage = (mid - avg_fill_price) / mid if mid > 0 else 0.0

    filled_notional = cost
    return OBFeature(
        value=slippage,
        components={"avg_fill": avg_fill_price, "mid": mid, "filled_notional": filled_notional, "qty": qty_accum},
        timestamp=snapshot.timestamp,
    )


def compute_simple_market_impact(snapshot: OrderBookSnapshot, notional: float, max_levels: int = 20) -> OBFeature:
    buy_slip = compute_expected_slippage(snapshot, "buy", notional, max_levels).value
    sell_slip = compute_expected_slippage(snapshot, "sell", notional, max_levels).value
    impact = abs(buy_slip) + abs(sell_slip)
    return OBFeature(
        value=impact,
        components={"buy_slippage": buy_slip, "sell_slippage": sell_slip},
        timestamp=snapshot.timestamp,
    )


def compute_orderbook_bundle(snapshot: OrderBookSnapshot, notional_usd: float = 1000.0) -> Dict[str, OBFeature]:
    depth5 = compute_depth(snapshot, 5)
    depth10 = compute_depth(snapshot, 10)
    imb5 = compute_imbalance(snapshot, 5)
    imb10 = compute_imbalance(snapshot, 10)
    slip_buy = compute_expected_slippage(snapshot, "buy", notional_usd, 20)
    slip_sell = compute_expected_slippage(snapshot, "sell", notional_usd, 20)
    impact = compute_simple_market_impact(snapshot, notional_usd, 20)
    return {
        "depth_5": depth5,
        "depth_10": depth10,
        "imbalance_5": imb5,
        "imbalance_10": imb10,
        "expected_slippage_buy": slip_buy,
        "expected_slippage_sell": slip_sell,
        "market_impact": impact,
    }