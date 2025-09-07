# Intégration Frontend - Base de Données

## 🎯 Vue d'ensemble

Ce document décrit l'intégration complète du système de base de données PostgreSQL avec le frontend React de CryptoSpreadEdge. L'intégration permet une gestion complète des données de trading, des utilisateurs, des alertes et des performances.

## 🏗️ Architecture

### Services API
- **`databaseApi.ts`** : Service principal pour les appels API vers la base de données
- **`useDatabaseApi.ts`** : Hooks React pour faciliter l'utilisation des APIs
- **Configuration** : Variables d'environnement pour l'URL de l'API

### Composants Principaux

#### 1. Données Historiques
- **`HistoricalData.tsx`** : Page principale pour les données historiques
- **`OrdersTable.tsx`** : Table des ordres avec filtres et actions
- **`PositionsTable.tsx`** : Table des positions avec gestion des PnL

#### 2. Gestion des Utilisateurs
- **`UserManagement.tsx`** : Page de gestion des utilisateurs
- **`UsersTable.tsx`** : Table des utilisateurs avec rôles et permissions
- **`AlertsManager.tsx`** : Gestionnaire d'alertes et notifications

#### 3. Monitoring des Performances
- **`Performance.tsx`** : Page de monitoring des performances
- **`PerformanceDashboard.tsx`** : Dashboard avec métriques en temps réel

## 🔧 Fonctionnalités Implémentées

### ✅ Données Historiques
- **Ordres** : Affichage, filtrage, détails, actions CRUD
- **Positions** : Gestion des positions ouvertes/fermées, PnL
- **Trades** : Historique des transactions (en développement)
- **Portefeuille** : Évolution du portefeuille (en développement)

### ✅ Gestion des Utilisateurs
- **CRUD Utilisateurs** : Création, modification, suppression
- **Rôles et Permissions** : Admin, Trader, Analyste, Observateur, Auditeur
- **Sécurité** : 2FA, vérification email, gestion des sessions
- **Alertes** : Création et gestion des alertes personnalisées

### ✅ Monitoring et Performance
- **Métriques Temps Réel** : Latence, utilisation mémoire, santé système
- **Dashboard Performance** : Score global, Sharpe ratio, drawdown
- **Backup Status** : Statut des sauvegardes et planification
- **Événements Sécurité** : Monitoring des événements de sécurité

## 🚀 Utilisation

### Installation des Dépendances
```bash
cd frontend
npm install
```

### Configuration
1. Copier `env.example` vers `.env`
2. Configurer les variables d'environnement :
   ```env
   REACT_APP_API_URL=http://localhost:8000/api/v1
   REACT_APP_WS_URL=ws://localhost:8000/ws
   REACT_APP_DB_ENABLED=true
   ```

### Démarrage
```bash
npm start
```

## 📊 Types de Données

### Ordres (Orders)
```typescript
interface Order {
  id: string;
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  price?: number;
  status: 'pending' | 'open' | 'filled' | 'partially_filled' | 'canceled' | 'rejected';
  exchange: string;
  created_at: string;
  updated_at: string;
}
```

### Positions (Positions)
```typescript
interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  average_price: number;
  current_price?: number;
  unrealized_pnl: number;
  realized_pnl: number;
  status: 'open' | 'closed' | 'partially_closed';
  exchange: string;
  opened_at: string;
  closed_at?: string;
}
```

### Utilisateurs (Users)
```typescript
interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'trader' | 'viewer' | 'analyst' | 'auditor';
  status: 'active' | 'inactive' | 'suspended' | 'pending_verification';
  two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
}
```

## 🔌 Hooks Disponibles

### Hooks de Lecture
- `useOrders()` : Récupération des ordres
- `usePositions()` : Récupération des positions
- `useTrades()` : Récupération des trades
- `useUsers()` : Récupération des utilisateurs
- `useAlerts()` : Récupération des alertes
- `usePerformanceMetrics()` : Métriques de performance

### Hooks de Mutation
- `useCreateOrder()` : Création d'ordres
- `useUpdateOrder()` : Modification d'ordres
- `useDeleteOrder()` : Suppression d'ordres
- `useCreateUser()` : Création d'utilisateurs
- `useUpdateUser()` : Modification d'utilisateurs
- `useCreateAlert()` : Création d'alertes

## 🎨 Interface Utilisateur

### Navigation
- **Dashboard** : Vue d'ensemble du système
- **Données Historiques** : Ordres, positions, trades, portefeuille
- **Utilisateurs** : Gestion des utilisateurs et alertes
- **Performance** : Monitoring des performances système

### Fonctionnalités UI
- **Filtres Avancés** : Par symbole, exchange, statut, date
- **Pagination** : Navigation dans les grandes listes
- **Actions CRUD** : Création, modification, suppression
- **Dialogs de Détails** : Affichage détaillé des éléments
- **Notifications** : Alertes et messages système

## 🔒 Sécurité

### Authentification
- **Token JWT** : Authentification via token
- **Intercepteurs Axios** : Ajout automatique du token
- **Gestion des Erreurs** : Redirection vers login en cas d'erreur 401

### Permissions
- **Rôles Utilisateurs** : Contrôle d'accès basé sur les rôles
- **Actions Sécurisées** : Vérification des permissions avant actions
- **Audit Trail** : Traçabilité des actions utilisateur

## 📈 Performance

### Optimisations
- **Hooks Personnalisés** : Réutilisation de la logique
- **Pagination** : Chargement progressif des données
- **Filtres Côté Serveur** : Réduction du trafic réseau
- **Cache Local** : Mise en cache des données fréquentes

### Monitoring
- **Métriques Temps Réel** : Latence, mémoire, CPU
- **Alertes Performance** : Notifications en cas de problème
- **Dashboard** : Vue d'ensemble des performances

## 🚧 Développements Futurs

### En Cours
- Interface de trading avancée
- Configuration des exchanges
- Optimisations de performance

### Prévus
- Notifications en temps réel
- Graphiques avancés
- Export de données
- Thèmes personnalisables

## 🐛 Dépannage

### Problèmes Courants
1. **Erreur 401** : Vérifier le token d'authentification
2. **Données manquantes** : Vérifier la connexion à l'API
3. **Performance lente** : Vérifier les filtres et la pagination

### Logs
- **Console Browser** : Erreurs JavaScript
- **Network Tab** : Requêtes API
- **React DevTools** : État des composants

## 📚 Ressources

- [Documentation API Backend](../docs/database/README.md)
- [Guide de Déploiement](../docs/deployment/)
- [Architecture Système](../docs/architecture/overview.md)

---

**Note** : Cette intégration est conçue pour fonctionner avec le système de base de données PostgreSQL développé précédemment. Assurez-vous que le backend est configuré et accessible avant d'utiliser ces fonctionnalités.