#!/bin/bash
# Installation des hooks Git pour CryptoSpreadEdge

set -e

echo "🔧 Installation des hooks Git pour CryptoSpreadEdge..."

# Vérifier que nous sommes dans un repository Git
if [ ! -d ".git" ]; then
    echo "❌ Ce n'est pas un repository Git"
    exit 1
fi

# Créer le répertoire des hooks s'il n'existe pas
mkdir -p .git/hooks

# Copier les hooks
echo "📋 Copie des hooks..."

# Pre-commit
cp scripts/git/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "✅ Hook pre-commit installé"

# Post-commit
cp scripts/git/hooks/post-commit .git/hooks/post-commit
chmod +x .git/hooks/post-commit
echo "✅ Hook post-commit installé"

# Pre-push
cp scripts/git/hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
echo "✅ Hook pre-push installé"

# Créer un hook de mise à jour automatique
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
# Hook post-merge pour CryptoSpreadEdge

echo "🔄 Mise à jour détectée..."

# Vérifier si les dépendances ont changé
if git diff HEAD@{1} --name-only | grep -q "requirements.txt\|environment.*\.yml"; then
    echo "📦 Dépendances mises à jour détectées"
    echo "💡 Vous devriez mettre à jour votre environnement conda:"
    echo "   conda env update -f environment-dev.yml"
fi

# Vérifier si la configuration a changé
if git diff HEAD@{1} --name-only | grep -q "config/"; then
    echo "⚙️  Configuration mise à jour détectée"
    echo "💡 Vérifiez votre fichier .env"
fi

echo "✅ Mise à jour terminée"
EOF

chmod +x .git/hooks/post-merge
echo "✅ Hook post-merge installé"

# Créer un hook de checkout pour changer d'environnement
cat > .git/hooks/post-checkout << 'EOF'
#!/bin/bash
# Hook post-checkout pour CryptoSpreadEdge

echo "🌿 Changement de branche détecté..."

# Vérifier l'environnement conda
if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
    echo "🐍 Environnement conda actuel: $CONDA_DEFAULT_ENV"
    
    # Suggérer l'environnement approprié
    branch=$(git branch --show-current)
    if [[ $branch == "master" ]] || [[ $branch == "main" ]]; then
        echo "💡 Branche principale - Utilisez l'environnement de production"
        echo "   conda activate cryptospreadedge-prod"
    elif [[ $branch == "develop" ]]; then
        echo "💡 Branche de développement - Utilisez l'environnement de développement"
        echo "   conda activate cryptospreadedge-dev"
    else
        echo "💡 Branche de fonctionnalité - Utilisez l'environnement de développement"
        echo "   conda activate cryptospreadedge-dev"
    fi
else
    echo "⚠️  Aucun environnement conda activé"
    echo "💡 Activez un environnement: conda activate cryptospreadedge-dev"
fi

echo "✅ Checkout terminé"
EOF

chmod +x .git/hooks/post-checkout
echo "✅ Hook post-checkout installé"

echo ""
echo "🎉 Hooks Git installés avec succès!"
echo ""
echo "📋 Hooks installés:"
echo "  - pre-commit: Vérifications avant commit"
echo "  - post-commit: Actions après commit"
echo "  - pre-push: Vérifications avant push"
echo "  - post-merge: Actions après merge"
echo "  - post-checkout: Actions après checkout"
echo ""
echo "💡 Pour désinstaller les hooks:"
echo "   rm .git/hooks/pre-commit .git/hooks/post-commit .git/hooks/pre-push .git/hooks/post-merge .git/hooks/post-checkout"