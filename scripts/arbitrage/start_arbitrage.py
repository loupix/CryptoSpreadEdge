"""
Script de démarrage du système d'arbitrage CryptoSpreadEdge
"""

import sys
import asyncio
import logging
import signal
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.arbitrage.arbitrage_engine import arbitrage_engine
from src.arbitrage.price_monitor import price_monitor
from src.arbitrage.execution_engine import execution_engine
from src.arbitrage.risk_manager import arbitrage_risk_manager
from src.arbitrage.profit_calculator import profit_calculator
from src.connectors.connector_factory import connector_factory
from src.data_sources.data_aggregator import data_aggregator
from config.api_keys_manager import api_keys_manager


class ArbitrageSystem:
    """Système d'arbitrage principal"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.is_running = False
        self.tasks = []
    
    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/arbitrage.log')
            ]
        )
    
    async def start(self, mode: str = "live"):
        """Démarre le système d'arbitrage"""
        try:
            self.logger.info(f"Démarrage du système d'arbitrage en mode {mode}")
            self.is_running = True
            
            # Créer le répertoire de logs
            Path("logs").mkdir(exist_ok=True)
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Démarrer les services
            await self._start_services()
            
            # Afficher le statut
            await self._show_status()
            
            # Démarrer la boucle principale
            await self._main_loop()
        
        except Exception as e:
            self.logger.error(f"Erreur démarrage système: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Arrête le système d'arbitrage"""
        self.logger.info("Arrêt du système d'arbitrage")
        self.is_running = False
        
        # Arrêter tous les services
        await self._stop_services()
        
        # Annuler toutes les tâches
        for task in self.tasks:
            task.cancel()
        
        # Attendre que toutes les tâches se terminent
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.logger.info("Système d'arbitrage arrêté")
    
    async def _initialize_components(self):
        """Initialise tous les composants"""
        try:
            self.logger.info("Initialisation des composants...")
            
            # Vérifier les clés API
            api_summary = api_keys_manager.get_summary()
            if api_summary["platforms_ready_for_trading"] == 0:
                self.logger.warning("Aucune plateforme prête pour le trading")
                self.logger.info("Configurez vos clés API avec: python scripts/setup/configure_platforms.py")
            
            # Initialiser l'agrégateur de données
            await data_aggregator.initialize_connectors()
            
            # Initialiser le gestionnaire de risques
            await arbitrage_risk_manager.start_monitoring()
            
            # Initialiser le moteur d'exécution
            await execution_engine.start()
            
            self.logger.info("Composants initialisés avec succès")
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation composants: {e}")
            raise
    
    async def _start_services(self):
        """Démarre tous les services"""
        try:
            self.logger.info("Démarrage des services...")
            
            # Démarrer le monitoring des prix
            price_task = asyncio.create_task(price_monitor.start())
            self.tasks.append(price_task)
            
            # Démarrer le moteur d'arbitrage
            arbitrage_task = asyncio.create_task(arbitrage_engine.start())
            self.tasks.append(arbitrage_task)
            
            # Démarrer le monitoring du système
            monitoring_task = asyncio.create_task(self._monitor_system())
            self.tasks.append(monitoring_task)
            
            # Démarrer l'affichage des statistiques
            stats_task = asyncio.create_task(self._display_statistics())
            self.tasks.append(stats_task)
            
            self.logger.info("Services démarrés avec succès")
        
        except Exception as e:
            self.logger.error(f"Erreur démarrage services: {e}")
            raise
    
    async def _stop_services(self):
        """Arrête tous les services"""
        try:
            self.logger.info("Arrêt des services...")
            
            # Arrêter le moteur d'arbitrage
            await arbitrage_engine.stop()
            
            # Arrêter le monitoring des prix
            await price_monitor.stop()
            
            # Arrêter le moteur d'exécution
            await execution_engine.stop()
            
            # Arrêter le gestionnaire de risques
            await arbitrage_risk_manager.stop_monitoring()
            
            self.logger.info("Services arrêtés avec succès")
        
        except Exception as e:
            self.logger.error(f"Erreur arrêt services: {e}")
    
    async def _monitor_system(self):
        """Surveille le système en continu"""
        while self.is_running:
            try:
                # Vérifier la santé du système
                await self._check_system_health()
                
                # Nettoyer les données anciennes
                await self._cleanup_old_data()
                
                await asyncio.sleep(30)  # Vérification toutes les 30 secondes
            
            except Exception as e:
                self.logger.error(f"Erreur monitoring système: {e}")
                await asyncio.sleep(30)
    
    async def _check_system_health(self):
        """Vérifie la santé du système"""
        try:
            # Vérifier les connecteurs
            connected_exchanges = len([
                connector for connector in connector_factory.get_all_connectors().values()
                if connector.is_connected()
            ])
            
            if connected_exchanges == 0:
                self.logger.warning("Aucun exchange connecté")
            
            # Vérifier les alertes de risque
            risk_alerts = arbitrage_risk_manager.get_recent_alerts(5)
            if risk_alerts:
                for alert in risk_alerts:
                    self.logger.warning(f"Alerte risque: {alert['message']}")
            
            # Vérifier les performances
            arbitrage_stats = arbitrage_engine.get_statistics()
            if arbitrage_stats["success_rate"] < 0.5:
                self.logger.warning(f"Taux de succès faible: {arbitrage_stats['success_rate']:.2%}")
        
        except Exception as e:
            self.logger.error(f"Erreur vérification santé: {e}")
    
    async def _cleanup_old_data(self):
        """Nettoie les données anciennes"""
        try:
            # Nettoyer l'historique des calculs de profit
            if len(profit_calculator.calculation_history) > 1000:
                profit_calculator.calculation_history = profit_calculator.calculation_history[-1000:]
            
            # Nettoyer l'historique des trades
            if len(arbitrage_risk_manager.trade_history) > 1000:
                arbitrage_risk_manager.trade_history = arbitrage_risk_manager.trade_history[-1000:]
        
        except Exception as e:
            self.logger.error(f"Erreur nettoyage données: {e}")
    
    async def _display_statistics(self):
        """Affiche les statistiques périodiquement"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Affichage toutes les minutes
                
                if not self.is_running:
                    break
                
                # Afficher les statistiques
                await self._show_status()
            
            except Exception as e:
                self.logger.error(f"Erreur affichage statistiques: {e}")
    
    async def _show_status(self):
        """Affiche le statut du système"""
        try:
            print("\n" + "="*80)
            print("STATUT DU SYSTÈME D'ARBITRAGE CRYPTOSPREADEDGE")
            print("="*80)
            
            # Statut général
            print(f"Mode: {'LIVE' if self.is_running else 'ARRÊTÉ'}")
            print(f"Temps de fonctionnement: {self._get_uptime()}")
            
            # Statut des connecteurs
            connected_exchanges = [
                name for name, connector in connector_factory.get_all_connectors().items()
                if connector.is_connected()
            ]
            print(f"Exchanges connectés: {len(connected_exchanges)}")
            if connected_exchanges:
                print(f"  {', '.join(connected_exchanges)}")
            
            # Statistiques d'arbitrage
            arbitrage_stats = arbitrage_engine.get_statistics()
            print(f"\nArbitrage:")
            print(f"  Opportunités trouvées: {arbitrage_stats['opportunities_found']}")
            print(f"  Opportunités exécutées: {arbitrage_stats['opportunities_executed']}")
            print(f"  Taux de succès: {arbitrage_stats['success_rate']:.2%}")
            print(f"  Profit total: {arbitrage_stats['total_profit']:.2f} USD")
            print(f"  Frais totaux: {arbitrage_stats['total_fees']:.2f} USD")
            print(f"  Profit net: {arbitrage_stats['net_profit']:.2f} USD")
            
            # Statistiques de monitoring
            price_stats = price_monitor.get_statistics()
            print(f"\nMonitoring des prix:")
            print(f"  Symboles surveillés: {price_stats['symbols_monitored']}")
            print(f"  Plateformes totales: {price_stats['total_platforms']}")
            print(f"  Mises à jour: {price_stats['total_updates']}")
            print(f"  Temps de réponse moyen: {price_stats['avg_update_time']:.2f}ms")
            
            # Statistiques de risque
            risk_status = arbitrage_risk_manager.get_risk_status()
            print(f"\nGestion des risques:")
            print(f"  Position actuelle: {risk_status['metrics']['current_position']:.2f} USD")
            print(f"  PnL quotidien: {risk_status['metrics']['daily_pnl']:.2f} USD")
            print(f"  Trades quotidiens: {risk_status['metrics']['daily_trades']}")
            print(f"  Taux de réussite: {risk_status['metrics']['win_rate']:.2%}")
            print(f"  Alertes actives: {risk_status['alerts_count']}")
            
            # Statistiques d'exécution
            execution_stats = execution_engine.get_statistics()
            print(f"\nExécution:")
            print(f"  Exécutions totales: {execution_stats['total_executions']}")
            print(f"  Exécutions réussies: {execution_stats['successful_executions']}")
            print(f"  Taux de succès: {execution_stats['success_rate']:.2%}")
            print(f"  Temps d'exécution moyen: {execution_stats['avg_execution_time']:.2f}s")
            
            # Opportunités récentes
            recent_opportunities = arbitrage_engine.get_recent_opportunities(3)
            if recent_opportunities:
                print(f"\nOpportunités récentes:")
                for i, opp in enumerate(recent_opportunities):
                    print(f"  {i+1}. {opp.symbol}: {opp.buy_exchange} -> {opp.sell_exchange} "
                          f"({opp.spread_percentage:.2%}, confiance: {opp.confidence:.2%})")
            
            print("="*80)
        
        except Exception as e:
            self.logger.error(f"Erreur affichage statut: {e}")
    
    def _get_uptime(self) -> str:
        """Retourne le temps de fonctionnement"""
        if not self.is_running:
            return "N/A"
        
        # Dans une implémentation réelle, on stockerait le temps de démarrage
        return "En cours..."
    
    async def _main_loop(self):
        """Boucle principale du système"""
        try:
            self.logger.info("Système d'arbitrage démarré avec succès")
            self.logger.info("Appuyez sur Ctrl+C pour arrêter")
            
            # Attendre indéfiniment
            while self.is_running:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            self.logger.info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            self.logger.error(f"Erreur boucle principale: {e}")
        finally:
            await self.stop()


def setup_signal_handlers(system: ArbitrageSystem):
    """Configure les gestionnaires de signaux"""
    def signal_handler(signum, frame):
        print(f"\nSignal {signum} reçu, arrêt du système...")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Système d'arbitrage CryptoSpreadEdge")
    parser.add_argument('--mode', choices=['live', 'test'], default='live',
                       help='Mode de fonctionnement (défaut: live)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                       help='Niveau de logging (défaut: INFO)')
    
    args = parser.parse_args()
    
    # Configurer le logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Créer le système
    system = ArbitrageSystem()
    
    # Configurer les gestionnaires de signaux
    setup_signal_handlers(system)
    
    try:
        # Démarrer le système
        await system.start(args.mode)
    except Exception as e:
        logging.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())