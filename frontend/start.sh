#!/bin/bash

# Script de démarrage pour le frontend CryptoSpreadEdge

echo "🚀 Démarrage du frontend CryptoSpreadEdge..."

# Vérifier si Node.js est installé
if ! command -v node &> /dev/null; then
    echo "❌ Node.js n'est pas installé. Veuillez installer Node.js 18+"
    exit 1
fi

# Vérifier la version de Node.js
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ requis. Version actuelle: $(node -v)"
    exit 1
fi

# Vérifier si npm est installé
if ! command -v npm &> /dev/null; then
    echo "❌ npm n'est pas installé"
    exit 1
fi

# Installer les dépendances si nécessaire
if [ ! -d "node_modules" ]; then
    echo "📦 Installation des dépendances..."
    npm install
fi

# Vérifier les variables d'environnement
if [ ! -f ".env" ]; then
    echo "⚙️  Création du fichier .env..."
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
EOF
    echo "✅ Fichier .env créé avec les valeurs par défaut"
fi

# Démarrer l'application
echo "🎯 Démarrage de l'application React..."
echo "📱 Interface disponible sur: http://localhost:3000"
echo "🔌 API Backend: http://localhost:8000"
echo ""

npm start