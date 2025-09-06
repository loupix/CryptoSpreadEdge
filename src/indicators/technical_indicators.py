"""
Indicateurs techniques classiques avec design patterns optimisés
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import talib
from .base_indicator import (
    BaseIndicator, IndicatorValue, IndicatorSignal, IndicatorType, 
    Timeframe, indicator_decorator, IndicatorFactory
)


class MovingAverageIndicator(BaseIndicator):
    """Indicateur de moyenne mobile (SMA, EMA, WMA)"""
    
    def __init__(self, name: str, ma_type: str = "SMA", period: int = 20, 
                 timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.TREND, timeframe)
        self.ma_type = ma_type.upper()
        self.period = period
        self.alpha = 2.0 / (period + 1) if ma_type.upper() == "EMA" else None
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule la moyenne mobile"""
        if len(data) < self.period:
            return []
        
        values = []
        close_prices = data['close'].values
        
        if self.ma_type == "SMA":
            ma_values = talib.SMA(close_prices, timeperiod=self.period)
        elif self.ma_type == "EMA":
            ma_values = talib.EMA(close_prices, timeperiod=self.period)
        elif self.ma_type == "WMA":
            ma_values = talib.WMA(close_prices, timeperiod=self.period)
        else:
            raise ValueError(f"Type de MA non supporté: {self.ma_type}")
        
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if not np.isnan(ma_values[i]):
                value = IndicatorValue(
                    value=float(ma_values[i]),
                    timestamp=timestamp,
                    confidence=1.0,
                    metadata={
                        'ma_type': self.ma_type,
                        'period': self.period,
                        'alpha': self.alpha
                    }
                )
                values.append(value)
        
        return values


class RSIIndicator(BaseIndicator):
    """Indicateur RSI (Relative Strength Index)"""
    
    def __init__(self, name: str, period: int = 14, 
                 timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.OSCILLATOR, timeframe)
        self.period = period
        self.overbought = 70
        self.oversold = 30
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule le RSI"""
        if len(data) < self.period + 1:
            return []
        
        close_prices = data['close'].values
        rsi_values = talib.RSI(close_prices, timeperiod=self.period)
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if not np.isnan(rsi_values[i]):
                rsi_value = float(rsi_values[i])
                
                # Calcul de la confiance basé sur la position dans la plage
                if rsi_value > self.overbought or rsi_value < self.oversold:
                    confidence = 0.9
                else:
                    confidence = 0.7
                
                value = IndicatorValue(
                    value=rsi_value,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'period': self.period,
                        'overbought': self.overbought,
                        'oversold': self.oversold,
                        'signal_zone': 'overbought' if rsi_value > self.overbought 
                                     else 'oversold' if rsi_value < self.oversold 
                                     else 'neutral'
                    }
                )
                values.append(value)
        
        return values
    
    def _generate_signals(self, values: List[IndicatorValue]) -> List[IndicatorSignal]:
        """Génère des signaux RSI spécifiques"""
        signals = []
        
        if len(values) < 2:
            return signals
        
        for i, value in enumerate(values[1:], 1):
            prev_value = values[i-1]
            
            # Signal de survente (achat)
            if (prev_value.value <= self.oversold and 
                value.value > self.oversold):
                signal = IndicatorSignal(
                    signal_type="buy",
                    strength=min(1.0, (self.oversold - prev_value.value) / 10),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=value.confidence,
                    metadata={'indicator': 'RSI', 'signal': 'oversold_bounce'}
                )
                signals.append(signal)
            
            # Signal de surachat (vente)
            elif (prev_value.value >= self.overbought and 
                  value.value < self.overbought):
                signal = IndicatorSignal(
                    signal_type="sell",
                    strength=min(1.0, (prev_value.value - self.overbought) / 10),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=value.confidence,
                    metadata={'indicator': 'RSI', 'signal': 'overbought_rejection'}
                )
                signals.append(signal)
        
        return signals


class MACDIndicator(BaseIndicator):
    """Indicateur MACD (Moving Average Convergence Divergence)"""
    
    def __init__(self, name: str, fast_period: int = 12, slow_period: int = 26, 
                 signal_period: int = 9, timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.MOMENTUM, timeframe)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule le MACD"""
        if len(data) < self.slow_period + self.signal_period:
            return []
        
        close_prices = data['close'].values
        macd, signal, histogram = talib.MACD(
            close_prices, 
            fastperiod=self.fast_period,
            slowperiod=self.slow_period,
            signalperiod=self.signal_period
        )
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if not np.isnan(macd[i]) and not np.isnan(signal[i]):
                macd_value = float(macd[i])
                signal_value = float(signal[i])
                histogram_value = float(histogram[i])
                
                # Calcul de la confiance basé sur la divergence
                divergence_strength = abs(histogram_value) / (abs(macd_value) + 1e-8)
                confidence = min(1.0, divergence_strength * 2)
                
                value = IndicatorValue(
                    value=macd_value,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'macd': macd_value,
                        'signal': signal_value,
                        'histogram': histogram_value,
                        'fast_period': self.fast_period,
                        'slow_period': self.slow_period,
                        'signal_period': self.signal_period
                    }
                )
                values.append(value)
        
        return values
    
    def _generate_signals(self, values: List[IndicatorValue]) -> List[IndicatorSignal]:
        """Génère des signaux MACD spécifiques"""
        signals = []
        
        if len(values) < 2:
            return signals
        
        for i, value in enumerate(values[1:], 1):
            prev_value = values[i-1]
            
            # Croisement MACD au-dessus de la ligne de signal (achat)
            if (prev_value.metadata['macd'] <= prev_value.metadata['signal'] and
                value.metadata['macd'] > value.metadata['signal']):
                signal = IndicatorSignal(
                    signal_type="buy",
                    strength=min(1.0, abs(value.metadata['histogram']) * 10),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=value.confidence,
                    metadata={'indicator': 'MACD', 'signal': 'bullish_crossover'}
                )
                signals.append(signal)
            
            # Croisement MACD en-dessous de la ligne de signal (vente)
            elif (prev_value.metadata['macd'] >= prev_value.metadata['signal'] and
                  value.metadata['macD'] < value.metadata['signal']):
                signal = IndicatorSignal(
                    signal_type="sell",
                    strength=min(1.0, abs(value.metadata['histogram']) * 10),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=value.confidence,
                    metadata={'indicator': 'MACD', 'signal': 'bearish_crossover'}
                )
                signals.append(signal)
        
        return signals


