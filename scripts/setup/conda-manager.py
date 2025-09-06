#!/usr/bin/env python3
"""
Gestionnaire d'environnements conda pour CryptoSpreadEdge
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


class CondaManager:
    """Gestionnaire d'environnements conda"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        import platform
        is_windows = platform.system() == 'Windows'
        
        self.env_files = {
            'prod': 'environment.yml',
            'dev': 'environment-dev-windows.yml' if is_windows else 'environment-dev.yml',
            'test': 'environment-test.yml'
        }
    
    def run_command(self, command, check=True):
        """Exécute une commande conda"""
        try:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'exécution de: {command}")
            print(f"Code de sortie: {e.returncode}")
            print(f"Erreur: {e.stderr}")
            return None
    
    def check_conda(self):
        """Vérifie si conda est installé"""
        result = self.run_command("conda --version", check=False)
        if result and result.returncode == 0:
            print(f"✅ Conda détecté: {result.stdout.strip()}")
            return True
        else:
            print("❌ Conda n'est pas installé ou pas dans le PATH")
            print("📥 Installez Miniconda depuis: https://docs.conda.io/en/latest/miniconda.html")
            return False
    
    def list_environments(self):
        """Liste les environnements conda"""
        print("📋 Environnements conda disponibles:")
        result = self.run_command("conda env list")
        if result:
            print(result.stdout)
    
    def create_environment(self, env_type='dev'):
        """Crée un environnement conda"""
        if not self.check_conda():
            return False
        
        env_file = self.env_files.get(env_type)
        if not env_file:
            print(f"❌ Type d'environnement inconnu: {env_type}")
            print(f"Types disponibles: {list(self.env_files.keys())}")
            return False
        
        env_path = self.project_root / env_file
        if not env_path.exists():
            print(f"❌ Fichier d'environnement non trouvé: {env_path}")
            return False
        
        env_name = f"cryptospreadedge-{env_type}"
        
        # Vérifier si l'environnement existe déjà
        result = self.run_command(f"conda env list | grep {env_name}", check=False)
        if result and result.returncode == 0:
            print(f"⚠️  L'environnement '{env_name}' existe déjà.")
            response = input("Voulez-vous le supprimer et le recréer ? (y/N): ")
            if response.lower() in ['y', 'yes']:
                print(f"🗑️  Suppression de l'environnement '{env_name}'...")
                self.run_command(f"conda env remove -n {env_name} -y")
            else:
                print(f"ℹ️  Utilisation de l'environnement existant '{env_name}'")
                return True
        
        print(f"🚀 Création de l'environnement '{env_name}'...")
        result = self.run_command(f"conda env create -f {env_path}")
        if result and result.returncode == 0:
            print(f"✅ Environnement '{env_name}' créé avec succès!")
            return True
        else:
            print(f"❌ Erreur lors de la création de l'environnement '{env_name}'")
            return False
    
    def activate_environment(self, env_type='dev'):
        """Active un environnement conda"""
        env_name = f"cryptospreadedge-{env_type}"
        print(f"🔄 Activation de l'environnement '{env_name}'...")
        print(f"Pour activer manuellement: conda activate {env_name}")
        return True
    
    def remove_environment(self, env_type='dev'):
        """Supprime un environnement conda"""
        env_name = f"cryptospreadedge-{env_type}"
        print(f"🗑️  Suppression de l'environnement '{env_name}'...")
        result = self.run_command(f"conda env remove -n {env_name} -y")
        if result and result.returncode == 0:
            print(f"✅ Environnement '{env_name}' supprimé avec succès!")
            return True
        else:
            print(f"❌ Erreur lors de la suppression de l'environnement '{env_name}'")
            return False
    
    def update_environment(self, env_type='dev'):
        """Met à jour un environnement conda"""
        env_name = f"cryptospreadedge-{env_type}"
        env_file = self.env_files.get(env_type)
        if not env_file:
            print(f"❌ Type d'environnement inconnu: {env_type}")
            return False
        
        env_path = self.project_root / env_file
        if not env_path.exists():
            print(f"❌ Fichier d'environnement non trouvé: {env_path}")
            return False
        
        print(f"🔄 Mise à jour de l'environnement '{env_name}'...")
        result = self.run_command(f"conda env update -f {env_path}")
        if result and result.returncode == 0:
            print(f"✅ Environnement '{env_name}' mis à jour avec succès!")
            return True
        else:
            print(f"❌ Erreur lors de la mise à jour de l'environnement '{env_name}'")
            return False
    
    def setup_directories(self):
        """Crée les répertoires nécessaires"""
        print("📁 Création des répertoires...")
        directories = [
            "data/historical",
            "data/models", 
            "data/logs",
            "logs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {directory}")
        
        # Copier le fichier de configuration
        env_example = self.project_root / "config" / "environments" / "env.example"
        env_file = self.project_root / "config" / "environments" / ".env"
        
        if not env_file.exists() and env_example.exists():
            import shutil
            shutil.copy2(env_example, env_file)
            print("  ✅ Fichier .env créé")
    
    def show_help(self):
        """Affiche l'aide"""
        print("🐍 Gestionnaire d'environnements conda pour CryptoSpreadEdge")
        print()
        print("Types d'environnements disponibles:")
        print("  prod  - Environnement de production (complet)")
        print("  dev   - Environnement de développement (léger)")
        print("  test  - Environnement de test (minimal)")
        print()
        print("Commandes disponibles:")
        print("  create    - Créer un environnement")
        print("  activate  - Afficher la commande d'activation")
        print("  remove    - Supprimer un environnement")
        print("  update    - Mettre à jour un environnement")
        print("  list      - Lister les environnements")
        print("  setup     - Créer les répertoires nécessaires")
        print()
        print("Exemples:")
        print("  python conda-manager.py create dev")
        print("  python conda-manager.py activate prod")
        print("  python conda-manager.py remove test")


def main():
    parser = argparse.ArgumentParser(description="Gestionnaire d'environnements conda")
    parser.add_argument('command', choices=['create', 'activate', 'remove', 'update', 'list', 'setup', 'help'],
                       help='Commande à exécuter')
    parser.add_argument('env_type', nargs='?', default='dev',
                       choices=['prod', 'dev', 'test'],
                       help='Type d\'environnement (défaut: dev)')
    
    args = parser.parse_args()
    
    manager = CondaManager()
    
    if args.command == 'help':
        manager.show_help()
    elif args.command == 'list':
        manager.list_environments()
    elif args.command == 'create':
        manager.create_environment(args.env_type)
    elif args.command == 'activate':
        manager.activate_environment(args.env_type)
    elif args.command == 'remove':
        manager.remove_environment(args.env_type)
    elif args.command == 'update':
        manager.update_environment(args.env_type)
    elif args.command == 'setup':
        manager.setup_directories()
    else:
        print(f"❌ Commande inconnue: {args.command}")
        manager.show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()