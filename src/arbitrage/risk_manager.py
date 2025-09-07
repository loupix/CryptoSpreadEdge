"""
Gestionnaire de risques pour l'arbitrage
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from arbitrage.arbitrage_engine import ArbitrageOpportunity
from connectors.connector_factory import connector_factory


@dataclass
class RiskLimits:
    """Limites de risque"""
    max_position_size: float = 10000.0  # USD
    max_daily_loss: float = 1000.0  # USD
    max_daily_trades: int = 100
    max_spread_percentage: float = 0.05  # 5%
    min_confidence: float = 0.8
    max_risk_score: float = 0.7
    max_execution_time: float = 30.0  # secondes
    max_slippage: float = 0.001  # 0.1%


@dataclass
class RiskMetrics:
    """Métriques de risque"""
    current_position: float = 0.0
    daily_pnl: float = 0.0
    daily_trades: int = 0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    sharpe_ratio: float = 0.0
    volatility: float = 0.0


class ArbitrageRiskManager:
    """Gestionnaire de risques pour l'arbitrage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.limits = RiskLimits()
        self.metrics = RiskMetrics()
        
        # Historique des trades
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_stats: Dict[str, Dict[str, Any]] = {}
        
        # Alertes de risque
        self.risk_alerts: List[Dict[str, Any]] = []
        
        # Configuration
        self.is_monitoring = False
        self.monitoring_interval = 10  # secondes
    
    async def start_monitoring(self):
        """Démarre le monitoring des risques"""
        self.logger.info("Démarrage du monitoring des risques")
        self.is_monitoring = True
        
        # Démarrer la tâche de monitoring
        asyncio.create_task(self._monitor_risks())
    
    async def stop_monitoring(self):
        """Arrête le monitoring des risques"""
        self.logger.info("Arrêt du monitoring des risques")
        self.is_monitoring = False
    
    async def is_opportunity_safe(self, opportunity: ArbitrageOpportunity) -> bool:
        """Vérifie si une opportunité d'arbitrage est sûre"""
        try:
            # Vérifier les limites de base
            if not await self._check_basic_limits(opportunity):
                return False
            
            # Vérifier les limites de position
            if not await self._check_position_limits(opportunity):
                return False
            
            # Vérifier les limites quotidiennes
            if not await self._check_daily_limits(opportunity):
                return False
            
            # Vérifier la liquidité
            if not await self._check_liquidity(opportunity):
                return False
            
            # Vérifier la volatilité
            if not await self._check_volatility(opportunity):
                return False
            
            # Vérifier la corrélation des plateformes
            if not await self._check_platform_correlation(opportunity):
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur vérification sécurité: {e}")
            return False
    
    async def _check_basic_limits(self, opportunity: ArbitrageOpportunity) -> bool:
        """Vérifie les limites de base"""
        try:
            # Vérifier le spread
            if opportunity.spread_percentage > self.limits.max_spread_percentage:
                self._add_risk_alert(
                    "spread_too_high",
                    f"Spread trop élevé: {opportunity.spread_percentage:.2%}",
                    opportunity
                )
                return False
            
            # Vérifier la confiance
            if opportunity.confidence < self.limits.min_confidence:
                self._add_risk_alert(
                    "low_confidence",
                    f"Confiance trop faible: {opportunity.confidence:.2%}",
                    opportunity
                )
                return False
            
            # Vérifier le score de risque
            if opportunity.risk_score > self.limits.max_risk_score:
                self._add_risk_alert(
                    "high_risk_score",
                    f"Score de risque trop élevé: {opportunity.risk_score:.2%}",
                    opportunity
                )
                return False
            
            # Vérifier le temps d'exécution
            if opportunity.execution_time_estimate > self.limits.max_execution_time:
                self._add_risk_alert(
                    "execution_time_too_long",
                    f"Temps d'exécution trop long: {opportunity.execution_time_estimate:.1f}s",
                    opportunity
                )
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur vérification limites de base: {e}")
            return False
    
    async def _check_position_limits(self, opportunity: ArbitrageOpportunity) -> bool:
        """Vérifie les limites de position"""
        try:
            # Calculer la taille de position requise
            position_size = opportunity.volume_available * opportunity.buy_price
            
            # Vérifier la limite de position
            if position_size > self.limits.max_position_size:
                self._add_risk_alert(
                    "position_size_too_large",
                    f"Taille de position trop grande: {position_size:.2f} USD",
                    opportunity
                )
                return False
            
            # Vérifier la position actuelle
            if self.metrics.current_position + position_size > self.limits.max_position_size:
                self._add_risk_alert(
                    "total_position_exceeded",
                    f"Position totale dépassée: {self.metrics.current_position + position_size:.2f} USD",
                    opportunity
                )
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur vérification limites de position: {e}")
            return False
    
    async def _check_daily_limits(self, opportunity: ArbitrageOpportunity) -> bool:
        """Vérifie les limites quotidiennes"""
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Initialiser les stats du jour si nécessaire
            if today not in self.daily_stats:
                self.daily_stats[today] = {
                    "trades": 0,
                    "pnl": 0.0,
                    "volume": 0.0
                }
            
            daily_stats = self.daily_stats[today]
            
            # Vérifier le nombre de trades
            if daily_stats["trades"] >= self.limits.max_daily_trades:
                self._add_risk_alert(
                    "daily_trades_exceeded",
                    f"Nombre de trades quotidien dépassé: {daily_stats['trades']}",
                    opportunity
                )
                return False
            
            # Vérifier la perte quotidienne
            if daily_stats["pnl"] <= -self.limits.max_daily_loss:
                self._add_risk_alert(
                    "daily_loss_exceeded",
                    f"Perte quotidienne dépassée: {daily_stats['pnl']:.2f} USD",
                    opportunity
                )
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur vérification limites quotidiennes: {e}")
            return False
    
    async def _check_liquidity(self, opportunity: ArbitrageOpportunity) -> bool:
        """Vérifie la liquidité des plateformes"""
        try:
            # Vérifier que les plateformes sont connectées
            buy_connector = connector_factory.get_connector(opportunity.buy_exchange)
            sell_connector = connector_factory.get_connector(opportunity.sell_exchange)
            
            if not buy_connector or not sell_connector:
                return False
            
            if not buy_connector.is_connected() or not sell_connector.is_connected():
                return False
            
            # Vérifier la liquidité minimale
            min_liquidity = 1000.0  # USD
            if opportunity.volume_available < min_liquidity:
                self._add_risk_alert(
                    "insufficient_liquidity",
                    f"Liquidité insuffisante: {opportunity.volume_available:.2f} USD",
                    opportunity
                )
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur vérification liquidité: {e}")
            return False
    
    async def _check_volatility(self, opportunity: ArbitrageOpportunity) -> bool:
        """Vérifie la volatilité du marché"""
        try:
            # Récupérer l'historique des prix
            from ..arbitrage.price_monitor import price_monitor
            
            price_trend = await price_monitor.get_price_trend(opportunity.symbol, minutes=10)
            if not price_trend:
                return True  # Pas assez de données, on accepte
            
            # Vérifier la volatilité
            max_volatility = 0.1  # 10%
            if price_trend["volatility"] > max_volatility:
                self._add_risk_alert(
                    "high_volatility",
                    f"Volatilité trop élevée: {price_trend['volatility']:.2%}",
                    opportunity
                )
                return False
            
            # Vérifier la tendance
            max_slope = 0.01  # 1% par minute
            if abs(price_trend["slope"]) > max_slope:
                self._add_risk_alert(
                    "strong_trend",
                    f"Tendance trop forte: {price_trend['slope']:.4f}",
                    opportunity
                )
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur vérification volatilité: {e}")
            return True  # En cas d'erreur, on accepte
    
    async def _check_platform_correlation(self, opportunity: ArbitrageOpportunity) -> bool:
        """Vérifie la corrélation entre les plateformes"""
        try:
            # Vérifier que les plateformes sont différentes
            if opportunity.buy_exchange == opportunity.sell_exchange:
                return False
            
            # Vérifier la réputation des plateformes
            tier_1_platforms = ["binance", "okx", "coinbase", "kraken"]
            
            # Si les deux plateformes sont tier 1, c'est sûr
            if (opportunity.buy_exchange in tier_1_platforms and 
                opportunity.sell_exchange in tier_1_platforms):
                return True
            
            # Si une seule est tier 1, vérifier la liquidité
            if (opportunity.buy_exchange in tier_1_platforms or 
                opportunity.sell_exchange in tier_1_platforms):
                return opportunity.volume_available > 5000.0  # Liquidité plus élevée requise
            
            # Si aucune n'est tier 1, vérifier la liquidité et la confiance
            return (opportunity.volume_available > 10000.0 and 
                    opportunity.confidence > 0.9)
        
        except Exception as e:
            self.logger.error(f"Erreur vérification corrélation: {e}")
            return True
    
    def _add_risk_alert(self, alert_type: str, message: str, opportunity: ArbitrageOpportunity):
        """Ajoute une alerte de risque"""
        alert = {
            "type": alert_type,
            "message": message,
            "symbol": opportunity.symbol,
            "buy_exchange": opportunity.buy_exchange,
            "sell_exchange": opportunity.sell_exchange,
            "timestamp": datetime.utcnow(),
            "severity": "warning"
        }
        
        self.risk_alerts.append(alert)
        self.logger.warning(f"Alerte risque: {message}")
    
    async def update_trade_result(self, execution_result: Dict[str, Any]):
        """Met à jour les métriques avec le résultat d'un trade"""
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Initialiser les stats du jour si nécessaire
            if today not in self.daily_stats:
                self.daily_stats[today] = {
                    "trades": 0,
                    "pnl": 0.0,
                    "volume": 0.0
                }
            
            # Mettre à jour les stats
            self.daily_stats[today]["trades"] += 1
            self.daily_stats[today]["pnl"] += execution_result.get("net_profit", 0.0)
            self.daily_stats[today]["volume"] += execution_result.get("volume", 0.0)
            
            # Mettre à jour les métriques globales
            self.metrics.daily_pnl = self.daily_stats[today]["pnl"]
            self.metrics.daily_trades = self.daily_stats[today]["trades"]
            
            # Ajouter à l'historique
            self.trade_history.append({
                **execution_result,
                "timestamp": datetime.utcnow()
            })
            
            # Garder seulement les 1000 derniers trades
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]
            
            # Mettre à jour les métriques calculées
            await self._update_calculated_metrics()
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour résultat trade: {e}")
    
    async def _update_calculated_metrics(self):
        """Met à jour les métriques calculées"""
        try:
            if not self.trade_history:
                return
            
            # Calculer le taux de réussite
            successful_trades = [t for t in self.trade_history if t.get("net_profit", 0) > 0]
            self.metrics.win_rate = len(successful_trades) / len(self.trade_history)
            
            # Calculer le profit moyen
            profits = [t.get("net_profit", 0) for t in self.trade_history]
            self.metrics.avg_profit = statistics.mean([p for p in profits if p > 0]) if any(p > 0 for p in profits) else 0.0
            self.metrics.avg_loss = statistics.mean([p for p in profits if p < 0]) if any(p < 0 for p in profits) else 0.0
            
            # Calculer la volatilité
            if len(profits) > 1:
                self.metrics.volatility = statistics.stdev(profits)
            
            # Calculer le ratio de Sharpe (simplifié)
            if self.metrics.volatility > 0:
                self.metrics.sharpe_ratio = statistics.mean(profits) / self.metrics.volatility
            
            # Calculer le drawdown maximum
            cumulative_pnl = 0
            max_pnl = 0
            max_drawdown = 0
            
            for trade in self.trade_history:
                cumulative_pnl += trade.get("net_profit", 0)
                max_pnl = max(max_pnl, cumulative_pnl)
                drawdown = max_pnl - cumulative_pnl
                max_drawdown = max(max_drawdown, drawdown)
            
            self.metrics.max_drawdown = max_drawdown
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour métriques calculées: {e}")
    
    async def _monitor_risks(self):
        """Surveille les risques en continu"""
        while self.is_monitoring:
            try:
                # Vérifier les limites quotidiennes
                await self._check_daily_risk_limits()
                
                # Nettoyer les alertes anciennes
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.risk_alerts = [
                    alert for alert in self.risk_alerts
                    if alert["timestamp"] > cutoff_time
                ]
                
                await asyncio.sleep(self.monitoring_interval)
            
            except Exception as e:
                self.logger.error(f"Erreur monitoring risques: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _check_daily_risk_limits(self):
        """Vérifie les limites de risque quotidiennes"""
        try:
            today = datetime.utcnow().date().isoformat()
            
            if today not in self.daily_stats:
                return
            
            daily_stats = self.daily_stats[today]
            
            # Vérifier la perte quotidienne
            if daily_stats["pnl"] <= -self.limits.max_daily_loss * 0.8:  # 80% de la limite
                self._add_risk_alert(
                    "approaching_daily_loss_limit",
                    f"Approche de la limite de perte quotidienne: {daily_stats['pnl']:.2f} USD",
                    None
                )
            
            # Vérifier le nombre de trades
            if daily_stats["trades"] >= self.limits.max_daily_trades * 0.8:  # 80% de la limite
                self._add_risk_alert(
                    "approaching_daily_trades_limit",
                    f"Approche de la limite de trades quotidien: {daily_stats['trades']}",
                    None
                )
        
        except Exception as e:
            self.logger.error(f"Erreur vérification limites quotidiennes: {e}")
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Retourne le statut des risques"""
        return {
            "limits": {
                "max_position_size": self.limits.max_position_size,
                "max_daily_loss": self.limits.max_daily_loss,
                "max_daily_trades": self.limits.max_daily_trades,
                "max_spread_percentage": self.limits.max_spread_percentage,
                "min_confidence": self.limits.min_confidence,
                "max_risk_score": self.limits.max_risk_score
            },
            "metrics": {
                "current_position": self.metrics.current_position,
                "daily_pnl": self.metrics.daily_pnl,
                "daily_trades": self.metrics.daily_trades,
                "max_drawdown": self.metrics.max_drawdown,
                "win_rate": self.metrics.win_rate,
                "avg_profit": self.metrics.avg_profit,
                "avg_loss": self.metrics.avg_loss,
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "volatility": self.metrics.volatility
            },
            "alerts_count": len(self.risk_alerts),
            "is_monitoring": self.is_monitoring
        }
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retourne les alertes récentes"""
        return sorted(
            self.risk_alerts,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
    
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Retourne les statistiques quotidiennes"""
        today = datetime.utcnow().date()
        stats = []
        
        for i in range(days):
            date = (today - timedelta(days=i)).isoformat()
            if date in self.daily_stats:
                stats.append({
                    "date": date,
                    **self.daily_stats[date]
                })
            else:
                stats.append({
                    "date": date,
                    "trades": 0,
                    "pnl": 0.0,
                    "volume": 0.0
                })
        
        return stats


# Instance globale du gestionnaire de risques
arbitrage_risk_manager = ArbitrageRiskManager()