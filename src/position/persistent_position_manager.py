"""
Gestionnaire de positions avec persistance PostgreSQL
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd

from ..database import get_database_manager, PositionRepository, TradeRepository
from ..database.models import PositionStatus, PositionType, OrderSide
from ..prediction.signal_generator import TradingSignal, SignalType
from ..backtesting.backtesting_engine import Position as BacktestPosition, Trade as BacktestTrade


class RiskLevel(Enum):
    """Niveaux de risque"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PositionRequest:
    """Demande de position"""
    signal: TradingSignal
    sizing_strategy: str
    priority: int
    max_risk: float = 0.02
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class PositionAllocation:
    """Allocation de position"""
    symbol: str
    size: float
    entry_price: float
    position_type: PositionType
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_level: RiskLevel
    confidence: float
    strategy_id: Optional[str] = None


class PersistentPositionManager:
    """Gestionnaire principal des positions avec persistance PostgreSQL"""
    
    def __init__(self, name: str = "PersistentPositionManager"):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Composants
        self.sizing_strategies = {}
        self.position_requests = []
        self.allocations = []
        
        # Configuration
        self.portfolio_value = 100000.0
        self.default_sizing_strategy = "percentage"
        
        # Base de données
        self._db_manager = get_database_manager()
        
        # Initialiser les stratégies
        self._initialize_sizing_strategies()
    
    async def initialize(self):
        """Initialise le gestionnaire de positions"""
        await self._db_manager.initialize()
        self.logger.info("Gestionnaire de positions initialisé avec persistance")
    
    def _initialize_sizing_strategies(self):
        """Initialise les stratégies de dimensionnement"""
        self.sizing_strategies = {
            "fixed": FixedSizeStrategy(1000.0),
            "percentage": PercentageStrategy(0.1),
            "kelly": KellyCriterionStrategy(0.25),
            "volatility": VolatilityBasedStrategy(0.02)
        }
    
    def set_portfolio_value(self, value: float):
        """Définit la valeur du portefeuille"""
        self.portfolio_value = value
        self.logger.info(f"Valeur du portefeuille mise à jour: {value:.2f}")
    
    async def add_position_request(self, signal: TradingSignal, 
                                 sizing_strategy: str = None,
                                 priority: int = 3) -> bool:
        """Ajoute une demande de position"""
        try:
            strategy_name = sizing_strategy or self.default_sizing_strategy
            
            request = PositionRequest(
                signal=signal,
                sizing_strategy=strategy_name,
                priority=priority
            )
            
            self.position_requests.append(request)
            self.logger.info(f"Demande de position ajoutée: {signal.symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur ajout demande position: {e}")
            return False
    
    async def process_position_requests(self) -> List[PositionAllocation]:
        """Traite les demandes de position"""
        allocations = []
        
        try:
            # Trier par priorité
            self.position_requests.sort(key=lambda x: x.priority, reverse=True)
            
            for request in self.position_requests:
                allocation = await self._create_allocation(request)
                if allocation:
                    allocations.append(allocation)
                    self.allocations.append(allocation)
            
            # Vider la liste des demandes
            self.position_requests.clear()
            
            return allocations
            
        except Exception as e:
            self.logger.error(f"Erreur traitement demandes position: {e}")
            return []
    
    async def open_position(self, allocation: PositionAllocation) -> bool:
        """Ouvre une position"""
        try:
            # Préparer les données pour la base
            position_data = {
                "symbol": allocation.symbol,
                "side": allocation.position_type,
                "quantity": allocation.size,
                "average_price": allocation.entry_price,
                "current_price": allocation.entry_price,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
                "status": PositionStatus.OPEN,
                "exchange": "system",  # À adapter selon votre logique
                "strategy_id": allocation.strategy_id,
                "metadata": {
                    "stop_loss": allocation.stop_loss,
                    "take_profit": allocation.take_profit,
                    "risk_level": allocation.risk_level.value,
                    "confidence": allocation.confidence,
                    "allocation_id": str(id(allocation))
                }
            }
            
            # Sauvegarder en base
            async with self._db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                db_position = await position_repo.create(position_data)
                
                self.logger.info(f"Position ouverte: {allocation.symbol} - {allocation.size} @ {allocation.entry_price}")
                return True
                
        except Exception as e:
            self.logger.error(f"Erreur ouverture position: {e}")
            return False
    
    async def update_positions(self, current_prices: Dict[str, float], current_time: datetime):
        """Met à jour toutes les positions"""
        try:
            async with self._db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                open_positions = await position_repo.get_open_positions()
                
                for position in open_positions:
                    if position.symbol in current_prices:
                        current_price = current_prices[position.symbol]
                        
                        # Calculer le PnL non réalisé
                        if position.side == PositionType.LONG:
                            unrealized_pnl = (current_price - position.average_price) * position.quantity
                        else:  # SHORT
                            unrealized_pnl = (position.average_price - current_price) * position.quantity
                        
                        # Mettre à jour en base
                        await position_repo.update_pnl(
                            str(position.id), 
                            current_price, 
                            unrealized_pnl
                        )
                        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour positions: {e}")
    
    async def close_position(self, symbol: str, exit_price: float, 
                           exit_time: datetime, reason: str) -> Optional[BacktestTrade]:
        """Ferme une position"""
        try:
            async with self._db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                trade_repo = TradeRepository(session)
                
                # Récupérer la position
                open_positions = await position_repo.get_open_positions(symbol)
                if not open_positions:
                    return None
                
                position = open_positions[0]  # Prendre la première position ouverte
                
                # Calculer le PnL
                if position.side == PositionType.LONG:
                    pnl = (exit_price - position.average_price) * position.quantity
                else:  # SHORT
                    pnl = (position.average_price - exit_price) * position.quantity
                
                # Calculer les frais
                fees = (position.average_price + exit_price) * position.quantity * 0.001
                net_pnl = pnl - fees
                
                # Créer le trade
                trade_data = {
                    "trade_id": f"TRD_{int(exit_time.timestamp())}_{symbol}",
                    "symbol": symbol,
                    "side": OrderSide.BUY if position.side == PositionType.LONG else OrderSide.SELL,
                    "quantity": position.quantity,
                    "price": exit_price,
                    "fees": fees,
                    "pnl": pnl,
                    "net_pnl": net_pnl,
                    "position_id": str(position.id),
                    "strategy_id": position.strategy_id,
                    "exchange": position.exchange,
                    "executed_at": exit_time,
                    "exit_reason": reason,
                    "metadata": {
                        "entry_price": position.average_price,
                        "entry_time": position.opened_at.isoformat(),
                        "duration_seconds": (exit_time - position.opened_at).total_seconds()
                    }
                }
                
                # Sauvegarder le trade
                db_trade = await trade_repo.create(trade_data)
                
                # Fermer la position
                await position_repo.close_position(str(position.id), net_pnl)
                
                # Mettre à jour le portefeuille
                self.portfolio_value += exit_price * position.quantity + net_pnl
                
                # Créer l'objet BacktestTrade pour compatibilité
                trade = BacktestTrade(
                    symbol=symbol,
                    entry_time=position.opened_at,
                    exit_time=exit_time,
                    entry_price=position.average_price,
                    exit_price=exit_price,
                    size=position.quantity,
                    position_type=position.side,
                    pnl=pnl,
                    fees=fees,
                    net_pnl=net_pnl,
                    signal_strength=0.0,  # À récupérer depuis les métadonnées
                    signal_confidence=0.0,
                    exit_reason=reason
                )
                
                self.logger.info(f"Position fermée: {symbol} PnL={net_pnl:.2f}")
                return trade
                
        except Exception as e:
            self.logger.error(f"Erreur fermeture position {symbol}: {e}")
            return None
    
    async def get_open_positions(self, symbol: str = None) -> List[BacktestPosition]:
        """Récupère les positions ouvertes"""
        try:
            async with self._db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                db_positions = await position_repo.get_open_positions(symbol)
                
                positions = []
                for db_pos in db_positions:
                    position = BacktestPosition(
                        symbol=db_pos.symbol,
                        position_type=db_pos.side,
                        size=db_pos.quantity,
                        entry_price=db_pos.average_price,
                        entry_time=db_pos.opened_at,
                        unrealized_pnl=db_pos.unrealized_pnl,
                        realized_pnl=db_pos.realized_pnl
                    )
                    positions.append(position)
                
                return positions
                
        except Exception as e:
            self.logger.error(f"Erreur récupération positions ouvertes: {e}")
            return []
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Récupère un résumé du portefeuille"""
        try:
            async with self._db_manager.get_session() as session:
                position_repo = PositionRepository(session)
                trade_repo = TradeRepository(session)
                
                # Positions ouvertes
                open_positions = await position_repo.get_open_positions()
                total_unrealized_pnl = sum(pos.unrealized_pnl for pos in open_positions)
                
                # Trades récents (30 derniers jours)
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                trades_summary = await trade_repo.get_trades_summary(
                    start_date=start_date, 
                    end_date=end_date
                )
                
                return {
                    "portfolio_value": self.portfolio_value,
                    "total_unrealized_pnl": total_unrealized_pnl,
                    "total_realized_pnl": trades_summary.get("total_pnl", 0.0),
                    "active_positions": len(open_positions),
                    "total_trades_30d": trades_summary.get("total_trades", 0),
                    "win_rate_30d": trades_summary.get("win_rate", 0.0),
                    "avg_pnl_30d": trades_summary.get("avg_pnl", 0.0)
                }
                
        except Exception as e:
            self.logger.error(f"Erreur récupération résumé portefeuille: {e}")
            return {}
    
    async def _create_allocation(self, request: PositionRequest) -> Optional[PositionAllocation]:
        """Crée une allocation de position"""
        try:
            signal = request.signal
            strategy = self.sizing_strategies.get(request.sizing_strategy)
            
            if not strategy:
                self.logger.error(f"Stratégie de dimensionnement inconnue: {request.sizing_strategy}")
                return None
            
            # Calculer la taille
            size = strategy.calculate_size(signal, self.portfolio_value)
            
            if size <= 0:
                return None
            
            # Déterminer le type de position
            position_type = PositionType.LONG if signal.signal_type == SignalType.BUY else PositionType.SHORT
            
            # Calculer le niveau de risque
            risk_level = self._calculate_risk_level(signal, size)
            
            allocation = PositionAllocation(
                symbol=signal.symbol,
                size=size,
                entry_price=signal.price,
                position_type=position_type,
                stop_loss=request.stop_loss,
                take_profit=request.take_profit,
                risk_level=risk_level,
                confidence=signal.confidence,
                strategy_id=None  # À adapter selon votre logique
            )
            
            return allocation
            
        except Exception as e:
            self.logger.error(f"Erreur création allocation: {e}")
            return None
    
    def _calculate_risk_level(self, signal: TradingSignal, size: float) -> RiskLevel:
        """Calcule le niveau de risque d'une position"""
        # Logique simplifiée - à adapter selon vos besoins
        risk_ratio = size / self.portfolio_value
        
        if risk_ratio < 0.01:
            return RiskLevel.LOW
        elif risk_ratio < 0.05:
            return RiskLevel.MEDIUM
        elif risk_ratio < 0.10:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL


# Stratégies de dimensionnement (simplifiées)
class FixedSizeStrategy:
    def __init__(self, fixed_amount: float):
        self.fixed_amount = fixed_amount
    
    def calculate_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        return min(self.fixed_amount, portfolio_value * 0.1)


class PercentageStrategy:
    def __init__(self, percentage: float):
        self.percentage = percentage
    
    def calculate_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        return portfolio_value * self.percentage


class KellyCriterionStrategy:
    def __init__(self, max_fraction: float):
        self.max_fraction = max_fraction
    
    def calculate_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        # Kelly Criterion simplifié
        win_rate = 0.6  # À calculer depuis l'historique
        avg_win = 0.02  # À calculer depuis l'historique
        avg_loss = 0.01  # À calculer depuis l'historique
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_fraction = max(0, min(kelly_fraction, self.max_fraction))
        
        return portfolio_value * kelly_fraction


class VolatilityBasedStrategy:
    def __init__(self, target_volatility: float):
        self.target_volatility = target_volatility
    
    def calculate_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        # Calcul simplifié basé sur la volatilité
        volatility = 0.02  # À calculer depuis les données de marché
        size = (self.target_volatility * portfolio_value) / (volatility * signal.price)
        return min(size, portfolio_value * 0.1)