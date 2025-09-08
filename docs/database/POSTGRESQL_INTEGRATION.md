# Intégration PostgreSQL - CryptoSpreadEdge

## Vue d'ensemble

Ce document décrit l'intégration de PostgreSQL dans l'architecture CryptoSpreadEdge pour la persistance des données de trading critiques.

## Architecture de données

### Stack de données hybride

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │    InfluxDB     │    │     Redis       │
│  (Relationnel)  │    │  (Time-series)  │    │    (Cache)      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Ordres        │    │ • Prix temps    │    │ • Sessions      │
│ • Positions     │    │ • Indicateurs   │    │ • Cache API     │
│ • Trades        │    │ • Métriques     │    │ • Pub/Sub       │
│ • Stratégies    │    │ • Analytics     │    │ • Queues        │
│ • Portefeuille  │    │ • Monitoring    │    │                 │
│ • Audit         │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Modèles de données

#### Ordres (Orders)
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side order_side NOT NULL,
    order_type order_type NOT NULL,
    quantity FLOAT NOT NULL,
    price FLOAT,
    stop_price FLOAT,
    status order_status NOT NULL,
    filled_quantity FLOAT DEFAULT 0.0,
    average_price FLOAT DEFAULT 0.0,
    exchange VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    filled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    metadata JSONB
);
```

#### Positions (Positions)
```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side position_type NOT NULL,
    quantity FLOAT NOT NULL,
    average_price FLOAT NOT NULL,
    current_price FLOAT,
    unrealized_pnl FLOAT DEFAULT 0.0,
    realized_pnl FLOAT DEFAULT 0.0,
    status position_status NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    strategy_id UUID REFERENCES strategies(id),
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

#### Trades (Trades)
```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY,
    trade_id VARCHAR(100) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side order_side NOT NULL,
    quantity FLOAT NOT NULL,
    price FLOAT NOT NULL,
    fees FLOAT DEFAULT 0.0,
    pnl FLOAT DEFAULT 0.0,
    net_pnl FLOAT DEFAULT 0.0,
    order_id UUID REFERENCES orders(id),
    position_id UUID REFERENCES positions(id),
    strategy_id UUID REFERENCES strategies(id),
    exchange VARCHAR(50) NOT NULL,
    executed_at TIMESTAMP DEFAULT NOW(),
    signal_strength FLOAT,
    signal_confidence FLOAT,
    exit_reason VARCHAR(100),
    metadata JSONB
);
```

## Configuration

### Variables d'environnement

```bash
# PostgreSQL
POSTGRES_URL=postgresql://trading_user:secure_password@localhost:5432/cryptospreadedge
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cryptospreadedge
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=secure_password
```

### Docker Compose

```yaml
postgres:
  image: postgres:15-alpine
  container_name: cryptospreadedge-postgres
  restart: unless-stopped
  ports:
    - "5432:5432"
  environment:
    - POSTGRES_DB=cryptospreadedge
    - POSTGRES_USER=trading_user
    - POSTGRES_PASSWORD=secure_password
    - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./init-scripts:/docker-entrypoint-initdb.d
  networks:
    - cryptospreadedge-network
```

## Utilisation

### Initialisation

```python
from database import init_database, get_database_manager

# Initialiser la base de données
db_manager = await init_database()

# Utiliser dans vos managers
async with db_manager.get_session() as session:
    order_repo = OrderRepository(session)
    # ... vos opérations
```

### Gestionnaires persistants

#### OrderManager persistant
```python
from core.order_management.persistent_order_manager import PersistentOrderManager

manager = PersistentOrderManager(config)
await manager.start()

# Placer un ordre (sauvegardé automatiquement)
order = await manager.place_order(market_order)
```

#### PositionManager persistant
```python
from position.persistent_position_manager import PersistentPositionManager

manager = PersistentPositionManager()
await manager.initialize()

# Ouvrir une position (sauvegardée automatiquement)
success = await manager.open_position(allocation)
```

### APIs historiques

#### Récupérer les ordres
```bash
GET /api/v1/historical/orders?symbol=BTCUSDT&limit=100
```

#### Récupérer les positions
```bash
GET /api/v1/historical/positions?status=open
```

#### Récupérer les trades
```bash
GET /api/v1/historical/trades?symbol=BTCUSDT&start_date=2024-01-01
```

#### Résumé du trading
```bash
GET /api/v1/historical/trades/summary?symbol=BTCUSDT&start_date=2024-01-01
```

## Scripts utilitaires

### Initialisation
```bash
python scripts/database/init_database.py
```

### Test de la base
```bash
python scripts/database/test_database.py
```

### Migration (à venir)
```bash
alembic upgrade head
```

## Monitoring et maintenance

### Vérification de santé
```python
health = await db_manager.health_check()
print(health)
```

### Nettoyage automatique
- Suppression des ordres anciens (> 30 jours)
- Archivage des trades anciens
- Optimisation des index

### Sauvegarde
```bash
# Sauvegarde complète
docker exec cryptospreadedge-postgres pg_dump -U trading_user cryptospreadedge > backup.sql

# Restauration
docker exec -i cryptospreadedge-postgres psql -U trading_user cryptospreadedge < backup.sql
```

## Performance

### Index optimisés
- Index composite sur (symbol, status, created_at)
- Index GIN sur les champs JSONB
- Index sur les clés étrangères

### Requêtes optimisées
- Pagination automatique
- Filtrage efficace
- Vues matérialisées pour les requêtes fréquentes

## Sécurité

### Chiffrement
- Connexions TLS/SSL
- Chiffrement des données sensibles
- Rotation des mots de passe

### Audit
- Logs de toutes les opérations
- Traçabilité complète
- Conformité réglementaire

## Migration depuis l'ancien système

### Étapes de migration
1. **Phase 1** : Ajout de PostgreSQL en parallèle
2. **Phase 2** : Migration des données existantes
3. **Phase 3** : Basculement vers les managers persistants
4. **Phase 4** : Suppression de l'ancien système

### Scripts de migration
```python
# Migration des ordres existants
async def migrate_orders():
    # Récupérer depuis l'ancien système
    # Convertir et insérer en PostgreSQL
    pass
```

## Dépannage

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
-- Accorder les permissions
GRANT ALL PRIVILEGES ON DATABASE cryptospreadedge TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
```

#### Performance lente
```sql
-- Analyser les requêtes lentes
EXPLAIN ANALYZE SELECT * FROM orders WHERE symbol = 'BTCUSDT';

-- Vérifier les index
\d+ orders
```

## Évolutions futures

### Fonctionnalités prévues
- Réplication en lecture
- Partitioning par date
- Compression des données anciennes
- Intégration avec des outils BI
- Alertes automatiques
- Dashboards avancés

### Optimisations
- Connection pooling avancé
- Cache de requêtes
- Requêtes asynchrones optimisées
- Compression des données