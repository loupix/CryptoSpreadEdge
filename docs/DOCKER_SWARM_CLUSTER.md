# Cluster Docker Swarm CryptoSpreadEdge

Le cluster Docker Swarm CryptoSpreadEdge est une architecture distribuée optimisée pour le trading haute fréquence et l'arbitrage de cryptomonnaies, avec un système de monitoring et d'observabilité complet.

## Architecture du Cluster

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRYPTOSPREADEDGE CLUSTER                    │
├─────────────────────────────────────────────────────────────────┤
│  API Gateway (Load Balancer)                                   │
│  ├── 3 répliques (Manager nodes)                              │
│  └── Health checking + Circuit breaker                        │
├─────────────────────────────────────────────────────────────────┤
│  Microservices de Trading                                      │
│  ├── Market Data Service (3 répliques)                        │
│  ├── Indicators Service (5 répliques)                         │
│  ├── Prediction Service (2 répliques + GPU)                   │
│  ├── Signals Service (3 répliques)                            │
│  ├── Positions Service (2 répliques)                          │
│  ├── Arbitrage Service (4 répliques)                          │
│  └── Backtesting Service (2 répliques)                        │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure de Données                                     │
│  ├── Redis Cluster (3 répliques)                              │
│  ├── PostgreSQL Cluster (2 répliques)                         │
│  ├── Kafka Cluster (3 répliques)                              │
│  └── Zookeeper (1 réplique)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Monitoring & Observabilité                                    │
│  ├── Prometheus (Métriques)                                   │
│  ├── Grafana (Dashboards)                                     │
│  ├── Jaeger (Tracing)                                         │
│  ├── ELK Stack (Logs)                                         │
│  └── Alertmanager (Alertes)                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Microservices

#### 1. Market Data Service
- **Rôle** : Collecte et agrégation des données de marché
- **Répliques** : 3 (Worker nodes)
- **Ressources** : 2 CPU, 4GB RAM
- **Fonctionnalités** :
  - Collecte multi-plateformes (25+ exchanges)
  - Cache Redis distribué
  - Publication Kafka temps réel
  - Health checking automatique

#### 2. Indicators Service
- **Rôle** : Calcul des indicateurs techniques
- **Répliques** : 5 (Worker nodes haute performance)
- **Ressources** : 4 CPU, 8GB RAM
- **Fonctionnalités** :
  - 20+ indicateurs techniques
  - Calculs parallèles (ProcessPoolExecutor)
  - Cache intelligent
  - Métriques de performance

#### 3. Prediction Service
- **Rôle** : Prédictions ML et IA
- **Répliques** : 2 (Worker nodes GPU)
- **Ressources** : 8 CPU, 16GB RAM, GPU
- **Fonctionnalités** :
  - Modèles LSTM, Transformer
  - Ensemble methods
  - Entraînement distribué
  - Prédictions en temps réel

#### 4. Signals Service
- **Rôle** : Génération de signaux de trading
- **Répliques** : 3 (Worker nodes)
- **Ressources** : 2 CPU, 4GB RAM
- **Fonctionnalités** :
  - Stratégies multiples
  - Combinaison intelligente
  - Filtrage de qualité
  - Notifications temps réel

#### 5. Positions Service
- **Rôle** : Gestion des positions
- **Répliques** : 2 (Manager nodes)
- **Ressources** : 2 CPU, 4GB RAM
- **Fonctionnalités** :
  - Dimensionnement optimisé
  - Gestion des risques
  - Persistance PostgreSQL
  - Métriques de performance

#### 6. Arbitrage Service
- **Rôle** : Détection et exécution d'arbitrage
- **Répliques** : 4 (Worker nodes basse latence)
- **Ressources** : 6 CPU, 8GB RAM
- **Fonctionnalités** :
  - Scan multi-plateformes
  - Exécution parallèle
  - Gestion des retry
  - Monitoring temps réel

#### 7. Backtesting Service
- **Rôle** : Tests de stratégies
- **Répliques** : 2 (Worker nodes)
- **Ressources** : 4 CPU, 8GB RAM
- **Fonctionnalités** :
  - Tests historiques
  - Métriques avancées
  - Optimisation de paramètres
  - Rapports détaillés

### Infrastructure de Données

#### Redis Cluster
- **Rôle** : Cache distribué et session store
- **Répliques** : 3 (Worker nodes)
- **Fonctionnalités** :
  - Cache des données de marché
  - Cache des indicateurs
  - Cache des prédictions
  - Persistance AOF

#### PostgreSQL Cluster
- **Rôle** : Base de données principale
- **Répliques** : 2 (Worker nodes)
- **Fonctionnalités** :
  - Données des positions
  - Historique des trades
  - Configuration des stratégies
  - Réplication maître-esclave

#### Kafka Cluster
- **Rôle** : Messaging asynchrone
- **Répliques** : 3 (Worker nodes)
- **Fonctionnalités** :
  - Topics de données de marché
  - Topics d'indicateurs
  - Topics de prédictions
  - Topics de signaux

### Monitoring et Observabilité

