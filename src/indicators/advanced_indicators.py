"""
Indicateurs avancés et de prédiction avec machine learning
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import talib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

from .base_indicator import (
    BaseIndicator, IndicatorValue, IndicatorSignal, IndicatorType, 
    Timeframe, indicator_decorator, IndicatorFactory
)


class IchimokuIndicator(BaseIndicator):
    """Indicateur Ichimoku Cloud complet"""
    
    def __init__(self, name: str, tenkan_period: int = 9, kijun_period: int = 26,
                 senkou_span_b_period: int = 52, timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.TREND, timeframe)
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_span_b_period = senkou_span_b_period
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule l'Ichimoku Cloud"""
        if len(data) < self.senkou_span_b_period + 26:
            return []
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        close_prices = data['close'].values
        
        # Calcul des composants Ichimoku
        tenkan_sen = self._calculate_tenkan_sen(high_prices, low_prices, self.tenkan_period)
        kijun_sen = self._calculate_kijun_sen(high_prices, low_prices, self.kijun_period)
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        senkou_span_b = self._calculate_senkou_span_b(high_prices, low_prices, self.senkou_span_b_period)
        chikou_span = np.roll(close_prices, -26)
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if i < len(tenkan_sen) and not np.isnan(tenkan_sen[i]):
                current_price = float(row['close'])
                
                # Position par rapport au cloud
                cloud_top = max(senkou_span_a[i], senkou_span_b[i])
                cloud_bottom = min(senkou_span_a[i], senkou_span_b[i])
                
                if current_price > cloud_top:
                    position = 1.0  # Au-dessus du cloud
                elif current_price < cloud_bottom:
                    position = -1.0  # En-dessous du cloud
                else:
                    position = 0.0  # Dans le cloud
                
                # Confiance basée sur la distance au cloud
                cloud_distance = abs(current_price - (cloud_top + cloud_bottom) / 2)
                confidence = min(1.0, cloud_distance / (current_price * 0.1))
                
                value = IndicatorValue(
                    value=position,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'tenkan_sen': float(tenkan_sen[i]),
                        'kijun_sen': float(kijun_sen[i]),
                        'senkou_span_a': float(senkou_span_a[i]),
                        'senkou_span_b': float(senkou_span_b[i]),
                        'chikou_span': float(chikou_span[i]),
                        'cloud_top': float(cloud_top),
                        'cloud_bottom': float(cloud_bottom),
                        'position': position
                    }
                )
                values.append(value)
        
        return values
    
    def _calculate_tenkan_sen(self, high: np.ndarray, low: np.ndarray, period: int) -> np.ndarray:
        """Calcule la ligne Tenkan-sen"""
        result = np.full(len(high), np.nan)
        for i in range(period - 1, len(high)):
            period_high = np.max(high[i - period + 1:i + 1])
            period_low = np.min(low[i - period + 1:i + 1])
            result[i] = (period_high + period_low) / 2
        return result
    
    def _calculate_kijun_sen(self, high: np.ndarray, low: np.ndarray, period: int) -> np.ndarray:
        """Calcule la ligne Kijun-sen"""
        return self._calculate_tenkan_sen(high, low, period)
    
    def _calculate_senkou_span_b(self, high: np.ndarray, low: np.ndarray, period: int) -> np.ndarray:
        """Calcule la ligne Senkou Span B"""
        return self._calculate_tenkan_sen(high, low, period)


