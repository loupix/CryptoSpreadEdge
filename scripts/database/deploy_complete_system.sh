#!/bin/bash
# Script de déploiement complet du système de base de données CryptoSpreadEdge

set -e

echo "🚀 Déploiement complet du système de base de données CryptoSpreadEdge..."

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    error "Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier que Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Aller dans le répertoire du projet
cd "$(dirname "$0")/../.."

log "Répertoire de travail: $(pwd)"

# 1. Arrêter les services existants
log "Arrêt des services existants..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml down || true

# 2. Nettoyer les volumes existants (optionnel)
if [ "$1" = "--clean" ]; then
    warn "Nettoyage des volumes existants..."
    docker volume prune -f
fi

# 3. Construire les images
log "Construction des images Docker..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml build --no-cache

# 4. Démarrer PostgreSQL en premier
log "Démarrage de PostgreSQL..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml up -d postgres

# Attendre que PostgreSQL soit prêt
log "Attente que PostgreSQL soit prêt..."
sleep 15

# Vérifier que PostgreSQL est en cours d'exécution
if ! docker-compose -f infrastructure/docker/compose/docker-compose.yml ps postgres | grep -q "Up"; then
    error "PostgreSQL n'a pas démarré correctement"
    docker-compose -f infrastructure/docker/compose/docker-compose.yml logs postgres
    exit 1
fi

log "PostgreSQL est démarré avec succès!"

# 5. Initialiser la base de données
log "Initialisation de la base de données..."

# Attendre un peu plus pour s'assurer que PostgreSQL est complètement prêt
sleep 10

# Exécuter le script d'initialisation
python scripts/database/init_database.py

if [ $? -eq 0 ]; then
    log "Base de données initialisée avec succès!"
else
    error "Échec de l'initialisation de la base de données"
    exit 1
fi

# 6. Tester la base de données
log "Test de la base de données..."
python scripts/database/test_database.py

if [ $? -eq 0 ]; then
    log "Tests de base de données réussis!"
else
    error "Échec des tests de base de données"
    exit 1
fi

# 7. Démarrer tous les services
log "Démarrage de tous les services..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml up -d

# Attendre que tous les services soient prêts
log "Attente que tous les services soient prêts..."
sleep 20

# 8. Vérifier l'état des services
log "Vérification de l'état des services..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml ps

# 9. Tester les APIs
log "Test des APIs..."

# Attendre que l'API soit prête
sleep 10

# Tester l'API de santé
if command -v curl &> /dev/null; then
    log "Test de l'API de santé..."
    curl -f http://localhost:8000/api/v1/historical/health || warn "API de santé non accessible"
    
    log "Test de l'API des ordres..."
    curl -f "http://localhost:8000/api/v1/historical/orders?limit=10" || warn "API des ordres non accessible"
    
    log "Test de l'API des positions..."
    curl -f "http://localhost:8000/api/v1/historical/positions" || warn "API des positions non accessible"
    
    log "Test de l'API des trades..."
    curl -f "http://localhost:8000/api/v1/historical/trades?limit=10" || warn "API des trades non accessible"
else
    warn "curl n'est pas installé, impossible de tester les APIs"
fi

# 10. Exécuter les tests d'intégration
if [ "$1" = "--test" ] || [ "$2" = "--test" ]; then
    log "Exécution des tests d'intégration..."
    python -m pytest tests/integration/test_postgresql_integration.py -v
fi

# 11. Afficher les informations de connexion
log "Informations de connexion:"
echo "PostgreSQL: localhost:5432"
echo "Base de données: cryptospreadedge"
echo "Utilisateur: trading_user"
echo "Mot de passe: secure_password"
echo ""
echo "URL de connexion: postgresql://trading_user:secure_password@localhost:5432/cryptospreadedge"
echo ""
echo "APIs disponibles:"
echo "- Santé: http://localhost:8000/api/v1/historical/health"
echo "- Ordres: http://localhost:8000/api/v1/historical/orders"
echo "- Positions: http://localhost:8000/api/v1/historical/positions"
echo "- Trades: http://localhost:8000/api/v1/historical/trades"
echo "- Portefeuille: http://localhost:8000/api/v1/historical/portfolio"

# 12. Afficher les commandes utiles
log "Commandes utiles:"
echo "Voir les logs PostgreSQL: docker-compose -f infrastructure/docker/compose/docker-compose.yml logs postgres"
echo "Se connecter à PostgreSQL: docker exec -it cryptospreadedge-postgres psql -U trading_user -d cryptospreadedge"
echo "Arrêter les services: docker-compose -f infrastructure/docker/compose/docker-compose.yml down"
echo "Redémarrer les services: docker-compose -f infrastructure/docker/compose/docker-compose.yml restart"
echo "Voir les logs de l'application: docker-compose -f infrastructure/docker/compose/docker-compose.yml logs cryptospreadedge"

# 13. Afficher le statut final
log "Statut final des services:"
docker-compose -f infrastructure/docker/compose/docker-compose.yml ps

# 14. Afficher les métriques de performance
log "Métriques de performance:"
echo "Mémoire utilisée:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep cryptospreadedge || true

echo ""
echo "Espace disque utilisé:"
docker system df

log "✅ Déploiement complet terminé avec succès!"

# 15. Afficher les prochaines étapes
echo ""
echo "🎯 Prochaines étapes:"
echo "1. Configurer les clés API des exchanges dans l'interface"
echo "2. Créer des utilisateurs et des stratégies de trading"
echo "3. Configurer les alertes et notifications"
echo "4. Monitorer les performances via les dashboards"
echo "5. Configurer les sauvegardes automatiques"

echo ""
echo "📚 Documentation:"
echo "- Guide d'utilisation: docs/database/README.md"
echo "- Documentation technique: docs/database/POSTGRESQL_INTEGRATION.md"
echo "- Configuration des plateformes: src/database/platform_config.py"

echo ""
echo "🔧 Maintenance:"
echo "- Sauvegardes: scripts/database/backup_system.py"
echo "- Monitoring: scripts/database/monitoring_system.py"
echo "- Optimisation: scripts/database/performance_optimizer.py"
echo "- Sécurité: scripts/database/security_system.py"