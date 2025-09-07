"""
Script de configuration des plateformes pour CryptoSpreadEdge
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.platforms_config import ALL_PLATFORM_CONFIGS, get_platform_summary
from config.api_keys_manager import api_keys_manager
from src.connectors.connector_factory import connector_factory
from src.data_sources.data_aggregator import data_aggregator
from src.monitoring.data_source_monitor import data_source_monitor


class PlatformConfigurator:
    """Configurateur de plateformes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
    
    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def show_platform_summary(self):
        """Affiche le résumé des plateformes"""
        print("\n" + "="*60)
        print("RÉSUMÉ DES PLATEFORMES CRYPTOSPREADEDGE")
        print("="*60)
        
        summary = get_platform_summary()
        
        print(f"Total des plateformes: {summary['total']}")
        print(f"Exchanges: {summary['exchanges']}")
        print(f"DEX: {summary['dex']}")
        print(f"Sources de données: {summary['data_sources']}")
        print(f"Agrégateurs: {summary['aggregators']}")
        print(f"Activées: {summary['enabled']}")
        print(f"Tier 1: {summary['tier_1']}")
        print(f"Tier 2: {summary['tier_2']}")
        print(f"Tier 3: {summary['tier_3']}")
        print(f"Émergentes: {summary['emerging']}")
        
        print("\n" + "="*60)
        print("PLATEFORMES PAR TYPE")
        print("="*60)
        
        # Exchanges
        print("\nEXCHANGES:")
        for platform, config in ALL_PLATFORM_CONFIGS.items():
            if config.platform_type.value == "exchange":
                status = "✓" if config.enabled else "✗"
                print(f"  {status} {platform}: {config.name} (Tier {config.tier.value})")
        
        # DEX
        print("\nDEX:")
        for platform, config in ALL_PLATFORM_CONFIGS.items():
            if config.platform_type.value == "dex":
                status = "✓" if config.enabled else "✗"
                print(f"  {status} {platform}: {config.name} (Tier {config.tier.value})")
        
        # Sources de données
        print("\nSOURCES DE DONNÉES:")
        for platform, config in ALL_PLATFORM_CONFIGS.items():
            if config.platform_type.value == "data_source":
                status = "✓" if config.enabled else "✗"
                print(f"  {status} {platform}: {config.name} (Tier {config.tier.value})")
        
        # Agrégateurs
        print("\nAGRÉGATEURS:")
        for platform, config in ALL_PLATFORM_CONFIGS.items():
            if config.platform_type.value == "aggregator":
                status = "✓" if config.enabled else "✗"
                print(f"  {status} {platform}: {config.name} (Tier {config.tier.value})")
    
    def show_api_keys_status(self):
        """Affiche le statut des clés API"""
        print("\n" + "="*60)
        print("STATUT DES CLÉS API")
        print("="*60)
        
        status = api_keys_manager.get_platform_status()
        summary = api_keys_manager.get_summary()
        
        print(f"Plateformes avec clés: {summary['total_platforms']}")
        print(f"Plateformes activées: {summary['enabled_platforms']}")
        print(f"Avec secret key: {summary['platforms_with_secrets']}")
        print(f"Avec passphrase: {summary['platforms_with_passphrase']}")
        print(f"Prêtes pour trading: {summary['platforms_ready_for_trading']}")
        print(f"Prêtes pour données: {summary['platforms_ready_for_data']}")
        print(f"Nécessitent des clés: {summary['platforms_needing_keys']}")
        
        print("\n" + "="*60)
        print("DÉTAIL PAR PLATEFORME")
        print("="*60)
        
        for platform, platform_status in status.items():
            status_icon = "✓" if platform_status["has_key"] and platform_status["enabled"] else "✗"
            key_status = "✓" if platform_status["has_key"] else "✗"
            secret_status = "✓" if platform_status["has_secret"] else "✗"
            passphrase_status = "✓" if platform_status["has_passphrase"] else "✗"
            
            print(f"{status_icon} {platform}:")
            print(f"    Clé API: {key_status}")
            print(f"    Secret: {secret_status}")
            print(f"    Passphrase: {passphrase_status}")
            print(f"    Utilisations: {platform_status['usage_count']}")
            print(f"    Dernière utilisation: {platform_status['last_used'] or 'Jamais'}")
            print()
    
    def add_api_key_interactive(self):
        """Ajoute une clé API de manière interactive"""
        print("\n" + "="*60)
        print("AJOUT D'UNE CLÉ API")
        print("="*60)
        
        # Afficher les plateformes disponibles
        platforms = list(ALL_PLATFORM_CONFIGS.keys())
        print("Plateformes disponibles:")
        for i, platform in enumerate(platforms, 1):
            config = ALL_PLATFORM_CONFIGS[platform]
            print(f"  {i}. {platform} ({config.name})")
        
        try:
            choice = int(input("\nChoisissez une plateforme (numéro): ")) - 1
            if 0 <= choice < len(platforms):
                platform = platforms[choice]
                config = ALL_PLATFORM_CONFIGS[platform]
                
                print(f"\nConfiguration de {config.name} ({platform})")
                print(f"Type: {config.platform_type.value}")
                print(f"Tier: {config.tier.value}")
                print(f"Fonctionnalités: {', '.join(config.features)}")
                
                # Demander les informations
                api_key = input("Clé API: ").strip()
                if not api_key:
                    print("Clé API requise!")
                    return
                
                secret_key = input("Secret Key (optionnel): ").strip()
                passphrase = input("Passphrase (optionnel): ").strip()
                
                # Paramètres supplémentaires
                extra_params = {}
                if config.platform_type.value == "exchange":
                    sandbox = input("Mode sandbox? (y/n): ").strip().lower() == 'y'
                    if sandbox:
                        extra_params["sandbox"] = "true"
                
                # Ajouter la clé
                if api_keys_manager.add_api_key(
                    platform=platform,
                    api_key=api_key,
                    secret_key=secret_key,
                    passphrase=passphrase,
                    extra_params=extra_params
                ):
                    print(f"✓ Clé API ajoutée avec succès pour {platform}")
                else:
                    print(f"✗ Erreur lors de l'ajout de la clé API pour {platform}")
            else:
                print("Choix invalide!")
        
        except (ValueError, KeyboardInterrupt):
            print("Opération annulée")
    
    def test_platform_connection(self, platform: str):
        """Teste la connexion à une plateforme"""
        print(f"\nTest de connexion à {platform}...")
        
        try:
            # Récupérer les identifiants
            credentials = api_keys_manager.get_credentials_for_platform(platform)
            if not credentials:
                print(f"✗ Aucune clé API trouvée pour {platform}")
                return False
            
            # Tester la connexion
            if platform in ["binance", "okx", "bybit", "bitget", "gateio", "huobi", "kucoin"]:
                # Tester avec le connecteur
                connector = connector_factory.get_connector(platform)
                if connector:
                    success = asyncio.run(connector.connect())
                    if success:
                        print(f"✓ Connexion réussie à {platform}")
                        asyncio.run(connector.disconnect())
                        return True
                    else:
                        print(f"✗ Échec de connexion à {platform}")
                        return False
                else:
                    print(f"✗ Connecteur non disponible pour {platform}")
                    return False
            else:
                # Pour les sources de données, on simule un test
                print(f"✓ Test simulé pour {platform} (source de données)")
                return True
        
        except Exception as e:
            print(f"✗ Erreur lors du test de connexion à {platform}: {e}")
            return False
    
    def test_all_platforms(self):
        """Teste toutes les plateformes"""
        print("\n" + "="*60)
        print("TEST DE TOUTES LES PLATEFORMES")
        print("="*60)
        
        platforms_with_keys = api_keys_manager.get_platforms_with_keys()
        
        if not platforms_with_keys:
            print("Aucune clé API configurée!")
            return
        
        results = {}
        for platform in platforms_with_keys:
            results[platform] = self.test_platform_connection(platform)
        
        # Résumé
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print(f"\nRésumé: {successful}/{total} plateformes connectées avec succès")
        
        if successful < total:
            print("\nPlateformes en échec:")
            for platform, success in results.items():
                if not success:
                    print(f"  ✗ {platform}")
    
    def show_platform_details(self, platform: str):
        """Affiche les détails d'une plateforme"""
        if platform not in ALL_PLATFORM_CONFIGS:
            print(f"Plateforme {platform} non trouvée!")
            return
        
        config = ALL_PLATFORM_CONFIGS[platform]
        api_key = api_keys_manager.get_api_key(platform)
        
        print(f"\n" + "="*60)
        print(f"DÉTAILS DE {platform.upper()}")
        print("="*60)
        
        print(f"Nom: {config.name}")
        print(f"Type: {config.platform_type.value}")
        print(f"Tier: {config.tier.value}")
        print(f"Activé: {'Oui' if config.enabled else 'Non'}")
        print(f"Priorité: {config.priority}/10")
        print(f"API requise: {'Oui' if config.api_required else 'Non'}")
        print(f"Limite de taux: {config.rate_limit} req/min")
        print(f"Timeout: {config.timeout}s")
        print(f"Tentatives: {config.retry_attempts}")
        print(f"Fonctionnalités: {', '.join(config.features)}")
        print(f"Symboles supportés: {', '.join(config.supported_symbols[:10])}{'...' if len(config.supported_symbols) > 10 else ''}")
        print(f"Timeframes: {', '.join(config.supported_timeframes)}")
        print(f"Montant min: {config.min_trade_amount}")
        print(f"Montant max: {config.max_trade_amount}")
        print(f"Frais maker: {config.fees['maker']:.4f}")
        print(f"Frais taker: {config.fees['taker']:.4f}")
        print(f"Régions: {', '.join(config.regions)}")
        print(f"Langues: {', '.join(config.languages)}")
        print(f"Documentation: {config.api_docs}")
        print(f"Statut: {config.status_page}")
        print(f"Support: {config.support_contact}")
        
        if api_key:
            print(f"\nClé API configurée: {'Oui' if api_key.enabled else 'Non'}")
            print(f"Utilisations: {api_key.usage_count}")
            print(f"Dernière utilisation: {api_key.last_used or 'Jamais'}")
        else:
            print("\nClé API: Non configurée")
    
    def show_menu(self):
        """Affiche le menu principal"""
        while True:
            print("\n" + "="*60)
            print("CONFIGURATEUR DE PLATEFORMES CRYPTOSPREADEDGE")
            print("="*60)
            print("1. Afficher le résumé des plateformes")
            print("2. Afficher le statut des clés API")
            print("3. Ajouter une clé API")
            print("4. Tester une plateforme")
            print("5. Tester toutes les plateformes")
            print("6. Détails d'une plateforme")
            print("7. Quitter")
            
            try:
                choice = input("\nChoisissez une option (1-7): ").strip()
                
                if choice == "1":
                    self.show_platform_summary()
                elif choice == "2":
                    self.show_api_keys_status()
                elif choice == "3":
                    self.add_api_key_interactive()
                elif choice == "4":
                    platform = input("Nom de la plateforme: ").strip()
                    if platform:
                        self.test_platform_connection(platform)
                elif choice == "5":
                    self.test_all_platforms()
                elif choice == "6":
                    platform = input("Nom de la plateforme: ").strip()
                    if platform:
                        self.show_platform_details(platform)
                elif choice == "7":
                    print("Au revoir!")
                    break
                else:
                    print("Option invalide!")
            
            except KeyboardInterrupt:
                print("\nAu revoir!")
                break
            except Exception as e:
                print(f"Erreur: {e}")


def main():
    """Fonction principale"""
    configurator = PlatformConfigurator()
    configurator.show_menu()


if __name__ == "__main__":
    main()