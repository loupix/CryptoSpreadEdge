#!/bin/bash

# Script de setup pour CryptoSpreadEdge

set -e

echo "🚀 Configuration de CryptoSpreadEdge..."

# Vérifier les prérequis
echo "📋 Vérification des prérequis..."

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 n'est pas installé"
    exit 1
fi

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

# Vérifier Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

echo "✅ Tous les prérequis sont installés"

# Créer l'environnement virtuel
echo "🐍 Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Créer les répertoires nécessaires
echo "📁 Création des répertoires..."
mkdir -p data/historical
mkdir -p data/models
mkdir -p data/logs
mkdir -p logs

# Copier le fichier de configuration
echo "⚙️ Configuration..."
if [ ! -f config/environments/.env ]; then
    cp config/environments/env.example config/environments/.env
    echo "📝 Fichier .env créé. Veuillez le configurer avec vos clés API."
fi

# Construire l'image Docker
echo "🐳 Construction de l'image Docker..."
docker build -f infrastructure/docker/services/cryptospreadedge/Dockerfile -t cryptospreadedge:latest .

# Démarrer les services de base
echo "🚀 Démarrage des services de base..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml up -d redis influxdb kafka

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 30

# Vérifier le statut des services
echo "🔍 Vérification du statut des services..."
docker-compose -f infrastructure/docker/compose/docker-compose.yml ps

echo "✅ Setup terminé avec succès!"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Configurez vos clés API dans config/environments/.env"
echo "2. Lancez l'application: python -m src.main"
echo "3. Ou utilisez Docker Compose: docker-compose up"
echo ""
echo "🌐 Services disponibles:"
echo "- Application: http://localhost:8000"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000"
echo "- Kibana: http://localhost:5601"