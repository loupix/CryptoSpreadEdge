# CryptoSpreadEdge Frontend

Frontend React complet pour la plateforme de trading crypto CryptoSpreadEdge avec intégration base de données PostgreSQL.

## 🎯 Vue d'ensemble

Application React moderne et professionnelle offrant une interface complète pour :
- **Trading avancé** : Ordres, positions, trades en temps réel
- **Gestion des utilisateurs** : Administration, rôles, permissions
- **Données historiques** : Ordres, positions, trades, portefeuille
- **Configuration des exchanges** : Multi-plateformes (Binance, Coinbase, etc.)
- **Monitoring** : Performance système et optimisation
- **Sécurité** : Authentification, autorisation, audit trail

## 🚀 Démarrage Rapide

### Prérequis
- Node.js 16+ 
- npm 8+
- Backend PostgreSQL configuré

### Installation Automatique
```bash
# Linux/Mac
./start-frontend.sh dev

# Windows PowerShell
.\start-frontend.ps1 dev
```

### Installation Manuelle
```bash
npm install
cp env.example .env
npm start
```

L'application sera accessible sur http://localhost:3000

## 📁 Structure du Projet

```
src/
├── components/              # Composants réutilisables
│   ├── Layout/             # Layout principal avec navigation
│   ├── Trading/            # Interface de trading
│   ├── HistoricalData/     # Données historiques
│   ├── UserManagement/     # Gestion des utilisateurs
│   ├── Alerts/             # Gestion des alertes
│   ├── Performance/        # Monitoring et optimisation
│   └── Exchanges/          # Configuration des exchanges
├── pages/                  # Pages de l'application
│   ├── Dashboard.tsx       # Vue d'ensemble
│   ├── Trading.tsx         # Interface de trading
│   ├── HistoricalData.tsx  # Données historiques
│   ├── UserManagement.tsx  # Gestion des utilisateurs
│   ├── Performance.tsx     # Monitoring des performances
│   ├── ExchangeConfig.tsx  # Configuration des exchanges
│   └── Settings.tsx        # Paramètres
├── services/               # Services API
│   ├── databaseApi.ts      # API base de données
│   ├── api.ts             # API général
│   └── websocket.ts       # WebSocket temps réel
├── hooks/                  # Hooks personnalisés
│   └── useDatabaseApi.ts  # Hooks pour la base de données
└── App.tsx                # Composant principal
```

## 🎨 Technologies

- **React 18** - Framework UI moderne
- **TypeScript** - Typage statique complet
- **Material-UI v5** - Composants UI professionnels
- **Recharts** - Graphiques et visualisations
- **Axios** - Client HTTP avec intercepteurs
- **Socket.io** - WebSocket temps réel
- **React Router v6** - Navigation SPA
- **Date-fns** - Manipulation des dates
- **Lodash** - Utilitaires JavaScript

## 🔧 Configuration

### Variables d'Environnement
```env
# API Backend
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000/ws

# Base de données
REACT_APP_DB_ENABLED=true
REACT_APP_DB_TYPE=postgresql

# Monitoring
REACT_APP_MONITORING_ENABLED=true
REACT_APP_METRICS_ENABLED=true

# Sécurité
REACT_APP_SECURITY_ENABLED=true
REACT_APP_ENCRYPTION_ENABLED=true

# Interface
REACT_APP_THEME=light
REACT_APP_LANGUAGE=fr
REACT_APP_TIMEZONE=Europe/Paris
```

## 🚀 Fonctionnalités Principales

### ✅ Interface de Trading
- **Création d'ordres** : Market, Limit, Stop, Stop-Limit
- **Gestion des positions** : Ouverture, fermeture, suivi PnL
- **Historique des trades** : Visualisation complète
- **Contrôles temps réel** : Démarrer, pause, arrêter
- **Filtres avancés** : Par symbole, statut, date

### ✅ Gestion des Utilisateurs
- **CRUD complet** : Création, modification, suppression
- **Rôles et permissions** : Admin, Trader, Analyste, Observateur, Auditeur
- **Sécurité avancée** : 2FA, vérification email, sessions
- **Gestion des alertes** : Création et configuration

### ✅ Données Historiques
- **Ordres** : Affichage, filtrage, détails, actions CRUD
- **Positions** : Gestion des positions ouvertes/fermées
- **Trades** : Historique avec métriques de performance
- **Portefeuille** : Évolution et performance

### ✅ Configuration des Exchanges
- **Support multi-plateformes** : Binance, Coinbase, Kraken, Bybit, Gate.io, OKX
- **Gestion des clés API** : Stockage sécurisé et chiffré
- **Test de connexion** : Validation des configurations
- **Monitoring** : Surveillance des connexions

