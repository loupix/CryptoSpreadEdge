"""
Gestionnaire des risques de trading
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..connectors.common.market_data_types import Order, Position, Balance


class RiskLevel(Enum):
    """Niveaux de risque"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskLimits:
    """Limites de risque"""
    max_daily_loss: float = 1000.0
    max_position_size: float = 10000.0
    max_total_exposure: float = 50000.0
    max_drawdown: float = 0.1  # 10%
    max_orders_per_minute: int = 100
    max_orders_per_hour: int = 1000


@dataclass
class RiskMetrics:
    """Métriques de risque"""
    daily_pnl: float = 0.0
    total_exposure: float = 0.0
    current_drawdown: float = 0.0
    orders_last_minute: int = 0
    orders_last_hour: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


class RiskManager:
    """
    Gestionnaire des risques de trading
    
    Surveille et contrôle les risques en temps réel,
    applique des limites et génère des alertes.
    """
    
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.logger = logging.getLogger(__name__)
        
        self._metrics = RiskMetrics()
        self._positions: Dict[str, Position] = {}
        self._balances: Dict[str, Balance] = {}
        self._order_history: List[Order] = []
        self._running = False
        
    async def start(self) -> None:
        """Démarre le gestionnaire de risques"""
        self.logger.info("Démarrage du gestionnaire de risques...")
        self._running = True
        
        # Démarrer les tâches de monitoring
        asyncio.create_task(self._risk_monitoring_loop())
        asyncio.create_task(self._metrics_update_loop())
    
    async def stop(self) -> None:
        """Arrête le gestionnaire de risques"""
        self.logger.info("Arrêt du gestionnaire de risques...")
        self._running = False
    
    async def check_order_risk(self, order: Order) -> bool:
        """Vérifie si un ordre respecte les limites de risque"""
        try:
            # Vérifier la taille de position
            if order.quantity > self.limits.max_position_size:
                self.logger.warning(f"Ordre rejeté: taille de position trop élevée ({order.quantity})")
                return False
            
            # Vérifier l'exposition totale
            current_exposure = self._calculate_total_exposure()
            if current_exposure + (order.quantity * order.price or 0) > self.limits.max_total_exposure:
                self.logger.warning(f"Ordre rejeté: exposition totale trop élevée")
                return False
            
            # Vérifier les limites de fréquence des ordres
            if not self._check_order_frequency():
                self.logger.warning(f"Ordre rejeté: limite de fréquence atteinte")
                return False
            
            # Vérifier les pertes journalières
            if self._metrics.daily_pnl < -self.limits.max_daily_loss:
                self.logger.warning(f"Ordre rejeté: limite de perte journalière atteinte")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des risques: {e}")
            return False
    
    async def check_limits(self) -> None:
        """Vérifie toutes les limites de risque"""
        try:
            # Vérifier les pertes journalières
            if self._metrics.daily_pnl < -self.limits.max_daily_loss:
                await self._trigger_risk_alert("Limite de perte journalière atteinte", RiskLevel.CRITICAL)
            
            # Vérifier l'exposition totale
            if self._metrics.total_exposure > self.limits.max_total_exposure:
                await self._trigger_risk_alert("Exposition totale trop élevée", RiskLevel.HIGH)
            
            # Vérifier le drawdown
            if self._metrics.current_drawdown > self.limits.max_drawdown:
                await self._trigger_risk_alert("Drawdown trop élevé", RiskLevel.HIGH)
            
            # Vérifier la fréquence des ordres
            if self._metrics.orders_last_minute > self.limits.max_orders_per_minute:
                await self._trigger_risk_alert("Trop d'ordres par minute", RiskLevel.MEDIUM)
            
            if self._metrics.orders_last_hour > self.limits.max_orders_per_hour:
                await self._trigger_risk_alert("Trop d'ordres par heure", RiskLevel.MEDIUM)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des limites: {e}")
    
    async def update_metrics(self) -> None:
        """Met à jour les métriques de risque"""
        try:
            # Calculer le PnL journalier
            self._metrics.daily_pnl = self._calculate_daily_pnl()
            
            # Calculer l'exposition totale
            self._metrics.total_exposure = self._calculate_total_exposure()
            
            # Calculer le drawdown actuel
            self._metrics.current_drawdown = self._calculate_current_drawdown()
            
            # Compter les ordres récents
            self._metrics.orders_last_minute = self._count_orders_last_minute()
            self._metrics.orders_last_hour = self._count_orders_last_hour()
            
            # Déterminer le niveau de risque
            self._metrics.risk_level = self._determine_risk_level()
            self._metrics.last_updated = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour des métriques: {e}")
    
    def update_positions(self, positions: List[Position]) -> None:
        """Met à jour les positions"""
        self._positions = {pos.symbol: pos for pos in positions}
    
    def update_balances(self, balances: List[Balance]) -> None:
        """Met à jour les soldes"""
        self._balances = {bal.currency: bal for bal in balances}
    
    def record_order(self, order: Order) -> None:
        """Enregistre un ordre dans l'historique"""
        self._order_history.append(order)
        
        # Limiter la taille de l'historique
        if len(self._order_history) > 10000:
            self._order_history = self._order_history[-5000:]
    
    async def _risk_monitoring_loop(self) -> None:
        """Boucle de monitoring des risques"""
        while self._running:
            try:
                await self.check_limits()
                await asyncio.sleep(1.0)  # 1 seconde
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de monitoring: {e}")
                await asyncio.sleep(5.0)
    
    async def _metrics_update_loop(self) -> None:
        """Boucle de mise à jour des métriques"""
        while self._running:
            try:
                await self.update_metrics()
                await asyncio.sleep(5.0)  # 5 secondes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de mise à jour: {e}")
                await asyncio.sleep(10.0)
    
    def _calculate_daily_pnl(self) -> float:
        """Calcule le PnL journalier"""
        today = datetime.utcnow().date()
        daily_orders = [
            order for order in self._order_history
            if order.timestamp.date() == today
        ]
        
        pnl = 0.0
        for order in daily_orders:
            if order.status.value == "filled":
                # TODO: Calculer le PnL réel basé sur les prix d'exécution
                pass
        
        return pnl
    
    def _calculate_total_exposure(self) -> float:
        """Calcule l'exposition totale"""
        exposure = 0.0
        for position in self._positions.values():
            exposure += abs(position.quantity * position.average_price)
        return exposure
    
    def _calculate_current_drawdown(self) -> float:
        """Calcule le drawdown actuel"""
        # TODO: Implémenter le calcul du drawdown
        return 0.0
    
    def _count_orders_last_minute(self) -> int:
        """Compte les ordres de la dernière minute"""
        cutoff = datetime.utcnow() - timedelta(minutes=1)
        return len([order for order in self._order_history if order.timestamp > cutoff])
    
    def _count_orders_last_hour(self) -> int:
        """Compte les ordres de la dernière heure"""
        cutoff = datetime.utcnow() - timedelta(hours=1)
        return len([order for order in self._order_history if order.timestamp > cutoff])
    
    def _determine_risk_level(self) -> RiskLevel:
        """Détermine le niveau de risque actuel"""
        if (self._metrics.daily_pnl < -self.limits.max_daily_loss * 0.8 or
            self._metrics.current_drawdown > self.limits.max_drawdown * 0.8):
            return RiskLevel.CRITICAL
        elif (self._metrics.daily_pnl < -self.limits.max_daily_loss * 0.5 or
              self._metrics.current_drawdown > self.limits.max_drawdown * 0.5):
            return RiskLevel.HIGH
        elif (self._metrics.daily_pnl < -self.limits.max_daily_loss * 0.2 or
              self._metrics.current_drawdown > self.limits.max_drawdown * 0.2):
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def _trigger_risk_alert(self, message: str, level: RiskLevel) -> None:
        """Déclenche une alerte de risque"""
        self.logger.warning(f"ALERTE RISQUE [{level.value}]: {message}")
        
        # TODO: Implémenter le système d'alertes
        # - Envoyer des notifications
        # - Arrêter le trading si critique
        # - Notifier les administrateurs
    
    def get_metrics(self) -> RiskMetrics:
        """Retourne les métriques de risque actuelles"""
        return self._metrics
    
    def get_status(self) -> Dict:
        """Retourne le statut du gestionnaire de risques"""
        return {
            "running": self._running,
            "risk_level": self._metrics.risk_level.value,
            "daily_pnl": self._metrics.daily_pnl,
            "total_exposure": self._metrics.total_exposure,
            "current_drawdown": self._metrics.current_drawdown,
            "orders_last_minute": self._metrics.orders_last_minute,
            "orders_last_hour": self._metrics.orders_last_hour,
            "positions_count": len(self._positions),
            "balances_count": len(self._balances),
            "order_history_size": len(self._order_history)
        }