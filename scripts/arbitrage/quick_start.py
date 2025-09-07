#!/usr/bin/env python3
"""
Démarrage rapide du système d'arbitrage CryptoSpreadEdge
"""

import asyncio
import logging
import sys
import os
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class QuickStartArbitrage:
    """Démarrage rapide du système d'arbitrage"""
    
    def __init__(self):
        self.running = False
    
    async def start(self):
        """Démarre le système d'arbitrage en mode rapide"""
        print("🚀 CryptoSpreadEdge - Démarrage Rapide de l'Arbitrage")
        print("=" * 60)
        print("Mode: Démonstration (pas de vrais trades)")
        print("Durée: 2 minutes")
        print("=" * 60)
        
        self.running = True
        
        try:
            # Démarrer les composants
            print("\n📊 Démarrage des composants...")
            await self._start_components()
            
            # Attendre et afficher les résultats
            print("\n⏱️ Surveillance en cours (2 minutes)...")
            await self._monitor_for_duration(120)  # 2 minutes
            
            # Afficher les résultats
            print("\n📈 Résultats de la session:")
            await self._show_results()
            
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
        finally:
            await self._stop_components()
    
    async def _start_components(self):
        """Démarre tous les composants"""
        try:
            # Démarrer le PriceMonitor
            print("  📊 PriceMonitor...")
            await price_monitor.start()
            
            # Démarrer l'ExecutionEngine
            print("  ⚡ ExecutionEngine...")
            await execution_engine.start()
            
            # Démarrer le RiskManager
            print("  🛡️ RiskManager...")
            await arbitrage_risk_manager.start_monitoring()
            
            # Démarrer l'ArbitrageEngine
            print("  🎯 ArbitrageEngine...")
            await arbitrage_engine.start()
            
            print("✅ Tous les composants démarrés!")
            
        except Exception as e:
            logger.error(f"Erreur démarrage composants: {e}")
            raise
    
    async def _monitor_for_duration(self, duration_seconds: int):
        """Surveille le système pendant une durée donnée"""
        start_time = asyncio.get_event_loop().time()
        
        while self.running:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time
            
            if elapsed >= duration_seconds:
                break
            
            # Afficher le progrès toutes les 30 secondes
            if int(elapsed) % 30 == 0 and elapsed > 0:
                remaining = duration_seconds - elapsed
                print(f"⏱️ Temps restant: {remaining:.0f}s")
                
                # Afficher les statistiques rapides
                await self._show_quick_stats()
            
            await asyncio.sleep(1)
    
    async def _show_quick_stats(self):
        """Affiche les statistiques rapides"""
        try:
            arb_stats = arbitrage_engine.get_statistics()
            price_stats = price_monitor.get_statistics()
            
            print(f"  📊 Prix surveillés: {price_stats.get('symbols_monitored', 0)}")
            print(f"  🎯 Opportunités: {arb_stats.get('opportunities_found', 0)}")
            print(f"  💰 Profit: {arb_stats.get('net_profit', 0):.2f} USD")
            
        except Exception as e:
            logger.debug(f"Erreur affichage stats: {e}")
    
    async def _show_results(self):
        """Affiche les résultats finaux"""
        try:
            # Statistiques d'arbitrage
            arb_stats = arbitrage_engine.get_statistics()
            print(f"\n🎯 Arbitrage:")
            print(f"  Opportunités trouvées: {arb_stats.get('opportunities_found', 0)}")
            print(f"  Opportunités exécutées: {arb_stats.get('opportunities_executed', 0)}")
            print(f"  Profit net: {arb_stats.get('net_profit', 0):.2f} USD")
            print(f"  Taux de succès: {arb_stats.get('success_rate', 0):.1%}")
            
            # Statistiques de prix
            price_stats = price_monitor.get_statistics()
            print(f"\n📊 Prix:")
            print(f"  Plateformes surveillées: {price_stats.get('total_platforms', 0)}")
            print(f"  Symboles surveillés: {price_stats.get('symbols_monitored', 0)}")
            print(f"  Mises à jour: {price_stats.get('total_updates', 0)}")
            print(f"  Alertes: {price_stats.get('active_alerts', 0)}")
            
            # Statistiques d'exécution
            exec_stats = execution_engine.get_statistics()
            print(f"\n⚡ Exécution:")
            print(f"  Exécutions totales: {exec_stats.get('total_executions', 0)}")
            print(f"  Exécutions réussies: {exec_stats.get('successful_executions', 0)}")
            print(f"  Taux de succès: {exec_stats.get('success_rate', 0):.1%}")
            print(f"  Temps moyen: {exec_stats.get('avg_execution_time', 0):.2f}s")
            
            # Statistiques de risque
            risk_stats = arbitrage_risk_manager.get_risk_status()
            print(f"\n🛡️ Risque:")
            print(f"  Position actuelle: {risk_stats['metrics']['current_position']:.2f} USD")
            print(f"  PnL quotidien: {risk_stats['metrics']['daily_pnl']:.2f} USD")
            print(f"  Trades quotidiens: {risk_stats['metrics']['daily_trades']}")
            print(f"  Taux de réussite: {risk_stats['metrics']['win_rate']:.1%}")
            
        except Exception as e:
            logger.error(f"Erreur affichage résultats: {e}")
    
    async def _stop_components(self):
        """Arrête tous les composants"""
        print("\n🛑 Arrêt des composants...")
        
        try:
            # Arrêter l'ArbitrageEngine
            print("  🎯 ArbitrageEngine...")
            await arbitrage_engine.stop()
            
            # Arrêter le RiskManager
            print("  🛡️ RiskManager...")
            await arbitrage_risk_manager.stop_monitoring()
            
            # Arrêter l'ExecutionEngine
            print("  ⚡ ExecutionEngine...")
            await execution_engine.stop()
            
            # Arrêter le PriceMonitor
            print("  📊 PriceMonitor...")
            await price_monitor.stop()
            
            print("✅ Tous les composants arrêtés!")
            
        except Exception as e:
            logger.error(f"Erreur arrêt composants: {e}")
        
        self.running = False


async def main():
    """Fonction principale"""
    quick_start = QuickStartArbitrage()
    await quick_start.start()


if __name__ == "__main__":
    # Créer le répertoire de logs s'il n'existe pas
    Path("logs").mkdir(exist_ok=True)
    
    print("🎯 CryptoSpreadEdge - Démarrage Rapide de l'Arbitrage")
    print("=" * 60)
    print("Ce script démarre le système d'arbitrage en mode démonstration")
    print("pour une durée de 2 minutes.")
    print("=" * 60)
    print("Appuyez sur Ctrl+C pour arrêter prématurément")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)