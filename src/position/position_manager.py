"""
Gestionnaire de positions intelligent avec design patterns optimisés
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd

from ..prediction.signal_generator import TradingSignal, SignalType
from ..backtesting.backtesting_engine import PositionType, Position, Trade


class PositionStatus(Enum):
    """Statut des positions"""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    PARTIALLY_FILLED = "partially_filled"


class RiskLevel(Enum):
    """Niveaux de risque"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class PositionRequest:
    """Demande de position"""
    signal: TradingSignal
    requested_size: float
    max_size: float
    risk_level: RiskLevel
    priority: int  # 1 = highest, 5 = lowest
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PositionAllocation:
    """Allocation de position"""
    symbol: str
    position_type: PositionType
    allocated_size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    max_loss: float
    expected_profit: float
    confidence: float
    timestamp: datetime


class PositionSizingStrategy(ABC):
    """Stratégie de dimensionnement des positions (Strategy Pattern)"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def calculate_position_size(self, request: PositionRequest, 
                              portfolio_value: float, 
                              current_positions: Dict[str, Position]) -> float:
        """Calcule la taille de position optimale"""
        pass


class FixedSizeStrategy(PositionSizingStrategy):
    """Stratégie de taille fixe"""
    
    def __init__(self, fixed_size: float = 1000.0):
        super().__init__("FixedSize")
        self.fixed_size = fixed_size
    
    def calculate_position_size(self, request: PositionRequest, 
                              portfolio_value: float, 
                              current_positions: Dict[str, Position]) -> float:
        """Calcule une taille fixe"""
        return min(self.fixed_size, request.max_size)


class PercentageStrategy(PositionSizingStrategy):
    """Stratégie basée sur un pourcentage du portefeuille"""
    
    def __init__(self, percentage: float = 0.1):  # 10% par défaut
        super().__init__("Percentage")
        self.percentage = percentage
    
    def calculate_position_size(self, request: PositionRequest, 
                              portfolio_value: float, 
                              current_positions: Dict[str, Position]) -> float:
        """Calcule basé sur un pourcentage"""
        max_size_value = portfolio_value * self.percentage
        max_size_units = max_size_value / request.signal.price
        return min(max_size_units, request.max_size)


class KellyCriterionStrategy(PositionSizingStrategy):
    """Stratégie basée sur le critère de Kelly"""
    
    def __init__(self, max_kelly_percentage: float = 0.25):  # Max 25%
        super().__init__("KellyCriterion")
        self.max_kelly_percentage = max_kelly_percentage
    
    def calculate_position_size(self, request: PositionRequest, 
                              portfolio_value: float, 
                              current_positions: Dict[str, Position]) -> float:
        """Calcule basé sur le critère de Kelly"""
        # Estimation des probabilités (simplifiée)
        win_probability = request.signal.confidence
        avg_win = request.signal.take_profit - request.signal.price if request.signal.take_profit else 0.1
        avg_loss = request.signal.price - request.signal.stop_loss if request.signal.stop_loss else 0.05
        
        if avg_loss <= 0:
            return 0.0
        
        # Critère de Kelly: f = (bp - q) / b
        # où b = odds, p = probabilité de gain, q = probabilité de perte
        b = avg_win / avg_loss
        p = win_probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Limiter à un maximum
        kelly_fraction = min(kelly_fraction, self.max_kelly_percentage)
        kelly_fraction = max(kelly_fraction, 0)  # Pas de positions négatives
        
        kelly_size_value = portfolio_value * kelly_fraction
        kelly_size_units = kelly_size_value / request.signal.price
        
        return min(kelly_size_units, request.max_size)


class VolatilityBasedStrategy(PositionSizingStrategy):
    """Stratégie basée sur la volatilité"""
    
    def __init__(self, target_volatility: float = 0.02):  # 2% de volatilité cible
        super().__init__("VolatilityBased")
        self.target_volatility = target_volatility
    
    def calculate_position_size(self, request: PositionRequest, 
                              portfolio_value: float, 
                              current_positions: Dict[str, Position]) -> float:
        """Calcule basé sur la volatilité"""
        # Estimation de la volatilité (simplifiée)
        if request.signal.stop_loss:
            volatility_estimate = abs(request.signal.price - request.signal.stop_loss) / request.signal.price
        else:
            volatility_estimate = 0.05  # 5% par défaut
        
        if volatility_estimate <= 0:
            return 0.0
        
        # Ajuster la taille selon la volatilité
        volatility_adjustment = self.target_volatility / volatility_estimate
        base_size_value = portfolio_value * 0.1  # 10% de base
        adjusted_size_value = base_size_value * volatility_adjustment
        adjusted_size_units = adjusted_size_value / request.signal.price
        
        return min(adjusted_size_units, request.max_size)


class RiskManager:
    """Gestionnaire de risques (Singleton Pattern)"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not RiskManager._initialized:
            self.max_portfolio_risk = 0.05  # 5% de risque maximum
            self.max_position_risk = 0.02   # 2% de risque par position
            self.max_correlation = 0.7      # Corrélation maximum entre positions
            self.max_positions = 10         # Nombre maximum de positions
            self.logger = logging.getLogger(__name__)
            RiskManager._initialized = True
    
    def validate_position_request(self, request: PositionRequest, 
                                portfolio_value: float,
                                current_positions: Dict[str, Position]) -> Tuple[bool, str]:
        """Valide une demande de position"""
        try:
            # Vérifier le risque de position
            if request.signal.stop_loss:
                position_risk = abs(request.signal.price - request.signal.stop_loss) / request.signal.price
                if position_risk > self.max_position_risk:
                    return False, f"Risque de position trop élevé: {position_risk:.2%}"
            
            # Vérifier le nombre de positions
            if len(current_positions) >= self.max_positions:
                return False, f"Nombre maximum de positions atteint: {self.max_positions}"
            
            # Vérifier la corrélation (simplifiée)
            if self._check_correlation(request, current_positions):
                return False, "Position trop corrélée avec les positions existantes"
            
            # Vérifier le capital disponible
            required_capital = request.signal.price * request.requested_size
            if required_capital > portfolio_value * 0.5:  # Max 50% du portefeuille
                return False, "Capital insuffisant"
            
            return True, "Position validée"
        
        except Exception as e:
            self.logger.error(f"Erreur validation position: {e}")
            return False, f"Erreur validation: {e}"
    
    def _check_correlation(self, request: PositionRequest, 
                          current_positions: Dict[str, Position]) -> bool:
        """Vérifie la corrélation avec les positions existantes"""
        # Simplifié: vérifier si c'est le même symbole
        if request.signal.symbol in current_positions:
            return True
        
        # Dans une implémentation réelle, on calculerait la corrélation
        # entre les prix des différents symboles
        return False
    
    def calculate_max_position_size(self, request: PositionRequest, 
                                  portfolio_value: float) -> float:
        """Calcule la taille maximale autorisée"""
        if not request.signal.stop_loss:
            return request.max_size
        
        position_risk = abs(request.signal.price - request.signal.stop_loss) / request.signal.price
        max_risk_value = portfolio_value * self.max_position_risk
        max_size_value = max_risk_value / position_risk
        max_size_units = max_size_value / request.signal.price
        
        return min(max_size_units, request.max_size)


