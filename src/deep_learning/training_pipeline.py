"""
Pipeline d'entraînement distribué pour les modèles Deep Learning
CryptoSpreadEdge - Deep Learning pour trading haute fréquence
"""

import torch
import torch.nn as nn
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import logging
import os
import json
import time
from datetime import datetime
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

from .cnn_models import CNNModelFactory, CNNTrainer, CNNConfig
from .rnn_models import RNNModelFactory, RNNTrainer, RNNConfig
from .transformer_models import TransformerModelFactory, TransformerTrainer, TransformerConfig
from .ensemble_models import EnsembleModelFactory, EnsembleTrainer, EnsembleConfig


@dataclass
class TrainingConfig:
    """Configuration pour le pipeline d'entraînement"""
    # Données
    data_path: str = "data/processed/"
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    
    # Modèles
    cnn_models: List[str] = None
    rnn_models: List[str] = None
    transformer_models: List[str] = None
    ensemble_models: List[str] = None
    
    # Entraînement
    batch_size: int = 32
    num_epochs: int = 100
    learning_rate: float = 0.001
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Distribution
    distributed: bool = False
    num_gpus: int = torch.cuda.device_count()
    world_size: int = 1
    rank: int = 0
    
    # Sauvegarde
    save_dir: str = "models/"
    checkpoint_interval: int = 10
    save_best_only: bool = True
    
    # Logging
    log_interval: int = 10
    log_dir: str = "logs/"
    
    def __post_init__(self):
        if self.cnn_models is None:
            self.cnn_models = ["cnn1d", "residual_cnn1d", "attention_cnn1d"]
        if self.rnn_models is None:
            self.rnn_models = ["lstm", "bidirectional_lstm", "conv_lstm"]
        if self.transformer_models is None:
            self.transformer_models = ["transformer", "transformer_attention", "transformer_cnn"]
        if self.ensemble_models is None:
            self.ensemble_models = ["weighted_ensemble", "stacking_ensemble"]


class FinancialDataset(torch.utils.data.Dataset):
    """Dataset pour les données financières"""
    
    def __init__(self, data: np.ndarray, labels: np.ndarray, sequence_length: int = 100):
        self.data = data
        self.labels = labels
        self.sequence_length = sequence_length
        
        # Vérifier les dimensions
        assert len(self.data) == len(self.labels), "Data et labels doivent avoir la même longueur"
        assert self.data.shape[1] >= self.sequence_length, "Séquence trop longue pour les données"
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        # Extraire la séquence
        sequence = self.data[idx, :self.sequence_length, :]
        label = self.labels[idx]
        
        return torch.FloatTensor(sequence), torch.LongTensor([label])


