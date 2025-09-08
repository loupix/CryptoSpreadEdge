"""
Moteur d'arbitrage principal pour CryptoSpreadEdge
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import statistics
import time

from connectors.common.market_data_types import MarketData, Order, OrderSide, OrderType
from connectors.connector_factory import connector_factory
from data_sources.data_aggregator import data_aggregator
from config.arbitrage_config import DATA_SOURCES
from monitoring.data_source_monitor import data_source_monitor
from ..utils.messaging.redis_bus import RedisEventBus


@dataclass
class ArbitrageOpportunity:
    """Opportunité d'arbitrage détectée"""
    symbol: str = ""
    buy_exchange: str = ""
    sell_exchange: str = ""
    buy_price: float = 0.0
    sell_price: float = 0.0
    spread: float = 0.0
    spread_percentage: float = 0.0
    volume_available: float = 0.0
    max_profit: float = 0.0
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_time_estimate: float = 0.0  # en secondes
    risk_score: float = 0.0  # 0-1, plus élevé = plus risqué

    # Alias facultatifs pour compatibilité tests: seront mappés en __post_init__
    buy_platform: Optional[str] = None
    sell_platform: Optional[str] = None
    expected_profit: Optional[float] = None
    fees: Optional[float] = None
    execution_time: Optional[float] = None

    def __post_init__(self):
        # Mapper les alias de plateformes vers les champs officiels
        if self.buy_platform and not self.buy_exchange:
            self.buy_exchange = self.buy_platform
        if self.sell_platform and not self.sell_exchange:
            self.sell_exchange = self.sell_platform

        # Mapper expected_profit vers max_profit si fourni
        if self.expected_profit is not None and (self.max_profit is None or self.max_profit == 0):
            self.max_profit = self.expected_profit

        # Mapper execution_time vers execution_time_estimate si fourni
        if self.execution_time is not None and (self.execution_time_estimate is None or self.execution_time_estimate == 0):
            self.execution_time_estimate = self.execution_time


@dataclass
class ArbitrageExecution:
    """Exécution d'un arbitrage"""
    opportunity: ArbitrageOpportunity
    buy_order: Optional[Order]
    sell_order: Optional[Order]
    status: str  # pending, executing, completed, failed
    actual_profit: float
    execution_time: float
    fees_paid: float
    net_profit: float
    timestamp: datetime


