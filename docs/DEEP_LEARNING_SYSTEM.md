# Système Deep Learning CryptoSpreadEdge

Le système Deep Learning CryptoSpreadEdge intègre des modèles avancés de CNN, RNN et Transformer pour l'analyse et la prédiction de données financières, avec un système d'ensemble sophistiqué et un pipeline d'entraînement distribué.

## Architecture du Système

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEEP LEARNING SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│  Modèles CNN                                                   │
│  ├── FinancialCNN1D (Convolution 1D)                          │
│  ├── FinancialCNN2D (Convolution 2D)                          │
│  ├── ResidualCNN1D (Blocs résiduels)                          │
│  └── AttentionCNN1D (Avec attention)                          │
├─────────────────────────────────────────────────────────────────┤
│  Modèles RNN/LSTM                                              │
│  ├── FinancialLSTM (LSTM standard)                            │
│  ├── FinancialGRU (GRU)                                       │
│  ├── StackedLSTM (LSTM empilé)                                │
│  ├── BidirectionalLSTM (LSTM bidirectionnel)                  │
│  └── ConvLSTM (LSTM + Convolution)                            │
├─────────────────────────────────────────────────────────────────┤
│  Modèles Transformer                                           │
│  ├── FinancialTransformer (Transformer standard)              │
│  ├── FinancialTransformerWithAttention (Avec attention)       │
│  ├── FinancialTransformerEncoder (Encoder seul)               │
│  ├── FinancialTransformerDecoder (Decoder seul)               │
│  └── FinancialTransformerWithCNN (Transformer + CNN)          │
├─────────────────────────────────────────────────────────────────┤
│  Système d'Ensemble                                            │
│  ├── WeightedEnsemble (Moyenne pondérée)                      │
│  ├── StackingEnsemble (Méta-apprentissage)                    │
│  └── VotingEnsemble (Vote majoritaire)                        │
├─────────────────────────────────────────────────────────────────┤
│  Pipeline d'Entraînement                                       │
│  ├── Entraînement distribué (Multi-GPU)                       │
│  ├── Gestion des données                                       │
│  ├── Sauvegarde automatique                                    │
│  └── Monitoring des performances                               │
└─────────────────────────────────────────────────────────────────┘
```

## Modèles CNN

### 1. FinancialCNN1D
**Architecture** : CNN 1D pour l'analyse de séries temporelles
- **Couches** : 3 couches de convolution + pooling + FC
- **Fonctionnalités** :
  - Extraction de patterns temporels
  - Batch normalization
  - Dropout pour la régularisation
  - Pooling pour la réduction dimensionnelle

```python
# Configuration
cnn_config = CNNConfig(
    input_channels=4,      # OHLC
    sequence_length=100,   # Longueur de séquence
    num_classes=3,         # Buy, Sell, Hold
    dropout_rate=0.2
)

# Création du modèle
model = FinancialCNN1D(cnn_config)
```

### 2. FinancialCNN2D
**Architecture** : CNN 2D pour l'analyse de patterns 2D
- **Fonctionnalités** :
  - Redimensionnement 1D → 2D
  - 4 couches de convolution
  - Analyse de patterns spatiaux
  - Pooling 2D

### 3. ResidualCNN1D
**Architecture** : CNN avec blocs résiduels
- **Fonctionnalités** :
  - Blocs résiduels pour l'apprentissage profond
  - Connexions skip
  - Pooling global adaptatif
  - Architecture ResNet-like

### 4. AttentionCNN1D
**Architecture** : CNN avec mécanisme d'attention
- **Fonctionnalités** :
  - Auto-attention 1D
  - Attention multi-têtes
  - Focus sur les patterns importants
  - Pondération dynamique

## Modèles RNN/LSTM

### 1. FinancialLSTM
**Architecture** : LSTM standard pour séries temporelles
- **Fonctionnalités** :
  - Mémoire à long terme
  - Gestion des dépendances temporelles
  - Bidirectionnel optionnel
  - Initialisation des poids optimisée

```python
# Configuration
rnn_config = RNNConfig(
    input_size=4,          # OHLC
    hidden_size=128,       # Taille cachée
    num_layers=3,          # Nombre de couches
    sequence_length=100,   # Longueur de séquence
    num_classes=3,         # Classes de sortie
    bidirectional=True     # Bidirectionnel
)

