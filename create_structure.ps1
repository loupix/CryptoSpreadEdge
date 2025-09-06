# Script pour créer la structure des dossiers CryptoSpreadEdge

# Dossiers principaux
$folders = @(
    "src\connectors\binance",
    "src\connectors\coinbase", 
    "src\connectors\kraken",
    "src\connectors\bybit",
    "src\connectors\common",
    "src\ai\models",
    "src\ai\strategies",
    "src\ai\feature_engineering",
    "src\ai\backtesting",
    "src\data\streaming",
    "src\data\storage",
    "src\data\processing",
    "src\data\analytics",
    "src\api\rest",
    "src\api\websocket",
    "src\api\grpc",
    "src\api\graphql",
    "src\monitoring\metrics",
    "src\monitoring\logging",
    "src\monitoring\alerting",
    "src\monitoring\dashboards",
    "src\utils\config",
    "src\utils\security",
    "src\utils\messaging",
    "src\utils\common",
    "infrastructure\docker\services",
    "infrastructure\docker\swarm",
    "infrastructure\docker\compose",
    "infrastructure\kubernetes",
    "infrastructure\terraform",
    "infrastructure\monitoring",
    "tests\unit",
    "tests\integration",
    "tests\performance",
    "tests\e2e",
    "docs\api",
    "docs\architecture",
    "docs\deployment",
    "docs\strategies",
    "scripts\setup",
    "scripts\deployment",
    "scripts\maintenance",
    "scripts\data",
    "config\environments",
    "config\strategies",
    "config\exchanges",
    "data\historical",
    "data\models",
    "data\logs",
    "tools\data_generators",
    "tools\simulators",
    "tools\analyzers"
)

# Créer tous les dossiers
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force
    Write-Host "Créé: $folder"
}

Write-Host "Structure des dossiers créée avec succès !"