class ArbitrageEngine:
    """Moteur d'arbitrage principal"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.opportunities: List[ArbitrageOpportunity] = []
        self.executions: List[ArbitrageExecution] = []
        self._event_bus: RedisEventBus | None = None
        
        # Configuration
        self.min_spread_percentage = 0.001  # 0.1% minimum
        self.max_spread_percentage = 0.05   # 5% maximum
        self.min_volume = 0.01              # Volume minimum
        self.max_risk_score = 0.7           # Score de risque maximum
        self.min_confidence = 0.8           # Confiance minimum
        
        # Monitoring
        self.price_monitor = None
        self.execution_engine = None
        self.risk_manager = None
        
        # Statistiques
        self.stats = {
            "opportunities_found": 0,
            "opportunities_executed": 0,
            "total_profit": 0.0,
            "total_fees": 0.0,
            "success_rate": 0.0,
            "avg_execution_time": 0.0
        }
    
    async def start(self):
        """Démarre le moteur d'arbitrage"""
        try:
            self.logger.info("Démarrage du moteur d'arbitrage")
            self.is_running = True
            self._event_bus = RedisEventBus()
            await self._event_bus.connect()
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Démarrer les tâches en parallèle
            tasks = [
                self._monitor_prices(),
                self._scan_opportunities(),
                self._execute_arbitrage(),
                self._update_statistics()
            ]
            
            await asyncio.gather(*tasks)
        
        except Exception as e:
            self.logger.error(f"Erreur démarrage moteur d'arbitrage: {e}")
            self.is_running = False
    
    async def stop(self):
        """Arrête le moteur d'arbitrage"""
        self.logger.info("Arrêt du moteur d'arbitrage")
        self.is_running = False
        if self._event_bus:
            self._event_bus.stop()
            await self._event_bus.close()
            self._event_bus = None
        
        # Annuler les ordres en cours
        await self._cancel_pending_orders()
    
    async def _initialize_components(self):
        """Initialise les composants du moteur d'arbitrage"""
        try:
            # Initialiser le monitor de prix
            from .price_monitor import PriceMonitor
            self.price_monitor = PriceMonitor()
            await self.price_monitor.start()
            
            # Initialiser le moteur d'exécution
            from .execution_engine import ExecutionEngine
            self.execution_engine = ExecutionEngine()
            await self.execution_engine.start()
            
            # Initialiser le gestionnaire de risques
            from .risk_manager import ArbitrageRiskManager
            self.risk_manager = ArbitrageRiskManager()
            
            self.logger.info("Composants d'arbitrage initialisés")
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation composants: {e}")
            raise
    
    async def _monitor_prices(self):
        """Surveille les prix en temps réel"""
        while self.is_running:
            try:
                # Récupérer les prix de toutes les plateformes
                symbols = ["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"]
                prices = await self.price_monitor.get_all_prices(symbols)
                
                # Mettre à jour le cache des prix
                await self.price_monitor.update_price_cache(prices)
                
                await asyncio.sleep(1)  # Mise à jour chaque seconde
            
            except Exception as e:
                self.logger.error(f"Erreur monitoring prix: {e}")
                await asyncio.sleep(5)
    
    async def _scan_opportunities(self):
        """Scanne les opportunités d'arbitrage"""
        while self.is_running:
            try:
                # Récupérer les prix actuels
                symbols = ["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"]
                opportunities = await self._find_arbitrage_opportunities(symbols)
                
                # Filtrer les opportunités
                filtered_opportunities = await self._filter_opportunities(opportunities)
                
                # Ajouter aux opportunités détectées
                self.opportunities.extend(filtered_opportunities)
                # Publier les opportunités
                await self._publish_opportunities(filtered_opportunities)
                
                # Garder seulement les opportunités récentes (dernières 5 minutes)
                cutoff_time = datetime.utcnow() - timedelta(minutes=5)
                self.opportunities = [
                    opp for opp in self.opportunities
                    if opp.timestamp > cutoff_time
                ]
                
                self.stats["opportunities_found"] += len(filtered_opportunities)
                
                await asyncio.sleep(2)  # Scan toutes les 2 secondes
            
            except Exception as e:
                self.logger.error(f"Erreur scan opportunités: {e}")
                await asyncio.sleep(5)
    
    async def _find_arbitrage_opportunities(self, symbols: List[str]) -> List[ArbitrageOpportunity]:
        """Trouve les opportunités d'arbitrage pour les symboles donnés"""
        opportunities = []
        
        try:
            # Récupérer les prix de toutes les plateformes
            all_prices = await data_aggregator.get_aggregated_data(symbols)
            
            for symbol, aggregated_data in all_prices.items():
                # Récupérer les prix par plateforme
                platform_prices = await self._get_platform_prices(symbol)
                
                if len(platform_prices) < 2:
                    continue
                
                # Trouver les meilleures opportunités
                symbol_opportunities = self._calculate_arbitrage_opportunities(
                    symbol, platform_prices, aggregated_data
                )
                
                opportunities.extend(symbol_opportunities)
        
        except Exception as e:
            self.logger.error(f"Erreur recherche opportunités: {e}")
        
        return opportunities
    
    async def _get_platform_prices(self, symbol: str) -> Dict[str, Dict[str, Any]]:
        """Récupère les prix d'un symbole depuis toutes les plateformes"""
        platform_prices = {}
        
        try:
            # Récupérer les prix des exchanges
            for exchange_id, connector in connector_factory.get_all_connectors().items():
                if connector.is_connected():
                    try:
                        market_data = await connector.get_ticker(symbol)
                        if market_data and market_data.ticker:
                            platform_prices[exchange_id] = {
                                "price": market_data.ticker.price,
                                "bid": market_data.ticker.bid,
                                "ask": market_data.ticker.ask,
                                "volume": market_data.ticker.volume,
                                "timestamp": market_data.timestamp,
                                "source": "exchange"
                            }
                    except Exception as e:
                        self.logger.debug(f"Erreur prix {exchange_id} {symbol}: {e}")
            
            # Récupérer les prix des sources alternatives (pilotées par la config)
            for source_name in [name for name, cfg in DATA_SOURCES.items() if cfg.enabled]:
                try:
                    data = await data_aggregator.alternative_sources.get_market_data([symbol], source_name)
                    if symbol in data and data[symbol].ticker:
                        platform_prices[source_name] = {
                            "price": data[symbol].ticker.price,
                            "bid": data[symbol].ticker.bid,
                            "ask": data[symbol].ticker.ask,
                            "volume": data[symbol].ticker.volume,
                            "timestamp": data[symbol].timestamp,
                            "source": "data_source"
                        }
                except Exception as e:
                    self.logger.debug(f"Erreur prix {source_name} {symbol}: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur récupération prix {symbol}: {e}")
        
        return platform_prices
    
    def _calculate_arbitrage_opportunities(
        self, 
        symbol: str, 
        platform_prices: Dict[str, Dict[str, Any]], 
        aggregated_data: Any
    ) -> List[ArbitrageOpportunity]:
        """Calcule les opportunités d'arbitrage pour un symbole"""
        opportunities = []
        
        try:
            # Trier les plateformes par prix
            sorted_platforms = sorted(
                platform_prices.items(),
                key=lambda x: x[1]["price"]
            )
            
            # Comparer chaque paire de plateformes
            for i, (buy_platform, buy_data) in enumerate(sorted_platforms):
                for j, (sell_platform, sell_data) in enumerate(sorted_platforms[i+1:], i+1):
                    
                    # Vérifier que ce sont des exchanges (pas des sources de données)
                    if (buy_data["source"] != "exchange" or 
                        sell_data["source"] != "exchange"):
                        continue
                    
                    buy_price = buy_data["ask"]  # Prix d'achat (ask)
                    sell_price = sell_data["bid"]  # Prix de vente (bid)
                    
                    if buy_price <= 0 or sell_price <= 0:
                        continue
                    
                    # Calculer le spread
                    spread = sell_price - buy_price
                    spread_percentage = spread / buy_price
                    
                    # Vérifier les critères minimum
                    if (spread_percentage < self.min_spread_percentage or 
                        spread_percentage > self.max_spread_percentage):
                        continue
                    
                    # Calculer le volume disponible
                    volume_available = min(
                        buy_data.get("volume", 0),
                        sell_data.get("volume", 0)
                    )
                    
                    if volume_available < self.min_volume:
                        continue
                    
                    # Calculer le profit maximum
                    max_profit = spread * volume_available
                    
                    # Calculer la confiance
                    confidence = self._calculate_confidence(
                        buy_data, sell_data, aggregated_data
                    )
                    
                    if confidence < self.min_confidence:
                        continue
                    
                    # Calculer le temps d'exécution estimé
                    execution_time = self._estimate_execution_time(
                        buy_platform, sell_platform
                    )
                    
                    # Calculer le score de risque
                    risk_score = self._calculate_risk_score(
                        buy_platform, sell_platform, spread_percentage, volume_available
                    )
                    
                    if risk_score > self.max_risk_score:
                        continue
                    
                    # Créer l'opportunité
                    opportunity = ArbitrageOpportunity(
                        symbol=symbol,
                        buy_exchange=buy_platform,
                        sell_exchange=sell_platform,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        spread=spread,
                        spread_percentage=spread_percentage,
                        volume_available=volume_available,
                        max_profit=max_profit,
                        confidence=confidence,
                        timestamp=datetime.utcnow(),
                        execution_time_estimate=execution_time,
                        risk_score=risk_score
                    )
                    
                    opportunities.append(opportunity)
        
        except Exception as e:
            self.logger.error(f"Erreur calcul opportunités {symbol}: {e}")
        
        return opportunities
    
    def _calculate_confidence(
        self, 
        buy_data: Dict[str, Any], 
        sell_data: Dict[str, Any], 
        aggregated_data: Any
    ) -> float:
        """Calcule la confiance d'une opportunité d'arbitrage"""
        try:
            confidence = 1.0
            
            # Vérifier la fraîcheur des données
            now = datetime.utcnow()
            buy_age = (now - buy_data["timestamp"]).total_seconds()
            sell_age = (now - sell_data["timestamp"]).total_seconds()
            
            if buy_age > 60 or sell_age > 60:  # Données trop anciennes
                confidence *= 0.5
            
            # Vérifier la cohérence avec les données agrégées
            if aggregated_data and hasattr(aggregated_data, 'price'):
                avg_price = aggregated_data.price
                buy_deviation = abs(buy_data["price"] - avg_price) / avg_price
                sell_deviation = abs(sell_data["price"] - avg_price) / avg_price
                
                if buy_deviation > 0.05 or sell_deviation > 0.05:  # 5% de déviation
                    confidence *= 0.7
            
            # Vérifier le volume
            if buy_data.get("volume", 0) < 1000 or sell_data.get("volume", 0) < 1000:
                confidence *= 0.8
            
            return min(1.0, confidence)
        
        except Exception as e:
            self.logger.error(f"Erreur calcul confiance: {e}")
            return 0.5
    
    def _estimate_execution_time(self, buy_platform: str, sell_platform: str) -> float:
        """Estime le temps d'exécution d'un arbitrage"""
        try:
            # Temps de base pour chaque plateforme
            platform_times = {
                "binance": 0.1,
                "okx": 0.15,
                "bybit": 0.2,
                "bitget": 0.25,
                "gateio": 0.3,
                "huobi": 0.35,
                "kucoin": 0.4,
                "coinbase": 0.5,
                "kraken": 0.6
            }
            
            buy_time = platform_times.get(buy_platform, 0.5)
            sell_time = platform_times.get(sell_platform, 0.5)
            
            # Ajouter un buffer de sécurité
            return (buy_time + sell_time) * 1.5
        
        except Exception as e:
            self.logger.error(f"Erreur estimation temps: {e}")
            return 1.0
    
    def _calculate_risk_score(
        self, 
        buy_platform: str, 
        sell_platform: str, 
        spread_percentage: float, 
        volume: float
    ) -> float:
        """Calcule le score de risque d'une opportunité"""
        try:
            risk_score = 0.0
            
            # Risque basé sur la taille du spread
            if spread_percentage > 0.02:  # 2%
                risk_score += 0.3
            elif spread_percentage > 0.01:  # 1%
                risk_score += 0.2
            else:
                risk_score += 0.1
            
            # Risque basé sur le volume
            if volume > 10000:
                risk_score += 0.2
            elif volume > 1000:
                risk_score += 0.1
            else:
                risk_score += 0.3
            
            # Risque basé sur les plateformes
            tier_1_platforms = ["binance", "okx", "coinbase", "kraken"]
            if buy_platform not in tier_1_platforms:
                risk_score += 0.1
            if sell_platform not in tier_1_platforms:
                risk_score += 0.1
            
            # Risque basé sur la différence de liquidité
            # (simplifié - dans une implémentation réelle, on comparerait les volumes)
            risk_score += 0.1
            
            return min(1.0, risk_score)
        
        except Exception as e:
            self.logger.error(f"Erreur calcul risque: {e}")
            return 0.5
    
    async def _filter_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Filtre les opportunités selon les critères"""
        filtered = []
        
        for opportunity in opportunities:
            # Vérifier les critères de base
            if (opportunity.spread_percentage >= self.min_spread_percentage and
                opportunity.spread_percentage <= self.max_spread_percentage and
                opportunity.volume_available >= self.min_volume and
                opportunity.confidence >= self.min_confidence and
                opportunity.risk_score <= self.max_risk_score):
                
                # Vérifier avec le gestionnaire de risques
                if self.risk_manager and await self.risk_manager.is_opportunity_safe(opportunity):
                    filtered.append(opportunity)
        
        # Trier par profit potentiel
        filtered.sort(key=lambda x: x.max_profit, reverse=True)
        
        return filtered
    
    async def _execute_arbitrage(self):
        """Exécute les opportunités d'arbitrage"""
        while self.is_running:
            try:
                # Prendre la meilleure opportunité disponible
                if self.opportunities:
                    opportunity = self.opportunities.pop(0)
                    
                    # Exécuter l'arbitrage
                    execution = await self.execution_engine.execute_arbitrage(opportunity)
                    
                    if execution:
                        self.executions.append(execution)
                        self.stats["opportunities_executed"] += 1
                        await self._publish_execution(execution)
                        
                        if execution.status == "completed":
                            self.stats["total_profit"] += execution.net_profit
                            self.stats["total_fees"] += execution.fees_paid
                
                await asyncio.sleep(0.1)  # Vérifier toutes les 100ms
            
            except Exception as e:
                self.logger.error(f"Erreur exécution arbitrage: {e}")
                await asyncio.sleep(1)
    
    async def _cancel_pending_orders(self):
        """Annule les ordres en cours"""
        try:
            for execution in self.executions:
                if execution.status == "executing":
                    if execution.buy_order:
                        await connector_factory.get_connector(execution.opportunity.buy_exchange).cancel_order(
                            execution.buy_order.order_id, execution.opportunity.symbol
                        )
                    if execution.sell_order:
                        await connector_factory.get_connector(execution.opportunity.sell_exchange).cancel_order(
                            execution.sell_order.order_id, execution.opportunity.symbol
                        )
                    execution.status = "cancelled"
        
        except Exception as e:
            self.logger.error(f"Erreur annulation ordres: {e}")
    
    async def _update_statistics(self):
        """Met à jour les statistiques"""
        while self.is_running:
            try:
                # Calculer le taux de succès
                if self.stats["opportunities_executed"] > 0:
                    successful_executions = len([
                        e for e in self.executions 
                        if e.status == "completed"
                    ])
                    self.stats["success_rate"] = successful_executions / self.stats["opportunities_executed"]
                
                # Calculer le temps d'exécution moyen
                if self.executions:
                    completed_executions = [
                        e for e in self.executions 
                        if e.status == "completed"
                    ]
                    if completed_executions:
                        self.stats["avg_execution_time"] = statistics.mean([
                            e.execution_time for e in completed_executions
                        ])
                
                await asyncio.sleep(10)  # Mise à jour toutes les 10 secondes
            
            except Exception as e:
                self.logger.error(f"Erreur mise à jour statistiques: {e}")
                await asyncio.sleep(10)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du moteur d'arbitrage"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "active_opportunities": len(self.opportunities),
            "total_executions": len(self.executions),
            "net_profit": self.stats["total_profit"] - self.stats["total_fees"]
        }
    
    def get_recent_opportunities(self, limit: int = 10) -> List[ArbitrageOpportunity]:
        """Retourne les opportunités récentes"""
        return sorted(
            self.opportunities,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]
    
    def get_recent_executions(self, limit: int = 10) -> List[ArbitrageExecution]:
        """Retourne les exécutions récentes"""
        return sorted(
            self.executions,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]

    async def _publish_opportunities(self, opps: List[ArbitrageOpportunity]) -> None:
        try:
            if not opps or not self._event_bus:
                return
            for o in opps:
                payload = {
                    'symbol': o.symbol,
                    'buy_exchange': o.buy_exchange,
                    'sell_exchange': o.sell_exchange,
                    'buy_price': o.buy_price,
                    'sell_price': o.sell_price,
                    'spread': o.spread,
                    'spread_pct': o.spread_percentage,
                    'volume': o.volume_available,
                    'confidence': o.confidence,
                    'risk_score': o.risk_score,
                    'timestamp': o.timestamp.isoformat(),
                }
                await self._event_bus.publish('arbitrage.opportunities', payload)
        except Exception:
            pass

    async def _publish_execution(self, exe: ArbitrageExecution) -> None:
        try:
            if not self._event_bus:
                return
            payload = {
                'symbol': exe.opportunity.symbol,
                'status': exe.status,
                'actual_profit': exe.actual_profit,
                'execution_time': exe.execution_time,
                'fees': exe.fees_paid,
                'net_profit': exe.net_profit,
                'timestamp': exe.timestamp.isoformat(),
            }
            await self._event_bus.publish('arbitrage.executions', payload)
        except Exception:
            pass


# Instance globale du moteur d'arbitrage
arbitrage_engine = ArbitrageEngine()