class BollingerBandsIndicator(BaseIndicator):
    """Indicateur des Bandes de Bollinger"""
    
    def __init__(self, name: str, period: int = 20, std_dev: float = 2.0,
                 timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.VOLATILITY, timeframe)
        self.period = period
        self.std_dev = std_dev
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule les Bandes de Bollinger"""
        if len(data) < self.period:
            return []
        
        close_prices = data['close'].values
        upper, middle, lower = talib.BBANDS(
            close_prices, 
            timeperiod=self.period,
            nbdevup=self.std_dev,
            nbdevdn=self.std_dev
        )
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if not np.isnan(upper[i]) and not np.isnan(lower[i]):
                upper_value = float(upper[i])
                lower_value = float(lower[i])
                middle_value = float(middle[i])
                current_price = float(row['close'])
                
                # Calcul de la position dans les bandes
                band_width = upper_value - lower_value
                position = (current_price - lower_value) / band_width if band_width > 0 else 0.5
                
                # Calcul de la confiance basé sur la position
                if position > 0.8 or position < 0.2:
                    confidence = 0.9
                else:
                    confidence = 0.6
                
                value = IndicatorValue(
                    value=position,  # Position normalisée dans les bandes
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'upper': upper_value,
                        'middle': middle_value,
                        'lower': lower_value,
                        'band_width': band_width,
                        'position': position,
                        'period': self.period,
                        'std_dev': self.std_dev
                    }
                )
                values.append(value)
        
        return values
    
    def _generate_signals(self, values: List[IndicatorValue]) -> List[IndicatorSignal]:
        """Génère des signaux Bollinger Bands spécifiques"""
        signals = []
        
        if len(values) < 2:
            return signals
        
        for i, value in enumerate(values[1:], 1):
            prev_value = values[i-1]
            
            # Sortie de la bande inférieure (achat)
            if (prev_value.metadata['position'] <= 0.1 and 
                value.metadata['position'] > 0.1):
                signal = IndicatorSignal(
                    signal_type="buy",
                    strength=min(1.0, (0.1 - prev_value.metadata['position']) * 10),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=value.confidence,
                    metadata={'indicator': 'BB', 'signal': 'lower_band_bounce'}
                )
                signals.append(signal)
            
            # Sortie de la bande supérieure (vente)
            elif (prev_value.metadata['position'] >= 0.9 and 
                  value.metadata['position'] < 0.9):
                signal = IndicatorSignal(
                    signal_type="sell",
                    strength=min(1.0, (prev_value.metadata['position'] - 0.9) * 10),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=value.confidence,
                    metadata={'indicator': 'BB', 'signal': 'upper_band_rejection'}
                )
                signals.append(signal)
        
        return signals


class StochasticIndicator(BaseIndicator):
    """Indicateur Stochastique"""
    
    def __init__(self, name: str, k_period: int = 14, d_period: int = 3,
                 timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.OSCILLATOR, timeframe)
        self.k_period = k_period
        self.d_period = d_period
        self.overbought = 80
        self.oversold = 20
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule le Stochastique"""
        if len(data) < self.k_period:
            return []
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        close_prices = data['close'].values
        
        slowk, slowd = talib.STOCH(
            high_prices, low_prices, close_prices,
            fastk_period=self.k_period,
            slowk_period=self.d_period,
            slowd_period=self.d_period
        )
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if not np.isnan(slowk[i]) and not np.isnan(slowd[i]):
                k_value = float(slowk[i])
                d_value = float(slowd[i])
                
                # Calcul de la confiance basé sur la divergence
                divergence = abs(k_value - d_value)
                confidence = min(1.0, divergence / 20)
                
                value = IndicatorValue(
                    value=k_value,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'k_percent': k_value,
                        'd_percent': d_value,
                        'divergence': divergence,
                        'k_period': self.k_period,
                        'd_period': self.d_period,
                        'overbought': self.overbought,
                        'oversold': self.oversold
                    }
                )
                values.append(value)
        
        return values