# Création du modèle
model = FinancialLSTM(rnn_config)
```

### 2. FinancialGRU
**Architecture** : GRU (Gated Recurrent Unit)
- **Fonctionnalités** :
  - Architecture simplifiée vs LSTM
  - Moins de paramètres
  - Entraînement plus rapide
  - Performance comparable

### 3. StackedLSTM
**Architecture** : LSTM empilé avec attention
- **Fonctionnalités** :
  - 3 couches LSTM empilées
  - Mécanisme d'attention
  - Apprentissage hiérarchique
  - Extraction de features multi-niveaux

### 4. BidirectionalLSTM
**Architecture** : LSTM bidirectionnel avec attention
- **Fonctionnalités** :
  - Information future et passée
  - Attention multi-têtes
  - Pooling global
  - Contexte complet

### 5. ConvLSTM
**Architecture** : LSTM avec convolutions
- **Fonctionnalités** :
  - Extraction de features CNN
  - Modélisation temporelle LSTM
  - Combinaison optimale
  - Patterns spatiaux-temporels

## Modèles Transformer

### 1. FinancialTransformer
**Architecture** : Transformer standard
- **Fonctionnalités** :
  - Encodage positionnel
  - Attention multi-têtes
  - Blocs Transformer empilés
  - Pooling global adaptatif

```python
# Configuration
transformer_config = TransformerConfig(
    input_size=4,          # OHLC
    d_model=256,           # Dimension du modèle
    nhead=8,               # Nombre de têtes d'attention
    num_layers=6,          # Nombre de couches
    sequence_length=100,   # Longueur de séquence
    num_classes=3,         # Classes de sortie
    dropout_rate=0.1
)

# Création du modèle
model = FinancialTransformer(transformer_config)
```

### 2. FinancialTransformerWithAttention
**Architecture** : Transformer avec attention personnalisée
- **Fonctionnalités** :
  - Attention finale pour classification
  - Pondération par attention
  - Focus sur les points importants
  - Métriques d'attention

### 3. FinancialTransformerEncoder
**Architecture** : Encoder Transformer seul
- **Fonctionnalités** :
  - Encoder standard PyTorch
  - Optimisations intégrées
  - Entraînement stable
  - Performance éprouvée

### 4. FinancialTransformerDecoder
**Architecture** : Decoder Transformer
- **Fonctionnalités** :
  - Masque causal
  - Génération de prédictions
  - Auto-attention
  - Modélisation générative

### 5. FinancialTransformerWithCNN
**Architecture** : Transformer + CNN
- **Fonctionnalités** :
  - Extraction CNN préliminaire
  - Features enrichies
  - Combinaison hybride
  - Patterns locaux + globaux

## Système d'Ensemble

### 1. WeightedEnsemble
**Méthode** : Moyenne pondérée des prédictions
- **Fonctionnalités** :
  - Poids appris automatiquement
  - Combinaison de tous les modèles
  - Optimisation end-to-end
  - Performance adaptative

```python
# Configuration
ensemble_config = EnsembleConfig(
    cnn_models=["cnn1d", "residual_cnn1d"],
    rnn_models=["lstm", "bidirectional_lstm"],
    transformer_models=["transformer", "transformer_attention"],
    classical_models=["random_forest", "gradient_boosting"],
    ensemble_method="weighted_average"
)

