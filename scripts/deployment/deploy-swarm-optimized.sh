#!/usr/bin/env bash
set -euo pipefail

STACK_NAME=${STACK_NAME:-cryptospreadedge}
STACK_FILE=infrastructure/docker/swarm/docker-stack-optimized.yml

echo "[+] Initialisation du cluster si nécessaire"
docker info >/dev/null 2>&1 || { echo "Docker n'est pas disponible"; exit 1; }
if ! docker node ls >/dev/null 2>&1; then
  docker swarm init || true
fi

echo "[+] Création des secrets/configs externes si absents"
docker secret ls | grep -q api_keys_encrypted || docker secret create api_keys_encrypted config/environments/api_keys.encrypted || true
docker secret ls | grep -q arbitrage_env || docker secret create arbitrage_env config/environments/arbitrage.env || true
docker config ls | grep -q nginx_conf || docker config create nginx_conf infrastructure/docker/nginx/nginx.conf || true
docker config ls | grep -q prometheus_conf || docker config create prometheus_conf infrastructure/monitoring/prometheus.yml || true

echo "[+] Déploiement de la stack ${STACK_NAME}"
docker stack deploy -c ${STACK_FILE} ${STACK_NAME}

echo "[+] Services"
docker stack services ${STACK_NAME}

echo "[+] Terminé"

