"""
Point d'entrée principal de CryptoSpreadEdge
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from .core.trading_engine.engine import TradingEngine, TradingConfig
from .core.market_data.market_data_manager import MarketDataManager, MarketDataConfig, DataSource
from .core.order_management.order_manager import OrderManager, OrderManagerConfig
from .core.risk_management.risk_manager import RiskManager, RiskLimits
from .arbitrage.arbitrage_engine import arbitrage_engine
from .arbitrage.price_monitor import price_monitor
from .arbitrage.execution_engine import execution_engine
from .arbitrage.risk_manager import arbitrage_risk_manager


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/cryptospreadedge.log')
    ]
)

logger = logging.getLogger(__name__)


class CryptoSpreadEdgeApp:
    """Application principale CryptoSpreadEdge"""
    
    def __init__(self):
        self.trading_engine: Optional[TradingEngine] = None
        self.arbitrage_enabled = True
        self.running = False
        
    async def initialize(self) -> None:
        """Initialise l'application"""
        logger.info("Initialisation de CryptoSpreadEdge...")
        
        try:
            # Configuration des composants
            market_config = MarketDataConfig(
                symbols=["BTC/USDT", "ETH/USDT", "BNB/USDT"],
                data_sources=[DataSource.BINANCE, DataSource.COINBASE],
                update_frequency=0.1
            )
            
            order_config = OrderManagerConfig(
                max_pending_orders=100,
                order_timeout=30.0
            )
            
            risk_limits = RiskLimits(
                max_daily_loss=1000.0,
                max_position_size=10000.0,
                max_total_exposure=50000.0
            )
            
            trading_config = TradingConfig(
                max_positions=10,
                max_daily_loss=1000.0,
                trading_enabled=True
            )
            
            # Créer les composants
            market_data_manager = MarketDataManager(market_config)
            order_manager = OrderManager(order_config)
            risk_manager = RiskManager(risk_limits)
            
            # Créer le moteur de trading
            self.trading_engine = TradingEngine(
                market_data_manager=market_data_manager,
                order_manager=order_manager,
                risk_manager=risk_manager,
                config=trading_config
            )
            
            # Initialiser le système d'arbitrage si activé
            if self.arbitrage_enabled:
                logger.info("Initialisation du système d'arbitrage...")
                await self._initialize_arbitrage_system()
            
            logger.info("Initialisation terminée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {e}")
            raise
    
    async def _initialize_arbitrage_system(self) -> None:
        """Initialise le système d'arbitrage"""
        try:
            # Démarrer le monitoring des prix
            await price_monitor.start()
            logger.info("PriceMonitor démarré")
            
            # Démarrer le moteur d'exécution
            await execution_engine.start()
            logger.info("ExecutionEngine démarré")
            
            # Démarrer le gestionnaire de risques d'arbitrage
            await arbitrage_risk_manager.start_monitoring()
            logger.info("ArbitrageRiskManager démarré")
            
            # Démarrer le moteur d'arbitrage
            await arbitrage_engine.start()
            logger.info("ArbitrageEngine démarré")
            
        except Exception as e:
            logger.error(f"Erreur initialisation système d'arbitrage: {e}")
            raise
    
    async def start(self) -> None:
        """Démarre l'application"""
        if not self.trading_engine:
            raise RuntimeError("Application non initialisée")
        
        logger.info("Démarrage de CryptoSpreadEdge...")
        self.running = True
        
        try:
            # Démarrer le moteur de trading
            await self.trading_engine.start()
            
            # Démarrer le système d'arbitrage si activé
            if self.arbitrage_enabled:
                logger.info("Système d'arbitrage activé et en cours d'exécution")
            
            # Démarrer le monitoring des performances
            monitoring_task = asyncio.create_task(self._monitor_performance())
            
            # Attendre indéfiniment
            while self.running:
                await asyncio.sleep(1.0)
                
        except KeyboardInterrupt:
            logger.info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Arrête l'application"""
        if not self.running:
            return
        
        logger.info("Arrêt de CryptoSpreadEdge...")
        self.running = False
        
        # Arrêter le système d'arbitrage si activé
        if self.arbitrage_enabled:
            try:
                await arbitrage_engine.stop()
                await execution_engine.stop()
                await price_monitor.stop()
                await arbitrage_risk_manager.stop_monitoring()
                logger.info("Système d'arbitrage arrêté")
            except Exception as e:
                logger.error(f"Erreur arrêt système d'arbitrage: {e}")
        
        # Arrêter le moteur de trading
        if self.trading_engine:
            await self.trading_engine.stop()
        
        logger.info("Arrêt terminé")
    
    async def _monitor_performance(self) -> None:
        """Surveille les performances du système"""
        while self.running:
            try:
                # Afficher les statistiques toutes les 30 secondes
                await asyncio.sleep(30)
                
                if self.arbitrage_enabled:
                    # Statistiques d'arbitrage
                    arb_stats = arbitrage_engine.get_statistics()
                    price_stats = price_monitor.get_statistics()
                    exec_stats = execution_engine.get_statistics()
                    
                    logger.info(f"Arbitrage - Opportunités: {arb_stats['opportunities_found']}, "
                              f"Exécutées: {arb_stats['opportunities_executed']}, "
                              f"Profit: {arb_stats['net_profit']:.2f} USD")
                    
                    logger.info(f"Prix - Plateformes: {price_stats['total_platforms']}, "
                              f"Symboles: {price_stats['symbols_monitored']}, "
                              f"Alertes: {price_stats['active_alerts']}")
                
                # Statistiques du moteur de trading
                if self.trading_engine:
                    trading_status = self.trading_engine.get_status()
                    logger.info(f"Trading - État: {trading_status['state']}, "
                              f"Positions max: {trading_status['config']['max_positions']}")
            
            except Exception as e:
                logger.error(f"Erreur monitoring performances: {e}")
                await asyncio.sleep(30)
    
    def get_status(self) -> dict:
        """Retourne le statut de l'application"""
        status = {
            "running": self.running,
            "arbitrage_enabled": self.arbitrage_enabled,
            "trading_engine": None,
            "arbitrage_system": None
        }
        
        if self.trading_engine:
            status["trading_engine"] = self.trading_engine.get_status()
        
        if self.arbitrage_enabled:
            status["arbitrage_system"] = {
                "arbitrage_engine": arbitrage_engine.get_statistics(),
                "price_monitor": price_monitor.get_statistics(),
                "execution_engine": execution_engine.get_statistics(),
                "risk_manager": arbitrage_risk_manager.get_risk_status()
            }
        
        return status


async def main():
    """Fonction principale"""
    app = CryptoSpreadEdgeApp()
    
    # Gestionnaire de signaux pour l'arrêt propre
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} reçu, arrêt en cours...")
        asyncio.create_task(app.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await app.initialize()
        await app.start()
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())