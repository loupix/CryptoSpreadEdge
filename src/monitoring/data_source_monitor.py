"""
Système de monitoring des sources de données pour CryptoSpreadEdge
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
import time

from ..connectors.common.market_data_types import MarketData
from ..connectors.connector_factory import connector_factory
from ..data_sources.data_aggregator import data_aggregator


@dataclass
class SourceMetrics:
    """Métriques d'une source de données"""
    source_name: str
    source_type: str  # exchange, alternative, dex
    is_connected: bool
    response_time: float  # en millisecondes
    success_rate: float  # pourcentage de succès
    data_quality: float  # qualité des données (0-1)
    last_update: datetime
    error_count: int
    total_requests: int
    uptime: float  # pourcentage de disponibilité


@dataclass
class Alert:
    """Alerte de monitoring"""
    level: str  # info, warning, error, critical
    source: str
    message: str
    timestamp: datetime
    resolved: bool = False


class DataSourceMonitor:
    """Moniteur des sources de données"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, SourceMetrics] = {}
        self.alerts: List[Alert] = []
        self.monitoring_active = False
        self.monitoring_interval = 30  # secondes
        self.alert_thresholds = {
            "response_time": 5000,  # 5 secondes
            "success_rate": 0.8,    # 80%
            "data_quality": 0.7,    # 70%
            "uptime": 0.9           # 90%
        }
    
    async def start_monitoring(self):
        """Démarre le monitoring des sources"""
        self.monitoring_active = True
        self.logger.info("Démarrage du monitoring des sources de données")
        
        # Initialiser les métriques
        await self._initialize_metrics()
        
        # Démarrer la boucle de monitoring
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Arrête le monitoring des sources"""
        self.monitoring_active = False
        self.logger.info("Arrêt du monitoring des sources de données")
    
    async def _initialize_metrics(self):
        """Initialise les métriques pour toutes les sources"""
        try:
            # Métriques des exchanges
            for exchange_id, connector in connector_factory.get_all_connectors().items():
                self.metrics[exchange_id] = SourceMetrics(
                    source_name=exchange_id,
                    source_type="exchange",
                    is_connected=connector.is_connected(),
                    response_time=0.0,
                    success_rate=1.0,
                    data_quality=1.0,
                    last_update=datetime.utcnow(),
                    error_count=0,
                    total_requests=0,
                    uptime=1.0
                )
            
            # Métriques des sources alternatives
            alternative_sources = ["coinmarketcap", "coingecko", "cryptocompare", "messari", "glassnode"]
            for source_name in alternative_sources:
                self.metrics[source_name] = SourceMetrics(
                    source_name=source_name,
                    source_type="alternative",
                    is_connected=True,
                    response_time=0.0,
                    success_rate=1.0,
                    data_quality=1.0,
                    last_update=datetime.utcnow(),
                    error_count=0,
                    total_requests=0,
                    uptime=1.0
                )
            
            # Métriques des DEX
            dex_sources = ["uniswap", "pancakeswap", "sushiswap"]
            for source_name in dex_sources:
                self.metrics[source_name] = SourceMetrics(
                    source_name=source_name,
                    source_type="dex",
                    is_connected=True,
                    response_time=0.0,
                    success_rate=1.0,
                    data_quality=1.0,
                    last_update=datetime.utcnow(),
                    error_count=0,
                    total_requests=0,
                    uptime=1.0
                )
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation métriques: {e}")
    
    async def _monitoring_loop(self):
        """Boucle principale de monitoring"""
        while self.monitoring_active:
            try:
                await self._check_all_sources()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Erreur boucle monitoring: {e}")
                await asyncio.sleep(5)  # Attendre avant de réessayer
    
    async def _check_all_sources(self):
        """Vérifie toutes les sources de données"""
        try:
            # Vérifier les exchanges
            for exchange_id, connector in connector_factory.get_all_connectors().items():
                await self._check_exchange_source(exchange_id, connector)
            
            # Vérifier les sources alternatives
            for source_name in ["coinmarketcap", "coingecko", "cryptocompare", "messari"]:
                await self._check_alternative_source(source_name)
            
            # Vérifier les DEX
            for source_name in ["uniswap", "pancakeswap", "sushiswap"]:
                await self._check_dex_source(source_name)
            
            # Analyser les métriques et générer des alertes
            await self._analyze_metrics()
        
        except Exception as e:
            self.logger.error(f"Erreur vérification sources: {e}")
    
    async def _check_exchange_source(self, exchange_id: str, connector):
        """Vérifie une source exchange"""
        try:
            start_time = time.time()
            
            # Test de connexion
            is_connected = connector.is_connected()
            
            # Test de récupération de données
            test_symbols = ["BTC/USDT", "ETH/USDT"]
            success = False
            data_quality = 0.0
            
            if is_connected:
                try:
                    data = await connector.get_market_data(test_symbols)
                    if data and len(data) > 0:
                        success = True
                        data_quality = self._calculate_data_quality(data)
                except Exception as e:
                    self.logger.debug(f"Erreur test données {exchange_id}: {e}")
            
            response_time = (time.time() - start_time) * 1000  # en millisecondes
            
            # Mettre à jour les métriques
            await self._update_exchange_metrics(exchange_id, is_connected, response_time, success, data_quality)
        
        except Exception as e:
            self.logger.error(f"Erreur vérification exchange {exchange_id}: {e}")
            await self._update_exchange_metrics(exchange_id, False, 0, False, 0.0)
    
    async def _check_alternative_source(self, source_name: str):
        """Vérifie une source alternative"""
        try:
            start_time = time.time()
            
            # Test de récupération de données
            test_symbols = ["BTC", "ETH"]
            success = False
            data_quality = 0.0
            
            try:
                data = await data_aggregator.alternative_sources.get_market_data(test_symbols, source_name)
                if data and len(data) > 0:
                    success = True
                    data_quality = self._calculate_data_quality(data)
            except Exception as e:
                self.logger.debug(f"Erreur test données {source_name}: {e}")
            
            response_time = (time.time() - start_time) * 1000
            
            # Mettre à jour les métriques
            await self._update_alternative_metrics(source_name, response_time, success, data_quality)
        
        except Exception as e:
            self.logger.error(f"Erreur vérification source {source_name}: {e}")
            await self._update_alternative_metrics(source_name, 0, False, 0.0)
    
    async def _check_dex_source(self, source_name: str):
        """Vérifie une source DEX"""
        try:
            start_time = time.time()
            
            # Test de récupération de données
            test_symbols = ["ETH/USDC", "BTC/USDC"]
            success = False
            data_quality = 0.0
            
            try:
                # Simuler la vérification DEX
                # Dans une implémentation réelle, on testerait la connexion au DEX
                success = True
                data_quality = 0.8  # Valeur par défaut pour les DEX
            except Exception as e:
                self.logger.debug(f"Erreur test DEX {source_name}: {e}")
            
            response_time = (time.time() - start_time) * 1000
            
            # Mettre à jour les métriques
            await self._update_dex_metrics(source_name, response_time, success, data_quality)
        
        except Exception as e:
            self.logger.error(f"Erreur vérification DEX {source_name}: {e}")
            await self._update_dex_metrics(source_name, 0, False, 0.0)
    
    def _calculate_data_quality(self, data: Dict[str, MarketData]) -> float:
        """Calcule la qualité des données"""
        if not data:
            return 0.0
        
        quality_scores = []
        
        for symbol, market_data in data.items():
            score = 0.0
            
            # Vérifier la présence du ticker
            if market_data.ticker:
                ticker = market_data.ticker
                
                # Prix valide
                if ticker.price > 0:
                    score += 0.3
                
                # Volume valide
                if ticker.volume > 0:
                    score += 0.2
                
                # Bid/Ask valides
                if ticker.bid > 0 and ticker.ask > 0 and ticker.ask > ticker.bid:
                    score += 0.2
                
                # Timestamp récent
                if market_data.timestamp and (datetime.utcnow() - market_data.timestamp).seconds < 300:
                    score += 0.3
            
            quality_scores.append(score)
        
        return statistics.mean(quality_scores) if quality_scores else 0.0
    
    async def _update_exchange_metrics(self, exchange_id: str, is_connected: bool, response_time: float, success: bool, data_quality: float):
        """Met à jour les métriques d'un exchange"""
        if exchange_id not in self.metrics:
            return
        
        metrics = self.metrics[exchange_id]
        
        # Mettre à jour les valeurs
        metrics.is_connected = is_connected
        metrics.response_time = response_time
        metrics.data_quality = data_quality
        metrics.last_update = datetime.utcnow()
        metrics.total_requests += 1
        
        if not success:
            metrics.error_count += 1
        
        # Calculer le taux de succès
        metrics.success_rate = 1.0 - (metrics.error_count / metrics.total_requests)
        
        # Calculer l'uptime (simplifié)
        if is_connected and success:
            metrics.uptime = min(1.0, metrics.uptime + 0.01)
        else:
            metrics.uptime = max(0.0, metrics.uptime - 0.05)
    
    async def _update_alternative_metrics(self, source_name: str, response_time: float, success: bool, data_quality: float):
        """Met à jour les métriques d'une source alternative"""
        if source_name not in self.metrics:
            return
        
        metrics = self.metrics[source_name]
        
        # Mettre à jour les valeurs
        metrics.response_time = response_time
        metrics.data_quality = data_quality
        metrics.last_update = datetime.utcnow()
        metrics.total_requests += 1
        
        if not success:
            metrics.error_count += 1
        
        # Calculer le taux de succès
        metrics.success_rate = 1.0 - (metrics.error_count / metrics.total_requests)
    
    async def _update_dex_metrics(self, source_name: str, response_time: float, success: bool, data_quality: float):
        """Met à jour les métriques d'un DEX"""
        if source_name not in self.metrics:
            return
        
        metrics = self.metrics[source_name]
        
        # Mettre à jour les valeurs
        metrics.response_time = response_time
        metrics.data_quality = data_quality
        metrics.last_update = datetime.utcnow()
        metrics.total_requests += 1
        
        if not success:
            metrics.error_count += 1
        
        # Calculer le taux de succès
        metrics.success_rate = 1.0 - (metrics.error_count / metrics.total_requests)
    
    async def _analyze_metrics(self):
        """Analyse les métriques et génère des alertes"""
        try:
            for source_name, metrics in self.metrics.items():
                # Vérifier le temps de réponse
                if metrics.response_time > self.alert_thresholds["response_time"]:
                    await self._create_alert("warning", source_name, f"Temps de réponse élevé: {metrics.response_time:.0f}ms")
                
                # Vérifier le taux de succès
                if metrics.success_rate < self.alert_thresholds["success_rate"]:
                    await self._create_alert("error", source_name, f"Taux de succès faible: {metrics.success_rate:.1%}")
                
                # Vérifier la qualité des données
                if metrics.data_quality < self.alert_thresholds["data_quality"]:
                    await self._create_alert("warning", source_name, f"Qualité des données faible: {metrics.data_quality:.1%}")
                
                # Vérifier l'uptime
                if metrics.uptime < self.alert_thresholds["uptime"]:
                    await self._create_alert("critical", source_name, f"Uptime faible: {metrics.uptime:.1%}")
                
                # Vérifier la déconnexion
                if metrics.source_type == "exchange" and not metrics.is_connected:
                    await self._create_alert("critical", source_name, "Source déconnectée")
        
        except Exception as e:
            self.logger.error(f"Erreur analyse métriques: {e}")
    
    async def _create_alert(self, level: str, source: str, message: str):
        """Crée une alerte"""
        alert = Alert(
            level=level,
            source=source,
            message=message,
            timestamp=datetime.utcnow()
        )
        
        self.alerts.append(alert)
        
        # Log de l'alerte
        if level == "critical":
            self.logger.critical(f"ALERTE CRITIQUE [{source}]: {message}")
        elif level == "error":
            self.logger.error(f"ALERTE ERREUR [{source}]: {message}")
        elif level == "warning":
            self.logger.warning(f"ALERTE AVERTISSEMENT [{source}]: {message}")
        else:
            self.logger.info(f"ALERTE INFO [{source}]: {message}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des métriques"""
        try:
            total_sources = len(self.metrics)
            connected_sources = sum(1 for m in self.metrics.values() if m.is_connected)
            
            avg_response_time = statistics.mean([m.response_time for m in self.metrics.values()])
            avg_success_rate = statistics.mean([m.success_rate for m in self.metrics.values()])
            avg_data_quality = statistics.mean([m.data_quality for m in self.metrics.values()])
            avg_uptime = statistics.mean([m.uptime for m in self.metrics.values()])
            
            # Compter les alertes par niveau
            alert_counts = {
                "critical": len([a for a in self.alerts if a.level == "critical" and not a.resolved]),
                "error": len([a for a in self.alerts if a.level == "error" and not a.resolved]),
                "warning": len([a for a in self.alerts if a.level == "warning" and not a.resolved]),
                "info": len([a for a in self.alerts if a.level == "info" and not a.resolved])
            }
            
            return {
                "monitoring_active": self.monitoring_active,
                "total_sources": total_sources,
                "connected_sources": connected_sources,
                "connection_rate": connected_sources / total_sources if total_sources > 0 else 0,
                "avg_response_time": avg_response_time,
                "avg_success_rate": avg_success_rate,
                "avg_data_quality": avg_data_quality,
                "avg_uptime": avg_uptime,
                "alert_counts": alert_counts,
                "total_alerts": sum(alert_counts.values()),
                "last_update": datetime.utcnow()
            }
        
        except Exception as e:
            self.logger.error(f"Erreur résumé métriques: {e}")
            return {}
    
    def get_source_metrics(self, source_name: str) -> Optional[SourceMetrics]:
        """Retourne les métriques d'une source spécifique"""
        return self.metrics.get(source_name)
    
    def get_all_metrics(self) -> Dict[str, SourceMetrics]:
        """Retourne toutes les métriques"""
        return self.metrics.copy()
    
    def get_active_alerts(self) -> List[Alert]:
        """Retourne les alertes actives"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def get_alerts_by_level(self, level: str) -> List[Alert]:
        """Retourne les alertes par niveau"""
        return [alert for alert in self.alerts if alert.level == level and not alert.resolved]
    
    def resolve_alert(self, alert_index: int):
        """Résout une alerte"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index].resolved = True
            self.logger.info(f"Alerte résolue: {self.alerts[alert_index].message}")
    
    def get_best_sources(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Retourne les meilleures sources basées sur les métriques"""
        try:
            source_scores = []
            
            for source_name, metrics in self.metrics.items():
                # Calculer un score composite
                score = (
                    metrics.success_rate * 0.3 +
                    metrics.data_quality * 0.3 +
                    metrics.uptime * 0.2 +
                    (1.0 - min(metrics.response_time / 10000, 1.0)) * 0.2  # Normaliser le temps de réponse
                )
                
                source_scores.append((source_name, score))
            
            # Trier par score décroissant
            source_scores.sort(key=lambda x: x[1], reverse=True)
            
            return source_scores[:limit]
        
        except Exception as e:
            self.logger.error(f"Erreur calcul meilleures sources: {e}")
            return []
    
    def get_worst_sources(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Retourne les pires sources basées sur les métriques"""
        try:
            source_scores = []
            
            for source_name, metrics in self.metrics.items():
                # Calculer un score composite (inversé)
                score = (
                    (1.0 - metrics.success_rate) * 0.3 +
                    (1.0 - metrics.data_quality) * 0.3 +
                    (1.0 - metrics.uptime) * 0.2 +
                    min(metrics.response_time / 10000, 1.0) * 0.2
                )
                
                source_scores.append((source_name, score))
            
            # Trier par score décroissant
            source_scores.sort(key=lambda x: x[1], reverse=True)
            
            return source_scores[:limit]
        
        except Exception as e:
            self.logger.error(f"Erreur calcul pires sources: {e}")
            return []


# Instance globale du moniteur
data_source_monitor = DataSourceMonitor()