### ✅ Monitoring et Performance
- **Dashboard temps réel** : Métriques système et base de données
- **Optimiseur de performance** : Analyse et recommandations
- **Métriques détaillées** : Bundle size, temps de chargement, mémoire
- **Alertes de performance** : Notifications automatiques

## 📦 Scripts Disponibles

### Scripts NPM
```bash
npm start          # Démarrage en développement
npm run build      # Build de production
npm test           # Tests unitaires
npm run eject      # Eject de Create React App
```

### Scripts Personnalisés
```bash
# Linux/Mac
./start-frontend.sh dev     # Démarrage développement
./start-frontend.sh prod    # Démarrage production
./start-frontend.sh build   # Build uniquement

# Windows PowerShell
.\start-frontend.ps1 dev     # Démarrage développement
.\start-frontend.ps1 prod    # Démarrage production
.\start-frontend.ps1 build   # Build uniquement
```

## 🔒 Sécurité

### Authentification
- **JWT Tokens** : Authentification stateless
- **Refresh Tokens** : Renouvellement automatique
- **Intercepteurs** : Gestion automatique des tokens
- **Redirection** : Retour au login en cas d'erreur 401

### Autorisation
- **Rôles** : Contrôle d'accès granulaire
- **Permissions** : Actions autorisées par rôle
- **UI Conditionnelle** : Affichage basé sur les permissions
- **Protection des routes** : Accès contrôlé

### Données Sensibles
- **Chiffrement** : Clés API chiffrées
- **Masquage** : Affichage sécurisé des données
- **Validation** : Vérification côté client et serveur
- **Audit** : Traçabilité des actions

## 📊 Performance

### Optimisations Implémentées
- **Code Splitting** : Chargement à la demande
- **Lazy Loading** : Composants chargés dynamiquement
- **Memoization** : Optimisation des re-renders
- **Pagination** : Chargement progressif des données
- **Cache** : Mise en cache des données fréquentes

### Métriques Surveillées
- **Bundle Size** : Taille du JavaScript
- **Load Time** : Temps de chargement initial
- **Memory Usage** : Utilisation de la mémoire
- **Network Requests** : Nombre de requêtes
- **Cache Hit Rate** : Taux de succès du cache
- **Render Time** : Temps de rendu des composants

## 🧪 Tests

### Types de Tests
- **Unit Tests** : Composants individuels
- **Integration Tests** : Flux complets
- **E2E Tests** : Scénarios utilisateur
- **Performance Tests** : Métriques de performance

### Commandes de Test
```bash
npm test                    # Tests unitaires
npm run test:coverage       # Tests avec couverture
npm run test:e2e           # Tests E2E
npm run test:performance   # Tests de performance
```

## 🚀 Déploiement

### Build de Production
```bash
npm run build
```

### Serveur de Production
```bash
# Avec serve
npx serve -s build -l 3000

# Avec nginx
# Configurer nginx pour servir le dossier build/
```

### Docker
```bash
# Build de l'image
docker build -t cryptospreadedge-frontend .

# Exécution du conteneur
docker run -p 3000:3000 cryptospreadedge-frontend
```

## 📚 Documentation

### Guides Disponibles
- [Intégration Base de Données](FRONTEND_DATABASE_INTEGRATION.md)
- [Résumé Complet](FRONTEND_COMPLETE_SUMMARY.md)
- [Guide de Développement](docs/DEVELOPMENT.md)
- [Guide de Déploiement](docs/DEPLOYMENT.md)

### API Reference
- **Endpoints** : Documentation des APIs
- **Types** : Types TypeScript
- **Hooks** : Documentation des hooks
- **Composants** : Storybook

## 🚧 Développements Futurs

### En Cours
- **Notifications temps réel** : WebSocket pour les alertes
- **Graphiques avancés** : TradingView integration
- **Export de données** : PDF, Excel, CSV
- **Thèmes personnalisables** : Mode sombre/clair

### Prévus
- **Mobile App** : Application mobile native
- **PWA** : Progressive Web App
- **Internationalisation** : Support multi-langues
- **Accessibilité** : Amélioration WCAG

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -m 'feat: ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🆘 Support

- **Documentation** : Voir les guides dans `/docs/`
- **Issues** : Utiliser le système d'issues GitHub
- **Discussions** : Utiliser les discussions GitHub
- **Email** : support@cryptospreadedge.com

---

**Note** : Cette application est conçue pour fonctionner avec le système de base de données PostgreSQL développé précédemment. Assurez-vous que le backend est configuré et accessible avant d'utiliser ces fonctionnalités.