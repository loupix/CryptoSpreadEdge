#!/bin/bash

# Script de gestion du cluster Docker Swarm
# CryptoSpreadEdge - Monitoring et maintenance

set -e

# Configuration
STACK_NAME="cryptospreadedge"
NETWORK_NAME="cryptospreadedge-network"

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

# Afficher le statut du cluster
show_status() {
    log_info "Statut du cluster CryptoSpreadEdge"
    echo ""
    echo "=========================================="
    echo "  STATUT DU CLUSTER"
    echo "=========================================="
    echo ""
    
    # Statut des nœuds
    echo "Nœuds du cluster:"
    docker node ls --format "table {{.ID}}\t{{.HOSTNAME}}\t{{.STATUS}}\t{{.AVAILABILITY}}\t{{.MANAGER STATUS}}"
    echo ""
    
    # Statut des services
    echo "Services déployés:"
    docker service ls --format "table {{.NAME}}\t{{.REPLICAS}}\t{{.IMAGE}}\t{{.PORTS}}"
    echo ""
    
    # Utilisation des ressources
    echo "Utilisation des ressources:"
    docker system df
    echo ""
    
    # Réseaux
    echo "Réseaux:"
    docker network ls | grep "$NETWORK_NAME"
    echo ""
    
    echo "=========================================="
}

# Vérifier la santé des services
check_health() {
    log_info "Vérification de la santé des services..."
    
    # Obtenir l'IP du gateway
    GATEWAY_IP=$(docker service inspect ${STACK_NAME}_api-gateway --format '{{.Endpoint.VirtualIPs[0].Addr}}' | cut -d'/' -f1)
    
    if [ -z "$GATEWAY_IP" ]; then
        log_error "Impossible de récupérer l'IP du gateway"
        return 1
    fi
    
    echo ""
    echo "=========================================="
    echo "  VÉRIFICATION DE SANTÉ"
    echo "=========================================="
    echo ""
    
    # Vérifier l'API Gateway
    log_info "Vérification de l'API Gateway..."
    if curl -f "http://$GATEWAY_IP/health" > /dev/null 2>&1; then
        log_success "API Gateway: OK"
        
        # Afficher les détails de santé
        echo "Détails de santé:"
        curl -s "http://$GATEWAY_IP/health" | jq '.' 2>/dev/null || curl -s "http://$GATEWAY_IP/health"
    else
        log_error "API Gateway: ERREUR"
    fi
    
    echo ""
    
    # Vérifier les métriques
    log_info "Métriques du système:"
    if curl -f "http://$GATEWAY_IP/metrics" > /dev/null 2>&1; then
        echo "Métriques disponibles:"
        curl -s "http://$GATEWAY_IP/metrics" | jq '.' 2>/dev/null || curl -s "http://$GATEWAY_IP/metrics"
    else
        log_warning "Métriques non disponibles"
    fi
    
    echo ""
    echo "=========================================="
}

# Redémarrer un service
restart_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        log_error "Nom du service requis"
        return 1
    fi
    
    log_info "Redémarrage du service $service_name..."
    
    # Vérifier si le service existe
    if ! docker service ls | grep -q "$service_name"; then
        log_error "Service $service_name non trouvé"
        return 1
    fi
    
    # Redémarrer le service
    docker service update --force "$service_name"
    
    log_success "Service $service_name redémarré"
}

# Mettre à l'échelle un service
scale_service() {
    local service_name="$1"
    local replicas="$2"
    
    if [ -z "$service_name" ] || [ -z "$replicas" ]; then
        log_error "Nom du service et nombre de répliques requis"
        return 1
    fi
    
    log_info "Mise à l'échelle du service $service_name à $replicas répliques..."
    
    # Vérifier si le service existe
    if ! docker service ls | grep -q "$service_name"; then
        log_error "Service $service_name non trouvé"
        return 1
    fi
    
    # Mettre à l'échelle
    docker service scale "$service_name=$replicas"
    
    log_success "Service $service_name mis à l'échelle à $replicas répliques"
}

# Nettoyer le système
cleanup_system() {
    log_info "Nettoyage du système..."
    
    # Nettoyer les images inutilisées
    log_info "Suppression des images inutilisées..."
    docker image prune -f
    
    # Nettoyer les volumes inutilisés
    log_info "Suppression des volumes inutilisés..."
    docker volume prune -f
    
    # Nettoyer les réseaux inutilisés
    log_info "Suppression des réseaux inutilisés..."
    docker network prune -f
    
    # Nettoyer le système
    log_info "Nettoyage général du système..."
    docker system prune -f
    
    log_success "Nettoyage terminé"
}

