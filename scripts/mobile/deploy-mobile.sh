#!/bin/bash

# Script de déploiement pour l'application mobile CryptoSpreadEdge

set -e

echo "🚀 Déploiement de l'application mobile CryptoSpreadEdge"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "mobile/package.json" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet CryptoSpreadEdge"
    exit 1
fi

# Aller dans le dossier mobile
cd mobile

echo "📱 Préparation de l'application mobile..."

# Installer les dépendances
echo "📦 Installation des dépendances..."
npm install

# Vérifier la configuration
if [ ! -f ".env" ]; then
    echo "⚠️  Fichier .env manquant, copie depuis env.example..."
    cp env.example .env
    echo "📝 Veuillez configurer le fichier .env avec vos paramètres"
fi

# Linter
echo "🔍 Vérification du code..."
npm run lint

# Tests
echo "🧪 Exécution des tests..."
npm test

# Build Android
echo "🤖 Build Android..."
cd android
./gradlew assembleRelease
echo "✅ APK Android généré: android/app/build/outputs/apk/release/app-release.apk"
cd ..

# Build iOS (si sur macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Build iOS..."
    cd ios
    xcodebuild -workspace CryptoSpreadEdgeMobile.xcworkspace \
               -scheme CryptoSpreadEdgeMobile \
               -configuration Release \
               -archivePath CryptoSpreadEdgeMobile.xcarchive \
               archive
    echo "✅ Archive iOS générée: ios/CryptoSpreadEdgeMobile.xcarchive"
    cd ..
else
    echo "⚠️  Build iOS ignoré (nécessite macOS)"
fi

echo "✅ Déploiement mobile terminé avec succès!"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Tester l'APK Android sur un appareil"
echo "2. Uploader l'APK sur Google Play Console"
echo "3. Soumettre l'application iOS sur App Store Connect"
echo "4. Configurer les notifications push"
echo "5. Tester en production"