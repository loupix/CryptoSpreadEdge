"""
Moteur de backtesting avancé avec design patterns optimisés
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
import pandas as pd
from enum import Enum

from ..prediction.signal_generator import TradingSignal, SignalType
from ..indicators.base_indicator import IndicatorValue
from src.utils.messaging.redis_bus import RedisEventBus


class PositionType(Enum):
    """Types de positions"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


@dataclass
class Position:
    """Position de trading"""
    symbol: str
    position_type: PositionType
    size: float
    entry_price: float
    entry_time: datetime
    current_price: float
    current_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    def update_pnl(self, current_price: float, current_time: datetime):
        """Met à jour le PnL de la position"""
        self.current_price = current_price
        self.current_time = current_time
        
        if self.position_type == PositionType.LONG:
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        elif self.position_type == PositionType.SHORT:
            self.unrealized_pnl = (self.entry_price - current_price) * self.size
        else:
            self.unrealized_pnl = 0.0


@dataclass
class Trade:
    """Trade exécuté"""
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    size: float
    position_type: PositionType
    pnl: float
    fees: float
    net_pnl: float
    duration: timedelta
    signal_strength: float
    signal_confidence: float
    exit_reason: str  # "take_profit", "stop_loss", "signal", "timeout"


@dataclass
class BacktestResult:
    """Résultat d'un backtest"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    gross_profit: float
    gross_loss: float
    net_profit: float
    total_fees: float
    max_drawdown: float
    max_drawdown_duration: timedelta
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    profit_factor: float
    avg_trade_duration: timedelta
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    volatility: float
    trades: List[Trade]
    equity_curve: pd.DataFrame


class BacktestStrategy(ABC):
    """Stratégie de backtesting (Strategy Pattern)"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def should_enter(self, signal: TradingSignal, current_price: float, 
                    current_time: datetime, portfolio: 'Portfolio') -> bool:
        """Détermine si on doit entrer en position"""
        pass
    
    @abstractmethod
    def should_exit(self, position: Position, current_price: float, 
                   current_time: datetime, portfolio: 'Portfolio') -> Tuple[bool, str]:
        """Détermine si on doit sortir de position"""
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: TradingSignal, current_price: float, 
                              portfolio: 'Portfolio') -> float:
        """Calcule la taille de position"""
        pass


class SimpleBacktestStrategy(BacktestStrategy):
    """Stratégie de backtesting simple"""
    
    def __init__(self, name: str = "SimpleStrategy", 
                 max_position_size: float = 0.1,  # 10% du capital
                 stop_loss_pct: float = 0.05,    # 5% de stop loss
                 take_profit_pct: float = 0.15,  # 15% de take profit
                 max_hold_days: int = 30):       # 30 jours max
        super().__init__(name)
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_hold_days = max_hold_days
    
    def should_enter(self, signal: TradingSignal, current_price: float, 
                    current_time: datetime, portfolio: 'Portfolio') -> bool:
        """Détermine si on doit entrer en position"""
        # Vérifier qu'on n'a pas déjà une position sur ce symbole
        if portfolio.has_position(signal.symbol):
            return False
        
        # Vérifier la force du signal
        if signal.strength < 0.5 or signal.confidence < 0.6:
            return False
        
        # Vérifier le capital disponible
        if portfolio.available_capital < current_price * self.max_position_size:
            return False
        
        return True
    
    def should_exit(self, position: Position, current_price: float, 
                   current_time: datetime, portfolio: 'Portfolio') -> Tuple[bool, str]:
        """Détermine si on doit sortir de position"""
        # Vérifier le stop loss
        if position.stop_loss is not None:
            if position.position_type == PositionType.LONG and current_price <= position.stop_loss:
                return True, "stop_loss"
            elif position.position_type == PositionType.SHORT and current_price >= position.stop_loss:
                return True, "stop_loss"
        
        # Vérifier le take profit
        if position.take_profit is not None:
            if position.position_type == PositionType.LONG and current_price >= position.take_profit:
                return True, "take_profit"
            elif position.position_type == PositionType.SHORT and current_price <= position.take_profit:
                return True, "take_profit"
        
        # Vérifier la durée maximale
        hold_duration = current_time - position.entry_time
        if hold_duration.days >= self.max_hold_days:
            return True, "timeout"
        
        return False, ""
    
    def calculate_position_size(self, signal: TradingSignal, current_price: float, 
                              portfolio: 'Portfolio') -> float:
        """Calcule la taille de position"""
        # Taille basée sur le capital disponible
        max_size_value = portfolio.available_capital * self.max_position_size
        max_size_units = max_size_value / current_price
        
        # Ajuster selon la force du signal
        signal_multiplier = signal.strength * signal.confidence
        adjusted_size = max_size_units * signal_multiplier
        
        return adjusted_size


class Portfolio:
    """Portefeuille de trading (Singleton Pattern)"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Portfolio._initialized:
            self.initial_capital = 100000.0  # 100k USD
            self.current_capital = self.initial_capital
            self.positions = {}
            self.trades = []
            self.equity_curve = []
            self.logger = logging.getLogger(__name__)
            Portfolio._initialized = True
    
    def reset(self, initial_capital: float = 100000.0):
        """Remet à zéro le portefeuille"""
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions.clear()
        self.trades.clear()
        self.equity_curve.clear()
    
    @property
    def available_capital(self) -> float:
        """Capital disponible pour de nouvelles positions"""
        return self.current_capital - sum(
            pos.entry_price * pos.size for pos in self.positions.values()
        )
    
    @property
    def total_equity(self) -> float:
        """Équité totale du portefeuille"""
        return self.current_capital + sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
    
    def has_position(self, symbol: str) -> bool:
        """Vérifie si on a une position sur un symbole"""
        return symbol in self.positions
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Récupère une position"""
        return self.positions.get(symbol)
    
    def open_position(self, signal: TradingSignal, position_size: float, 
                     current_price: float, current_time: datetime) -> bool:
        """Ouvre une nouvelle position"""
        try:
            if self.has_position(signal.symbol):
                self.logger.warning(f"Position déjà ouverte pour {signal.symbol}")
                return False
            
            # Déterminer le type de position
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                position_type = PositionType.LONG
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                position_type = PositionType.SHORT
            else:
                return False
            
            # Créer la position
            position = Position(
                symbol=signal.symbol,
                position_type=position_type,
                size=position_size,
                entry_price=current_price,
                entry_time=current_time,
                current_price=current_price,
                current_time=current_time,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit
            )
            
            # Ajouter au portefeuille
            self.positions[signal.symbol] = position
            
            # Mettre à jour le capital
            self.current_capital -= current_price * position_size
            
            self.logger.info(f"Position ouverte: {signal.symbol} {position_type.value} "
                           f"size={position_size:.4f} price={current_price:.2f}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur ouverture position: {e}")
            return False
    
    def close_position(self, symbol: str, current_price: float, current_time: datetime, 
                      exit_reason: str) -> Optional[Trade]:
        """Ferme une position"""
        try:
            if not self.has_position(symbol):
                return None
            
            position = self.positions[symbol]
            
            # Calculer les frais (0.1% par trade)
            fees = position.entry_price * position.size * 0.001 + current_price * position.size * 0.001
            
            # Calculer le PnL
            if position.position_type == PositionType.LONG:
                pnl = (current_price - position.entry_price) * position.size
            else:  # SHORT
                pnl = (position.entry_price - current_price) * position.size
            
            net_pnl = pnl - fees
            
            # Créer le trade
            trade = Trade(
                symbol=symbol,
                entry_time=position.entry_time,
                exit_time=current_time,
                entry_price=position.entry_price,
                exit_price=current_price,
                size=position.size,
                position_type=position.position_type,
                pnl=pnl,
                fees=fees,
                net_pnl=net_pnl,
                duration=current_time - position.entry_time,
                signal_strength=0.0,  # À remplir depuis le signal original
                signal_confidence=0.0,
                exit_reason=exit_reason
            )
            
            # Mettre à jour le capital
            self.current_capital += current_price * position.size + net_pnl
            
            # Ajouter le trade
            self.trades.append(trade)
            
            # Supprimer la position
            del self.positions[symbol]
            
            self.logger.info(f"Position fermée: {symbol} PnL={net_pnl:.2f} "
                           f"reason={exit_reason}")
            
            return trade
        
        except Exception as e:
            self.logger.error(f"Erreur fermeture position: {e}")
            return None
    
    def update_positions(self, current_prices: Dict[str, float], current_time: datetime):
        """Met à jour toutes les positions"""
        for position in self.positions.values():
            if position.symbol in current_prices:
                position.update_pnl(current_prices[position.symbol], current_time)
    
    def add_equity_point(self, current_time: datetime):
        """Ajoute un point à la courbe d'équité"""
        self.equity_curve.append({
            'timestamp': current_time,
            'equity': self.total_equity,
            'capital': self.current_capital,
            'unrealized_pnl': sum(pos.unrealized_pnl for pos in self.positions.values())
        })


class BacktestingEngine:
    """Moteur de backtesting principal"""
    
    def __init__(self, name: str = "BacktestingEngine"):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.portfolio = Portfolio()
        self.strategy = None
        self.data = None
        self.signals = []
        self.results = None
        self._event_bus: RedisEventBus | None = None
    
    def set_strategy(self, strategy: BacktestStrategy):
        """Définit la stratégie de backtesting"""
        self.strategy = strategy
        self.logger.info(f"Stratégie définie: {strategy.name}")
    
    def load_data(self, data: pd.DataFrame):
        """Charge les données de marché"""
        self.data = data.copy()
        self.logger.info(f"Données chargées: {len(data)} points")
    
    def load_signals(self, signals: List[TradingSignal]):
        """Charge les signaux de trading"""
        self.signals = signals.copy()
        self.logger.info(f"Signaux chargés: {len(signals)} signaux")
    
    def run_backtest(self, start_date: datetime = None, end_date: datetime = None, 
                    initial_capital: float = 100000.0) -> BacktestResult:
        """Exécute le backtest"""
        if not self.strategy:
            raise ValueError("Stratégie non définie")
        
        if self.data is None or self.data.empty:
            raise ValueError("Données non chargées")
        
        if not self.signals:
            raise ValueError("Signaux non chargés")
        
        self.logger.info("Début du backtest")
        # Connexion EventBus lazy
        if self._event_bus is None:
            try:
                self._event_bus = RedisEventBus()
                import asyncio
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    pass
                # Dans un contexte sync, on poursuit sans bloquer si pas d'event loop
                if loop and loop.is_running():
                    loop.create_task(self._event_bus.connect())
            except Exception:
                pass
        
        # Réinitialiser le portefeuille
        self.portfolio.reset(initial_capital)
        
        # Filtrer les données par date
        if start_date:
            self.data = self.data[self.data.index >= start_date]
        if end_date:
            self.data = self.data[self.data.index <= end_date]
        
        # Trier les signaux par timestamp
        self.signals.sort(key=lambda x: x.timestamp)
        
        # Exécuter le backtest
        signal_index = 0
        
        for timestamp, row in self.data.iterrows():
            current_time = timestamp
            current_prices = {'close': row['close']}  # Simplifié pour un seul symbole
            
            # Mettre à jour les positions existantes
            self.portfolio.update_positions(current_prices, current_time)
            
            # Vérifier les sorties de positions
            positions_to_close = []
            for symbol, position in self.portfolio.positions.items():
                should_exit, exit_reason = self.strategy.should_exit(
                    position, row['close'], current_time, self.portfolio
                )
                if should_exit:
                    positions_to_close.append((symbol, exit_reason))
            
            # Fermer les positions
            for symbol, exit_reason in positions_to_close:
                self.portfolio.close_position(symbol, row['close'], current_time, exit_reason)
            
            # Traiter les nouveaux signaux
            while (signal_index < len(self.signals) and 
                   self.signals[signal_index].timestamp <= current_time):
                signal = self.signals[signal_index]
                
                # Vérifier si on doit entrer en position
                if self.strategy.should_enter(signal, row['close'], current_time, self.portfolio):
                    position_size = self.strategy.calculate_position_size(
                        signal, row['close'], self.portfolio
                    )
                    
                    if position_size > 0:
                        self.portfolio.open_position(signal, position_size, row['close'], current_time)
                
                signal_index += 1
            
            # Ajouter un point à la courbe d'équité
            self.portfolio.add_equity_point(current_time)
            # Publier point d'équité
            self._publish_bt_event_sync('backtesting.equity', {
                'timestamp': current_time.isoformat(),
                'equity': self.portfolio.total_equity,
                'capital': self.portfolio.current_capital,
            })
        
        # Fermer toutes les positions restantes
        for symbol in list(self.portfolio.positions.keys()):
            self.portfolio.close_position(symbol, self.data['close'].iloc[-1], 
                                        self.data.index[-1], "end_of_data")
        
        # Calculer les résultats
        self.results = self._calculate_results()
        
        self.logger.info("Backtest terminé")
        # Publier résultats
        self._publish_bt_event_sync('backtesting.results', {
            'total_trades': self.results.total_trades if self.results else 0,
            'win_rate': self.results.win_rate if self.results else 0.0,
            'total_pnl': self.results.total_pnl if self.results else 0.0,
            'sharpe_ratio': self.results.sharpe_ratio if self.results else 0.0,
            'max_drawdown': self.results.max_drawdown if self.results else 0.0,
        })
        return self.results
    
    def _calculate_results(self) -> BacktestResult:
        """Calcule les résultats du backtest"""
        if not self.portfolio.trades:
            return self._create_empty_result()
        
        trades = self.portfolio.trades
        equity_curve = pd.DataFrame(self.portfolio.equity_curve)
        
        # Statistiques de base
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.net_pnl > 0])
        losing_trades = len([t for t in trades if t.net_pnl < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # PnL
        total_pnl = sum(t.net_pnl for t in trades)
        gross_profit = sum(t.net_pnl for t in trades if t.net_pnl > 0)
        gross_loss = sum(t.net_pnl for t in trades if t.net_pnl < 0)
        total_fees = sum(t.fees for t in trades)
        net_profit = total_pnl
        
        # Drawdown
        max_drawdown, max_dd_duration = self._calculate_drawdown(equity_curve)
        
        # Ratios
        sharpe_ratio = self._calculate_sharpe_ratio(equity_curve)
        sortino_ratio = self._calculate_sortino_ratio(equity_curve)
        calmar_ratio = self._calculate_calmar_ratio(equity_curve, max_drawdown)
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
        
        # Durées
        avg_trade_duration = np.mean([t.duration for t in trades])
        
        # Gains/Pertes
        wins = [t.net_pnl for t in trades if t.net_pnl > 0]
        losses = [t.net_pnl for t in trades if t.net_pnl < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0
        
        # Séquences
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(trades)
        
        # Retours
        initial_capital = self.portfolio.initial_capital
        final_capital = self.portfolio.current_capital
        total_return = (final_capital - initial_capital) / initial_capital
        
        # Calcul de la durée totale
        if equity_curve.empty:
            duration = timedelta(0)
        else:
            duration = equity_curve['timestamp'].iloc[-1] - equity_curve['timestamp'].iloc[0]
        
        annualized_return = self._calculate_annualized_return(total_return, duration)
        volatility = self._calculate_volatility(equity_curve)
        
        return BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_profit=net_profit,
            total_fees=total_fees,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            profit_factor=profit_factor,
            avg_trade_duration=avg_trade_duration,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            start_date=equity_curve['timestamp'].iloc[0] if not equity_curve.empty else datetime.utcnow(),
            end_date=equity_curve['timestamp'].iloc[-1] if not equity_curve.empty else datetime.utcnow(),
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            trades=trades,
            equity_curve=equity_curve
        )
    
    def _create_empty_result(self) -> BacktestResult:
        """Crée un résultat vide"""
        return BacktestResult(
            total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
            total_pnl=0.0, gross_profit=0.0, gross_loss=0.0, net_profit=0.0,
            total_fees=0.0, max_drawdown=0.0, max_drawdown_duration=timedelta(0),
            sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0, profit_factor=0.0,
            avg_trade_duration=timedelta(0), avg_win=0.0, avg_loss=0.0,
            largest_win=0.0, largest_loss=0.0, consecutive_wins=0, consecutive_losses=0,
            start_date=datetime.utcnow(), end_date=datetime.utcnow(),
            initial_capital=self.portfolio.initial_capital, final_capital=self.portfolio.initial_capital,
            total_return=0.0, annualized_return=0.0, volatility=0.0,
            trades=[], equity_curve=pd.DataFrame()
        )
    
    def _calculate_drawdown(self, equity_curve: pd.DataFrame) -> Tuple[float, timedelta]:
        """Calcule le drawdown maximum"""
        if equity_curve.empty:
            return 0.0, timedelta(0)
        
        equity = equity_curve['equity'].values
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        max_drawdown = np.max(drawdown)
        
        # Durée du drawdown maximum
        max_dd_idx = np.argmax(drawdown)
        dd_start = max_dd_idx
        while dd_start > 0 and drawdown[dd_start - 1] < drawdown[dd_start]:
            dd_start -= 1
        
        dd_duration = equity_curve['timestamp'].iloc[max_dd_idx] - equity_curve['timestamp'].iloc[dd_start]
        
        return max_drawdown, dd_duration
    
    def _calculate_sharpe_ratio(self, equity_curve: pd.DataFrame) -> float:
        """Calcule le ratio de Sharpe"""
        if equity_curve.empty or len(equity_curve) < 2:
            return 0.0
        
        returns = equity_curve['equity'].pct_change().dropna()
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - 0.02 / 252  # 2% risk-free rate annualized
        return np.mean(excess_returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
    
    def _calculate_sortino_ratio(self, equity_curve: pd.DataFrame) -> float:
        """Calcule le ratio de Sortino"""
        if equity_curve.empty or len(equity_curve) < 2:
            return 0.0
        
        returns = equity_curve['equity'].pct_change().dropna()
        if len(returns) == 0:
            return 0.0
        
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return float('inf')
        
        excess_returns = returns - 0.02 / 252
        downside_deviation = np.std(negative_returns)
        
        return np.mean(excess_returns) / downside_deviation * np.sqrt(252) if downside_deviation > 0 else 0.0
    
    def _calculate_calmar_ratio(self, equity_curve: pd.DataFrame, max_drawdown: float) -> float:
        """Calcule le ratio de Calmar"""
        if max_drawdown == 0:
            return float('inf')
        
        if equity_curve.empty:
            return 0.0
        
        total_return = (equity_curve['equity'].iloc[-1] - equity_curve['equity'].iloc[0]) / equity_curve['equity'].iloc[0]
        return total_return / max_drawdown if max_drawdown > 0 else 0.0
    
    def _calculate_consecutive_trades(self, trades: List[Trade]) -> Tuple[int, int]:
        """Calcule les séquences de gains/pertes consécutives"""
        if not trades:
            return 0, 0
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            if trade.net_pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return max_wins, max_losses
    
    def _calculate_annualized_return(self, total_return: float, duration: timedelta) -> float:
        """Calcule le retour annualisé"""
        if duration.total_seconds() == 0:
            return 0.0
        
        years = duration.total_seconds() / (365.25 * 24 * 3600)
        return (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0
    
    def _calculate_volatility(self, equity_curve: pd.DataFrame) -> float:
        """Calcule la volatilité annualisée"""
        if equity_curve.empty or len(equity_curve) < 2:
            return 0.0
        
        returns = equity_curve['equity'].pct_change().dropna()
        if len(returns) == 0:
            return 0.0
        
        return np.std(returns) * np.sqrt(252)  # Annualized
    
    def get_results(self) -> Optional[BacktestResult]:
        """Retourne les résultats du backtest"""
        return self.results
    
    def export_results(self, filepath: str):
        """Exporte les résultats vers un fichier"""
        if not self.results:
            self.logger.warning("Aucun résultat à exporter")
            return
        
        try:
            # Exporter la courbe d'équité
            self.results.equity_curve.to_csv(f"{filepath}_equity_curve.csv", index=False)
            
            # Exporter les trades
            trades_df = pd.DataFrame([
                {
                    'symbol': t.symbol,
                    'entry_time': t.entry_time,
                    'exit_time': t.exit_time,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'size': t.size,
                    'position_type': t.position_type.value,
                    'pnl': t.pnl,
                    'fees': t.fees,
                    'net_pnl': t.net_pnl,
                    'duration_days': t.duration.days,
                    'exit_reason': t.exit_reason
                }
                for t in self.results.trades
            ])
            trades_df.to_csv(f"{filepath}_trades.csv", index=False)
            
            # Exporter les statistiques
            stats = {
                'total_trades': self.results.total_trades,
                'win_rate': self.results.win_rate,
                'total_pnl': self.results.total_pnl,
                'sharpe_ratio': self.results.sharpe_ratio,
                'max_drawdown': self.results.max_drawdown,
                'total_return': self.results.total_return
            }
            
            pd.DataFrame([stats]).to_csv(f"{filepath}_stats.csv", index=False)
            
            self.logger.info(f"Résultats exportés: {filepath}")
        
        except Exception as e:
            self.logger.error(f"Erreur export: {e}")

    def _publish_bt_event_sync(self, stream: str, payload: Dict[str, Any]) -> None:
        try:
            import asyncio
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                pass
            if loop and loop.is_running() and self._event_bus is not None:
                loop.create_task(self._event_bus.publish(stream, payload))
        except Exception:
            pass


# Instance globale du moteur de backtesting
backtesting_engine = BacktestingEngine()