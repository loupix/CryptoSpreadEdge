"""
Moteur de trading haute fréquence principal
"""

import asyncio
import logging
from typing import Dict, List, Optional
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
        # TODO: Implémenter la logique de traitement des signaux
        # Cette méthode sera appelée par les stratégies d'IA
        pass
    
    async def _update_positions(self) -> None:
        """Met à jour les positions"""
        # TODO: Implémenter la logique de mise à jour des positions
        pass
    
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