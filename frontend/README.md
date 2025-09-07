# CryptoSpreadEdge Frontend

Interface utilisateur moderne pour la plateforme de trading crypto CryptoSpreadEdge.

## 🚀 Fonctionnalités

- **Dashboard Temps Réel** : Vue d'ensemble des performances et métriques
- **Données de Marché** : Visualisation des prix et volumes en temps réel
- **Indicateurs Techniques** : Calcul et affichage d'indicateurs avancés
- **Prédictions ML** : Interface pour les modèles de machine learning
- **Arbitrage** : Détection et exécution d'opportunités d'arbitrage
- **Paramètres** : Configuration complète du système

## 🛠️ Technologies

- **React 18** avec TypeScript
- **Material-UI (MUI)** pour l'interface utilisateur
- **Recharts** pour les graphiques
- **Axios** pour les requêtes API
- **Socket.IO** pour les mises à jour temps réel

## 📦 Installation

```bash
# Installer les dépendances
npm install

# Démarrer en mode développement
npm start

# Construire pour la production
npm run build
```

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` dans le dossier `frontend/` :

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### API Backend

Le frontend communique avec l'API Gateway de CryptoSpreadEdge via :

- **REST API** : `http://localhost:8000`
- **WebSocket** : `ws://localhost:8000`

## 📱 Pages Principales

### Dashboard
- Vue d'ensemble des services
- Métriques de performance
- Graphiques des prix
- Statut des connexions

### Données de Marché
- Sélection des symboles et timeframes
- Graphiques interactifs
- Tableau des données détaillées
- Mises à jour temps réel

### Indicateurs
- Calcul d'indicateurs techniques
- Visualisation graphique
- Valeurs détaillées
- Statistiques de performance

### Prédictions
- Interface ML pour les prédictions
- Entraînement de modèles
- Graphiques de prédictions
- Gestion des modèles

### Arbitrage
- Détection d'opportunités
- Filtres avancés
- Exécution d'arbitrage
- Monitoring temps réel

### Paramètres
- Configuration API
- Paramètres de trading
- Notifications
- Préférences d'affichage

## 🔌 API Integration

### Services Disponibles

- **Market Data Service** : Données de marché en temps réel
- **Indicators Service** : Calcul d'indicateurs techniques
- **Prediction Service** : Prédictions ML
- **Arbitrage Service** : Détection d'opportunités

### WebSocket Events

- `market-data-update` : Mises à jour des prix
- `indicators-update` : Nouveaux indicateurs
- `predictions-update` : Prédictions en temps réel
- `arbitrage-update` : Nouvelles opportunités

## 🎨 Thème et Styling

Le frontend utilise un thème sombre optimisé pour le trading :

- **Couleurs principales** : Vert crypto (#00ff88), Orange accent (#ff6b35)
- **Arrière-plan** : Noir profond (#0a0a0a)
- **Cartes** : Gris foncé (#1a1a1a)
- **Typographie** : Roboto pour la lisibilité

## 📊 Graphiques

Utilisation de Recharts pour :

- Graphiques de prix (candlesticks, lignes)
- Indicateurs techniques superposés
- Graphiques de prédictions
- Métriques de performance

## 🔄 Mises à jour Temps Réel

- Connexion WebSocket automatique
- Reconnexion en cas de perte de connexion
- Mise à jour des données sans rechargement
- Notifications visuelles des changements

## 🚀 Déploiement

### Production

```bash
# Construire l'application
npm run build

# Les fichiers sont dans le dossier build/
# Servir avec nginx ou un serveur web
```

### Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
```

## 🧪 Tests

```bash
# Tests unitaires
npm test

# Tests avec couverture
npm run test -- --coverage
```

## 📝 Scripts Disponibles

- `npm start` : Démarre le serveur de développement
- `npm run build` : Construit l'application pour la production
- `npm test` : Lance les tests
- `npm run eject` : Éjecte la configuration (irréversible)

## 🔧 Développement

### Structure des Dossiers

```
src/
├── components/          # Composants réutilisables
│   └── Layout/         # Layout principal
├── pages/              # Pages de l'application
├── services/           # Services API et WebSocket
├── types/              # Types TypeScript
└── utils/              # Utilitaires
```

### Ajout de Nouvelles Fonctionnalités

1. Créer le composant dans `src/components/`
2. Ajouter la page dans `src/pages/`
3. Mettre à jour la navigation dans `Layout.tsx`
4. Ajouter les types dans `services/api.ts`

## 🐛 Dépannage

### Problèmes Courants

- **Erreur de connexion API** : Vérifier l'URL dans les paramètres
- **WebSocket ne se connecte pas** : Vérifier le serveur backend
- **Données ne se chargent pas** : Vérifier les CORS et l'API Gateway

### Logs

Les logs sont disponibles dans la console du navigateur (F12).

## 📄 Licence

Ce projet fait partie de CryptoSpreadEdge et est sous licence MIT.