"""
Types de données pour les données de marché
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class OrderSide(Enum):
    """Côté de l'ordre"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Type d'ordre"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Statut de l'ordre"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIALLY_FILLED = "partially_filled"


@dataclass
class Ticker:
    """Données de ticker"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime
    source: str = ""


@dataclass
class OrderBookEntry:
    """Entrée du carnet d'ordres"""
    price: float
    quantity: float


@dataclass
class OrderBook:
    """Carnet d'ordres"""
    symbol: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    timestamp: datetime
    source: str = ""


@dataclass
class Trade:
    """Transaction"""
    symbol: str
    price: float
    quantity: float
    side: OrderSide
    timestamp: datetime
    trade_id: str = ""
    source: str = ""


@dataclass
class MarketData:
    """Données de marché agrégées"""
    symbol: str
    ticker: Optional[Ticker] = None
    order_book: Optional[OrderBook] = None
    trades: List[Trade] = None
    timestamp: datetime = None
    source: str = ""
    
    def __post_init__(self):
        if self.trades is None:
            self.trades = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class Order:
    """Ordre de trading"""
    symbol: str
    side: OrderSide
    quantity: float
    order_type: Optional[OrderType] = None
    price: Optional[float] = None
    stop_price: Optional[float] = None
    id: str = ""
    exchange: str = ""
    type: Optional[OrderType] = None
    order_id: str = ""
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_price: float = 0.0
    timestamp: datetime = None
    source: str = ""
    
    def __post_init__(self):
        # Support alias: certains tests utilisent `id` au lieu de `order_id`
        if self.order_id == "" and self.id:
            self.order_id = self.id
        # Alias: certains tests passent `exchange` au lieu de `source`
        if not self.source and self.exchange:
            self.source = self.exchange
        # Alias: certains tests passent `type` au lieu de `order_type`
        if self.type is not None and self.order_type is None:
            self.order_type = self.type
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class Position:
    """Position de trading"""
    symbol: str
    side: OrderSide
    quantity: float
    average_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    timestamp: datetime = None
    source: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class Balance:
    """Solde de compte"""
    currency: str
    free: float
    used: float
    total: float
    timestamp: datetime = None
    source: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()