class DataProcessor:
    """Processeur de données pour l'entraînement"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
    
    def load_data(self, file_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Charge les données depuis un fichier"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.parquet'):
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Format de fichier non supporté: {file_path}")
            
            self.logger.info(f"Données chargées: {df.shape}")
            return df.values, df.columns.tolist()
        
        except Exception as e:
            self.logger.error(f"Erreur chargement données: {e}")
            raise
    
    def preprocess_data(self, data: np.ndarray, labels: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
        """Préprocesse les données"""
        try:
            # Normaliser les données
            if len(data.shape) == 3:  # (samples, sequence, features)
                original_shape = data.shape
                data_reshaped = data.reshape(-1, data.shape[-1])
                data_scaled = self.scaler.fit_transform(data_reshaped)
                data = data_scaled.reshape(original_shape)
            else:
                data = self.scaler.fit_transform(data)
            
            # Encoder les labels si fournis
            if labels is not None:
                labels = self.label_encoder.fit_transform(labels)
            
            self.logger.info(f"Données préprocessées: {data.shape}")
            return data, labels
        
        except Exception as e:
            self.logger.error(f"Erreur préprocessing: {e}")
            raise
    
    def create_sequences(self, data: np.ndarray, sequence_length: int = 100) -> np.ndarray:
        """Crée des séquences à partir des données"""
        try:
            sequences = []
            for i in range(len(data) - sequence_length + 1):
                sequences.append(data[i:i + sequence_length])
            
            sequences = np.array(sequences)
            self.logger.info(f"Séquences créées: {sequences.shape}")
            return sequences
        
        except Exception as e:
            self.logger.error(f"Erreur création séquences: {e}")
            raise
    
    def split_data(self, data: np.ndarray, labels: np.ndarray) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """Divise les données en train/val/test"""
        try:
            # Division train/val/test
            X_temp, X_test, y_temp, y_test = train_test_split(
                data, labels, test_size=self.config.test_ratio, random_state=42, stratify=labels
            )
            
            val_size = self.config.val_ratio / (1 - self.config.test_ratio)
            X_train, X_val, y_train, y_val = train_test_split(
                X_temp, y_temp, test_size=val_size, random_state=42, stratify=y_temp
            )
            
            splits = {
                "train": (X_train, y_train),
                "val": (X_val, y_val),
                "test": (X_test, y_test)
            }
            
            self.logger.info(f"Données divisées - Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
            return splits
        
        except Exception as e:
            self.logger.error(f"Erreur division données: {e}")
            raise


class DistributedTrainingManager:
    """Gestionnaire d'entraînement distribué"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def setup_distributed(self, rank: int, world_size: int):
        """Configure l'entraînement distribué"""
        try:
            os.environ['MASTER_ADDR'] = 'localhost'
            os.environ['MASTER_PORT'] = '12355'
            
            dist.init_process_group("nccl", rank=rank, world_size=world_size)
            torch.cuda.set_device(rank)
            
            self.logger.info(f"Processus distribué initialisé - Rank: {rank}, World Size: {world_size}")
        
        except Exception as e:
            self.logger.error(f"Erreur configuration distribuée: {e}")
            raise
    
    def cleanup_distributed(self):
        """Nettoie l'entraînement distribué"""
        try:
            dist.destroy_process_group()
            self.logger.info("Processus distribué nettoyé")
        
        except Exception as e:
            self.logger.error(f"Erreur nettoyage distribué: {e}")
    
    def create_distributed_dataloader(self, dataset: torch.utils.data.Dataset, 
                                    batch_size: int, shuffle: bool = True) -> DataLoader:
        """Crée un DataLoader distribué"""
        try:
            sampler = DistributedSampler(dataset, shuffle=shuffle)
            dataloader = DataLoader(
                dataset, 
                batch_size=batch_size, 
                sampler=sampler,
                num_workers=4,
                pin_memory=True
            )
            
            return dataloader
        
        except Exception as e:
            self.logger.error(f"Erreur création DataLoader distribué: {e}")
            raise


