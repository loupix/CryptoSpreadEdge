"""
Tests d'intégration PostgreSQL
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from database import get_database_manager, OrderRepository, PositionRepository, TradeRepository
from database.models import OrderStatus, OrderSide, OrderType, PositionStatus, PositionType
from src.core.order_management.persistent_order_manager import PersistentOrderManager, OrderManagerConfig
from src.position.persistent_position_manager import PersistentPositionManager


@pytest.fixture
async def db_manager():
    """Fixture pour le gestionnaire de base de données"""
    manager = get_database_manager()
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.fixture
async def db_session(db_manager):
    """Fixture pour la session de base de données"""
    async with db_manager.get_session() as session:
        yield session


@pytest.mark.asyncio
async def test_database_initialization(db_manager):
    """Test l'initialisation de la base de données"""
    health = await db_manager.health_check()
    assert health["status"] == "healthy"
    assert "tables_stats" in health


@pytest.mark.asyncio
async def test_order_crud_operations(db_session):
    """Test les opérations CRUD sur les ordres"""
    order_repo = OrderRepository(db_session)
    
    # Créer un ordre
    order_data = {
        "order_id": "TEST_ORD_001",
        "symbol": "BTCUSDT",
        "side": OrderSide.BUY,
        "order_type": OrderType.LIMIT,
        "quantity": 0.001,
        "price": 50000.0,
        "status": OrderStatus.PENDING,
        "exchange": "test",
        "source": "test"
    }
    
    order = await order_repo.create(order_data)
    assert order.order_id == "TEST_ORD_001"
    assert order.symbol == "BTCUSDT"
    assert order.status == OrderStatus.PENDING
    
    # Récupérer l'ordre
    retrieved_order = await order_repo.get_by_id("TEST_ORD_001")
    assert retrieved_order is not None
    assert retrieved_order.symbol == "BTCUSDT"
    
    # Mettre à jour le statut
    success = await order_repo.update_status(
        "TEST_ORD_001", 
        OrderStatus.FILLED, 
        0.001, 
        50000.0
    )
    assert success
    
    # Vérifier la mise à jour
    updated_order = await order_repo.get_by_id("TEST_ORD_001")
    assert updated_order.status == OrderStatus.FILLED
    assert updated_order.filled_quantity == 0.001


@pytest.mark.asyncio
async def test_position_crud_operations(db_session):
    """Test les opérations CRUD sur les positions"""
    position_repo = PositionRepository(db_session)
    
    # Créer une position
    position_data = {
        "symbol": "BTCUSDT",
        "side": PositionType.LONG,
        "quantity": 0.001,
        "average_price": 50000.0,
        "current_price": 50000.0,
        "unrealized_pnl": 0.0,
        "realized_pnl": 0.0,
        "status": PositionStatus.OPEN,
        "exchange": "test"
    }
    
    position = await position_repo.create(position_data)
    assert position.symbol == "BTCUSDT"
    assert position.side == PositionType.LONG
    assert position.status == PositionStatus.OPEN
    
    # Récupérer les positions ouvertes
    open_positions = await position_repo.get_open_positions()
    assert len(open_positions) >= 1
    
    # Mettre à jour le PnL
    success = await position_repo.update_pnl(
        str(position.id), 
        51000.0, 
        1.0  # PnL de 1 USDT
    )
    assert success
    
    # Fermer la position
    success = await position_repo.close_position(str(position.id), 1.0)
    assert success


@pytest.mark.asyncio
async def test_trade_crud_operations(db_session):
    """Test les opérations CRUD sur les trades"""
    trade_repo = TradeRepository(db_session)
    
    # Créer un trade
    trade_data = {
        "trade_id": "TEST_TRD_001",
        "symbol": "BTCUSDT",
        "side": OrderSide.BUY,
        "quantity": 0.001,
        "price": 50000.0,
        "fees": 0.05,
        "pnl": 0.0,
        "net_pnl": -0.05,
        "exchange": "test",
        "executed_at": datetime.utcnow()
    }
    
    trade = await trade_repo.create(trade_data)
    assert trade.trade_id == "TEST_TRD_001"
    assert trade.symbol == "BTCUSDT"
    assert trade.net_pnl == -0.05
    
    # Récupérer les trades
    trades = await trade_repo.get_by_symbol("BTCUSDT")
    assert len(trades) >= 1
    
    # Test du résumé
    summary = await trade_repo.get_trades_summary()
    assert "total_trades" in summary
    assert "total_pnl" in summary


