"""
Gestionnaire des ordres de trading
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from src.utils.messaging.redis_bus import RedisEventBus

from src.connectors.common.market_data_types import Order, OrderStatus, OrderSide, OrderType
from src.connectors.common.base_connector import BaseConnector


@dataclass
class OrderManagerConfig:
    """Configuration du gestionnaire d'ordres"""
    max_pending_orders: int = 100
    order_timeout: float = 30.0  # secondes
    retry_attempts: int = 3
    retry_delay: float = 1.0  # secondes


class OrderManager:
    """
    Gestionnaire central des ordres de trading
    
    Coordonne l'exécution des ordres sur les différents exchanges
    et maintient l'état des ordres.
    """
    
    def __init__(self, config: OrderManagerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self._connectors: Dict[str, BaseConnector] = {}
        self._orders: Dict[str, Order] = {}
        self._running = False
        self._order_counter = 0
        self._event_bus: RedisEventBus | None = None
    
    async def start(self) -> None:
        """Démarre le gestionnaire d'ordres"""
        self.logger.info("Démarrage du gestionnaire d'ordres...")
        self._running = True
        # Connecter l'EventBus
        self._event_bus = RedisEventBus()
        await self._event_bus.connect()
        
        # Démarrer les tâches de monitoring
        asyncio.create_task(self._order_monitoring_loop())
        asyncio.create_task(self._order_cleanup_loop())
    
    async def stop(self) -> None:
        """Arrête le gestionnaire d'ordres"""
        self.logger.info("Arrêt du gestionnaire d'ordres...")
        self._running = False
        if self._event_bus:
            self._event_bus.stop()
            await self._event_bus.close()
            self._event_bus = None
    
    def register_connector(self, name: str, connector: BaseConnector) -> None:
        """Enregistre un connecteur d'exchange"""
        self._connectors[name] = connector
        self.logger.info(f"Connecteur {name} enregistré")
    
    async def place_order(self, order: Order) -> Optional[Order]:
        """Place un ordre sur l'exchange approprié"""
        try:
            # Générer un ID d'ordre unique
            if not order.order_id:
                order.order_id = self._generate_order_id()
            
            # Valider l'ordre
            if not self._validate_order(order):
                self.logger.error(f"Ordre invalide: {order}")
                return None
            
            # Sélectionner le connecteur approprié
            connector = self._get_connector_for_symbol(order.symbol)
            if not connector:
                self.logger.error(f"Aucun connecteur trouvé pour {order.symbol}")
                return None
            
            # Placer l'ordre
            self.logger.info(f"Placement de l'ordre {order.order_id} sur {order.symbol}")
            placed_order = await connector.place_order(order)
            
            if placed_order:
                # Enregistrer l'ordre
                self._orders[placed_order.order_id] = placed_order
                self.logger.info(f"Ordre {placed_order.order_id} placé avec succès")
                # Publier événement ordre soumis
                await self._publish_order_event("orders.submitted", placed_order)
                return placed_order
            else:
                self.logger.error(f"Échec du placement de l'ordre {order.order_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors du placement de l'ordre: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Annule un ordre"""
        try:
            order = self._orders.get(order_id)
            if not order:
                self.logger.warning(f"Ordre {order_id} non trouvé")
                return False
            
            # Sélectionner le connecteur approprié
            connector = self._get_connector_for_symbol(order.symbol)
            if not connector:
                self.logger.error(f"Aucun connecteur trouvé pour {order.symbol}")
                return False
            
            # Annuler l'ordre
            success = await connector.cancel_order(order_id, order.symbol)
            if success:
                order.status = OrderStatus.CANCELLED
                self.logger.info(f"Ordre {order_id} annulé avec succès")
                # Publier événement annulation
                await self._publish_order_event("orders.cancelled", order)
            else:
                self.logger.error(f"Échec de l'annulation de l'ordre {order_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'annulation de l'ordre: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Récupère le statut d'un ordre"""
        return self._orders.get(order_id)
    
    async def get_all_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """Récupère tous les ordres, optionnellement filtrés par statut"""
        orders = list(self._orders.values())
        if status:
            orders = [order for order in orders if order.status == status]
        return orders
    
    async def process_pending_orders(self) -> None:
        """Traite les ordres en attente"""
        pending_orders = await self.get_all_orders(OrderStatus.PENDING)
        
        for order in pending_orders:
            try:
                # Vérifier le timeout
                if self._is_order_timed_out(order):
                    self.logger.warning(f"Timeout de l'ordre {order.order_id}")
                    order.status = OrderStatus.CANCELLED
                    continue
                
                # Retry si nécessaire
                if self._should_retry_order(order):
                    await self._retry_order(order)
                
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de l'ordre {order.order_id}: {e}")
    
    async def update_order_status(self) -> None:
        """Met à jour le statut des ordres"""
        for order in self._orders.values():
            if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                try:
                    connector = self._get_connector_for_symbol(order.symbol)
                    if connector:
                        updated_order = await connector.get_order_status(order.order_id, order.symbol)
                        if updated_order:
                            previous_status = self._orders[order.order_id].status
                            self._orders[order.order_id] = updated_order
                            if updated_order.status != previous_status:
                                await self._publish_order_event("orders.updated", updated_order)
                                if updated_order.status == OrderStatus.FILLED:
                                    await self._publish_order_event("orders.executed", updated_order)
                except Exception as e:
                    self.logger.error(f"Erreur lors de la mise à jour de l'ordre {order.order_id}: {e}")
    
    async def _order_monitoring_loop(self) -> None:
        """Boucle de monitoring des ordres"""
        while self._running:
            try:
                await self.process_pending_orders()
                await self.update_order_status()
                await asyncio.sleep(0.1)  # 100ms
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de monitoring: {e}")
                await asyncio.sleep(1.0)
    
    async def _order_cleanup_loop(self) -> None:
        """Boucle de nettoyage des ordres anciens"""
        while self._running:
            try:
                # Supprimer les ordres terminés anciens
                cutoff_time = datetime.utcnow().timestamp() - 3600  # 1 heure
                orders_to_remove = []
                
                for order_id, order in self._orders.items():
                    if (order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED] 
                        and order.timestamp.timestamp() < cutoff_time):
                        orders_to_remove.append(order_id)
                
                for order_id in orders_to_remove:
                    del self._orders[order_id]
                
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de nettoyage: {e}")
                await asyncio.sleep(60)
    
    def _generate_order_id(self) -> str:
        """Génère un ID d'ordre unique"""
        self._order_counter += 1
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        return f"ORD_{timestamp}_{self._order_counter}"
    
    def _validate_order(self, order: Order) -> bool:
        """Valide un ordre avant placement"""
        if not order.symbol:
            return False
        if not order.side:
            return False
        if not order.order_type:
            return False
        if order.quantity <= 0:
            return False
        if order.order_type == OrderType.LIMIT and not order.price:
            return False
        if order.order_type == OrderType.STOP and not order.stop_price:
            return False
        return True
    
    def _get_connector_for_symbol(self, symbol: str) -> Optional[BaseConnector]:
        """Sélectionne le connecteur approprié pour un symbole"""
        # TODO: Implémenter la logique de sélection du connecteur
        # Pour l'instant, retourner le premier connecteur disponible
        if self._connectors:
            return list(self._connectors.values())[0]
        return None
    
    def _is_order_timed_out(self, order: Order) -> bool:
        """Vérifie si un ordre a expiré"""
        elapsed = (datetime.utcnow() - order.timestamp).total_seconds()
        return elapsed > self.config.order_timeout
    
    def _should_retry_order(self, order: Order) -> bool:
        """Vérifie si un ordre doit être retenté"""
        # TODO: Implémenter la logique de retry
        return False
    
    async def _retry_order(self, order: Order) -> None:
        """Retente un ordre"""
        # TODO: Implémenter la logique de retry
        pass
    
    def get_status(self) -> Dict:
        """Retourne le statut du gestionnaire d'ordres"""
        return {
            "running": self._running,
            "total_orders": len(self._orders),
            "orders_by_status": {
                status.value: len([o for o in self._orders.values() if o.status == status])
                for status in OrderStatus
            },
            "connectors": list(self._connectors.keys())
        }

    async def _publish_order_event(self, stream_name: str, order: Order) -> None:
        try:
            if not self._event_bus:
                return
            payload = {
                "order_id": order.order_id,
                "symbol": getattr(order, "symbol", None),
                "side": getattr(order, "side", None).value if getattr(order, "side", None) else None,
                "type": getattr(order, "order_type", None).value if getattr(order, "order_type", None) else None,
                "price": getattr(order, "price", None),
                "quantity": getattr(order, "quantity", None),
                "status": getattr(order, "status", None).value if getattr(order, "status", None) else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self._event_bus.publish(stream_name, payload)
        except Exception:
            pass