"""
Modèles Transformer avancés pour l'analyse et prédiction financières
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
import copy


@dataclass
class TransformerConfig:
    """Configuration pour les modèles Transformer"""
    input_size: int = 4  # OHLC
    d_model: int = 256
    nhead: int = 8
    num_layers: int = 6
    sequence_length: int = 100
    num_classes: int = 3  # Buy, Sell, Hold
    dropout_rate: float = 0.1
    learning_rate: float = 0.001
    batch_size: int = 32
    num_epochs: int = 100
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    max_len: int = 5000
    activation: str = "relu"  # relu, gelu


class PositionalEncoding(nn.Module):
    """Encodage positionnel pour Transformer"""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Ajoute l'encodage positionnel"""
        return x + self.pe[:x.size(0), :]


class MultiHeadAttention(nn.Module):
    """Attention multi-têtes pour Transformer"""
    
    def __init__(self, d_model: int, nhead: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % nhead == 0
        
        self.d_model = d_model
        self.nhead = nhead
        self.d_k = d_model // nhead
        
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.d_k)
    
    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass de l'attention multi-têtes"""
        batch_size, seq_len, d_model = query.size()
        
        # Calculer Q, K, V
        Q = self.W_q(query).view(batch_size, seq_len, self.nhead, self.d_k).transpose(1, 2)
        K = self.W_k(key).view(batch_size, seq_len, self.nhead, self.d_k).transpose(1, 2)
        V = self.W_v(value).view(batch_size, seq_len, self.nhead, self.d_k).transpose(1, 2)
        
        # Calculer les scores d'attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        
        # Appliquer le masque si fourni
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # Appliquer l'attention
        context = torch.matmul(attention_weights, V)
        
        # Concaténer et projeter
        context = context.transpose(1, 2).contiguous().view(
            batch_size, seq_len, d_model
        )
        
        output = self.W_o(context)
        
        return output, attention_weights


