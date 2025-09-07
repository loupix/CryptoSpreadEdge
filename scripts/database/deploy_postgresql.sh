#!/bin/bash
# Script de déploiement PostgreSQL pour CryptoSpreadEdge

set -e

echo "🚀 Déploiement de PostgreSQL pour CryptoSpreadEdge..."

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 2. Construire les images
log "Construction des images Docker..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml build

# 3. Démarrer PostgreSQL en premier
log "Démarrage de PostgreSQL..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml up -d postgres

# Attendre que PostgreSQL soit prêt
log "Attente que PostgreSQL soit prêt..."
sleep 10

# Vérifier que PostgreSQL est en cours d'exécution
if ! docker-compose -f infrastructure/docker/compose/docker-compose.yml ps postgres | grep -q "Up"; then
    error "PostgreSQL n'a pas démarré correctement"
    docker-compose -f infrastructure/docker/compose/docker-compose.yml logs postgres
    exit 1
fi

log "PostgreSQL est démarré avec succès!"

# 4. Initialiser la base de données
log "Initialisation de la base de données..."

# Attendre un peu plus pour s'assurer que PostgreSQL est complètement prêt
sleep 5

# Exécuter le script d'initialisation
python scripts/database/init_database.py

if [ $? -eq 0 ]; then
    log "Base de données initialisée avec succès!"
else
    error "Échec de l'initialisation de la base de données"
    exit 1
fi

# 5. Tester la base de données
log "Test de la base de données..."
python scripts/database/test_database.py

if [ $? -eq 0 ]; then
    log "Tests de base de données réussis!"
else
    error "Échec des tests de base de données"
    exit 1
fi

# 6. Démarrer tous les services
log "Démarrage de tous les services..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml up -d

# Attendre que tous les services soient prêts
log "Attente que tous les services soient prêts..."
sleep 15

# 7. Vérifier l'état des services
log "Vérification de l'état des services..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml ps

# 8. Afficher les informations de connexion
log "Informations de connexion:"
echo "PostgreSQL: localhost:5432"
echo "Base de données: cryptospreadedge"
echo "Utilisateur: trading_user"
echo "Mot de passe: secure_password"
echo ""
echo "URL de connexion: postgresql://trading_user:secure_password@localhost:5432/cryptospreadedge"

# 9. Afficher les commandes utiles
log "Commandes utiles:"
echo "Voir les logs PostgreSQL: docker-compose -f infrastructure/docker/compose/docker-compose.yml logs postgres"
echo "Se connecter à PostgreSQL: docker exec -it cryptospreadedge-postgres psql -U trading_user -d cryptospreadedge"
echo "Arrêter les services: docker-compose -f infrastructure/docker/compose/docker-compose.yml down"
echo "Redémarrer les services: docker-compose -f infrastructure/docker/compose/docker-compose.yml restart"

log "✅ Déploiement PostgreSQL terminé avec succès!"

# 10. Optionnel: Exécuter les tests d'intégration
if [ "$1" = "--test" ]; then
    log "Exécution des tests d'intégration..."
    python -m pytest tests/integration/test_postgresql_integration.py -v
fi