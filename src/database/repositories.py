"""
Repositories pour les opérations CRUD sur les entités de trading
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Order, Position, Trade, Strategy, Portfolio, AuditLog
from .models import OrderStatus, PositionStatus, StrategyStatus, OrderSide, PositionType

logger = logging.getLogger(__name__)


class BaseRepository:
    """Repository de base avec opérations communes"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def _log_audit(self, entity_type: str, entity_id: str, action: str, 
                        old_values: Dict = None, new_values: Dict = None, 
                        user_id: str = None, metadata: Dict = None):
        """Enregistre un log d'audit"""
        try:
            audit_log = AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                user_id=user_id,
                metadata=metadata
            )
            self.session.add(audit_log)
        except Exception as e:
            logger.error(f"Erreur log audit: {e}")


class OrderRepository(BaseRepository):
    """Repository pour les ordres"""
    
    async def create(self, order_data: Dict[str, Any]) -> Order:
        """Crée un nouvel ordre"""
        order = Order(**order_data)
        self.session.add(order)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="order",
            entity_id=str(order.id),
            action="create",
            new_values=order_data
        )
        
        return order
    
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """Récupère un ordre par ID"""
        result = await self.session.execute(
            select(Order).where(Order.order_id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_symbol(self, symbol: str, limit: int = 100) -> List[Order]:
        """Récupère les ordres par symbole"""
        result = await self.session.execute(
            select(Order)
            .where(Order.symbol == symbol)
            .order_by(desc(Order.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_status(self, status: OrderStatus, limit: int = 100) -> List[Order]:
        """Récupère les ordres par statut"""
        result = await self.session.execute(
            select(Order)
            .where(Order.status == status)
            .order_by(desc(Order.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_status(self, order_id: str, status: OrderStatus, 
                          filled_quantity: float = None, average_price: float = None) -> bool:
        """Met à jour le statut d'un ordre"""
        try:
            # Récupérer l'ordre existant
            order = await self.get_by_id(order_id)
            if not order:
                return False
            
            old_values = {
                "status": order.status.value,
                "filled_quantity": order.filled_quantity,
                "average_price": order.average_price
            }
            
            # Mettre à jour
            update_data = {"status": status, "updated_at": datetime.utcnow()}
            if filled_quantity is not None:
                update_data["filled_quantity"] = filled_quantity
            if average_price is not None:
                update_data["average_price"] = average_price
            if status == OrderStatus.FILLED:
                update_data["filled_at"] = datetime.utcnow()
            elif status == OrderStatus.CANCELLED:
                update_data["cancelled_at"] = datetime.utcnow()
            
            await self.session.execute(
                update(Order)
                .where(Order.order_id == order_id)
                .values(**update_data)
            )
            
            await self._log_audit(
                entity_type="order",
                entity_id=str(order.id),
                action="update",
                old_values=old_values,
                new_values=update_data
            )
            
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour ordre {order_id}: {e}")
            return False
    
    async def get_active_orders(self, symbol: str = None) -> List[Order]:
        """Récupère les ordres actifs"""
        query = select(Order).where(
            Order.status.in_([OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED])
        )
        
        if symbol:
            query = query.where(Order.symbol == symbol)
        
        query = query.order_by(desc(Order.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def delete_old_orders(self, days: int = 30) -> int:
        """Supprime les anciens ordres"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.session.execute(
            delete(Order).where(
                and_(
                    Order.status.in_([OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]),
                    Order.created_at < cutoff_date
                )
            )
        )
        
        return result.rowcount


class PositionRepository(BaseRepository):
    """Repository pour les positions"""
    
    async def create(self, position_data: Dict[str, Any]) -> Position:
        """Crée une nouvelle position"""
        position = Position(**position_data)
        self.session.add(position)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="position",
            entity_id=str(position.id),
            action="create",
            new_values=position_data
        )
        
        return position
    
    async def get_by_id(self, position_id: str) -> Optional[Position]:
        """Récupère une position par ID"""
        result = await self.session.execute(
            select(Position).where(Position.id == position_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_symbol(self, symbol: str) -> List[Position]:
        """Récupère les positions par symbole"""
        result = await self.session.execute(
            select(Position)
            .where(Position.symbol == symbol)
            .order_by(desc(Position.opened_at))
        )
        return result.scalars().all()
    
    async def get_open_positions(self, symbol: str = None) -> List[Position]:
        """Récupère les positions ouvertes"""
        query = select(Position).where(Position.status == PositionStatus.OPEN)
        
        if symbol:
            query = query.where(Position.symbol == symbol)
        
        query = query.order_by(desc(Position.opened_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_pnl(self, position_id: str, current_price: float, 
                        unrealized_pnl: float) -> bool:
        """Met à jour le PnL d'une position"""
        try:
            await self.session.execute(
                update(Position)
                .where(Position.id == position_id)
                .values(
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    updated_at=datetime.utcnow()
                )
            )
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour PnL position {position_id}: {e}")
            return False
    
    async def close_position(self, position_id: str, realized_pnl: float) -> bool:
        """Ferme une position"""
        try:
            await self.session.execute(
                update(Position)
                .where(Position.id == position_id)
                .values(
                    status=PositionStatus.CLOSED,
                    realized_pnl=realized_pnl,
                    closed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            
            await self._log_audit(
                entity_type="position",
                entity_id=position_id,
                action="close",
                new_values={"status": "closed", "realized_pnl": realized_pnl}
            )
            
            return True
        except Exception as e:
            logger.error(f"Erreur fermeture position {position_id}: {e}")
            return False


class TradeRepository(BaseRepository):
    """Repository pour les trades"""
    
    async def create(self, trade_data: Dict[str, Any]) -> Trade:
        """Crée un nouveau trade"""
        trade = Trade(**trade_data)
        self.session.add(trade)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="trade",
            entity_id=str(trade.id),
            action="create",
            new_values=trade_data
        )
        
        return trade
    
    async def get_by_id(self, trade_id: str) -> Optional[Trade]:
        """Récupère un trade par ID"""
        result = await self.session.execute(
            select(Trade).where(Trade.trade_id == trade_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_symbol(self, symbol: str, limit: int = 100) -> List[Trade]:
        """Récupère les trades par symbole"""
        result = await self.session.execute(
            select(Trade)
            .where(Trade.symbol == symbol)
            .order_by(desc(Trade.executed_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_strategy(self, strategy_id: str, limit: int = 100) -> List[Trade]:
        """Récupère les trades par stratégie"""
        result = await self.session.execute(
            select(Trade)
            .where(Trade.strategy_id == strategy_id)
            .order_by(desc(Trade.executed_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_trades_summary(self, symbol: str = None, 
                               start_date: datetime = None, 
                               end_date: datetime = None) -> Dict[str, Any]:
        """Récupère un résumé des trades"""
        query = select(Trade)
        
        conditions = []
        if symbol:
            conditions.append(Trade.symbol == symbol)
        if start_date:
            conditions.append(Trade.executed_at >= start_date)
        if end_date:
            conditions.append(Trade.executed_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        trades = result.scalars().all()
        
        if not trades:
            return {
                "total_trades": 0,
                "total_pnl": 0.0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0
            }
        
        total_trades = len(trades)
        total_pnl = sum(trade.net_pnl for trade in trades)
        winning_trades = len([t for t in trades if t.net_pnl > 0])
        losing_trades = len([t for t in trades if t.net_pnl < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_pnl": avg_pnl
        }


class StrategyRepository(BaseRepository):
    """Repository pour les stratégies"""
    
    async def create(self, strategy_data: Dict[str, Any]) -> Strategy:
        """Crée une nouvelle stratégie"""
        strategy = Strategy(**strategy_data)
        self.session.add(strategy)
        await self.session.flush()
        
        await self._log_audit(
            entity_type="strategy",
            entity_id=str(strategy.id),
            action="create",
            new_values=strategy_data
        )
        
        return strategy
    
    async def get_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """Récupère une stratégie par ID"""
        result = await self.session.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Strategy]:
        """Récupère une stratégie par nom"""
        result = await self.session.execute(
            select(Strategy).where(Strategy.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_active_strategies(self) -> List[Strategy]:
        """Récupère les stratégies actives"""
        result = await self.session.execute(
            select(Strategy).where(Strategy.status == StrategyStatus.ACTIVE)
        )
        return result.scalars().all()
    
    async def update_status(self, strategy_id: str, status: StrategyStatus) -> bool:
        """Met à jour le statut d'une stratégie"""
        try:
            await self.session.execute(
                update(Strategy)
                .where(Strategy.id == strategy_id)
                .values(
                    status=status,
                    updated_at=datetime.utcnow(),
                    activated_at=datetime.utcnow() if status == StrategyStatus.ACTIVE else None,
                    deactivated_at=datetime.utcnow() if status == StrategyStatus.INACTIVE else None
                )
            )
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour stratégie {strategy_id}: {e}")
            return False


class PortfolioRepository(BaseRepository):
    """Repository pour le portefeuille"""
    
    async def create_snapshot(self, portfolio_data: Dict[str, Any]) -> Portfolio:
        """Crée un snapshot du portefeuille"""
        portfolio = Portfolio(**portfolio_data)
        self.session.add(portfolio)
        await self.session.flush()
        return portfolio
    
    async def get_latest_snapshot(self) -> Optional[Portfolio]:
        """Récupère le dernier snapshot"""
        result = await self.session.execute(
            select(Portfolio)
            .order_by(desc(Portfolio.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_historical_snapshots(self, days: int = 30) -> List[Portfolio]:
        """Récupère les snapshots historiques"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.session.execute(
            select(Portfolio)
            .where(Portfolio.timestamp >= start_date)
            .order_by(desc(Portfolio.timestamp))
        )
        return result.scalars().all()