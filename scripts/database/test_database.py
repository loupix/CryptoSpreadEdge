#!/usr/bin/env python3
"""
Script de test de la base de données PostgreSQL
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from database import get_database_manager, OrderRepository, PositionRepository, TradeRepository
from database.models import OrderStatus, OrderSide, OrderType, PositionStatus, PositionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database():
    """Test complet de la base de données"""
    try:
        logger.info("Démarrage des tests de base de données...")
        
        db_manager = get_database_manager()
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            # Test des ordres
            logger.info("Test des ordres...")
            order_repo = OrderRepository(session)
            
            # Créer un ordre de test
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
            logger.info(f"Ordre créé: {order.order_id}")
            
            # Récupérer l'ordr
            retrieved_order = await order_repo.get_by_id("TEST_ORD_001")
            assert retrieved_order is not None
            logger.info(f"Ordre récupéré: {retrieved_order.symbol}")
            
            # Mettre à jour le statut
            await order_repo.update_status("TEST_ORD_001", OrderStatus.FILLED, 0.001, 50000.0)
            logger.info("Statut de l'ordre mis à jour")
            
            # Test des positions
            logger.info("Test des positions...")
            position_repo = PositionRepository(session)
            
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
            logger.info(f"Position créée: {position.symbol}")
            
            # Récupérer les positions ouvertes
            open_positions = await position_repo.get_open_positions()
            logger.info(f"Positions ouvertes: {len(open_positions)}")
            
            # Test des trades
            logger.info("Test des trades...")
            trade_repo = TradeRepository(session)
            
            trade_data = {
                "trade_id": "TEST_TRD_001",
                "symbol": "BTCUSDT",
                "side": OrderSide.BUY,
                "quantity": 0.001,
                "price": 50000.0,
                "fees": 0.05,
                "pnl": 0.0,
                "net_pnl": -0.05,
                "order_id": str(order.id),
                "position_id": str(position.id),
                "exchange": "test",
                "executed_at": datetime.utcnow()
            }
            
            trade = await trade_repo.create(trade_data)
            logger.info(f"Trade créé: {trade.trade_id}")
            
            # Récupérer les trades
            trades = await trade_repo.get_by_symbol("BTCUSDT")
            logger.info(f"Trades récupérés: {len(trades)}")
            
            # Test du résumé
            summary = await trade_repo.get_trades_summary()
            logger.info(f"Résumé des trades: {summary}")
            
        # Test de santé
        health = await db_manager.health_check()
        logger.info(f"État de la base de données: {health}")
        
        await db_manager.close()
        
        logger.info("Tous les tests sont passés avec succès!")
        
    except Exception as e:
        logger.error(f"Erreur lors des tests: {e}")
        raise


async def main():
    """Fonction principale"""
    try:
        await test_database()
    except Exception as e:
        logger.error(f"Échec des tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())