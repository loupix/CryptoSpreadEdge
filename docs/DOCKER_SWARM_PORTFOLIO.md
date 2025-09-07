# Déploiement Docker Swarm - Portfolio Multi-Plateformes

Ce document décrit le déploiement optimisé du système de rebalance de portefeuille multi-plateformes sur Docker Swarm.

## Architecture Optimisée

### Services Principaux

1. **cryptospreadedge-main** (2 répliques)
   - Service principal avec rebalance intégré
   - Ports: 8000 (API), 9001 (métriques rebalance)
   - Ressources: 1.5-3.0 CPU, 3-8GB RAM
   - Placement: nœuds worker avec label `tier=trading`

2. **portfolio-rebalancer** (1 réplique)
   - Service dédié pour le rebalance de portefeuille
   - Ressources: 0.5-1.5 CPU, 1-3GB RAM
   - Placement: nœuds worker avec label `tier=portfolio`

3. **arbitrage-worker** (3 répliques)
   - Service dédié pour l'arbitrage intensif
   - Ressources: 0.5-2.0 CPU, 1-4GB RAM
   - Placement: nœuds worker avec label `tier=arbitrage`

4. **portfolio-monitor** (1 réplique)
   - Service de monitoring des métriques de rebalance
   - Port: 9002
   - Placement: nœud manager

### Infrastructure

- **Redis**: Cache et pub/sub (1 réplique, manager)
- **InfluxDB**: Données time-series (1 réplique, manager)
- **Kafka**: Streaming de données (1 réplique, manager)
- **Prometheus**: Métriques (1 réplique, manager)
- **Grafana**: Dashboards (1 réplique, manager)
- **Elasticsearch + Kibana**: Logs centralisés
- **Nginx**: Load balancer et reverse proxy

## Configuration

### Variables d'Environnement

Le rebalance est configuré via les variables d'environnement suivantes :

```bash
# Activation et timing
CSE_REBALANCE_ENABLED=1
CSE_REBALANCE_INTERVAL=300

# Méthode d'allocation
CSE_REBALANCE_METHOD=rp  # risk-parity ou mean-variance

# Covariance et volatilité
CSE_REBALANCE_USE_REAL_COV=1
CSE_REBALANCE_VOL_TARGET_ENABLED=1
CSE_REBALANCE_VOL_TARGET=0.01

# Exécution
CSE_REBALANCE_DRY_RUN=0
CSE_REBALANCE_MAX_ORDERS=10

# Coûts et contraintes
CSE_REBALANCE_FEE_RATE=0.001
CSE_REBALANCE_SLIPPAGE_BPS=5
CSE_REBALANCE_MIN_NOTIONAL=10.0

# Backoff dynamique
CSE_REBALANCE_BACKOFF_ENABLED=1
CSE_REBALANCE_BACKOFF_MULT=2.0
CSE_REBALANCE_BACKOFF_MAX=3600

# Monitoring
CSE_REBALANCE_PROMETHEUS=1
CSE_REBALANCE_PROM_PORT=9001
```

### Secrets Docker Swarm

Les secrets suivants doivent être créés :

```bash
# Clés API des exchanges
docker secret create api_keys_encrypted config/api_keys.encrypted

# Configuration arbitrage
docker secret create arbitrage_env config/environments/arbitrage.env

# Configuration rebalance
docker secret create rebalance_env config/environments/rebalance.env
```

### Configs Docker Swarm

```bash
# Configuration Nginx
docker config create nginx_conf infrastructure/nginx/nginx-portfolio.conf

# Configuration Prometheus
docker config create prometheus_conf infrastructure/monitoring/prometheus-portfolio.yml

# Dashboards Grafana
docker config create grafana_dashboards infrastructure/monitoring/grafana-dashboards-portfolio.json
```

## Déploiement

### Prérequis

1. Docker Swarm initialisé
2. Nœuds avec labels appropriés :
   ```bash
   # Nœuds de trading
   docker node update --label-add tier=trading <node-id>
   
   # Nœuds d'arbitrage
   docker node update --label-add tier=arbitrage <node-id>
   
   # Nœuds de portefeuille
   docker node update --label-add tier=portfolio <node-id>
   ```

### Script de Déploiement

```bash
# Déploiement complet
./scripts/deployment/deploy-portfolio-swarm.sh production deploy

# Vérification du statut
./scripts/deployment/deploy-portfolio-swarm.sh production status

# Consultation des logs
./scripts/deployment/deploy-portfolio-swarm.sh production logs

# Nettoyage
./scripts/deployment/deploy-portfolio-swarm.sh production cleanup
```

### Déploiement Manuel

```bash
# 1. Créer les secrets et configs
docker secret create api_keys_encrypted config/api_keys.encrypted
docker secret create arbitrage_env config/environments/arbitrage.env
docker secret create rebalance_env config/environments/rebalance.env

docker config create nginx_conf infrastructure/nginx/nginx-portfolio.conf
docker config create prometheus_conf infrastructure/monitoring/prometheus-portfolio.yml
docker config create grafana_dashboards infrastructure/monitoring/grafana-dashboards-portfolio.json

# 2. Construire l'image
docker build -t cryptospreadedge:latest -f infrastructure/docker/services/cryptospreadedge/Dockerfile .

# 3. Déployer le stack
docker stack deploy -c infrastructure/docker/swarm/docker-stack-portfolio-optimized.yml cryptospreadedge-portfolio
```

