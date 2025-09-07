# Script de démarrage du frontend CryptoSpreadEdge pour Windows PowerShell
# Usage: .\start-frontend.ps1 [dev|prod|build]

param(
    [string]$Command = "dev"
)

# Fonction pour afficher les messages
function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Log $Message "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-Log $Message "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-Log $Message "Red"
}

# Vérifier si Node.js est installé
function Test-Node {
    try {
        $nodeVersion = node --version
        Write-Log "Node.js version: $nodeVersion"
        return $true
    }
    catch {
        Write-Error "Node.js n'est pas installé. Veuillez l'installer d'abord."
        return $false
    }
}

# Vérifier si npm est installé
function Test-Npm {
    try {
        $npmVersion = npm --version
        Write-Log "npm version: $npmVersion"
        return $true
    }
    catch {
        Write-Error "npm n'est pas installé. Veuillez l'installer d'abord."
        return $false
    }
}

# Installer les dépendances
function Install-Dependencies {
    Write-Log "Installation des dépendances..."
    
    if (-not (Test-Path "package.json")) {
        Write-Error "package.json non trouvé. Êtes-vous dans le bon répertoire ?"
        exit 1
    }
    
    npm install
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dépendances installées avec succès"
    } else {
        Write-Error "Échec de l'installation des dépendances"
        exit 1
    }
}

# Vérifier la configuration
function Test-Config {
    Write-Log "Vérification de la configuration..."
    
    if (-not (Test-Path ".env")) {
        Write-Warning "Fichier .env non trouvé. Copie de env.example..."
        if (Test-Path "env.example") {
            Copy-Item "env.example" ".env"
            Write-Success "Fichier .env créé à partir de env.example"
        } else {
            Write-Error "Fichier env.example non trouvé"
            exit 1
        }
    }
    
    # Vérifier les variables d'environnement critiques
    $envContent = Get-Content ".env" -Raw
    if ($envContent -notmatch "REACT_APP_API_URL") {
        Write-Warning "REACT_APP_API_URL non définie dans .env"
    }
    
    Write-Success "Configuration vérifiée"
}

# Démarrer en mode développement
function Start-Dev {
    Write-Log "Démarrage en mode développement..."
    
    if (-not (Test-Node)) { exit 1 }
    if (-not (Test-Npm)) { exit 1 }
    Install-Dependencies
    Test-Config
    
    Write-Log "Lancement du serveur de développement..."
    Write-Success "Frontend accessible sur http://localhost:3000"
    npm start
}

# Démarrer en mode production
function Start-Prod {
    Write-Log "Démarrage en mode production..."
    
    if (-not (Test-Node)) { exit 1 }
    if (-not (Test-Npm)) { exit 1 }
    Install-Dependencies
    Test-Config
    
    Write-Log "Build de l'application..."
    npm run build
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path "build")) {
        Write-Success "Build terminé avec succès"
        Write-Log "Lancement du serveur de production..."
        
        # Vérifier si serve est disponible
        try {
            serve -s build -l 3000
        }
        catch {
            Write-Log "Installation de serve..."
            npm install -g serve
            serve -s build -l 3000
        }
    } else {
        Write-Error "Échec du build"
        exit 1
    }
}

# Build uniquement
function Build-Only {
    Write-Log "Build de l'application..."
    
    if (-not (Test-Node)) { exit 1 }
    if (-not (Test-Npm)) { exit 1 }
    Install-Dependencies
    Test-Config
    
    npm run build
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path "build")) {
        Write-Success "Build terminé avec succès dans le dossier 'build'"
    } else {
        Write-Error "Échec du build"
        exit 1
    }
}

# Afficher l'aide
function Show-Help {
    Write-Host "Usage: .\start-frontend.ps1 [COMMAND]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  dev     Démarrer en mode développement (défaut)" -ForegroundColor White
    Write-Host "  prod    Démarrer en mode production" -ForegroundColor White
    Write-Host "  build   Build uniquement" -ForegroundColor White
    Write-Host "  help    Afficher cette aide" -ForegroundColor White
    Write-Host ""
    Write-Host "Exemples:" -ForegroundColor White
    Write-Host "  .\start-frontend.ps1 dev     # Démarrer en mode développement" -ForegroundColor White
    Write-Host "  .\start-frontend.ps1 prod    # Démarrer en mode production" -ForegroundColor White
    Write-Host "  .\start-frontend.ps1 build   # Build uniquement" -ForegroundColor White
}

# Fonction principale
function Main {
    # Vérifier si on est dans le bon répertoire
    if (-not (Test-Path "package.json")) {
        Write-Error "Ce script doit être exécuté depuis le répertoire frontend/"
        exit 1
    }
    
    switch ($Command.ToLower()) {
        "dev" {
            Start-Dev
        }
        "prod" {
            Start-Prod
        }
        "build" {
            Build-Only
        }
        "help" {
            Show-Help
        }
        default {
            Write-Error "Commande inconnue: $Command"
            Show-Help
            exit 1
        }
    }
}

# Exécuter la fonction principale
Main