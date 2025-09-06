#!/usr/bin/env python3
"""
Script de test pour les modèles Deep Learning
CryptoSpreadEdge - Test des modèles CNN, RNN et Transformer
"""

import sys
import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import logging
from typing import Dict, List, Any
import time
import json
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.deep_learning.cnn_models import (
    CNNModelFactory, CNNTrainer, CNNConfig,
    FinancialCNN1D, FinancialCNN2D, ResidualCNN1D, AttentionCNN1D
)
from src.deep_learning.rnn_models import (
    RNNModelFactory, RNNTrainer, RNNConfig,
    FinancialLSTM, FinancialGRU, StackedLSTM, BidirectionalLSTM, ConvLSTM
)
from src.deep_learning.transformer_models import (
    TransformerModelFactory, TransformerTrainer, TransformerConfig,
    FinancialTransformer, FinancialTransformerWithAttention, 
    FinancialTransformerEncoder, FinancialTransformerDecoder, FinancialTransformerWithCNN
)
from src.deep_learning.ensemble_models import (
    EnsembleModelFactory, EnsembleTrainer, EnsembleConfig,
    WeightedEnsemble, StackingEnsemble, VotingEnsemble
)
from src.deep_learning.training_pipeline import TrainingPipeline, TrainingConfig


class DeepLearningTester:
    """Testeur pour les modèles Deep Learning"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.results = {}
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def generate_test_data(self, num_samples: int = 1000, sequence_length: int = 100, 
                          num_features: int = 4) -> tuple:
        """Génère des données de test"""
        try:
            # Générer des données aléatoires simulant des données financières
            np.random.seed(42)
            
            # Données OHLC
            data = np.random.randn(num_samples, sequence_length, num_features)
            
            # Ajouter une tendance
            trend = np.linspace(0, 1, sequence_length).reshape(1, -1, 1)
            data[:, :, 0] += trend.squeeze()  # Open
            data[:, :, 1] += trend.squeeze() + np.random.randn(num_samples, sequence_length) * 0.1  # High
            data[:, :, 2] += trend.squeeze() - np.random.randn(num_samples, sequence_length) * 0.1  # Low
            data[:, :, 3] += trend.squeeze() + np.random.randn(num_samples, sequence_length) * 0.05  # Close
            
            # Générer des labels (0: Sell, 1: Hold, 2: Buy)
            labels = np.random.randint(0, 3, num_samples)
            
            self.logger.info(f"Données de test générées: {data.shape}, Labels: {labels.shape}")
            return data, labels
        
        except Exception as e:
            self.logger.error(f"Erreur génération données: {e}")
            raise
    
    def create_dataloader(self, data: np.ndarray, labels: np.ndarray, 
                         batch_size: int = 32) -> DataLoader:
        """Crée un DataLoader"""
        try:
            # Convertir en tenseurs
            data_tensor = torch.FloatTensor(data)
            labels_tensor = torch.LongTensor(labels)
            
            # Créer le dataset
            dataset = TensorDataset(data_tensor, labels_tensor)
            
            # Créer le DataLoader
            dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
            
            return dataloader
        
        except Exception as e:
            self.logger.error(f"Erreur création DataLoader: {e}")
            raise
    
    def test_cnn_models(self) -> Dict[str, Any]:
        """Teste les modèles CNN"""
        self.logger.info("Test des modèles CNN")
        results = {}
        
        try:
            # Générer des données de test
            data, labels = self.generate_test_data()
            train_loader = self.create_dataloader(data, labels)
            
            # Configuration CNN
            cnn_config = CNNConfig(
                input_channels=4,
                sequence_length=100,
                num_classes=3,
                dropout_rate=0.2,
                learning_rate=0.001,
                batch_size=32,
                num_epochs=5,  # Réduit pour les tests
                device=self.device
            )
            
            # Tester chaque modèle CNN
            cnn_models = ["cnn1d", "cnn2d", "residual_cnn1d", "attention_cnn1d"]
            
            for model_name in cnn_models:
                try:
                    self.logger.info(f"Test du modèle CNN: {model_name}")
                    
                    # Créer le modèle
                    model = CNNModelFactory.create_model(model_name, cnn_config)
                    model.to(self.device)
                    
                    # Test de forward pass
                    start_time = time.time()
                    with torch.no_grad():
                        sample_data = torch.randn(1, 4, 100).to(self.device)
                        output = model(sample_data)
                        forward_time = time.time() - start_time
                    
                    # Test de prédiction
                    start_time = time.time()
                    predictions = model.predict(sample_data)
                    prediction_time = time.time() - start_time
                    
                    # Vérifier les dimensions
                    assert output.shape == (1, 3), f"Shape incorrecte: {output.shape}"
                    assert "predictions" in predictions, "Prédictions manquantes"
                    
                    results[model_name] = {
                        "status": "success",
                        "forward_time": forward_time,
                        "prediction_time": prediction_time,
                        "output_shape": output.shape,
                        "predictions_keys": list(predictions.keys())
                    }
                    
                    self.logger.info(f"Modèle CNN {model_name} testé avec succès")
                
                except Exception as e:
                    self.logger.error(f"Erreur test CNN {model_name}: {e}")
                    results[model_name] = {"status": "error", "error": str(e)}
            
            return results
        
        except Exception as e:
            self.logger.error(f"Erreur test modèles CNN: {e}")
            return {"error": str(e)}
    
    def test_rnn_models(self) -> Dict[str, Any]:
        """Teste les modèles RNN"""
        self.logger.info("Test des modèles RNN")
        results = {}
        
        try:
            # Générer des données de test
            data, labels = self.generate_test_data()
            train_loader = self.create_dataloader(data, labels)
            
            # Configuration RNN
            rnn_config = RNNConfig(
                input_size=4,
                hidden_size=128,
                num_layers=3,
                sequence_length=100,
                num_classes=3,
                dropout_rate=0.2,
                learning_rate=0.001,
                batch_size=32,
                num_epochs=5,  # Réduit pour les tests
                device=self.device
            )
            
            # Tester chaque modèle RNN
            rnn_models = ["lstm", "gru", "stacked_lstm", "bidirectional_lstm", "conv_lstm"]
            
            for model_name in rnn_models:
                try:
                    self.logger.info(f"Test du modèle RNN: {model_name}")
                    
                    # Créer le modèle
                    model = RNNModelFactory.create_model(model_name, rnn_config)
                    model.to(self.device)
                    
                    # Test de forward pass
                    start_time = time.time()
                    with torch.no_grad():
                        sample_data = torch.randn(1, 100, 4).to(self.device)
                        output = model(sample_data)
                        forward_time = time.time() - start_time
                    
                    # Test de prédiction
                    start_time = time.time()
                    predictions = model.predict(sample_data)
                    prediction_time = time.time() - start_time
                    
                    # Vérifier les dimensions
                    assert output.shape == (1, 3), f"Shape incorrecte: {output.shape}"
                    assert "predictions" in predictions, "Prédictions manquantes"
                    
                    results[model_name] = {
                        "status": "success",
                        "forward_time": forward_time,
                        "prediction_time": prediction_time,
                        "output_shape": output.shape,
                        "predictions_keys": list(predictions.keys())
                    }
                    
                    self.logger.info(f"Modèle RNN {model_name} testé avec succès")
                
                except Exception as e:
                    self.logger.error(f"Erreur test RNN {model_name}: {e}")
                    results[model_name] = {"status": "error", "error": str(e)}
            
            return results
        
        except Exception as e:
            self.logger.error(f"Erreur test modèles RNN: {e}")
            return {"error": str(e)}
    
    def test_transformer_models(self) -> Dict[str, Any]:
        """Teste les modèles Transformer"""
        self.logger.info("Test des modèles Transformer")
        results = {}
        
        try:
            # Générer des données de test
            data, labels = self.generate_test_data()
            train_loader = self.create_dataloader(data, labels)
            
            # Configuration Transformer
            transformer_config = TransformerConfig(
                input_size=4,
                d_model=256,
                nhead=8,
                num_layers=6,
                sequence_length=100,
                num_classes=3,
                dropout_rate=0.1,
                learning_rate=0.001,
                batch_size=32,
                num_epochs=5,  # Réduit pour les tests
                device=self.device
            )
            
            # Tester chaque modèle Transformer
            transformer_models = [
                "transformer", "transformer_attention", "transformer_encoder",
                "transformer_decoder", "transformer_cnn"
            ]
            
            for model_name in transformer_models:
                try:
                    self.logger.info(f"Test du modèle Transformer: {model_name}")
                    
                    # Créer le modèle
                    model = TransformerModelFactory.create_model(model_name, transformer_config)
                    model.to(self.device)
                    
                    # Test de forward pass
                    start_time = time.time()
                    with torch.no_grad():
                        sample_data = torch.randn(1, 100, 4).to(self.device)
                        output = model(sample_data)
                        forward_time = time.time() - start_time
                    
                    # Test de prédiction
                    start_time = time.time()
                    predictions = model.predict(sample_data)
                    prediction_time = time.time() - start_time
                    
                    # Vérifier les dimensions
                    assert output.shape == (1, 3), f"Shape incorrecte: {output.shape}"
                    assert "predictions" in predictions, "Prédictions manquantes"
                    
                    results[model_name] = {
                        "status": "success",
                        "forward_time": forward_time,
                        "prediction_time": prediction_time,
                        "output_shape": output.shape,
                        "predictions_keys": list(predictions.keys())
                    }
                    
                    self.logger.info(f"Modèle Transformer {model_name} testé avec succès")
                
                except Exception as e:
                    self.logger.error(f"Erreur test Transformer {model_name}: {e}")
                    results[model_name] = {"status": "error", "error": str(e)}
            
            return results
        
        except Exception as e:
            self.logger.error(f"Erreur test modèles Transformer: {e}")
            return {"error": str(e)}
    
    def test_ensemble_models(self) -> Dict[str, Any]:
        """Teste les modèles d'ensemble"""
        self.logger.info("Test des modèles d'ensemble")
        results = {}
        
        try:
            # Générer des données de test
            data, labels = self.generate_test_data()
            train_loader = self.create_dataloader(data, labels)
            
            # Configuration Ensemble
            ensemble_config = EnsembleConfig(
                cnn_models=["cnn1d"],
                rnn_models=["lstm"],
                transformer_models=["transformer"],
                classical_models=["random_forest"],
                ensemble_method="weighted_average",
                learning_rate=0.001,
                num_epochs=5,  # Réduit pour les tests
                device=self.device
            )
            
            # Tester chaque modèle d'ensemble
            ensemble_models = ["weighted_ensemble", "stacking_ensemble", "voting_ensemble"]
            
            for model_name in ensemble_models:
                try:
                    self.logger.info(f"Test du modèle d'ensemble: {model_name}")
                    
                    # Créer le modèle
                    model = EnsembleModelFactory.create_model(model_name, ensemble_config)
                    model.to(self.device)
                    
                    # Test de forward pass
                    start_time = time.time()
                    with torch.no_grad():
                        sample_data = torch.randn(1, 100, 4).to(self.device)
                        output = model(sample_data)
                        forward_time = time.time() - start_time
                    
                    # Test de prédiction
                    start_time = time.time()
                    predictions = model.predict(sample_data)
                    prediction_time = time.time() - start_time
                    
                    # Vérifier les dimensions
                    assert output.shape == (1, 3), f"Shape incorrecte: {output.shape}"
                    assert "predictions" in predictions, "Prédictions manquantes"
                    
                    results[model_name] = {
                        "status": "success",
                        "forward_time": forward_time,
                        "prediction_time": prediction_time,
                        "output_shape": output.shape,
                        "predictions_keys": list(predictions.keys())
                    }
                    
                    self.logger.info(f"Modèle d'ensemble {model_name} testé avec succès")
                
                except Exception as e:
                    self.logger.error(f"Erreur test ensemble {model_name}: {e}")
                    results[model_name] = {"status": "error", "error": str(e)}
            
            return results
        
        except Exception as e:
            self.logger.error(f"Erreur test modèles d'ensemble: {e}")
            return {"error": str(e)}
    
    def test_training_pipeline(self) -> Dict[str, Any]:
        """Teste le pipeline d'entraînement"""
        self.logger.info("Test du pipeline d'entraînement")
        
        try:
            # Générer des données de test
            data, labels = self.generate_test_data(num_samples=100)  # Petit dataset pour test
            
            # Sauvegarder les données temporairement
            import pandas as pd
            test_data = np.column_stack([data.reshape(data.shape[0], -1), labels])
            test_file = "test_data.csv"
            pd.DataFrame(test_data).to_csv(test_file, index=False)
            
            # Configuration d'entraînement
            training_config = TrainingConfig(
                data_path="",
                batch_size=16,
                num_epochs=2,  # Très réduit pour les tests
                learning_rate=0.001,
                device=self.device,
                save_dir="test_models/",
                log_dir="test_logs/",
                cnn_models=["cnn1d"],
                rnn_models=["lstm"],
                transformer_models=["transformer"],
                ensemble_models=[]
            )
            
            # Créer le pipeline
            pipeline = TrainingPipeline(training_config)
            
            # Exécuter l'entraînement
            start_time = time.time()
            results = pipeline.run_training(test_file)
            training_time = time.time() - start_time
            
            # Nettoyage
            os.remove(test_file)
            import shutil
            if os.path.exists("test_models"):
                shutil.rmtree("test_models")
            if os.path.exists("test_logs"):
                shutil.rmtree("test_logs")
            
            return {
                "status": "success",
                "training_time": training_time,
                "results_keys": list(results.keys()) if results else []
            }
        
        except Exception as e:
            self.logger.error(f"Erreur test pipeline: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests"""
        self.logger.info("Démarrage de tous les tests Deep Learning")
        
        start_time = time.time()
        
        # Tests des modèles
        self.results["cnn_models"] = self.test_cnn_models()
        self.results["rnn_models"] = self.test_rnn_models()
        self.results["transformer_models"] = self.test_transformer_models()
        self.results["ensemble_models"] = self.test_ensemble_models()
        self.results["training_pipeline"] = self.test_training_pipeline()
        
        total_time = time.time() - start_time
        
        # Résumé
        self.results["summary"] = {
            "total_time": total_time,
            "device": str(self.device),
            "timestamp": datetime.now().isoformat()
        }
        
        # Compter les succès/échecs
        total_tests = 0
        successful_tests = 0
        
        for category, tests in self.results.items():
            if isinstance(tests, dict) and "error" not in tests:
                for test_name, result in tests.items():
                    if isinstance(result, dict):
                        total_tests += 1
                        if result.get("status") == "success":
                            successful_tests += 1
        
        self.results["summary"]["total_tests"] = total_tests
        self.results["summary"]["successful_tests"] = successful_tests
        self.results["summary"]["success_rate"] = successful_tests / total_tests if total_tests > 0 else 0
        
        self.logger.info(f"Tests terminés: {successful_tests}/{total_tests} réussis")
        self.logger.info(f"Temps total: {total_time:.2f} secondes")
        
        return self.results
    
    def save_results(self, filename: str = None):
        """Sauvegarde les résultats des tests"""
        if filename is None:
            filename = f"deep_learning_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            self.logger.info(f"Résultats sauvegardés dans: {filename}")
        
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde résultats: {e}")


def main():
    """Fonction principale"""
    print("=" * 60)
    print("  CRYPTOSPREADEDGE - TEST DES MODÈLES DEEP LEARNING")
    print("=" * 60)
    
    # Créer le testeur
    tester = DeepLearningTester()
    
    # Exécuter tous les tests
    results = tester.run_all_tests()
    
    # Afficher le résumé
    print("\n" + "=" * 60)
    print("  RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    summary = results.get("summary", {})
    print(f"Tests réussis: {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)}")
    print(f"Taux de réussite: {summary.get('success_rate', 0):.2%}")
    print(f"Temps total: {summary.get('total_time', 0):.2f} secondes")
    print(f"Device utilisé: {summary.get('device', 'Unknown')}")
    
    # Détails par catégorie
    print("\n" + "-" * 60)
    print("  DÉTAILS PAR CATÉGORIE")
    print("-" * 60)
    
    for category, tests in results.items():
        if category != "summary" and isinstance(tests, dict):
            print(f"\n{category.upper()}:")
            
            if "error" in tests:
                print(f"  ❌ Erreur: {tests['error']}")
            else:
                for test_name, result in tests.items():
                    if isinstance(result, dict):
                        status = "✅" if result.get("status") == "success" else "❌"
                        print(f"  {status} {test_name}")
                        
                        if result.get("status") == "success":
                            print(f"    - Temps forward: {result.get('forward_time', 0):.4f}s")
                            print(f"    - Temps prédiction: {result.get('prediction_time', 0):.4f}s")
                        else:
                            print(f"    - Erreur: {result.get('error', 'Unknown')}")
    
    # Sauvegarder les résultats
    tester.save_results()
    
    print("\n" + "=" * 60)
    print("  TESTS TERMINÉS")
    print("=" * 60)


if __name__ == "__main__":
    main()