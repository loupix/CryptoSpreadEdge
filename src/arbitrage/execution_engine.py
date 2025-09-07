"""
Moteur d'exécution des ordres d'arbitrage
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

from connectors.common.market_data_types import Order, OrderSide, OrderType, OrderStatus
from connectors.connector_factory import connector_factory
from arbitrage.arbitrage_engine import ArbitrageOpportunity, ArbitrageExecution


@dataclass
class ExecutionConfig:
    """Configuration d'exécution"""
    max_execution_time: float = 30.0  # secondes
    retry_attempts: int = 3
    retry_delay: float = 1.0  # secondes
    partial_fill_threshold: float = 0.8  # 80% du volume
    slippage_tolerance: float = 0.001  # 0.1%
    max_order_size: float = 10000.0  # USD


class ExecutionEngine:
    """Moteur d'exécution des ordres d'arbitrage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.config = ExecutionConfig()
        self.active_executions: Dict[str, ArbitrageExecution] = {}
        
        # Statistiques
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "partial_executions": 0,
            "total_profit": 0.0,
            "total_fees": 0.0,
            "avg_execution_time": 0.0,
            "success_rate": 0.0
        }
    
    async def start(self):
        """Démarre le moteur d'exécution"""
        self.logger.info("Démarrage du moteur d'exécution")
        self.is_running = True
        
        # Démarrer la tâche de monitoring des exécutions
        asyncio.create_task(self._monitor_executions())
    
    async def stop(self):
        """Arrête le moteur d'exécution"""
        self.logger.info("Arrêt du moteur d'exécution")
        self.is_running = False
        
        # Annuler toutes les exécutions en cours
        await self._cancel_all_executions()
    
    async def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> Optional[ArbitrageExecution]:
        """Exécute un arbitrage"""
        try:
            execution_id = f"{opportunity.symbol}_{opportunity.buy_exchange}_{opportunity.sell_exchange}_{int(time.time())}"
            
            # Créer l'exécution
            execution = ArbitrageExecution(
                opportunity=opportunity,
                buy_order=None,
                sell_order=None,
                status="pending",
                actual_profit=0.0,
                execution_time=0.0,
                fees_paid=0.0,
                net_profit=0.0,
                timestamp=datetime.utcnow()
            )
            
            self.active_executions[execution_id] = execution
            self.stats["total_executions"] += 1
            
            # Exécuter l'arbitrage
            success = await self._execute_arbitrage_orders(execution)
            
            if success:
                execution.status = "completed"
                self.stats["successful_executions"] += 1
                self.stats["total_profit"] += execution.net_profit
                self.stats["total_fees"] += execution.fees_paid
            else:
                execution.status = "failed"
                self.stats["failed_executions"] += 1
            
            # Mettre à jour les statistiques
            self._update_statistics()
            
            return execution
        
        except Exception as e:
            self.logger.error(f"Erreur exécution arbitrage: {e}")
            return None
    
    async def _execute_arbitrage_orders(self, execution: ArbitrageExecution) -> bool:
        """Exécute les ordres d'un arbitrage"""
        try:
            opportunity = execution.opportunity
            start_time = time.time()
            
            # Vérifier la validité de l'opportunité
            if not await self._validate_opportunity(opportunity):
                self.logger.warning(f"Opportunité invalide: {opportunity.symbol}")
                return False
            
            # Calculer la taille des ordres
            order_size = await self._calculate_order_size(opportunity)
            if order_size <= 0:
                self.logger.warning(f"Taille d'ordre invalide: {order_size}")
                return False
            
            # Récupérer les connecteurs
            buy_connector = connector_factory.get_connector(opportunity.buy_exchange)
            sell_connector = connector_factory.get_connector(opportunity.sell_exchange)
            
            if not buy_connector or not sell_connector:
                self.logger.error("Connecteurs non disponibles")
                return False
            
            # Créer les ordres
            buy_order = Order(
                symbol=opportunity.symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=order_size,
                price=opportunity.buy_price,
                timestamp=datetime.utcnow(),
                source=opportunity.buy_exchange
            )
            
            sell_order = Order(
                symbol=opportunity.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=order_size,
                price=opportunity.sell_price,
                timestamp=datetime.utcnow(),
                source=opportunity.sell_exchange
            )
            
            # Exécuter les ordres en parallèle
            execution.status = "executing"
            execution.buy_order = buy_order
            execution.sell_order = sell_order
            
            # Placer les ordres
            buy_task = asyncio.create_task(
                self._place_order_with_retry(buy_connector, buy_order)
            )
            sell_task = asyncio.create_task(
                self._place_order_with_retry(sell_connector, sell_order)
            )
            
            # Attendre les résultats
            buy_result, sell_result = await asyncio.gather(
                buy_task, sell_task, return_exceptions=True
            )
            
            # Vérifier les résultats
            if isinstance(buy_result, Exception) or isinstance(sell_result, Exception):
                self.logger.error(f"Erreur placement ordres: buy={buy_result}, sell={sell_result}")
                await self._cancel_orders(buy_connector, sell_connector, buy_order, sell_order)
                return False
            
            if not buy_result or not sell_result:
                self.logger.error("Échec placement ordres")
                await self._cancel_orders(buy_connector, sell_connector, buy_order, sell_order)
                return False
            
            # Mettre à jour les ordres
            execution.buy_order = buy_result
            execution.sell_order = sell_result
            
            # Attendre l'exécution complète
            execution_complete = await self._wait_for_execution_completion(execution)
            
            if not execution_complete:
                self.logger.warning("Exécution incomplète")
                execution.status = "partial"
                self.stats["partial_executions"] += 1
            
            # Calculer les résultats
            execution.execution_time = time.time() - start_time
            execution.actual_profit = await self._calculate_actual_profit(execution)
            execution.fees_paid = await self._calculate_fees(execution)
            execution.net_profit = execution.actual_profit - execution.fees_paid
            
            self.logger.info(
                f"Arbitrage exécuté: {opportunity.symbol} "
                f"profit={execution.net_profit:.2f} "
                f"temps={execution.execution_time:.2f}s"
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur exécution ordres: {e}")
            return False
    
    async def _validate_opportunity(self, opportunity: ArbitrageOpportunity) -> bool:
        """Valide une opportunité d'arbitrage"""
        try:
            # Vérifier que les connecteurs sont disponibles
            buy_connector = connector_factory.get_connector(opportunity.buy_exchange)
            sell_connector = connector_factory.get_connector(opportunity.sell_exchange)
            
            if not buy_connector or not sell_connector:
                return False
            
            if not buy_connector.is_connected() or not sell_connector.is_connected():
                return False
            
            # Vérifier que l'opportunité n'est pas trop ancienne
            if (datetime.utcnow() - opportunity.timestamp).total_seconds() > 30:
                return False
            
            # Vérifier les prix
            if opportunity.buy_price <= 0 or opportunity.sell_price <= 0:
                return False
            
            if opportunity.sell_price <= opportunity.buy_price:
                return False
            
            # Vérifier le volume
            if opportunity.volume_available < self.config.max_order_size:
                return False
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur validation opportunité: {e}")
            return False
    
    async def _calculate_order_size(self, opportunity: ArbitrageOpportunity) -> float:
        """Calcule la taille optimale des ordres"""
        try:
            # Taille basée sur le volume disponible
            max_size = min(
                opportunity.volume_available,
                self.config.max_order_size
            )
            
            # Ajuster selon le score de risque
            risk_factor = 1.0 - opportunity.risk_score
            adjusted_size = max_size * risk_factor
            
            # Ajuster selon la confiance
            confidence_factor = opportunity.confidence
            final_size = adjusted_size * confidence_factor
            
            # Arrondir à 4 décimales
            return round(final_size, 4)
        
        except Exception as e:
            self.logger.error(f"Erreur calcul taille ordre: {e}")
            return 0.0
    
    async def _place_order_with_retry(self, connector, order: Order) -> Optional[Order]:
        """Place un ordre avec retry"""
        for attempt in range(self.config.retry_attempts):
            try:
                result = await connector.place_order(order)
                if result:
                    return result
                
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
            
            except Exception as e:
                self.logger.warning(f"Tentative {attempt + 1} échouée: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
        
        return None
    
    async def _wait_for_execution_completion(self, execution: ArbitrageExecution) -> bool:
        """Attend la completion de l'exécution"""
        try:
            start_time = time.time()
            timeout = self.config.max_execution_time
            
            while time.time() - start_time < timeout:
                # Vérifier le statut des ordres
                buy_status = await self._check_order_status(execution.buy_order)
                sell_status = await self._check_order_status(execution.sell_order)
                
                if buy_status == OrderStatus.FILLED and sell_status == OrderStatus.FILLED:
                    return True
                
                if buy_status == OrderStatus.CANCELLED or sell_status == OrderStatus.CANCELLED:
                    return False
                
                await asyncio.sleep(0.5)
            
            # Timeout atteint
            self.logger.warning("Timeout d'exécution atteint")
            return False
        
        except Exception as e:
            self.logger.error(f"Erreur attente exécution: {e}")
            return False
    
    async def _check_order_status(self, order: Order) -> OrderStatus:
        """Vérifie le statut d'un ordre"""
        try:
            if not order or not order.order_id:
                return OrderStatus.PENDING
            
            connector = connector_factory.get_connector(order.source)
            if not connector:
                return OrderStatus.PENDING
            
            status = await connector.get_order_status(order.order_id, order.symbol)
            if status:
                return status.status
            
            return OrderStatus.PENDING
        
        except Exception as e:
            self.logger.error(f"Erreur vérification statut ordre: {e}")
            return OrderStatus.PENDING
    
    async def _calculate_actual_profit(self, execution: ArbitrageExecution) -> float:
        """Calcule le profit réel de l'exécution"""
        try:
            if not execution.buy_order or not execution.sell_order:
                return 0.0
            
            # Récupérer les prix d'exécution réels
            buy_price = execution.buy_order.average_price or execution.buy_order.price
            sell_price = execution.sell_order.average_price or execution.sell_order.price
            
            if not buy_price or not sell_price:
                return 0.0
            
            # Calculer le profit
            quantity = execution.buy_order.filled_quantity or execution.buy_order.quantity
            profit = (sell_price - buy_price) * quantity
            
            return profit
        
        except Exception as e:
            self.logger.error(f"Erreur calcul profit: {e}")
            return 0.0
    
    async def _calculate_fees(self, execution: ArbitrageExecution) -> float:
        """Calcule les frais payés"""
        try:
            total_fees = 0.0
            
            # Frais d'achat
            if execution.buy_order and execution.buy_order.filled_quantity:
                buy_quantity = execution.buy_order.filled_quantity
                buy_price = execution.buy_order.average_price or execution.buy_order.price
                if buy_price:
                    # Estimation des frais (0.1% par défaut)
                    buy_fees = buy_quantity * buy_price * 0.001
                    total_fees += buy_fees
            
            # Frais de vente
            if execution.sell_order and execution.sell_order.filled_quantity:
                sell_quantity = execution.sell_order.filled_quantity
                sell_price = execution.sell_order.average_price or execution.sell_order.price
                if sell_price:
                    # Estimation des frais (0.1% par défaut)
                    sell_fees = sell_quantity * sell_price * 0.001
                    total_fees += sell_fees
            
            return total_fees
        
        except Exception as e:
            self.logger.error(f"Erreur calcul frais: {e}")
            return 0.0
    
    async def _cancel_orders(self, buy_connector, sell_connector, buy_order: Order, sell_order: Order):
        """Annule les ordres"""
        try:
            if buy_order and buy_order.order_id:
                await buy_connector.cancel_order(buy_order.order_id, buy_order.symbol)
            
            if sell_order and sell_order.order_id:
                await sell_connector.cancel_order(sell_order.order_id, sell_order.symbol)
        
        except Exception as e:
            self.logger.error(f"Erreur annulation ordres: {e}")
    
    async def _cancel_all_executions(self):
        """Annule toutes les exécutions en cours"""
        try:
            for execution_id, execution in self.active_executions.items():
                if execution.status == "executing":
                    await self._cancel_orders(
                        connector_factory.get_connector(execution.opportunity.buy_exchange),
                        connector_factory.get_connector(execution.opportunity.sell_exchange),
                        execution.buy_order,
                        execution.sell_order
                    )
                    execution.status = "cancelled"
        
        except Exception as e:
            self.logger.error(f"Erreur annulation exécutions: {e}")
    
    async def _monitor_executions(self):
        """Surveille les exécutions en cours"""
        while self.is_running:
            try:
                # Nettoyer les exécutions terminées
                completed_executions = [
                    exec_id for exec_id, execution in self.active_executions.items()
                    if execution.status in ["completed", "failed", "cancelled"]
                ]
                
                for exec_id in completed_executions:
                    del self.active_executions[exec_id]
                
                await asyncio.sleep(5)  # Vérification toutes les 5 secondes
            
            except Exception as e:
                self.logger.error(f"Erreur monitoring exécutions: {e}")
                await asyncio.sleep(5)
    
    def _update_statistics(self):
        """Met à jour les statistiques"""
        try:
            total = self.stats["total_executions"]
            if total > 0:
                self.stats["success_rate"] = self.stats["successful_executions"] / total
                
                # Calculer le temps d'exécution moyen
                if self.active_executions:
                    execution_times = [
                        exec.execution_time for exec in self.active_executions.values()
                        if exec.execution_time > 0
                    ]
                    if execution_times:
                        self.stats["avg_execution_time"] = sum(execution_times) / len(execution_times)
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour statistiques: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du moteur d'exécution"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "active_executions": len(self.active_executions),
            "net_profit": self.stats["total_profit"] - self.stats["total_fees"]
        }
    
    def get_active_executions(self) -> List[ArbitrageExecution]:
        """Retourne les exécutions actives"""
        return list(self.active_executions.values())
    
    def get_execution_history(self, limit: int = 50) -> List[ArbitrageExecution]:
        """Retourne l'historique des exécutions"""
        # Dans une implémentation réelle, on stockerait l'historique en base
        return []


# Instance globale du moteur d'exécution
execution_engine = ExecutionEngine()