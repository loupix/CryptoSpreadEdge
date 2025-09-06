#!/bin/bash

# Script de déploiement complet du cluster CryptoSpreadEdge
# Inclut le système de trading + monitoring + observabilité

set -e

# Configuration
STACK_NAME="cryptospreadedge"
MONITORING_STACK="cryptospreadedge-monitoring"
TRADING_COMPOSE="infrastructure/docker/swarm/docker-stack-optimized.yml"
MONITORING_COMPOSE="infrastructure/monitoring/docker-compose.monitoring.yml"
NETWORK_NAME="cryptospreadedge-network"
REGISTRY_URL="your-registry.com"
VERSION="latest"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_monitoring() {
    echo -e "${PURPLE}[MONITORING]${NC} $1"
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
    
    # Vérifier les fichiers compose
    if [ ! -f "$TRADING_COMPOSE" ]; then
        log_error "Fichier trading compose non trouvé: $TRADING_COMPOSE"
        exit 1
    fi
    
    if [ ! -f "$MONITORING_COMPOSE" ]; then
        log_error "Fichier monitoring compose non trouvé: $MONITORING_COMPOSE"
        exit 1
    fi
    
    # Vérifier jq pour le parsing JSON
    if ! command -v jq &> /dev/null; then
        log_warning "jq n'est pas installé, certaines fonctionnalités seront limitées"
    fi
    
    log_success "Prérequis vérifiés"
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
            docker node update --label-add monitoring=true $node_id
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

# Créer les réseaux
create_networks() {
    log_info "Création des réseaux..."
    
    # Réseau principal
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
    
    # Réseau de monitoring
    if ! docker network ls | grep -q "monitoring-network"; then
        docker network create \
            --driver overlay \
            --attachable \
            --subnet=10.1.0.0/16 \
            "monitoring-network"
        log_success "Réseau monitoring-network créé"
    else
        log_info "Réseau monitoring-network existe déjà"
    fi
}

# Déployer le système de trading
deploy_trading_system() {
    log_info "Déploiement du système de trading..."
    
    # Déployer le stack principal
    docker stack deploy -c "$TRADING_COMPOSE" "$STACK_NAME"
    
    log_success "Système de trading déployé"
}

# Déployer le système de monitoring
deploy_monitoring_system() {
    log_monitoring "Déploiement du système de monitoring..."
    
    # Déployer le stack de monitoring
    docker stack deploy -c "$MONITORING_COMPOSE" "$MONITORING_STACK"
    
    log_success "Système de monitoring déployé"
}

# Attendre que les services soient prêts
wait_for_services() {
    log_info "Attente que les services soient prêts..."
    
    # Services critiques du trading
    TRADING_SERVICES=("api-gateway" "market-data-service" "indicators-service" "prediction-service")
    
    for service in "${TRADING_SERVICES[@]}"; do
        log_info "Attente du service $service..."
        
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
    
    # Services de monitoring
    MONITORING_SERVICES=("prometheus" "grafana" "node-exporter")
    
    for service in "${MONITORING_SERVICES[@]}"; do
        log_monitoring "Attente du service $service..."
        
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
            log_warning "Timeout en attendant le service $service"
        fi
    done
}

# Configurer Grafana
configure_grafana() {
    log_monitoring "Configuration de Grafana..."
    
    # Attendre que Grafana soit prêt
    sleep 30
    
    # Obtenir l'IP de Grafana
    GRAFANA_IP=$(docker service inspect ${MONITORING_STACK}_grafana --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    
    if [ -z "$GRAFANA_IP" ]; then
        log_warning "Impossible de récupérer l'IP de Grafana"
        return
    fi
    
    # Attendre que Grafana soit accessible
    timeout=120
    while [ $timeout -gt 0 ]; do
        if curl -f "http://$GRAFANA_IP:3000/api/health" > /dev/null 2>&1; then
            log_success "Grafana est accessible"
            break
        fi
        
        sleep 5
        timeout=$((timeout - 5))
    done
    
    if [ $timeout -le 0 ]; then
        log_warning "Grafana n'est pas accessible"
        return
    fi
    
    # Configurer la source de données Prometheus
    log_monitoring "Configuration de la source de données Prometheus..."
    
    PROMETHEUS_IP=$(docker service inspect ${MONITORING_STACK}_prometheus --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    
    # Créer la source de données
    curl -X POST "http://$GRAFANA_IP:3000/api/datasources" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"Prometheus\",
            \"type\": \"prometheus\",
            \"url\": \"http://$PROMETHEUS_IP:9090\",
            \"access\": \"proxy\",
            \"isDefault\": true
        }" \
        -u admin:admin123 > /dev/null 2>&1 || log_warning "Impossible de configurer la source de données Prometheus"
    
    log_success "Grafana configuré"
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
    
    # Vérifier Prometheus
    PROMETHEUS_IP=$(docker service inspect ${MONITORING_STACK}_prometheus --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    
    if curl -f "http://$PROMETHEUS_IP:9090/-/healthy" > /dev/null 2>&1; then
        log_success "Prometheus est sain"
    else
        log_warning "Prometheus n'est pas accessible"
    fi
    
    # Vérifier Grafana
    GRAFANA_IP=$(docker service inspect ${MONITORING_STACK}_grafana --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    
    if curl -f "http://$GRAFANA_IP:3000/api/health" > /dev/null 2>&1; then
        log_success "Grafana est sain"
    else
        log_warning "Grafana n'est pas accessible"
    fi
}

# Afficher les informations de déploiement
show_deployment_info() {
    log_info "Informations de déploiement:"
    
    echo ""
    echo "=========================================="
    echo "  CRYPTOSPREADEDGE CLUSTER COMPLET"
    echo "=========================================="
    echo ""
    echo "Stack de trading: $STACK_NAME"
    echo "Stack de monitoring: $MONITORING_STACK"
    echo "Réseau principal: $NETWORK_NAME"
    echo "Réseau de monitoring: monitoring-network"
    echo "Registry: $REGISTRY_URL"
    echo "Version: $VERSION"
    echo ""
    
    # Afficher les services de trading
    echo "Services de trading:"
    docker service ls --filter "name=${STACK_NAME}_" --format "table {{.NAME}}\t{{.REPLICAS}}\t{{.IMAGE}}\t{{.PORTS}}"
    echo ""
    
    # Afficher les services de monitoring
    echo "Services de monitoring:"
    docker service ls --filter "name=${MONITORING_STACK}_" --format "table {{.NAME}}\t{{.REPLICAS}}\t{{.IMAGE}}\t{{.PORTS}}"
    echo ""
    
    # Afficher les nœuds
    echo "Nœuds du cluster:"
    docker node ls --format "table {{.ID}}\t{{.HOSTNAME}}\t{{.STATUS}}\t{{.AVAILABILITY}}\t{{.MANAGER STATUS}}"
    echo ""
    
    # Afficher les URLs d'accès
    GATEWAY_IP=$(docker service inspect ${STACK_NAME}_api-gateway --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    PROMETHEUS_IP=$(docker service inspect ${MONITORING_STACK}_prometheus --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    GRAFANA_IP=$(docker service inspect ${MONITORING_STACK}_grafana --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    
    echo "URLs d'accès:"
    echo "  API Gateway: http://$GATEWAY_IP"
    echo "  Health check: http://$GATEWAY_IP/health"
    echo "  Métriques: http://$GATEWAY_IP/metrics"
    echo ""
    echo "  Prometheus: http://$PROMETHEUS_IP:9090"
    echo "  Grafana: http://$GRAFANA_IP:3000 (admin/admin123)"
    echo "  Jaeger: http://$GRAFANA_IP:16686"
    echo "  Kibana: http://$GRAFANA_IP:5601"
    echo ""
    
    echo "=========================================="
}

# Fonction principale
main() {
    log_info "Démarrage du déploiement complet CryptoSpreadEdge"
    
    # Vérifier les prérequis
    check_prerequisites
    
    # Configurer les labels des nœuds
    configure_node_labels
    
    # Créer les réseaux
    create_networks
    
    # Déployer le système de trading
    deploy_trading_system
    
    # Déployer le système de monitoring
    deploy_monitoring_system
    
    # Attendre que les services soient prêts
    wait_for_services
    
    # Configurer Grafana
    configure_grafana
    
    # Vérifier la santé
    check_health
    
    # Afficher les informations
    show_deployment_info
    
    log_success "Déploiement complet terminé avec succès!"
    log_info "Le cluster CryptoSpreadEdge est maintenant opérationnel avec monitoring complet"
}

# Gestion des arguments
case "${1:-}" in
    --help)
        echo "Usage: $0 [--help]"
        echo ""
        echo "Ce script déploie le cluster CryptoSpreadEdge complet avec:"
        echo "  - Système de trading haute fréquence"
        echo "  - Monitoring avec Prometheus et Grafana"
        echo "  - Observabilité avec Jaeger et ELK Stack"
        echo "  - Alerting avec Alertmanager"
        echo ""
        echo "Prérequis:"
        echo "  - Docker et Docker Swarm"
        echo "  - jq (optionnel)"
        echo "  - curl"
        echo ""
        echo "Exemples:"
        echo "  $0                # Déployer le cluster complet"
        echo "  $0 --help         # Afficher cette aide"
        ;;
    *)
        main
        ;;
esac