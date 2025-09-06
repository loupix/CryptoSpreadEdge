#!/bin/bash

# Script de setup conda pour CryptoSpreadEdge

set -e

echo "🐍 Configuration de l'environnement conda pour CryptoSpreadEdge..."

# Vérifier si conda est installé
if ! command -v conda &> /dev/null; then
    echo "❌ Conda n'est pas installé. Veuillez installer Miniconda ou Anaconda."
    echo "📥 Téléchargez depuis: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✅ Conda détecté: $(conda --version)"

# Vérifier si l'environnement existe déjà
if conda env list | grep -q "cryptospreadedge"; then
    echo "⚠️  L'environnement 'cryptospreadedge' existe déjà."
    read -p "Voulez-vous le supprimer et le recréer ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Suppression de l'environnement existant..."
        conda env remove -n cryptospreadedge -y
    else
        echo "ℹ️  Utilisation de l'environnement existant."
        echo "🔄 Activation de l'environnement..."
        conda activate cryptospreadedge
        echo "✅ Environnement activé !"
        exit 0
    fi
fi

# Créer l'environnement conda
echo "🚀 Création de l'environnement conda..."
conda env create -f environment.yml

# Activer l'environnement
echo "🔄 Activation de l'environnement..."
conda activate cryptospreadedge

# Vérifier l'installation
echo "🔍 Vérification de l'installation..."
python --version
pip list | grep -E "(fastapi|ccxt|pandas|torch|tensorflow)"

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

echo "✅ Setup conda terminé avec succès!"
echo ""
echo "📋 Pour utiliser l'environnement:"
echo "1. conda activate cryptospreadedge"
echo "2. python -m src.main"
echo ""
echo "📋 Pour désactiver l'environnement:"
echo "conda deactivate"
echo ""
echo "📋 Pour supprimer l'environnement:"
echo "conda env remove -n cryptospreadedge"