# CryptoSpreadEdge

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
- **Déploiement Docker Swarm** : Infrastructure scalable et résiliente

## Architecture

Le projet suit une architecture modulaire avec les composants suivants :

- **Core** : Moteur de trading, gestion des données de marché, ordres et risques
- **Connectors** : Connecteurs pour les différentes plateformes d'échange
- **AI** : Modèles d'IA, stratégies de trading et backtesting
- **Data** : Gestion des données temps réel, stockage et analytics
- **API** : Interfaces REST, WebSocket, gRPC et GraphQL
- **Monitoring** : Métriques, logs, alertes et dashboards

## Technologies utilisées

- **Backend** : Python 3.11+, FastAPI, asyncio
- **Trading** : CCXT, WebSockets, Redis, InfluxDB
- **IA/ML** : PyTorch, TensorFlow, scikit-learn, TA-Lib
- **Infrastructure** : Docker Swarm, Prometheus, Grafana, ELK Stack

## Installation

### Prérequis

- Python 3.11+
- Docker et Docker Swarm
- Redis
- InfluxDB

### Installation locale

```bash
# Cloner le repository
git clone https://github.com/username/CryptoSpreadEdge.git
cd CryptoSpreadEdge

# Installer les dépendances
pip install -r requirements.txt

# Configuration
cp config/environments/.env.example config/environments/.env
# Éditer le fichier .env avec vos clés API

# Lancer les services
docker-compose up -d
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
# Lancer le système complet
python -m src.main

# Lancer seulement les connecteurs de données
python -m src.connectors.main

# Lancer les stratégies d'IA
python -m src.ai.main
```

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

# Tests de performance
pytest tests/performance
```

### Formatage du code

```bash
# Formatage automatique
black src/
isort src/

# Vérification des types
mypy src/
```

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