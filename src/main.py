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
            
            logger.info("Initialisation terminée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {e}")
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
        
        if self.trading_engine:
            await self.trading_engine.stop()
        
        logger.info("Arrêt terminé")
    
    def get_status(self) -> dict:
        """Retourne le statut de l'application"""
        status = {
            "running": self.running,
            "trading_engine": None
        }
        
        if self.trading_engine:
            status["trading_engine"] = self.trading_engine.get_status()
        
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