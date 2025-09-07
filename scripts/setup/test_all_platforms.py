"""
Script de test de toutes les plateformes CryptoSpreadEdge
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.platforms_config import ALL_PLATFORM_CONFIGS, get_platform_summary
from config.api_keys_manager import api_keys_manager
from src.connectors.connector_factory import connector_factory
from src.data_sources.data_aggregator import data_aggregator
from src.monitoring.data_source_monitor import data_source_monitor


class PlatformTester:
    """Testeur de plateformes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.results = {}
    
    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def test_exchange_platforms(self) -> Dict[str, bool]:
        """Teste les plateformes d'exchanges"""
        print("\n" + "="*60)
        print("TEST DES EXCHANGES")
        print("="*60)
        
        results = {}
        exchange_platforms = [
            platform for platform, config in ALL_PLATFORM_CONFIGS.items()
            if config.platform_type.value == "exchange" and config.enabled
        ]
        
        for platform in exchange_platforms:
            print(f"\nTest de {platform}...")
            
            try:
                # Vérifier les clés API
                credentials = api_keys_manager.get_credentials_for_platform(platform)
                if not credentials:
                    print(f"  ✗ Aucune clé API configurée")
                    results[platform] = False
                    continue
                
                # Créer le connecteur
                connector = await connector_factory.create_connector(
                    exchange_id=platform,
                    **credentials
                )
                
                if not connector:
                    print(f"  ✗ Impossible de créer le connecteur")
                    results[platform] = False
                    continue
                
                # Tester la connexion
                start_time = time.time()
                connected = await connector.connect()
                connection_time = time.time() - start_time
                
                if connected:
                    print(f"  ✓ Connecté en {connection_time:.2f}s")
                    
                    # Tester la récupération de données
                    try:
                        test_symbols = ["BTC/USDT", "ETH/USDT"]
                        data = await connector.get_market_data(test_symbols)
                        
                        if data and len(data) > 0:
                            print(f"  ✓ Données récupérées: {len(data)} symboles")
                            results[platform] = True
                        else:
                            print(f"  ✗ Aucune donnée récupérée")
                            results[platform] = False
                    
                    except Exception as e:
                        print(f"  ✗ Erreur récupération données: {e}")
                        results[platform] = False
                    
                    # Déconnecter
                    await connector.disconnect()
                
                else:
                    print(f"  ✗ Échec de connexion")
                    results[platform] = False
            
            except Exception as e:
                print(f"  ✗ Erreur: {e}")
                results[platform] = False
        
        return results
    
    async def test_dex_platforms(self) -> Dict[str, bool]:
        """Teste les plateformes DEX"""
        print("\n" + "="*60)
        print("TEST DES DEX")
        print("="*60)
        
        results = {}
        dex_platforms = [
            platform for platform, config in ALL_PLATFORM_CONFIGS.items()
            if config.platform_type.value == "dex" and config.enabled
        ]
        
        for platform in dex_platforms:
            print(f"\nTest de {platform}...")
            
            try:
                # Créer le connecteur DEX
                connector = await connector_factory.create_connector(
                    exchange_id=platform,
                    api_key="",
                    secret_key=""
                )
                
                if not connector:
                    print(f"  ✗ Impossible de créer le connecteur")
                    results[platform] = False
                    continue
                
                # Tester la connexion
                start_time = time.time()
                connected = await connector.connect()
                connection_time = time.time() - start_time
                
                if connected:
                    print(f"  ✓ Connecté en {connection_time:.2f}s")
                    
                    # Tester la récupération de données
                    try:
                        test_symbols = ["ETH/USDC", "BTC/USDC"]
                        data = await connector.get_market_data(test_symbols)
                        
                        if data and len(data) > 0:
                            print(f"  ✓ Données récupérées: {len(data)} symboles")
                            results[platform] = True
                        else:
                            print(f"  ✗ Aucune donnée récupérée")
                            results[platform] = False
                    
                    except Exception as e:
                        print(f"  ✗ Erreur récupération données: {e}")
                        results[platform] = False
                    
                    # Déconnecter
                    await connector.disconnect()
                
                else:
                    print(f"  ✗ Échec de connexion")
                    results[platform] = False
            
            except Exception as e:
                print(f"  ✗ Erreur: {e}")
                results[platform] = False
        
        return results
    
    async def test_data_sources(self) -> Dict[str, bool]:
        """Teste les sources de données"""
        print("\n" + "="*60)
        print("TEST DES SOURCES DE DONNÉES")
        print("="*60)
        
        results = {}
        data_platforms = [
            platform for platform, config in ALL_PLATFORM_CONFIGS.items()
            if config.platform_type.value in ["data_source", "aggregator"] and config.enabled
        ]
        
        for platform in data_platforms:
            print(f"\nTest de {platform}...")
            
            try:
                # Tester la source de données
                test_symbols = ["BTC", "ETH"]
                data = await data_aggregator.alternative_sources.get_market_data(
                    test_symbols, platform
                )
                
                if data and len(data) > 0:
                    print(f"  ✓ Données récupérées: {len(data)} symboles")
                    results[platform] = True
                else:
                    print(f"  ✗ Aucune donnée récupérée")
                    results[platform] = False
            
            except Exception as e:
                print(f"  ✗ Erreur: {e}")
                results[platform] = False
        
        return results
    
    async def test_data_aggregation(self) -> bool:
        """Teste l'agrégation de données"""
        print("\n" + "="*60)
        print("TEST DE L'AGRÉGATION DE DONNÉES")
        print("="*60)
        
        try:
            # Initialiser l'agrégateur
            await data_aggregator.initialize_connectors()
            
            # Tester l'agrégation
            test_symbols = ["BTC", "ETH"]
            aggregated_data = await data_aggregator.get_aggregated_data(test_symbols)
            
            if aggregated_data:
                print(f"  ✓ Données agrégées récupérées: {len(aggregated_data)} symboles")
                
                # Afficher un exemple
                for symbol, data in list(aggregated_data.items())[:2]:
                    print(f"    {symbol}: {data.price:.2f} (confiance: {data.confidence:.2f})")
                
                return True
            else:
                print(f"  ✗ Aucune donnée agrégée récupérée")
                return False
        
        except Exception as e:
            print(f"  ✗ Erreur agrégation: {e}")
            return False
    
    async def test_arbitrage_opportunities(self) -> bool:
        """Teste la détection d'opportunités d'arbitrage"""
        print("\n" + "="*60)
        print("TEST DE DÉTECTION D'ARBITRAGE")
        print("="*60)
        
        try:
            # Tester la détection d'arbitrage
            test_symbols = ["BTC", "ETH"]
            opportunities = await data_aggregator.get_arbitrage_opportunities(test_symbols)
            
            if opportunities:
                print(f"  ✓ {len(opportunities)} opportunités d'arbitrage détectées")
                
                # Afficher les opportunités
                for opp in opportunities[:3]:  # Afficher les 3 premières
                    print(f"    {opp['symbol']}: spread {opp['spread']:.4f} "
                          f"({opp['min_source']} -> {opp['max_source']})")
                
                return True
            else:
                print(f"  ✓ Aucune opportunité d'arbitrage détectée")
                return True  # Pas d'erreur, juste pas d'opportunité
        
        except Exception as e:
            print(f"  ✗ Erreur détection arbitrage: {e}")
            return False
    
    async def test_monitoring_system(self) -> bool:
        """Teste le système de monitoring"""
        print("\n" + "="*60)
        print("TEST DU SYSTÈME DE MONITORING")
        print("="*60)
        
        try:
            # Démarrer le monitoring
            await data_source_monitor.start_monitoring()
            
            # Attendre un peu pour collecter des métriques
            await asyncio.sleep(5)
            
            # Récupérer les métriques
            metrics_summary = data_source_monitor.get_metrics_summary()
            
            if metrics_summary:
                print(f"  ✓ Monitoring actif: {metrics_summary['monitoring_active']}")
                print(f"  ✓ Sources totales: {metrics_summary['total_sources']}")
                print(f"  ✓ Sources connectées: {metrics_summary['connected_sources']}")
                print(f"  ✓ Taux de connexion: {metrics_summary['connection_rate']:.2%}")
                print(f"  ✓ Temps de réponse moyen: {metrics_summary['avg_response_time']:.2f}ms")
                print(f"  ✓ Taux de succès moyen: {metrics_summary['avg_success_rate']:.2%}")
                print(f"  ✓ Qualité des données moyenne: {metrics_summary['avg_data_quality']:.2%}")
                print(f"  ✓ Uptime moyen: {metrics_summary['avg_uptime']:.2%}")
                
                # Afficher les alertes
                alerts = data_source_monitor.get_active_alerts()
                if alerts:
                    print(f"  ⚠️  {len(alerts)} alertes actives")
                    for alert in alerts[:3]:  # Afficher les 3 premières
                        print(f"    {alert.level.upper()}: {alert.source} - {alert.message}")
                else:
                    print(f"  ✓ Aucune alerte active")
                
                # Arrêter le monitoring
                await data_source_monitor.stop_monitoring()
                
                return True
            else:
                print(f"  ✗ Aucune métrique récupérée")
                return False
        
        except Exception as e:
            print(f"  ✗ Erreur monitoring: {e}")
            return False
    
    async def run_all_tests(self):
        """Exécute tous les tests"""
        print("="*60)
        print("DÉMARRAGE DES TESTS CRYPTOSPREADEDGE")
        print("="*60)
        
        start_time = time.time()
        
        # Test des exchanges
        exchange_results = await self.test_exchange_platforms()
        self.results["exchanges"] = exchange_results
        
        # Test des DEX
        dex_results = await self.test_dex_platforms()
        self.results["dex"] = dex_results
        
        # Test des sources de données
        data_results = await self.test_data_sources()
        self.results["data_sources"] = data_results
        
        # Test de l'agrégation
        aggregation_success = await self.test_data_aggregation()
        self.results["aggregation"] = aggregation_success
        
        # Test de l'arbitrage
        arbitrage_success = await self.test_arbitrage_opportunities()
        self.results["arbitrage"] = arbitrage_success
        
        # Test du monitoring
        monitoring_success = await self.test_monitoring_system()
        self.results["monitoring"] = monitoring_success
        
        # Calculer le temps total
        total_time = time.time() - start_time
        
        # Afficher le résumé
        self.show_summary(total_time)
    
    def show_summary(self, total_time: float):
        """Affiche le résumé des tests"""
        print("\n" + "="*60)
        print("RÉSUMÉ DES TESTS")
        print("="*60)
        
        # Compter les succès
        exchange_success = sum(1 for success in self.results["exchanges"].values() if success)
        exchange_total = len(self.results["exchanges"])
        
        dex_success = sum(1 for success in self.results["dex"].values() if success)
        dex_total = len(self.results["dex"])
        
        data_success = sum(1 for success in self.results["data_sources"].values() if success)
        data_total = len(self.results["data_sources"])
        
        print(f"Exchanges: {exchange_success}/{exchange_total} réussis")
        print(f"DEX: {dex_success}/{dex_total} réussis")
        print(f"Sources de données: {data_success}/{data_total} réussis")
        print(f"Agrégation: {'✓' if self.results['aggregation'] else '✗'}")
        print(f"Arbitrage: {'✓' if self.results['arbitrage'] else '✗'}")
        print(f"Monitoring: {'✓' if self.results['monitoring'] else '✗'}")
        
        # Calculer le score global
        total_tests = exchange_total + dex_total + data_total + 3  # +3 pour les tests système
        successful_tests = exchange_success + dex_success + data_success + sum([
            self.results['aggregation'],
            self.results['arbitrage'],
            self.results['monitoring']
        ])
        
        score = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\nScore global: {score:.1f}% ({successful_tests}/{total_tests})")
        print(f"Temps total: {total_time:.2f}s")
        
        # Afficher les plateformes en échec
        failed_platforms = []
        
        for platform, success in self.results["exchanges"].items():
            if not success:
                failed_platforms.append(f"Exchange: {platform}")
        
        for platform, success in self.results["dex"].items():
            if not success:
                failed_platforms.append(f"DEX: {platform}")
        
        for platform, success in self.results["data_sources"].items():
            if not success:
                failed_platforms.append(f"Source: {platform}")
        
        if failed_platforms:
            print(f"\nPlateformes en échec:")
            for platform in failed_platforms:
                print(f"  ✗ {platform}")
        
        # Recommandations
        print(f"\nRecommandations:")
        if score < 50:
            print("  - Configurer plus de clés API")
            print("  - Vérifier la connectivité réseau")
            print("  - Vérifier les identifiants API")
        elif score < 80:
            print("  - Optimiser les plateformes en échec")
            print("  - Configurer des sources de données supplémentaires")
        else:
            print("  - Système prêt pour le trading!")
            print("  - Considérer l'ajout de plateformes supplémentaires")


async def main():
    """Fonction principale"""
    tester = PlatformTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())