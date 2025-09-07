"""
Système de prédiction avancé avec LSTM, Transformer et ensemble methods
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
import pandas as pd
import joblib
import warnings
warnings.filterwarnings('ignore')

# Imports pour le deep learning
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch non disponible. Les modèles LSTM/Transformer ne seront pas utilisables.")

# Imports pour les modèles classiques
from sklearn.ensemble import (
    RandomForestRegressor, GradientBoostingRegressor, 
    VotingRegressor, StackingRegressor
)
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

from .signal_generator import TradingSignal, SignalType


@dataclass
class PredictionResult:
    """Résultat de prédiction"""
    predicted_price: float
    predicted_change: float
    confidence: float
    timestamp: datetime
    model_name: str
    features_used: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TimeSeriesDataset(Dataset):
    """Dataset pour les séries temporelles (PyTorch)"""
    
    def __init__(self, sequences: np.ndarray, targets: np.ndarray):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class LSTMPredictor(nn.Module):
    """Modèle LSTM pour la prédiction de prix"""
    
    def __init__(self, input_size: int, hidden_size: int = 64, 
                 num_layers: int = 2, dropout: float = 0.2):
        super(LSTMPredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Couches LSTM
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Couches de sortie
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc2 = nn.Linear(hidden_size // 2, 1)
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # Initialiser les états cachés
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        # LSTM
        lstm_out, _ = self.lstm(x, (h0, c0))
        
        # Prendre la dernière sortie
        last_output = lstm_out[:, -1, :]
        
        # Couches fully connected
        x = self.dropout(last_output)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        
        return x


class TransformerPredictor(nn.Module):
    """Modèle Transformer pour la prédiction de prix"""
    
    def __init__(self, input_size: int, d_model: int = 64, 
                 nhead: int = 8, num_layers: int = 4, dropout: float = 0.1):
        super(TransformerPredictor, self).__init__()
        
        self.d_model = d_model
        self.input_projection = nn.Linear(input_size, d_model)
        self.pos_encoding = self._create_positional_encoding(1000, d_model)
        
        # Couche Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Couches de sortie
        self.fc = nn.Linear(d_model, 1)
        self.dropout = nn.Dropout(dropout)
    
    def _create_positional_encoding(self, max_len: int, d_model: int):
        """Crée l'encodage positionnel"""
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           -(np.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        return pe.unsqueeze(0)
    
    def forward(self, x):
        seq_len = x.size(1)
        
        # Projection d'entrée
        x = self.input_projection(x)
        
        # Ajouter l'encodage positionnel
        x = x + self.pos_encoding[:, :seq_len, :]
        
        # Transformer
        x = x.transpose(0, 1)  # (seq_len, batch, d_model)
        x = self.transformer(x)
        x = x.transpose(0, 1)  # (batch, seq_len, d_model)
        
        # Prendre la dernière sortie
        last_output = x[:, -1, :]
        
        # Couche de sortie
        x = self.dropout(last_output)
        x = self.fc(x)
        
        return x


class MLPredictor:
    """Prédicteur ML principal avec ensemble methods"""
    
    def __init__(self, name: str = "MLPredictor"):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Modèles
        self.models = {}
        self.scalers = {}
        self.is_trained = False
        
        # Configuration
        self.sequence_length = 60  # 60 périodes pour la prédiction
        self.prediction_horizon = 5  # Prédire 5 périodes à l'avance
        self.feature_columns = [
            'open', 'high', 'low', 'close', 'volume',
            'sma_5', 'sma_10', 'sma_20', 'sma_50',
            'ema_5', 'ema_10', 'ema_20',
            'rsi_14', 'macd', 'bb_position', 'atr',
            'price_change', 'volume_change', 'volatility'
        ]
        
        # Initialiser les modèles
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialise tous les modèles"""
        # Modèles classiques
        self.models['random_forest'] = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.models['gradient_boosting'] = GradientBoostingRegressor(
            n_estimators=100, max_depth=6, random_state=42
        )
        self.models['neural_network'] = MLPRegressor(
            hidden_layer_sizes=(100, 50, 25),
            max_iter=500, random_state=42
        )
        self.models['svr'] = SVR(kernel='rbf', C=1.0, gamma='scale')
        
        # Ensemble models
        self.models['voting'] = VotingRegressor([
            ('rf', self.models['random_forest']),
            ('gb', self.models['gradient_boosting']),
            ('nn', self.models['neural_network'])
        ])
        
        self.models['stacking'] = StackingRegressor(
            estimators=[
                ('rf', self.models['random_forest']),
                ('gb', self.models['gradient_boosting']),
                ('svr', self.models['svr'])
            ],
            final_estimator=LinearRegression()
        )
        
        # Modèles PyTorch (si disponible)
        if TORCH_AVAILABLE:
            self.models['lstm'] = LSTMPredictor(
                input_size=len(self.feature_columns),
                hidden_size=64,
                num_layers=2
            )
            self.models['transformer'] = TransformerPredictor(
                input_size=len(self.feature_columns),
                d_model=64,
                nhead=8,
                num_layers=4
            )
        
        # Scaler pour chaque modèle
        for model_name in self.models.keys():
            self.scalers[model_name] = StandardScaler()
    
    def _create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Crée les features pour la prédiction"""
        features = data.copy()
        
        # Moyennes mobiles
        features['sma_5'] = features['close'].rolling(5).mean()
        features['sma_10'] = features['close'].rolling(10).mean()
        features['sma_20'] = features['close'].rolling(20).mean()
        features['sma_50'] = features['close'].rolling(50).mean()
        
        # Moyennes mobiles exponentielles
        features['ema_5'] = features['close'].ewm(span=5).mean()
        features['ema_10'] = features['close'].ewm(span=10).mean()
        features['ema_20'] = features['close'].ewm(span=20).mean()
        
        # RSI
        delta = features['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = features['close'].ewm(span=12).mean()
        ema_26 = features['close'].ewm(span=26).mean()
        features['macd'] = ema_12 - ema_26
        
        # Bollinger Bands
        bb_middle = features['close'].rolling(20).mean()
        bb_std = features['close'].rolling(20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        features['bb_position'] = (features['close'] - bb_lower) / (bb_upper - bb_lower)
        
        # ATR
        high_low = features['high'] - features['low']
        high_close = np.abs(features['high'] - features['close'].shift())
        low_close = np.abs(features['low'] - features['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        features['atr'] = true_range.rolling(14).mean()
        
        # Features de momentum
        features['price_change'] = features['close'].pct_change()
        features['volume_change'] = features['volume'].pct_change()
        features['volatility'] = features['close'].rolling(20).std()
        
        return features
    
    def _prepare_sequences(self, data: pd.DataFrame, target_col: str = 'close') -> Tuple[np.ndarray, np.ndarray]:
        """Prépare les séquences pour l'entraînement"""
        features = self._create_features(data)
        features = features[self.feature_columns].dropna()
        
        if len(features) < self.sequence_length + self.prediction_horizon:
            return np.array([]), np.array([])
        
        X, y = [], []
        
        for i in range(self.sequence_length, len(features) - self.prediction_horizon):
            # Séquence d'entrée
            sequence = features.iloc[i - self.sequence_length:i][self.feature_columns].values
            X.append(sequence)
            
            # Target: prix futur
            current_price = features.iloc[i][target_col]
            future_price = features.iloc[i + self.prediction_horizon][target_col]
            price_change = (future_price - current_price) / current_price
            y.append(price_change)
        
        return np.array(X), np.array(y)
    
    def train_models(self, data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Entraîne tous les modèles"""
        self.logger.info("Début de l'entraînement des modèles")
        
        # Préparer les données
        X, y = self._prepare_sequences(data)
        
        if len(X) == 0:
            return {'error': 'Pas assez de données pour l\'entraînement'}
        
        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        results = {}
        
        # Entraîner les modèles classiques
        for model_name, model in self.models.items():
            if model_name in ['lstm', 'transformer'] and not TORCH_AVAILABLE:
                continue
            
            try:
                if model_name in ['lstm', 'transformer']:
                    # Entraînement PyTorch
                    result = self._train_pytorch_model(
                        model_name, model, X_train, y_train, X_test, y_test
                    )
                else:
                    # Entraînement sklearn
                    result = self._train_sklearn_model(
                        model_name, model, X_train, y_train, X_test, y_test
                    )
                
                results[model_name] = result
                self.logger.info(f"Modèle {model_name} entraîné: R² = {result['r2_score']:.4f}")
                
            except Exception as e:
                self.logger.error(f"Erreur entraînement {model_name}: {e}")
                results[model_name] = {'error': str(e)}
        
        self.is_trained = True
        return results
    
    def _train_sklearn_model(self, model_name: str, model, X_train: np.ndarray, 
                            y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Entraîne un modèle sklearn"""
        # Reshape pour les modèles 2D
        X_train_2d = X_train.reshape(X_train.shape[0], -1)
        X_test_2d = X_test.reshape(X_test.shape[0], -1)
        
        # Normalisation
        X_train_scaled = self.scalers[model_name].fit_transform(X_train_2d)
        X_test_scaled = self.scalers[model_name].transform(X_test_2d)
        
        # Entraînement
        model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = model.predict(X_test_scaled)
        
        # Métriques
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        return {
            'mse': mse,
            'mae': mae,
            'r2_score': r2,
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    def _train_pytorch_model(self, model_name: str, model, X_train: np.ndarray, 
                           y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Entraîne un modèle PyTorch"""
        if not TORCH_AVAILABLE:
            return {'error': 'PyTorch non disponible'}
        
        # Créer les datasets
        train_dataset = TimeSeriesDataset(X_train, y_train)
        test_dataset = TimeSeriesDataset(X_test, y_test)
        
        # DataLoaders
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
        
        # Optimiseur et loss
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        
        # Entraînement
        model.train()
        for epoch in range(50):  # 50 époques
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs.squeeze(), batch_y)
                loss.backward()
                optimizer.step()
        
        # Évaluation
        model.eval()
        y_pred = []
        with torch.no_grad():
            for batch_X, _ in test_loader:
                outputs = model(batch_X)
                y_pred.extend(outputs.squeeze().numpy())
        
        y_pred = np.array(y_pred)
        
        # Métriques
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        return {
            'mse': mse,
            'mae': mae,
            'r2_score': r2,
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    def predict(self, data: pd.DataFrame, model_name: str = 'voting') -> List[PredictionResult]:
        """Fait des prédictions avec un modèle spécifique"""
        if not self.is_trained:
            self.logger.warning("Modèles non entraînés")
            return []
        
        if model_name not in self.models:
            self.logger.error(f"Modèle {model_name} non trouvé")
            return []
        
        try:
            # Préparer les données
            X, _ = self._prepare_sequences(data)
            
            if len(X) == 0:
                return []
            
            model = self.models[model_name]
            scaler = self.scalers[model_name]
            
            # Prédictions
            if model_name in ['lstm', 'transformer'] and TORCH_AVAILABLE:
                # Prédiction PyTorch
                model.eval()
                with torch.no_grad():
                    X_tensor = torch.FloatTensor(X)
                    predictions = model(X_tensor).squeeze().numpy()
            else:
                # Prédiction sklearn
                X_2d = X.reshape(X.shape[0], -1)
                X_scaled = scaler.transform(X_2d)
                predictions = model.predict(X_scaled)
            
            # Créer les résultats
            results = []
            for i, pred in enumerate(predictions):
                current_price = data['close'].iloc[i + self.sequence_length]
                predicted_price = current_price * (1 + pred)
                
                result = PredictionResult(
                    predicted_price=predicted_price,
                    predicted_change=pred,
                    confidence=min(1.0, abs(pred) * 5),  # Confiance basée sur la prédiction
                    timestamp=datetime.utcnow(),
                    model_name=model_name,
                    features_used=self.feature_columns,
                    metadata={
                        'current_price': current_price,
                        'sequence_length': self.sequence_length,
                        'prediction_horizon': self.prediction_horizon
                    }
                )
                results.append(result)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Erreur prédiction {model_name}: {e}")
            return []
    
    def predict_ensemble(self, data: pd.DataFrame) -> List[PredictionResult]:
        """Fait des prédictions avec tous les modèles et combine les résultats"""
        all_predictions = {}
        
        # Prédictions de tous les modèles
        for model_name in self.models.keys():
            if model_name in ['lstm', 'transformer'] and not TORCH_AVAILABLE:
                continue
            
            try:
                predictions = self.predict(data, model_name)
                if predictions:
                    all_predictions[model_name] = predictions
            except Exception as e:
                self.logger.error(f"Erreur prédiction {model_name}: {e}")
        
        if not all_predictions:
            return []
        
        # Combiner les prédictions (moyenne pondérée par la confiance)
        combined_results = []
        
        # Prendre le nombre minimum de prédictions
        min_length = min(len(preds) for preds in all_predictions.values())
        
        for i in range(min_length):
            predictions_at_i = []
            confidences = []
            
            for model_name, predictions in all_predictions.items():
                pred = predictions[i]
                predictions_at_i.append(pred.predicted_change)
                confidences.append(pred.confidence)
            
            # Moyenne pondérée
            total_confidence = sum(confidences)
            if total_confidence > 0:
                weighted_prediction = sum(
                    pred * conf for pred, conf in zip(predictions_at_i, confidences)
                ) / total_confidence
                
                # Confiance combinée
                combined_confidence = min(1.0, total_confidence / len(confidences))
            else:
                weighted_prediction = np.mean(predictions_at_i)
                combined_confidence = 0.5
            
            # Créer le résultat combiné
            current_price = data['close'].iloc[i + self.sequence_length]
            predicted_price = current_price * (1 + weighted_prediction)
            
            result = PredictionResult(
                predicted_price=predicted_price,
                predicted_change=weighted_prediction,
                confidence=combined_confidence,
                timestamp=datetime.utcnow(),
                model_name='ensemble',
                features_used=self.feature_columns,
                metadata={
                    'models_used': list(all_predictions.keys()),
                    'individual_predictions': {
                        name: preds[i].predicted_change 
                        for name, preds in all_predictions.items()
                    },
                    'current_price': current_price
                }
            )
            combined_results.append(result)
        
        return combined_results
    
    def save_models(self, filepath: str):
        """Sauvegarde les modèles"""
        try:
            model_data = {
                'models': self.models,
                'scalers': self.scalers,
                'is_trained': self.is_trained,
                'feature_columns': self.feature_columns,
                'sequence_length': self.sequence_length,
                'prediction_horizon': self.prediction_horizon
            }
            joblib.dump(model_data, filepath)
            self.logger.info(f"Modèles sauvegardés: {filepath}")
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde: {e}")
    
    def load_models(self, filepath: str):
        """Charge les modèles"""
        try:
            model_data = joblib.load(filepath)
            self.models = model_data['models']
            self.scalers = model_data['scalers']
            self.is_trained = model_data['is_trained']
            self.feature_columns = model_data['feature_columns']
            self.sequence_length = model_data['sequence_length']
            self.prediction_horizon = model_data['prediction_horizon']
            self.logger.info(f"Modèles chargés: {filepath}")
        except Exception as e:
            self.logger.error(f"Erreur chargement: {e}")
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Retourne les performances des modèles"""
        if not self.is_trained:
            return {'error': 'Modèles non entraînés'}
        
        return {
            'is_trained': self.is_trained,
            'models_count': len(self.models),
            'feature_columns': self.feature_columns,
            'sequence_length': self.sequence_length,
            'prediction_horizon': self.prediction_horizon,
            'pytorch_available': TORCH_AVAILABLE
        }


# Instance globale du prédicteur ML
ml_predictor = MLPredictor()