# Création du modèle
model = WeightedEnsemble(ensemble_config)
```

### 2. StackingEnsemble
**Méthode** : Méta-apprentissage (stacking)
- **Fonctionnalités** :
  - Méta-modèle (réseau de neurones)
  - Apprentissage de la combinaison
  - Validation croisée
  - Performance optimale

### 3. VotingEnsemble
**Méthode** : Vote majoritaire pondéré
- **Fonctionnalités** :
  - Vote pondéré
  - Robustesse aux erreurs
  - Interprétabilité
  - Décision collective

## Pipeline d'Entraînement

### 1. Gestion des Données
```python
# Processeur de données
data_processor = DataProcessor(config)

# Chargement et préprocessing
data, labels = data_processor.load_data("data.csv")
X, y = data_processor.preprocess_data(data, labels)

# Création de séquences
X_sequences = data_processor.create_sequences(X, sequence_length=100)

# Division train/val/test
splits = data_processor.split_data(X_sequences, y)
```

### 2. Entraînement Distribué
```python
# Configuration distribuée
config = TrainingConfig(
    distributed=True,
    num_gpus=4,
    world_size=4
)

# Pipeline d'entraînement
pipeline = TrainingPipeline(config)

# Entraînement distribué
results = pipeline.run_distributed_training("data.csv", rank=0, world_size=4)
```

### 3. Monitoring et Sauvegarde
- **Métriques** : Loss, accuracy, precision, recall, F1
- **Sauvegarde** : Modèles, checkpoints, métriques
- **Logging** : TensorBoard, fichiers de log
- **Early Stopping** : Arrêt automatique

## Utilisation

### 1. Entraînement Simple
```python
from src.deep_learning.training_pipeline import TrainingPipeline, TrainingConfig

# Configuration
config = TrainingConfig(
    data_path="data/processed/",
    batch_size=32,
    num_epochs=100,
    learning_rate=0.001
)

# Pipeline
pipeline = TrainingPipeline(config)

# Entraînement
results = pipeline.run_training("financial_data.csv")
```

### 2. Entraînement Distribué
```python
import torch.multiprocessing as mp

def train_distributed(rank, world_size):
    config = TrainingConfig(distributed=True, world_size=world_size)
    pipeline = TrainingPipeline(config)
    pipeline.run_distributed_training("data.csv", rank, world_size)

# Lancer l'entraînement distribué
mp.spawn(train_distributed, args=(4,), nprocs=4)
```

### 3. Prédiction
```python
# Charger un modèle entraîné
model = FinancialTransformer(transformer_config)
model.load_state_dict(torch.load("best_model.pth"))

# Faire des prédictions
predictions = model.predict(data)
print(f"Prédictions: {predictions['predictions']}")
print(f"Confiance: {predictions['confidence']}")
```

## Tests et Validation

### 1. Tests Automatiques
```bash
# Exécuter tous les tests
python scripts/deep_learning/test_deep_learning_models.py
```

### 2. Tests par Catégorie
- **Tests CNN** : Vérification des architectures
- **Tests RNN** : Validation des modèles temporels
- **Tests Transformer** : Contrôle des modèles d'attention
- **Tests Ensemble** : Validation des combinaisons
- **Tests Pipeline** : Vérification de l'entraînement

### 3. Métriques de Performance
- **Accuracy** : Précision globale
- **Precision** : Précision par classe
- **Recall** : Rappel par classe
- **F1-Score** : Score F1 pondéré
- **Temps d'entraînement** : Performance
- **Temps de prédiction** : Latence

## Optimisations

### 1. Performance
- **GPU Support** : CUDA optimisé
- **Entraînement distribué** : Multi-GPU
- **Gradient Clipping** : Stabilité
- **Mixed Precision** : FP16 pour vitesse
- **DataLoader optimisé** : Chargement parallèle

### 2. Mémoire
- **Gradient Checkpointing** : Économie mémoire
- **Batch Size adaptatif** : Optimisation automatique
- **Nettoyage automatique** : Gestion mémoire
- **Modèles quantifiés** : Réduction taille

### 3. Entraînement
- **Learning Rate Scheduling** : Adaptation automatique
- **Early Stopping** : Éviter l'overfitting
- **Regularization** : Dropout, weight decay
- **Data Augmentation** : Robustesse

## Configuration Avancée

### 1. Hyperparamètres
```python
# Configuration optimisée
cnn_config = CNNConfig(
    input_channels=4,
    sequence_length=100,
    num_classes=3,
    dropout_rate=0.2,
    learning_rate=0.001,
    batch_size=32,
    num_epochs=100
)

