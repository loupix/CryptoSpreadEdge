"""
Script de test du système d'arbitrage CryptoSpreadEdge
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.arbitrage.arbitrage_engine import arbitrage_engine, ArbitrageOpportunity
from src.arbitrage.price_monitor import price_monitor
from src.arbitrage.execution_engine import execution_engine
from src.arbitrage.risk_manager import arbitrage_risk_manager
from src.arbitrage.profit_calculator import profit_calculator
from src.connectors.connector_factory import connector_factory
from src.data_sources.data_aggregator import data_aggregator


class ArbitrageSystemTester:
    """Testeur du système d'arbitrage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.test_results = {}
    
    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def test_price_monitoring(self) -> bool:
        """Teste le système de monitoring des prix"""
        print("\n" + "="*60)
        print("TEST DU MONITORING DES PRIX")
        print("="*60)
        
        try:
            # Démarrer le monitoring
            await price_monitor.start()
            
            # Attendre quelques secondes pour collecter des données
            await asyncio.sleep(5)
            
            # Tester la récupération des prix
            symbols = ["BTC", "ETH", "BNB"]
            all_prices = await price_monitor.get_all_prices(symbols)
            
            if not all_prices:
                print("❌ Aucun prix récupéré")
                return False
            
            print(f"✅ Prix récupérés pour {len(all_prices)} symboles")
            
            # Tester les meilleurs prix
            for symbol in symbols:
                best_prices = await price_monitor.get_best_prices(symbol)
                if best_prices:
                    print(f"  {symbol}: Meilleur achat: {best_prices['best_buy'].platform} "
                          f"({best_prices['best_buy'].ask:.2f}), "
                          f"Meilleure vente: {best_prices['best_sell'].platform} "
                          f"({best_prices['best_sell'].bid:.2f})")
            
            # Tester l'écart de prix
            for symbol in symbols:
                spread = await price_monitor.get_price_spread(symbol)
                if spread:
                    print(f"  {symbol}: Écart {spread['spread_percentage']:.2%} "
                          f"({spread['buy_platform']} -> {spread['sell_platform']})")
            
            # Tester la tendance des prix
            for symbol in symbols:
                trend = await price_monitor.get_price_trend(symbol, minutes=5)
                if trend:
                    print(f"  {symbol}: Tendance {trend['slope']:.4f}, "
                          f"Volatilité {trend['volatility']:.2%}")
            
            # Afficher les statistiques
            stats = price_monitor.get_statistics()
            print(f"\nStatistiques du monitoring:")
            print(f"  Symboles surveillés: {stats['symbols_monitored']}")
            print(f"  Plateformes totales: {stats['total_platforms']}")
            print(f"  Alertes actives: {stats['active_alerts']}")
            print(f"  Mises à jour: {stats['total_updates']}")
            
            # Arrêter le monitoring
            await price_monitor.stop()
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test monitoring prix: {e}")
            return False
    
    async def test_arbitrage_opportunities(self) -> bool:
        """Teste la détection d'opportunités d'arbitrage"""
        print("\n" + "="*60)
        print("TEST DE DÉTECTION D'OPPORTUNITÉS D'ARBITRAGE")
        print("="*60)
        
        try:
            # Initialiser les connecteurs
            await data_aggregator.initialize_connectors()
            
            # Rechercher des opportunités
            symbols = ["BTC", "ETH", "BNB"]
            opportunities = await arbitrage_engine._find_arbitrage_opportunities(symbols)
            
            if not opportunities:
                print("⚠️  Aucune opportunité d'arbitrage trouvée")
                return True  # Pas une erreur, juste pas d'opportunité
            
            print(f"✅ {len(opportunities)} opportunités trouvées")
            
            # Afficher les opportunités
            for i, opp in enumerate(opportunities[:5]):  # Afficher les 5 premières
                print(f"\nOpportunité {i+1}:")
                print(f"  Symbole: {opp.symbol}")
                print(f"  Achat: {opp.buy_exchange} à {opp.buy_price:.2f}")
                print(f"  Vente: {opp.sell_exchange} à {opp.sell_price:.2f}")
                print(f"  Spread: {opp.spread_percentage:.2%}")
                print(f"  Volume: {opp.volume_available:.2f}")
                print(f"  Profit max: {opp.max_profit:.2f} USD")
                print(f"  Confiance: {opp.confidence:.2%}")
                print(f"  Risque: {opp.risk_score:.2%}")
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test opportunités: {e}")
            return False
    
    async def test_profit_calculation(self) -> bool:
        """Teste le calcul de profit"""
        print("\n" + "="*60)
        print("TEST DU CALCUL DE PROFIT")
        print("="*60)
        
        try:
            # Créer une opportunité de test
            test_opportunity = ArbitrageOpportunity(
                symbol="BTC",
                buy_exchange="binance",
                sell_exchange="okx",
                buy_price=50000.0,
                sell_price=50100.0,
                spread=100.0,
                spread_percentage=0.002,
                volume_available=1.0,
                max_profit=100.0,
                confidence=0.9,
                timestamp=time.time(),
                execution_time_estimate=2.0,
                risk_score=0.3
            )
            
            # Tester le calcul de profit
            quantity = 0.1
            calculation = profit_calculator.calculate_profit(test_opportunity, quantity)
            
            if not calculation:
                print("❌ Échec du calcul de profit")
                return False
            
            print(f"✅ Calcul de profit réussi:")
            print(f"  Symbole: {calculation.symbol}")
            print(f"  Quantité: {calculation.quantity}")
            print(f"  Profit brut: {calculation.gross_profit:.2f} USD")
            print(f"  Frais: {calculation.fees:.2f} USD")
            print(f"  Profit net: {calculation.net_profit:.2f} USD")
            print(f"  Pourcentage: {calculation.profit_percentage:.2%}")
            print(f"  ROI: {calculation.roi:.2%}")
            
            # Tester le calcul de quantité optimale
            max_investment = 1000.0
            optimal_quantity = profit_calculator.calculate_optimal_quantity(test_opportunity, max_investment)
            print(f"\nQuantité optimale pour {max_investment} USD: {optimal_quantity:.4f}")
            
            # Tester le seuil de rentabilité
            breakeven_quantity = profit_calculator.calculate_breakeven_quantity(test_opportunity)
            print(f"Seuil de rentabilité: {breakeven_quantity:.4f}")
            
            # Tester le profit ajusté au risque
            risk_adjusted = profit_calculator.calculate_risk_adjusted_profit(test_opportunity, quantity)
            if risk_adjusted:
                print(f"\nProfit ajusté au risque:")
                print(f"  Profit de base: {risk_adjusted['base_profit']:.2f} USD")
                print(f"  Profit ajusté: {risk_adjusted['adjusted_profit']:.2f} USD")
                print(f"  Probabilité de succès: {risk_adjusted['success_probability']:.2%}")
                print(f"  Valeur attendue: {risk_adjusted['expected_value']:.2f} USD")
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test calcul profit: {e}")
            return False
    
    async def test_risk_management(self) -> bool:
        """Teste la gestion des risques"""
        print("\n" + "="*60)
        print("TEST DE LA GESTION DES RISQUES")
        print("="*60)
        
        try:
            # Démarrer le monitoring des risques
            await arbitrage_risk_manager.start_monitoring()
            
            # Créer des opportunités de test
            test_opportunities = [
                ArbitrageOpportunity(
                    symbol="BTC",
                    buy_exchange="binance",
                    sell_exchange="okx",
                    buy_price=50000.0,
                    sell_price=50100.0,
                    spread=100.0,
                    spread_percentage=0.002,
                    volume_available=1.0,
                    max_profit=100.0,
                    confidence=0.9,
                    timestamp=time.time(),
                    execution_time_estimate=2.0,
                    risk_score=0.3
                ),
                ArbitrageOpportunity(
                    symbol="ETH",
                    buy_exchange="coinbase",
                    sell_exchange="kraken",
                    buy_price=3000.0,
                    sell_price=3100.0,
                    spread=100.0,
                    spread_percentage=0.033,
                    volume_available=0.5,
                    max_profit=50.0,
                    confidence=0.7,
                    timestamp=time.time(),
                    execution_time_estimate=5.0,
                    risk_score=0.6
                )
            ]
            
            # Tester la validation des opportunités
            for i, opp in enumerate(test_opportunities):
                is_safe = await arbitrage_risk_manager.is_opportunity_safe(opp)
                print(f"Opportunité {i+1}: {'✅ Sûre' if is_safe else '❌ Risquée'}")
                
                if not is_safe:
                    # Afficher les alertes récentes
                    alerts = arbitrage_risk_manager.get_recent_alerts(3)
                    for alert in alerts:
                        print(f"  Alerte: {alert['message']}")
            
            # Afficher le statut des risques
            risk_status = arbitrage_risk_manager.get_risk_status()
            print(f"\nStatut des risques:")
            print(f"  Position actuelle: {risk_status['metrics']['current_position']:.2f} USD")
            print(f"  PnL quotidien: {risk_status['metrics']['daily_pnl']:.2f} USD")
            print(f"  Trades quotidiens: {risk_status['metrics']['daily_trades']}")
            print(f"  Taux de réussite: {risk_status['metrics']['win_rate']:.2%}")
            print(f"  Drawdown max: {risk_status['metrics']['max_drawdown']:.2f} USD")
            print(f"  Alertes actives: {risk_status['alerts_count']}")
            
            # Arrêter le monitoring
            await arbitrage_risk_manager.stop_monitoring()
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test gestion risques: {e}")
            return False
    
    async def test_execution_engine(self) -> bool:
        """Teste le moteur d'exécution"""
        print("\n" + "="*60)
        print("TEST DU MOTEUR D'EXÉCUTION")
        print("="*60)
        
        try:
            # Démarrer le moteur d'exécution
            await execution_engine.start()
            
            # Créer une opportunité de test (simulation)
            test_opportunity = ArbitrageOpportunity(
                symbol="BTC",
                buy_exchange="binance",
                sell_exchange="okx",
                buy_price=50000.0,
                sell_price=50100.0,
                spread=100.0,
                spread_percentage=0.002,
                volume_available=0.001,  # Très petit pour le test
                max_profit=0.1,
                confidence=0.9,
                timestamp=time.time(),
                execution_time_estimate=2.0,
                risk_score=0.3
            )
            
            print("⚠️  Test d'exécution simulé (pas d'ordres réels)")
            
            # Tester la validation de l'opportunité
            is_valid = await execution_engine._validate_opportunity(test_opportunity)
            print(f"Validation opportunité: {'✅ Valide' if is_valid else '❌ Invalide'}")
            
            # Tester le calcul de taille d'ordre
            order_size = await execution_engine._calculate_order_size(test_opportunity)
            print(f"Taille d'ordre calculée: {order_size:.4f}")
            
            # Afficher les statistiques
            stats = execution_engine.get_statistics()
            print(f"\nStatistiques d'exécution:")
            print(f"  Exécutions totales: {stats['total_executions']}")
            print(f"  Exécutions réussies: {stats['successful_executions']}")
            print(f"  Exécutions échouées: {stats['failed_executions']}")
            print(f"  Taux de succès: {stats['success_rate']:.2%}")
            print(f"  Profit total: {stats['total_profit']:.2f} USD")
            print(f"  Frais totaux: {stats['total_fees']:.2f} USD")
            print(f"  Profit net: {stats['net_profit']:.2f} USD")
            
            # Arrêter le moteur
            await execution_engine.stop()
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test moteur exécution: {e}")
            return False
    
    async def test_full_arbitrage_system(self) -> bool:
        """Teste le système d'arbitrage complet"""
        print("\n" + "="*60)
        print("TEST DU SYSTÈME D'ARBITRAGE COMPLET")
        print("="*60)
        
        try:
            # Initialiser tous les composants
            await data_aggregator.initialize_connectors()
            await arbitrage_risk_manager.start_monitoring()
            await execution_engine.start()
            
            # Démarrer le moteur d'arbitrage
            print("🚀 Démarrage du moteur d'arbitrage...")
            arbitrage_task = asyncio.create_task(arbitrage_engine.start())
            
            # Attendre quelques secondes pour la collecte de données
            print("⏳ Collecte de données en cours...")
            await asyncio.sleep(10)
            
            # Afficher les statistiques
            arbitrage_stats = arbitrage_engine.get_statistics()
            print(f"\nStatistiques d'arbitrage:")
            print(f"  En cours: {arbitrage_stats['is_running']}")
            print(f"  Opportunités trouvées: {arbitrage_stats['opportunities_found']}")
            print(f"  Opportunités exécutées: {arbitrage_stats['opportunities_executed']}")
            print(f"  Profit total: {arbitrage_stats['total_profit']:.2f} USD")
            print(f"  Frais totaux: {arbitrage_stats['total_fees']:.2f} USD")
            print(f"  Profit net: {arbitrage_stats['net_profit']:.2f} USD")
            print(f"  Taux de succès: {arbitrage_stats['success_rate']:.2%}")
            
            # Afficher les opportunités récentes
            recent_opportunities = arbitrage_engine.get_recent_opportunities(5)
            if recent_opportunities:
                print(f"\nOpportunités récentes:")
                for i, opp in enumerate(recent_opportunities):
                    print(f"  {i+1}. {opp.symbol}: {opp.buy_exchange} -> {opp.sell_exchange} "
                          f"({opp.spread_percentage:.2%})")
            
            # Arrêter le système
            print("\n🛑 Arrêt du système d'arbitrage...")
            await arbitrage_engine.stop()
            await arbitrage_risk_manager.stop_monitoring()
            await execution_engine.stop()
            
            # Annuler la tâche d'arbitrage
            arbitrage_task.cancel()
            try:
                await arbitrage_task
            except asyncio.CancelledError:
                pass
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test système complet: {e}")
            return False
    
    async def run_all_tests(self):
        """Exécute tous les tests"""
        print("="*60)
        print("DÉMARRAGE DES TESTS DU SYSTÈME D'ARBITRAGE")
        print("="*60)
        
        start_time = time.time()
        
        # Liste des tests
        tests = [
            ("Monitoring des prix", self.test_price_monitoring),
            ("Détection d'opportunités", self.test_arbitrage_opportunities),
            ("Calcul de profit", self.test_profit_calculation),
            ("Gestion des risques", self.test_risk_management),
            ("Moteur d'exécution", self.test_execution_engine),
            ("Système complet", self.test_full_arbitrage_system)
        ]
        
        # Exécuter les tests
        results = {}
        for test_name, test_func in tests:
            print(f"\n🧪 Test: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                print(f"✅ {test_name}: {'Réussi' if result else 'Échoué'}")
            except Exception as e:
                print(f"❌ {test_name}: Erreur - {e}")
                results[test_name] = False
        
        # Calculer le temps total
        total_time = time.time() - start_time
        
        # Afficher le résumé
        print("\n" + "="*60)
        print("RÉSUMÉ DES TESTS")
        print("="*60)
        
        successful_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        print(f"Tests réussis: {successful_tests}/{total_tests}")
        print(f"Temps total: {total_time:.2f}s")
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
        
        if successful_tests == total_tests:
            print("\n🎉 Tous les tests sont passés avec succès!")
        else:
            print(f"\n⚠️  {total_tests - successful_tests} test(s) ont échoué")
        
        return successful_tests == total_tests


async def main():
    """Fonction principale"""
    tester = ArbitrageSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Le système d'arbitrage est prêt!")
    else:
        print("\n🔧 Des corrections sont nécessaires avant de pouvoir utiliser le système d'arbitrage")


if __name__ == "__main__":
    asyncio.run(main())