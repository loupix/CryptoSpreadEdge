# Déploiement Docker Swarm (Optimisé)

## Prérequis

- Docker 24+
- Cluster Swarm initialisé (`docker swarm init`)

## Secrets et Configs

```
docker secret create api_keys_encrypted config/environments/api_keys.encrypted
docker secret create arbitrage_env config/environments/arbitrage.env
docker config create nginx_conf infrastructure/docker/nginx/nginx.conf
docker config create prometheus_conf infrastructure/monitoring/prometheus.yml
```

## Déploiement

```
bash scripts/deployment/deploy-swarm-optimized.sh
```

La stack utilisée: `infrastructure/docker/swarm/docker-stack-optimized.yml`

- réseaux overlay `frontend` et `backend`
- ressources et `restart_policy` adaptées
- `healthcheck` de base
- services séparés: `cryptospreadedge` (workers), `arbitrage-worker` (scalable), monitoring (Prometheus/Grafana), Kafka/Redis

## Vérification

```
docker stack services cryptospreadedge
docker service ls
docker service ps cryptospreadedge_cryptospreadedge
```

## Mise à jour

```
docker service update --image cryptospreadedge:latest cryptospreadedge_cryptospreadedge
```

## Suppression

```
docker stack rm cryptospreadedge
```