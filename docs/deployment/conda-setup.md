# Configuration Conda pour CryptoSpreadEdge

## Vue d'ensemble

CryptoSpreadEdge utilise Conda pour gérer les environnements Python et les dépendances. Cette approche garantit la reproductibilité et la compatibilité entre différents systèmes.

## Types d'environnements

### 1. Environnement de développement (dev)
- **Fichier** : `environment-dev.yml` (Linux/Mac) ou `environment-dev-windows.yml` (Windows)
- **Nom** : `cryptospreadedge-dev`
- **Usage** : Développement local, tests, débogage
- **Caractéristiques** :
  - Packages légers pour le développement
  - Support CPU seulement pour PyTorch
  - Outils de développement inclus (Jupyter, pytest, etc.)

### 2. Environnement de production (prod)
- **Fichier** : `environment.yml`
- **Nom** : `cryptospreadedge-prod`
- **Usage** : Déploiement en production
- **Caractéristiques** :
  - Packages complets avec support GPU
  - Optimisé pour les performances
  - Toutes les dépendances de production

### 3. Environnement de test (test)
- **Fichier** : `environment-test.yml`
- **Nom** : `cryptospreadedge-test`
- **Usage** : Exécution des tests automatisés
- **Caractéristiques** :
  - Packages minimaux pour les tests
  - Outils de test et de qualité de code
  - Pas de dépendances lourdes

## Installation rapide

### Méthode 1 : Script automatique (Recommandé)

```bash
# Configuration complète
python start.py setup dev

# Vérification du statut
python start.py status

# Lancement de l'application
python start.py run dev
```

### Méthode 2 : Gestionnaire conda

```bash
# Créer un environnement
python scripts/setup/conda-manager.py create dev

# Activer l'environnement
conda activate cryptospreadedge-dev

# Mettre à jour l'environnement
python scripts/setup/conda-manager.py update dev

# Supprimer l'environnement
python scripts/setup/conda-manager.py remove dev
```

### Méthode 3 : Manuel

```bash
# Créer l'environnement
conda env create -f environment-dev.yml

# Activer l'environnement
conda activate cryptospreadedge-dev

# Installer les dépendances supplémentaires
pip install -r requirements.txt
```

## Gestion des environnements

### Création d'environnements

```bash
# Environnement de développement
conda env create -f environment-dev.yml

# Environnement de production
conda env create -f environment.yml

# Environnement de test
conda env create -f environment-test.yml
```

### Activation des environnements

```bash
# Développement
conda activate cryptospreadedge-dev

# Production
conda activate cryptospreadedge-prod

# Test
conda activate cryptospreadedge-test
```

### Mise à jour des environnements

```bash
# Mettre à jour depuis le fichier
conda env update -f environment-dev.yml

# Mettre à jour un package spécifique
conda update pandas

# Mettre à jour via pip
pip install --upgrade fastapi
```

### Suppression des environnements

```bash
# Supprimer un environnement
conda env remove -n cryptospreadedge-dev

# Lister les environnements
conda env list
```

## Configuration

### Fichier .condarc

Le fichier `.condarc` contient la configuration conda pour le projet :

```yaml
channels:
  - conda-forge
  - pytorch
  - defaults

channel_priority: flexible
solver: libmamba
```

### Variables d'environnement

Les variables d'environnement sont gérées via le fichier `.env` :

```bash
# Copier le fichier d'exemple
cp config/environments/env.example config/environments/.env

# Éditer la configuration
nano config/environments/.env
```

## Développement

### Structure des environnements

```
CryptoSpreadEdge/
├── environment.yml              # Production
├── environment-dev.yml          # Développement (Linux/Mac)
├── environment-dev-windows.yml  # Développement (Windows)
├── environment-test.yml         # Tests
├── .condarc                     # Configuration conda
└── requirements.txt             # Dépendances pip
```

### Scripts utiles

- `start.py` : Script de démarrage principal
- `scripts/setup/conda-manager.py` : Gestionnaire d'environnements
- `scripts/setup/setup-conda.sh` : Setup automatique (Linux/Mac)
- `scripts/setup/setup-conda.ps1` : Setup automatique (Windows)

### Commandes de développement

```bash
# Démarrer en mode développement
python start.py run dev

# Lancer les tests
python start.py test

# Vérifier le statut
python start.py status

# Activer l'environnement manuellement
conda activate cryptospreadedge-dev
python -m src.main
```

## Dépannage

### Problèmes courants

1. **Package non trouvé**
   ```bash
   # Vérifier les canaux
   conda config --show channels
   
   # Ajouter un canal
   conda config --add channels conda-forge
   ```

2. **Conflits de dépendances**
   ```bash
   # Utiliser le solveur libmamba
   conda install -n cryptospreadedge-dev --solver=libmamba
   ```

3. **Environnement corrompu**
   ```bash
   # Supprimer et recréer
   conda env remove -n cryptospreadedge-dev
   conda env create -f environment-dev.yml
   ```

4. **Problèmes de permissions**
   ```bash
   # Vérifier les permissions
   conda info --envs
   
   # Réparer les permissions
   conda clean --all
   ```

### Logs et débogage

```bash
# Activer les logs détaillés
conda config --set verbosity 3

# Vérifier la configuration
conda info

# Nettoyer le cache
conda clean --all
```

## Bonnes pratiques

### 1. Isolation des environnements
- Utiliser un environnement par projet
- Ne pas installer de packages globalement
- Documenter les dépendances

### 2. Gestion des versions
- Épingler les versions des packages critiques
- Tester les mises à jour dans un environnement séparé
- Utiliser des environnements de test

### 3. Performance
- Utiliser des environnements légers pour le développement
- Optimiser les environnements de production
- Nettoyer régulièrement les caches

### 4. Sécurité
- Ne pas commiter les fichiers `.env`
- Utiliser des clés API séparées par environnement
- Valider les packages avant installation

## Intégration CI/CD

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: conda-incubator/setup-miniconda@v2
        with:
          environment-file: environment-test.yml
          activate-environment: cryptospreadedge-test
      - run: python start.py test
```

### Docker

```dockerfile
FROM continuumio/miniconda3

COPY environment.yml .
RUN conda env create -f environment.yml
SHELL ["conda", "run", "-n", "cryptospreadedge-prod", "/bin/bash", "-c"]

CMD ["conda", "run", "-n", "cryptospreadedge-prod", "python", "-m", "src.main"]
```

Cette configuration conda garantit un environnement de développement stable et reproductible pour CryptoSpreadEdge.