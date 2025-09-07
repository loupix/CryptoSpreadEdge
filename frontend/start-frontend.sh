#!/bin/bash

# Script de démarrage du frontend CryptoSpreadEdge
# Usage: ./start-frontend.sh [dev|prod|build]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Vérifier si Node.js est installé
check_node() {
    if ! command -v node &> /dev/null; then
        error "Node.js n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    log "Node.js version: $NODE_VERSION"
}

# Vérifier si npm est installé
check_npm() {
    if ! command -v npm &> /dev/null; then
        error "npm n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
    
    NPM_VERSION=$(npm --version)
    log "npm version: $NPM_VERSION"
}

# Installer les dépendances
install_dependencies() {
    log "Installation des dépendances..."
    
    if [ ! -f "package.json" ]; then
        error "package.json non trouvé. Êtes-vous dans le bon répertoire ?"
        exit 1
    fi
    
    npm install
    success "Dépendances installées avec succès"
}

# Vérifier la configuration
check_config() {
    log "Vérification de la configuration..."
    
    if [ ! -f ".env" ]; then
        warning "Fichier .env non trouvé. Copie de env.example..."
        if [ -f "env.example" ]; then
            cp env.example .env
            success "Fichier .env créé à partir de env.example"
        else
            error "Fichier env.example non trouvé"
            exit 1
        fi
    fi
    
    # Vérifier les variables d'environnement critiques
    if ! grep -q "REACT_APP_API_URL" .env; then
        warning "REACT_APP_API_URL non définie dans .env"
    fi
    
    success "Configuration vérifiée"
}

# Démarrer en mode développement
start_dev() {
    log "Démarrage en mode développement..."
    check_node
    check_npm
    install_dependencies
    check_config
    
    log "Lancement du serveur de développement..."
    success "Frontend accessible sur http://localhost:3000"
    npm start
}

# Démarrer en mode production
start_prod() {
    log "Démarrage en mode production..."
    check_node
    check_npm
    install_dependencies
    check_config
    
    log "Build de l'application..."
    npm run build
    
    if [ -d "build" ]; then
        success "Build terminé avec succès"
        log "Lancement du serveur de production..."
        
        # Installer serve si disponible, sinon utiliser npx
        if command -v serve &> /dev/null; then
            serve -s build -l 3000
        else
            npx serve -s build -l 3000
        fi
    else
        error "Échec du build"
        exit 1
    fi
}

# Build uniquement
build_only() {
    log "Build de l'application..."
    check_node
    check_npm
    install_dependencies
    check_config
    
    npm run build
    
    if [ -d "build" ]; then
        success "Build terminé avec succès dans le dossier 'build'"
    else
        error "Échec du build"
        exit 1
    fi
}

# Afficher l'aide
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev     Démarrer en mode développement (défaut)"
    echo "  prod    Démarrer en mode production"
    echo "  build   Build uniquement"
    echo "  help    Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 dev     # Démarrer en mode développement"
    echo "  $0 prod    # Démarrer en mode production"
    echo "  $0 build   # Build uniquement"
}

# Fonction principale
main() {
    local command=${1:-dev}
    
    case $command in
        dev)
            start_dev
            ;;
        prod)
            start_prod
            ;;
        build)
            build_only
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Commande inconnue: $command"
            show_help
            exit 1
            ;;
    esac
}

# Vérifier si on est dans le bon répertoire
if [ ! -f "package.json" ]; then
    error "Ce script doit être exécuté depuis le répertoire frontend/"
    exit 1
fi

# Exécuter la fonction principale
main "$@"