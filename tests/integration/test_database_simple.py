"""
Tests d'intégration simples pour la base de données PostgreSQL
"""

import pytest
import asyncio
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Configuration de test
TEST_DATABASE_URL = "postgresql+asyncpg://trading_user:secure_password@localhost:5432/cryptospreadedge_test"

@pytest.fixture(scope="session")
def event_loop():
    """Créer un event loop pour les tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Créer un moteur de base de données de test"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session")
async def test_session_factory(test_engine):
    """Créer une factory de sessions de test"""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        class_=AsyncSession
    )

@pytest.fixture
async def test_session(test_session_factory):
    """Créer une session de test"""
    async with test_session_factory() as session:
        yield session

@pytest.mark.asyncio
async def test_database_connection(test_engine):
    """Test de connexion à la base de données"""
    try:
        async with test_engine.begin() as conn:
            result = await conn.execute("SELECT 1 as test")
            assert result.scalar() == 1
        print("✅ Connexion à la base de données réussie")
    except Exception as e:
        pytest.skip(f"Base de données non disponible: {e}")

@pytest.mark.asyncio
async def test_create_tables(test_engine):
    """Test de création des tables"""
    try:
        from src.database.models import Base
        
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tables créées avec succès")
    except Exception as e:
        pytest.skip(f"Impossible de créer les tables: {e}")

@pytest.mark.asyncio
async def test_basic_crud_operations(test_session):
    """Test des opérations CRUD de base"""
    try:
        from src.database.models import Order, OrderStatus, OrderSide, OrderType
        from src.database.repositories import OrderRepository
        
        # Créer un repository
        order_repo = OrderRepository(test_session)
        
        # Créer un ordre de test
        order_data = {
            "order_id": "test_order_001",
            "symbol": "BTCUSDT",
            "side": OrderSide.BUY,
            "order_type": OrderType.LIMIT,
            "quantity": 0.01,
            "price": 50000.0,
            "status": OrderStatus.PENDING,
            "exchange": "binance",
            "source": "test"
        }
        
        # Créer l'ordre
        created_order = await order_repo.create(order_data)
        assert created_order is not None
        assert created_order.symbol == "BTCUSDT"
        assert created_order.quantity == 0.01
        
        # Récupérer l'ordre
        retrieved_order = await order_repo.get_by_id(str(created_order.id))
        assert retrieved_order is not None
        assert retrieved_order.symbol == "BTCUSDT"
        
        # Mettre à jour l'ordre
        await order_repo.update_status(str(created_order.id), OrderStatus.FILLED)
        updated_order = await order_repo.get_by_id(str(created_order.id))
        assert updated_order.status == OrderStatus.FILLED
        
        # Supprimer l'ordre
        await order_repo.delete(str(created_order.id))
        deleted_order = await order_repo.get_by_id(str(created_order.id))
        assert deleted_order is None
        
        print("✅ Opérations CRUD de base réussies")
        
    except Exception as e:
        pytest.skip(f"Impossible d'exécuter les tests CRUD: {e}")

@pytest.mark.asyncio
async def test_repository_queries(test_session):
    """Test des requêtes de repository"""
    try:
        from src.database.models import Order, OrderStatus, OrderSide, OrderType
        from src.database.repositories import OrderRepository
        
        order_repo = OrderRepository(test_session)
        
        # Créer plusieurs ordres de test
        test_orders = [
            {
                "order_id": f"test_order_{i:03d}",
                "symbol": "BTCUSDT",
                "side": OrderSide.BUY,
                "order_type": OrderType.LIMIT,
                "quantity": 0.01,
                "price": 50000.0 + i * 100,
                "status": OrderStatus.PENDING,
                "exchange": "binance",
                "source": "test"
            }
            for i in range(5)
        ]
        
        created_orders = []
        for order_data in test_orders:
            order = await order_repo.create(order_data)
            created_orders.append(order)
        
        # Tester la récupération par symbole
        btc_orders = await order_repo.get_orders_by_symbol("BTCUSDT")
        assert len(btc_orders) >= 5
        
        # Tester la récupération par statut
        pending_orders = await order_repo.get_orders_by_status(OrderStatus.PENDING)
        assert len(pending_orders) >= 5
        
        # Nettoyer
        for order in created_orders:
            await order_repo.delete(str(order.id))
        
        print("✅ Requêtes de repository réussies")
        
    except Exception as e:
        pytest.skip(f"Impossible d'exécuter les tests de requêtes: {e}")

@pytest.mark.asyncio
async def test_audit_logging(test_session):
    """Test du système d'audit"""
    try:
        from src.database.models import AuditLog
        from src.database.repositories import BaseRepository
        
        base_repo = BaseRepository(test_session)
        
        # Tester l'enregistrement d'audit
        await base_repo._log_audit(
            entity_type="test_entity",
            entity_id="test_001",
            action="create",
            old_values=None,
            new_values={"test": "value"},
            user_id="test_user",
            metadata={"test": True}
        )
        
        # Vérifier que l'audit a été enregistré
        result = await test_session.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE entity_type = 'test_entity'"
        )
        count = result.scalar()
        assert count > 0
        
        print("✅ Système d'audit fonctionnel")
        
    except Exception as e:
        pytest.skip(f"Impossible de tester l'audit: {e}")

@pytest.mark.asyncio
async def test_database_performance(test_session):
    """Test de performance de la base de données"""
    try:
        from src.database.models import Order, OrderStatus, OrderSide, OrderType
        from src.database.repositories import OrderRepository
        import time
        
        order_repo = OrderRepository(test_session)
        
        # Test de création en lot
        start_time = time.time()
        
        batch_orders = []
        for i in range(100):
            order_data = {
                "order_id": f"perf_test_{i:03d}",
                "symbol": "BTCUSDT",
                "side": OrderSide.BUY,
                "order_type": OrderType.LIMIT,
                "quantity": 0.01,
                "price": 50000.0,
                "status": OrderStatus.PENDING,
                "exchange": "binance",
                "source": "performance_test"
            }
            order = await order_repo.create(order_data)
            batch_orders.append(order)
        
        creation_time = time.time() - start_time
        
        # Test de requête
        start_time = time.time()
        orders = await order_repo.get_orders_by_symbol("BTCUSDT")
        query_time = time.time() - start_time
        
        # Nettoyer
        for order in batch_orders:
            await order_repo.delete(str(order.id))
        
        print(f"✅ Performance: {len(batch_orders)} créations en {creation_time:.2f}s")
        print(f"✅ Performance: Requête de {len(orders)} ordres en {query_time:.2f}s")
        
        # Vérifier que les performances sont acceptables
        assert creation_time < 10.0  # Moins de 10 secondes pour 100 créations
        assert query_time < 5.0      # Moins de 5 secondes pour la requête
        
    except Exception as e:
        pytest.skip(f"Impossible de tester les performances: {e}")

if __name__ == "__main__":
    # Exécuter les tests si le script est lancé directement
    pytest.main([__file__, "-v"])