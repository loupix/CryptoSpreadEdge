"""
Modèles CNN avancés pour l'analyse de patterns financiers
CryptoSpreadEdge - Deep Learning pour trading haute fréquence
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod


@dataclass
class CNNConfig:
    """Configuration pour les modèles CNN"""
    input_channels: int = 4  # OHLC
    sequence_length: int = 100
    num_classes: int = 3  # Buy, Sell, Hold
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 32
    num_epochs: int = 100
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class BaseCNNModel(nn.Module, ABC):
    """Classe de base pour tous les modèles CNN"""
    
    def __init__(self, config: CNNConfig):
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


class FinancialCNN1D(BaseCNNModel):
    """CNN 1D pour l'analyse de séries temporelles financières"""
    
    def __init__(self, config: CNNConfig):
        super().__init__(config)
        
        # Couches de convolution 1D
        self.conv1 = nn.Conv1d(
            in_channels=config.input_channels,
            out_channels=64,
            kernel_size=3,
            padding=1
        )
        self.bn1 = nn.BatchNorm1d(64)
        
        self.conv2 = nn.Conv1d(
            in_channels=64,
            out_channels=128,
            kernel_size=5,
            padding=2
        )
        self.bn2 = nn.BatchNorm1d(128)
        
        self.conv3 = nn.Conv1d(
            in_channels=128,
            out_channels=256,
            kernel_size=7,
            padding=3
        )
        self.bn3 = nn.BatchNorm1d(256)
        
        # Pooling
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Calcul de la taille après convolutions
        conv_output_size = self._calculate_conv_output_size()
        
        # Couches fully connected
        self.fc1 = nn.Linear(conv_output_size, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, config.num_classes)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _calculate_conv_output_size(self) -> int:
        """Calcule la taille de sortie après les convolutions"""
        x = torch.randn(1, self.config.input_channels, self.config.sequence_length)
        
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        
        return x.view(1, -1).size(1)
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, channels, sequence_length)
        
        # Première couche de convolution
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.dropout(x)
        
        # Deuxième couche de convolution
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.dropout(x)
        
        # Troisième couche de convolution
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.dropout(x)
        
        # Flatten
        x = x.view(x.size(0), -1)
        
        # Couches fully connected
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class FinancialCNN2D(BaseCNNModel):
    """CNN 2D pour l'analyse de patterns dans les données financières"""
    
    def __init__(self, config: CNNConfig):
        super().__init__(config)
        
        # Redimensionner pour CNN 2D (créer une image à partir des données)
        self.input_height = int(np.sqrt(config.sequence_length))
        self.input_width = config.sequence_length // self.input_height
        
        # Couches de convolution 2D
        self.conv1 = nn.Conv2d(
            in_channels=config.input_channels,
            out_channels=32,
            kernel_size=3,
            padding=1
        )
        self.bn1 = nn.BatchNorm2d(32)
        
        self.conv2 = nn.Conv2d(
            in_channels=32,
            out_channels=64,
            kernel_size=3,
            padding=1
        )
        self.bn2 = nn.BatchNorm2d(64)
        
        self.conv3 = nn.Conv2d(
            in_channels=64,
            out_channels=128,
            kernel_size=3,
            padding=1
        )
        self.bn3 = nn.BatchNorm2d(128)
        
        self.conv4 = nn.Conv2d(
            in_channels=128,
            out_channels=256,
            kernel_size=3,
            padding=1
        )
        self.bn4 = nn.BatchNorm2d(256)
        
        # Pooling
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Calcul de la taille après convolutions
        conv_output_size = self._calculate_conv_output_size()
        
        # Couches fully connected
        self.fc1 = nn.Linear(conv_output_size, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, config.num_classes)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _calculate_conv_output_size(self) -> int:
        """Calcule la taille de sortie après les convolutions"""
        x = torch.randn(1, self.config.input_channels, self.input_height, self.input_width)
        
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.pool(F.relu(self.bn4(self.conv4(x))))
        
        return x.view(1, -1).size(1)
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def _reshape_to_2d(self, x: torch.Tensor) -> torch.Tensor:
        """Redimensionne les données 1D en 2D pour CNN 2D"""
        batch_size, channels, seq_len = x.shape
        
        # Ajuster la séquence pour qu'elle soit divisible
        if seq_len != self.input_height * self.input_width:
            # Padding ou troncature
            target_size = self.input_height * self.input_width
            if seq_len < target_size:
                padding = target_size - seq_len
                x = F.pad(x, (0, padding))
            else:
                x = x[:, :, :target_size]
        
        # Reshape en 2D
        x = x.view(batch_size, channels, self.input_height, self.input_width)
        return x
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # Redimensionner en 2D
        x = self._reshape_to_2d(x)
        
        # Première couche de convolution
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.dropout(x)
        
        # Deuxième couche de convolution
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.dropout(x)
        
        # Troisième couche de convolution
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.dropout(x)
        
        # Quatrième couche de convolution
        x = self.pool(F.relu(self.bn4(self.conv4(x))))
        x = self.dropout(x)
        
        # Flatten
        x = x.view(x.size(0), -1)
        
        # Couches fully connected
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class ResidualCNN1D(BaseCNNModel):
    """CNN 1D avec blocs résiduels pour l'analyse financière"""
    
    def __init__(self, config: CNNConfig):
        super().__init__(config)
        
        # Couche d'entrée
        self.conv1 = nn.Conv1d(
            in_channels=config.input_channels,
            out_channels=64,
            kernel_size=7,
            padding=3
        )
        self.bn1 = nn.BatchNorm1d(64)
        
        # Blocs résiduels
        self.res_blocks = nn.ModuleList([
            ResidualBlock1D(64, 64),
            ResidualBlock1D(64, 128, stride=2),
            ResidualBlock1D(128, 128),
            ResidualBlock1D(128, 256, stride=2),
            ResidualBlock1D(256, 256),
            ResidualBlock1D(256, 512, stride=2),
        ])
        
        # Pooling global
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Couches fully connected
        self.fc1 = nn.Linear(512, 256)
        self.fc2 = nn.Linear(256, config.num_classes)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # Couche d'entrée
        x = F.relu(self.bn1(self.conv1(x)))
        
        # Blocs résiduels
        for res_block in self.res_blocks:
            x = res_block(x)
        
        # Pooling global
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        
        # Couches fully connected
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        x = self.fc2(x)
        
        return x


