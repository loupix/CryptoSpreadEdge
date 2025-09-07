"""
Base classes pour les indicateurs financiers avec design patterns
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
import pandas as pd
from enum import Enum


class IndicatorType(Enum):
    """Types d'indicateurs"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    SUPPORT_RESISTANCE = "support_resistance"
    OSCILLATOR = "oscillator"
    CUSTOM = "custom"


class Timeframe(Enum):
    """Timeframes supportés"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


@dataclass
class IndicatorValue:
    """Valeur d'un indicateur"""
    value: float
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict[str, Any] = None


@dataclass
class IndicatorSignal:
    """Signal généré par un indicateur"""
    signal_type: str  # "buy", "sell", "hold", "strong_buy", "strong_sell"
    strength: float  # 0-1
    value: float
    timestamp: datetime
    confidence: float
    metadata: Dict[str, Any] = None


class BaseIndicator(ABC):
    """Classe de base pour tous les indicateurs (Template Method Pattern)"""
    
    def __init__(self, name: str, indicator_type: IndicatorType, timeframe: Timeframe):
        self.name = name
        self.indicator_type = indicator_type
        self.timeframe = timeframe
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.is_initialized = False
        self.cache = {}
        self.observers = []  # Observer Pattern
        
    def add_observer(self, observer: 'IndicatorObserver'):
        """Ajoute un observateur (Observer Pattern)"""
        self.observers.append(observer)
    
    def remove_observer(self, observer: 'IndicatorObserver'):
        """Supprime un observateur"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_observers(self, signal: IndicatorSignal):
        """Notifie tous les observateurs (Observer Pattern)"""
        for observer in self.observers:
            observer.update(signal)
    
    def calculate(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Méthode template pour le calcul (Template Method Pattern)"""
        try:
            # Validation des données
            if not self._validate_data(data):
                return []
            
            # Préparation des données
            prepared_data = self._prepare_data(data)
            
            # Calcul de l'indicateur
            values = self._calculate_indicator(prepared_data)
            
            # Post-traitement
            processed_values = self._post_process(values)
            
            # Génération des signaux
            signals = self._generate_signals(processed_values)
            
            # Notification des observateurs
            for signal in signals:
                self.notify_observers(signal)
            
            return processed_values
        
        except Exception as e:
            self.logger.error(f"Erreur calcul indicateur {self.name}: {e}")
            return []
    
    def _validate_data(self, data: pd.DataFrame) -> bool:
        """Valide les données d'entrée"""
        if data.empty:
            self.logger.warning("Données vides")
            return False
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            self.logger.error(f"Colonnes manquantes: {missing_columns}")
            return False
        
        return True
    
    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prépare les données pour le calcul"""
        return data.copy()
    
    @abstractmethod
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule l'indicateur (à implémenter par les sous-classes)"""
        pass
    
    def _post_process(self, values: List[IndicatorValue]) -> List[IndicatorValue]:
        """Post-traitement des valeurs"""
        return values
    
    def _generate_signals(self, values: List[IndicatorValue]) -> List[IndicatorSignal]:
        """Génère les signaux basés sur les valeurs"""
        signals = []
        
        if len(values) < 2:
            return signals
        
        # Logique de génération de signaux (à personnaliser)
        for i, value in enumerate(values[1:], 1):
            prev_value = values[i-1]
            
            # Signal basé sur la variation
            if value.value > prev_value.value * 1.02:  # +2%
                signal = IndicatorSignal(
                    signal_type="buy",
                    strength=min(1.0, (value.value - prev_value.value) / prev_value.value),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=value.confidence
                )
                signals.append(signal)
            elif value.value < prev_value.value * 0.98:  # -2%
                signal = IndicatorSignal(
                    signal_type="sell",
                    strength=min(1.0, (prev_value.value - value.value) / prev_value.value),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=value.confidence
                )
                signals.append(signal)
        
        return signals
    
    def get_cached_value(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        return self.cache.get(key)
    
    def set_cached_value(self, key: str, value: Any):
        """Met une valeur en cache"""
        self.cache[key] = value
    
    def clear_cache(self):
        """Vide le cache"""
        self.cache.clear()


class IndicatorObserver(ABC):
    """Interface pour les observateurs d'indicateurs (Observer Pattern)"""
    
    @abstractmethod
    def update(self, signal: IndicatorSignal):
        """Met à jour l'observateur avec un nouveau signal"""
        pass


class IndicatorFactory:
    """Factory pour créer des indicateurs (Factory Pattern)"""
    
    _indicators = {}
    
    @classmethod
    def register_indicator(cls, name: str, indicator_class: type):
        """Enregistre un type d'indicateur"""
        cls._indicators[name] = indicator_class
    
    @classmethod
    def create_indicator(cls, name: str, indicator_type: str, **kwargs) -> BaseIndicator:
        """Crée un indicateur"""
        if indicator_type not in cls._indicators:
            raise ValueError(f"Type d'indicateur inconnu: {indicator_type}")
        
        indicator_class = cls._indicators[indicator_type]
        return indicator_class(name=name, **kwargs)
    
    @classmethod
    def get_available_indicators(cls) -> List[str]:
        """Retourne la liste des indicateurs disponibles"""
        return list(cls._indicators.keys())


class IndicatorComposite:
    """Composite pour gérer plusieurs indicateurs (Composite Pattern)"""
    
    def __init__(self, name: str):
        self.name = name
        self.indicators = []
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def add_indicator(self, indicator: BaseIndicator):
        """Ajoute un indicateur au composite"""
        self.indicators.append(indicator)
    
    def remove_indicator(self, indicator: BaseIndicator):
        """Supprime un indicateur du composite"""
        if indicator in self.indicators:
            self.indicators.remove(indicator)
    
    def calculate_all(self, data: pd.DataFrame) -> Dict[str, List[IndicatorValue]]:
        """Calcule tous les indicateurs"""
        results = {}
        
        for indicator in self.indicators:
            try:
                values = indicator.calculate(data)
                results[indicator.name] = values
            except Exception as e:
                self.logger.error(f"Erreur calcul {indicator.name}: {e}")
                results[indicator.name] = []
        
        return results
    
    def get_combined_signals(self, data: pd.DataFrame) -> List[IndicatorSignal]:
        """Combine les signaux de tous les indicateurs"""
        all_signals = []
        
        for indicator in self.indicators:
            try:
                values = indicator.calculate(data)
                signals = indicator._generate_signals(values)
                all_signals.extend(signals)
            except Exception as e:
                self.logger.error(f"Erreur signaux {indicator.name}: {e}")
        
        return all_signals


class IndicatorStrategy:
    """Stratégie pour le calcul d'indicateurs (Strategy Pattern)"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.logger = logging.getLogger(f"{__name__}.{strategy_name}")
    
    def calculate(self, data: pd.DataFrame, indicator: BaseIndicator) -> List[IndicatorValue]:
        """Calcule l'indicateur selon la stratégie"""
        raise NotImplementedError


class SimpleMovingAverageStrategy(IndicatorStrategy):
    """Stratégie pour les moyennes mobiles simples"""
    
    def __init__(self, period: int = 20):
        super().__init__("SMA")
        self.period = period
    
    def calculate(self, data: pd.DataFrame, indicator: BaseIndicator) -> List[IndicatorValue]:
        """Calcule la moyenne mobile simple"""
        if len(data) < self.period:
            return []
        
        values = []
        for i in range(self.period - 1, len(data)):
            period_data = data.iloc[i - self.period + 1:i + 1]
            sma_value = period_data['close'].mean()
            
            value = IndicatorValue(
                value=sma_value,
                timestamp=period_data.index[-1],
                confidence=1.0,
                metadata={'period': self.period}
            )
            values.append(value)
        
        return values


class ExponentialMovingAverageStrategy(IndicatorStrategy):
    """Stratégie pour les moyennes mobiles exponentielles"""
    
    def __init__(self, period: int = 20, alpha: float = None):
        super().__init__("EMA")
        self.period = period
        self.alpha = alpha or (2.0 / (period + 1))
    
    def calculate(self, data: pd.DataFrame, indicator: BaseIndicator) -> List[IndicatorValue]:
        """Calcule la moyenne mobile exponentielle"""
        if len(data) < self.period:
            return []
        
        values = []
        ema = data['close'].iloc[0]  # Initialisation
        
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if i == 0:
                continue
            
            ema = self.alpha * row['close'] + (1 - self.alpha) * ema
            
            value = IndicatorValue(
                value=ema,
                timestamp=timestamp,
                confidence=1.0,
                metadata={'period': self.period, 'alpha': self.alpha}
            )
            values.append(value)
        
        return values


class IndicatorCommand:
    """Commande pour exécuter des indicateurs (Command Pattern)"""
    
    def __init__(self, indicator: BaseIndicator, data: pd.DataFrame):
        self.indicator = indicator
        self.data = data
        self.result = None
        self.executed = False
    
    def execute(self) -> List[IndicatorValue]:
        """Exécute la commande"""
        if not self.executed:
            self.result = self.indicator.calculate(self.data)
            self.executed = True
        return self.result
    
    def undo(self):
        """Annule la commande (si possible)"""
        self.result = None
        self.executed = False


class IndicatorInvoker:
    """Invokeur pour les commandes d'indicateurs (Command Pattern)"""
    
    def __init__(self):
        self.history = []
        self.logger = logging.getLogger(__name__)
    
    def execute_command(self, command: IndicatorCommand) -> List[IndicatorValue]:
        """Exécute une commande"""
        try:
            result = command.execute()
            self.history.append(command)
            return result
        except Exception as e:
            self.logger.error(f"Erreur exécution commande: {e}")
            return []
    
    def get_history(self) -> List[IndicatorCommand]:
        """Retourne l'historique des commandes"""
        return self.history.copy()


# Décorateur pour les indicateurs (Decorator Pattern)
def indicator_decorator(func):
    """Décorateur pour ajouter des fonctionnalités aux indicateurs"""
    def wrapper(self, data: pd.DataFrame) -> List[IndicatorValue]:
        start_time = datetime.utcnow()
        
        # Exécution de la fonction
        result = func(self, data)
        
        # Calcul du temps d'exécution
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Mise en cache des métadonnées
        self.set_cached_value('last_execution_time', execution_time)
        self.set_cached_value('last_calculation_count', len(result))
        
        return result
    
    return wrapper


# Singleton pour le gestionnaire d'indicateurs (Singleton Pattern)
class IndicatorManager:
    """Gestionnaire global des indicateurs (Singleton Pattern)"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not IndicatorManager._initialized:
            self.indicators = {}
            self.composites = {}
            self.invoker = IndicatorInvoker()
            self.logger = logging.getLogger(__name__)
            IndicatorManager._initialized = True
    
    def register_indicator(self, name: str, indicator: BaseIndicator):
        """Enregistre un indicateur"""
        self.indicators[name] = indicator
        self.logger.info(f"Indicateur enregistré: {name}")
    
    def get_indicator(self, name: str) -> Optional[BaseIndicator]:
        """Récupère un indicateur"""
        return self.indicators.get(name)
    
    def calculate_indicator(self, name: str, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule un indicateur"""
        indicator = self.get_indicator(name)
        if not indicator:
            self.logger.error(f"Indicateur non trouvé: {name}")
            return []
        
        command = IndicatorCommand(indicator, data)
        return self.invoker.execute_command(command)
    
    def get_all_indicators(self) -> Dict[str, BaseIndicator]:
        """Retourne tous les indicateurs"""
        return self.indicators.copy()


# Instance globale du gestionnaire
indicator_manager = IndicatorManager()