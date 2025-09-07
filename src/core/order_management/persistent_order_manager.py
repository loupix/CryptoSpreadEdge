"""
Gestionnaire des ordres de trading avec persistance PostgreSQL
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from ...database import get_database_manager, OrderRepository
from ...database.models import OrderStatus, OrderSide, OrderType
from ..connectors.common.market_data_types import Order as MarketOrder
from ..connectors.common.base_connector import BaseConnector


@dataclass
class OrderManagerConfig:
    """Configuration du gestionnaire d'ordres"""
    max_pending_orders: int = 100
    order_timeout: float = 30.0  # secondes
    retry_attempts: int = 3
    retry_delay: float = 1.0  # secondes


class PersistentOrderManager:
    """
    Gestionnaire central des ordres de trading avec persistance PostgreSQL
    
    Coordonne l'exécution des ordres sur les différents exchanges
    et maintient l'état des ordres en base de données.
    """
    
    def __init__(self, config: OrderManagerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self._connectors: Dict[str, BaseConnector] = {}
        self._running = False
        self._order_counter = 0
        self._db_manager = get_database_manager()
    
    async def start(self) -> None:
        """Démarre le gestionnaire d'ordres"""
        self.logger.info("Démarrage du gestionnaire d'ordres avec persistance...")
        
        # Initialiser la base de données
        await self._db_manager.initialize()
        
        self._running = True
        
        # Démarrer les tâches de monitoring
        asyncio.create_task(self._order_monitoring_loop())
        asyncio.create_task(self._order_cleanup_loop())
    
    async def stop(self) -> None:
        """Arrête le gestionnaire d'ordres"""
        self.logger.info("Arrêt du gestionnaire d'ordres...")
        self._running = False
    
    def register_connector(self, name: str, connector: BaseConnector) -> None:
        """Enregistre un connecteur d'exchange"""
        self._connectors[name] = connector
        self.logger.info(f"Connecteur {name} enregistré")
    
    async def place_order(self, order: MarketOrder) -> Optional[MarketOrder]:
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
            
            # Préparer les données pour la base
            order_data = {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": OrderSide.BUY if order.side == "buy" else OrderSide.SELL,
                "order_type": self._convert_order_type(order.order_type),
                "quantity": order.quantity,
                "price": order.price,
                "stop_price": order.stop_price,
                "status": OrderStatus.PENDING,
                "exchange": order.source or connector.get_name(),
                "source": order.source or connector.get_name(),
                "metadata": {
                    "original_order": {
                        "id": order.id,
                        "exchange": order.exchange,
                        "type": order.type
                    }
                }
            }
            
            # Sauvegarder en base
            async with self._db_manager.get_session() as session:
                order_repo = OrderRepository(session)
                db_order = await order_repo.create(order_data)
                
                # Placer l'ordre sur l'exchange
                self.logger.info(f"Placement de l'ordre {order.order_id} sur {order.symbol}")
                placed_order = await connector.place_order(order)
                
                if placed_order:
                    # Mettre à jour le statut en base
                    await order_repo.update_status(
                        order.order_id, 
                        OrderStatus.OPEN,
                        placed_order.filled_quantity,
                        placed_order.average_price
                    )
                    
                    self.logger.info(f"Ordre {placed_order.order_id} placé avec succès")
                    return placed_order
                else:
                    # Marquer comme rejeté
                    await order_repo.update_status(order.order_id, OrderStatus.REJECTED)
                    self.logger.error(f"Échec du placement de l'ordre {order.order_id}")
                    return None
                
        except Exception as e:
            self.logger.error(f"Erreur lors du placement de l'ordre: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Annule un ordre"""
        try:
            # Récupérer l'ordre depuis la base
            async with self._db_manager.get_session() as session:
                order_repo = OrderRepository(session)
                db_order = await order_repo.get_by_id(order_id)
                
                if not db_order:
                    self.logger.error(f"Ordre {order_id} non trouvé")
                    return False
                
                # Annuler sur l'exchange
                connector = self._get_connector_for_symbol(db_order.symbol)
                if connector:
                    success = await connector.cancel_order(order_id)
                    if success:
                        await order_repo.update_status(order_id, OrderStatus.CANCELLED)
                        self.logger.info(f"Ordre {order_id} annulé avec succès")
                        return True
                    else:
                        self.logger.error(f"Échec de l'annulation de l'ordre {order_id}")
                        return False
                else:
                    self.logger.error(f"Connecteur non trouvé pour {db_order.symbol}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Erreur lors de l'annulation de l'ordre {order_id}: {e}")
            return False
    
    async def get_order(self, order_id: str) -> Optional[MarketOrder]:
        """Récupère un ordre par ID"""
        try:
            async with self._db_manager.get_session() as session:
                order_repo = OrderRepository(session)
                db_order = await order_repo.get_by_id(order_id)
                
                if not db_order:
                    return None
                
                # Convertir vers MarketOrder
                return self._convert_db_order_to_market_order(db_order)
                
        except Exception as e:
            self.logger.error(f"Erreur récupération ordre {order_id}: {e}")
            return None
    
    async def get_active_orders(self, symbol: str = None) -> List[MarketOrder]:
        """Récupère les ordres actifs"""
        try:
            async with self._db_manager.get_session() as session:
                order_repo = OrderRepository(session)
                db_orders = await order_repo.get_active_orders(symbol)
                
                return [self._convert_db_order_to_market_order(order) for order in db_orders]
                
        except Exception as e:
            self.logger.error(f"Erreur récupération ordres actifs: {e}")
            return []
    
    async def get_orders_by_symbol(self, symbol: str, limit: int = 100) -> List[MarketOrder]:
        """Récupère les ordres par symbole"""
        try:
            async with self._db_manager.get_session() as session:
                order_repo = OrderRepository(session)
                db_orders = await order_repo.get_by_symbol(symbol, limit)
                
                return [self._convert_db_order_to_market_order(order) for order in db_orders]
                
        except Exception as e:
            self.logger.error(f"Erreur récupération ordres pour {symbol}: {e}")
            return []
    
    def _generate_order_id(self) -> str:
        """Génère un ID d'ordre unique"""
        self._order_counter += 1
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"ORD_{timestamp}_{self._order_counter:06d}"
    
    def _validate_order(self, order: MarketOrder) -> bool:
        """Valide un ordre"""
        if not order.symbol or not order.quantity or order.quantity <= 0:
            return False
        
        if order.order_type == "limit" and (not order.price or order.price <= 0):
            return False
        
        return True
    
    def _get_connector_for_symbol(self, symbol: str) -> Optional[BaseConnector]:
        """Sélectionne le connecteur approprié pour un symbole"""
        # Logique de sélection du connecteur basée sur le symbole
        # Pour l'instant, retourne le premier connecteur disponible
        return next(iter(self._connectors.values())) if self._connectors else None
    
    def _convert_order_type(self, order_type: str) -> OrderType:
        """Convertit le type d'ordre vers l'enum de base"""
        type_mapping = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop": OrderType.STOP,
            "stop_limit": OrderType.STOP_LIMIT
        }
        return type_mapping.get(order_type, OrderType.MARKET)
    
    def _convert_db_order_to_market_order(self, db_order) -> MarketOrder:
        """Convertit un ordre de base vers MarketOrder"""
        return MarketOrder(
            symbol=db_order.symbol,
            side=db_order.side.value,
            quantity=db_order.quantity,
            order_type=db_order.order_type.value,
            price=db_order.price,
            stop_price=db_order.stop_price,
            order_id=db_order.order_id,
            exchange=db_order.exchange,
            source=db_order.source,
            status=db_order.status.value,
            filled_quantity=db_order.filled_quantity,
            average_price=db_order.average_price,
            timestamp=db_order.created_at
        )
    
    async def _order_monitoring_loop(self):
        """Boucle de monitoring des ordres"""
        while self._running:
            try:
                # Vérifier les ordres en attente
                async with self._db_manager.get_session() as session:
                    order_repo = OrderRepository(session)
                    pending_orders = await order_repo.get_by_status(OrderStatus.PENDING)
                    
                    for order in pending_orders:
                        # Vérifier si l'ordre a expiré
                        if (datetime.utcnow() - order.created_at).seconds > self.config.order_timeout:
                            await order_repo.update_status(order.order_id, OrderStatus.CANCELLED)
                            self.logger.warning(f"Ordre {order.order_id} expiré et annulé")
                
                await asyncio.sleep(5)  # Vérifier toutes les 5 secondes
                
            except Exception as e:
                self.logger.error(f"Erreur monitoring ordres: {e}")
                await asyncio.sleep(10)
    
    async def _order_cleanup_loop(self):
        """Boucle de nettoyage des anciens ordres"""
        while self._running:
            try:
                # Nettoyer les ordres anciens (plus de 30 jours)
                async with self._db_manager.get_session() as session:
                    order_repo = OrderRepository(session)
                    deleted_count = await order_repo.delete_old_orders(days=30)
                    
                    if deleted_count > 0:
                        self.logger.info(f"Nettoyage: {deleted_count} anciens ordres supprimés")
                
                await asyncio.sleep(3600)  # Nettoyer toutes les heures
                
            except Exception as e:
                self.logger.error(f"Erreur nettoyage ordres: {e}")
                await asyncio.sleep(3600)