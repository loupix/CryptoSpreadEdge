# Installation des hooks Git pour CryptoSpreadEdge (Windows)

Write-Host "🔧 Installation des hooks Git pour CryptoSpreadEdge..." -ForegroundColor Green

# Vérifier que nous sommes dans un repository Git
if (!(Test-Path ".git")) {
    Write-Host "❌ Ce n'est pas un repository Git" -ForegroundColor Red
    exit 1
}

# Créer le répertoire des hooks s'il n'existe pas
New-Item -ItemType Directory -Path ".git\hooks" -Force | Out-Null

# Copier les hooks
Write-Host "📋 Copie des hooks..." -ForegroundColor Blue

# Pre-commit
Copy-Item "scripts\git\hooks\pre-commit" ".git\hooks\pre-commit" -Force
Write-Host "✅ Hook pre-commit installé" -ForegroundColor Green

# Post-commit
Copy-Item "scripts\git\hooks\post-commit" ".git\hooks\post-commit" -Force
Write-Host "✅ Hook post-commit installé" -ForegroundColor Green

# Pre-push
Copy-Item "scripts\git\hooks\pre-push" ".git\hooks\pre-push" -Force
Write-Host "✅ Hook pre-push installé" -ForegroundColor Green

# Créer un hook de mise à jour automatique
$postMergeContent = @'
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
'@

$postMergeContent | Out-File -FilePath ".git\hooks\post-merge" -Encoding UTF8
Write-Host "✅ Hook post-merge installé" -ForegroundColor Green

# Créer un hook de checkout pour changer d'environnement
$postCheckoutContent = @'
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
'@

$postCheckoutContent | Out-File -FilePath ".git\hooks\post-checkout" -Encoding UTF8
Write-Host "✅ Hook post-checkout installé" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Hooks Git installés avec succès!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Hooks installés:" -ForegroundColor Cyan
Write-Host "  - pre-commit: Vérifications avant commit" -ForegroundColor White
Write-Host "  - post-commit: Actions après commit" -ForegroundColor White
Write-Host "  - pre-push: Vérifications avant push" -ForegroundColor White
Write-Host "  - post-merge: Actions après merge" -ForegroundColor White
Write-Host "  - post-checkout: Actions après checkout" -ForegroundColor White
Write-Host ""
Write-Host "💡 Pour désinstaller les hooks:" -ForegroundColor Yellow
Write-Host "   Remove-Item .git\hooks\pre-commit, .git\hooks\post-commit, .git\hooks\pre-push, .git\hooks\post-merge, .git\hooks\post-checkout" -ForegroundColor White