class ResidualBlock1D(nn.Module):
    """Bloc résiduel 1D pour CNN"""
    
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        
        self.conv1 = nn.Conv1d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=stride,
            padding=1,
            bias=False
        )
        self.bn1 = nn.BatchNorm1d(out_channels)
        
        self.conv2 = nn.Conv1d(
            in_channels=out_channels,
            out_channels=out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
            bias=False
        )
        self.bn2 = nn.BatchNorm1d(out_channels)
        
        # Couche de projection pour la connexion résiduelle
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(
                    in_channels=in_channels,
                    out_channels=out_channels,
                    kernel_size=1,
                    stride=stride,
                    bias=False
                ),
                nn.BatchNorm1d(out_channels)
            )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass du bloc résiduel"""
        residual = self.shortcut(x)
        
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        
        out += residual
        out = F.relu(out)
        
        return out


class AttentionCNN1D(BaseCNNModel):
    """CNN 1D avec mécanisme d'attention pour l'analyse financière"""
    
    def __init__(self, config: CNNConfig):
        super().__init__(config)
        
        # Couches de convolution
        self.conv_layers = nn.ModuleList([
            nn.Conv1d(config.input_channels, 64, kernel_size=3, padding=1),
            nn.Conv1d(64, 128, kernel_size=5, padding=2),
            nn.Conv1d(128, 256, kernel_size=7, padding=3),
        ])
        
        self.bn_layers = nn.ModuleList([
            nn.BatchNorm1d(64),
            nn.BatchNorm1d(128),
            nn.BatchNorm1d(256),
        ])
        
        # Mécanisme d'attention
        self.attention = SelfAttention1D(256)
        
        # Pooling
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Couches fully connected
        self.fc1 = nn.Linear(256, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, config.num_classes)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # Couches de convolution
        for conv, bn in zip(self.conv_layers, self.bn_layers):
            x = self.pool(F.relu(bn(conv(x))))
            x = self.dropout(x)
        
        # Mécanisme d'attention
        x = self.attention(x)
        
        # Pooling global
        x = F.adaptive_avg_pool1d(x, 1)
        x = x.view(x.size(0), -1)
        
        # Couches fully connected
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class SelfAttention1D(nn.Module):
    """Mécanisme d'auto-attention 1D"""
    
    def __init__(self, d_model: int, num_heads: int = 8):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        
        assert d_model % num_heads == 0, "d_model doit être divisible par num_heads"
        
        self.query = nn.Linear(d_model, d_model)
        self.key = nn.Linear(d_model, d_model)
        self.value = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(0.1)
        self.scale = self.head_dim ** -0.5
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass de l'auto-attention"""
        batch_size, channels, seq_len = x.shape
        
        # Reshape pour l'attention
        x = x.transpose(1, 2)  # (batch_size, seq_len, channels)
        
        # Calculer Q, K, V
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)
        
        # Reshape pour multi-head attention
        Q = Q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Calculer les scores d'attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) * self.scale
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # Appliquer l'attention
        context = torch.matmul(attention_weights, V)
        
        # Reshape et concaténer
        context = context.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.d_model
        )
        
        # Reshape de retour
        context = context.transpose(1, 2)  # (batch_size, channels, seq_len)
        
        return context


class CNNModelFactory:
    """Factory pour créer des modèles CNN"""
    
    @staticmethod
    def create_model(model_type: str, config: CNNConfig) -> BaseCNNModel:
        """Crée un modèle CNN selon le type spécifié"""
        
        models = {
            "cnn1d": FinancialCNN1D,
            "cnn2d": FinancialCNN2D,
            "residual_cnn1d": ResidualCNN1D,
            "attention_cnn1d": AttentionCNN1D,
        }
        
        if model_type not in models:
            raise ValueError(f"Type de modèle non supporté: {model_type}")
        
        return models[model_type](config)
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Retourne la liste des modèles disponibles"""
        return ["cnn1d", "cnn2d", "residual_cnn1d", "attention_cnn1d"]


class CNNTrainer:
    """Entraîneur pour les modèles CNN"""
    
    def __init__(self, model: BaseCNNModel, config: CNNConfig):
        self.model = model
        self.config = config
        self.device = torch.device(config.device)
        self.model.to(self.device)
        
        # Optimiseur et loss
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=1e-5
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
    
    def train(self, train_loader, val_loader) -> Dict[str, List[float]]:
        """Entraîne le modèle complet"""
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
                torch.save(self.model.state_dict(), 'best_cnn_model.pth')
            else:
                patience_counter += 1
                if patience_counter >= 20:  # Patience de 20 époques
                    print(f"Early stopping à l'époque {epoch}")
                    break
            
            # Logging
            if epoch % 10 == 0:
                print(f"Époque {epoch}: Train Loss: {train_loss:.4f}, "
                      f"Train Acc: {train_acc:.2f}%, Val Loss: {val_loss:.4f}, "
                      f"Val Acc: {val_acc:.2f}%")
        
        return {
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "train_accuracies": self.train_accuracies,
            "val_accuracies": self.val_accuracies
        }
    
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