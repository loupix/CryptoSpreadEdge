"""
Modèles SQLAlchemy pour les entités de trading
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, 
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()


class OrderStatus(Enum):
    """Statut des ordres"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIALLY_FILLED = "partially_filled"


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


class PositionType(Enum):
    """Type de position"""
    LONG = "long"
    SHORT = "short"


class PositionStatus(Enum):
    """Statut des positions"""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class StrategyStatus(Enum):
    """Statut des stratégies"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"


class Order(Base):
    """Table des ordres de trading"""
    __tablename__ = 'orders'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    filled_quantity = Column(Float, default=0.0)
    average_price = Column(Float, default=0.0)
    exchange = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    meta_data = Column(JSONB, nullable=True)
    
    # Relations
    trades = relationship("Trade", back_populates="order")
    
    # Indexes
    __table_args__ = (
        Index('idx_orders_symbol_status', 'symbol', 'status'),
        Index('idx_orders_created_at', 'created_at'),
        Index('idx_orders_exchange', 'exchange'),
    )


class Position(Base):
    """Table des positions de trading"""
    __tablename__ = 'positions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(PositionType), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    status = Column(SQLEnum(PositionStatus), nullable=False, default=PositionStatus.OPEN)
    exchange = Column(String(50), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey('strategies.id'), nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_data = Column(JSONB, nullable=True)
    
    # Relations
    strategy = relationship("Strategy", back_populates="positions")
    trades = relationship("Trade", back_populates="position")
    
    # Indexes
    __table_args__ = (
        Index('idx_positions_symbol_status', 'symbol', 'status'),
        Index('idx_positions_strategy', 'strategy_id'),
        Index('idx_positions_opened_at', 'opened_at'),
    )


class Trade(Base):
    """Table des trades exécutés"""
    __tablename__ = 'trades'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(String(100), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey('positions.id'), nullable=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey('strategies.id'), nullable=True)
    exchange = Column(String(50), nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    signal_strength = Column(Float, nullable=True)
    signal_confidence = Column(Float, nullable=True)
    exit_reason = Column(String(100), nullable=True)
    meta_data = Column(JSONB, nullable=True)
    
    # Relations
    order = relationship("Order", back_populates="trades")
    position = relationship("Position", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    
    # Indexes
    __table_args__ = (
        Index('idx_trades_symbol_executed', 'symbol', 'executed_at'),
        Index('idx_trades_strategy', 'strategy_id'),
        Index('idx_trades_position', 'position_id'),
        Index('idx_trades_executed_at', 'executed_at'),
    )


class Strategy(Base):
    """Table des stratégies de trading"""
    __tablename__ = 'strategies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(StrategyStatus), nullable=False, default=StrategyStatus.INACTIVE)
    config = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    meta_data = Column(JSONB, nullable=True)
    
    # Relations
    positions = relationship("Position", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategy")
    
    # Indexes
    __table_args__ = (
        Index('idx_strategies_status', 'status'),
        Index('idx_strategies_created_at', 'created_at'),
    )


class Portfolio(Base):
    """Table de l'état du portefeuille"""
    __tablename__ = 'portfolio'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_value = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    total_fees = Column(Float, default=0.0)
    active_positions = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta_data = Column(JSONB, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_portfolio_timestamp', 'timestamp'),
    )


class AuditLog(Base):
    """Table des logs d'audit"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)  # 'order', 'position', 'trade', etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(50), nullable=False)  # 'create', 'update', 'delete', 'execute'
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta_data = Column(JSONB, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_action', 'action'),
    )


class MarketAbuseAlertRecord(Base):
    """
    Table de persistance des alertes d'abus de marché
    """
    __tablename__ = 'market_abuse_alerts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(32), nullable=False, index=True)
    alert_type = Column(String(32), nullable=False, index=True)
    severity = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    detector = Column(String(64), nullable=True)
    exchange = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    meta_data = Column(JSONB, nullable=True)

    __table_args__ = (
        Index('idx_ma_alerts_symbol_time', 'symbol', 'timestamp'),
        Index('idx_ma_alerts_type_time', 'alert_type', 'timestamp'),
        Index('idx_ma_alerts_exchange', 'exchange'),
    )