class FeedForward(nn.Module):
    """Réseau feed-forward pour Transformer"""
    
    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1, activation: str = "relu"):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)
        
        if activation == "relu":
            self.activation = F.relu
        elif activation == "gelu":
            self.activation = F.gelu
        else:
            raise ValueError(f"Activation non supportée: {activation}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass du feed-forward"""
        return self.linear2(self.dropout(self.activation(self.linear1(x))))


class TransformerBlock(nn.Module):
    """Bloc Transformer avec attention et feed-forward"""
    
    def __init__(self, d_model: int, nhead: int, d_ff: int, dropout: float = 0.1, activation: str = "relu"):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, nhead, dropout)
        self.feed_forward = FeedForward(d_model, d_ff, dropout, activation)
        
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Forward pass du bloc Transformer"""
        # Attention avec résidu
        attn_output, _ = self.attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        # Feed-forward avec résidu
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        
        return x


class BaseTransformerModel(nn.Module, ABC):
    """Classe de base pour tous les modèles Transformer"""
    
    def __init__(self, config: TransformerConfig):
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


class FinancialTransformer(BaseTransformerModel):
    """Transformer pour l'analyse de séries temporelles financières"""
    
    def __init__(self, config: TransformerConfig):
        super().__init__(config)
        
        # Couche d'embedding
        self.input_embedding = nn.Linear(config.input_size, config.d_model)
        
        # Encodage positionnel
        self.pos_encoding = PositionalEncoding(config.d_model, config.max_len)
        
        # Blocs Transformer
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(
                d_model=config.d_model,
                nhead=config.nhead,
                d_ff=config.d_model * 4,
                dropout=config.dropout_rate,
                activation=config.activation
            )
            for _ in range(config.num_layers)
        ])
        
        # Couches de sortie
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(config.d_model, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LayerNorm):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # Embedding
        x = self.input_embedding(x)  # (batch_size, sequence_length, d_model)
        
        # Encodage positionnel
        x = x.transpose(0, 1)  # (sequence_length, batch_size, d_model)
        x = self.pos_encoding(x)
        x = x.transpose(0, 1)  # (batch_size, sequence_length, d_model)
        
        # Dropout
        x = self.dropout(x)
        
        # Blocs Transformer
        for transformer_block in self.transformer_blocks:
            x = transformer_block(x)
        
        # Pooling global
        x = x.transpose(1, 2)  # (batch_size, d_model, sequence_length)
        x = self.global_pool(x)  # (batch_size, d_model, 1)
        x = x.squeeze(-1)  # (batch_size, d_model)
        
        # Couches fully connected
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class FinancialTransformerWithAttention(BaseTransformerModel):
    """Transformer avec attention personnalisée pour l'analyse financière"""
    
    def __init__(self, config: TransformerConfig):
        super().__init__(config)
        
        # Couche d'embedding
        self.input_embedding = nn.Linear(config.input_size, config.d_model)
        
        # Encodage positionnel
        self.pos_encoding = PositionalEncoding(config.d_model, config.max_len)
        
        # Blocs Transformer
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(
                d_model=config.d_model,
                nhead=config.nhead,
                d_ff=config.d_model * 4,
                dropout=config.dropout_rate,
                activation=config.activation
            )
            for _ in range(config.num_layers)
        ])
        
        # Attention finale pour la classification
        self.final_attention = MultiHeadAttention(config.d_model, config.nhead, config.dropout_rate)
        
        # Couches de sortie
        self.fc1 = nn.Linear(config.d_model, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LayerNorm):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # Embedding
        x = self.input_embedding(x)
        
        # Encodage positionnel
        x = x.transpose(0, 1)
        x = self.pos_encoding(x)
        x = x.transpose(0, 1)
        
        # Dropout
        x = self.dropout(x)
        
        # Blocs Transformer
        for transformer_block in self.transformer_blocks:
            x = transformer_block(x)
        
        # Attention finale
        attended_output, attention_weights = self.final_attention(x, x, x)
        
        # Pooling global avec attention
        attention_weights = attention_weights.mean(dim=1)  # Moyenne sur les têtes
        weighted_output = torch.sum(attended_output * attention_weights.unsqueeze(-1), dim=1)
        
        # Couches fully connected
        x = F.relu(self.fc1(weighted_output))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class FinancialTransformerEncoder(BaseTransformerModel):
    """Transformer Encoder pour l'analyse de séries temporelles"""
    
    def __init__(self, config: TransformerConfig):
        super().__init__(config)
        
        # Couche d'embedding
        self.input_embedding = nn.Linear(config.input_size, config.d_model)
        
        # Encodage positionnel
        self.pos_encoding = PositionalEncoding(config.d_model, config.max_len)
        
        # Encoder Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.nhead,
            dim_feedforward=config.d_model * 4,
            dropout=config.dropout_rate,
            activation=config.activation
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=config.num_layers
        )
        
        # Couches de sortie
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(config.d_model, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # Embedding
        x = self.input_embedding(x)
        
        # Encodage positionnel
        x = x.transpose(0, 1)  # (sequence_length, batch_size, d_model)
        x = self.pos_encoding(x)
        
        # Dropout
        x = self.dropout(x)
        
        # Transformer Encoder
        x = self.transformer_encoder(x)
        
        # Transposer de retour
        x = x.transpose(0, 1)  # (batch_size, sequence_length, d_model)
        
        # Pooling global
        x = x.transpose(1, 2)  # (batch_size, d_model, sequence_length)
        x = self.global_pool(x)  # (batch_size, d_model, 1)
        x = x.squeeze(-1)  # (batch_size, d_model)
        
        # Couches fully connected
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class FinancialTransformerDecoder(BaseTransformerModel):
    """Transformer Decoder pour la génération de prédictions"""
    
    def __init__(self, config: TransformerConfig):
        super().__init__(config)
        
        # Couche d'embedding
        self.input_embedding = nn.Linear(config.input_size, config.d_model)
        
        # Encodage positionnel
        self.pos_encoding = PositionalEncoding(config.d_model, config.max_len)
        
        # Decoder Transformer
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=config.d_model,
            nhead=config.nhead,
            dim_feedforward=config.d_model * 4,
            dropout=config.dropout_rate,
            activation=config.activation
        )
        self.transformer_decoder = nn.TransformerDecoder(
            decoder_layer,
            num_layers=config.num_layers
        )
        
        # Couches de sortie
        self.fc1 = nn.Linear(config.d_model, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, config.num_classes)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout_rate)
        
        # Initialisation des poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids du modèle"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # Embedding
        x = self.input_embedding(x)
        
        # Encodage positionnel
        x = x.transpose(0, 1)  # (sequence_length, batch_size, d_model)
        x = self.pos_encoding(x)
        
        # Dropout
        x = self.dropout(x)
        
        # Créer un masque causal pour le decoder
        seq_len = x.size(0)
        mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
        mask = mask.to(x.device)
        
        # Transformer Decoder
        x = self.transformer_decoder(x, x, tgt_mask=mask)
        
        # Transposer de retour
        x = x.transpose(0, 1)  # (batch_size, sequence_length, d_model)
        
        # Prendre la dernière sortie
        x = x[:, -1, :]  # (batch_size, d_model)
        
        # Couches fully connected
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class FinancialTransformerWithCNN(BaseTransformerModel):
    """Transformer avec CNN pour l'analyse de patterns financiers"""
    
    def __init__(self, config: TransformerConfig):
        super().__init__(config)
        
        # Couches CNN pour l'extraction de features
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
        
        # Couche d'embedding
        self.input_embedding = nn.Linear(128, config.d_model)
        
        # Encodage positionnel
        self.pos_encoding = PositionalEncoding(config.d_model, config.max_len)
        
        # Blocs Transformer
        self.transformer_blocks = nn.ModuleList([
            TransformerBlock(
                d_model=config.d_model,
                nhead=config.nhead,
                d_ff=config.d_model * 4,
                dropout=config.dropout_rate,
                activation=config.activation
            )
            for _ in range(config.num_layers)
        ])
        
        # Couches de sortie
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(config.d_model, 256)
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
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LayerNorm):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # x shape: (batch_size, sequence_length, input_size)
        
        # Transposer pour CNN
        x = x.transpose(1, 2)  # (batch_size, input_size, sequence_length)
        
        # Couches CNN
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.dropout(x)
        
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.dropout(x)
        
        # Transposer de retour
        x = x.transpose(1, 2)  # (batch_size, sequence_length, 128)
        
        # Embedding
        x = self.input_embedding(x)
        
        # Encodage positionnel
        x = x.transpose(0, 1)  # (sequence_length, batch_size, d_model)
        x = self.pos_encoding(x)
        x = x.transpose(0, 1)  # (batch_size, sequence_length, d_model)
        
        # Dropout
        x = self.dropout(x)
        
        # Blocs Transformer
        for transformer_block in self.transformer_blocks:
            x = transformer_block(x)
        
        # Pooling global
        x = x.transpose(1, 2)  # (batch_size, d_model, sequence_length)
        x = self.global_pool(x)  # (batch_size, d_model, 1)
        x = x.squeeze(-1)  # (batch_size, d_model)
        
        # Couches fully connected
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        x = self.fc3(x)
        
        return x


class TransformerModelFactory:
    """Factory pour créer des modèles Transformer"""
    
    @staticmethod
    def create_model(model_type: str, config: TransformerConfig) -> BaseTransformerModel:
        """Crée un modèle Transformer selon le type spécifié"""
        
        models = {
            "transformer": FinancialTransformer,
            "transformer_attention": FinancialTransformerWithAttention,
            "transformer_encoder": FinancialTransformerEncoder,
            "transformer_decoder": FinancialTransformerDecoder,
            "transformer_cnn": FinancialTransformerWithCNN,
        }
        
        if model_type not in models:
            raise ValueError(f"Type de modèle non supporté: {model_type}")
        
        return models[model_type](config)
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Retourne la liste des modèles disponibles"""
        return ["transformer", "transformer_attention", "transformer_encoder", 
                "transformer_decoder", "transformer_cnn"]


class TransformerTrainer:
    """Entraîneur pour les modèles Transformer"""
    
    def __init__(self, model: BaseTransformerModel, config: TransformerConfig):
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
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=config.num_epochs
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
            self.scheduler.step()
            
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
                torch.save(self.model.state_dict(), 'best_transformer_model.pth')
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