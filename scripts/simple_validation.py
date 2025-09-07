#!/usr/bin/env python3
"""
Validation simple du système CryptoSpreadEdge
"""

import os
import sys
from pathlib import Path

def validate_files():
    """Valide que tous les fichiers nécessaires existent"""
    print("🔍 === VALIDATION DES FICHIERS ===")
    
    required_files = [
        "src/main.py",
        "src/arbitrage/arbitrage_engine.py",
        "src/arbitrage/price_monitor.py",
        "src/arbitrage/execution_engine.py",
        "src/arbitrage/risk_manager.py",
        "src/arbitrage/profit_calculator.py",
        "src/connectors/binance/binance_connector.py",
        "src/connectors/okx/okx_connector.py",
        "src/connectors/bybit/bybit_connector.py",
        "src/connectors/bitget/bitget_connector.py",
        "src/connectors/gateio/gateio_connector.py",
        "src/core/trading_engine/engine.py",
        "scripts/arbitrage/start_arbitrage.py",
        "scripts/arbitrage/test_arbitrage_system.py",
        "scripts/arbitrage/demo_arbitrage.py",
        "scripts/arbitrage/quick_start.py",
        "config/arbitrage_config.py",
        "config/environments/arbitrage.env.example",
        "docs/arbitrage/README.md",
        "docs/arbitrage/SCRIPTS.md"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    print(f"\n📊 Résultat: {len(existing_files)}/{len(required_files)} fichiers trouvés")
    
    if missing_files:
        print(f"\n❌ Fichiers manquants:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("\n🎉 Tous les fichiers sont présents!")
        return True

def validate_directories():
    """Valide que tous les répertoires nécessaires existent"""
    print("\n🔍 === VALIDATION DES RÉPERTOIRES ===")
    
    required_dirs = [
        "src",
        "src/arbitrage",
        "src/connectors",
        "src/connectors/binance",
        "src/connectors/okx",
        "src/connectors/bybit",
        "src/connectors/bitget",
        "src/connectors/gateio",
        "src/core",
        "src/core/trading_engine",
        "scripts",
        "scripts/arbitrage",
        "config",
        "config/environments",
        "docs",
        "docs/arbitrage",
        "logs"
    ]
    
    missing_dirs = []
    existing_dirs = []
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            existing_dirs.append(dir_path)
            print(f"✅ {dir_path}/")
        else:
            missing_dirs.append(dir_path)
            print(f"❌ {dir_path}/")
    
    print(f"\n📊 Résultat: {len(existing_dirs)}/{len(required_dirs)} répertoires trouvés")
    
    if missing_dirs:
        print(f"\n❌ Répertoires manquants:")
        for dir_path in missing_dirs:
            print(f"   - {dir_path}/")
        return False
    else:
        print("\n🎉 Tous les répertoires sont présents!")
        return True

def validate_python_syntax():
    """Valide la syntaxe Python des fichiers principaux"""
    print("\n🔍 === VALIDATION DE LA SYNTAXE PYTHON ===")
    
    python_files = [
        "src/main.py",
        "src/arbitrage/arbitrage_engine.py",
        "src/arbitrage/price_monitor.py",
        "src/arbitrage/execution_engine.py",
        "src/arbitrage/risk_manager.py",
        "src/arbitrage/profit_calculator.py",
        "scripts/arbitrage/start_arbitrage.py",
        "scripts/arbitrage/test_arbitrage_system.py",
        "scripts/arbitrage/demo_arbitrage.py",
        "scripts/arbitrage/quick_start.py"
    ]
    
    valid_files = []
    invalid_files = []
    
    for file_path in python_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), file_path, 'exec')
                valid_files.append(file_path)
                print(f"✅ {file_path}")
            except SyntaxError as e:
                invalid_files.append(file_path)
                print(f"❌ {file_path} - Erreur de syntaxe: {e}")
            except Exception as e:
                invalid_files.append(file_path)
                print(f"⚠️ {file_path} - Erreur: {e}")
        else:
            print(f"❌ {file_path} - Fichier non trouvé")
    
    print(f"\n📊 Résultat: {len(valid_files)}/{len(python_files)} fichiers Python valides")
    
    if invalid_files:
        print(f"\n❌ Fichiers avec erreurs:")
        for file_path in invalid_files:
            print(f"   - {file_path}")
        return False
    else:
        print("\n🎉 Tous les fichiers Python sont syntaxiquement corrects!")
        return True

def validate_configuration():
    """Valide la configuration"""
    print("\n🔍 === VALIDATION DE LA CONFIGURATION ===")
    
    config_files = [
        "config/arbitrage_config.py",
        "config/environments/arbitrage.env.example"
    ]
    
    valid_configs = []
    invalid_configs = []
    
    for config_path in config_files:
        if Path(config_path).exists():
            try:
                if config_path.endswith('.py'):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        compile(f.read(), config_path, 'exec')
                valid_configs.append(config_path)
                print(f"✅ {config_path}")
            except Exception as e:
                invalid_configs.append(config_path)
                print(f"❌ {config_path} - Erreur: {e}")
        else:
            print(f"❌ {config_path} - Fichier non trouvé")
    
    print(f"\n📊 Résultat: {len(valid_configs)}/{len(config_files)} fichiers de configuration valides")
    
    if invalid_configs:
        print(f"\n❌ Fichiers de configuration avec erreurs:")
        for config_path in invalid_configs:
            print(f"   - {config_path}")
        return False
    else:
        print("\n🎉 Tous les fichiers de configuration sont valides!")
        return True

def main():
    """Fonction principale"""
    print("🔍 CryptoSpreadEdge - Validation Simple du Système")
    print("=" * 60)
    
    # Vérifier que nous sommes dans le bon répertoire
    if not Path("src/main.py").exists():
        print("❌ Veuillez exécuter ce script depuis la racine du projet CryptoSpreadEdge")
        sys.exit(1)
    
    # Exécuter les validations
    validations = [
        ("Fichiers", validate_files),
        ("Répertoires", validate_directories),
        ("Syntaxe Python", validate_python_syntax),
        ("Configuration", validate_configuration)
    ]
    
    results = []
    
    for validation_name, validation_func in validations:
        try:
            result = validation_func()
            results.append((validation_name, result))
        except Exception as e:
            print(f"❌ Erreur lors de la validation {validation_name}: {e}")
            results.append((validation_name, False))
    
    # Afficher le résumé
    print("\n" + "=" * 60)
    print("📊 === RÉSUMÉ DE VALIDATION ===")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for validation_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{validation_name}: {status}")
    
    print(f"\nRésultat global: {passed}/{total} validations réussies")
    
    if passed == total:
        print("\n🎉 Toutes les validations sont réussies!")
        print("✅ Le système CryptoSpreadEdge est prêt à être utilisé")
        print("\n💡 Prochaines étapes:")
        print("   1. Configurer les clés API dans config/environments/arbitrage.env")
        print("   2. Tester avec: python scripts/arbitrage/demo_arbitrage.py")
        print("   3. Démarrage: python scripts/arbitrage/start_arbitrage.py")
    else:
        print(f"\n⚠️ {total - passed} validation(s) ont échoué")
        print("❌ Veuillez corriger les erreurs avant d'utiliser le système")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Validation interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors de la validation: {e}")
        sys.exit(1)