# Workflow Git pour CryptoSpreadEdge

## Vue d'ensemble

CryptoSpreadEdge utilise un système de gestion Git automatisé avec des conventions strictes pour les branches, tags et commits. Ce workflow garantit la traçabilité, la qualité du code et la collaboration efficace.

## Conventions de nommage

### Branches

- **feature/** : Nouvelles fonctionnalités
  - Exemple : `feature/arbitrage-strategy`
  - Exemple : `feature/ai-models`

- **hotfix/** : Corrections urgentes
  - Exemple : `hotfix/critical-bug-fix`
  - Exemple : `hotfix/security-patch`

- **release/** : Préparation des versions
  - Exemple : `release/v1.0.0`
  - Exemple : `release/v1.1.0`

- **bugfix/** : Corrections de bugs
  - Exemple : `bugfix/order-processing-error`
  - Exemple : `bugfix/data-sync-issue`

### Tags

- **Format** : `vX.Y.Z` (Semantic Versioning)
- **Exemples** : `v1.0.0`, `v1.1.0`, `v2.0.0`
- **Pré-releases** : `v1.0.0-rc1`, `v1.0.0-beta1`

### Messages de commit

- **feat:** : Nouvelles fonctionnalités
- **fix:** : Corrections de bugs
- **docs:** : Documentation
- **test:** : Tests
- **refactor:** : Refactoring
- **chore:** : Tâches de maintenance
- **perf:** : Améliorations de performance
- **ci:** : Configuration CI/CD

## Commandes de base

### Gestion des branches

```bash
# Voir le statut
python git.py status

# Lister les branches
python git.py branch list

# Créer une branche
python git.py branch create feature nom-fonctionnalite

# Supprimer une branche
python git.py branch delete feature/nom-fonctionnalite

# Nettoyer les branches fusionnées
python git.py cleanup
```

### Gestion des tags

```bash
# Lister les tags
python git.py tag list

# Créer un tag
python git.py tag create 1.0.0

# Créer une pré-release
python git.py tag create 1.0.0 --pre-release
```

### Installation des hooks

```bash
# Windows
python git.py hooks

# Linux/Mac
bash scripts/git/install-hooks.sh
```

## Workflow de développement

### 1. Développement d'une fonctionnalité

```bash
# Créer une branche
python git.py branch create feature nouvelle-fonctionnalite

# Développer et commiter
git add .
git commit -m "feat: ajout de la nouvelle fonctionnalité"

# Pousser la branche
git push origin feature/nouvelle-fonctionnalite

# Créer une Pull Request sur GitHub
```

### 2. Correction d'un bug

```bash
# Créer une branche de hotfix
python git.py branch create hotfix correction-urgente

# Corriger et commiter
git add .
git commit -m "fix: correction du bug critique"

# Pousser et fusionner rapidement
git push origin hotfix/correction-urgente
```

### 3. Préparation d'une release

```bash
# Créer une branche de release
python git.py branch create release v1.0.0

# Finaliser la version
# Mettre à jour la documentation
# Tester

# Créer le tag
python git.py tag create 1.0.0

# Fusionner vers master
git checkout master
git merge release/v1.0.0
git push origin master
```

## Hooks Git automatiques

### Pre-commit
- Vérification de la syntaxe Python
- Vérification des imports
- Vérification des fichiers de configuration
- Vérification des secrets

### Post-commit
- Affichage des informations du commit
- Suggestions d'actions selon le type de commit
- Rappels pour les prochaines étapes

### Pre-push
- Exécution des tests
- Vérification de la couverture de code
- Vérification de la qualité du code
- Vérification des secrets

### Post-merge
- Détection des changements de dépendances
- Suggestions de mise à jour d'environnement

### Post-checkout
- Suggestions d'environnement conda approprié
- Rappels de configuration

## GitHub Actions

### CI/CD Pipeline

Le pipeline automatique vérifie :
- Tests unitaires et d'intégration
- Qualité du code (Black, isort, mypy)
- Couverture de code
- Sécurité (Bandit)
- Build Docker

### Release automatique

- Déclenché par les tags de version
- Génération automatique du changelog
- Build et push des images Docker
- Création des releases GitHub

## Bonnes pratiques

### 1. Branches
- Une branche par fonctionnalité/bug
- Noms descriptifs et courts
- Supprimer les branches fusionnées
- Ne jamais commiter directement sur master

### 2. Commits
- Messages clairs et descriptifs
- Un commit par changement logique
- Utiliser les conventions de message
- Tester avant de commiter

### 3. Pull Requests
- Description détaillée des changements
- Tests et vérifications
- Review de code obligatoire
- Merge après approbation

### 4. Tags
- Créer des tags pour chaque release
- Utiliser le versioning sémantique
- Documenter les changements
- Tester avant de tagger

## Dépannage

### Problèmes courants

1. **Branche non trouvée**
   ```bash
   git fetch origin
   python git.py branch list
   ```

2. **Conflits de merge**
   ```bash
   git status
   # Résoudre les conflits
   git add .
   git commit -m "fix: résolution des conflits"
   ```

3. **Hooks qui échouent**
   ```bash
   # Réinstaller les hooks
   python git.py hooks
   ```

4. **Tag déjà existant**
   ```bash
   # Supprimer le tag local
   git tag -d v1.0.0
   # Supprimer le tag distant
   git push origin --delete v1.0.0
   ```

### Commandes utiles

```bash
# Voir l'historique des commits
git log --oneline

# Voir les différences
git diff

# Annuler le dernier commit
git reset --soft HEAD~1

# Voir les branches distantes
git branch -r

# Synchroniser avec le remote
git fetch origin
git pull origin master
```

## Intégration avec l'environnement

### Conda
- Changement automatique d'environnement selon la branche
- Suggestions d'environnement approprié
- Vérification des dépendances

### Docker
- Build automatique des images
- Tests dans des conteneurs
- Déploiement automatisé

### Monitoring
- Métriques de qualité du code
- Temps de build et de test
- Couverture de code

Ce workflow garantit un développement efficace et une qualité de code élevée pour CryptoSpreadEdge.