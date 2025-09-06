#!/usr/bin/env python3
"""
Gestionnaire Git simplifié pour CryptoSpreadEdge (sans emojis)
"""

import argparse
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict


class GitManager:
    """Gestionnaire Git simplifié"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.branch_config = {
            'main': 'master',
            'develop': 'develop',
            'feature_prefix': 'feature/',
            'hotfix_prefix': 'hotfix/',
            'release_prefix': 'release/',
            'bugfix_prefix': 'bugfix/'
        }
        self.tag_config = {
            'version_prefix': 'v',
            'pre_release_suffix': '-rc',
            'beta_suffix': '-beta',
            'alpha_suffix': '-alpha'
        }
    
    def run_command(self, command: str, check: bool = True) -> Optional[subprocess.CompletedProcess]:
        """Exécute une commande Git"""
        try:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True, cwd=self.project_root)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Erreur Git: {e}")
            if e.stderr:
                print(f"Erreur: {e.stderr}")
            return None
    
    def get_current_branch(self) -> str:
        """Récupère la branche actuelle"""
        result = self.run_command("git branch --show-current")
        return result.stdout.strip() if result else ""
    
    def get_all_branches(self) -> List[str]:
        """Récupère toutes les branches"""
        result = self.run_command("git branch -a")
        if not result or not result.stdout:
            return []
        
        branches = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and not line.startswith('*'):
                # Nettoyer les préfixes
                branch = line.replace('remotes/origin/', '').replace('remotes/', '')
                if branch and branch not in branches:
                    branches.append(branch)
        return branches
    
    def get_all_tags(self) -> List[str]:
        """Récupère tous les tags"""
        result = self.run_command("git tag -l")
        if not result or not result.stdout:
            return []
        return [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
    
    def get_latest_version(self) -> Optional[str]:
        """Récupère la dernière version taguée"""
        tags = self.get_all_tags()
        version_tags = [tag for tag in tags if tag.startswith(self.tag_config['version_prefix'])]
        
        if not version_tags:
            return None
        
        # Trier par version (semver)
        def version_key(tag):
            version = tag.replace(self.tag_config['version_prefix'], '')
            try:
                parts = version.split('.')
                return tuple(int(part) for part in parts)
            except ValueError:
                return (0, 0, 0)
        
        version_tags.sort(key=version_key, reverse=True)
        return version_tags[0]
    
    def create_branch(self, branch_type: str, name: str, base_branch: str = 'master') -> bool:
        """Crée une nouvelle branche"""
        if branch_type not in ['feature', 'hotfix', 'release', 'bugfix']:
            print(f"Type de branche invalide: {branch_type}")
            return False
        
        prefix = self.branch_config.get(f'{branch_type}_prefix', '')
        full_name = f"{prefix}{name}"
        
        # Vérifier si la branche existe déjà
        branches = self.get_all_branches()
        if full_name in branches:
            print(f"La branche '{full_name}' existe deja")
            return False
        
        # Créer la branche
        print(f"Creation de la branche '{full_name}'...")
        result = self.run_command(f"git checkout -b {full_name} {base_branch}")
        
        if result and result.returncode == 0:
            print(f"Branche '{full_name}' creee avec succes")
            return True
        else:
            print(f"Erreur lors de la creation de la branche '{full_name}'")
            return False
    
    def delete_branch(self, branch_name: str, force: bool = False) -> bool:
        """Supprime une branche"""
        if branch_name in ['master', 'main', 'develop']:
            print(f"Impossible de supprimer la branche principale '{branch_name}'")
            return False
        
        current_branch = self.get_current_branch()
        if branch_name == current_branch:
            print(f"Impossible de supprimer la branche actuelle '{branch_name}'")
            return False
        
        print(f"Suppression de la branche '{branch_name}'...")
        
        # Supprimer la branche locale
        cmd = f"git branch -D {branch_name}" if force else f"git branch -d {branch_name}"
        result = self.run_command(cmd)
        
        if result and result.returncode == 0:
            print(f"Branche locale '{branch_name}' supprimee")
            
            # Supprimer la branche distante si elle existe
            remote_result = self.run_command(f"git push origin --delete {branch_name}", check=False)
            if remote_result and remote_result.returncode == 0:
                print(f"Branche distante '{branch_name}' supprimee")
            
            return True
        else:
            print(f"Erreur lors de la suppression de la branche '{branch_name}'")
            return False
    
    def create_tag(self, version: str, message: str = "", pre_release: bool = False) -> bool:
        """Crée un tag de version"""
        # Nettoyer la version
        version = version.replace(self.tag_config['version_prefix'], '')
        
        # Valider le format de version (semver)
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            print(f"Format de version invalide: {version}. Utilisez le format X.Y.Z")
            return False
        
        # Ajouter le préfixe
        tag_name = f"{self.tag_config['version_prefix']}{version}"
        
        # Ajouter le suffixe si c'est une pré-release
        if pre_release:
            tag_name += self.tag_config['pre_release_suffix']
        
        # Vérifier si le tag existe déjà
        tags = self.get_all_tags()
        if tag_name in tags:
            print(f"Le tag '{tag_name}' existe deja")
            return False
        
        # Créer le message par défaut
        if not message:
            message = f"Release {tag_name}"
        
        print(f"Creation du tag '{tag_name}'...")
        
        # Créer le tag
        result = self.run_command(f'git tag -a {tag_name} -m "{message}"')
        if result and result.returncode == 0:
            print(f"Tag '{tag_name}' cree avec succes")
            
            # Pousser le tag
            push_result = self.run_command(f"git push origin {tag_name}")
            if push_result and push_result.returncode == 0:
                print(f"Tag '{tag_name}' pousse vers le remote")
            
            return True
        else:
            print(f"Erreur lors de la creation du tag '{tag_name}'")
            return False
    
    def list_branches(self, pattern: str = None) -> None:
        """Liste les branches"""
        branches = self.get_all_branches()
        current = self.get_current_branch()
        
        print("Branches disponibles:")
        print("=" * 50)
        
        for branch in sorted(branches):
            if pattern and pattern.lower() not in branch.lower():
                continue
            
            marker = "->" if branch == current else "  "
            print(f"{marker} {branch}")
    
    def list_tags(self, pattern: str = None) -> None:
        """Liste les tags"""
        tags = self.get_all_tags()
        latest = self.get_latest_version()
        
        print("Tags disponibles:")
        print("=" * 50)
        
        for tag in sorted(tags, reverse=True):
            if pattern and pattern.lower() not in tag.lower():
                continue
            
            marker = "*" if tag == latest else " "
            print(f"{marker} {tag}")
    
    def show_status(self) -> None:
        """Affiche le statut Git"""
        print("Statut Git de CryptoSpreadEdge")
        print("=" * 50)
        
        # Branche actuelle
        current = self.get_current_branch()
        print(f"Branche actuelle: {current}")
        
        # Dernière version
        latest = self.get_latest_version()
        if latest:
            print(f"Derniere version: {latest}")
        else:
            print("Aucune version taguee")
        
        # Statut des fichiers
        result = self.run_command("git status --porcelain")
        if result and result.stdout.strip():
            print("\nFichiers modifies:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            print("\nAucun fichier modifie")
        
        # Branches récentes
        branches = self.get_all_branches()
        recent_branches = [b for b in branches if b.startswith(('feature/', 'hotfix/', 'release/'))]
        if recent_branches:
            print(f"\nBranches de travail ({len(recent_branches)}):")
            for branch in sorted(recent_branches)[:5]:  # Afficher les 5 premières
                print(f"  - {branch}")


def main():
    parser = argparse.ArgumentParser(description="Gestionnaire Git pour CryptoSpreadEdge")
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Branches
    branch_parser = subparsers.add_parser('branch', help='Gestion des branches')
    branch_subparsers = branch_parser.add_subparsers(dest='branch_action')
    
    branch_subparsers.add_parser('list', help='Lister les branches')
    
    create_branch_parser = branch_subparsers.add_parser('create', help='Créer une branche')
    create_branch_parser.add_argument('type', choices=['feature', 'hotfix', 'release', 'bugfix'])
    create_branch_parser.add_argument('name', help='Nom de la branche')
    create_branch_parser.add_argument('--base', default='master', help='Branche de base')
    
    delete_branch_parser = branch_subparsers.add_parser('delete', help='Supprimer une branche')
    delete_branch_parser.add_argument('name', help='Nom de la branche')
    delete_branch_parser.add_argument('--force', action='store_true', help='Forcer la suppression')
    
    # Tags
    tag_parser = subparsers.add_parser('tag', help='Gestion des tags')
    tag_subparsers = tag_parser.add_subparsers(dest='tag_action')
    
    tag_subparsers.add_parser('list', help='Lister les tags')
    
    create_tag_parser = tag_subparsers.add_parser('create', help='Créer un tag')
    create_tag_parser.add_argument('version', help='Version (ex: 1.0.0)')
    create_tag_parser.add_argument('--message', help='Message du tag')
    create_tag_parser.add_argument('--pre-release', action='store_true', help='Version de pré-release')
    
    # Status
    subparsers.add_parser('status', help='Afficher le statut Git')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = GitManager()
    
    if args.command == 'branch':
        if args.branch_action == 'list':
            manager.list_branches()
        elif args.branch_action == 'create':
            manager.create_branch(args.type, args.name, args.base)
        elif args.branch_action == 'delete':
            manager.delete_branch(args.name, args.force)
    
    elif args.command == 'tag':
        if args.tag_action == 'list':
            manager.list_tags()
        elif args.tag_action == 'create':
            manager.create_tag(args.version, args.message, args.pre_release)
    
    elif args.command == 'status':
        manager.show_status()


if __name__ == "__main__":
    main()