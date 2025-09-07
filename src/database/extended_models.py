"""
Modèles étendus pour couvrir tous les aspects de CryptoSpreadEdge
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, 
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, INET
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()


# Enums étendus
class ExchangeType(Enum):
    """Types d'exchanges"""
    CENTRALIZED = "centralized"
    DECENTRALIZED = "decentralized"
    HYBRID = "hybrid"


class ExchangeStatus(Enum):
    """Statut des exchanges"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"
    ERROR = "error"


class UserRole(Enum):
    """Rôles utilisateurs"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"
    ANALYST = "analyst"
    AUDITOR = "auditor"


class UserStatus(Enum):
    """Statut des utilisateurs"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class AlertType(Enum):
    """Types d'alertes"""
    PRICE = "price"
    VOLUME = "volume"
    RISK = "risk"
    SYSTEM = "system"
    TRADING = "trading"
    PERFORMANCE = "performance"


class AlertSeverity(Enum):
    """Sévérité des alertes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Canaux de notification"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    PUSH = "push"


class TradingSessionStatus(Enum):
    """Statut des sessions de trading"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


# Modèles étendus
class Exchange(Base):
    """Table des exchanges supportés"""
    __tablename__ = 'exchanges'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    exchange_type = Column(SQLEnum(ExchangeType), nullable=False)
    status = Column(SQLEnum(ExchangeStatus), nullable=False, default=ExchangeStatus.ACTIVE)
    api_base_url = Column(String(255), nullable=False)
    websocket_url = Column(String(255), nullable=True)
    supported_pairs = Column(ARRAY(String), nullable=True)
    trading_fees = Column(JSONB, nullable=True)  # Structure: {"maker": 0.001, "taker": 0.001}
    withdrawal_fees = Column(JSONB, nullable=True)
    limits = Column(JSONB, nullable=True)  # Limites de trading, retrait, etc.
    features = Column(ARRAY(String), nullable=True)  # ["spot", "futures", "margin", "options"]
    countries = Column(ARRAY(String), nullable=True)
    is_regulated = Column(Boolean, default=False)
    regulation_authorities = Column(ARRAY(String), nullable=True)
    kyc_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relations
    api_keys = relationship("ExchangeAPIKey", back_populates="exchange")
    trading_sessions = relationship("TradingSession", back_populates="exchange")
    orders = relationship("Order", back_populates="exchange_rel")
    positions = relationship("Position", back_populates="exchange_rel")
    trades = relationship("Trade", back_populates="exchange_rel")
    
    # Indexes
    __table_args__ = (
        Index('idx_exchanges_status', 'status'),
        Index('idx_exchanges_type', 'exchange_type'),
        Index('idx_exchanges_features', 'features', postgresql_using='gin'),
    )


