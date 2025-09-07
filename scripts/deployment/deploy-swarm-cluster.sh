#!/bin/bash

# Script de déploiement pour Docker Swarm Cluster
# CryptoSpreadEdge - Système de trading haute fréquence

set -e

# Configuration
STACK_NAME="cryptospreadedge"
COMPOSE_FILE="infrastructure/docker/swarm/docker-stack-optimized.yml"
NETWORK_NAME="cryptospreadedge-network"
REGISTRY_URL="your-registry.com"
VERSION="latest"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier les prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    # Vérifier Docker Swarm
    if ! docker info | grep -q "Swarm: active"; then
        log_warning "Docker Swarm n'est pas initialisé"
        log_info "Initialisation de Docker Swarm..."
        docker swarm init
    fi
    
    # Vérifier le fichier compose
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Fichier compose non trouvé: $COMPOSE_FILE"
        exit 1
    fi
    
    log_success "Prérequis vérifiés"
}

# Construire les images
build_images() {
    log_info "Construction des images Docker..."
    
    # Images à construire
    SERVICES=("market-data" "indicators" "prediction" "signals" "positions" "arbitrage" "backtesting" "api-gateway" "monitoring" "config")
    
    for service in "${SERVICES[@]}"; do
        log_info "Construction de l'image $service..."
        
        # Construire l'image
        docker build -t "$REGISTRY_URL/cryptospreadedge-$service:$VERSION" \
            -f "infrastructure/docker/services/$service/Dockerfile" .
        
        # Pousser vers le registry
        log_info "Push de l'image $service vers le registry..."
        docker push "$REGISTRY_URL/cryptospreadedge-$service:$VERSION"
        
        log_success "Image $service construite et poussée"
    done
}

# Créer le réseau
create_network() {
    log_info "Création du réseau Docker..."
    
    # Vérifier si le réseau existe
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        docker network create \
            --driver overlay \
            --attachable \
            --subnet=10.0.0.0/16 \
            "$NETWORK_NAME"
        log_success "Réseau $NETWORK_NAME créé"
    else
        log_info "Réseau $NETWORK_NAME existe déjà"
    fi
}

# Déployer le stack
deploy_stack() {
    log_info "Déploiement du stack $STACK_NAME..."
    
    # Déployer le stack
    docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME"
    
    log_success "Stack $STACK_NAME déployé"
}

# Attendre que les services soient prêts
wait_for_services() {
    log_info "Attente que les services soient prêts..."
    
    # Services critiques
    CRITICAL_SERVICES=("api-gateway" "market-data-service" "indicators-service" "prediction-service")
    
    for service in "${CRITICAL_SERVICES[@]}"; do
        log_info "Attente du service $service..."
        
        # Attendre que le service soit running
        timeout=300  # 5 minutes
        while [ $timeout -gt 0 ]; do
            if docker service ls | grep -q "$service.*Running"; then
                log_success "Service $service est prêt"
                break
            fi
            
            sleep 10
            timeout=$((timeout - 10))
        done
        
        if [ $timeout -le 0 ]; then
            log_error "Timeout en attendant le service $service"
            exit 1
        fi
    done
}

# Vérifier la santé des services
check_health() {
    log_info "Vérification de la santé des services..."
    
    # Attendre un peu pour que les services se stabilisent
    sleep 30
    
    # Vérifier l'API Gateway
    GATEWAY_IP=$(docker service inspect ${STACK_NAME}_api-gateway --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    
    if curl -f "http://$GATEWAY_IP/health" > /dev/null 2>&1; then
        log_success "API Gateway est sain"
    else
        log_warning "API Gateway n'est pas accessible"
    fi
    
    # Afficher le statut des services
    log_info "Statut des services:"
    docker service ls
}

# Configurer les labels des nœuds
configure_node_labels() {
    log_info "Configuration des labels des nœuds..."
    
    # Obtenir la liste des nœuds
    NODES=$(docker node ls --format "{{.ID}}")
    
    for node_id in $NODES; do
        # Vérifier le rôle du nœud
        ROLE=$(docker node inspect $node_id --format '{{.Spec.Role}}')
        
        if [ "$ROLE" = "manager" ]; then
            # Labels pour les nœuds manager
            docker node update --label-add performance=high $node_id
            docker node update --label-add latency=low $node_id
            log_info "Labels configurés pour le nœud manager $node_id"
        else
            # Labels pour les nœuds worker
            docker node update --label-add performance=medium $node_id
            docker node update --label-add latency=medium $node_id
            
            # Vérifier si le nœud a une GPU
            if nvidia-smi > /dev/null 2>&1; then
                docker node update --label-add gpu=true $node_id
                log_info "GPU détecté sur le nœud worker $node_id"
            fi
            
            log_info "Labels configurés pour le nœud worker $node_id"
        fi
    done
}

# Afficher les informations de déploiement
show_deployment_info() {
    log_info "Informations de déploiement:"
    
    echo ""
    echo "=========================================="
    echo "  CRYPTOSPREADEDGE CLUSTER DÉPLOYÉ"
    echo "=========================================="
    echo ""
    echo "Stack: $STACK_NAME"
    echo "Réseau: $NETWORK_NAME"
    echo "Registry: $REGISTRY_URL"
    echo "Version: $VERSION"
    echo ""
    
    # Afficher les services
    echo "Services déployés:"
    docker service ls --format "table {{.NAME}}\t{{.REPLICAS}}\t{{.IMAGE}}\t{{.PORTS}}"
    
    echo ""
    
    # Afficher les nœuds
    echo "Nœuds du cluster:"
    docker node ls --format "table {{.ID}}\t{{.HOSTNAME}}\t{{.STATUS}}\t{{.AVAILABILITY}}\t{{.MANAGER STATUS}}"
    
    echo ""
    
    # Afficher l'URL d'accès
    GATEWAY_IP=$(docker service inspect ${STACK_NAME}_api-gateway --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    echo "URL d'accès: http://$GATEWAY_IP"
    echo "Health check: http://$GATEWAY_IP/health"
    echo "Métriques: http://$GATEWAY_IP/metrics"
    
    echo ""
    echo "=========================================="
}

# Fonction principale
main() {
    log_info "Démarrage du déploiement CryptoSpreadEdge"
    
    # Vérifier les prérequis
    check_prerequisites
    
    # Configurer les labels des nœuds
    configure_node_labels
    
    # Créer le réseau
    create_network
    
    # Construire les images (optionnel)
    if [ "$1" = "--build" ]; then
        build_images
    fi
    
    # Déployer le stack
    deploy_stack
    
    # Attendre que les services soient prêts
    wait_for_services
    
    # Vérifier la santé
    check_health
    
    # Afficher les informations
    show_deployment_info
    
    log_success "Déploiement terminé avec succès!"
}

# Gestion des arguments
case "${1:-}" in
    --build)
        main --build
        ;;
    --help)
        echo "Usage: $0 [--build] [--help]"
        echo ""
        echo "Options:"
        echo "  --build    Construire et pousser les images Docker"
        echo "  --help     Afficher cette aide"
        echo ""
        echo "Exemples:"
        echo "  $0                # Déployer avec les images existantes"
        echo "  $0 --build        # Construire et déployer"
        ;;
    *)
        main
        ;;
esac