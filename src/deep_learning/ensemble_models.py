"""
Système d'ensemble avancé pour combiner CNN, RNN et Transformer
CryptoSpreadEdge - Deep Learning pour trading haute fréquence
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

from .cnn_models import (
    CNNModelFactory, FinancialCNN1D, FinancialCNN2D, 
    ResidualCNN1D, AttentionCNN1D, CNNConfig
)
from .rnn_models import (
    RNNModelFactory, FinancialLSTM, FinancialGRU, 
    StackedLSTM, BidirectionalLSTM, ConvLSTM, RNNConfig
)
from .transformer_models import (
    TransformerModelFactory, FinancialTransformer, 
    FinancialTransformerWithAttention, FinancialTransformerEncoder,
    FinancialTransformerDecoder, FinancialTransformerWithCNN, TransformerConfig
)


@dataclass
class EnsembleConfig:
    """Configuration pour le système d'ensemble"""
    # Modèles CNN
    cnn_models: List[str] = None
    cnn_config: CNNConfig = None
    
    # Modèles RNN
    rnn_models: List[str] = None
    rnn_config: RNNConfig = None
    
    # Modèles Transformer
    transformer_models: List[str] = None
    transformer_config: TransformerConfig = None
    
    # Modèles classiques
    classical_models: List[str] = None
    
    # Configuration ensemble
    ensemble_method: str = "weighted_average"  # weighted_average, stacking, voting
    learning_rate: float = 0.001
    num_epochs: int = 100
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    def __post_init__(self):
        if self.cnn_models is None:
            self.cnn_models = ["cnn1d", "residual_cnn1d", "attention_cnn1d"]
        if self.rnn_models is None:
            self.rnn_models = ["lstm", "bidirectional_lstm", "conv_lstm"]
        if self.transformer_models is None:
            self.transformer_models = ["transformer", "transformer_attention", "transformer_cnn"]
        if self.classical_models is None:
            self.classical_models = ["random_forest", "gradient_boosting", "svm", "logistic_regression"]


