#!/usr/bin/env python3
"""
Script de validation du système CryptoSpreadEdge
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Imports avec gestion d'erreur
try:
    from arbitrage.arbitrage_engine import arbitrage_engine
    from arbitrage.price_monitor import price_monitor
    from arbitrage.execution_engine import execution_engine
    from arbitrage.risk_manager import arbitrage_risk_manager
    from arbitrage.profit_calculator import ProfitCalculator
    from connectors.connector_factory import connector_factory
    from core.trading_engine.engine import TradingEngine, TradingConfig
    from core.market_data.market_data_manager import MarketDataManager, MarketDataConfig, DataSource
    from core.order_management.order_manager import OrderManager, OrderManagerConfig
    from core.risk_management.risk_manager import RiskManager, RiskLimits
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("💡 Assurez-vous d'être dans le répertoire racine du projet")
    sys.exit(1)


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SystemValidator:
    """Validateur du système CryptoSpreadEdge"""
    
    def __init__(self):
        self.validation_results = {}
    
    async def validate_system(self):
        """Valide l'ensemble du système"""
        print("🔍 === VALIDATION DU SYSTÈME CRYPTOSPREADEDGE ===")
        print("=" * 60)
        
        validations = [
            ("Validation des imports", self.validate_imports),
            ("Validation des connecteurs", self.validate_connectors),
            ("Validation du système d'arbitrage", self.validate_arbitrage_system),
            ("Validation du moteur de trading", self.validate_trading_engine),
            ("Validation de la configuration", self.validate_configuration),
            ("Validation des scripts", self.validate_scripts)
        ]
        
        for validation_name, validation_func in validations:
            try:
                print(f"\n🔍 {validation_name}...")
                result = await validation_func()
                self.validation_results[validation_name] = result
                status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
                print(f"   {status}")
            except Exception as e:
                logger.error(f"Erreur validation {validation_name}: {e}")
                self.validation_results[validation_name] = False
                print(f"   ❌ ERREUR - {e}")
        
        self.print_summary()
    
    async def validate_imports(self) -> bool:
        """Valide que tous les imports fonctionnent"""
        try:
            # Tester les imports principaux
            from arbitrage.arbitrage_engine import ArbitrageEngine
            from arbitrage.price_monitor import PriceMonitor
            from arbitrage.execution_engine import ExecutionEngine
            from arbitrage.risk_manager import ArbitrageRiskManager
            from arbitrage.profit_calculator import ProfitCalculator
            
            from connectors.connector_factory import ConnectorFactory
            from connectors.binance.binance_connector import BinanceConnector
            from connectors.okx.okx_connector import OKXConnector
            from connectors.bybit.bybit_connector import BybitConnector
            from connectors.bitget.bitget_connector import BitgetConnector
            from connectors.gateio.gateio_connector import GateIOConnector
            
            from core.trading_engine.engine import TradingEngine
            from core.market_data.market_data_manager import MarketDataManager
            from core.order_management.order_manager import OrderManager
            from core.risk_management.risk_manager import RiskManager
            
            print("   ✅ Tous les imports sont valides")
            return True
        
        except ImportError as e:
            print(f"   ❌ Erreur d'import: {e}")
            return False
    
    async def validate_connectors(self) -> bool:
        """Valide les connecteurs d'exchanges"""
        try:
            # Tester la factory
            factory = ConnectorFactory()
            connectors = factory.get_all_connectors()
            
            if not connectors:
                print("   ⚠️ Aucun connecteur disponible")
                return False
            
            print(f"   ✅ {len(connectors)} connecteurs disponibles")
            
            # Tester la création de connecteurs
            test_connectors = ["binance", "okx", "bybit", "bitget", "gateio"]
            created_connectors = 0
            
            for connector_id in test_connectors:
                try:
                    connector = factory.get_connector(connector_id)
                    if connector:
                        created_connectors += 1
                        print(f"   ✅ Connecteur {connector_id} créé")
                except Exception as e:
                    print(f"   ⚠️ Erreur création {connector_id}: {e}")
            
            print(f"   ✅ {created_connectors}/{len(test_connectors)} connecteurs créés")
            return created_connectors > 0
        
        except Exception as e:
            print(f"   ❌ Erreur validation connecteurs: {e}")
            return False
    
    async def validate_arbitrage_system(self) -> bool:
        """Valide le système d'arbitrage"""
        try:
            # Tester les composants
            components = {
                "ArbitrageEngine": arbitrage_engine,
                "PriceMonitor": price_monitor,
                "ExecutionEngine": execution_engine,
                "RiskManager": arbitrage_risk_manager,
                "ProfitCalculator": ProfitCalculator()
            }
            
            valid_components = 0
            
            for name, component in components.items():
                try:
                    # Tester les méthodes principales
                    if hasattr(component, 'get_statistics'):
                        stats = component.get_statistics()
                        print(f"   ✅ {name} - Statistiques disponibles")
                    elif hasattr(component, 'calculate_profit'):
                        # Test du ProfitCalculator
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
                        
                        calculation = component.calculate_profit(opportunity, 1.0)
                        print(f"   ✅ {name} - Calcul de profit fonctionnel")
                    else:
                        print(f"   ✅ {name} - Composant disponible")
                    
                    valid_components += 1
                
                except Exception as e:
                    print(f"   ⚠️ Erreur {name}: {e}")
            
            print(f"   ✅ {valid_components}/{len(components)} composants validés")
            return valid_components == len(components)
        
        except Exception as e:
            print(f"   ❌ Erreur validation système d'arbitrage: {e}")
            return False
    
    async def validate_trading_engine(self) -> bool:
        """Valide le moteur de trading"""
        try:
            # Tester la création des composants
            market_config = MarketDataConfig(
                symbols=["BTC/USDT", "ETH/USDT"],
                data_sources=[DataSource.BINANCE],
                update_frequency=1.0
            )
            
            order_config = OrderManagerConfig(
                max_pending_orders=10,
                order_timeout=30.0
            )
            
            risk_limits = RiskLimits(
                max_daily_loss=1000.0,
                max_position_size=10000.0,
                max_total_exposure=50000.0
            )
            
            trading_config = TradingConfig(
                max_positions=5,
                max_daily_loss=1000.0,
                trading_enabled=False  # Désactivé pour les tests
            )
            
            # Créer les composants
            market_data_manager = MarketDataManager(market_config)
            order_manager = OrderManager(order_config)
            risk_manager = RiskManager(risk_limits)
            
            trading_engine = TradingEngine(
                market_data_manager=market_data_manager,
                order_manager=order_manager,
                risk_manager=risk_manager,
                config=trading_config
            )
            
            # Tester le statut
            status = trading_engine.get_status()
            print(f"   ✅ Moteur de trading créé - État: {status['state']}")
            
            return True
        
        except Exception as e:
            print(f"   ❌ Erreur validation moteur de trading: {e}")
            return False
    
    async def validate_configuration(self) -> bool:
        """Valide la configuration"""
        try:
            # Tester la configuration d'arbitrage
            from config.arbitrage_config import get_arbitrage_config, validate_config
            
            config = get_arbitrage_config()
            print(f"   ✅ Configuration d'arbitrage chargée")
            print(f"   ✅ Symboles: {len(config.symbols)}")
            print(f"   ✅ Exchanges: {len(config.exchanges)}")
            
            # Valider la configuration
            is_valid = validate_config()
            print(f"   ✅ Configuration valide: {is_valid}")
            
            return is_valid
        
        except Exception as e:
            print(f"   ❌ Erreur validation configuration: {e}")
            return False
    
    async def validate_scripts(self) -> bool:
        """Valide les scripts"""
        try:
            scripts_dir = Path(__file__).parent / "arbitrage"
            required_scripts = [
                "start_arbitrage.py",
                "test_arbitrage_system.py",
                "demo_arbitrage.py",
                "quick_start.py"
            ]
            
            existing_scripts = 0
            
            for script in required_scripts:
                script_path = scripts_dir / script
                if script_path.exists():
                    print(f"   ✅ Script {script} trouvé")
                    existing_scripts += 1
                else:
                    print(f"   ❌ Script {script} manquant")
            
            print(f"   ✅ {existing_scripts}/{len(required_scripts)} scripts trouvés")
            return existing_scripts == len(required_scripts)
        
        except Exception as e:
            print(f"   ❌ Erreur validation scripts: {e}")
            return False
    
    def print_summary(self):
        """Affiche le résumé de validation"""
        print("\n" + "=" * 60)
        print("📊 === RÉSUMÉ DE VALIDATION ===")
        print("=" * 60)
        
        passed = sum(1 for result in self.validation_results.values() if result)
        total = len(self.validation_results)
        
        for validation_name, result in self.validation_results.items():
            status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
            print(f"{validation_name}: {status}")
        
        print(f"\nRésultat global: {passed}/{total} validations réussies")
        
        if passed == total:
            print("\n🎉 Toutes les validations sont réussies!")
            print("✅ Le système CryptoSpreadEdge est prêt à être utilisé")
        else:
            print(f"\n⚠️ {total - passed} validation(s) ont échoué")
            print("❌ Veuillez corriger les erreurs avant d'utiliser le système")
        
        print("\n💡 Prochaines étapes:")
        print("   1. Configurer les clés API dans config/environments/arbitrage.env")
        print("   2. Tester avec: python scripts/arbitrage/test_arbitrage_system.py")
        print("   3. Démonstration: python scripts/arbitrage/demo_arbitrage.py")
        print("   4. Démarrage: python scripts/arbitrage/start_arbitrage.py")


async def main():
    """Fonction principale"""
    validator = SystemValidator()
    await validator.validate_system()


if __name__ == "__main__":
    print("🔍 CryptoSpreadEdge - Validation du Système")
    print("=" * 60)
    print("Ce script valide que tous les composants du système")
    print("sont correctement installés et configurés.")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Validation interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors de la validation: {e}")
        sys.exit(1)