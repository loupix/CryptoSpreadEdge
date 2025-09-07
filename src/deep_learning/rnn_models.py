"""
Modèles RNN/LSTM avancés pour l'analyse de séries temporelles financières
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
import math


@dataclass
class RNNConfig:
    """Configuration pour les modèles RNN"""
    input_size: int = 4  # OHLC
    hidden_size: int = 128
    num_layers: int = 3
    sequence_length: int = 100
    num_classes: int = 3  # Buy, Sell, Hold
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 32
    num_epochs: int = 100
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    bidirectional: bool = True
    rnn_type: str = "LSTM"  # LSTM, GRU, RNN


class BaseRNNModel(nn.Module, ABC):
    """Classe de base pour tous les modèles RNN"""
    
    def __init__(self, config: RNNConfig):
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


class FinancialLSTM(BaseRNNModel):
    """LSTM pour l'analyse de séries temporelles financières"""
    
    def __init__(self, config: RNNConfig):
        super().__init__(config)
        
        # Couche LSTM
        self.lstm = nn.LSTM(
            input_size=config.input_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout_rate if config.num_layers > 1 else 0,
            bidirectional=config.bidirectional,
            batch_first=True
        )
        
        # Calcul de la taille de sortie
        lstm_output_size = config.hidden_size * (2 if config.bidirectional else 1)
        
        # Couches fully connected
        self.fc1 = nn.Linear(lstm_output_size, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for name, param in self.lstm.named_parameters():
            if 'weight_ih' in name:
                nn.init.xavier_uniform_(param.data)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param.data)
            elif 'bias' in name:
                param.data.fill_(0)
                # Initialiser les forget gates à 1
                n = param.size(0)
                param.data[(n//4):(n//2)].fill_(1)
        
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Prendre la dernière sortie
        last_output = lstm_out[:, -1, :]
        
        # Couches fully connected
        x = F.relu(self.fc1(last_output))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class FinancialGRU(BaseRNNModel):
    """GRU pour l'analyse de séries temporelles financières"""
    
    def __init__(self, config: RNNConfig):
        super().__init__(config)
        
        # Couche GRU
        self.gru = nn.GRU(
            input_size=config.input_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout_rate if config.num_layers > 1 else 0,
            bidirectional=config.bidirectional,
            batch_first=True
        )
        
        # Calcul de la taille de sortie
        gru_output_size = config.hidden_size * (2 if config.bidirectional else 1)
        
        # Couches fully connected
        self.fc1 = nn.Linear(gru_output_size, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for name, param in self.gru.named_parameters():
            if 'weight_ih' in name:
                nn.init.xavier_uniform_(param.data)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param.data)
            elif 'bias' in name:
                param.data.fill_(0)
        
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # GRU
        gru_out, hidden = self.gru(x)
        
        # Prendre la dernière sortie
        last_output = gru_out[:, -1, :]
        
        # Couches fully connected
        x = F.relu(self.fc1(last_output))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class StackedLSTM(BaseRNNModel):
    """LSTM empilé avec attention pour l'analyse financière"""
    
    def __init__(self, config: RNNConfig):
        super().__init__(config)
        
        # Première couche LSTM
        self.lstm1 = nn.LSTM(
            input_size=config.input_size,
            hidden_size=config.hidden_size,
            num_layers=1,
            batch_first=True,
            dropout=0
        )
        
        # Deuxième couche LSTM
        self.lstm2 = nn.LSTM(
            input_size=config.hidden_size,
            hidden_size=config.hidden_size,
            num_layers=1,
            batch_first=True,
            dropout=0
        )
        
        # Troisième couche LSTM
        self.lstm3 = nn.LSTM(
            input_size=config.hidden_size,
            hidden_size=config.hidden_size,
            num_layers=1,
            batch_first=True,
            dropout=0
        )
        
        # Mécanisme d'attention
        self.attention = AttentionLayer(config.hidden_size)
        
        # Couches fully connected
        self.fc1 = nn.Linear(config.hidden_size, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for lstm in [self.lstm1, self.lstm2, self.lstm3]:
            for name, param in lstm.named_parameters():
                if 'weight_ih' in name:
                    nn.init.xavier_uniform_(param.data)
                elif 'weight_hh' in name:
                    nn.init.orthogonal_(param.data)
                elif 'bias' in name:
                    param.data.fill_(0)
                    n = param.size(0)
                    param.data[(n//4):(n//2)].fill_(1)
        
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # Première couche LSTM
        lstm1_out, _ = self.lstm1(x)
        
        # Deuxième couche LSTM
        lstm2_out, _ = self.lstm2(lstm1_out)
        
        # Troisième couche LSTM
        lstm3_out, _ = self.lstm3(lstm2_out)
        
        # Attention
        attended_output = self.attention(lstm3_out)
        
        # Couches fully connected
        x = F.relu(self.fc1(attended_output))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class AttentionLayer(nn.Module):
    """Couche d'attention pour RNN"""
    
    def __init__(self, hidden_size: int):
        super().__init__()
        self.hidden_size = hidden_size
        self.attention_weights = nn.Linear(hidden_size, 1)
    
    def forward(self, lstm_output: torch.Tensor) -> torch.Tensor:
        """Forward pass de l'attention"""
        # lstm_output shape: (batch_size, sequence_length, hidden_size)
        
        # Calculer les poids d'attention
        attention_scores = self.attention_weights(lstm_output)  # (batch_size, sequence_length, 1)
        attention_weights = F.softmax(attention_scores, dim=1)  # (batch_size, sequence_length, 1)
        
        # Appliquer l'attention
        attended_output = torch.sum(lstm_output * attention_weights, dim=1)  # (batch_size, hidden_size)
        
        return attended_output


class BidirectionalLSTM(BaseRNNModel):
    """LSTM bidirectionnel avec attention pour l'analyse financière"""
    
    def __init__(self, config: RNNConfig):
        super().__init__(config)
        
        # LSTM bidirectionnel
        self.lstm = nn.LSTM(
            input_size=config.input_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout_rate if config.num_layers > 1 else 0,
            bidirectional=True,
            batch_first=True
        )
        
        # Mécanisme d'attention
        self.attention = MultiHeadAttention(
            d_model=config.hidden_size * 2,  # *2 pour bidirectionnel
            num_heads=8
        )
        
        # Couches fully connected
        self.fc1 = nn.Linear(config.hidden_size * 2, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for name, param in self.lstm.named_parameters():
            if 'weight_ih' in name:
                nn.init.xavier_uniform_(param.data)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param.data)
            elif 'bias' in name:
                param.data.fill_(0)
                n = param.size(0)
                param.data[(n//4):(n//2)].fill_(1)
        
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # LSTM bidirectionnel
        lstm_out, _ = self.lstm(x)
        
        # Attention multi-têtes
        attended_output = self.attention(lstm_out)
        
        # Pooling global
        global_output = torch.mean(attended_output, dim=1)
        
        # Couches fully connected
        x = F.relu(self.fc1(global_output))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class MultiHeadAttention(nn.Module):
    """Attention multi-têtes pour RNN"""
    
    def __init__(self, d_model: int, num_heads: int = 8):
        super().__init__()
        assert d_model % num_heads == 0
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(0.1)
        self.scale = math.sqrt(self.d_k)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass de l'attention multi-têtes"""
        batch_size, seq_len, d_model = x.size()
        
        # Calculer Q, K, V
        Q = self.W_q(x).view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(x).view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(x).view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        
        # Calculer les scores d'attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # Appliquer l'attention
        context = torch.matmul(attention_weights, V)
        
        # Concaténer et projeter
        context = context.transpose(1, 2).contiguous().view(
            batch_size, seq_len, d_model
        )
        
        output = self.W_o(context)
        
        return output


class ConvLSTM(BaseRNNModel):
    """LSTM avec convolutions pour l'analyse financière"""
    
    def __init__(self, config: RNNConfig):
        super().__init__(config)
        
        # Couches de convolution
        self.conv1 = nn.Conv1d(
            in_channels=config.input_size,
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
        
        # LSTM
        self.lstm = nn.LSTM(
            input_size=128,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout_rate if config.num_layers > 1 else 0,
            bidirectional=config.bidirectional,
            batch_first=True
        )
        
        # Calcul de la taille de sortie
        lstm_output_size = config.hidden_size * (2 if config.bidirectional else 1)
        
        # Couches fully connected
        self.fc1 = nn.Linear(lstm_output_size, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
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
            elif isinstance(m, nn.LSTM):
                for name, param in m.named_parameters():
                    if 'weight_ih' in name:
                        nn.init.xavier_uniform_(param.data)
                    elif 'weight_hh' in name:
                        nn.init.orthogonal_(param.data)
                    elif 'bias' in name:
                        param.data.fill_(0)
                        n = param.size(0)
                        param.data[(n//4):(n//2)].fill_(1)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # Transposer pour convolution
        x = x.transpose(1, 2)  # (batch_size, input_size, sequence_length)
        
        # Couches de convolution
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.dropout(x)
        
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.dropout(x)
        
        # Transposer de retour pour LSTM
        x = x.transpose(1, 2)  # (batch_size, sequence_length, 128)
        
        # LSTM
        lstm_out, _ = self.lstm(x)
        
        # Prendre la dernière sortie
        last_output = lstm_out[:, -1, :]
        
        # Couches fully connected
        x = F.relu(self.fc1(last_output))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class RNNModelFactory:
    """Factory pour créer des modèles RNN"""
    
    @staticmethod
    def create_model(model_type: str, config: RNNConfig) -> BaseRNNModel:
        """Crée un modèle RNN selon le type spécifié"""
        
        models = {
            "lstm": FinancialLSTM,
            "gru": FinancialGRU,
            "stacked_lstm": StackedLSTM,
            "bidirectional_lstm": BidirectionalLSTM,
            "conv_lstm": ConvLSTM,
        }
        
        if model_type not in models:
            raise ValueError(f"Type de modèle non supporté: {model_type}")
        
        return models[model_type](config)
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Retourne la liste des modèles disponibles"""
        return ["lstm", "gru", "stacked_lstm", "bidirectional_lstm", "conv_lstm"]


class RNNTrainer:
    """Entraîneur pour les modèles RNN"""
    
    def __init__(self, model: BaseRNNModel, config: RNNConfig):
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
                torch.save(self.model.state_dict(), 'best_rnn_model.pth')
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