rnn_config = RNNConfig(
    input_size=4,
    hidden_size=128,
    num_layers=3,
    sequence_length=100,
    num_classes=3,
    dropout_rate=0.2,
    bidirectional=True
)

transformer_config = TransformerConfig(
    input_size=4,
    d_model=256,
    nhead=8,
    num_layers=6,
    sequence_length=100,
    num_classes=3,
    dropout_rate=0.1
)
```

### 2. Modèles Personnalisés
```python
# Créer un modèle personnalisé
class CustomModel(BaseCNNModel):
    def __init__(self, config):
        super().__init__(config)
        # Architecture personnalisée
    
    def forward(self, x):
        # Logique personnalisée
        return output

# Enregistrer dans la factory
CNNModelFactory.register_model("custom", CustomModel)
```

### 3. Entraînement Personnalisé
```python
# Entraîneur personnalisé
class CustomTrainer:
    def __init__(self, model, config):
        self.model = model
        self.config = config
    
    def train(self, train_loader, val_loader):
        # Logique d'entraînement personnalisée
        pass
```

## Intégration avec le Système

### 1. Service de Prédiction
```python
# Intégration dans le service de prédiction
from src.deep_learning.ensemble_models import EnsembleModelFactory

class PredictionService:
    def __init__(self):
        self.ensemble_model = EnsembleModelFactory.create_model(
            "weighted_ensemble", ensemble_config
        )
    
    def predict(self, data):
        return self.ensemble_model.predict(data)
```

### 2. API REST
```python
# Endpoint pour les prédictions
@app.post("/predictions/deep_learning")
async def predict_deep_learning(request: PredictionRequest):
    predictions = prediction_service.predict(request.data)
    return PredictionResponse(
        predictions=predictions["predictions"],
        confidence=predictions["confidence"]
    )
```

### 3. Monitoring
```python
# Métriques de performance
@app.get("/metrics/deep_learning")
async def get_deep_learning_metrics():
    return {
        "model_accuracy": model_accuracy,
        "prediction_latency": prediction_latency,
        "model_confidence": model_confidence
    }
```

## Déploiement

### 1. Docker
```dockerfile
# Dockerfile pour les modèles Deep Learning
FROM nvidia/cuda:11.8-devel-ubuntu20.04

# Installation des dépendances
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip install transformers scikit-learn

# Copie du code
COPY src/ /app/src/
COPY models/ /app/models/

# Commande de démarrage
CMD ["python", "-m", "src.deep_learning.prediction_service"]
```

### 2. Kubernetes
```yaml
# Déploiement Kubernetes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deep-learning-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: deep-learning
  template:
    metadata:
      labels:
        app: deep-learning
    spec:
      containers:
      - name: deep-learning
        image: cryptospreadedge/deep-learning:latest
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
```

### 3. Scaling
- **Horizontal** : Répliques multiples
- **Vertical** : GPU plus puissants
- **Auto-scaling** : Basé sur la charge
- **Load balancing** : Distribution des requêtes

Le système Deep Learning CryptoSpreadEdge représente l'état de l'art en matière d'IA pour le trading financier, combinant les dernières avancées en CNN, RNN et Transformer avec un système d'ensemble sophistiqué et un pipeline d'entraînement distribué pour offrir des prédictions de haute qualité en temps réel.