#### Prometheus
- **Rôle** : Collecte de métriques
- **Fonctionnalités** :
  - Métriques des services
  - Métriques système
  - Métriques applicatives
  - Alerting rules

#### Grafana
- **Rôle** : Visualisation des métriques
- **Fonctionnalités** :
  - Dashboards temps réel
  - Alertes visuelles
  - Rapports personnalisés
  - Intégration Prometheus

#### Jaeger
- **Rôle** : Tracing distribué
- **Fonctionnalités** :
  - Traçage des requêtes
  - Analyse des performances
  - Détection des goulots
  - Visualisation des flux

#### ELK Stack
- **Rôle** : Gestion des logs
- **Fonctionnalités** :
  - Collecte centralisée
  - Indexation Elasticsearch
  - Recherche Kibana
  - Analyse Logstash

## Déploiement

### Prérequis

```bash
# Docker et Docker Swarm
docker --version
docker swarm init

# Outils optionnels
jq --version  # Pour le parsing JSON
curl --version  # Pour les health checks
```

### Déploiement Simple

```bash
# Déployer le cluster complet
./scripts/deployment/deploy-complete-cluster.sh

# Vérifier le statut
./scripts/deployment/manage-swarm-cluster.sh status

# Surveiller en temps réel
./scripts/deployment/manage-swarm-cluster.sh monitor
```

### Déploiement Avancé

```bash
# 1. Configurer les labels des nœuds
docker node update --label-add performance=high <node-id>
docker node update --label-add gpu=true <node-id>

# 2. Déployer le système de trading
docker stack deploy -c infrastructure/docker/swarm/docker-stack-optimized.yml cryptospreadedge

# 3. Déployer le monitoring
docker stack deploy -c infrastructure/monitoring/docker-compose.monitoring.yml cryptospreadedge-monitoring

# 4. Vérifier la santé
./scripts/deployment/manage-swarm-cluster.sh health
```

## Configuration

### Variables d'Environnement

#### Services de Trading
```yaml
# Market Data Service
REDIS_URL: redis://redis-cluster:6379
KAFKA_BROKERS: kafka-cluster:9092
LOG_LEVEL: INFO

# Indicators Service
NUM_WORKERS: 4
CACHE_TTL: 600

# Prediction Service
CUDA_VISIBLE_DEVICES: 0
MODEL_PATH: /app/models

# Positions Service
POSTGRES_URL: postgresql://postgres:password@postgres-cluster:5432/trading
MAX_POSITIONS: 10
```

#### Monitoring
```yaml
# Prometheus
RETENTION_TIME: 200h
SCRAPE_INTERVAL: 15s

# Grafana
GF_SECURITY_ADMIN_PASSWORD: admin123
GF_USERS_ALLOW_SIGN_UP: false

# Elasticsearch
ES_JAVA_OPTS: -Xms4g -Xmx4g
discovery.type: single-node
```

### Ressources et Limites

#### CPU et Mémoire
```yaml
# Services critiques
api-gateway:
  limits: { cpus: '2.0', memory: 2G }
  reservations: { cpus: '1.0', memory: 1G }

# Services de calcul
indicators-service:
  limits: { cpus: '4.0', memory: 8G }
  reservations: { cpus: '2.0', memory: 4G }

# Services ML
prediction-service:
  limits: { cpus: '8.0', memory: 16G }
  reservations: { cpus: '4.0', memory: 8G }
```

#### Stockage
```yaml
# Volumes persistants
volumes:
  market-data-cache: { driver: local }
  indicators-cache: { driver: local }
  models-data: { driver: local }
  postgres-data: { driver: local }
  redis-data: { driver: local }
```

## Monitoring

### Métriques Disponibles

#### Métriques Système
- **CPU** : Utilisation par nœud et conteneur
- **Mémoire** : Utilisation et limites
- **Réseau** : Trafic entrant/sortant
- **Disque** : Espace utilisé et I/O

#### Métriques Applicatives
- **Trading** : Signaux générés, positions ouvertes
- **Arbitrage** : Opportunités détectées, profits
- **Performance** : Temps de réponse, throughput
- **Erreurs** : Taux d'erreur, exceptions

#### Métriques Business
- **P&L** : Profit et perte en temps réel
- **Volume** : Volume de trading
- **Latence** : Latence des opérations
- **Disponibilité** : Uptime des services

### Dashboards Grafana

#### Dashboard Principal
- Vue d'ensemble du cluster
- Métriques de performance
- Alertes actives
- Statut des services

#### Dashboard Trading
- Signaux en temps réel
- Positions ouvertes
- P&L par stratégie
- Métriques d'arbitrage

#### Dashboard Infrastructure
- Utilisation des ressources
- Santé des services
- Logs d'erreurs
- Métriques réseau

### Alertes

#### Alertes Critiques
- Service down
- Erreur de trading
- Perte de données
- Surcharge système

#### Alertes de Performance
- Latence élevée
- Utilisation CPU > 80%
- Mémoire > 90%
- Erreurs > 5%

#### Alertes Business
- P&L négatif
- Volume anormal
- Opportunités manquées
- Risque élevé

## Gestion du Cluster

### Commandes de Base

