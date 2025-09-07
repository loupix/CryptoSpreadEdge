#!/bin/bash

# Script de déploiement optimisé pour le rebalance de portefeuille multi-plateformes
# Usage: ./deploy-portfolio-swarm.sh [environment] [action]

set -e

ENVIRONMENT=${1:-production}
ACTION=${2:-deploy}

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier que Docker Swarm est initialisé
check_swarm() {
    log "Vérification de l'état du Docker Swarm..."
    if ! docker node ls > /dev/null 2>&1; then
        error "Docker Swarm n'est pas initialisé. Exécutez: docker swarm init"
        exit 1
    fi
    success "Docker Swarm est actif"
}

# Créer les secrets nécessaires
create_secrets() {
    log "Création des secrets Docker Swarm..."
    
    # Vérifier si les secrets existent déjà
    if ! docker secret ls | grep -q "api_keys_encrypted"; then
        if [ -f "config/api_keys.encrypted" ]; then
            docker secret create api_keys_encrypted config/api_keys.encrypted
            success "Secret api_keys_encrypted créé"
        else
            warning "Fichier config/api_keys.encrypted non trouvé, création d'un secret vide"
            echo "placeholder" | docker secret create api_keys_encrypted -
        fi
    fi
    
    if ! docker secret ls | grep -q "arbitrage_env"; then
        if [ -f "config/environments/arbitrage.env" ]; then
            docker secret create arbitrage_env config/environments/arbitrage.env
            success "Secret arbitrage_env créé"
        else
            warning "Fichier arbitrage.env non trouvé, création d'un secret vide"
            echo "placeholder" | docker secret create arbitrage_env -
        fi
    fi
    
    if ! docker secret ls | grep -q "rebalance_env"; then
        if [ -f "config/environments/rebalance.env" ]; then
            docker secret create rebalance_env config/environments/rebalance.env
            success "Secret rebalance_env créé"
        else
            warning "Fichier rebalance.env non trouvé, création d'un secret vide"
            echo "placeholder" | docker secret create rebalance_env -
        fi
    fi
}

# Créer les configs nécessaires
create_configs() {
    log "Création des configs Docker Swarm..."
    
    # Config Nginx
    if ! docker config ls | grep -q "nginx_conf"; then
        if [ -f "infrastructure/nginx/nginx.conf" ]; then
            docker config create nginx_conf infrastructure/nginx/nginx.conf
            success "Config nginx_conf créée"
        else
            warning "Fichier nginx.conf non trouvé, création d'une config par défaut"
            echo "events { worker_connections 1024; } http { upstream app { server cryptospreadedge-main:8000; } server { listen 80; location / { proxy_pass http://app; } } }" | docker config create nginx_conf -
        fi
    fi
    
    # Config Prometheus
    if ! docker config ls | grep -q "prometheus_conf"; then
        if [ -f "infrastructure/monitoring/prometheus-portfolio.yml" ]; then
            docker config create prometheus_conf infrastructure/monitoring/prometheus-portfolio.yml
            success "Config prometheus_conf créée"
        else
            warning "Fichier prometheus-portfolio.yml non trouvé, utilisation de la config par défaut"
            docker config create prometheus_conf infrastructure/monitoring/prometheus.yml
        fi
    fi
    
    # Config Grafana dashboards
    if ! docker config ls | grep -q "grafana_dashboards"; then
        if [ -f "infrastructure/monitoring/grafana-dashboards-portfolio.json" ]; then
            docker config create grafana_dashboards infrastructure/monitoring/grafana-dashboards-portfolio.json
            success "Config grafana_dashboards créée"
        else
            warning "Fichier grafana-dashboards-portfolio.json non trouvé, création d'une config vide"
            echo "{}" | docker config create grafana_dashboards -
        fi
    fi
}

# Créer les volumes persistants
create_volumes() {
    log "Création des volumes persistants..."
    
    # Créer les répertoires sur les nœuds
    docker service create --name volume-setup --mode global --mount type=bind,source=/var/lib/cryptospreadedge,target=/app --restart-condition none alpine:latest sh -c "
        mkdir -p /app/data /app/logs /app/portfolio
        chmod 755 /app/data /app/logs /app/portfolio
    " || true
    
    # Attendre que le service se termine
    sleep 5
    
    # Supprimer le service temporaire
    docker service rm volume-setup || true
    
    success "Volumes persistants créés"
}

# Construire l'image Docker
build_image() {
    log "Construction de l'image Docker..."
    docker build -t cryptospreadedge:latest -f infrastructure/docker/services/cryptospreadedge/Dockerfile .
    success "Image Docker construite"
}

# Déployer le stack
deploy_stack() {
    log "Déploiement du stack Docker Swarm..."
    
    # Choisir le fichier de stack selon l'environnement
    STACK_FILE="infrastructure/docker/swarm/docker-stack-portfolio-optimized.yml"
    
    if [ ! -f "$STACK_FILE" ]; then
        error "Fichier de stack non trouvé: $STACK_FILE"
        exit 1
    fi
    
    # Déployer le stack
    docker stack deploy -c "$STACK_FILE" cryptospreadedge-portfolio
    
    success "Stack déployé: cryptospreadedge-portfolio"
}

# Vérifier le statut du déploiement
check_status() {
    log "Vérification du statut du déploiement..."
    
    echo "=== Services ==="
    docker service ls --filter name=cryptospreadedge-portfolio
    
    echo ""
    echo "=== Tâches ==="
    docker service ps cryptospreadedge-portfolio_cryptospreadedge-main --no-trunc
    
    echo ""
    echo "=== Logs (dernières 10 lignes) ==="
    docker service logs --tail 10 cryptospreadedge-portfolio_cryptospreadedge-main || true
}

# Nettoyer le déploiement
cleanup() {
    log "Nettoyage du déploiement..."
    
    # Supprimer le stack
    docker stack rm cryptospreadedge-portfolio
    
    # Attendre que les services se terminent
    sleep 10
    
    success "Déploiement nettoyé"
}

# Fonction principale
main() {
    log "Déploiement du système de rebalance de portefeuille multi-plateformes"
    log "Environnement: $ENVIRONMENT"
    log "Action: $ACTION"
    
    case $ACTION in
        "deploy")
            check_swarm
            create_secrets
            create_configs
            create_volumes
            build_image
            deploy_stack
            sleep 30
            check_status
            ;;
        "status")
            check_status
            ;;
        "cleanup")
            cleanup
            ;;
        "logs")
            docker service logs -f cryptospreadedge-portfolio_cryptospreadedge-main
            ;;
        *)
            echo "Usage: $0 [environment] [action]"
            echo "Actions disponibles: deploy, status, cleanup, logs"
            exit 1
            ;;
    esac
}

# Exécuter la fonction principale
main "$@"