@pytest.mark.asyncio
async def test_persistent_order_manager(db_manager):
    """Test du gestionnaire d'ordres persistant"""
    config = OrderManagerConfig()
    manager = PersistentOrderManager(config)
    
    # Mock du connecteur
    mock_connector = AsyncMock()
    mock_connector.get_name.return_value = "test_exchange"
    mock_connector.place_order.return_value = MagicMock(
        order_id="MOCK_ORD_001",
        symbol="BTCUSDT",
        side="buy",
        quantity=0.001,
        price=50000.0,
        filled_quantity=0.001,
        average_price=50000.0,
        source="test_exchange"
    )
    
    manager.register_connector("test", mock_connector)
    await manager.start()
    
    # Créer un ordre de test
    from connectors.common.market_data_types import Order as MarketOrder
    
    market_order = MarketOrder(
        symbol="BTCUSDT",
        side="buy",
        quantity=0.001,
        order_type="limit",
        price=50000.0,
        source="test_exchange"
    )
    
    # Placer l'ordre
    placed_order = await manager.place_order(market_order)
    assert placed_order is not None
    assert placed_order.symbol == "BTCUSDT"
    
    # Récupérer l'ordre depuis la base
    retrieved_order = await manager.get_order(placed_order.order_id)
    assert retrieved_order is not None
    assert retrieved_order.symbol == "BTCUSDT"
    
    await manager.stop()


@pytest.mark.asyncio
async def test_persistent_position_manager(db_manager):
    """Test du gestionnaire de positions persistant"""
    manager = PersistentPositionManager()
    await manager.initialize()
    
    # Créer une allocation de test
    from prediction.signal_generator import TradingSignal, SignalType
    
    signal = TradingSignal(
        symbol="BTCUSDT",
        signal_type=SignalType.BUY,
        price=50000.0,
        confidence=0.8,
        strength=0.7
    )
    
    # Ajouter une demande de position
    success = await manager.add_position_request(signal, "percentage", 3)
    assert success
    
    # Traiter les demandes
    allocations = await manager.process_position_requests()
    assert len(allocations) >= 1
    
    # Ouvrir une position
    if allocations:
        allocation = allocations[0]
        success = await manager.open_position(allocation)
        assert success
        
        # Vérifier que la position est ouverte
        open_positions = await manager.get_open_positions()
        assert len(open_positions) >= 1


@pytest.mark.asyncio
async def test_historical_data_api(db_session):
    """Test de l'API des données historiques"""
    from api.rest.historical_data_api import OrderRepository, PositionRepository, TradeRepository
    
    # Test des repositories via l'API
    order_repo = OrderRepository(db_session)
    position_repo = PositionRepository(db_session)
    trade_repo = TradeRepository(db_session)
    
    # Créer des données de test
    order_data = {
        "order_id": "API_TEST_ORD_001",
        "symbol": "ETHUSDT",
        "side": OrderSide.SELL,
        "order_type": OrderType.MARKET,
        "quantity": 0.1,
        "status": OrderStatus.FILLED,
        "filled_quantity": 0.1,
        "average_price": 3000.0,
        "exchange": "test",
        "source": "test"
    }
    
    order = await order_repo.create(order_data)
    
    # Test des requêtes par symbole
    orders = await order_repo.get_by_symbol("ETHUSDT")
    assert len(orders) >= 1
    
    # Test des ordres actifs
    active_orders = await order_repo.get_active_orders()
    # Peut être vide selon les données de test
    
    # Test des positions
    position_data = {
        "symbol": "ETHUSDT",
        "side": PositionType.SHORT,
        "quantity": 0.1,
        "average_price": 3000.0,
        "status": PositionStatus.OPEN,
        "exchange": "test"
    }
    
    position = await position_repo.create(position_data)
    open_positions = await position_repo.get_open_positions("ETHUSDT")
    assert len(open_positions) >= 1


@pytest.mark.asyncio
async def test_database_health_check(db_manager):
    """Test de la vérification de santé de la base de données"""
    health = await db_manager.health_check()
    
    assert "status" in health
    assert health["status"] in ["healthy", "unhealthy"]
    
    if health["status"] == "healthy":
        assert "tables_stats" in health
        assert "database_url" in health


@pytest.mark.asyncio
async def test_concurrent_operations(db_manager):
    """Test des opérations concurrentes"""
    async def create_order(session, order_id_suffix):
        order_repo = OrderRepository(session)
        order_data = {
            "order_id": f"CONCURRENT_ORD_{order_id_suffix}",
            "symbol": "BTCUSDT",
            "side": OrderSide.BUY,
            "order_type": OrderType.LIMIT,
            "quantity": 0.001,
            "price": 50000.0,
            "status": OrderStatus.PENDING,
            "exchange": "test",
            "source": "test"
        }
        return await order_repo.create(order_data)
    
    # Créer plusieurs ordres en parallèle
    tasks = []
    for i in range(5):
        async with db_manager.get_session() as session:
            task = create_order(session, i)
            tasks.append(task)
    
    orders = await asyncio.gather(*tasks)
    
    # Vérifier que tous les ordres ont été créés
    assert len(orders) == 5
    for i, order in enumerate(orders):
        assert order.order_id == f"CONCURRENT_ORD_{i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])