class User(Base):
    """Table des utilisateurs"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.TRADER)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relations
    api_keys = relationship("ExchangeAPIKey", back_populates="user")
    trading_sessions = relationship("TradingSession", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    portfolio_snapshots = relationship("Portfolio", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role'),
        Index('idx_users_status', 'status'),
        Index('idx_users_last_login', 'last_login'),
    )


class ExchangeAPIKey(Base):
    """Table des clés API des exchanges"""
    __tablename__ = 'exchange_api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    exchange_id = Column(UUID(as_uuid=True), ForeignKey('exchanges.id'), nullable=False)
    name = Column(String(100), nullable=False)  # Nom donné par l'utilisateur
    api_key = Column(String(255), nullable=False)  # Chiffré
    secret_key = Column(String(255), nullable=True)  # Chiffré
    passphrase = Column(String(255), nullable=True)  # Chiffré (pour Coinbase)
    is_active = Column(Boolean, default=True)
    permissions = Column(ARRAY(String), nullable=True)  # ["read", "trade", "withdraw"]
    ip_whitelist = Column(ARRAY(INET), nullable=True)
    rate_limit = Column(Integer, nullable=True)  # Limite de requêtes par minute
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="api_keys")
    exchange = relationship("Exchange", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_keys_user_exchange', 'user_id', 'exchange_id'),
        Index('idx_api_keys_active', 'is_active'),
        Index('idx_api_keys_last_used', 'last_used'),
        UniqueConstraint('user_id', 'exchange_id', 'name', name='uq_user_exchange_key_name'),
    )


class TradingSession(Base):
    """Table des sessions de trading"""
    __tablename__ = 'trading_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    exchange_id = Column(UUID(as_uuid=True), ForeignKey('exchanges.id'), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey('strategies.id'), nullable=True)
    name = Column(String(100), nullable=False)
    status = Column(SQLEnum(TradingSessionStatus), nullable=False, default=TradingSessionStatus.ACTIVE)
    config = Column(JSONB, nullable=True)  # Configuration de la session
    initial_capital = Column(Float, nullable=False)
    current_capital = Column(Float, nullable=False)
    total_pnl = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="trading_sessions")
    exchange = relationship("Exchange", back_populates="trading_sessions")
    strategy = relationship("Strategy", back_populates="trading_sessions")
    orders = relationship("Order", back_populates="trading_session")
    positions = relationship("Position", back_populates="trading_session")
    trades = relationship("Trade", back_populates="trading_session")
    
    # Indexes
    __table_args__ = (
        Index('idx_trading_sessions_user', 'user_id'),
        Index('idx_trading_sessions_exchange', 'exchange_id'),
        Index('idx_trading_sessions_status', 'status'),
        Index('idx_trading_sessions_started', 'started_at'),
    )


class Alert(Base):
    """Table des alertes"""
    __tablename__ = 'alerts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    symbol = Column(String(20), nullable=True)
    condition = Column(JSONB, nullable=False)  # Condition de déclenchement
    is_active = Column(Boolean, default=True)
    triggered_count = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)
    cooldown_seconds = Column(Integer, default=300)  # Cooldown entre déclenchements
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert")
    
    # Indexes
    __table_args__ = (
        Index('idx_alerts_user', 'user_id'),
        Index('idx_alerts_type', 'alert_type'),
        Index('idx_alerts_severity', 'severity'),
        Index('idx_alerts_symbol', 'symbol'),
        Index('idx_alerts_active', 'is_active'),
    )


class Notification(Base):
    """Table des notifications"""
    __tablename__ = 'notifications'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    alert_id = Column(UUID(as_uuid=True), ForeignKey('alerts.id'), nullable=True)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="notifications")
    alert = relationship("Alert", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index('idx_notifications_user', 'user_id'),
        Index('idx_notifications_channel', 'channel'),
        Index('idx_notifications_sent', 'is_sent'),
        Index('idx_notifications_created', 'created_at'),
    )


class MarketData(Base):
    """Table des données de marché historiques"""
    __tablename__ = 'market_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    exchange_id = Column(UUID(as_uuid=True), ForeignKey('exchanges.id'), nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=True)
    trade_count = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relations
    exchange = relationship("Exchange")
    
    # Indexes
    __table_args__ = (
        Index('idx_market_data_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_market_data_exchange_timestamp', 'exchange_id', 'timestamp'),
        Index('idx_market_data_timeframe', 'timeframe'),
        UniqueConstraint('symbol', 'exchange_id', 'timeframe', 'timestamp', name='uq_market_data_unique'),
    )


class TechnicalIndicator(Base):
    """Table des indicateurs techniques"""
    __tablename__ = 'technical_indicators'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    indicator_name = Column(String(50), nullable=False)  # RSI, MACD, BB, etc.
    indicator_type = Column(String(50), nullable=False)  # momentum, trend, volatility, etc.
    value = Column(Float, nullable=False)
    parameters = Column(JSONB, nullable=True)  # Paramètres de l'indicateur
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_indicators_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_indicators_name', 'indicator_name'),
        Index('idx_indicators_type', 'indicator_type'),
        Index('idx_indicators_timeframe', 'timeframe'),
    )


class RiskEvent(Base):
    """Table des événements de risque"""
    __tablename__ = 'risk_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey('trading_sessions.id'), nullable=True)
    event_type = Column(String(50), nullable=False)  # max_drawdown, position_size, etc.
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    symbol = Column(String(20), nullable=True)
    current_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Relations
    user = relationship("User", foreign_keys=[user_id])
    trading_session = relationship("TradingSession")
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_risk_events_user', 'user_id'),
        Index('idx_risk_events_session', 'trading_session_id'),
        Index('idx_risk_events_type', 'event_type'),
        Index('idx_risk_events_severity', 'severity'),
        Index('idx_risk_events_resolved', 'is_resolved'),
        Index('idx_risk_events_created', 'created_at'),
    )


class SystemMetric(Base):
    """Table des métriques système"""
    __tablename__ = 'system_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    value = Column(Float, nullable=False)
    labels = Column(JSONB, nullable=True)  # Labels Prometheus-style
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_system_metrics_name_timestamp', 'metric_name', 'timestamp'),
        Index('idx_system_metrics_type', 'metric_type'),
        Index('idx_system_metrics_timestamp', 'timestamp'),
    )


# Mise à jour des modèles existants pour ajouter les relations
class Order(Base):
    """Table des ordres de trading (mise à jour)"""
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
    exchange_id = Column(UUID(as_uuid=True), ForeignKey('exchanges.id'), nullable=True)
    source = Column(String(50), nullable=False)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey('trading_sessions.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    metadata = Column(JSONB, nullable=True)
    
    # Relations étendues
    exchange_rel = relationship("Exchange", back_populates="orders")
    trading_session = relationship("TradingSession", back_populates="orders")
    trades = relationship("Trade", back_populates="order")
    
    # Indexes
    __table_args__ = (
        Index('idx_orders_symbol_status', 'symbol', 'status'),
        Index('idx_orders_created_at', 'created_at'),
        Index('idx_orders_exchange', 'exchange'),
        Index('idx_orders_trading_session', 'trading_session_id'),
    )


class Position(Base):
    """Table des positions de trading (mise à jour)"""
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
    exchange_id = Column(UUID(as_uuid=True), ForeignKey('exchanges.id'), nullable=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey('strategies.id'), nullable=True)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey('trading_sessions.id'), nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relations étendues
    strategy = relationship("Strategy", back_populates="positions")
    exchange_rel = relationship("Exchange", back_populates="positions")
    trading_session = relationship("TradingSession", back_populates="positions")
    trades = relationship("Trade", back_populates="position")
    
    # Indexes
    __table_args__ = (
        Index('idx_positions_symbol_status', 'symbol', 'status'),
        Index('idx_positions_strategy', 'strategy_id'),
        Index('idx_positions_exchange', 'exchange_id'),
        Index('idx_positions_trading_session', 'trading_session_id'),
        Index('idx_positions_opened_at', 'opened_at'),
    )


class Trade(Base):
    """Table des trades exécutés (mise à jour)"""
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
    exchange_id = Column(UUID(as_uuid=True), ForeignKey('exchanges.id'), nullable=True)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey('trading_sessions.id'), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    signal_strength = Column(Float, nullable=True)
    signal_confidence = Column(Float, nullable=True)
    exit_reason = Column(String(100), nullable=True)
    metadata = Column(JSONB, nullable=True)
    
    # Relations étendues
    order = relationship("Order", back_populates="trades")
    position = relationship("Position", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    exchange_rel = relationship("Exchange", back_populates="trades")
    trading_session = relationship("TradingSession", back_populates="trades")
    
    # Indexes
    __table_args__ = (
        Index('idx_trades_symbol_executed', 'symbol', 'executed_at'),
        Index('idx_trades_strategy', 'strategy_id'),
        Index('idx_trades_position', 'position_id'),
        Index('idx_trades_exchange', 'exchange_id'),
        Index('idx_trades_trading_session', 'trading_session_id'),
        Index('idx_trades_executed_at', 'executed_at'),
    )


class Strategy(Base):
    """Table des stratégies de trading (mise à jour)"""
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
    metadata = Column(JSONB, nullable=True)
    
    # Relations étendues
    positions = relationship("Position", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategy")
    trading_sessions = relationship("TradingSession", back_populates="strategy")
    
    # Indexes
    __table_args__ = (
        Index('idx_strategies_status', 'status'),
        Index('idx_strategies_created_at', 'created_at'),
    )


class Portfolio(Base):
    """Table de l'état du portefeuille (mise à jour)"""
    __tablename__ = 'portfolio'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    trading_session_id = Column(UUID(as_uuid=True), ForeignKey('trading_sessions.id'), nullable=True)
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
    metadata = Column(JSONB, nullable=True)
    
    # Relations étendues
    user = relationship("User", back_populates="portfolio_snapshots")
    trading_session = relationship("TradingSession")
    
    # Indexes
    __table_args__ = (
        Index('idx_portfolio_user', 'user_id'),
        Index('idx_portfolio_trading_session', 'trading_session_id'),
        Index('idx_portfolio_timestamp', 'timestamp'),
    )