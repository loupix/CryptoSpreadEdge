"""
Moteur de trading haute fréquence principal
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..market_data.market_data_manager import MarketDataManager
from ..order_management.order_manager import OrderManager
from ..risk_management.risk_manager import RiskManager


class TradingState(Enum):
    """États du moteur de trading"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class TradingConfig:
    """Configuration du moteur de trading"""
    max_positions: int = 10
    max_daily_loss: float = 1000.0
    max_position_size: float = 10000.0
    trading_enabled: bool = True
    risk_management_enabled: bool = True


class TradingEngine:
    """
    Moteur de trading haute fréquence principal
    
    Gère l'exécution des stratégies, la gestion des ordres
    et la coordination entre les différents composants.
    """
    
    def __init__(
        self,
        market_data_manager: MarketDataManager,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        config: TradingConfig
    ):
        self.market_data_manager = market_data_manager
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.config = config
        
        self.state = TradingState.STOPPED
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
    async def start(self) -> None:
        """Démarre le moteur de trading"""
        if self.state != TradingState.STOPPED:
            raise RuntimeError(f"Le moteur est déjà en état {self.state}")
            
        self.logger.info("Démarrage du moteur de trading...")
        self.state = TradingState.STARTING
        
        try:
            # Initialiser les composants
            await self.market_data_manager.start()
            await self.order_manager.start()
            await self.risk_manager.start()
            
            # Démarrer les tâches principales
            self._running = True
            self._tasks = [
                asyncio.create_task(self._main_loop()),
                asyncio.create_task(self._risk_monitoring_loop()),
                asyncio.create_task(self._order_processing_loop())
            ]
            
            self.state = TradingState.RUNNING
            self.logger.info("Moteur de trading démarré avec succès")
            
        except Exception as e:
            self.state = TradingState.ERROR
            self.logger.error(f"Erreur lors du démarrage: {e}")
            raise
    
    async def stop(self) -> None:
        """Arrête le moteur de trading"""
        if self.state not in [TradingState.RUNNING, TradingState.PAUSED]:
            return
            
        self.logger.info("Arrêt du moteur de trading...")
        self.state = TradingState.STOPPING
        
        # Arrêter les tâches
        self._running = False
        for task in self._tasks:
            task.cancel()
        
        # Attendre que les tâches se terminent
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Arrêter les composants
        await self.market_data_manager.stop()
        await self.order_manager.stop()
        await self.risk_manager.stop()
        
        self.state = TradingState.STOPPED
        self.logger.info("Moteur de trading arrêté")
    
    async def pause(self) -> None:
        """Met en pause le moteur de trading"""
        if self.state != TradingState.RUNNING:
            return
            
        self.state = TradingState.PAUSED
        self.logger.info("Moteur de trading en pause")
    
    async def resume(self) -> None:
        """Reprend le moteur de trading"""
        if self.state != TradingState.PAUSED:
            return
            
        self.state = TradingState.RUNNING
        self.logger.info("Moteur de trading repris")
    
    async def _main_loop(self) -> None:
        """Boucle principale du moteur de trading"""
        while self._running:
            try:
                if self.state == TradingState.RUNNING:
                    # Traiter les signaux de trading
                    await self._process_trading_signals()
                    
                    # Mettre à jour les positions
                    await self._update_positions()
                
                await asyncio.sleep(0.001)  # 1ms de latence
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle principale: {e}")
                await asyncio.sleep(0.1)
    
    async def _risk_monitoring_loop(self) -> None:
        """Boucle de monitoring des risques"""
        while self._running:
            try:
                if self.state in [TradingState.RUNNING, TradingState.PAUSED]:
                    # Vérifier les limites de risque
                    await self.risk_manager.check_limits()
                    
                    # Mettre à jour les métriques de risque
                    await self.risk_manager.update_metrics()
                
                await asyncio.sleep(0.1)  # 100ms
                
            except Exception as e:
                self.logger.error(f"Erreur dans le monitoring des risques: {e}")
                await asyncio.sleep(0.1)
    
    async def _order_processing_loop(self) -> None:
        """Boucle de traitement des ordres"""
        while self._running:
            try:
                if self.state == TradingState.RUNNING:
                    # Traiter les ordres en attente
                    await self.order_manager.process_pending_orders()
                    
                    # Mettre à jour le statut des ordres
                    await self.order_manager.update_order_status()
                
                await asyncio.sleep(0.01)  # 10ms
                
            except Exception as e:
                self.logger.error(f"Erreur dans le traitement des ordres: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_trading_signals(self) -> None:
        """Traite les signaux de trading"""
        try:
            # Récupérer les signaux des stratégies d'IA
            signals = await self._get_trading_signals()
            
            for signal in signals:
                # Vérifier les risques avant d'exécuter
                if await self.risk_manager.is_signal_safe(signal):
                    # Créer l'ordre basé sur le signal
                    order = await self._create_order_from_signal(signal)
                    if order:
                        # Placer l'ordre via le gestionnaire d'ordres
                        await self.order_manager.place_order(order)
                        self.logger.info(f"Ordre placé basé sur signal: {signal.symbol}")
                else:
                    self.logger.warning(f"Signal rejeté par gestion des risques: {signal.symbol}")
        
        except Exception as e:
            self.logger.error(f"Erreur traitement signaux: {e}")
    
    async def _get_trading_signals(self) -> List[Any]:
        """Récupère les signaux de trading des stratégies"""
        signals = []
        
        try:
            # Récupérer les données de marché
            market_data = await self.market_data_manager.get_latest_data()
            
            # Analyser les données avec les stratégies d'IA
            # TODO: Intégrer avec les modèles d'IA une fois implémentés
            # Pour l'instant, on simule des signaux basiques
            
            for symbol, data in market_data.items():
                if data and hasattr(data, 'ticker'):
                    # Logique simple de détection de tendance
                    if await self._detect_trend_signal(symbol, data):
                        signal = {
                            'symbol': symbol,
                            'action': 'buy',  # ou 'sell'
                            'confidence': 0.8,
                            'timestamp': datetime.utcnow()
                        }
                        signals.append(signal)
        
        except Exception as e:
            self.logger.error(f"Erreur récupération signaux: {e}")
        
        return signals
    
    async def _detect_trend_signal(self, symbol: str, data: Any) -> bool:
        """Détecte un signal de tendance basique"""
        try:
            # Logique simplifiée pour détecter des tendances
            # Dans une implémentation réelle, on utiliserait des indicateurs techniques
            
            if not data or not hasattr(data, 'ticker'):
                return False
            
            # Vérifier si le prix a augmenté significativement
            # (logique simplifiée - à remplacer par de vrais indicateurs)
            price_change = getattr(data.ticker, 'price_change_percent', 0)
            
            # Signal d'achat si augmentation > 2%
            return price_change > 2.0
        
        except Exception as e:
            self.logger.error(f"Erreur détection tendance {symbol}: {e}")
            return False
    
    async def _create_order_from_signal(self, signal: Dict[str, Any]) -> Optional[Any]:
        """Crée un ordre basé sur un signal"""
        try:
            from ..connectors.common.market_data_types import Order, OrderSide, OrderType
            
            # Calculer la quantité basée sur la gestion des risques
            quantity = await self._calculate_order_quantity(signal)
            if quantity <= 0:
                return None
            
            # Créer l'ordre
            order = Order(
                symbol=signal['symbol'],
                side=OrderSide.BUY if signal['action'] == 'buy' else OrderSide.SELL,
                order_type=OrderType.MARKET,  # Ordre au marché pour l'instant
                quantity=quantity,
                timestamp=datetime.utcnow()
            )
            
            return order
        
        except Exception as e:
            self.logger.error(f"Erreur création ordre: {e}")
            return None
    
    async def _calculate_order_quantity(self, signal: Dict[str, Any]) -> float:
        """Calcule la quantité d'un ordre basée sur la gestion des risques"""
        try:
            # Récupérer le prix actuel
            market_data = await self.market_data_manager.get_latest_data()
            symbol_data = market_data.get(signal['symbol'])
            
            if not symbol_data or not hasattr(symbol_data, 'ticker'):
                return 0.0
            
            current_price = symbol_data.ticker.price
            if current_price <= 0:
                return 0.0
            
            # Calculer la taille de position basée sur les limites de risque
            max_position_value = self.config.max_position_size
            confidence_factor = signal.get('confidence', 0.5)
            
            # Ajuster la taille selon la confiance
            position_value = max_position_value * confidence_factor
            
            # Calculer la quantité
            quantity = position_value / current_price
            
            return round(quantity, 6)  # Arrondir à 6 décimales
        
        except Exception as e:
            self.logger.error(f"Erreur calcul quantité: {e}")
            return 0.0
    
    async def _update_positions(self) -> None:
        """Met à jour les positions"""
        try:
            # Récupérer les positions actuelles depuis les exchanges
            positions = await self._get_current_positions()
            
            # Mettre à jour les positions dans le gestionnaire de risques
            for position in positions:
                await self.risk_manager.update_position(position)
            
            # Vérifier les positions pour des actions nécessaires
            await self._check_position_actions(positions)
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour positions: {e}")
    
    async def _get_current_positions(self) -> List[Any]:
        """Récupère les positions actuelles depuis tous les exchanges"""
        positions = []
        
        try:
            # Récupérer les positions depuis tous les connecteurs
            from ..connectors.connector_factory import connector_factory
            
            for exchange_id, connector in connector_factory.get_all_connectors().items():
                if connector.is_connected():
                    try:
                        exchange_positions = await connector.get_positions()
                        for position in exchange_positions:
                            position.source = exchange_id
                            positions.append(position)
                    except Exception as e:
                        self.logger.debug(f"Erreur récupération positions {exchange_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur récupération positions: {e}")
        
        return positions
    
    async def _check_position_actions(self, positions: List[Any]) -> None:
        """Vérifie les positions pour des actions nécessaires"""
        try:
            for position in positions:
                # Vérifier les positions avec des pertes importantes
                if hasattr(position, 'unrealized_pnl') and position.unrealized_pnl < -1000:
                    self.logger.warning(f"Position avec perte importante: {position.symbol} = {position.unrealized_pnl}")
                
                # Vérifier les positions qui approchent des limites
                if hasattr(position, 'quantity') and abs(position.quantity) > 0:
                    # Calculer la valeur de la position
                    market_data = await self.market_data_manager.get_latest_data()
                    symbol_data = market_data.get(position.symbol)
                    
                    if symbol_data and hasattr(symbol_data, 'ticker'):
                        position_value = abs(position.quantity) * symbol_data.ticker.price
                        
                        # Vérifier si la position dépasse les limites
                        if position_value > self.config.max_position_size:
                            self.logger.warning(f"Position dépasse limite: {position.symbol} = {position_value}")
        
        except Exception as e:
            self.logger.error(f"Erreur vérification actions positions: {e}")
    
    def get_status(self) -> Dict:
        """Retourne le statut du moteur"""
        return {
            "state": self.state.value,
            "running": self._running,
            "config": {
                "max_positions": self.config.max_positions,
                "max_daily_loss": self.config.max_daily_loss,
                "trading_enabled": self.config.trading_enabled,
                "risk_management_enabled": self.config.risk_management_enabled
            },
            "timestamp": datetime.utcnow().isoformat()
        }