class ModelTrainer:
    """Entraîneur de modèles avec support distribué"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.distributed_manager = DistributedTrainingManager(config)
    
    def train_cnn_models(self, train_loader: DataLoader, val_loader: DataLoader, 
                        rank: int = 0) -> Dict[str, Any]:
        """Entraîne les modèles CNN"""
        results = {}
        
        for model_name in self.config.cnn_models:
            try:
                self.logger.info(f"Entraînement du modèle CNN: {model_name}")
                
                # Configuration CNN
                cnn_config = CNNConfig(
                    input_channels=4,
                    sequence_length=100,
                    num_classes=3,
                    dropout_rate=0.2,
                    learning_rate=self.config.learning_rate,
                    batch_size=self.config.batch_size,
                    num_epochs=self.config.num_epochs,
                    device=self.config.device
                )
                
                # Créer le modèle
                model = CNNModelFactory.create_model(model_name, cnn_config)
                
                # Entraînement distribué si activé
                if self.config.distributed:
                    model = DDP(model, device_ids=[rank])
                
                # Entraîner
                trainer = CNNTrainer(model, cnn_config)
                training_results = trainer.train(train_loader, val_loader)
                
                # Sauvegarder le modèle
                model_path = os.path.join(self.config.save_dir, f"{model_name}_cnn.pth")
                torch.save(model.state_dict(), model_path)
                
                results[model_name] = {
                    "training_results": training_results,
                    "model_path": model_path
                }
                
                self.logger.info(f"Modèle CNN {model_name} entraîné et sauvegardé")
            
            except Exception as e:
                self.logger.error(f"Erreur entraînement CNN {model_name}: {e}")
                results[model_name] = {"error": str(e)}
        
        return results
    
    def train_rnn_models(self, train_loader: DataLoader, val_loader: DataLoader, 
                        rank: int = 0) -> Dict[str, Any]:
        """Entraîne les modèles RNN"""
        results = {}
        
        for model_name in self.config.rnn_models:
            try:
                self.logger.info(f"Entraînement du modèle RNN: {model_name}")
                
                # Configuration RNN
                rnn_config = RNNConfig(
                    input_size=4,
                    hidden_size=128,
                    num_layers=3,
                    sequence_length=100,
                    num_classes=3,
                    dropout_rate=0.2,
                    learning_rate=self.config.learning_rate,
                    batch_size=self.config.batch_size,
                    num_epochs=self.config.num_epochs,
                    device=self.config.device
                )
                
                # Créer le modèle
                model = RNNModelFactory.create_model(model_name, rnn_config)
                
                # Entraînement distribué si activé
                if self.config.distributed:
                    model = DDP(model, device_ids=[rank])
                
                # Entraîner
                trainer = RNNTrainer(model, rnn_config)
                training_results = trainer.train(train_loader, val_loader)
                
                # Sauvegarder le modèle
                model_path = os.path.join(self.config.save_dir, f"{model_name}_rnn.pth")
                torch.save(model.state_dict(), model_path)
                
                results[model_name] = {
                    "training_results": training_results,
                    "model_path": model_path
                }
                
                self.logger.info(f"Modèle RNN {model_name} entraîné et sauvegardé")
            
            except Exception as e:
                self.logger.error(f"Erreur entraînement RNN {model_name}: {e}")
                results[model_name] = {"error": str(e)}
        
        return results
    
    def train_transformer_models(self, train_loader: DataLoader, val_loader: DataLoader, 
                               rank: int = 0) -> Dict[str, Any]:
        """Entraîne les modèles Transformer"""
        results = {}
        
        for model_name in self.config.transformer_models:
            try:
                self.logger.info(f"Entraînement du modèle Transformer: {model_name}")
                
                # Configuration Transformer
                transformer_config = TransformerConfig(
                    input_size=4,
                    d_model=256,
                    nhead=8,
                    num_layers=6,
                    sequence_length=100,
                    num_classes=3,
                    dropout_rate=0.1,
                    learning_rate=self.config.learning_rate,
                    batch_size=self.config.batch_size,
                    num_epochs=self.config.num_epochs,
                    device=self.config.device
                )
                
                # Créer le modèle
                model = TransformerModelFactory.create_model(model_name, transformer_config)
                
                # Entraînement distribué si activé
                if self.config.distributed:
                    model = DDP(model, device_ids=[rank])
                
                # Entraîner
                trainer = TransformerTrainer(model, transformer_config)
                training_results = trainer.train(train_loader, val_loader)
                
                # Sauvegarder le modèle
                model_path = os.path.join(self.config.save_dir, f"{model_name}_transformer.pth")
                torch.save(model.state_dict(), model_path)
                
                results[model_name] = {
                    "training_results": training_results,
                    "model_path": model_path
                }
                
                self.logger.info(f"Modèle Transformer {model_name} entraîné et sauvegardé")
            
            except Exception as e:
                self.logger.error(f"Erreur entraînement Transformer {model_name}: {e}")
                results[model_name] = {"error": str(e)}
        
        return results
    
    def train_ensemble_models(self, train_loader: DataLoader, val_loader: DataLoader, 
                            rank: int = 0) -> Dict[str, Any]:
        """Entraîne les modèles d'ensemble"""
        results = {}
        
        for model_name in self.config.ensemble_models:
            try:
                self.logger.info(f"Entraînement du modèle d'ensemble: {model_name}")
                
                # Configuration Ensemble
                ensemble_config = EnsembleConfig(
                    cnn_models=self.config.cnn_models,
                    rnn_models=self.config.rnn_models,
                    transformer_models=self.config.transformer_models,
                    classical_models=["random_forest", "gradient_boosting"],
                    ensemble_method=model_name.split('_')[0],
                    learning_rate=self.config.learning_rate,
                    num_epochs=self.config.num_epochs,
                    device=self.config.device
                )
                
                # Créer le modèle
                model = EnsembleModelFactory.create_model(model_name, ensemble_config)
                
                # Entraînement distribué si activé
                if self.config.distributed:
                    model = DDP(model, device_ids=[rank])
                
                # Entraîner
                trainer = EnsembleTrainer(model, ensemble_config)
                training_results = trainer.train_ensemble(train_loader, val_loader)
                
                # Sauvegarder le modèle
                model_path = os.path.join(self.config.save_dir, f"{model_name}_ensemble.pth")
                torch.save(model.state_dict(), model_path)
                
                results[model_name] = {
                    "training_results": training_results,
                    "model_path": model_path
                }
                
                self.logger.info(f"Modèle d'ensemble {model_name} entraîné et sauvegardé")
            
            except Exception as e:
                self.logger.error(f"Erreur entraînement ensemble {model_name}: {e}")
                results[model_name] = {"error": str(e)}
        
        return results


