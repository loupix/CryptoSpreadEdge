"""
Système de monitoring et d'alertes avancé pour CryptoSpreadEdge
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import uuid

from .extended_models import (
    Alert, Notification, RiskEvent, SystemMetric, TradingSession,
    AlertType, AlertSeverity, NotificationChannel, TradingSessionStatus
)
from .extended_repositories import (
    AlertRepository, NotificationRepository, RiskEventRepository,
    SystemMetricRepository, TradingSessionRepository
)
from ..utils.messaging.redis_bus import RedisEventBus

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types de métriques"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertCondition(Enum):
    """Conditions d'alerte"""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"


@dataclass
class AlertRule:
    """Règle d'alerte"""
    name: str
    description: str
    alert_type: AlertType
    condition: AlertCondition
    threshold: float
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    cooldown_seconds: int = 300
    enabled: bool = True
    metadata: Dict[str, Any] = None


@dataclass
class NotificationConfig:
    """Configuration de notification"""
    channel: NotificationChannel
    enabled: bool = True
    template: Optional[str] = None
    webhook_url: Optional[str] = None
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    slack_channel: Optional[str] = None
    discord_webhook: Optional[str] = None


class MonitoringSystem:
    """Système de monitoring centralisé"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.alert_repo = AlertRepository(db_session)
        self.notification_repo = NotificationRepository(db_session)
        self.risk_repo = RiskEventRepository(db_session)
        self.metric_repo = SystemMetricRepository(db_session)
        self.session_repo = TradingSessionRepository(db_session)
        
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_configs: Dict[str, NotificationConfig] = {}
        self.metric_handlers: Dict[str, Callable] = {}
        self.is_running = False
        self._event_bus: Optional[RedisEventBus] = None
        
        self._load_default_rules()
        self._load_default_notifications()
    
    async def _ensure_bus(self):
        if self._event_bus is None:
            self._event_bus = RedisEventBus()
            await self._event_bus.connect()
    
    def _load_default_rules(self):
        """Charge les règles d'alerte par défaut"""
        
        # Règles de prix
        self.alert_rules["price_drop_5pct"] = AlertRule(
            name="price_drop_5pct",
            description="Chute de prix de 5% en 1 heure",
            alert_type=AlertType.PRICE,
            condition=AlertCondition.LESS_THAN,
            threshold=0.95,
            severity=AlertSeverity.HIGH,
            cooldown_seconds=1800
        )
        
        self.alert_rules["price_spike_10pct"] = AlertRule(
            name="price_spike_10pct",
            description="Hausse de prix de 10% en 1 heure",
            alert_type=AlertType.PRICE,
            condition=AlertCondition.GREATER_THAN,
            threshold=1.10,
            severity=AlertSeverity.MEDIUM,
            cooldown_seconds=1800
        )
        
        # Règles de volume
        self.alert_rules["volume_spike_200pct"] = AlertRule(
            name="volume_spike_200pct",
            description="Pic de volume de 200%",
            alert_type=AlertType.VOLUME,
            condition=AlertCondition.GREATER_THAN,
            threshold=3.0,
            severity=AlertSeverity.MEDIUM,
            cooldown_seconds=3600
        )
        
        # Règles de risque
        self.alert_rules["max_drawdown_10pct"] = AlertRule(
            name="max_drawdown_10pct",
            description="Drawdown maximum de 10%",
            alert_type=AlertType.RISK,
            condition=AlertCondition.LESS_THAN,
            threshold=0.90,
            severity=AlertSeverity.CRITICAL,
            cooldown_seconds=600
        )
        
        self.alert_rules["position_size_50pct"] = AlertRule(
            name="position_size_50pct",
            description="Taille de position supérieure à 50% du portefeuille",
            alert_type=AlertType.RISK,
            condition=AlertCondition.GREATER_THAN,
            threshold=0.50,
            severity=AlertSeverity.HIGH,
            cooldown_seconds=300
        )
        
        # Règles système
        self.alert_rules["api_error_rate_5pct"] = AlertRule(
            name="api_error_rate_5pct",
            description="Taux d'erreur API supérieur à 5%",
            alert_type=AlertType.SYSTEM,
            condition=AlertCondition.GREATER_THAN,
            threshold=0.05,
            severity=AlertSeverity.HIGH,
            cooldown_seconds=900
        )
        
        self.alert_rules["latency_1000ms"] = AlertRule(
            name="latency_1000ms",
            description="Latence supérieure à 1000ms",
            alert_type=AlertType.SYSTEM,
            condition=AlertCondition.GREATER_THAN,
            threshold=1000.0,
            severity=AlertSeverity.MEDIUM,
            cooldown_seconds=600
        )
        
        # Règles de trading
        self.alert_rules["consecutive_losses_5"] = AlertRule(
            name="consecutive_losses_5",
            description="5 pertes consécutives",
            alert_type=AlertType.TRADING,
            condition=AlertCondition.GREATER_EQUAL,
            threshold=5.0,
            severity=AlertSeverity.HIGH,
            cooldown_seconds=1800
        )
        
        self.alert_rules["win_rate_below_40pct"] = AlertRule(
            name="win_rate_below_40pct",
            description="Taux de réussite inférieur à 40%",
            alert_type=AlertType.PERFORMANCE,
            condition=AlertCondition.LESS_THAN,
            threshold=0.40,
            severity=AlertSeverity.MEDIUM,
            cooldown_seconds=3600
        )
    
    def _load_default_notifications(self):
        """Charge les configurations de notification par défaut"""
        
        self.notification_configs["email"] = NotificationConfig(
            channel=NotificationChannel.EMAIL,
            enabled=True,
            template="alert_email.html"
        )
        
        self.notification_configs["slack"] = NotificationConfig(
            channel=NotificationChannel.SLACK,
            enabled=True,
            template="alert_slack.json"
        )
        
        self.notification_configs["webhook"] = NotificationConfig(
            channel=NotificationChannel.WEBHOOK,
            enabled=True,
            template="alert_webhook.json"
        )
    
    async def start(self):
        """Démarre le système de monitoring"""
        self.is_running = True
        logger.info("Système de monitoring démarré")
        
        # Démarrer les tâches de monitoring
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._alert_processing_loop())
        asyncio.create_task(self._notification_loop())
        asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Arrête le système de monitoring"""
        self.is_running = False
        logger.info("Système de monitoring arrêté")
    
    async def _monitoring_loop(self):
        """Boucle principale de monitoring"""
        while self.is_running:
            try:
                # Collecter les métriques
                await self._collect_metrics()
                
                # Vérifier les alertes
                await self._check_alerts()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(30)  # Vérifier toutes les 30 secondes
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _collect_metrics(self):
        """Collecte les métriques système"""
        try:
            # Métriques de trading
            await self._collect_trading_metrics()
            
            # Métriques système
            await self._collect_system_metrics()
            
            # Métriques de performance
            await self._collect_performance_metrics()
            
        except Exception as e:
            logger.error(f"Erreur collecte métriques: {e}")
    
    async def _collect_trading_metrics(self):
        """Collecte les métriques de trading"""
        try:
            # Récupérer les sessions actives
            active_sessions = await self.session_repo.get_active_sessions()
            
            for session in active_sessions:
                # Métriques de PnL
                await self.metric_repo.create({
                    "metric_name": "trading_pnl",
                    "metric_type": "gauge",
                    "value": session.total_pnl,
                    "labels": {
                        "session_id": str(session.id),
                        "user_id": str(session.user_id),
                        "exchange": session.exchange.name
                    },
                    "timestamp": datetime.utcnow()
                })
                
                # Métriques de trades
                await self.metric_repo.create({
                    "metric_name": "trading_trades_count",
                    "metric_type": "counter",
                    "value": session.total_trades,
                    "labels": {
                        "session_id": str(session.id),
                        "user_id": str(session.user_id)
                    },
                    "timestamp": datetime.utcnow()
                })
                
                # Métriques de win rate
                win_rate = session.winning_trades / session.total_trades if session.total_trades > 0 else 0
                await self.metric_repo.create({
                    "metric_name": "trading_win_rate",
                    "metric_type": "gauge",
                    "value": win_rate,
                    "labels": {
                        "session_id": str(session.id),
                        "user_id": str(session.user_id)
                    },
                    "timestamp": datetime.utcnow()
                })
                
        except Exception as e:
            logger.error(f"Erreur collecte métriques trading: {e}")
    
    async def _collect_system_metrics(self):
        """Collecte les métriques système"""
        try:
            # Métriques de connexions API
            await self.metric_repo.create({
                "metric_name": "api_connections_active",
                "metric_type": "gauge",
                "value": 5,  # À calculer depuis les connecteurs
                "labels": {"status": "active"},
                "timestamp": datetime.utcnow()
            })
            
            # Métriques de latence
            await self.metric_repo.create({
                "metric_name": "api_latency_ms",
                "metric_type": "histogram",
                "value": 150.0,  # À calculer depuis les connecteurs
                "labels": {"exchange": "binance"},
                "timestamp": datetime.utcnow()
            })
            
            # Métriques d'erreurs
            await self.metric_repo.create({
                "metric_name": "api_errors_total",
                "metric_type": "counter",
                "value": 0,  # À calculer depuis les connecteurs
                "labels": {"exchange": "binance", "error_type": "timeout"},
                "timestamp": datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Erreur collecte métriques système: {e}")
    
    async def _collect_performance_metrics(self):
        """Collecte les métriques de performance"""
        try:
            # Métriques de mémoire
            import psutil
            memory_percent = psutil.virtual_memory().percent
            await self.metric_repo.create({
                "metric_name": "system_memory_percent",
                "metric_type": "gauge",
                "value": memory_percent,
                "labels": {"component": "trading_engine"},
                "timestamp": datetime.utcnow()
            })
            
            # Métriques de CPU
            cpu_percent = psutil.cpu_percent()
            await self.metric_repo.create({
                "metric_name": "system_cpu_percent",
                "metric_type": "gauge",
                "value": cpu_percent,
                "labels": {"component": "trading_engine"},
                "timestamp": datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Erreur collecte métriques performance: {e}")
    
    async def _check_alerts(self):
        """Vérifie les règles d'alerte"""
        try:
            for rule_name, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                # Vérifier si la règle doit être déclenchée
                if await self._evaluate_rule(rule):
                    await self._trigger_alert(rule)
                    
        except Exception as e:
            logger.error(f"Erreur vérification alertes: {e}")
    
    async def _evaluate_rule(self, rule: AlertRule) -> bool:
        """Évalue une règle d'alerte"""
        try:
            # Récupérer les métriques pertinentes
            metrics = await self.metric_repo.get_by_name(
                f"trading_{rule.alert_type.value}",
                start_date=datetime.utcnow() - timedelta(hours=1)
            )
            
            if not metrics:
                return False
            
            # Évaluer la condition
            latest_value = metrics[0].value
            
            if rule.condition == AlertCondition.GREATER_THAN:
                return latest_value > rule.threshold
            elif rule.condition == AlertCondition.LESS_THAN:
                return latest_value < rule.threshold
            elif rule.condition == AlertCondition.EQUAL:
                return latest_value == rule.threshold
            elif rule.condition == AlertCondition.NOT_EQUAL:
                return latest_value != rule.threshold
            elif rule.condition == AlertCondition.GREATER_EQUAL:
                return latest_value >= rule.threshold
            elif rule.condition == AlertCondition.LESS_EQUAL:
                return latest_value <= rule.threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur évaluation règle {rule.name}: {e}")
            return False
    
    async def _trigger_alert(self, rule: AlertRule):
        """Déclenche une alerte"""
        try:
            # Vérifier le cooldown
            if await self._is_in_cooldown(rule):
                return
            
            # Créer l'alerte
            alert_data = {
                "name": rule.name,
                "alert_type": rule.alert_type,
                "severity": rule.severity,
                "symbol": rule.symbol,
                "condition": {
                    "type": rule.condition.value,
                    "threshold": rule.threshold,
                    "timeframe": rule.timeframe
                },
                "is_active": True,
                "cooldown_seconds": rule.cooldown_seconds,
                "metadata": rule.metadata or {}
            }
            
            alert = await self.alert_repo.create(alert_data)
            
            # Déclencher l'alerte
            await self.alert_repo.trigger_alert(str(alert.id))
            
            # Créer les notifications
            await self._create_notifications(alert, rule)
            
            # Publier l'alerte sur Redis Streams
            try:
                await self._ensure_bus()
                if self._event_bus is not None:
                    await self._event_bus.publish("alerts.general", {
                        "id": str(alert.id),
                        "name": rule.name,
                        "type": rule.alert_type.value,
                        "severity": rule.severity.value,
                        "symbol": rule.symbol,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": rule.metadata or {},
                    })
            except Exception:
                pass

            logger.warning(f"Alerte déclenchée: {rule.name}")
            
        except Exception as e:
            logger.error(f"Erreur déclenchement alerte {rule.name}: {e}")
    
    async def _is_in_cooldown(self, rule: AlertRule) -> bool:
        """Vérifie si une règle est en cooldown"""
        try:
            # Récupérer les alertes récentes pour cette règle
            recent_alerts = await self.alert_repo.get_by_user("system")  # À adapter
            
            for alert in recent_alerts:
                if (alert.name == rule.name and 
                    alert.last_triggered and 
                    (datetime.utcnow() - alert.last_triggered).seconds < rule.cooldown_seconds):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur vérification cooldown {rule.name}: {e}")
            return False
    
    async def _create_notifications(self, alert: Alert, rule: AlertRule):
        """Crée les notifications pour une alerte"""
        try:
            for config_name, config in self.notification_configs.items():
                if not config.enabled:
                    continue
                
                # Créer la notification
                notification_data = {
                    "user_id": alert.user_id,
                    "alert_id": str(alert.id),
                    "channel": config.channel,
                    "title": f"Alerte {rule.name}",
                    "message": self._format_alert_message(alert, rule),
                    "is_sent": False,
                    "metadata": {
                        "rule_name": rule.name,
                        "severity": rule.severity.value,
                        "threshold": rule.threshold
                    }
                }
                
                await self.notification_repo.create(notification_data)
                
        except Exception as e:
            logger.error(f"Erreur création notifications: {e}")
    
    def _format_alert_message(self, alert: Alert, rule: AlertRule) -> str:
        """Formate le message d'alerte"""
        return f"""
🚨 Alerte {rule.name}
Type: {alert.alert_type.value}
Sévérité: {alert.severity.value}
Symbole: {alert.symbol or 'N/A'}
Condition: {rule.condition.value} {rule.threshold}
Heure: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
    
    async def _alert_processing_loop(self):
        """Boucle de traitement des alertes"""
        while self.is_running:
            try:
                # Traiter les alertes en attente
                await self._process_pending_alerts()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Erreur traitement alertes: {e}")
                await asyncio.sleep(30)
    
    async def _process_pending_alerts(self):
        """Traite les alertes en attente"""
        try:
            # Récupérer les alertes actives
            active_alerts = await self.alert_repo.get_active_alerts()
            
            for alert in active_alerts:
                # Vérifier si l'alerte doit être résolue
                if await self._should_resolve_alert(alert):
                    await self._resolve_alert(alert)
                
        except Exception as e:
            logger.error(f"Erreur traitement alertes en attente: {e}")
    
    async def _should_resolve_alert(self, alert: Alert) -> bool:
        """Détermine si une alerte doit être résolue"""
        try:
            # Récupérer les métriques récentes
            metrics = await self.metric_repo.get_by_name(
                f"trading_{alert.alert_type.value}",
                start_date=datetime.utcnow() - timedelta(minutes=5)
            )
            
            if not metrics:
                return False
            
            # Vérifier si la condition n'est plus remplie
            latest_value = metrics[0].value
            condition = alert.condition
            
            if condition["type"] == "gt":
                return latest_value <= condition["threshold"]
            elif condition["type"] == "lt":
                return latest_value >= condition["threshold"]
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur vérification résolution alerte: {e}")
            return False
    
    async def _resolve_alert(self, alert: Alert):
        """Résout une alerte"""
        try:
            await self.alert_repo.update_status(str(alert.id), False)
            logger.info(f"Alerte résolue: {alert.name}")
            
        except Exception as e:
            logger.error(f"Erreur résolution alerte {alert.name}: {e}")
    
    async def _notification_loop(self):
        """Boucle de traitement des notifications"""
        while self.is_running:
            try:
                # Traiter les notifications en attente
                await self._process_pending_notifications()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Erreur traitement notifications: {e}")
                await asyncio.sleep(30)
    
    async def _process_pending_notifications(self):
        """Traite les notifications en attente"""
        try:
            # Récupérer les notifications en attente
            pending_notifications = await self.notification_repo.get_pending_notifications()
            
            for notification in pending_notifications:
                # Envoyer la notification
                success = await self._send_notification(notification)
                
                if success:
                    await self.notification_repo.mark_as_sent(str(notification.id))
                else:
                    await self.notification_repo.increment_retry(
                        str(notification.id), 
                        "Échec envoi notification"
                    )
                
        except Exception as e:
            logger.error(f"Erreur traitement notifications: {e}")
    
    async def _send_notification(self, notification: Notification) -> bool:
        """Envoie une notification"""
        try:
            if notification.channel == NotificationChannel.EMAIL:
                return await self._send_email_notification(notification)
            elif notification.channel == NotificationChannel.SLACK:
                return await self._send_slack_notification(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook_notification(notification)
            else:
                logger.warning(f"Canal de notification non supporté: {notification.channel}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur envoi notification: {e}")
            return False
    
    async def _send_email_notification(self, notification: Notification) -> bool:
        """Envoie une notification par email"""
        # Implémentation de l'envoi d'email
        logger.info(f"Envoi email: {notification.title}")
        return True  # Simulé
    
    async def _send_slack_notification(self, notification: Notification) -> bool:
        """Envoie une notification Slack"""
        # Implémentation de l'envoi Slack
        logger.info(f"Envoi Slack: {notification.title}")
        return True  # Simulé
    
    async def _send_webhook_notification(self, notification: Notification) -> bool:
        """Envoie une notification webhook"""
        # Implémentation de l'envoi webhook
        logger.info(f"Envoi webhook: {notification.title}")
        return True  # Simulé
    
    async def _cleanup_loop(self):
        """Boucle de nettoyage"""
        while self.is_running:
            try:
                # Nettoyer les anciennes métriques
                await self._cleanup_old_metrics()
                
                # Nettoyer les anciennes notifications
                await self._cleanup_old_notifications()
                
                # Attendre avant la prochaine itération
                await asyncio.sleep(3600)  # Nettoyer toutes les heures
                
            except Exception as e:
                logger.error(f"Erreur nettoyage: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_metrics(self):
        """Nettoie les anciennes métriques"""
        try:
            # Supprimer les métriques de plus de 30 jours
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Implémentation de la suppression
            logger.info("Nettoyage des anciennes métriques")
            
        except Exception as e:
            logger.error(f"Erreur nettoyage métriques: {e}")
    
    async def _cleanup_old_notifications(self):
        """Nettoie les anciennes notifications"""
        try:
            # Supprimer les notifications de plus de 7 jours
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # Implémentation de la suppression
            logger.info("Nettoyage des anciennes notifications")
            
        except Exception as e:
            logger.error(f"Erreur nettoyage notifications: {e}")
    
    # Méthodes publiques pour la gestion des alertes
    
    async def create_alert_rule(self, rule: AlertRule):
        """Crée une nouvelle règle d'alerte"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Règle d'alerte créée: {rule.name}")
    
    async def update_alert_rule(self, rule_name: str, updates: Dict[str, Any]):
        """Met à jour une règle d'alerte"""
        if rule_name in self.alert_rules:
            rule = self.alert_rules[rule_name]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            logger.info(f"Règle d'alerte mise à jour: {rule_name}")
    
    async def delete_alert_rule(self, rule_name: str):
        """Supprime une règle d'alerte"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Règle d'alerte supprimée: {rule_name}")
    
    async def get_alert_rules(self) -> Dict[str, AlertRule]:
        """Récupère toutes les règles d'alerte"""
        return self.alert_rules.copy()
    
    async def get_alert_rule(self, rule_name: str) -> Optional[AlertRule]:
        """Récupère une règle d'alerte"""
        return self.alert_rules.get(rule_name)
    
    async def get_metrics_summary(self, metric_name: str, 
                                start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Récupère un résumé des métriques"""
        return await self.metric_repo.get_metric_summary(metric_name, start_date, end_date)
    
    async def get_active_alerts(self) -> List[Alert]:
        """Récupère les alertes actives"""
        return await self.alert_repo.get_active_alerts()
    
    async def get_notifications(self, user_id: str, limit: int = 100) -> List[Notification]:
        """Récupère les notifications d'un utilisateur"""
        return await self.notification_repo.get_by_user(user_id, limit)