class PositionManager:
    """Gestionnaire principal des positions"""
    
    def __init__(self, name: str = "PositionManager"):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Composants
        self.risk_manager = RiskManager()
        self.sizing_strategies = {}
        self.positions = {}
        self.position_requests = []
        self.allocations = []
        
        # Configuration
        self.portfolio_value = 100000.0
        self.default_sizing_strategy = "percentage"
        
        # Initialiser les stratégies
        self._initialize_sizing_strategies()
    
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
    
    def add_position_request(self, signal: TradingSignal, 
                           sizing_strategy: str = None,
                           priority: int = 3) -> bool:
        """Ajoute une demande de position"""
        try:
            sizing_strategy = sizing_strategy or self.default_sizing_strategy
            
            if sizing_strategy not in self.sizing_strategies:
                self.logger.error(f"Stratégie de dimensionnement inconnue: {sizing_strategy}")
                return False
            
            # Calculer la taille maximale
            max_size = self.risk_manager.calculate_max_position_size(signal, self.portfolio_value)
            
            # Déterminer le niveau de risque
            risk_level = self._determine_risk_level(signal)
            
            # Créer la demande
            request = PositionRequest(
                signal=signal,
                requested_size=0.0,  # Sera calculé plus tard
                max_size=max_size,
                risk_level=risk_level,
                priority=priority,
                timestamp=datetime.utcnow()
            )
            
            # Valider la demande
            is_valid, message = self.risk_manager.validate_position_request(
                request, self.portfolio_value, self.positions
            )
            
            if not is_valid:
                self.logger.warning(f"Demande de position rejetée: {message}")
                return False
            
            # Calculer la taille de position
            sizing_strategy_obj = self.sizing_strategies[sizing_strategy]
            calculated_size = sizing_strategy_obj.calculate_position_size(
                request, self.portfolio_value, self.positions
            )
            
            request.requested_size = calculated_size
            
            # Ajouter à la liste
            self.position_requests.append(request)
            
            self.logger.info(f"Demande de position ajoutée: {signal.symbol} "
                           f"size={calculated_size:.4f} strategy={sizing_strategy}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur ajout demande position: {e}")
            return False
    
    def _determine_risk_level(self, signal: TradingSignal) -> RiskLevel:
        """Détermine le niveau de risque d'un signal"""
        # Combinaison de la force et de la confiance
        risk_score = signal.strength * signal.confidence
        
        if risk_score >= 0.8:
            return RiskLevel.LOW
        elif risk_score >= 0.6:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.4:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def process_position_requests(self) -> List[PositionAllocation]:
        """Traite les demandes de positions"""
        if not self.position_requests:
            return []
        
        # Trier par priorité et timestamp
        self.position_requests.sort(key=lambda x: (x.priority, x.timestamp))
        
        new_allocations = []
        
        for request in self.position_requests:
            try:
                # Vérifier à nouveau la validation
                is_valid, message = self.risk_manager.validate_position_request(
                    request, self.portfolio_value, self.positions
                )
                
                if not is_valid:
                    self.logger.warning(f"Demande rejetée lors du traitement: {message}")
                    continue
                
                # Créer l'allocation
                allocation = self._create_allocation(request)
                if allocation:
                    new_allocations.append(allocation)
                    
                    # Mettre à jour le portefeuille
                    self.portfolio_value -= allocation.allocated_size * allocation.entry_price
                    
                    # Créer la position
                    position = Position(
                        symbol=allocation.symbol,
                        position_type=allocation.position_type,
                        size=allocation.allocated_size,
                        entry_price=allocation.entry_price,
                        entry_time=allocation.timestamp,
                        current_price=allocation.entry_price,
                        current_time=allocation.timestamp,
                        stop_loss=allocation.stop_loss,
                        take_profit=allocation.take_profit
                    )
                    
                    self.positions[allocation.symbol] = position
                    
                    self.logger.info(f"Position allouée: {allocation.symbol} "
                                   f"size={allocation.allocated_size:.4f}")
            
            except Exception as e:
                self.logger.error(f"Erreur traitement demande: {e}")
                continue
        
        # Nettoyer les demandes traitées
        self.position_requests.clear()
        
        # Ajouter aux allocations
        self.allocations.extend(new_allocations)
        
        return new_allocations
    
    def _create_allocation(self, request: PositionRequest) -> Optional[PositionAllocation]:
        """Crée une allocation de position"""
        try:
            signal = request.signal
            
            # Déterminer le type de position
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                position_type = PositionType.LONG
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                position_type = PositionType.SHORT
            else:
                return None
            
            # Calculer le ratio risque/récompense
            if signal.stop_loss and signal.take_profit:
                risk = abs(signal.price - signal.stop_loss)
                reward = abs(signal.take_profit - signal.price)
                risk_reward_ratio = reward / risk if risk > 0 else 0
            else:
                risk_reward_ratio = 1.0
            
            # Calculer les pertes/profits attendus
            max_loss = request.requested_size * abs(signal.price - (signal.stop_loss or signal.price * 0.95))
            expected_profit = request.requested_size * abs((signal.take_profit or signal.price * 1.05) - signal.price)
            
            allocation = PositionAllocation(
                symbol=signal.symbol,
                position_type=position_type,
                allocated_size=request.requested_size,
                entry_price=signal.price,
                stop_loss=signal.stop_loss or (signal.price * 0.95 if position_type == PositionType.LONG else signal.price * 1.05),
                take_profit=signal.take_profit or (signal.price * 1.05 if position_type == PositionType.LONG else signal.price * 0.95),
                risk_reward_ratio=risk_reward_ratio,
                max_loss=max_loss,
                expected_profit=expected_profit,
                confidence=signal.confidence,
                timestamp=datetime.utcnow()
            )
            
            return allocation
        
        except Exception as e:
            self.logger.error(f"Erreur création allocation: {e}")
            return None
    
    def update_positions(self, current_prices: Dict[str, float], current_time: datetime):
        """Met à jour toutes les positions"""
        for position in self.positions.values():
            if position.symbol in current_prices:
                position.update_pnl(current_prices[position.symbol], current_time)
    
    def close_position(self, symbol: str, exit_price: float, 
                      exit_time: datetime, reason: str) -> Optional[Trade]:
        """Ferme une position"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        # Calculer le PnL
        if position.position_type == PositionType.LONG:
            pnl = (exit_price - position.entry_price) * position.size
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.size
        
        # Calculer les frais
        fees = (position.entry_price + exit_price) * position.size * 0.001
        net_pnl = pnl - fees
        
        # Créer le trade
        trade = Trade(
            symbol=symbol,
            entry_time=position.entry_time,
            exit_time=exit_time,
            entry_price=position.entry_price,
            exit_price=exit_price,
            size=position.size,
            position_type=position.position_type,
            pnl=pnl,
            fees=fees,
            net_pnl=net_pnl,
            duration=exit_time - position.entry_time,
            signal_strength=0.0,  # À remplir depuis l'allocation
            signal_confidence=0.0,
            exit_reason=reason
        )
        
        # Mettre à jour le portefeuille
        self.portfolio_value += exit_price * position.size + net_pnl
        
        # Supprimer la position
        del self.positions[symbol]
        
        self.logger.info(f"Position fermée: {symbol} PnL={net_pnl:.2f} reason={reason}")
        
        return trade
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Retourne un résumé du portefeuille"""
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_equity = self.portfolio_value + total_unrealized_pnl
        
        return {
            'portfolio_value': self.portfolio_value,
            'total_equity': total_equity,
            'unrealized_pnl': total_unrealized_pnl,
            'positions_count': len(self.positions),
            'pending_requests': len(self.position_requests),
            'allocations_count': len(self.allocations),
            'positions': {
                symbol: {
                    'type': pos.position_type.value,
                    'size': pos.size,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl
                }
                for symbol, pos in self.positions.items()
            }
        }
    
    def get_position_risk_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de risque des positions"""
        if not self.positions:
            return {}
        
        # Calculer la VaR (Value at Risk) simplifiée
        pnls = [pos.unrealized_pnl for pos in self.positions.values()]
        var_95 = np.percentile(pnls, 5) if pnls else 0
        
        # Calculer la corrélation moyenne (simplifiée)
        correlation_risk = len(self.positions) / 10  # Plus de positions = plus de risque
        
        # Calculer la concentration
        total_exposure = sum(pos.size * pos.current_price for pos in self.positions.values())
        concentration_risk = total_exposure / self.portfolio_value if self.portfolio_value > 0 else 0
        
        return {
            'var_95': var_95,
            'correlation_risk': correlation_risk,
            'concentration_risk': concentration_risk,
            'total_exposure': total_exposure,
            'leverage_ratio': total_exposure / self.portfolio_value if self.portfolio_value > 0 else 0
        }


# Instance globale du gestionnaire de positions
position_manager = PositionManager()