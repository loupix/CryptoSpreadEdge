#!/usr/bin/env python3
"""
Script de démarrage du système d'arbitrage CryptoSpreadEdge
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from arbitrage.arbitrage_engine import arbitrage_engine
from arbitrage.price_monitor import price_monitor
from arbitrage.execution_engine import execution_engine
from arbitrage.risk_manager import arbitrage_risk_manager


# Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
        logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/arbitrage.log')
            ]
        )
    
logger = logging.getLogger(__name__)


class ArbitrageSystem:
    """Système d'arbitrage autonome"""
    
    def __init__(self):
        self.running = False
        self.components = {
            'price_monitor': price_monitor,
            'execution_engine': execution_engine,
            'risk_manager': arbitrage_risk_manager,
            'arbitrage_engine': arbitrage_engine
        }
    
    async def start(self):
        """Démarre le système d'arbitrage"""
        logger.info("🚀 Démarrage du système d'arbitrage CryptoSpreadEdge")
        self.running = True
        
        try:
            # Démarrer les composants dans l'ordre
            logger.info("📊 Démarrage du PriceMonitor...")
            await self.components['price_monitor'].start()
            
            logger.info("⚡ Démarrage de l'ExecutionEngine...")
            await self.components['execution_engine'].start()
            
            logger.info("🛡️ Démarrage du RiskManager...")
            await self.components['risk_manager'].start_monitoring()
            
            logger.info("🎯 Démarrage de l'ArbitrageEngine...")
            await self.components['arbitrage_engine'].start()
            
            logger.info("✅ Système d'arbitrage démarré avec succès!")
            
            # Démarrer le monitoring des performances
            monitoring_task = asyncio.create_task(self._monitor_performance())
            
            # Attendre indéfiniment
            while self.running:
                await asyncio.sleep(1.0)
        
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Arrête le système d'arbitrage"""
        if not self.running:
            return
        
        logger.info("🛑 Arrêt du système d'arbitrage...")
        self.running = False
        
        # Arrêter les composants dans l'ordre inverse
        try:
            logger.info("Arrêt de l'ArbitrageEngine...")
            await self.components['arbitrage_engine'].stop()
            
            logger.info("Arrêt du RiskManager...")
            await self.components['risk_manager'].stop_monitoring()
            
            logger.info("Arrêt de l'ExecutionEngine...")
            await self.components['execution_engine'].stop()
            
            logger.info("Arrêt du PriceMonitor...")
            await self.components['price_monitor'].stop()
            
            logger.info("✅ Système d'arbitrage arrêté avec succès!")
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'arrêt: {e}")
    
    async def _monitor_performance(self):
        """Surveille les performances du système"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Rapport toutes les 30 secondes
                
                # Statistiques d'arbitrage
                arb_stats = arbitrage_engine.get_statistics()
                price_stats = price_monitor.get_statistics()
                exec_stats = execution_engine.get_statistics()
                risk_status = arbitrage_risk_manager.get_risk_status()
                
                logger.info("📈 === RAPPORT DE PERFORMANCE ===")
                logger.info(f"🎯 Arbitrage - Opportunités trouvées: {arb_stats['opportunities_found']}")
                logger.info(f"💰 Arbitrage - Opportunités exécutées: {arb_stats['opportunities_executed']}")
                logger.info(f"💵 Arbitrage - Profit net: {arb_stats['net_profit']:.2f} USD")
                logger.info(f"📊 Prix - Plateformes surveillées: {price_stats['total_platforms']}")
                logger.info(f"🔍 Prix - Symboles surveillés: {price_stats['symbols_monitored']}")
                logger.info(f"⚠️ Prix - Alertes actives: {price_stats['active_alerts']}")
                logger.info(f"⚡ Exécution - Taux de succès: {exec_stats['success_rate']:.2%}")
                logger.info(f"🛡️ Risque - Monitoring actif: {risk_status['is_monitoring']}")
                logger.info("=" * 50)
            
            except Exception as e:
                logger.error(f"❌ Erreur monitoring performances: {e}")
                await asyncio.sleep(30)
    
    def get_status(self):
        """Retourne le statut du système"""
        return {
            "running": self.running,
            "components": {
                name: {
                    "running": getattr(component, 'is_running', False),
                    "statistics": getattr(component, 'get_statistics', lambda: {})()
                }
                for name, component in self.components.items()
            }
        }


async def main():
    """Fonction principale"""
    system = ArbitrageSystem()
    
    # Gestionnaire de signaux pour l'arrêt propre
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} reçu, arrêt en cours...")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Créer le répertoire de logs s'il n'existe pas
    Path("logs").mkdir(exist_ok=True)
    
    print("🚀 CryptoSpreadEdge - Système d'Arbitrage")
    print("=" * 50)
    print("Démarrage en cours...")
    print("Appuyez sur Ctrl+C pour arrêter")
    print("=" * 50)
    
    asyncio.run(main())