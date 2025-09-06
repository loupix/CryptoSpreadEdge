# Système de Gestion Git Automatique - CryptoSpreadEdge

## ✅ Fonctionnalités Implémentées

### 1. Gestionnaire Git Automatique
- **Script principal** : `python git.py`
- **Gestionnaire avancé** : `scripts/git/git-manager.py`
- **Version simplifiée** : `scripts/git/git-manager-simple.py`

### 2. Commandes Disponibles

#### Branches
```bash
python git.py branch list                    # Lister les branches
python git.py branch create feature nom     # Créer une branche feature
python git.py branch create hotfix nom      # Créer une branche hotfix
python git.py branch create release nom     # Créer une branche release
python git.py branch create bugfix nom      # Créer une branche bugfix
python git.py branch delete nom             # Supprimer une branche
python git.py cleanup                       # Nettoyer les branches fusionnées
```

#### Tags
```bash
python git.py tag list                      # Lister les tags
python git.py tag create 1.0.0             # Créer un tag de version
python git.py tag create 1.0.0 --pre-release # Créer une pré-release
```

#### Statut
```bash
python git.py status                        # Voir le statut Git complet
python git.py hooks                         # Installer les hooks Git
```

### 3. Hooks Git Automatiques

#### Pre-commit
- Vérification de la syntaxe Python
- Vérification des imports et dépendances
- Vérification des fichiers de configuration
- Détection des secrets exposés

#### Post-commit
- Affichage des informations du commit
- Suggestions d'actions selon le type
- Rappels pour les prochaines étapes

#### Pre-push
- Exécution des tests automatiques
- Vérification de la couverture de code
- Vérification de la qualité du code (Black, isort, mypy)
- Détection des fichiers volumineux

#### Post-merge
- Détection des changements de dépendances
- Suggestions de mise à jour d'environnement

#### Post-checkout
- Suggestions d'environnement conda approprié
- Rappels de configuration

### 4. GitHub Actions

#### CI/CD Pipeline (`.github/workflows/ci.yml`)
- Tests multi-environnements (dev, test)
- Vérification de la qualité du code
- Tests de sécurité avec Bandit
- Build Docker automatique
- Upload des rapports de couverture

#### Release Automatique (`.github/workflows/release.yml`)
- Déclenché par les tags de version
- Génération automatique du changelog
- Build et push des images Docker
- Création des releases GitHub

### 5. Conventions Intégrées

#### Messages de Commit
- `feat:` - Nouvelles fonctionnalités
- `fix:` - Corrections de bugs
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Refactoring
- `chore:` - Tâches de maintenance

#### Nommage des Branches
- `feature/` - Fonctionnalités
- `hotfix/` - Corrections urgentes
- `release/` - Versions
- `bugfix/` - Corrections de bugs

#### Tags de Version
- Format : `vX.Y.Z` (Semantic Versioning)
- Pré-releases : `vX.Y.Z-rc1`, `vX.Y.Z-beta1`

### 6. Intégration avec Cursor

Le fichier `.cursorrules` a été mis à jour avec :
- Règles de gestion Git automatique
- Conventions de nommage
- Workflow de développement
- Commandes utiles

## 🚀 Utilisation

### Démarrage Rapide
```bash
# Voir le statut
python git.py status

# Créer une branche de fonctionnalité
python git.py branch create feature ma-fonctionnalite

# Installer les hooks
python git.py hooks

# Créer un tag de version
python git.py tag create 1.0.0
```

### Workflow Complet
1. **Créer une branche** : `python git.py branch create feature nom`
2. **Développer** : Coder et commiter avec des messages conventionnels
3. **Pousser** : `git push origin feature/nom`
4. **Pull Request** : Créer une PR sur GitHub
5. **Merge** : Après review et approbation
6. **Nettoyer** : `python git.py cleanup`

## 📁 Fichiers Créés

### Scripts
- `git.py` - Script de démarrage rapide
- `scripts/git/git-manager.py` - Gestionnaire complet
- `scripts/git/git-manager-simple.py` - Version simplifiée
- `scripts/git/install-hooks.sh` - Installation hooks (Linux/Mac)
- `scripts/git/install-hooks.ps1` - Installation hooks (Windows)

### Hooks
- `scripts/git/hooks/pre-commit` - Vérifications avant commit
- `scripts/git/hooks/post-commit` - Actions après commit
- `scripts/git/hooks/pre-push` - Vérifications avant push

### GitHub Actions
- `.github/workflows/ci.yml` - Pipeline CI/CD
- `.github/workflows/release.yml` - Release automatique

### Documentation
- `docs/deployment/git-workflow.md` - Documentation complète
- `.cursorrules` - Règles Cursor mises à jour

## 🎯 Avantages

1. **Automatisation** : Plus de tâches Git manuelles
2. **Qualité** : Vérifications automatiques du code
3. **Conventions** : Respect des standards de développement
4. **Traçabilité** : Historique clair et organisé
5. **Collaboration** : Workflow standardisé pour l'équipe
6. **Intégration** : Hooks avec l'environnement conda
7. **CI/CD** : Pipeline automatique complet

## 🔧 Configuration

### Prérequis
- Python 3.11+
- Git
- Environnement conda activé

### Installation
```bash
# Cloner le projet
git clone https://github.com/loupix/CryptoSpreadEdge.git
cd CryptoSpreadEdge

# Activer l'environnement
conda activate cryptospreadedge-dev

# Installer les hooks
python git.py hooks
```

## 📊 Statut Actuel

- ✅ **Architecture** : Complète
- ✅ **Environnement Conda** : Configuré
- ✅ **Gestion Git** : Automatisée
- ✅ **Hooks** : Installés
- ✅ **CI/CD** : Configuré
- ✅ **Documentation** : Complète

Le système de gestion Git automatique est maintenant opérationnel et prêt à être utilisé pour le développement de CryptoSpreadEdge !