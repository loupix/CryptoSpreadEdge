"""
Repositories étendus pour toutes les entités de CryptoSpreadEdge
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, desc, asc, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from .extended_models import (
    Exchange, User, ExchangeAPIKey, TradingSession, Alert, Notification,
    MarketData, TechnicalIndicator, RiskEvent, SystemMetric,
    Order, Position, Trade, Strategy, Portfolio
)
from .extended_models import (
    ExchangeType, ExchangeStatus, UserRole, UserStatus, AlertType, AlertSeverity,
    NotificationChannel, TradingSessionStatus, OrderStatus, PositionStatus, StrategyStatus
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """Repository de base avec opérations communes"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def _log_audit(self, entity_type: str, entity_id: str, action: str, 
                        old_values: Dict = None, new_values: Dict = None, 
                        user_id: str = None, metadata: Dict = None):
        """Enregistre un log d'audit"""
        try:
            from .models import AuditLog
            audit_log = AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                user_id=user_id,
                metadata=metadata
            )
            self.session.add(audit_log)
        except Exception as e:
            logger.error(f"Erreur log audit: {e}")


class ExchangeRepository(BaseRepository):
    """Repository pour les exchanges"""
    
    async def create(self, exchange_data: Dict[str, Any]) -> Exchange:
        """Crée un nouvel exchange"""
        exchange = Exchange(**exchange_data)
        self.session.add(exchange)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="exchange",
            entity_id=str(exchange.id),
            action="create",
            new_values=exchange_data
        )
        
        return exchange
    
    async def get_by_id(self, exchange_id: str) -> Optional[Exchange]:
        """Récupère un exchange par ID"""
        result = await self.session.execute(
            select(Exchange).where(Exchange.id == exchange_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Exchange]:
        """Récupère un exchange par nom"""
        result = await self.session.execute(
            select(Exchange).where(Exchange.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_active_exchanges(self) -> List[Exchange]:
        """Récupère les exchanges actifs"""
        result = await self.session.execute(
            select(Exchange).where(Exchange.status == ExchangeStatus.ACTIVE)
        )
        return result.scalars().all()
    
    async def get_by_type(self, exchange_type: ExchangeType) -> List[Exchange]:
        """Récupère les exchanges par type"""
        result = await self.session.execute(
            select(Exchange).where(Exchange.exchange_type == exchange_type)
        )
        return result.scalars().all()
    
    async def update_status(self, exchange_id: str, status: ExchangeStatus) -> bool:
        """Met à jour le statut d'un exchange"""
        try:
            await self.session.execute(
                update(Exchange)
                .where(Exchange.id == exchange_id)
                .values(status=status, updated_at=datetime.utcnow())
            )
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour statut exchange {exchange_id}: {e}")
            return False
    
    async def get_exchanges_with_features(self, features: List[str]) -> List[Exchange]:
        """Récupère les exchanges supportant certaines fonctionnalités"""
        result = await self.session.execute(
            select(Exchange).where(Exchange.features.overlap(features))
        )
        return result.scalars().all()


class UserRepository(BaseRepository):
    """Repository pour les utilisateurs"""
    
    async def create(self, user_data: Dict[str, Any]) -> User:
        """Crée un nouvel utilisateur"""
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="user",
            entity_id=str(user.id),
            action="create",
            new_values=user_data
        )
        
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Récupère un utilisateur par nom d'utilisateur"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_active_users(self) -> List[User]:
        """Récupère les utilisateurs actifs"""
        result = await self.session.execute(
            select(User).where(User.status == UserStatus.ACTIVE)
        )
        return result.scalars().all()
    
    async def update_last_login(self, user_id: str) -> bool:
        """Met à jour la dernière connexion"""
        try:
            await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    last_login=datetime.utcnow(),
                    login_count=User.login_count + 1,
                    failed_login_attempts=0
                )
            )
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour dernière connexion {user_id}: {e}")
            return False
    
    async def increment_failed_login(self, user_id: str) -> bool:
        """Incrémente le compteur de tentatives de connexion échouées"""
        try:
            await self.session.execute(
                update(User)
                .where(User.id == user_id)
                .values(failed_login_attempts=User.failed_login_attempts + 1)
            )
            return True
        except Exception as e:
            logger.error(f"Erreur incrément échecs connexion {user_id}: {e}")
            return False


