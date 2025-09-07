# CryptoSpreadEdge

![Tests](https://github.com/loupix/CryptoSpreadEdge/actions/workflows/tests.yml/badge.svg)

Système de trading crypto haute fréquence avec intelligence artificielle et déploiement Docker Swarm.

## Vue d'ensemble

CryptoSpreadEdge est une plateforme de trading automatisée pour les cryptomonnaies, conçue pour la haute fréquence et l'optimisation maximale. Le système utilise des stratégies d'IA en temps réel et se connecte à de multiples plateformes d'échange pour maximiser les opportunités de trading.

## Fonctionnalités principales

- **Trading haute fréquence** : Exécution ultra-rapide des ordres
- **Multi-plateformes** : Support de Binance, Coinbase, Kraken, Bybit et plus
- **Temps réel** : Données de marché en streaming continu
- **IA intégrée** : Stratégies de trading basées sur l'apprentissage automatique
- **Analyse de marché** : Détection automatique des opportunités
- **Gestion des risques** : Contrôles automatiques et alertes
- **Persistance PostgreSQL** : Stockage robuste des données de trading
- **APIs historiques** : Accès complet à l'historique des opérations
- **Déploiement Docker Swarm** : Infrastructure scalable et résiliente

## Architecture

Le projet suit une architecture modulaire avec les composants suivants :

- **Core** : Moteur de trading, gestion des données de marché, ordres et risques
- **Frontend** : Interface React moderne avec trading, monitoring et administration
- **Connectors** : Connecteurs pour les différentes plateformes d'échange
- **AI** : Modèles d'IA, stratégies de trading et backtesting
- **Data** : Gestion des données temps réel, stockage et analytics
- **API** : Interfaces REST, WebSocket, gRPC et GraphQL
- **Monitoring** : Métriques, logs, alertes et dashboards

## Technologies utilisées

- **Backend** : Python 3.11+, FastAPI, asyncio
- **Frontend** : React 18, TypeScript, Material-UI v5
- **Trading** : CCXT, WebSockets, Redis, InfluxDB
- **Base de données** : PostgreSQL, SQLAlchemy, asyncpg
- **IA/ML** : PyTorch, TensorFlow, scikit-learn, TA-Lib
- **Infrastructure** : Docker Swarm, Prometheus, Grafana, ELK Stack

## Installation

### Prérequis

- Python 3.11+
- Conda (Miniconda ou Anaconda)
- Docker et Docker Swarm
- Redis
- InfluxDB

### Installation avec Conda (Recommandé)

```bash
# Cloner le repository
git clone https://github.com/loupix/CryptoSpreadEdge.git
cd CryptoSpreadEdge

# Méthode 1: Script automatique
python start.py setup dev

# Méthode 2: Gestionnaire conda
python scripts/setup/conda-manager.py create dev
python scripts/setup/conda-manager.py setup

# Méthode 3: Manuel
conda env create -f environment-dev.yml
conda activate cryptospreadedge-dev
```

### Installation avec pip (Alternative)

```bash
# Cloner le repository
git clone https://github.com/loupix/CryptoSpreadEdge.git
cd CryptoSpreadEdge

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp config/environments/env.example config/environments/.env
# Éditer le fichier .env avec vos clés API
```

### Déploiement Docker Swarm

```bash
# Initialiser le swarm
docker swarm init

# Déployer la stack
docker stack deploy -c infrastructure/docker/swarm/docker-stack.yml cryptospreadedge
```

## Configuration

1. Copier les fichiers de configuration d'exemple
2. Configurer les clés API des exchanges
3. Ajuster les paramètres de trading selon vos besoins
4. Configurer les stratégies d'IA

## Utilisation

### Démarrage rapide

```bash
# Méthode 1: Script de démarrage (recommandé)
python start.py run dev      # Mode développement
python start.py run prod     # Mode production
python start.py test         # Lancer les tests
python start.py status       # Voir le statut

# Méthode 2: Manuel
conda activate cryptospreadedge-dev
python -m src.main

# Méthode 3: Direct
python -m src.main
```

### Gestion des environnements

```bash
# Créer un environnement
python scripts/setup/conda-manager.py create dev
python scripts/setup/conda-manager.py create prod
python scripts/setup/conda-manager.py create test

# Activer un environnement
conda activate cryptospreadedge-dev
conda activate cryptospreadedge-prod
conda activate cryptospreadedge-test

# Mettre à jour un environnement
python scripts/setup/conda-manager.py update dev

# Supprimer un environnement
python scripts/setup/conda-manager.py remove dev

# Lister les environnements
python scripts/setup/conda-manager.py list
```

### Types d'environnements

- **dev** : Environnement de développement (léger, CPU seulement)
- **prod** : Environnement de production (complet, GPU support)
- **test** : Environnement de test (minimal, pour les tests)

### API

Une fois démarré, l'API est disponible sur `http://localhost:8000`

- Documentation interactive : `http://localhost:8000/docs`
- WebSocket temps réel : `ws://localhost:8000/ws`

## Stratégies de trading

Le système inclut plusieurs stratégies d'IA :

- **Arbitrage** : Détection des écarts de prix entre exchanges
- **Momentum** : Trading basé sur les tendances
- **Mean Reversion** : Retour à la moyenne
- **Machine Learning** : Modèles prédictifs personnalisés

## Monitoring

- **Métriques** : Prometheus sur `http://localhost:9090`
- **Dashboards** : Grafana sur `http://localhost:3000`
- **Logs** : Kibana sur `http://localhost:5601`

## Développement

### Tests

```bash
# Tests unitaires
pytest tests/unit

# Tests d'intégration
pytest tests/integration

# Tests end-to-end
pytest tests/e2e

# Tests de performance
pytest tests/performance
```

#### Notes sur l'exécution des tests

- Certains tests externes (deep learning, prédiction) requièrent `torch` ou `ta-lib`. Ils ne sont pas inclus par défaut.
- Pour exécuter notre pipeline d'indicateurs sans ces dépendances: `pytest -k "not deep_learning and not prediction"`.
- La CI exécute automatiquement `tests/unit` et `tests/integration` sur chaque PR, et `tests/e2e` sur la branche `main`.

### Formatage du code

```bash
# Formatage automatique
black src/
isort src/

# Vérification des types
mypy src/
```

## Frontend

Le frontend React de CryptoSpreadEdge offre une interface utilisateur moderne et complète :

### Fonctionnalités Frontend
- **Interface de Trading** : Ordres, positions, trades en temps réel
- **Gestion des Utilisateurs** : Administration, rôles, permissions
- **Données Historiques** : Ordres, positions, trades, portefeuille
- **Configuration des Exchanges** : Multi-plateformes (Binance, Coinbase, etc.)
- **Monitoring** : Performance système et optimisation
- **Sécurité** : Authentification, autorisation, audit trail

### Démarrage Frontend
```bash
cd frontend
npm install
cp env.example .env
npm start
```

### Documentation Frontend
Toute la documentation détaillée du frontend est disponible dans [`docs/frontend/`](docs/frontend/) :
- [Documentation principale](docs/frontend/README.md)
- [Intégration base de données](docs/frontend/FRONTEND_DATABASE_INTEGRATION.md)
- [Résumé des fonctionnalités](docs/frontend/FRONTEND_COMPLETE_SUMMARY.md)
- [Résumé du développement](docs/frontend/FRONTEND_DEVELOPMENT_COMPLETE.md)

## Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Avertissement

Le trading de cryptomonnaies comporte des risques élevés. Ce logiciel est fourni à des fins éducatives et de recherche. Utilisez-le à vos propres risques.