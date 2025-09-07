#!/bin/bash

# Script de démarrage du système d'arbitrage CryptoSpreadEdge

echo "🚀 CryptoSpreadEdge - Système d'Arbitrage"
echo "=========================================="

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "src/main.py" ]; then
    echo "❌ Veuillez exécuter ce script depuis la racine du projet CryptoSpreadEdge"
    exit 1
fi

# Créer le répertoire de logs s'il n'existe pas
mkdir -p logs

# Fonction d'aide
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  validate    Valider le système"
    echo "  test        Lancer les tests"
    echo "  demo        Démonstration interactive"
    echo "  quick       Démarrage rapide (2 minutes)"
    echo "  start       Démarrage complet"
    echo "  main        Application complète"
    echo "  help        Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 validate    # Valider le système"
    echo "  $0 demo        # Voir la démonstration"
    echo "  $0 quick       # Test rapide"
    echo "  $0 start       # Démarrage complet"
}

# Fonction de validation
validate_system() {
    echo "🔍 Validation du système..."
    python3 scripts/validate_system.py
}

# Fonction de test
test_system() {
    echo "🧪 Tests du système d'arbitrage..."
    python3 scripts/arbitrage/test_arbitrage_system.py
}

# Fonction de démonstration
demo_system() {
    echo "🎯 Démonstration du système d'arbitrage..."
    python3 scripts/arbitrage/demo_arbitrage.py
}

# Fonction de démarrage rapide
quick_start() {
    echo "⚡ Démarrage rapide (2 minutes)..."
    python3 scripts/arbitrage/quick_start.py
}

# Fonction de démarrage complet
start_arbitrage() {
    echo "🚀 Démarrage du système d'arbitrage..."
    python3 scripts/arbitrage/start_arbitrage.py
}

# Fonction d'application complète
start_main() {
    echo "🎯 Démarrage de l'application complète..."
    python3 start.py run dev
}

# Traitement des arguments
case "${1:-help}" in
    validate)
        validate_system
        ;;
    test)
        test_system
        ;;
    demo)
        demo_system
        ;;
    quick)
        quick_start
        ;;
    start)
        start_arbitrage
        ;;
    main)
        start_main
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Option inconnue: $1"
        echo ""
        show_help
        exit 1
        ;;
esac