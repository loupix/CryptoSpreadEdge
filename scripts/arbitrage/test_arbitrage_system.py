#!/usr/bin/env python3
"""
Script de test pour le système d'arbitrage CryptoSpreadEdge
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
from arbitrage.profit_calculator import ProfitCalculator
from connectors.connector_factory import connector_factory


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ArbitrageSystemTester:
    """Testeur du système d'arbitrage"""
    
    def __init__(self):
        self.test_results = {}
        self.profit_calculator = ProfitCalculator()
    
    async def run_all_tests(self):
        """Lance tous les tests"""
        logger.info("=== Début des tests du système d'arbitrage ===")
        
        tests = [
            ("Test des connecteurs", self.test_connectors),
            ("Test du PriceMonitor", self.test_price_monitor),
            ("Test du ProfitCalculator", self.test_profit_calculator),
            ("Test du RiskManager", self.test_risk_manager),
            ("Test de l'ExecutionEngine", self.test_execution_engine),
            ("Test de l'ArbitrageEngine", self.test_arbitrage_engine),
            ("Test d'intégration", self.test_integration)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"Exécution: {test_name}")
                result = await test_func()
                self.test_results[test_name] = result
                status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
                logger.info(f"{test_name}: {status}")
            except Exception as e:
                logger.error(f"{test_name}: ❌ ERREUR - {e}")
                self.test_results[test_name] = False
        
        self.print_summary()
    
    async def test_connectors(self) -> bool:
        """Test des connecteurs"""
        try:
            # Tester la factory
            connectors = connector_factory.get_all_connectors()
            if not connectors:
                logger.warning("Aucun connecteur disponible")
                return False
            
            logger.info(f"Connecteurs disponibles: {list(connectors.keys())}")
            
            # Tester la création d'un connecteur
            binance_connector = connector_factory.get_connector("binance")
            if binance_connector:
                logger.info("Connecteur Binance créé avec succès")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Erreur test connecteurs: {e}")
            return False
    
    async def test_price_monitor(self) -> bool:
        """Test du PriceMonitor"""
        try:
            # Démarrer le PriceMonitor
            await price_monitor.start()
            
            # Attendre un peu pour la collecte de données
            await asyncio.sleep(5)
            
            # Vérifier les statistiques
            stats = price_monitor.get_statistics()
            logger.info(f"Statistiques PriceMonitor: {stats}")
            
            # Arrêter le PriceMonitor
            await price_monitor.stop()
            
            return stats["total_updates"] > 0
        
        except Exception as e:
            logger.error(f"Erreur test PriceMonitor: {e}")
            return False
    
    async def test_profit_calculator(self) -> bool:
        """Test du ProfitCalculator"""
        try:
            # Créer une opportunité d'arbitrage fictive
            from arbitrage.arbitrage_engine import ArbitrageOpportunity
            from datetime import datetime
            
            opportunity = ArbitrageOpportunity(
                symbol="BTC/USDT",
                buy_exchange="binance",
                sell_exchange="okx",
                buy_price=50000.0,
                sell_price=50100.0,
                spread=100.0,
                spread_percentage=0.002,
                volume_available=1.0,
                max_profit=100.0,
                confidence=0.9,
                timestamp=datetime.utcnow(),
                execution_time_estimate=2.0,
                risk_score=0.3
            )
            
            # Calculer le profit
            calculation = self.profit_calculator.calculate_profit(opportunity, 1.0)
            logger.info(f"Calcul de profit: {calculation}")
            
            return calculation.net_profit > 0
        
        except Exception as e:
            logger.error(f"Erreur test ProfitCalculator: {e}")
            return False
    
    async def test_risk_manager(self) -> bool:
        """Test du RiskManager"""
        try:
            # Démarrer le RiskManager
            await arbitrage_risk_manager.start_monitoring()
            
            # Vérifier le statut
            status = arbitrage_risk_manager.get_risk_status()
            logger.info(f"Statut RiskManager: {status}")
            
            # Arrêter le RiskManager
            await arbitrage_risk_manager.stop_monitoring()
            
            return status["is_monitoring"] is False  # Vérifier qu'il s'est arrêté correctement
        
        except Exception as e:
            logger.error(f"Erreur test RiskManager: {e}")
            return False
    
    async def test_execution_engine(self) -> bool:
        """Test de l'ExecutionEngine"""
        try:
            # Démarrer l'ExecutionEngine
            await execution_engine.start()
            
            # Vérifier les statistiques
            stats = execution_engine.get_statistics()
            logger.info(f"Statistiques ExecutionEngine: {stats}")
            
            # Arrêter l'ExecutionEngine
            await execution_engine.stop()
            
            return stats["is_running"] is False  # Vérifier qu'il s'est arrêté correctement
        
        except Exception as e:
            logger.error(f"Erreur test ExecutionEngine: {e}")
            return False
    
    async def test_arbitrage_engine(self) -> bool:
        """Test de l'ArbitrageEngine"""
        try:
            # Vérifier les statistiques initiales
            stats = arbitrage_engine.get_statistics()
            logger.info(f"Statistiques ArbitrageEngine: {stats}")
            
            # Vérifier que le moteur n'est pas en cours d'exécution
            return not arbitrage_engine.is_running
        
        except Exception as e:
            logger.error(f"Erreur test ArbitrageEngine: {e}")
            return False
    
    async def test_integration(self) -> bool:
        """Test d'intégration du système complet"""
        try:
            logger.info("Test d'intégration du système d'arbitrage...")
            
            # Démarrer tous les composants
            await price_monitor.start()
            await execution_engine.start()
            await arbitrage_risk_manager.start_monitoring()
            
            # Attendre un peu pour la collecte de données
            await asyncio.sleep(10)
            
            # Vérifier que tous les composants fonctionnent
            price_stats = price_monitor.get_statistics()
            exec_stats = execution_engine.get_statistics()
            risk_status = arbitrage_risk_manager.get_risk_status()
            
            logger.info(f"Intégration - Prix: {price_stats['is_running']}, "
                       f"Exécution: {exec_stats['is_running']}, "
                       f"Risque: {risk_status['is_monitoring']}")
            
            # Arrêter tous les composants
            await arbitrage_risk_manager.stop_monitoring()
            await execution_engine.stop()
            await price_monitor.stop()
            
            return (price_stats['is_running'] and 
                   exec_stats['is_running'] and 
                   risk_status['is_monitoring'])
        
        except Exception as e:
            logger.error(f"Erreur test intégration: {e}")
            return False
    
    def print_summary(self):
        """Affiche le résumé des tests"""
        logger.info("\n=== RÉSUMÉ DES TESTS ===")
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nRésultat global: {passed}/{total} tests passés")
        
        if passed == total:
            logger.info("🎉 Tous les tests sont passés avec succès!")
        else:
            logger.warning(f"⚠️  {total - passed} test(s) ont échoué")


async def main():
    """Fonction principale"""
    tester = ArbitrageSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())