class TrainingPipeline:
    """Pipeline principal d'entraînement"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_processor = DataProcessor(config)
        self.model_trainer = ModelTrainer(config)
        
        # Créer les répertoires
        os.makedirs(self.config.save_dir, exist_ok=True)
        os.makedirs(self.config.log_dir, exist_ok=True)
        
        # Configuration du logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure le logging"""
        log_file = os.path.join(self.config.log_dir, f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def run_training(self, data_file: str) -> Dict[str, Any]:
        """Exécute le pipeline d'entraînement complet"""
        try:
            self.logger.info("Démarrage du pipeline d'entraînement")
            
            # Charger et préprocesser les données
            self.logger.info("Chargement et préprocessing des données")
            data, columns = self.data_processor.load_data(data_file)
            
            # Supposer que la dernière colonne est le label
            X = data[:, :-1]
            y = data[:, -1]
            
            # Préprocesser
            X, y = self.data_processor.preprocess_data(X, y)
            
            # Créer des séquences
            X_sequences = self.data_processor.create_sequences(X, sequence_length=100)
            
            # Diviser les données
            splits = self.data_processor.split_data(X_sequences, y)
            
            # Créer les datasets
            train_dataset = FinancialDataset(splits["train"][0], splits["train"][1])
            val_dataset = FinancialDataset(splits["val"][0], splits["val"][1])
            test_dataset = FinancialDataset(splits["test"][0], splits["test"][1])
            
            # Créer les DataLoaders
            train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=self.config.batch_size, shuffle=False)
            test_loader = DataLoader(test_dataset, batch_size=self.config.batch_size, shuffle=False)
            
            # Entraîner les modèles
            results = {}
            
            # Modèles CNN
            if self.config.cnn_models:
                self.logger.info("Entraînement des modèles CNN")
                cnn_results = self.model_trainer.train_cnn_models(train_loader, val_loader)
                results["cnn_models"] = cnn_results
            
            # Modèles RNN
            if self.config.rnn_models:
                self.logger.info("Entraînement des modèles RNN")
                rnn_results = self.model_trainer.train_rnn_models(train_loader, val_loader)
                results["rnn_models"] = rnn_results
            
            # Modèles Transformer
            if self.config.transformer_models:
                self.logger.info("Entraînement des modèles Transformer")
                transformer_results = self.model_trainer.train_transformer_models(train_loader, val_loader)
                results["transformer_models"] = transformer_results
            
            # Modèles d'ensemble
            if self.config.ensemble_models:
                self.logger.info("Entraînement des modèles d'ensemble")
                ensemble_results = self.model_trainer.train_ensemble_models(train_loader, val_loader)
                results["ensemble_models"] = ensemble_results
            
            # Sauvegarder les résultats
            results_file = os.path.join(self.config.save_dir, "training_results.json")
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info("Pipeline d'entraînement terminé avec succès")
            return results
        
        except Exception as e:
            self.logger.error(f"Erreur pipeline d'entraînement: {e}")
            raise
    
    def run_distributed_training(self, data_file: str, rank: int, world_size: int):
        """Exécute l'entraînement distribué"""
        try:
            # Configuration distribuée
            self.model_trainer.distributed_manager.setup_distributed(rank, world_size)
            
            # Exécuter l'entraînement
            results = self.run_training(data_file)
            
            # Nettoyage
            self.model_trainer.distributed_manager.cleanup_distributed()
            
            return results
        
        except Exception as e:
            self.logger.error(f"Erreur entraînement distribué: {e}")
            self.model_trainer.distributed_manager.cleanup_distributed()
            raise


def main():
    """Fonction principale pour l'entraînement"""
    # Configuration
    config = TrainingConfig(
        data_path="data/processed/",
        batch_size=32,
        num_epochs=100,
        learning_rate=0.001,
        distributed=False,
        save_dir="models/",
        log_dir="logs/"
    )
    
    # Créer le pipeline
    pipeline = TrainingPipeline(config)
    
    # Exécuter l'entraînement
    results = pipeline.run_training("data/processed/financial_data.csv")
    
    print("Entraînement terminé!")
    print(f"Résultats sauvegardés dans: {config.save_dir}")


if __name__ == "__main__":
    main()