## Monitoring

### Métriques Prometheus

Le système expose les métriques suivantes :

- `portfolio_rebalance_orders_placed_total`: Nombre d'ordres placés
- `portfolio_rebalance_orders_skipped_total`: Nombre d'ordres ignorés
- `portfolio_rebalance_errors_total`: Nombre d'erreurs
- `portfolio_rebalance_transaction_costs_total`: Coûts de transaction
- `portfolio_rebalance_actual_volatility`: Volatilité réelle
- `portfolio_rebalance_target_volatility`: Volatilité cible
- `portfolio_rebalance_backoff_active`: État du backoff
- `portfolio_total_value`: Valeur totale du portefeuille
- `portfolio_symbol_allocation`: Allocation par symbole
- `portfolio_exchange_pnl`: PnL par exchange

### Dashboards Grafana

1. **Portfolio Rebalance Dashboard**
   - Valeur du portefeuille dans le temps
   - Statut des ordres de rebalance
   - Coûts de transaction
   - Volatilité cible vs réelle
   - État du backoff
   - Taux d'erreur

2. **Portfolio Performance Dashboard**
   - Allocation par symbole (graphique en secteurs)
   - PnL par exchange
   - Corrélations entre positions
   - Drawdown du portefeuille

### Alertes

Les règles d'alerte suivantes sont configurées :

- **Taux d'échec élevé du rebalance** (> 0.1 erreurs/seconde)
- **Trop d'ordres ignorés** (> 0.5 ordres/seconde)
- **Backoff activé fréquemment** (> 0.1 activations/minute)
- **Coûts de transaction élevés** (> 100 USD/minute)
- **Volatilité cible non atteinte** (différence > 0.005)
- **Portefeuille en perte significative** (< -1000 USD)
- **Corrélation élevée entre positions** (> 0.8)
- **Drawdown élevé** (> 10%)

## Accès aux Services

- **API Principale**: http://localhost/api/
- **Métriques Rebalance**: http://localhost/metrics ou http://localhost:9001/
- **Monitoring Portfolio**: http://localhost:9002/
- **Prometheus**: http://localhost/prometheus/
- **Grafana**: http://localhost/grafana/ (admin/admin123)

## Optimisations

### Ressources

- **CPU**: Allocation dynamique basée sur la charge
- **Mémoire**: Limites strictes pour éviter l'OOM
- **Réseau**: Keepalive et compression activés
- **Stockage**: Volumes persistants pour les données critiques

### Scalabilité

- **Services principaux**: Répliques configurables
- **Load balancing**: Nginx avec health checks
- **Placement**: Contraintes de nœuds pour optimiser les performances
- **Mise à jour**: Rolling updates avec rollback automatique

### Sécurité

- **Secrets**: Gestion sécurisée des clés API
- **Réseau**: Isolation des services backend/frontend
- **Rate limiting**: Protection contre les abus
- **Health checks**: Surveillance continue de la santé

## Maintenance

### Logs

```bash
# Logs du service principal
docker service logs -f cryptospreadedge-portfolio_cryptospreadedge-main

# Logs du rebalancer
docker service logs -f cryptospreadedge-portfolio_portfolio-rebalancer

# Logs de tous les services
docker service logs cryptospreadedge-portfolio
```

### Mise à jour

```bash
# Mise à jour de l'image
docker build -t cryptospreadedge:latest .
docker service update --image cryptospreadedge:latest cryptospreadedge-portfolio_cryptospreadedge-main

# Mise à jour du stack complet
docker stack deploy -c infrastructure/docker/swarm/docker-stack-portfolio-optimized.yml cryptospreadedge-portfolio
```

### Sauvegarde

```bash
# Sauvegarde des volumes
docker run --rm -v cryptospreadedge-portfolio_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .

# Sauvegarde des configs
docker config ls -q | xargs -I {} docker config inspect {} > configs-backup.json
```

## Dépannage

### Problèmes Courants

1. **Service ne démarre pas**
   - Vérifier les secrets et configs
   - Consulter les logs du service
   - Vérifier les contraintes de placement

2. **Métriques non disponibles**
   - Vérifier que le port 9001 est accessible
   - Consulter les logs de Prometheus
   - Vérifier la configuration de scraping

3. **Rebalance ne fonctionne pas**
   - Vérifier les variables d'environnement
   - Consulter les logs du rebalancer
   - Vérifier la connectivité aux exchanges

### Commandes Utiles

```bash
# Statut des services
docker service ls

# Détails d'un service
docker service inspect cryptospreadedge-portfolio_cryptospreadedge-main

# Tâches d'un service
docker service ps cryptospreadedge-portfolio_cryptospreadedge-main

# Logs en temps réel
docker service logs -f cryptospreadedge-portfolio_cryptospreadedge-main

# Redémarrer un service
docker service update --force cryptospreadedge-portfolio_cryptospreadedge-main
```

Cette configuration optimisée permet un déploiement robuste et scalable du système de rebalance de portefeuille multi-plateformes sur Docker Swarm.