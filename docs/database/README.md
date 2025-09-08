# Base de données PostgreSQL - CryptoSpreadEdge

## 🎯 Vue d'ensemble

L'intégration PostgreSQL dans CryptoSpreadEdge apporte la persistance des données critiques de trading, remplaçant le stockage en mémoire par une solution robuste et scalable.

## 🚀 Démarrage rapide

### 1. Déploiement automatique
```bash
# Déployer PostgreSQL avec tous les services
./scripts/database/deploy_postgresql.sh

# Déployer et exécuter les tests
./scripts/database/deploy_postgresql.sh --test
```

### 2. Déploiement manuel
```bash
# Démarrer PostgreSQL
docker-compose -f infrastructure/docker/compose/docker-compose.yml up -d postgres

# Initialiser la base de données
python scripts/database/init_database.py

# Tester la base de données
python scripts/database/test_database.py
```

## 📊 Architecture des données

### Tables principales
- **orders** : Ordres de trading
- **positions** : Positions ouvertes/fermées
- **trades** : Historique des transactions
- **strategies** : Configuration des stratégies
- **portfolio** : Snapshots du portefeuille
- **audit_logs** : Logs d'audit

### Relations
```
strategies (1) ──→ (N) positions
strategies (1) ──→ (N) trades
orders (1) ──→ (N) trades
positions (1) ──→ (N) trades
```

## 🔧 Utilisation

### Gestionnaires persistants

#### OrderManager persistant
```python
from core.order_management.persistent_order_manager import PersistentOrderManager

# Créer le manager
manager = PersistentOrderManager(config)
await manager.start()

# Placer un ordre (sauvegardé automatiquement)
order = await manager.place_order(market_order)

# Récupérer les ordres
orders = await manager.get_active_orders()
```

#### PositionManager persistant
```python
from position.persistent_position_manager import PersistentPositionManager

# Créer le manager
manager = PersistentPositionManager()
await manager.initialize()

# Ouvrir une position (sauvegardée automatiquement)
success = await manager.open_position(allocation)

# Récupérer les positions
positions = await manager.get_open_positions()
```

### APIs historiques

#### Endpoints disponibles
```bash
# Ordres
GET /api/v1/historical/orders
GET /api/v1/historical/orders/{order_id}

# Positions
GET /api/v1/historical/positions

# Trades
GET /api/v1/historical/trades
GET /api/v1/historical/trades/summary

# Portefeuille
GET /api/v1/historical/portfolio/snapshots
GET /api/v1/historical/portfolio/latest
```

#### Exemples de requêtes
```bash
# Récupérer les ordres BTCUSDT
curl "http://localhost:8000/api/v1/historical/orders?symbol=BTCUSDT&limit=100"

# Récupérer les positions ouvertes
curl "http://localhost:8000/api/v1/historical/positions?status=open"

# Résumé des trades des 30 derniers jours
curl "http://localhost:8000/api/v1/historical/trades/summary?start_date=2024-01-01"
```

## 🧪 Tests

### Tests unitaires
```bash
# Tests de base de données
python -m pytest tests/integration/test_postgresql_integration.py -v

# Tests avec couverture
python -m pytest tests/integration/test_postgresql_integration.py --cov=src/database
```

### Tests manuels
```bash
# Test de la base de données
python scripts/database/test_database.py

# Test de santé
curl "http://localhost:8000/api/v1/historical/health"
```

## 📈 Monitoring

### Vérification de santé
```python
from database import get_database_manager

db_manager = get_database_manager()
health = await db_manager.health_check()
print(health)
```

### Métriques disponibles
- Nombre d'ordres par statut
- Nombre de positions ouvertes
- Nombre de trades par période
- Performance des requêtes
- Utilisation de l'espace disque

## 🔒 Sécurité

### Configuration sécurisée
```bash
# Variables d'environnement
POSTGRES_PASSWORD=your_secure_password
POSTGRES_USER=trading_user
POSTGRES_DB=cryptospreadedge
```

### Bonnes pratiques
- Changer les mots de passe par défaut
- Utiliser des connexions chiffrées
- Limiter les accès réseau
- Sauvegarder régulièrement

## 🛠️ Maintenance

### Sauvegarde
```bash
# Sauvegarde complète
docker exec cryptospreadedge-postgres pg_dump -U trading_user cryptospreadedge > backup.sql

# Sauvegarde avec compression
docker exec cryptospreadedge-postgres pg_dump -U trading_user -Z 9 cryptospreadedge > backup.sql.gz
```

### Restauration
```bash
# Restauration depuis un fichier
docker exec -i cryptospreadedge-postgres psql -U trading_user cryptospreadedge < backup.sql

# Restauration avec compression
gunzip -c backup.sql.gz | docker exec -i cryptospreadedge-postgres psql -U trading_user cryptospreadedge
```

### Nettoyage
```python
# Nettoyage automatique des anciens ordres
await order_repo.delete_old_orders(days=30)
```

## 🚨 Dépannage

### Problèmes courants

#### Connexion refusée
```bash
# Vérifier que PostgreSQL est démarré
docker ps | grep postgres

# Vérifier les logs
docker logs cryptospreadedge-postgres
```

#### Erreurs de permissions
```sql
-- Se connecter à PostgreSQL
docker exec -it cryptospreadedge-postgres psql -U trading_user -d cryptospreadedge

-- Accorder les permissions
GRANT ALL PRIVILEGES ON DATABASE cryptospreadedge TO trading_user;
```

#### Performance lente
```sql
-- Analyser les requêtes
EXPLAIN ANALYZE SELECT * FROM orders WHERE symbol = 'BTCUSDT';

-- Vérifier les index
\d+ orders
```

### Logs utiles
```bash
# Logs PostgreSQL
docker logs cryptospreadedge-postgres

# Logs de l'application
docker logs cryptospreadedge-app

# Logs avec suivi en temps réel
docker logs -f cryptospreadedge-postgres
```

## 📚 Documentation complète

- [Intégration PostgreSQL](POSTGRESQL_INTEGRATION.md) - Documentation technique détaillée
- [Architecture des données](ARCHITECTURE.md) - Vue d'ensemble de l'architecture
- [Guide de migration](MIGRATION.md) - Migration depuis l'ancien système

## 🤝 Contribution

### Ajout de nouvelles tables
1. Créer le modèle dans `src/database/models.py`
2. Créer le repository dans `src/database/repositories.py`
3. Ajouter les tests dans `tests/integration/`
4. Mettre à jour la documentation

### Ajout de nouvelles APIs
1. Créer l'endpoint dans `src/api/rest/historical_data_api.py`
2. Ajouter les tests
3. Mettre à jour la documentation API

## 📞 Support

En cas de problème :
1. Vérifier les logs
2. Consulter la documentation
3. Exécuter les tests
4. Créer une issue sur GitHub