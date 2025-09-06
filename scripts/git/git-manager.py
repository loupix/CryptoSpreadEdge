#!/usr/bin/env python3
"""
Gestionnaire automatique des branches et tags pour CryptoSpreadEdge
"""

import argparse
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import json


class GitManager:
    """Gestionnaire automatique des branches et tags Git"""
    
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
            print(f"❌ Erreur Git: {e}")
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
        if not result:
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
            print(f"❌ Type de branche invalide: {branch_type}")
            return False
        
        prefix = self.branch_config.get(f'{branch_type}_prefix', '')
        full_name = f"{prefix}{name}"
        
        # Vérifier si la branche existe déjà
        branches = self.get_all_branches()
        if full_name in branches:
            print(f"⚠️  La branche '{full_name}' existe déjà")
            return False
        
        # Créer la branche
        print(f"🌿 Création de la branche '{full_name}'...")
        result = self.run_command(f"git checkout -b {full_name} {base_branch}")
        
        if result and result.returncode == 0:
            print(f"✅ Branche '{full_name}' créée avec succès")
            return True
        else:
            print(f"❌ Erreur lors de la création de la branche '{full_name}'")
            return False
    
    def delete_branch(self, branch_name: str, force: bool = False) -> bool:
        """Supprime une branche"""
        if branch_name in ['master', 'main', 'develop']:
            print(f"❌ Impossible de supprimer la branche principale '{branch_name}'")
            return False
        
        current_branch = self.get_current_branch()
        if branch_name == current_branch:
            print(f"❌ Impossible de supprimer la branche actuelle '{branch_name}'")
            return False
        
        print(f"🗑️  Suppression de la branche '{branch_name}'...")
        
        # Supprimer la branche locale
        cmd = f"git branch -D {branch_name}" if force else f"git branch -d {branch_name}"
        result = self.run_command(cmd)
        
        if result and result.returncode == 0:
            print(f"✅ Branche locale '{branch_name}' supprimée")
            
            # Supprimer la branche distante si elle existe
            remote_result = self.run_command(f"git push origin --delete {branch_name}", check=False)
            if remote_result and remote_result.returncode == 0:
                print(f"✅ Branche distante '{branch_name}' supprimée")
            
            return True
        else:
            print(f"❌ Erreur lors de la suppression de la branche '{branch_name}'")
            return False
    
    def merge_branch(self, source_branch: str, target_branch: str = 'master') -> bool:
        """Fusionne une branche"""
        print(f"🔄 Fusion de '{source_branch}' vers '{target_branch}'...")
        
        # Basculer vers la branche cible
        result = self.run_command(f"git checkout {target_branch}")
        if not result or result.returncode != 0:
            print(f"❌ Impossible de basculer vers '{target_branch}'")
            return False
        
        # Fusionner
        result = self.run_command(f"git merge {source_branch}")
        if result and result.returncode == 0:
            print(f"✅ Fusion réussie de '{source_branch}' vers '{target_branch}'")
            return True
        else:
            print(f"❌ Erreur lors de la fusion de '{source_branch}' vers '{target_branch}'")
            return False
    
    def create_tag(self, version: str, message: str = "", pre_release: bool = False) -> bool:
        """Crée un tag de version"""
        # Nettoyer la version
        version = version.replace(self.tag_config['version_prefix'], '')
        
        # Valider le format de version (semver)
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            print(f"❌ Format de version invalide: {version}. Utilisez le format X.Y.Z")
            return False
        
        # Ajouter le préfixe
        tag_name = f"{self.tag_config['version_prefix']}{version}"
        
        # Ajouter le suffixe si c'est une pré-release
        if pre_release:
            tag_name += self.tag_config['pre_release_suffix']
        
        # Vérifier si le tag existe déjà
        tags = self.get_all_tags()
        if tag_name in tags:
            print(f"⚠️  Le tag '{tag_name}' existe déjà")
            return False
        
        # Créer le message par défaut
        if not message:
            message = f"Release {tag_name}"
        
        print(f"🏷️  Création du tag '{tag_name}'...")
        
        # Créer le tag
        result = self.run_command(f'git tag -a {tag_name} -m "{message}"')
        if result and result.returncode == 0:
            print(f"✅ Tag '{tag_name}' créé avec succès")
            
            # Pousser le tag
            push_result = self.run_command(f"git push origin {tag_name}")
            if push_result and push_result.returncode == 0:
                print(f"✅ Tag '{tag_name}' poussé vers le remote")
            
            return True
        else:
            print(f"❌ Erreur lors de la création du tag '{tag_name}'")
            return False
    
    def delete_tag(self, tag_name: str) -> bool:
        """Supprime un tag"""
        print(f"🗑️  Suppression du tag '{tag_name}'...")
        
        # Supprimer le tag local
        result = self.run_command(f"git tag -d {tag_name}")
        if result and result.returncode == 0:
            print(f"✅ Tag local '{tag_name}' supprimé")
            
            # Supprimer le tag distant
            remote_result = self.run_command(f"git push origin --delete {tag_name}")
            if remote_result and remote_result.returncode == 0:
                print(f"✅ Tag distant '{tag_name}' supprimé")
            
            return True
        else:
            print(f"❌ Erreur lors de la suppression du tag '{tag_name}'")
            return False
    
    def list_branches(self, pattern: str = None) -> None:
        """Liste les branches"""
        branches = self.get_all_branches()
        current = self.get_current_branch()
        
        print("🌿 Branches disponibles:")
        print("=" * 50)
        
        for branch in sorted(branches):
            if pattern and pattern.lower() not in branch.lower():
                continue
            
            marker = "👉" if branch == current else "  "
            print(f"{marker} {branch}")
    
    def list_tags(self, pattern: str = None) -> None:
        """Liste les tags"""
        tags = self.get_all_tags()
        latest = self.get_latest_version()
        
        print("🏷️  Tags disponibles:")
        print("=" * 50)
        
        for tag in sorted(tags, reverse=True):
            if pattern and pattern.lower() not in tag.lower():
                continue
            
            marker = "⭐" if tag == latest else "  "
            print(f"{marker} {tag}")
    
    def auto_branch_cleanup(self) -> None:
        """Nettoie automatiquement les branches fusionnées"""
        print("🧹 Nettoyage automatique des branches...")
        
        # Récupérer les branches fusionnées
        result = self.run_command("git branch --merged master")
        if not result:
            return
        
        merged_branches = []
        for line in result.stdout.split('\n'):
            line = line.strip().replace('*', '').strip()
            if line and line not in ['master', 'main', 'develop']:
                merged_branches.append(line)
        
        if not merged_branches:
            print("✅ Aucune branche à nettoyer")
            return
        
        print(f"📋 Branches fusionnées trouvées: {len(merged_branches)}")
        for branch in merged_branches:
            print(f"  - {branch}")
        
        # Demander confirmation
        response = input("\nVoulez-vous supprimer ces branches ? (y/N): ")
        if response.lower() in ['y', 'yes']:
            for branch in merged_branches:
                self.delete_branch(branch)
        else:
            print("❌ Nettoyage annulé")
    
    def generate_changelog(self, from_tag: str = None, to_tag: str = None) -> str:
        """Génère un changelog entre deux tags"""
        if not from_tag:
            from_tag = self.get_latest_version() or "HEAD~10"
        
        if not to_tag:
            to_tag = "HEAD"
        
        print(f"📝 Génération du changelog de {from_tag} à {to_tag}...")
        
        # Récupérer les commits
        result = self.run_command(f"git log {from_tag}..{to_tag} --oneline --pretty=format:'%h %s'")
        if not result:
            return ""
        
        commits = result.stdout.strip().split('\n')
        
        changelog = f"# Changelog\n\n"
        changelog += f"## {to_tag} ({datetime.now().strftime('%Y-%m-%d')})\n\n"
        
        # Grouper par type de commit
        features = []
        fixes = []
        others = []
        
        for commit in commits:
            if not commit.strip():
                continue
            
            if commit.lower().startswith(('feat', 'feature')):
                features.append(commit)
            elif commit.lower().startswith(('fix', 'bug')):
                fixes.append(commit)
            else:
                others.append(commit)
        
        if features:
            changelog += "### ✨ Nouvelles fonctionnalités\n"
            for feature in features:
                changelog += f"- {feature}\n"
            changelog += "\n"
        
        if fixes:
            changelog += "### 🐛 Corrections\n"
            for fix in fixes:
                changelog += f"- {fix}\n"
            changelog += "\n"
        
        if others:
            changelog += "### 🔧 Autres changements\n"
            for other in others:
                changelog += f"- {other}\n"
            changelog += "\n"
        
        return changelog
    
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
    branch_subparsers.add_parser('cleanup', help='Nettoyer les branches fusionnées')
    
    create_branch_parser = branch_subparsers.add_parser('create', help='Créer une branche')
    create_branch_parser.add_argument('type', choices=['feature', 'hotfix', 'release', 'bugfix'])
    create_branch_parser.add_argument('name', help='Nom de la branche')
    create_branch_parser.add_argument('--base', default='master', help='Branche de base')
    
    delete_branch_parser = branch_subparsers.add_parser('delete', help='Supprimer une branche')
    delete_branch_parser.add_argument('name', help='Nom de la branche')
    delete_branch_parser.add_argument('--force', action='store_true', help='Forcer la suppression')
    
    merge_parser = branch_subparsers.add_parser('merge', help='Fusionner une branche')
    merge_parser.add_argument('source', help='Branche source')
    merge_parser.add_argument('--target', default='master', help='Branche cible')
    
    # Tags
    tag_parser = subparsers.add_parser('tag', help='Gestion des tags')
    tag_subparsers = tag_parser.add_subparsers(dest='tag_action')
    
    tag_subparsers.add_parser('list', help='Lister les tags')
    
    create_tag_parser = tag_subparsers.add_parser('create', help='Créer un tag')
    create_tag_parser.add_argument('version', help='Version (ex: 1.0.0)')
    create_tag_parser.add_argument('--message', help='Message du tag')
    create_tag_parser.add_argument('--pre-release', action='store_true', help='Version de pré-release')
    
    delete_tag_parser = tag_subparsers.add_parser('delete', help='Supprimer un tag')
    delete_tag_parser.add_argument('name', help='Nom du tag')
    
    # Changelog
    changelog_parser = subparsers.add_parser('changelog', help='Générer un changelog')
    changelog_parser.add_argument('--from-tag', help='Tag de début')
    changelog_parser.add_argument('--to-tag', help='Tag de fin')
    changelog_parser.add_argument('--output', help='Fichier de sortie')
    
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
        elif args.branch_action == 'cleanup':
            manager.auto_branch_cleanup()
        elif args.branch_action == 'create':
            manager.create_branch(args.type, args.name, args.base)
        elif args.branch_action == 'delete':
            manager.delete_branch(args.name, args.force)
        elif args.branch_action == 'merge':
            manager.merge_branch(args.source, args.target)
    
    elif args.command == 'tag':
        if args.tag_action == 'list':
            manager.list_tags()
        elif args.tag_action == 'create':
            manager.create_tag(args.version, args.message, args.pre_release)
        elif args.tag_action == 'delete':
            manager.delete_tag(args.name)
    
    elif args.command == 'changelog':
        changelog = manager.generate_changelog(getattr(args, 'from_tag', None), getattr(args, 'to_tag', None))
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(changelog)
            print(f"📝 Changelog sauvegardé dans {args.output}")
        else:
            print(changelog)
    
    elif args.command == 'status':
        manager.show_status()


if __name__ == "__main__":
    main()