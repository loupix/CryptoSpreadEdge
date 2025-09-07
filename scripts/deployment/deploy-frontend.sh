#!/bin/bash

# Script de déploiement du frontend CryptoSpreadEdge

set -e

echo "🚀 Déploiement du frontend CryptoSpreadEdge..."

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    log_error "Docker n'est pas installé. Veuillez installer Docker."
    exit 1
fi

# Vérifier si Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose n'est pas installé. Veuillez installer Docker Compose."
    exit 1
fi

# Aller dans le répertoire du projet
cd "$(dirname "$0")/../.."

log_info "Répertoire de travail: $(pwd)"

# Vérifier si le dossier frontend existe
if [ ! -d "frontend" ]; then
    log_error "Le dossier frontend n'existe pas."
    exit 1
fi

# Vérifier si package.json existe
if [ ! -f "frontend/package.json" ]; then
    log_error "Le fichier package.json n'existe pas dans le dossier frontend."
    exit 1
fi

log_info "Construction de l'image Docker du frontend..."

# Construire l'image Docker
docker build -f infrastructure/docker/services/frontend/Dockerfile -t cryptospreadedge-frontend:latest .

if [ $? -eq 0 ]; then
    log_success "Image Docker construite avec succès"
else
    log_error "Erreur lors de la construction de l'image Docker"
    exit 1
fi

log_info "Démarrage du conteneur frontend..."

# Arrêter le conteneur existant s'il existe
if [ "$(docker ps -q -f name=cryptospreadedge-frontend)" ]; then
    log_info "Arrêt du conteneur existant..."
    docker stop cryptospreadedge-frontend
fi

# Supprimer le conteneur existant s'il existe
if [ "$(docker ps -aq -f name=cryptospreadedge-frontend)" ]; then
    log_info "Suppression du conteneur existant..."
    docker rm cryptospreadedge-frontend
fi

# Démarrer le nouveau conteneur
docker run -d \
    --name cryptospreadedge-frontend \
    --network cryptospreadedge-network \
    -p 3000:80 \
    --restart unless-stopped \
    cryptospreadedge-frontend:latest

if [ $? -eq 0 ]; then
    log_success "Conteneur frontend démarré avec succès"
else
    log_error "Erreur lors du démarrage du conteneur frontend"
    exit 1
fi

# Attendre que le conteneur soit prêt
log_info "Attente du démarrage du conteneur..."
sleep 10

# Vérifier le statut du conteneur
if [ "$(docker ps -q -f name=cryptospreadedge-frontend)" ]; then
    log_success "Frontend déployé avec succès!"
    log_info "Interface disponible sur: http://localhost:3000"
    log_info "Pour voir les logs: docker logs cryptospreadedge-frontend"
    log_info "Pour arrêter: docker stop cryptospreadedge-frontend"
else
    log_error "Le conteneur frontend n'est pas en cours d'exécution"
    log_info "Logs du conteneur:"
    docker logs cryptospreadedge-frontend
    exit 1
fi

# Afficher les informations de déploiement
echo ""
log_info "=== Informations de déploiement ==="
echo "🌐 Frontend URL: http://localhost:3000"
echo "🐳 Conteneur: cryptospreadedge-frontend"
echo "📊 Statut: $(docker inspect --format='{{.State.Status}}' cryptospreadedge-frontend)"
echo "🔗 Réseau: cryptospreadedge-network"
echo ""

# Vérifier la santé du conteneur
log_info "Vérification de la santé du conteneur..."
if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    log_success "Le frontend répond correctement"
else
    log_warning "Le frontend ne répond pas encore (peut prendre quelques secondes)"
fi

echo ""
log_success "Déploiement du frontend terminé!"