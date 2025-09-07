"""
API REST pour les données historiques de trading
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_database_manager, OrderRepository, PositionRepository, TradeRepository, PortfolioRepository
from ...database.models import OrderStatus, PositionStatus, StrategyStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/historical", tags=["historical-data"])


# Modèles de réponse
class OrderResponse(BaseModel):
    id: str
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    status: str
    filled_quantity: float
    average_price: float
    exchange: str
    created_at: datetime
    updated_at: datetime
    filled_at: Optional[datetime]
    cancelled_at: Optional[datetime]


class PositionResponse(BaseModel):
    id: str
    symbol: str
    side: str
    quantity: float
    average_price: float
    current_price: Optional[float]
    unrealized_pnl: float
    realized_pnl: float
    status: str
    exchange: str
    strategy_name: Optional[str]
    opened_at: datetime
    closed_at: Optional[datetime]
    updated_at: datetime


class TradeResponse(BaseModel):
    id: str
    trade_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    fees: float
    pnl: float
    net_pnl: float
    exchange: str
    strategy_name: Optional[str]
    executed_at: datetime
    signal_strength: Optional[float]
    signal_confidence: Optional[float]
    exit_reason: Optional[str]


class PortfolioSnapshotResponse(BaseModel):
    id: str
    total_value: float
    cash_balance: float
    invested_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_fees: float
    active_positions: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    timestamp: datetime


class TradingSummaryResponse(BaseModel):
    total_trades: int
    total_pnl: float
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_pnl: float
    best_trade: float
    worst_trade: float
    total_fees: float
    period_start: datetime
    period_end: datetime


# Dépendances
async def get_db_session():
    """Obtient une session de base de données"""
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        yield session


# Endpoints pour les ordres
@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    exchange: Optional[str] = Query(None, description="Filtrer par exchange"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'ordres"),
    offset: int = Query(0, ge=0, description="Décalage"),
    session: AsyncSession = Depends(get_db_session)
):
    """Récupère les ordres historiques"""
    try:
        order_repo = OrderRepository(session)
        
        # Construire les conditions de filtrage
        conditions = []
        if symbol:
            conditions.append(Order.symbol == symbol)
        if status:
            conditions.append(Order.status == OrderStatus(status))
        if exchange:
            conditions.append(Order.exchange == exchange)
        if start_date:
            conditions.append(Order.created_at >= start_date)
        if end_date:
            conditions.append(Order.created_at <= end_date)
        
        # Récupérer les ordres
        if conditions:
            # Implémentation simplifiée - à adapter selon vos besoins
            orders = await order_repo.get_by_symbol(symbol or "BTCUSDT", limit)
        else:
            orders = await order_repo.get_by_symbol("BTCUSDT", limit)
        
        return [OrderResponse(
            id=str(order.id),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side.value,
            order_type=order.order_type.value,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
            status=order.status.value,
            filled_quantity=order.filled_quantity,
            average_price=order.average_price,
            exchange=order.exchange,
            created_at=order.created_at,
            updated_at=order.updated_at,
            filled_at=order.filled_at,
            cancelled_at=order.cancelled_at
        ) for order in orders]
        
    except Exception as e:
        logger.error(f"Erreur récupération ordres: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération ordres")


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Récupère un ordre spécifique"""
    try:
        order_repo = OrderRepository(session)
        order = await order_repo.get_by_id(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Ordre non trouvé")
        
        return OrderResponse(
            id=str(order.id),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side.value,
            order_type=order.order_type.value,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
            status=order.status.value,
            filled_quantity=order.filled_quantity,
            average_price=order.average_price,
            exchange=order.exchange,
            created_at=order.created_at,
            updated_at=order.updated_at,
            filled_at=order.filled_at,
            cancelled_at=order.cancelled_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération ordre {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération ordre")


# Endpoints pour les positions
@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    strategy_id: Optional[str] = Query(None, description="Filtrer par stratégie"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de positions"),
    session: AsyncSession = Depends(get_db_session)
):
    """Récupère les positions historiques"""
    try:
        position_repo = PositionRepository(session)
        
        if symbol:
            positions = await position_repo.get_by_symbol(symbol)
        else:
            positions = await position_repo.get_open_positions()
        
        # Appliquer les filtres supplémentaires
        if status:
            positions = [p for p in positions if p.status.value == status]
        if strategy_id:
            positions = [p for p in positions if str(p.strategy_id) == strategy_id]
        
        # Limiter les résultats
        positions = positions[:limit]
        
        return [PositionResponse(
            id=str(position.id),
            symbol=position.symbol,
            side=position.side.value,
            quantity=position.quantity,
            average_price=position.average_price,
            current_price=position.current_price,
            unrealized_pnl=position.unrealized_pnl,
            realized_pnl=position.realized_pnl,
            status=position.status.value,
            exchange=position.exchange,
            strategy_name=position.strategy.name if position.strategy else None,
            opened_at=position.opened_at,
            closed_at=position.closed_at,
            updated_at=position.updated_at
        ) for position in positions]
        
    except Exception as e:
        logger.error(f"Erreur récupération positions: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération positions")


# Endpoints pour les trades
@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    strategy_id: Optional[str] = Query(None, description="Filtrer par stratégie"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de trades"),
    session: AsyncSession = Depends(get_db_session)
):
    """Récupère les trades historiques"""
    try:
        trade_repo = TradeRepository(session)
        
        if symbol:
            trades = await trade_repo.get_by_symbol(symbol, limit)
        elif strategy_id:
            trades = await trade_repo.get_by_strategy(strategy_id, limit)
        else:
            trades = await trade_repo.get_by_symbol("BTCUSDT", limit)
        
        return [TradeResponse(
            id=str(trade.id),
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            side=trade.side.value,
            quantity=trade.quantity,
            price=trade.price,
            fees=trade.fees,
            pnl=trade.pnl,
            net_pnl=trade.net_pnl,
            exchange=trade.exchange,
            strategy_name=trade.strategy.name if trade.strategy else None,
            executed_at=trade.executed_at,
            signal_strength=trade.signal_strength,
            signal_confidence=trade.signal_confidence,
            exit_reason=trade.exit_reason
        ) for trade in trades]
        
    except Exception as e:
        logger.error(f"Erreur récupération trades: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération trades")


@router.get("/trades/summary", response_model=TradingSummaryResponse)
async def get_trading_summary(
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    session: AsyncSession = Depends(get_db_session)
):
    """Récupère un résumé des trades"""
    try:
        trade_repo = TradeRepository(session)
        
        # Utiliser les dates par défaut si non fournies
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        summary = await trade_repo.get_trades_summary(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        return TradingSummaryResponse(
            total_trades=summary.get("total_trades", 0),
            total_pnl=summary.get("total_pnl", 0.0),
            winning_trades=summary.get("winning_trades", 0),
            losing_trades=summary.get("losing_trades", 0),
            win_rate=summary.get("win_rate", 0.0),
            avg_pnl=summary.get("avg_pnl", 0.0),
            best_trade=0.0,  # À calculer
            worst_trade=0.0,  # À calculer
            total_fees=0.0,  # À calculer
            period_start=start_date,
            period_end=end_date
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération résumé trades: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération résumé trades")


# Endpoints pour le portefeuille
@router.get("/portfolio/snapshots", response_model=List[PortfolioSnapshotResponse])
async def get_portfolio_snapshots(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de snapshots"),
    session: AsyncSession = Depends(get_db_session)
):
    """Récupère les snapshots du portefeuille"""
    try:
        portfolio_repo = PortfolioRepository(session)
        snapshots = await portfolio_repo.get_historical_snapshots(days)
        
        # Limiter les résultats
        snapshots = snapshots[:limit]
        
        return [PortfolioSnapshotResponse(
            id=str(snapshot.id),
            total_value=snapshot.total_value,
            cash_balance=snapshot.cash_balance,
            invested_value=snapshot.invested_value,
            unrealized_pnl=snapshot.unrealized_pnl,
            realized_pnl=snapshot.realized_pnl,
            total_fees=snapshot.total_fees,
            active_positions=snapshot.active_positions,
            total_trades=snapshot.total_trades,
            winning_trades=snapshot.winning_trades,
            losing_trades=snapshot.losing_trades,
            win_rate=snapshot.win_rate,
            max_drawdown=snapshot.max_drawdown,
            sharpe_ratio=snapshot.sharpe_ratio,
            timestamp=snapshot.timestamp
        ) for snapshot in snapshots]
        
    except Exception as e:
        logger.error(f"Erreur récupération snapshots portefeuille: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération snapshots portefeuille")


@router.get("/portfolio/latest", response_model=PortfolioSnapshotResponse)
async def get_latest_portfolio_snapshot(
    session: AsyncSession = Depends(get_db_session)
):
    """Récupère le dernier snapshot du portefeuille"""
    try:
        portfolio_repo = PortfolioRepository(session)
        snapshot = await portfolio_repo.get_latest_snapshot()
        
        if not snapshot:
            raise HTTPException(status_code=404, detail="Aucun snapshot trouvé")
        
        return PortfolioSnapshotResponse(
            id=str(snapshot.id),
            total_value=snapshot.total_value,
            cash_balance=snapshot.cash_balance,
            invested_value=snapshot.invested_value,
            unrealized_pnl=snapshot.unrealized_pnl,
            realized_pnl=snapshot.realized_pnl,
            total_fees=snapshot.total_fees,
            active_positions=snapshot.active_positions,
            total_trades=snapshot.total_trades,
            winning_trades=snapshot.winning_trades,
            losing_trades=snapshot.losing_trades,
            win_rate=snapshot.win_rate,
            max_drawdown=snapshot.max_drawdown,
            sharpe_ratio=snapshot.sharpe_ratio,
            timestamp=snapshot.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération dernier snapshot: {e}")
        raise HTTPException(status_code=500, detail="Erreur récupération dernier snapshot")


# Endpoint de santé
@router.get("/health")
async def health_check():
    """Vérifie la santé de l'API des données historiques"""
    try:
        db_manager = get_database_manager()
        health = await db_manager.health_check()
        
        return {
            "status": "healthy" if health["status"] == "healthy" else "unhealthy",
            "database": health,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }