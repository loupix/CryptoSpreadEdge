"""
Générateur de signaux de trading avec design patterns optimisés
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
import pandas as pd
from enum import Enum
from ..utils.messaging.redis_bus import RedisEventBus

from ..indicators.base_indicator import (
    IndicatorValue, IndicatorSignal, IndicatorType, 
    IndicatorComposite, IndicatorObserver
)


class SignalStrength(Enum):
    """Force des signaux"""
    VERY_WEAK = 0.2
    WEAK = 0.4
    MEDIUM = 0.6
    STRONG = 0.8
    VERY_STRONG = 1.0


class SignalType(Enum):
    """Types de signaux"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"


@dataclass
class TradingSignal:
    """Signal de trading complet"""
    signal_type: SignalType
    strength: float
    confidence: float
    timestamp: datetime
    symbol: str
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    reasoning: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []
        if self.metadata is None:
            self.metadata = {}


class SignalStrategy(ABC):
    """Stratégie de génération de signaux (Strategy Pattern)"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def generate_signals(self, indicators: Dict[str, List[IndicatorValue]], 
                        current_price: float, symbol: str) -> List[TradingSignal]:
        """Génère des signaux selon la stratégie"""
        pass
    
    def calculate_signal_strength(self, signals: List[IndicatorSignal]) -> float:
        """Calcule la force globale des signaux"""
        if not signals:
            return 0.0
        
        # Moyenne pondérée par la confiance
        total_weight = sum(signal.confidence for signal in signals)
        if total_weight == 0:
            return 0.0
        
        weighted_strength = sum(
            signal.strength * signal.confidence for signal in signals
        )
        return weighted_strength / total_weight


class TrendFollowingStrategy(SignalStrategy):
    """Stratégie de suivi de tendance"""
    
    def __init__(self, name: str = "TrendFollowing"):
        super().__init__(name)
        self.required_indicators = ["SMA_20", "SMA_50", "MACD", "RSI"]
    
    def generate_signals(self, indicators: Dict[str, List[IndicatorValue]], 
                        current_price: float, symbol: str) -> List[TradingSignal]:
        """Génère des signaux de suivi de tendance"""
        signals = []
        
        try:
            # Vérifier la disponibilité des indicateurs
            if not all(ind in indicators for ind in self.required_indicators):
                return signals
            
            # Récupérer les dernières valeurs
            sma_20 = self._get_latest_value(indicators["SMA_20"])
            sma_50 = self._get_latest_value(indicators["SMA_50"])
            macd = self._get_latest_value(indicators["MACD"])
            rsi = self._get_latest_value(indicators["RSI"])
            
            if not all([sma_20, sma_50, macd, rsi]):
                return signals
            
            reasoning = []
            
            # Signal de tendance haussière
            if (sma_20.value > sma_50.value and 
                current_price > sma_20.value and
                rsi.value < 70):  # Pas de survente
                
                strength = self._calculate_trend_strength(sma_20, sma_50, current_price)
                confidence = min(sma_20.confidence, sma_50.confidence, rsi.confidence)
                
                reasoning.extend([
                    f"SMA 20 ({sma_20.value:.2f}) > SMA 50 ({sma_50.value:.2f})",
                    f"Prix ({current_price:.2f}) > SMA 20",
                    f"RSI ({rsi.value:.2f}) < 70"
                ])
                
                signal = TradingSignal(
                    signal_type=SignalType.BUY if strength < 0.8 else SignalType.STRONG_BUY,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.utcnow(),
                    symbol=symbol,
                    price=current_price,
                    stop_loss=current_price * 0.95,  # 5% de stop loss
                    take_profit=current_price * 1.15,  # 15% de take profit
                    reasoning=reasoning,
                    metadata={
                        'strategy': self.name,
                        'sma_20': sma_20.value,
                        'sma_50': sma_50.value,
                        'rsi': rsi.value,
                        'macd': macd.value
                    }
                )
                signals.append(signal)
            
            # Signal de tendance baissière
            elif (sma_20.value < sma_50.value and 
                  current_price < sma_20.value and
                  rsi.value > 30):  # Pas de survente
                
                strength = self._calculate_trend_strength(sma_20, sma_50, current_price)
                confidence = min(sma_20.confidence, sma_50.confidence, rsi.confidence)
                
                reasoning.extend([
                    f"SMA 20 ({sma_20.value:.2f}) < SMA 50 ({sma_50.value:.2f})",
                    f"Prix ({current_price:.2f}) < SMA 20",
                    f"RSI ({rsi.value:.2f}) > 30"
                ])
                
                signal = TradingSignal(
                    signal_type=SignalType.SELL if strength < 0.8 else SignalType.STRONG_SELL,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.utcnow(),
                    symbol=symbol,
                    price=current_price,
                    stop_loss=current_price * 1.05,  # 5% de stop loss
                    take_profit=current_price * 0.85,  # 15% de take profit
                    reasoning=reasoning,
                    metadata={
                        'strategy': self.name,
                        'sma_20': sma_20.value,
                        'sma_50': sma_50.value,
                        'rsi': rsi.value,
                        'macd': macd.value
                    }
                )
                signals.append(signal)
        
        except Exception as e:
            self.logger.error(f"Erreur génération signaux tendance: {e}")
        
        return signals
    
    def _get_latest_value(self, values: List[IndicatorValue]) -> Optional[IndicatorValue]:
        """Récupère la dernière valeur d'un indicateur"""
        if not values:
            return None
        return values[-1]
    
    def _calculate_trend_strength(self, sma_20: IndicatorValue, sma_50: IndicatorValue, 
                                 current_price: float) -> float:
        """Calcule la force de la tendance"""
        # Distance entre les moyennes mobiles
        sma_distance = abs(sma_20.value - sma_50.value) / sma_50.value
        
        # Distance du prix à la SMA 20
        price_distance = abs(current_price - sma_20.value) / sma_20.value
        
        # Force combinée
        strength = min(1.0, (sma_distance + price_distance) * 2)
        return strength


class MeanReversionStrategy(SignalStrategy):
    """Stratégie de retour à la moyenne"""
    
    def __init__(self, name: str = "MeanReversion"):
        super().__init__(name)
        self.required_indicators = ["RSI", "BOLLINGER", "STOCHASTIC"]
    
    def generate_signals(self, indicators: Dict[str, List[IndicatorValue]], 
                        current_price: float, symbol: str) -> List[TradingSignal]:
        """Génère des signaux de retour à la moyenne"""
        signals = []
        
        try:
            if not all(ind in indicators for ind in self.required_indicators):
                return signals
            
            rsi = self._get_latest_value(indicators["RSI"])
            bb = self._get_latest_value(indicators["BOLLINGER"])
            stoch = self._get_latest_value(indicators["STOCHASTIC"])
            
            if not all([rsi, bb, stoch]):
                return signals
            
            reasoning = []
            
            # Signal d'achat (survente)
            if (rsi.value < 30 and 
                bb.metadata.get('position', 0.5) < 0.2 and
                stoch.value < 20):
                
                strength = self._calculate_oversold_strength(rsi, bb, stoch)
                confidence = min(rsi.confidence, bb.confidence, stoch.confidence)
                
                reasoning.extend([
                    f"RSI ({rsi.value:.2f}) < 30 (survente)",
                    f"Position BB ({bb.metadata.get('position', 0):.2f}) < 0.2",
                    f"Stochastique ({stoch.value:.2f}) < 20"
                ])
                
                signal = TradingSignal(
                    signal_type=SignalType.BUY if strength < 0.8 else SignalType.STRONG_BUY,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.utcnow(),
                    symbol=symbol,
                    price=current_price,
                    stop_loss=current_price * 0.98,  # 2% de stop loss
                    take_profit=current_price * 1.08,  # 8% de take profit
                    reasoning=reasoning,
                    metadata={
                        'strategy': self.name,
                        'rsi': rsi.value,
                        'bb_position': bb.metadata.get('position', 0),
                        'stochastic': stoch.value
                    }
                )
                signals.append(signal)
            
            # Signal de vente (surachat)
            elif (rsi.value > 70 and 
                  bb.metadata.get('position', 0.5) > 0.8 and
                  stoch.value > 80):
                
                strength = self._calculate_overbought_strength(rsi, bb, stoch)
                confidence = min(rsi.confidence, bb.confidence, stoch.confidence)
                
                reasoning.extend([
                    f"RSI ({rsi.value:.2f}) > 70 (surachat)",
                    f"Position BB ({bb.metadata.get('position', 0):.2f}) > 0.8",
                    f"Stochastique ({stoch.value:.2f}) > 80"
                ])
                
                signal = TradingSignal(
                    signal_type=SignalType.SELL if strength < 0.8 else SignalType.STRONG_SELL,
                    strength=strength,
                    confidence=confidence,
                    timestamp=datetime.utcnow(),
                    symbol=symbol,
                    price=current_price,
                    stop_loss=current_price * 1.02,  # 2% de stop loss
                    take_profit=current_price * 0.92,  # 8% de take profit
                    reasoning=reasoning,
                    metadata={
                        'strategy': self.name,
                        'rsi': rsi.value,
                        'bb_position': bb.metadata.get('position', 0),
                        'stochastic': stoch.value
                    }
                )
                signals.append(signal)
        
        except Exception as e:
            self.logger.error(f"Erreur génération signaux retour à la moyenne: {e}")
        
        return signals
    
    def _get_latest_value(self, values: List[IndicatorValue]) -> Optional[IndicatorValue]:
        """Récupère la dernière valeur d'un indicateur"""
        if not values:
            return None
        return values[-1]
    
    def _calculate_oversold_strength(self, rsi: IndicatorValue, bb: IndicatorValue, 
                                   stoch: IndicatorValue) -> float:
        """Calcule la force du signal de survente"""
        rsi_strength = (30 - rsi.value) / 30
        bb_strength = (0.2 - bb.metadata.get('position', 0.5)) / 0.2
        stoch_strength = (20 - stoch.value) / 20
        
        return min(1.0, (rsi_strength + bb_strength + stoch_strength) / 3)
    
    def _calculate_overbought_strength(self, rsi: IndicatorValue, bb: IndicatorValue, 
                                     stoch: IndicatorValue) -> float:
        """Calcule la force du signal de surachat"""
        rsi_strength = (rsi.value - 70) / 30
        bb_strength = (bb.metadata.get('position', 0.5) - 0.8) / 0.2
        stoch_strength = (stoch.value - 80) / 20
        
        return min(1.0, (rsi_strength + bb_strength + stoch_strength) / 3)


class MLPredictionStrategy(SignalStrategy):
    """Stratégie basée sur les prédictions ML"""
    
    def __init__(self, name: str = "MLPrediction"):
        super().__init__(name)
        self.required_indicators = ["ML_PREDICTION", "VOLATILITY", "SENTIMENT"]
        self.prediction_threshold = 0.02  # 2% de changement prédit
        self.confidence_threshold = 0.7
    
    def generate_signals(self, indicators: Dict[str, List[IndicatorValue]], 
                        current_price: float, symbol: str) -> List[TradingSignal]:
        """Génère des signaux basés sur les prédictions ML"""
        signals = []
        
        try:
            if not all(ind in indicators for ind in self.required_indicators):
                return signals
            
            ml_pred = self._get_latest_value(indicators["ML_PREDICTION"])
            volatility = self._get_latest_value(indicators["VOLATILITY"])
            sentiment = self._get_latest_value(indicators["SENTIMENT"])
            
            if not all([ml_pred, volatility, sentiment]):
                return signals
            
            prediction = ml_pred.value
            confidence = ml_pred.confidence
            
            # Vérifier les seuils
            if (abs(prediction) > self.prediction_threshold and 
                confidence > self.confidence_threshold):
                
                reasoning = []
                
                # Signal d'achat (prédiction de hausse)
                if prediction > self.prediction_threshold:
                    strength = min(1.0, prediction * 10)
                    
                    reasoning.extend([
                        f"Prédiction ML: +{prediction:.2%}",
                        f"Confiance: {confidence:.2%}",
                        f"Volatilité: {volatility.metadata.get('volatility_level', 'unknown')}",
                        f"Sentiment: {sentiment.metadata.get('sentiment_level', 'unknown')}"
                    ])
                    
                    signal = TradingSignal(
                        signal_type=SignalType.BUY if strength < 0.8 else SignalType.STRONG_BUY,
                        strength=strength,
                        confidence=confidence,
                        timestamp=datetime.utcnow(),
                        symbol=symbol,
                        price=current_price,
                        stop_loss=current_price * (1 - abs(prediction) * 0.5),
                        take_profit=current_price * (1 + abs(prediction) * 1.5),
                        reasoning=reasoning,
                        metadata={
                            'strategy': self.name,
                            'prediction': prediction,
                            'volatility': volatility.value,
                            'sentiment': sentiment.value
                        }
                    )
                    signals.append(signal)
                
                # Signal de vente (prédiction de baisse)
                elif prediction < -self.prediction_threshold:
                    strength = min(1.0, abs(prediction) * 10)
                    
                    reasoning.extend([
                        f"Prédiction ML: {prediction:.2%}",
                        f"Confiance: {confidence:.2%}",
                        f"Volatilité: {volatility.metadata.get('volatility_level', 'unknown')}",
                        f"Sentiment: {sentiment.metadata.get('sentiment_level', 'unknown')}"
                    ])
                    
                    signal = TradingSignal(
                        signal_type=SignalType.SELL if strength < 0.8 else SignalType.STRONG_SELL,
                        strength=strength,
                        confidence=confidence,
                        timestamp=datetime.utcnow(),
                        symbol=symbol,
                        price=current_price,
                        stop_loss=current_price * (1 + abs(prediction) * 0.5),
                        take_profit=current_price * (1 - abs(prediction) * 1.5),
                        reasoning=reasoning,
                        metadata={
                            'strategy': self.name,
                            'prediction': prediction,
                            'volatility': volatility.value,
                            'sentiment': sentiment.value
                        }
                    )
                    signals.append(signal)
        
        except Exception as e:
            self.logger.error(f"Erreur génération signaux ML: {e}")
        
        return signals
    
    def _get_latest_value(self, values: List[IndicatorValue]) -> Optional[IndicatorValue]:
        """Récupère la dernière valeur d'un indicateur"""
        if not values:
            return None
        return values[-1]


class SignalGenerator(IndicatorObserver):
    """Générateur principal de signaux (Observer Pattern)"""
    
    def __init__(self, name: str = "SignalGenerator"):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.strategies = []
        self.signals_history = []
        self.current_signals = {}
        self._event_bus: RedisEventBus | None = None
        
    def add_strategy(self, strategy: SignalStrategy):
        """Ajoute une stratégie"""
        self.strategies.append(strategy)
        self.logger.info(f"Stratégie ajoutée: {strategy.name}")
    
    def remove_strategy(self, strategy: SignalStrategy):
        """Supprime une stratégie"""
        if strategy in self.strategies:
            self.strategies.remove(strategy)
            self.logger.info(f"Stratégie supprimée: {strategy.name}")
    
    def update(self, signal: IndicatorSignal):
        """Met à jour avec un nouveau signal d'indicateur (Observer Pattern)"""
        # Traitement des signaux d'indicateurs
        pass
    
    def generate_signals(self, indicators: Dict[str, List[IndicatorValue]], 
                        current_price: float, symbol: str) -> List[TradingSignal]:
        """Génère des signaux en utilisant toutes les stratégies"""
        all_signals = []
        
        for strategy in self.strategies:
            try:
                strategy_signals = strategy.generate_signals(indicators, current_price, symbol)
                all_signals.extend(strategy_signals)
            except Exception as e:
                self.logger.error(f"Erreur stratégie {strategy.name}: {e}")
        
        # Combiner et filtrer les signaux
        combined_signals = self._combine_signals(all_signals)
        
        # Mettre à jour l'historique
        self.signals_history.extend(combined_signals)
        self.current_signals[symbol] = combined_signals
        # Publier les signaux générés
        self._publish_signals_sync(symbol, combined_signals)
        
        return combined_signals
    
    def _combine_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Combine et filtre les signaux"""
        if not signals:
            return []
        
        # Grouper par type de signal
        signal_groups = {}
        for signal in signals:
            key = (signal.signal_type, signal.symbol)
            if key not in signal_groups:
                signal_groups[key] = []
            signal_groups[key].append(signal)
        
        combined = []
        
        for (signal_type, symbol), group in signal_groups.items():
            if len(group) == 1:
                combined.append(group[0])
            else:
                # Combiner les signaux du même type
                combined_signal = self._merge_signals(group)
                combined.append(combined_signal)
        
        # Trier par force et confiance
        combined.sort(key=lambda x: (x.strength * x.confidence), reverse=True)
        
        return combined
    
    def _merge_signals(self, signals: List[TradingSignal]) -> TradingSignal:
        """Fusionne plusieurs signaux du même type"""
        if not signals:
            return None
        
        if len(signals) == 1:
            return signals[0]
        
        # Prendre le signal le plus récent comme base
        base_signal = max(signals, key=lambda x: x.timestamp)
        
        # Calculer les moyennes pondérées
        total_weight = sum(s.strength * s.confidence for s in signals)
        
        if total_weight > 0:
            weighted_strength = sum(s.strength * s.strength * s.confidence for s in signals) / total_weight
            weighted_confidence = sum(s.confidence * s.confidence for s in signals) / len(signals)
        else:
            weighted_strength = base_signal.strength
            weighted_confidence = base_signal.confidence
        
        # Combiner le raisonnement
        all_reasoning = []
        for signal in signals:
            all_reasoning.extend(signal.reasoning)
        
        # Créer le signal combiné
        combined = TradingSignal(
            signal_type=base_signal.signal_type,
            strength=min(1.0, weighted_strength),
            confidence=min(1.0, weighted_confidence),
            timestamp=base_signal.timestamp,
            symbol=base_signal.symbol,
            price=base_signal.price,
            stop_loss=base_signal.stop_loss,
            take_profit=base_signal.take_profit,
            reasoning=list(set(all_reasoning)),  # Supprimer les doublons
            metadata={
                'merged_from': [s.metadata.get('strategy', 'unknown') for s in signals],
                'original_count': len(signals)
            }
        )
        
        return combined
    
    def get_latest_signals(self, symbol: str) -> List[TradingSignal]:
        """Récupère les derniers signaux pour un symbole"""
        return self.current_signals.get(symbol, [])
    
    def get_signal_history(self, symbol: str = None, limit: int = 100) -> List[TradingSignal]:
        """Récupère l'historique des signaux"""
        if symbol:
            filtered = [s for s in self.signals_history if s.symbol == symbol]
        else:
            filtered = self.signals_history
        
        return filtered[-limit:] if limit else filtered
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques des signaux"""
        if not self.signals_history:
            return {}
        
        total_signals = len(self.signals_history)
        signal_types = {}
        
        for signal in self.signals_history:
            signal_type = signal.signal_type.value
            if signal_type not in signal_types:
                signal_types[signal_type] = 0
            signal_types[signal_type] += 1
        
        avg_strength = np.mean([s.strength for s in self.signals_history])
        avg_confidence = np.mean([s.confidence for s in self.signals_history])
        
        return {
            'total_signals': total_signals,
            'signal_types': signal_types,
            'average_strength': avg_strength,
            'average_confidence': avg_confidence,
            'strategies_count': len(self.strategies)
        }

    def _publish_signals_sync(self, symbol: str, signals: List[TradingSignal]) -> None:
        try:
            import asyncio
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                pass
            if loop and loop.is_running() and signals:
                loop.create_task(self._publish_signals_async(symbol, signals))
        except Exception:
            pass

    async def _publish_signals_async(self, symbol: str, signals: List[TradingSignal]) -> None:
        try:
            if self._event_bus is None:
                self._event_bus = RedisEventBus()
                await self._event_bus.connect()
            payload = {
                'symbol': symbol,
                'signals': [
                    {
                        'type': s.signal_type.value,
                        'strength': s.strength,
                        'confidence': s.confidence,
                        'timestamp': s.timestamp.isoformat(),
                        'price': s.price,
                        'stop_loss': s.stop_loss,
                        'take_profit': s.take_profit,
                        'metadata': s.metadata or {},
                    }
                    for s in signals
                ],
                'timestamp': datetime.utcnow().isoformat(),
            }
            await self._event_bus.publish('signals.generated', payload)
        except Exception:
            pass


# Factory pour les stratégies (Factory Pattern)
class StrategyFactory:
    """Factory pour créer des stratégies de signaux"""
    
    _strategies = {
        'trend_following': TrendFollowingStrategy,
        'mean_reversion': MeanReversionStrategy,
        'ml_prediction': MLPredictionStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_type: str, **kwargs) -> SignalStrategy:
        """Crée une stratégie"""
        if strategy_type not in cls._strategies:
            raise ValueError(f"Type de stratégie inconnu: {strategy_type}")
        
        strategy_class = cls._strategies[strategy_type]
        return strategy_class(**kwargs)
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """Retourne les stratégies disponibles"""
        return list(cls._strategies.keys())


# Instance globale du générateur de signaux
signal_generator = SignalGenerator()