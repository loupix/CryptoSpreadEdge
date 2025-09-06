# Script de setup conda pour CryptoSpreadEdge (Windows)

Write-Host "🐍 Configuration de l'environnement conda pour CryptoSpreadEdge..." -ForegroundColor Green

# Vérifier si conda est installé
try {
    $condaVersion = conda --version
    Write-Host "✅ Conda détecté: $condaVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Conda n'est pas installé. Veuillez installer Miniconda ou Anaconda." -ForegroundColor Red
    Write-Host "📥 Téléchargez depuis: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
    exit 1
}

# Vérifier si l'environnement existe déjà
$envExists = conda env list | Select-String "cryptospreadedge"
if ($envExists) {
    Write-Host "⚠️  L'environnement 'cryptospreadedge' existe déjà." -ForegroundColor Yellow
    $response = Read-Host "Voulez-vous le supprimer et le recréer ? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "🗑️  Suppression de l'environnement existant..." -ForegroundColor Yellow
        conda env remove -n cryptospreadedge -y
    } else {
        Write-Host "ℹ️  Utilisation de l'environnement existant." -ForegroundColor Blue
        Write-Host "🔄 Activation de l'environnement..." -ForegroundColor Blue
        conda activate cryptospreadedge
        Write-Host "✅ Environnement activé !" -ForegroundColor Green
        exit 0
    }
}

# Créer l'environnement conda
Write-Host "🚀 Création de l'environnement conda..." -ForegroundColor Green
conda env create -f environment.yml

# Activer l'environnement
Write-Host "🔄 Activation de l'environnement..." -ForegroundColor Blue
conda activate cryptospreadedge

# Vérifier l'installation
Write-Host "🔍 Vérification de l'installation..." -ForegroundColor Blue
python --version
pip list | Select-String -Pattern "(fastapi|ccxt|pandas|torch|tensorflow)"

# Créer les répertoires nécessaires
Write-Host "📁 Création des répertoires..." -ForegroundColor Blue
New-Item -ItemType Directory -Path "data\historical" -Force | Out-Null
New-Item -ItemType Directory -Path "data\models" -Force | Out-Null
New-Item -ItemType Directory -Path "data\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "logs" -Force | Out-Null

# Copier le fichier de configuration
Write-Host "⚙️ Configuration..." -ForegroundColor Blue
if (!(Test-Path "config\environments\.env")) {
    Copy-Item "config\environments\env.example" "config\environments\.env"
    Write-Host "📝 Fichier .env créé. Veuillez le configurer avec vos clés API." -ForegroundColor Yellow
}

Write-Host "✅ Setup conda terminé avec succès!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Pour utiliser l'environnement:" -ForegroundColor Cyan
Write-Host "1. conda activate cryptospreadedge" -ForegroundColor White
Write-Host "2. python -m src.main" -ForegroundColor White
Write-Host ""
Write-Host "📋 Pour désactiver l'environnement:" -ForegroundColor Cyan
Write-Host "conda deactivate" -ForegroundColor White
Write-Host ""
Write-Host "📋 Pour supprimer l'environnement:" -ForegroundColor Cyan
Write-Host "conda env remove -n cryptospreadedge" -ForegroundColor White