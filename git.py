#!/usr/bin/env python3
"""
Script de démarrage rapide pour la gestion Git de CryptoSpreadEdge
"""

import sys
import subprocess
from pathlib import Path

def run_command(command):
    """Exécute une commande et retourne le résultat"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    if len(sys.argv) < 2:
        print("🔧 Gestionnaire Git CryptoSpreadEdge")
        print("=" * 40)
        print()
        print("Commandes disponibles:")
        print("  python git.py status          - Voir le statut")
        print("  python git.py branch <action> - Gérer les branches")
        print("  python git.py tag <action>    - Gérer les tags")
        print("  python git.py hooks           - Installer les hooks")
        print("  python git.py cleanup         - Nettoyer les branches")
        print("  python git.py changelog       - Générer le changelog")
        print()
        print("Exemples:")
        print("  python git.py branch create feature nouvelle-fonctionnalite")
        print("  python git.py tag create 1.0.0")
        print("  python git.py hooks")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        # Utiliser le gestionnaire Git simplifié
        success, stdout, stderr = run_command("python scripts/git/git-manager-simple.py status")
        if success:
            print(stdout)
        else:
            print(f"Erreur: {stderr}")
    
    elif command == "hooks":
        # Installer les hooks
        print("🔧 Installation des hooks Git...")
        if sys.platform == "win32":
            success, stdout, stderr = run_command("powershell -ExecutionPolicy Bypass -File scripts/git/install-hooks.ps1")
        else:
            success, stdout, stderr = run_command("bash scripts/git/install-hooks.sh")
        
        if success:
            print("✅ Hooks installés avec succès!")
        else:
            print(f"❌ Erreur lors de l'installation: {stderr}")
    
    elif command == "cleanup":
        # Nettoyer les branches
        success, stdout, stderr = run_command("python scripts/git/git-manager.py branch cleanup")
        if success:
            print(stdout)
        else:
            print(f"Erreur: {stderr}")
    
    elif command == "changelog":
        # Générer le changelog
        success, stdout, stderr = run_command("python scripts/git/git-manager.py changelog")
        if success:
            print(stdout)
        else:
            print(f"Erreur: {stderr}")
    
    elif command in ["branch", "tag"]:
        # Déléguer au gestionnaire Git simplifié
        args = sys.argv[1:]
        cmd = f"python scripts/git/git-manager-simple.py {' '.join(args)}"
        success, stdout, stderr = run_command(cmd)
        if success:
            print(stdout)
        else:
            print(f"Erreur: {stderr}")
    
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Utilisez 'python git.py' pour voir les commandes disponibles")

if __name__ == "__main__":
    main()