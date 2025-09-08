-- Script d'initialisation de la base de données CryptoSpreadEdge
-- Ce script est exécuté automatiquement au démarrage du conteneur PostgreSQL

-- Créer l'extension pour les UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Créer l'extension pour les données JSON
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Créer l'extension pour les index GIN sur JSONB
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Créer un schéma pour les données de trading
CREATE SCHEMA IF NOT EXISTS trading;

-- Créer un utilisateur dédié pour les applications (si pas déjà créé)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'trading_user') THEN
        CREATE ROLE trading_user WITH LOGIN PASSWORD 'secure_password';
    END IF;
END
$$;

-- Accorder les permissions
GRANT ALL PRIVILEGES ON DATABASE cryptospreadedge TO trading_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON SCHEMA trading TO trading_user;

-- Créer des types personnalisés si nécessaire
DO $$
BEGIN
    -- Type pour les statuts d'ordres
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') THEN
        CREATE TYPE order_status AS ENUM (
            'pending', 'open', 'filled', 'cancelled', 'rejected', 'partially_filled'
        );
    END IF;
    
    -- Type pour les côtés d'ordres
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_side') THEN
        CREATE TYPE order_side AS ENUM ('buy', 'sell');
    END IF;
    
    -- Type pour les types d'ordres
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_type') THEN
        CREATE TYPE order_type AS ENUM ('market', 'limit', 'stop', 'stop_limit');
    END IF;
    
    -- Type pour les types de positions
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'position_type') THEN
        CREATE TYPE position_type AS ENUM ('long', 'short');
    END IF;
    
    -- Type pour les statuts de positions
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'position_status') THEN
        CREATE TYPE position_status AS ENUM (
            'pending', 'open', 'closed', 'cancelled'
        );
    END IF;
    
    -- Type pour les statuts de stratégies
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'strategy_status') THEN
        CREATE TYPE strategy_status AS ENUM (
            'active', 'inactive', 'paused', 'error'
        );
    END IF;
END
$$;

-- Accorder l'usage des types à l'utilisateur
GRANT USAGE ON TYPE order_status TO trading_user;
GRANT USAGE ON TYPE order_side TO trading_user;
GRANT USAGE ON TYPE order_type TO trading_user;
GRANT USAGE ON TYPE position_type TO trading_user;
GRANT USAGE ON TYPE position_status TO trading_user;
GRANT USAGE ON TYPE strategy_status TO trading_user;

-- Créer des vues utiles pour les requêtes fréquentes
CREATE OR REPLACE VIEW active_orders AS
SELECT 
    o.*,
    s.name as strategy_name
FROM orders o
LEFT JOIN strategies s ON o.strategy_id = s.id
WHERE o.status IN ('pending', 'open', 'partially_filled');

CREATE OR REPLACE VIEW open_positions AS
SELECT 
    p.*,
    s.name as strategy_name
FROM positions p
LEFT JOIN strategies s ON p.strategy_id = s.id
WHERE p.status = 'open';

CREATE OR REPLACE VIEW recent_trades AS
SELECT 
    t.*,
    s.name as strategy_name,
    o.order_id
FROM trades t
LEFT JOIN strategies s ON t.strategy_id = s.id
LEFT JOIN orders o ON t.order_id = o.id
WHERE t.executed_at >= NOW() - INTERVAL '24 hours'
ORDER BY t.executed_at DESC;

-- Créer des index pour optimiser les performances
-- (Les index seront créés automatiquement par SQLAlchemy, mais on peut en ajouter d'autres)

-- Index composite pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_orders_symbol_status_created 
ON orders (symbol, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_positions_symbol_status_opened 
ON positions (symbol, status, opened_at DESC);

CREATE INDEX IF NOT EXISTS idx_trades_symbol_executed 
ON trades (symbol, executed_at DESC);

-- Index sur les champs JSONB pour les requêtes sur les métadonnées
CREATE INDEX IF NOT EXISTS idx_orders_metadata_gin 
ON orders USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_positions_metadata_gin 
ON positions USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_trades_metadata_gin 
ON trades USING GIN (metadata);

-- Accorder les permissions sur les vues
GRANT SELECT ON active_orders TO trading_user;
GRANT SELECT ON open_positions TO trading_user;
GRANT SELECT ON recent_trades TO trading_user;

-- Message de confirmation
DO $$
BEGIN
    RAISE NOTICE 'Base de données CryptoSpreadEdge initialisée avec succès!';
    RAISE NOTICE 'Utilisateur: trading_user';
    RAISE NOTICE 'Base de données: cryptospreadedge';
    RAISE NOTICE 'Extensions: uuid-ossp, btree_gin';
    RAISE NOTICE 'Vues créées: active_orders, open_positions, recent_trades';
END
$$;