# Sauvegarder la configuration
backup_config() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "Sauvegarde de la configuration vers $backup_dir..."
    
    # Créer le répertoire de sauvegarde
    mkdir -p "$backup_dir"
    
    # Sauvegarder la configuration du stack
    docker stack config "$STACK_NAME" > "$backup_dir/stack-config.yml" 2>/dev/null || true
    
    # Sauvegarder la configuration des services
    docker service ls --format "{{.Name}}" | while read service; do
        docker service inspect "$service" > "$backup_dir/${service}-inspect.json"
    done
    
    # Sauvegarder la configuration des nœuds
    docker node ls --format "{{.ID}}" | while read node; do
        docker node inspect "$node" > "$backup_dir/node-${node}-inspect.json"
    done
    
    # Sauvegarder les logs
    docker service logs --no-task-ids --raw "${STACK_NAME}_api-gateway" > "$backup_dir/api-gateway.log" 2>/dev/null || true
    
    log_success "Sauvegarde terminée dans $backup_dir"
}

# Afficher les logs d'un service
show_logs() {
    local service_name="$1"
    local lines="${2:-100}"
    
    if [ -z "$service_name" ]; then
        log_error "Nom du service requis"
        return 1
    fi
    
    log_info "Affichage des logs du service $service_name (dernières $lines lignes)..."
    
    # Vérifier si le service existe
    if ! docker service ls | grep -q "$service_name"; then
        log_error "Service $service_name non trouvé"
        return 1
    fi
    
    # Afficher les logs
    docker service logs --tail "$lines" --follow "$service_name"
}

# Surveiller les services en temps réel
monitor_services() {
    log_info "Surveillance des services en temps réel..."
    log_info "Appuyez sur Ctrl+C pour arrêter"
    
    while true; do
        clear
        echo "=========================================="
        echo "  SURVEILLANCE TEMPS RÉEL"
        echo "  $(date)"
        echo "=========================================="
        echo ""
        
        # Statut des services
        docker service ls --format "table {{.NAME}}\t{{.REPLICAS}}\t{{.IMAGE}}\t{{.PORTS}}"
        echo ""
        
        # Utilisation des ressources
        echo "Utilisation des ressources:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
        echo ""
        
        # Attendre 5 secondes
        sleep 5
    done
}

# Mettre à jour le stack
update_stack() {
    local compose_file="$1"
    
    if [ -z "$compose_file" ]; then
        log_error "Fichier compose requis"
        return 1
    fi
    
    if [ ! -f "$compose_file" ]; then
        log_error "Fichier compose non trouvé: $compose_file"
        return 1
    fi
    
    log_info "Mise à jour du stack avec $compose_file..."
    
    # Mettre à jour le stack
    docker stack deploy -c "$compose_file" "$STACK_NAME"
    
    log_success "Stack mis à jour"
}

# Arrêter le stack
stop_stack() {
    log_warning "Arrêt du stack $STACK_NAME..."
    
    # Demander confirmation
    read -p "Êtes-vous sûr de vouloir arrêter le stack? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker stack rm "$STACK_NAME"
        log_success "Stack arrêté"
    else
        log_info "Arrêt annulé"
    fi
}

# Afficher l'aide
show_help() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commandes disponibles:"
    echo "  status                    Afficher le statut du cluster"
    echo "  health                    Vérifier la santé des services"
    echo "  restart <service>         Redémarrer un service"
    echo "  scale <service> <replicas> Mettre à l'échelle un service"
    echo "  logs <service> [lines]    Afficher les logs d'un service"
    echo "  monitor                   Surveiller les services en temps réel"
    echo "  cleanup                   Nettoyer le système"
    echo "  backup                    Sauvegarder la configuration"
    echo "  update <compose-file>     Mettre à jour le stack"
    echo "  stop                      Arrêter le stack"
    echo "  help                      Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 status"
    echo "  $0 restart api-gateway"
    echo "  $0 scale indicators-service 5"
    echo "  $0 logs market-data-service 200"
    echo "  $0 monitor"
    echo "  $0 update infrastructure/docker/swarm/docker-stack-optimized.yml"
}

# Fonction principale
main() {
    case "${1:-help}" in
        status)
            show_status
            ;;
        health)
            check_health
            ;;
        restart)
            restart_service "$2"
            ;;
        scale)
            scale_service "$2" "$3"
            ;;
        logs)
            show_logs "$2" "$3"
            ;;
        monitor)
            monitor_services
            ;;
        cleanup)
            cleanup_system
            ;;
        backup)
            backup_config
            ;;
        update)
            update_stack "$2"
            ;;
        stop)
            stop_stack
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Exécuter la fonction principale
main "$@"