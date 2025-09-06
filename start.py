#!/usr/bin/env python3
"""
Script de démarrage rapide pour CryptoSpreadEdge
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_conda():
    """Vérifie si conda est disponible"""
    try:
        result = subprocess.run(['conda', '--version'], 
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_environment(env_name):
    """Vérifie si l'environnement conda existe"""
    try:
        result = subprocess.run(['conda', 'env', 'list'], 
                              capture_output=True, text=True, check=True)
        return env_name in result.stdout
    except subprocess.CalledProcessError:
        return False


def activate_environment(env_name):
    """Active l'environnement conda"""
    if not check_conda():
        print("❌ Conda n'est pas installé ou pas dans le PATH")
        print("📥 Installez Miniconda depuis: https://docs.conda.io/en/latest/miniconda.html")
        return False
    
    if not check_environment(env_name):
        print(f"❌ L'environnement '{env_name}' n'existe pas")
        print(f"💡 Créez-le avec: python scripts/setup/conda-manager.py create dev")
        return False
    
    print(f"🔄 Activation de l'environnement '{env_name}'...")
    print(f"💡 Pour activer manuellement: conda activate {env_name}")
    return True


def run_application(env_name, mode='dev'):
    """Lance l'application CryptoSpreadEdge"""
    if not activate_environment(env_name):
        return False
    
    print(f"🚀 Lancement de CryptoSpreadEdge en mode {mode}...")
    
    # Changer vers le répertoire du projet
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Lancer l'application
    try:
        if mode == 'dev':
            # Mode développement avec rechargement automatique
            subprocess.run(['python', '-m', 'src.main'], check=True)
        elif mode == 'prod':
            # Mode production
            subprocess.run(['python', '-m', 'src.main'], check=True)
        elif mode == 'test':
            # Mode test
            subprocess.run(['python', '-m', 'pytest', 'tests/'], check=True)
        else:
            print(f"❌ Mode inconnu: {mode}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du lancement: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
        return True
    
    return True


def setup_environment(env_type='dev'):
    """Configure l'environnement"""
    print(f"🔧 Configuration de l'environnement {env_type}...")
    
    # Lancer le gestionnaire conda
    try:
        subprocess.run(['python', 'scripts/setup/conda-manager.py', 'create', env_type], 
                      check=True)
        subprocess.run(['python', 'scripts/setup/conda-manager.py', 'setup'], 
                      check=True)
        print("✅ Configuration terminée!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return False


def show_status():
    """Affiche le statut du projet"""
    print("📊 Statut de CryptoSpreadEdge")
    print("=" * 40)
    
    # Vérifier conda
    if check_conda():
        print("✅ Conda: Installé")
    else:
        print("❌ Conda: Non installé")
    
    # Vérifier les environnements
    environments = ['cryptospreadedge-prod', 'cryptospreadedge-dev', 'cryptospreadedge-test']
    for env in environments:
        if check_environment(env):
            print(f"✅ Environnement {env}: Disponible")
        else:
            print(f"❌ Environnement {env}: Non disponible")
    
    # Vérifier les fichiers de configuration
    config_files = [
        'config/environments/.env',
        'requirements.txt',
        'environment.yml'
    ]
    
    print("\n📁 Fichiers de configuration:")
    for file in config_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
    
    print("\n💡 Commandes utiles:")
    print("  python start.py setup dev    - Configurer l'environnement de dev")
    print("  python start.py run dev      - Lancer en mode développement")
    print("  python start.py run prod     - Lancer en mode production")
    print("  python start.py test         - Lancer les tests")
    print("  python start.py status       - Afficher le statut")


def main():
    parser = argparse.ArgumentParser(description="Script de démarrage CryptoSpreadEdge")
    parser.add_argument('command', choices=['setup', 'run', 'test', 'status'],
                       help='Commande à exécuter')
    parser.add_argument('env_type', nargs='?', default='dev',
                       choices=['prod', 'dev', 'test'],
                       help='Type d\'environnement (défaut: dev)')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup_environment(args.env_type)
    elif args.command == 'run':
        env_name = f"cryptospreadedge-{args.env_type}"
        run_application(env_name, args.env_type)
    elif args.command == 'test':
        env_name = "cryptospreadedge-test"
        run_application(env_name, 'test')
    elif args.command == 'status':
        show_status()
    else:
        print(f"❌ Commande inconnue: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()