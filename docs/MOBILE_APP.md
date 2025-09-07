# Application Mobile CryptoSpreadEdge

## Vue d'ensemble

L'application mobile CryptoSpreadEdge est une application React Native qui permet aux utilisateurs de trader des cryptomonnaies en temps réel, de surveiller les opportunités d'arbitrage et de gérer leur portefeuille depuis leur smartphone.

## Architecture

### Frontend Mobile (React Native)

```
mobile/
├── src/
│   ├── components/          # Composants réutilisables
│   ├── screens/            # Écrans de l'application
│   │   ├── auth/          # Authentification (Login, Register)
│   │   └── main/          # Écrans principaux (Dashboard, Trading, Portfolio, Arbitrage, Settings)
│   ├── services/          # Services API et WebSocket
│   │   ├── api.ts         # Service API REST
│   │   ├── websocket.ts   # Service WebSocket temps réel
│   │   └── auth.ts        # Service d'authentification
│   ├── contexts/          # Contextes React pour l'état global
│   │   ├── AuthContext.tsx
│   │   ├── MarketDataContext.tsx
│   │   └── ThemeContext.tsx
│   ├── navigation/        # Configuration de navigation
│   │   └── AppNavigator.tsx
│   ├── types/            # Types TypeScript
│   │   ├── index.ts
│   │   └── navigation.ts
│   └── utils/            # Utilitaires
├── android/              # Configuration Android
├── ios/                  # Configuration iOS
└── package.json
```

### Backend API Mobile

```
src/api/rest/mobile_api.py      # API REST pour mobile
src/api/websocket/mobile_websocket.py  # WebSocket pour mobile
src/core/security/auth_manager.py     # Gestionnaire d'authentification
```

## Fonctionnalités

### 1. Authentification
- **Connexion/Inscription** : Interface utilisateur intuitive
- **Sécurité** : JWT tokens, stockage sécurisé des credentials
- **Gestion des sessions** : Refresh tokens, déconnexion automatique

### 2. Dashboard
- **Données temps réel** : Prix des cryptomonnaies en direct
- **Opportunités d'arbitrage** : Affichage des spreads entre plateformes
- **Métriques clés** : Performance du portefeuille, P&L
- **Actions rapides** : Accès direct au trading et à l'arbitrage

### 3. Trading
- **Passage d'ordres** : Market et limit orders
- **Sélection de paires** : BTC/USDT, ETH/USDT, etc.
- **Gestion des ordres** : Historique, annulation, statuts
- **Interface intuitive** : Boutons d'achat/vente, saisie de quantités

### 4. Portefeuille
- **Vue d'ensemble** : Valeur totale, performance 24h
- **Positions** : Détail des holdings par symbole
- **P&L** : Profit/Loss par position et global
- **Liquidités** : Cash disponible

### 5. Arbitrage
- **Détection automatique** : Opportunités entre plateformes
- **Filtrage** : Par profit, spread, confiance
- **Exécution** : Bouton d'exécution d'arbitrage
- **Historique** : Suivi des arbitrages passés

### 6. Paramètres
- **Profil utilisateur** : Modification des informations
- **Préférences** : Thème, devise, langue
- **Notifications** : Configuration des alertes
- **Sécurité** : Déconnexion, gestion des sessions

## Technologies

### Frontend
- **React Native 0.81.1** : Framework mobile cross-platform
- **TypeScript** : Typage statique
- **React Navigation** : Navigation entre écrans
- **React Native Vector Icons** : Icônes
- **React Native Chart Kit** : Graphiques
- **React Native WebSocket** : Connexions temps réel
- **AsyncStorage** : Stockage local
- **React Native Keychain** : Stockage sécurisé

### Backend
- **FastAPI** : API REST haute performance
- **WebSocket** : Connexions temps réel
- **JWT** : Authentification
- **bcrypt** : Hachage des mots de passe
- **Pydantic** : Validation des données

## API Endpoints

### Authentification
- `POST /mobile/auth/login` - Connexion
- `POST /mobile/auth/register` - Inscription
- `POST /mobile/auth/logout` - Déconnexion
- `POST /mobile/auth/refresh` - Refresh token
- `GET /mobile/auth/me` - Informations utilisateur

### Données de marché
- `GET /mobile/market/data` - Prix en temps réel
- `GET /mobile/market/pairs` - Paires disponibles
- `GET /mobile/indicators/bundle` - Indicateurs techniques

### Trading
- `POST /mobile/trading/orders` - Passer un ordre
- `GET /mobile/trading/orders` - Liste des ordres
- `DELETE /mobile/trading/orders/{id}` - Annuler un ordre

### Portefeuille
- `GET /mobile/portfolio` - Vue d'ensemble
- `GET /mobile/portfolio/positions` - Positions détaillées

### Arbitrage
- `GET /mobile/arbitrage/opportunities` - Opportunités actuelles
- `GET /mobile/arbitrage/history` - Historique

### Alertes
- `POST /mobile/alerts` - Créer une alerte
- `GET /mobile/alerts` - Liste des alertes
- `PUT /mobile/alerts/{id}` - Modifier une alerte
- `DELETE /mobile/alerts/{id}` - Supprimer une alerte

## WebSocket

### Connexion
```
ws://localhost:8000/ws?user_id=USER_ID
```

### Messages
- `market_data` : Données de marché temps réel
- `order_update` : Mise à jour d'ordres
- `portfolio_update` : Mise à jour du portefeuille
- `arbitrage_opportunity` : Nouvelles opportunités

### Souscriptions
```json
{
  "type": "subscribe",
  "channel": "market_data",
  "symbols": ["BTC/USDT", "ETH/USDT"]
}
```

## Déploiement

### Développement
```bash
cd mobile
npm install
npm start
```

### Android
```bash
npm run android
```

### iOS
```bash
npm run ios
```

### Production
```bash
./scripts/mobile/deploy-mobile.sh
```

## Configuration

### Variables d'environnement
```env
API_BASE_URL=http://localhost:8000/api
WS_URL=ws://localhost:8000/ws
DEBUG=true
```

### Android
- Permissions : Internet, Notifications, Vibrations
- Min SDK : 21
- Target SDK : 33

### iOS
- Deployment Target : 11.0
- Permissions : Camera, Microphone, Location
- Background Modes : Background fetch, Background processing

## Sécurité

### Authentification
- JWT tokens avec expiration
- Refresh tokens pour renouvellement
- Stockage sécurisé des credentials

### Communication
- HTTPS/WSS en production
- Validation des données côté serveur
- Chiffrement des données sensibles

### Stockage
- Keychain (iOS) / Keystore (Android)
- Chiffrement des tokens
- Nettoyage automatique des sessions

## Performance

### Optimisations
- Lazy loading des écrans
- Cache des données API
- Optimisation des images
- Gestion mémoire efficace

### Monitoring
- Métriques de performance
- Logs d'erreurs
- Analytics d'usage

## Tests

### Unitaires
```bash
npm test
```

### E2E
```bash
npm run e2e
```

### Linting
```bash
npm run lint
```

## Roadmap

### Version 1.1
- [ ] Graphiques avancés
- [ ] Notifications push
- [ ] Mode hors ligne
- [ ] Biométrie

### Version 1.2
- [ ] Trading social
- [ ] Copy trading
- [ ] Alertes avancées
- [ ] Widgets

### Version 2.0
- [ ] IA intégrée
- [ ] Trading automatisé
- [ ] Multi-comptes
- [ ] API publique

## Support

Pour toute question ou problème :
1. Consulter la documentation du backend
2. Vérifier les logs de l'application
3. Contacter l'équipe de développement
4. Créer une issue sur le repository