```bash
# Statut du cluster
./scripts/deployment/manage-swarm-cluster.sh status

# Santé des services
./scripts/deployment/manage-swarm-cluster.sh health

# Logs d'un service
./scripts/deployment/manage-swarm-cluster.sh logs api-gateway 200

# Redémarrer un service
./scripts/deployment/manage-swarm-cluster.sh restart indicators-service

# Mettre à l'échelle
./scripts/deployment/manage-swarm-cluster.sh scale indicators-service 8

# Surveillance temps réel
./scripts/deployment/manage-swarm-cluster.sh monitor
```

### Maintenance

#### Nettoyage
```bash
# Nettoyer le système
./scripts/deployment/manage-swarm-cluster.sh cleanup

# Sauvegarder la configuration
./scripts/deployment/manage-swarm-cluster.sh backup

# Mettre à jour le stack
./scripts/deployment/manage-swarm-cluster.sh update docker-stack-optimized.yml
```

#### Scaling
```bash
# Mettre à l'échelle automatiquement
docker service update --replicas 10 indicators-service

# Mettre à l'échelle avec contraintes
docker service update \
  --constraint-add node.labels.performance==high \
  --replicas 5 prediction-service
```

### Sauvegarde et Récupération

#### Sauvegarde
```bash
# Sauvegarde complète
./scripts/deployment/manage-swarm-cluster.sh backup

# Sauvegarde des données
docker run --rm -v postgres-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/postgres-backup.tar.gz -C /data .
```

#### Récupération
```bash
# Restaurer la configuration
docker stack deploy -c backup/stack-config.yml cryptospreadedge

# Restaurer les données
docker run --rm -v postgres-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/postgres-backup.tar.gz -C /data
```

## Optimisations

### Performance

#### Calculs Parallèles
- ProcessPoolExecutor pour les indicateurs
- ThreadPoolExecutor pour les I/O
- Calculs GPU pour le ML
- Cache distribué Redis

#### Réseau
- Load balancing intelligent
- Circuit breaker pattern
- Retry automatique
- Compression gzip

#### Stockage
- Cache multi-niveaux
- Persistance optimisée
- Compression des données
- Nettoyage automatique

### Sécurité

#### Conteneurs
- Utilisateurs non-root
- Images minimales
- Scan de vulnérabilités
- Mise à jour automatique

#### Réseau
- Isolation des réseaux
- Chiffrement TLS
- Authentification API
- Rate limiting

#### Données
- Chiffrement au repos
- Chiffrement en transit
- Rotation des clés
- Audit des accès

### Fiabilité

#### Haute Disponibilité
- Répliques multiples
- Distribution des nœuds
- Health checking
- Auto-recovery

#### Résilience
- Circuit breaker
- Retry policies
- Timeout configuration
- Graceful shutdown

#### Observabilité
- Logging centralisé
- Métriques détaillées
- Tracing distribué
- Alerting intelligent

## URLs d'Accès

### Services de Trading
- **API Gateway** : http://gateway-ip
- **Health Check** : http://gateway-ip/health
- **Métriques** : http://gateway-ip/metrics

### Monitoring
- **Prometheus** : http://prometheus-ip:9090
- **Grafana** : http://grafana-ip:3000 (admin/admin123)
- **Jaeger** : http://jaeger-ip:16686
- **Kibana** : http://kibana-ip:5601

### Services Individuels
- **Market Data** : http://gateway-ip/market-data
- **Indicators** : http://gateway-ip/indicators
- **Predictions** : http://gateway-ip/predictions
- **Signals** : http://gateway-ip/signals
- **Positions** : http://gateway-ip/positions
- **Arbitrage** : http://gateway-ip/arbitrage
- **Backtesting** : http://gateway-ip/backtesting

## Dépannage

### Problèmes Courants

#### Service Non Accessible
```bash
# Vérifier le statut
docker service ls
docker service ps <service-name>

# Vérifier les logs
docker service logs <service-name>

# Redémarrer le service
docker service update --force <service-name>
```

#### Performance Dégradée
```bash
# Vérifier les ressources
docker stats

# Vérifier les métriques
curl http://gateway-ip/metrics

# Mettre à l'échelle
docker service scale <service-name>=<replicas>
```

#### Erreurs de Connexion
```bash
# Vérifier le réseau
docker network ls
docker network inspect <network-name>

# Vérifier les services
docker service inspect <service-name>
```

### Logs et Debugging

#### Logs des Services
```bash
# Logs en temps réel
docker service logs -f <service-name>

# Logs avec filtrage
docker service logs <service-name> | grep ERROR

# Logs des dernières 100 lignes
docker service logs --tail 100 <service-name>
```

#### Debugging Avancé
```bash
# Entrer dans un conteneur
docker exec -it <container-id> /bin/bash

# Vérifier les variables d'environnement
docker exec <container-id> env

# Vérifier les ports
docker exec <container-id> netstat -tlnp
```

Le cluster Docker Swarm CryptoSpreadEdge représente l'état de l'art en matière d'architecture distribuée pour le trading haute fréquence, offrant une scalabilité, une fiabilité et une observabilité exceptionnelles pour les opérations de trading de cryptomonnaies.