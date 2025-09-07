# CryptoSpreadEdge Mobile

Application mobile React Native pour le trading crypto haute fréquence.

## Fonctionnalités

- **Dashboard en temps réel** : Visualisation des prix et opportunités d'arbitrage
- **Trading** : Passer des ordres d'achat/vente sur différentes plateformes
- **Portefeuille** : Suivi des positions et performance
- **Arbitrage** : Détection et exécution d'opportunités d'arbitrage
- **Notifications push** : Alertes de prix et de trading
- **Thème sombre/clair** : Interface adaptative
- **Sécurité** : Authentification sécurisée et stockage des clés

## Installation

### Prérequis

- Node.js >= 20
- React Native CLI
- Android Studio (pour Android)
- Xcode (pour iOS)

### Installation des dépendances

```bash
npm install
```

### Configuration

1. Copier le fichier de configuration :
```bash
cp .env.example .env
```

2. Configurer les variables d'environnement dans `.env` :
```
API_BASE_URL=http://localhost:8000/api
WS_URL=ws://localhost:8000/ws
```

### Lancement

#### Android
```bash
npm run android
```

#### iOS
```bash
npm run ios
```

## Structure du projet

```
src/
├── components/          # Composants réutilisables
├── screens/            # Écrans de l'application
│   ├── auth/          # Authentification
│   └── main/          # Écrans principaux
├── services/          # Services API et WebSocket
├── contexts/          # Contextes React
├── navigation/        # Configuration de navigation
├── types/            # Types TypeScript
└── utils/            # Utilitaires
```

## API Backend

L'application se connecte à l'API REST et WebSocket du backend CryptoSpreadEdge :

- **REST API** : `/api/mobile/`
- **WebSocket** : `ws://localhost:8000/ws`

### Endpoints principaux

- `POST /auth/login` - Connexion
- `POST /auth/register` - Inscription
- `GET /market/data` - Données de marché
- `POST /trading/orders` - Passer un ordre
- `GET /portfolio` - Portefeuille
- `GET /arbitrage/opportunities` - Opportunités d'arbitrage

## Développement

### Ajout d'un nouvel écran

1. Créer le composant dans `src/screens/`
2. Ajouter la route dans `src/navigation/AppNavigator.tsx`
3. Mettre à jour les types dans `src/types/navigation.ts`

### Ajout d'un service API

1. Créer le service dans `src/services/`
2. Ajouter les types dans `src/types/`
3. Intégrer dans les contextes si nécessaire

## Tests

```bash
npm test
```

## Build de production

### Android

```bash
cd android
./gradlew assembleRelease
```

### iOS

```bash
cd ios
xcodebuild -workspace CryptoSpreadEdgeMobile.xcworkspace -scheme CryptoSpreadEdgeMobile -configuration Release
```

## Déploiement

### Google Play Store

1. Générer un APK signé
2. Créer une release dans Google Play Console
3. Uploader l'APK

### Apple App Store

1. Archiver l'application dans Xcode
2. Uploader via Xcode ou Application Loader
3. Soumettre pour review

## Sécurité

- Authentification JWT
- Stockage sécurisé des tokens
- Chiffrement des données sensibles
- Validation des entrées utilisateur

## Performance

- Optimisation des images
- Lazy loading des écrans
- Cache des données API
- Gestion mémoire optimisée

## Support

Pour toute question ou problème, consulter la documentation du backend ou contacter l'équipe de développement.