class WilliamsRIndicator(BaseIndicator):
    """Indicateur Williams %R"""
    
    def __init__(self, name: str, period: int = 14, timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.OSCILLATOR, timeframe)
        self.period = period
        self.overbought = -20
        self.oversold = -80
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule Williams %R"""
        if len(data) < self.period:
            return []
        
        high_prices = data['high'].values
        low_prices = data['low'].values
        close_prices = data['close'].values
        
        williams_r = talib.WILLR(high_prices, low_prices, close_prices, timeperiod=self.period)
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if not np.isnan(williams_r[i]):
                wr_value = float(williams_r[i])
                
                # Confiance basée sur la position dans la plage
                if wr_value > self.overbought or wr_value < self.oversold:
                    confidence = 0.9
                else:
                    confidence = 0.6
                
                value = IndicatorValue(
                    value=wr_value,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'williams_r': wr_value,
                        'period': self.period,
                        'overbought': self.overbought,
                        'oversold': self.oversold,
                        'signal_zone': 'overbought' if wr_value > self.overbought 
                                     else 'oversold' if wr_value < self.oversold 
                                     else 'neutral'
                    }
                )
                values.append(value)
        
        return values


class MLPredictionIndicator(BaseIndicator):
    """Indicateur de prédiction basé sur Machine Learning"""
    
    def __init__(self, name: str, model_type: str = "RandomForest", 
                 lookback_period: int = 50, prediction_horizon: int = 5,
                 timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.CUSTOM, timeframe)
        self.model_type = model_type
        self.lookback_period = lookback_period
        self.prediction_horizon = prediction_horizon
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'open', 'high', 'low', 'close', 'volume',
            'sma_5', 'sma_10', 'sma_20', 'sma_50',
            'ema_5', 'ema_10', 'ema_20',
            'rsi_14', 'macd', 'bb_position', 'atr'
        ]
    
    def _create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Crée les features pour le modèle ML"""
        features = data.copy()
        
        # Moyennes mobiles
        features['sma_5'] = talib.SMA(data['close'], timeperiod=5)
        features['sma_10'] = talib.SMA(data['close'], timeperiod=10)
        features['sma_20'] = talib.SMA(data['close'], timeperiod=20)
        features['sma_50'] = talib.SMA(data['close'], timeperiod=50)
        
        # Moyennes mobiles exponentielles
        features['ema_5'] = talib.EMA(data['close'], timeperiod=5)
        features['ema_10'] = talib.EMA(data['close'], timeperiod=10)
        features['ema_20'] = talib.EMA(data['close'], timeperiod=20)
        
        # RSI
        features['rsi_14'] = talib.RSI(data['close'], timeperiod=14)
        
        # MACD
        macd, _, _ = talib.MACD(data['close'])
        features['macd'] = macd
        
        # Bollinger Bands position
        upper, middle, lower = talib.BBANDS(data['close'])
        features['bb_position'] = (data['close'] - lower) / (upper - lower)
        
        # ATR
        features['atr'] = talib.ATR(data['high'], data['low'], data['close'])
        
        # Features de momentum
        features['price_change'] = data['close'].pct_change()
        features['volume_change'] = data['volume'].pct_change()
        features['high_low_ratio'] = data['high'] / data['low']
        features['close_open_ratio'] = data['close'] / data['open']
        
        # Features de volatilité
        features['volatility_5'] = data['close'].rolling(5).std()
        features['volatility_20'] = data['close'].rolling(20).std()
        
        return features
    
    def _prepare_training_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prépare les données d'entraînement"""
        features = self._create_features(data)
        
        # Supprimer les NaN
        features = features.dropna()
        
        if len(features) < self.lookback_period + self.prediction_horizon:
            return np.array([]), np.array([])
        
        X = []
        y = []
        
        for i in range(self.lookback_period, len(features) - self.prediction_horizon):
            # Features: fenêtre glissante
            feature_window = features.iloc[i - self.lookback_period:i][self.feature_columns].values
            X.append(feature_window.flatten())
            
            # Target: prix futur
            future_price = features.iloc[i + self.prediction_horizon]['close']
            current_price = features.iloc[i]['close']
            price_change = (future_price - current_price) / current_price
            y.append(price_change)
        
        return np.array(X), np.array(y)
    
    def train_model(self, data: pd.DataFrame) -> Dict[str, float]:
        """Entraîne le modèle ML"""
        X, y = self._prepare_training_data(data)
        
        if len(X) == 0:
            return {'error': 'Pas assez de données pour l\'entraînement'}
        
        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Normalisation
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Création du modèle
        if self.model_type == "RandomForest":
            self.model = RandomForestRegressor(
                n_estimators=100, 
                max_depth=10, 
                random_state=42
            )
        elif self.model_type == "GradientBoosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100, 
                max_depth=6, 
                random_state=42
            )
        elif self.model_type == "NeuralNetwork":
            self.model = MLPRegressor(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=42
            )
        else:
            raise ValueError(f"Type de modèle non supporté: {self.model_type}")
        
        # Entraînement
        self.model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = self.model.predict(X_test_scaled)
        
        # Métriques
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        self.is_trained = True
        
        return {
            'mse': mse,
            'r2_score': r2,
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule les prédictions ML"""
        if not self.is_trained:
            # Entraîner le modèle si pas encore fait
            self.train_model(data)
        
        if not self.is_trained or self.model is None:
            return []
        
        features = self._create_features(data)
        features = features.dropna()
        
        if len(features) < self.lookback_period:
            return []
        
        values = []
        
        # Prédiction pour chaque point
        for i in range(self.lookback_period, len(features)):
            # Préparer les features
            feature_window = features.iloc[i - self.lookback_period:i][self.feature_columns].values
            X = feature_window.flatten().reshape(1, -1)
            X_scaled = self.scaler.transform(X)
            
            # Prédiction
            prediction = self.model.predict(X_scaled)[0]
            current_price = features.iloc[i]['close']
            predicted_price = current_price * (1 + prediction)
            
            # Confiance basée sur la cohérence des prédictions
            confidence = min(1.0, abs(prediction) * 10)  # Plus la prédiction est forte, plus la confiance est élevée
            
            value = IndicatorValue(
                value=prediction,  # Changement de prix prédit
                timestamp=features.index[i],
                confidence=confidence,
                metadata={
                    'predicted_price': predicted_price,
                    'current_price': current_price,
                    'price_change_prediction': prediction,
                    'model_type': self.model_type,
                    'lookback_period': self.lookback_period,
                    'prediction_horizon': self.prediction_horizon
                }
            )
            values.append(value)
        
        return values
    
    def _generate_signals(self, values: List[IndicatorValue]) -> List[IndicatorSignal]:
        """Génère des signaux basés sur les prédictions ML"""
        signals = []
        
        if len(values) < 2:
            return signals
        
        for i, value in enumerate(values[1:], 1):
            prev_value = values[i-1]
            
            # Signal basé sur la prédiction de changement de prix
            prediction = value.value
            confidence = value.confidence
            
            if prediction > 0.02 and confidence > 0.7:  # Prédiction de hausse > 2%
                signal = IndicatorSignal(
                    signal_type="buy",
                    strength=min(1.0, prediction * 10),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=confidence,
                    metadata={
                        'indicator': 'ML_Prediction',
                        'signal': 'bullish_prediction',
                        'predicted_change': prediction
                    }
                )
                signals.append(signal)
            
            elif prediction < -0.02 and confidence > 0.7:  # Prédiction de baisse > 2%
                signal = IndicatorSignal(
                    signal_type="sell",
                    strength=min(1.0, abs(prediction) * 10),
                    value=value.value,
                    timestamp=value.timestamp,
                    confidence=confidence,
                    metadata={
                        'indicator': 'ML_Prediction',
                        'signal': 'bearish_prediction',
                        'predicted_change': prediction
                    }
                )
                signals.append(signal)
        
        return signals


class SentimentIndicator(BaseIndicator):
    """Indicateur de sentiment basé sur l'analyse des données"""
    
    def __init__(self, name: str, timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.CUSTOM, timeframe)
        self.sentiment_data = []
    
    def add_sentiment_data(self, sentiment_score: float, timestamp: datetime, source: str):
        """Ajoute des données de sentiment"""
        self.sentiment_data.append({
            'score': sentiment_score,
            'timestamp': timestamp,
            'source': source
        })
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule l'indicateur de sentiment"""
        if not self.sentiment_data:
            return []
        
        # Convertir en DataFrame
        sentiment_df = pd.DataFrame(self.sentiment_data)
        sentiment_df = sentiment_df.set_index('timestamp')
        
        # Agréger par timeframe
        sentiment_df = sentiment_df.resample('1H').mean()
        
        values = []
        for timestamp, row in sentiment_df.iterrows():
            sentiment_score = row['score']
            
            # Confiance basée sur la cohérence des sources
            sources_count = len(self.sentiment_data)
            confidence = min(1.0, sources_count / 10)  # Plus de sources = plus de confiance
            
            value = IndicatorValue(
                value=sentiment_score,
                timestamp=timestamp,
                confidence=confidence,
                metadata={
                    'sentiment_score': sentiment_score,
                    'sources_count': sources_count,
                    'sentiment_level': 'bullish' if sentiment_score > 0.5 
                                     else 'bearish' if sentiment_score < -0.5 
                                     else 'neutral'
                }
            )
            values.append(value)
        
        return values


class VolatilityIndicator(BaseIndicator):
    """Indicateur de volatilité avancé"""
    
    def __init__(self, name: str, period: int = 20, timeframe: Timeframe = Timeframe.H1):
        super().__init__(name, IndicatorType.VOLATILITY, timeframe)
        self.period = period
    
    @indicator_decorator
    def _calculate_indicator(self, data: pd.DataFrame) -> List[IndicatorValue]:
        """Calcule l'indicateur de volatilité"""
        if len(data) < self.period:
            return []
        
        close_prices = data['close'].values
        
        # Volatilité historique
        returns = np.diff(np.log(close_prices))
        historical_vol = np.std(returns) * np.sqrt(24)  # Annualisée
        
        # Volatilité GARCH (simplifiée)
        garch_vol = self._calculate_garch_volatility(returns)
        
        # Volatilité implicite (approximation)
        implied_vol = self._calculate_implied_volatility(data)
        
        values = []
        for i, (timestamp, row) in enumerate(data.iterrows()):
            if i >= self.period:
                current_vol = historical_vol[i - self.period] if i - self.period < len(historical_vol) else historical_vol[-1]
                
                # Confiance basée sur la cohérence des mesures
                vol_consistency = 1.0 - abs(current_vol - garch_vol) / (current_vol + 1e-8)
                confidence = max(0.5, vol_consistency)
                
                value = IndicatorValue(
                    value=current_vol,
                    timestamp=timestamp,
                    confidence=confidence,
                    metadata={
                        'historical_volatility': current_vol,
                        'garch_volatility': garch_vol,
                        'implied_volatility': implied_vol,
                        'volatility_level': 'high' if current_vol > 0.3 
                                         else 'medium' if current_vol > 0.15 
                                         else 'low',
                        'period': self.period
                    }
                )
                values.append(value)
        
        return values
    
    def _calculate_garch_volatility(self, returns: np.ndarray) -> float:
        """Calcule la volatilité GARCH (simplifiée)"""
        # Implémentation simplifiée du GARCH(1,1)
        alpha = 0.1
        beta = 0.85
        omega = 0.0001
        
        vol = np.var(returns)
        for r in returns:
            vol = omega + alpha * r**2 + beta * vol
        
        return np.sqrt(vol * 24)  # Annualisée
    
    def _calculate_implied_volatility(self, data: pd.DataFrame) -> float:
        """Calcule la volatilité implicite (approximation)"""
        # Approximation basée sur la largeur des bandes de Bollinger
        close_prices = data['close'].values
        upper, middle, lower = talib.BBANDS(close_prices, timeperiod=20)
        
        if len(upper) > 0 and not np.isnan(upper[-1]):
            bb_width = (upper[-1] - lower[-1]) / middle[-1]
            return bb_width / 4  # Approximation
        return 0.2


# Enregistrement des indicateurs avancés
IndicatorFactory.register_indicator("ICHIMOKU", IchimokuIndicator)
IndicatorFactory.register_indicator("WILLIAMS_R", WilliamsRIndicator)
IndicatorFactory.register_indicator("ML_PREDICTION", MLPredictionIndicator)
IndicatorFactory.register_indicator("SENTIMENT", SentimentIndicator)
IndicatorFactory.register_indicator("VOLATILITY", VolatilityIndicator)