class ExchangeAPIKeyRepository(BaseRepository):
    """Repository pour les clés API des exchanges"""
    
    async def create(self, api_key_data: Dict[str, Any]) -> ExchangeAPIKey:
        """Crée une nouvelle clé API"""
        api_key = ExchangeAPIKey(**api_key_data)
        self.session.add(api_key)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="api_key",
            entity_id=str(api_key.id),
            action="create",
            new_values=api_key_data
        )
        
        return api_key
    
    async def get_by_id(self, api_key_id: str) -> Optional[ExchangeAPIKey]:
        """Récupère une clé API par ID"""
        result = await self.session.execute(
            select(ExchangeAPIKey)
            .options(joinedload(ExchangeAPIKey.user), joinedload(ExchangeAPIKey.exchange))
            .where(ExchangeAPIKey.id == api_key_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(self, user_id: str) -> List[ExchangeAPIKey]:
        """Récupère les clés API d'un utilisateur"""
        result = await self.session.execute(
            select(ExchangeAPIKey)
            .options(joinedload(ExchangeAPIKey.exchange))
            .where(ExchangeAPIKey.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_active_keys(self, user_id: str = None) -> List[ExchangeAPIKey]:
        """Récupère les clés API actives"""
        query = select(ExchangeAPIKey).options(
            joinedload(ExchangeAPIKey.user), 
            joinedload(ExchangeAPIKey.exchange)
        ).where(ExchangeAPIKey.is_active == True)
        
        if user_id:
            query = query.where(ExchangeAPIKey.user_id == user_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_last_used(self, api_key_id: str) -> bool:
        """Met à jour la dernière utilisation"""
        try:
            await self.session.execute(
                update(ExchangeAPIKey)
                .where(ExchangeAPIKey.id == api_key_id)
                .values(last_used=datetime.utcnow())
            )
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour dernière utilisation {api_key_id}: {e}")
            return False
    
    async def deactivate_key(self, api_key_id: str) -> bool:
        """Désactive une clé API"""
        try:
            await self.session.execute(
                update(ExchangeAPIKey)
                .where(ExchangeAPIKey.id == api_key_id)
                .values(is_active=False, updated_at=datetime.utcnow())
            )
            return True
        except Exception as e:
            logger.error(f"Erreur désactivation clé {api_key_id}: {e}")
            return False


class TradingSessionRepository(BaseRepository):
    """Repository pour les sessions de trading"""
    
    async def create(self, session_data: Dict[str, Any]) -> TradingSession:
        """Crée une nouvelle session de trading"""
        session = TradingSession(**session_data)
        self.session.add(session)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="trading_session",
            entity_id=str(session.id),
            action="create",
            new_values=session_data
        )
        
        return session
    
    async def get_by_id(self, session_id: str) -> Optional[TradingSession]:
        """Récupère une session par ID"""
        result = await self.session.execute(
            select(TradingSession)
            .options(
                joinedload(TradingSession.user),
                joinedload(TradingSession.exchange),
                joinedload(TradingSession.strategy)
            )
            .where(TradingSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(self, user_id: str) -> List[TradingSession]:
        """Récupère les sessions d'un utilisateur"""
        result = await self.session.execute(
            select(TradingSession)
            .options(joinedload(TradingSession.exchange), joinedload(TradingSession.strategy))
            .where(TradingSession.user_id == user_id)
            .order_by(desc(TradingSession.started_at))
        )
        return result.scalars().all()
    
    async def get_active_sessions(self, user_id: str = None) -> List[TradingSession]:
        """Récupère les sessions actives"""
        query = select(TradingSession).options(
            joinedload(TradingSession.user),
            joinedload(TradingSession.exchange),
            joinedload(TradingSession.strategy)
        ).where(TradingSession.status == TradingSessionStatus.ACTIVE)
        
        if user_id:
            query = query.where(TradingSession.user_id == user_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_status(self, session_id: str, status: TradingSessionStatus) -> bool:
        """Met à jour le statut d'une session"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if status == TradingSessionStatus.STOPPED:
                update_data["ended_at"] = datetime.utcnow()
            
            await self.session.execute(
                update(TradingSession)
                .where(TradingSession.id == session_id)
                .values(**update_data)
            )
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour statut session {session_id}: {e}")
            return False
    
    async def update_metrics(self, session_id: str, metrics: Dict[str, Any]) -> bool:
        """Met à jour les métriques d'une session"""
        try:
            await self.session.execute(
                update(TradingSession)
                .where(TradingSession.id == session_id)
                .values(
                    **metrics,
                    last_activity=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour métriques session {session_id}: {e}")
            return False


class AlertRepository(BaseRepository):
    """Repository pour les alertes"""
    
    async def create(self, alert_data: Dict[str, Any]) -> Alert:
        """Crée une nouvelle alerte"""
        alert = Alert(**alert_data)
        self.session.add(alert)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="alert",
            entity_id=str(alert.id),
            action="create",
            new_values=alert_data
        )
        
        return alert
    
    async def get_by_id(self, alert_id: str) -> Optional[Alert]:
        """Récupère une alerte par ID"""
        result = await self.session.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(self, user_id: str) -> List[Alert]:
        """Récupère les alertes d'un utilisateur"""
        result = await self.session.execute(
            select(Alert)
            .where(Alert.user_id == user_id)
            .order_by(desc(Alert.created_at))
        )
        return result.scalars().all()
    
    async def get_active_alerts(self, user_id: str = None) -> List[Alert]:
        """Récupère les alertes actives"""
        query = select(Alert).where(Alert.is_active == True)
        
        if user_id:
            query = query.where(Alert.user_id == user_id)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def trigger_alert(self, alert_id: str) -> bool:
        """Déclenche une alerte"""
        try:
            await self.session.execute(
                update(Alert)
                .where(Alert.id == alert_id)
                .values(
                    triggered_count=Alert.triggered_count + 1,
                    last_triggered=datetime.utcnow()
                )
            )
            return True
        except Exception as e:
            logger.error(f"Erreur déclenchement alerte {alert_id}: {e}")
            return False


class NotificationRepository(BaseRepository):
    """Repository pour les notifications"""
    
    async def create(self, notification_data: Dict[str, Any]) -> Notification:
        """Crée une nouvelle notification"""
        notification = Notification(**notification_data)
        self.session.add(notification)
        await self.session.flush()
        return notification
    
    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """Récupère une notification par ID"""
        result = await self.session.execute(
            select(Notification)
            .options(joinedload(Notification.user), joinedload(Notification.alert))
            .where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(self, user_id: str, limit: int = 100) -> List[Notification]:
        """Récupère les notifications d'un utilisateur"""
        result = await self.session.execute(
            select(Notification)
            .options(joinedload(Notification.alert))
            .where(Notification.user_id == user_id)
            .order_by(desc(Notification.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_pending_notifications(self) -> List[Notification]:
        """Récupère les notifications en attente"""
        result = await self.session.execute(
            select(Notification)
            .options(joinedload(Notification.user), joinedload(Notification.alert))
            .where(
                and_(
                    Notification.is_sent == False,
                    Notification.retry_count < Notification.max_retries
                )
            )
            .order_by(Notification.created_at)
        )
        return result.scalars().all()
    
    async def mark_as_sent(self, notification_id: str) -> bool:
        """Marque une notification comme envoyée"""
        try:
            await self.session.execute(
                update(Notification)
                .where(Notification.id == notification_id)
                .values(
                    is_sent=True,
                    sent_at=datetime.utcnow()
                )
            )
            return True
        except Exception as e:
            logger.error(f"Erreur marquage notification envoyée {notification_id}: {e}")
            return False
    
    async def increment_retry(self, notification_id: str, error_message: str = None) -> bool:
        """Incrémente le compteur de tentatives"""
        try:
            await self.session.execute(
                update(Notification)
                .where(Notification.id == notification_id)
                .values(
                    retry_count=Notification.retry_count + 1,
                    error_message=error_message
                )
            )
            return True
        except Exception as e:
            logger.error(f"Erreur incrément tentatives notification {notification_id}: {e}")
            return False


class MarketDataRepository(BaseRepository):
    """Repository pour les données de marché"""
    
    async def create(self, market_data: Dict[str, Any]) -> MarketData:
        """Crée une nouvelle donnée de marché"""
        data = MarketData(**market_data)
        self.session.add(data)
        await self.session.flush()
        return data
    
    async def create_batch(self, market_data_list: List[Dict[str, Any]]) -> List[MarketData]:
        """Crée plusieurs données de marché en lot"""
        data_objects = [MarketData(**data) for data in market_data_list]
        self.session.add_all(data_objects)
        await self.session.flush()
        return data_objects
    
    async def get_by_symbol(self, symbol: str, exchange_id: str = None, 
                          timeframe: str = None, limit: int = 1000) -> List[MarketData]:
        """Récupère les données de marché par symbole"""
        query = select(MarketData).where(MarketData.symbol == symbol)
        
        if exchange_id:
            query = query.where(MarketData.exchange_id == exchange_id)
        if timeframe:
            query = query.where(MarketData.timeframe == timeframe)
        
        query = query.order_by(desc(MarketData.timestamp)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_price(self, symbol: str, exchange_id: str = None) -> Optional[MarketData]:
        """Récupère le dernier prix d'un symbole"""
        query = select(MarketData).where(MarketData.symbol == symbol)
        
        if exchange_id:
            query = query.where(MarketData.exchange_id == exchange_id)
        
        query = query.order_by(desc(MarketData.timestamp)).limit(1)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_price_range(self, symbol: str, start_date: datetime, 
                            end_date: datetime, exchange_id: str = None) -> List[MarketData]:
        """Récupère les prix sur une période"""
        query = select(MarketData).where(
            and_(
                MarketData.symbol == symbol,
                MarketData.timestamp >= start_date,
                MarketData.timestamp <= end_date
            )
        )
        
        if exchange_id:
            query = query.where(MarketData.exchange_id == exchange_id)
        
        query = query.order_by(MarketData.timestamp)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class TechnicalIndicatorRepository(BaseRepository):
    """Repository pour les indicateurs techniques"""
    
    async def create(self, indicator_data: Dict[str, Any]) -> TechnicalIndicator:
        """Crée un nouvel indicateur technique"""
        indicator = TechnicalIndicator(**indicator_data)
        self.session.add(indicator)
        await self.session.flush()
        return indicator
    
    async def create_batch(self, indicator_list: List[Dict[str, Any]]) -> List[TechnicalIndicator]:
        """Crée plusieurs indicateurs en lot"""
        indicators = [TechnicalIndicator(**data) for data in indicator_list]
        self.session.add_all(indicators)
        await self.session.flush()
        return indicators
    
    async def get_by_symbol(self, symbol: str, indicator_name: str = None,
                          timeframe: str = None, limit: int = 1000) -> List[TechnicalIndicator]:
        """Récupère les indicateurs par symbole"""
        query = select(TechnicalIndicator).where(TechnicalIndicator.symbol == symbol)
        
        if indicator_name:
            query = query.where(TechnicalIndicator.indicator_name == indicator_name)
        if timeframe:
            query = query.where(TechnicalIndicator.timeframe == timeframe)
        
        query = query.order_by(desc(TechnicalIndicator.timestamp)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_indicator(self, symbol: str, indicator_name: str) -> Optional[TechnicalIndicator]:
        """Récupère le dernier indicateur d'un symbole"""
        result = await self.session.execute(
            select(TechnicalIndicator)
            .where(
                and_(
                    TechnicalIndicator.symbol == symbol,
                    TechnicalIndicator.indicator_name == indicator_name
                )
            )
            .order_by(desc(TechnicalIndicator.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()


class RiskEventRepository(BaseRepository):
    """Repository pour les événements de risque"""
    
    async def create(self, risk_event_data: Dict[str, Any]) -> RiskEvent:
        """Crée un nouvel événement de risque"""
        risk_event = RiskEvent(**risk_event_data)
        self.session.add(risk_event)
        await self.session.flush()
        return risk_event
    
    async def get_by_id(self, risk_event_id: str) -> Optional[RiskEvent]:
        """Récupère un événement de risque par ID"""
        result = await self.session.execute(
            select(RiskEvent)
            .options(
                joinedload(RiskEvent.user),
                joinedload(RiskEvent.trading_session),
                joinedload(RiskEvent.resolved_by_user)
            )
            .where(RiskEvent.id == risk_event_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(self, user_id: str, unresolved_only: bool = True) -> List[RiskEvent]:
        """Récupère les événements de risque d'un utilisateur"""
        query = select(RiskEvent).options(
            joinedload(RiskEvent.trading_session),
            joinedload(RiskEvent.resolved_by_user)
        ).where(RiskEvent.user_id == user_id)
        
        if unresolved_only:
            query = query.where(RiskEvent.is_resolved == False)
        
        query = query.order_by(desc(RiskEvent.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_severity(self, severity: AlertSeverity) -> List[RiskEvent]:
        """Récupère les événements par sévérité"""
        result = await self.session.execute(
            select(RiskEvent)
            .options(
                joinedload(RiskEvent.user),
                joinedload(RiskEvent.trading_session)
            )
            .where(
                and_(
                    RiskEvent.severity == severity,
                    RiskEvent.is_resolved == False
                )
            )
            .order_by(desc(RiskEvent.created_at))
        )
        return result.scalars().all()
    
    async def resolve_event(self, risk_event_id: str, resolved_by: str) -> bool:
        """Résout un événement de risque"""
        try:
            await self.session.execute(
                update(RiskEvent)
                .where(RiskEvent.id == risk_event_id)
                .values(
                    is_resolved=True,
                    resolved_at=datetime.utcnow(),
                    resolved_by=resolved_by
                )
            )
            return True
        except Exception as e:
            logger.error(f"Erreur résolution événement {risk_event_id}: {e}")
            return False


class SystemMetricRepository(BaseRepository):
    """Repository pour les métriques système"""
    
    async def create(self, metric_data: Dict[str, Any]) -> SystemMetric:
        """Crée une nouvelle métrique système"""
        metric = SystemMetric(**metric_data)
        self.session.add(metric)
        await self.session.flush()
        return metric
    
    async def create_batch(self, metrics_list: List[Dict[str, Any]]) -> List[SystemMetric]:
        """Crée plusieurs métriques en lot"""
        metrics = [SystemMetric(**data) for data in metrics_list]
        self.session.add_all(metrics)
        await self.session.flush()
        return metrics
    
    async def get_by_name(self, metric_name: str, start_date: datetime = None,
                         end_date: datetime = None, limit: int = 1000) -> List[SystemMetric]:
        """Récupère les métriques par nom"""
        query = select(SystemMetric).where(SystemMetric.metric_name == metric_name)
        
        if start_date:
            query = query.where(SystemMetric.timestamp >= start_date)
        if end_date:
            query = query.where(SystemMetric.timestamp <= end_date)
        
        query = query.order_by(desc(SystemMetric.timestamp)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_latest_metric(self, metric_name: str) -> Optional[SystemMetric]:
        """Récupère la dernière métrique d'un nom"""
        result = await self.session.execute(
            select(SystemMetric)
            .where(SystemMetric.metric_name == metric_name)
            .order_by(desc(SystemMetric.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_metric_summary(self, metric_name: str, 
                               start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Récupère un résumé des métriques"""
        result = await self.session.execute(
            select(
                func.count(SystemMetric.id).label('count'),
                func.avg(SystemMetric.value).label('avg'),
                func.min(SystemMetric.value).label('min'),
                func.max(SystemMetric.value).label('max'),
                func.stddev(SystemMetric.value).label('stddev')
            )
            .where(
                and_(
                    SystemMetric.metric_name == metric_name,
                    SystemMetric.timestamp >= start_date,
                    SystemMetric.timestamp <= end_date
                )
            )
        )
        
        row = result.first()
        return {
            'count': row.count or 0,
            'average': float(row.avg or 0),
            'minimum': float(row.min or 0),
            'maximum': float(row.max or 0),
            'standard_deviation': float(row.stddev or 0)
        }