class VolumeIndicator(BaseIndicator):
    """Indicateur de volume"""
    
    def __init__(self, name: str, period: int = 20, timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.VOLUME, timeframe)
        self.period = period
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule l'indicateur de volume"""
        if len(data) < self.period:
            return []
        
        volume = data['volume'].values
        close_prices = data['close'].values
        
        # Volume moyen
        volume_sma = talib.SMA(volume, timeperiod=self.period)
        
        # On Balance Volume (OBV)
        obv = talib.OBV(close_prices, volume)
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if not np.isnan(volume_sma[i]):
                current_volume = float(volume[i])
                avg_volume = float(volume_sma[i])
                obv_value = float(obv[i]) if not np.isnan(obv[i]) else 0
                
                # Ratio de volume
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                
                # Confiance basée sur l'anomalie de volume
                if volume_ratio > 2.0 or volume_ratio < 0.5:
                    confidence = 0.9
                else:
                    confidence = 0.6
                
                value = IndicatorValue(
                    value=volume_ratio,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'current_volume': current_volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': volume_ratio,
                        'obv': obv_value,
                        'period': self.period
                    }
                )
                values.append(value)
        
        return values


class ATRIndicator(BaseIndicator):
    """Indicateur ATR (Average True Range)"""
    
    def __init__(self, name: str, period: int = 14, timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.VOLATILITY, timeframe)
        self.period = period
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule l'ATR"""
        if len(data) < self.period + 1:
            return []
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        close_prices = data['close'].values
        
        atr_values = talib.ATR(high_prices, low_prices, close_prices, timeperiod=self.period)
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if not np.isnan(atr_values[i]):
                atr_value = float(atr_values[i])
                current_price = float(row['close'])
                
                # ATR normalisé par le prix
                atr_percentage = (atr_value / current_price) * 100 if current_price > 0 else 0
                
                # Confiance basée sur la volatilité
                if atr_percentage > 5.0:  # Haute volatilité
                    confidence = 0.9
                elif atr_percentage > 2.0:  # Volatilité moyenne
                    confidence = 0.7
                else:  # Faible volatilité
                    confidence = 0.5
                
                value = IndicatorValue(
                    value=atr_value,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'atr': atr_value,
                        'atr_percentage': atr_percentage,
                        'period': self.period,
                        'volatility_level': 'high' if atr_percentage > 5.0 
                                         else 'medium' if atr_percentage > 2.0 
                                         else 'low'
                    }
                )
                values.append(value)
        
        return values


# Enregistrement des indicateurs dans la factory
IndicatorFactory.register_indicator("SMA", MovingAverageIndicator)
IndicatorFactory.register_indicator("EMA", MovingAverageIndicator)
IndicatorFactory.register_indicator("RSI", RSIIndicator)
IndicatorFactory.register_indicator("MACD", MACDIndicator)
IndicatorFactory.register_indicator("BOLLINGER", BollingerBandsIndicator)
IndicatorFactory.register_indicator("STOCHASTIC", StochasticIndicator)
IndicatorFactory.register_indicator("VOLUME", VolumeIndicator)
IndicatorFactory.register_indicator("ATR", ATRIndicator)