class BaseEnsembleModel(nn.Module, ABC):
    """Classe de base pour tous les modèles d'ensemble"""
    
    def __init__(self, config: EnsembleConfig):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass du modèle"""
        pass
    
    def predict(self, x: torch.Tensor) -> Dict[str, Any]:
        """Prédiction avec métadonnées"""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = F.softmax(logits, dim=1)
            predictions = torch.argmax(probabilities, dim=1)
            
            return {
                "predictions": predictions.cpu().numpy(),
                "probabilities": probabilities.cpu().numpy(),
                "confidence": torch.max(probabilities, dim=1)[0].cpu().numpy(),
                "logits": logits.cpu().numpy()
            }


class WeightedEnsemble(BaseEnsembleModel):
    """Ensemble avec moyenne pondérée des prédictions"""
    
    def __init__(self, config: EnsembleConfig):
        super().__init__(config)
        
        # Initialiser les modèles
        self.cnn_models = {}
        self.rnn_models = {}
        self.transformer_models = {}
        self.classical_models = {}
        
        # Créer les modèles CNN
        if config.cnn_config:
            for model_name in config.cnn_models:
                self.cnn_models[model_name] = CNNModelFactory.create_model(
                    model_name, config.cnn_config
                )
        
        # Créer les modèles RNN
        if config.rnn_config:
            for model_name in config.rnn_models:
                self.rnn_models[model_name] = RNNModelFactory.create_model(
                    model_name, config.rnn_config
                )
        
        # Créer les modèles Transformer
        if config.transformer_config:
            for model_name in config.transformer_models:
                self.transformer_models[model_name] = TransformerModelFactory.create_model(
                    model_name, config.transformer_config
                )
        
        # Créer les modèles classiques
        self._create_classical_models()
        
        # Poids des modèles (initialisés uniformément)
        self.model_weights = nn.Parameter(torch.ones(len(self._get_all_models())) / len(self._get_all_models()))
        
        # Couche de fusion
        self.fusion_layer = nn.Linear(len(self._get_all_models()), config.cnn_config.num_classes if config.cnn_config else 3)
        
        # Dropout
        self.dropout = nn.Dropout(0.2)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _create_classical_models(self):
        """Crée les modèles classiques"""
        for model_name in self.config.classical_models:
            if model_name == "random_forest":
                self.classical_models[model_name] = RandomForestClassifier(
                    n_estimators=100, random_state=42, n_jobs=-1
                )
            elif model_name == "gradient_boosting":
                self.classical_models[model_name] = GradientBoostingClassifier(
                    n_estimators=100, random_state=42
                )
            elif model_name == "svm":
                self.classical_models[model_name] = SVC(
                    probability=True, random_state=42
                )
            elif model_name == "logistic_regression":
                self.classical_models[model_name] = LogisticRegression(
                    random_state=42, max_iter=1000
                )
    
    def _get_all_models(self) -> List[str]:
        """Retourne la liste de tous les modèles"""
        all_models = []
        all_models.extend(self.cnn_models.keys())
        all_models.extend(self.rnn_models.keys())
        all_models.extend(self.transformer_models.keys())
        all_models.extend(self.classical_models.keys())
        return all_models
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass de l'ensemble"""
        # Collecter les prédictions de tous les modèles
        predictions = []
        
        # Modèles CNN
        for model_name, model in self.cnn_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles RNN
        for model_name, model in self.rnn_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles Transformer
        for model_name, model in self.transformer_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles classiques (nécessitent des features extraites)
        if self.classical_models:
            # Extraire des features pour les modèles classiques
            features = self._extract_features(x)
            for model_name, model in self.classical_models.items():
                if hasattr(model, 'predict_proba'):
                    pred_proba = model.predict_proba(features.cpu().numpy())
                    pred_tensor = torch.tensor(pred_proba, dtype=torch.float32, device=x.device)
                    predictions.append(pred_tensor)
        
        # Concaténer les prédictions
        if predictions:
            stacked_predictions = torch.stack(predictions, dim=1)  # (batch_size, num_models, num_classes)
            
            # Appliquer les poids
            weights = F.softmax(self.model_weights, dim=0)
            weighted_predictions = stacked_predictions * weights.view(1, -1, 1)
            
            # Moyenne pondérée
            ensemble_output = torch.sum(weighted_predictions, dim=1)
            
            # Couche de fusion finale
            ensemble_output = self.fusion_layer(ensemble_output)
            
            return ensemble_output
        else:
            # Fallback si aucun modèle n'est disponible
            return torch.zeros(x.size(0), 3, device=x.device)
    
    def _extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extrait des features pour les modèles classiques"""
        # Features simples : statistiques des séries temporelles
        batch_size, seq_len, features = x.shape
        
        # Moyenne, écart-type, min, max pour chaque feature
        mean_features = torch.mean(x, dim=1)  # (batch_size, features)
        std_features = torch.std(x, dim=1)    # (batch_size, features)
        min_features = torch.min(x, dim=1)[0] # (batch_size, features)
        max_features = torch.max(x, dim=1)[0] # (batch_size, features)
        
        # Concaténer toutes les features
        extracted_features = torch.cat([
            mean_features, std_features, min_features, max_features
        ], dim=1)
        
        return extracted_features


class StackingEnsemble(BaseEnsembleModel):
    """Ensemble avec stacking (méta-apprentissage)"""
    
    def __init__(self, config: EnsembleConfig):
        super().__init__(config)
        
        # Initialiser les modèles de base
        self.cnn_models = {}
        self.rnn_models = {}
        self.transformer_models = {}
        self.classical_models = {}
        
        # Créer les modèles de base
        self._create_base_models(config)
        
        # Méta-modèle (réseau de neurones)
        num_base_models = len(self._get_all_models())
        self.meta_model = nn.Sequential(
            nn.Linear(num_base_models * 3, 128),  # 3 classes
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 3)  # 3 classes finales
        )
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _create_base_models(self, config: EnsembleConfig):
        """Crée les modèles de base"""
        # Créer les modèles CNN
        if config.cnn_config:
            for model_name in config.cnn_models:
                self.cnn_models[model_name] = CNNModelFactory.create_model(
                    model_name, config.cnn_config
                )
        
        # Créer les modèles RNN
        if config.rnn_config:
            for model_name in config.rnn_models:
                self.rnn_models[model_name] = RNNModelFactory.create_model(
                    model_name, config.rnn_config
                )
        
        # Créer les modèles Transformer
        if config.transformer_config:
            for model_name in config.transformer_models:
                self.transformer_models[model_name] = TransformerModelFactory.create_model(
                    model_name, config.transformer_config
                )
        
        # Créer les modèles classiques
        self._create_classical_models()
    
    def _create_classical_models(self):
        """Crée les modèles classiques"""
        for model_name in self.config.classical_models:
            if model_name == "random_forest":
                self.classical_models[model_name] = RandomForestClassifier(
                    n_estimators=100, random_state=42, n_jobs=-1
                )
            elif model_name == "gradient_boosting":
                self.classical_models[model_name] = GradientBoostingClassifier(
                    n_estimators=100, random_state=42
                )
            elif model_name == "svm":
                self.classical_models[model_name] = SVC(
                    probability=True, random_state=42
                )
            elif model_name == "logistic_regression":
                self.classical_models[model_name] = LogisticRegression(
                    random_state=42, max_iter=1000
                )
    
    def _get_all_models(self) -> List[str]:
        """Retourne la liste de tous les modèles"""
        all_models = []
        all_models.extend(self.cnn_models.keys())
        all_models.extend(self.rnn_models.keys())
        all_models.extend(self.transformer_models.keys())
        all_models.extend(self.classical_models.keys())
        return all_models
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass de l'ensemble avec stacking"""
        # Collecter les prédictions de tous les modèles
        predictions = []
        
        # Modèles CNN
        for model_name, model in self.cnn_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles RNN
        for model_name, model in self.rnn_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles Transformer
        for model_name, model in self.transformer_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles classiques
        if self.classical_models:
            features = self._extract_features(x)
            for model_name, model in self.classical_models.items():
                if hasattr(model, 'predict_proba'):
                    pred_proba = model.predict_proba(features.cpu().numpy())
                    pred_tensor = torch.tensor(pred_proba, dtype=torch.float32, device=x.device)
                    predictions.append(pred_tensor)
        
        # Concaténer les prédictions pour le méta-modèle
        if predictions:
            stacked_predictions = torch.cat(predictions, dim=1)  # (batch_size, num_models * num_classes)
            
            # Méta-modèle
            ensemble_output = self.meta_model(stacked_predictions)
            
            return ensemble_output
        else:
            # Fallback
            return torch.zeros(x.size(0), 3, device=x.device)
    
    def _extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extrait des features pour les modèles classiques"""
        batch_size, seq_len, features = x.shape
        
        # Features statistiques
        mean_features = torch.mean(x, dim=1)
        std_features = torch.std(x, dim=1)
        min_features = torch.min(x, dim=1)[0]
        max_features = torch.max(x, dim=1)[0]
        
        # Features de tendance
        trend_features = torch.mean(torch.diff(x, dim=1), dim=1)
        
        # Concaténer
        extracted_features = torch.cat([
            mean_features, std_features, min_features, max_features, trend_features
        ], dim=1)
        
        return extracted_features


class VotingEnsemble(BaseEnsembleModel):
    """Ensemble avec vote majoritaire"""
    
    def __init__(self, config: EnsembleConfig):
        super().__init__(config)
        
        # Initialiser les modèles
        self.cnn_models = {}
        self.rnn_models = {}
        self.transformer_models = {}
        self.classical_models = {}
        
        # Créer les modèles
        self._create_base_models(config)
        
        # Poids pour le vote pondéré
        self.model_weights = nn.Parameter(torch.ones(len(self._get_all_models())))
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _create_base_models(self, config: EnsembleConfig):
        """Crée les modèles de base"""
        # Créer les modèles CNN
        if config.cnn_config:
            for model_name in config.cnn_models:
                self.cnn_models[model_name] = CNNModelFactory.create_model(
                    model_name, config.cnn_config
                )
        
        # Créer les modèles RNN
        if config.rnn_config:
            for model_name in config.rnn_models:
                self.rnn_models[model_name] = RNNModelFactory.create_model(
                    model_name, config.rnn_config
                )
        
        # Créer les modèles Transformer
        if config.transformer_config:
            for model_name in config.transformer_models:
                self.transformer_models[model_name] = TransformerModelFactory.create_model(
                    model_name, config.transformer_config
                )
        
        # Créer les modèles classiques
        self._create_classical_models()
    
    def _create_classical_models(self):
        """Crée les modèles classiques"""
        for model_name in self.config.classical_models:
            if model_name == "random_forest":
                self.classical_models[model_name] = RandomForestClassifier(
                    n_estimators=100, random_state=42, n_jobs=-1
                )
            elif model_name == "gradient_boosting":
                self.classical_models[model_name] = GradientBoostingClassifier(
                    n_estimators=100, random_state=42
                )
            elif model_name == "svm":
                self.classical_models[model_name] = SVC(
                    probability=True, random_state=42
                )
            elif model_name == "logistic_regression":
                self.classical_models[model_name] = LogisticRegression(
                    random_state=42, max_iter=1000
                )
    
    def _get_all_models(self) -> List[str]:
        """Retourne la liste de tous les modèles"""
        all_models = []
        all_models.extend(self.cnn_models.keys())
        all_models.extend(self.rnn_models.keys())
        all_models.extend(self.transformer_models.keys())
        all_models.extend(self.classical_models.keys())
        return all_models
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        pass  # Pas de poids à initialiser pour le vote
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass de l'ensemble avec vote"""
        # Collecter les prédictions de tous les modèles
        predictions = []
        
        # Modèles CNN
        for model_name, model in self.cnn_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles RNN
        for model_name, model in self.rnn_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles Transformer
        for model_name, model in self.transformer_models.items():
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # Modèles classiques
        if self.classical_models:
            features = self._extract_features(x)
            for model_name, model in self.classical_models.items():
                if hasattr(model, 'predict_proba'):
                    pred_proba = model.predict_proba(features.cpu().numpy())
                    pred_tensor = torch.tensor(pred_proba, dtype=torch.float32, device=x.device)
                    predictions.append(pred_tensor)
        
        # Vote pondéré
        if predictions:
            stacked_predictions = torch.stack(predictions, dim=1)  # (batch_size, num_models, num_classes)
            
            # Appliquer les poids
            weights = F.softmax(self.model_weights, dim=0)
            weighted_predictions = stacked_predictions * weights.view(1, -1, 1)
            
            # Vote pondéré
            ensemble_output = torch.sum(weighted_predictions, dim=1)
            
            return ensemble_output
        else:
            # Fallback
            return torch.zeros(x.size(0), 3, device=x.device)
    
    def _extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extrait des features pour les modèles classiques"""
        batch_size, seq_len, features = x.shape
        
        # Features statistiques
        mean_features = torch.mean(x, dim=1)
        std_features = torch.std(x, dim=1)
        min_features = torch.min(x, dim=1)[0]
        max_features = torch.max(x, dim=1)[0]
        
        # Concaténer
        extracted_features = torch.cat([
            mean_features, std_features, min_features, max_features
        ], dim=1)
        
        return extracted_features


class EnsembleModelFactory:
    """Factory pour créer des modèles d'ensemble"""
    
    @staticmethod
    def create_model(model_type: str, config: EnsembleConfig) -> BaseEnsembleModel:
        """Crée un modèle d'ensemble selon le type spécifié"""
        
        models = {
            "weighted_ensemble": WeightedEnsemble,
            "stacking_ensemble": StackingEnsemble,
            "voting_ensemble": VotingEnsemble,
        }
        
        if model_type not in models:
            raise ValueError(f"Type de modèle non supporté: {model_type}")
        
        return models[model_type](config)
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Retourne la liste des modèles disponibles"""
        return ["weighted_ensemble", "stacking_ensemble", "voting_ensemble"]


class EnsembleTrainer:
    """Entraîneur pour les modèles d'ensemble"""
    
    def __init__(self, model: BaseEnsembleModel, config: EnsembleConfig):
        self.model = model
        self.config = config
        self.device = torch.device(config.device)
        self.model.to(self.device)
        
        # Optimiseur et loss
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=0.01
        )
        self.criterion = nn.CrossEntropyLoss()
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', patience=10, factor=0.5
        )
        
        # Métriques
        self.train_losses = []
        self.val_losses = []
        self.train_accuracies = []
        self.val_accuracies = []
    
    def train_base_models(self, train_loader, val_loader):
        """Entraîne les modèles de base"""
        self.logger.info("Entraînement des modèles de base...")
        
        # Entraîner les modèles CNN
        for model_name, model in self.model.cnn_models.items():
            self.logger.info(f"Entraînement du modèle CNN: {model_name}")
            # Ici, vous devriez utiliser les entraîneurs spécifiques
            # CNNTrainer(model, self.config.cnn_config).train(train_loader, val_loader)
        
        # Entraîner les modèles RNN
        for model_name, model in self.model.rnn_models.items():
            self.logger.info(f"Entraînement du modèle RNN: {model_name}")
            # RNNTrainer(model, self.config.rnn_config).train(train_loader, val_loader)
        
        # Entraîner les modèles Transformer
        for model_name, model in self.model.transformer_models.items():
            self.logger.info(f"Entraînement du modèle Transformer: {model_name}")
            # TransformerTrainer(model, self.config.transformer_config).train(train_loader, val_loader)
        
        # Entraîner les modèles classiques
        self._train_classical_models(train_loader)
    
    def _train_classical_models(self, train_loader):
        """Entraîne les modèles classiques"""
        # Extraire les features et labels
        features_list = []
        labels_list = []
        
        for data, target in train_loader:
            features = self.model._extract_features(data)
            features_list.append(features.cpu().numpy())
            labels_list.append(target.cpu().numpy())
        
        X = np.vstack(features_list)
        y = np.hstack(labels_list)
        
        # Entraîner chaque modèle classique
        for model_name, model in self.model.classical_models.items():
            self.logger.info(f"Entraînement du modèle classique: {model_name}")
            model.fit(X, y)
    
    def train_ensemble(self, train_loader, val_loader):
        """Entraîne l'ensemble complet"""
        # D'abord entraîner les modèles de base
        self.train_base_models(train_loader, val_loader)
        
        # Ensuite entraîner l'ensemble
        self.logger.info("Entraînement de l'ensemble...")
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.config.num_epochs):
            # Entraînement
            train_loss, train_acc = self.train_epoch(train_loader)
            
            # Validation
            val_loss, val_acc = self.validate_epoch(val_loader)
            
            # Mise à jour du scheduler
            self.scheduler.step(val_loss)
            
            # Sauvegarde des métriques
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            self.train_accuracies.append(train_acc)
            self.val_accuracies.append(val_acc)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Sauvegarder le meilleur modèle
                torch.save(self.model.state_dict(), 'best_ensemble_model.pth')
            else:
                patience_counter += 1
                if patience_counter >= 20:
                    self.logger.info(f"Early stopping à l'époque {epoch}")
                    break
            
            # Logging
            if epoch % 10 == 0:
                self.logger.info(f"Époque {epoch}: Train Loss: {train_loss:.4f}, "
                               f"Train Acc: {train_acc:.2f}%, Val Loss: {val_loss:.4f}, "
                               f"Val Acc: {val_acc:.2f}%")
        
        return {
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "train_accuracies": self.train_accuracies,
            "val_accuracies": self.val_accuracies
        }
    
    def train_epoch(self, train_loader) -> Tuple[float, float]:
        """Entraîne le modèle pour une époque"""
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(self.device), target.to(self.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            total_loss += loss.item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
            total += target.size(0)
        
        avg_loss = total_loss / len(train_loader)
        accuracy = 100. * correct / total
        
        return avg_loss, accuracy
    
    def validate_epoch(self, val_loader) -> Tuple[float, float]:
        """Valide le modèle pour une époque"""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in val_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                loss = self.criterion(output, target)
                
                total_loss += loss.item()
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += target.size(0)
        
        avg_loss = total_loss / len(val_loader)
        accuracy = 100. * correct / total
        
        return avg_loss, accuracy
    
    def predict(self, data_loader) -> Dict[str, Any]:
        """Fait des prédictions sur un dataset"""
        self.model.eval()
        all_predictions = []
        all_probabilities = []
        all_confidences = []
        
        with torch.no_grad():
            for data, _ in data_loader:
                data = data.to(self.device)
                results = self.model.predict(data)
                
                all_predictions.extend(results["predictions"])
                all_probabilities.extend(results["probabilities"])
                all_confidences.extend(results["confidence"])
        
        return {
            "predictions": np.array(all_predictions),
            "probabilities": np.array(all_probabilities),
            "confidences": np.array(all_confidences)
        }
    
    def evaluate(self, data_loader) -> Dict[str, float]:
        """Évalue le modèle sur un dataset"""
        predictions = self.predict(data_loader)
        
        # Extraire les vraies labels
        true_labels = []
        for _, target in data_loader:
            true_labels.extend(target.cpu().numpy())
        true_labels = np.array(true_labels)
        
        # Calculer les métriques
        accuracy = accuracy_score(true_labels, predictions["predictions"])
        precision = precision_score(true_labels, predictions["predictions"], average='weighted')
        recall = recall_score(true_labels, predictions["predictions"], average='weighted')
        f1 = f1_score(true_labels, predictions["predictions"], average='weighted')
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }