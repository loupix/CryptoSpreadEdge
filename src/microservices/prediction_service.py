"""
Service de prédiction ML optimisé pour Docker Swarm
"""

import asyncio
import logging
import json
import time
import pickle
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import aioredis
from kafka import KafkaProducer, KafkaConsumer
import uvicorn
from contextlib import asynccontextmanager
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import torch
import joblib

from ..prediction.ml_predictor import MLPredictor
from ..prediction.signal_generator import SignalGenerator, MLPredictionStrategy
from ..monitoring.market_abuse.opportunities import Opportunity
from ..monitoring.market_abuse.opportunity_sinks import DatabaseOpportunitySink
from ..monitoring.market_abuse.redis_sinks import RedisAlertSink, RedisOpportunitySink
from ..database.database import init_database
from ..monitoring.market_abuse.stream_monitor import MarketAbuseStreamMonitor
from ..monitoring.market_abuse.calibration import AutoThresholdCalibrator


class PredictionRequest(BaseModel):
    """Requête de prédiction"""
    symbol: str
    data: List[Dict[str, Any]]
    model_type: str = "ensemble"
    prediction_horizon: int = 5
    include_confidence: bool = True


class PredictionResponse(BaseModel):
    """Réponse de prédiction"""
    symbol: str
    predictions: List[Dict[str, Any]]
    model_used: str
    timestamp: datetime
    processing_time: float
    confidence: float
    cached: bool = False


class TrainingRequest(BaseModel):
    """Requête d'entraînement"""
    symbol: str
    data: List[Dict[str, Any]]
    model_types: List[str] = ["RandomForest", "GradientBoosting", "LSTM"]
    test_size: float = 0.2


class TrainingResponse(BaseModel):
    """Réponse d'entraînement"""
    symbol: str
    results: Dict[str, Dict[str, Any]]
    timestamp: datetime
    training_time: float
    models_saved: List[str]


class HealthResponse(BaseModel):
    """Réponse de santé"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    performance: Dict[str, Any]


class OpportunityIn(BaseModel):
    """Payload d'opportunité à ingérer"""
    symbol: str
    kind: str
    confidence: float
    rationale: Optional[str] = None
    timestamp: Optional[datetime] = None


class PredictionService:
    """Service de prédiction ML distribué"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.kafka_producer = None
        self.kafka_consumer = None
        self.is_running = False
        self.cache_ttl = 1800  # 30 minutes
        
        # Prédicteurs ML
        self.ml_predictors = {}
        self.signal_generator = None
        
        # Pool de processus pour les calculs intensifs
        self.process_pool = ProcessPoolExecutor(max_workers=2)  # Limité pour les modèles ML
        
        # Métriques de performance
        self.metrics = {
            "predictions_processed": 0,
            "training_sessions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "kafka_messages_sent": 0,
            "avg_prediction_time": 0.0,
            "avg_training_time": 0.0,
            "error_count": 0,
            "models_loaded": 0
        }
        # Opportunités -> stratégie: monitors d'abus avec auto-calibration
        self.market_abuse_monitors = {}
    
    async def initialize(self):
        """Initialise le service"""
        try:
            # Initialiser Redis
            self.redis_client = await aioredis.from_url(
                "redis://redis-cluster:6379",
                encoding="utf-8",
                decode_responses=True
            )
            
            # Initialiser Kafka
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['kafka-cluster:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10
            )
            
            # Initialiser le consumer Kafka
            self.kafka_consumer = KafkaConsumer(
                'indicators-updates',
                bootstrap_servers=['kafka-cluster:9092'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='prediction-service',
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            # Initialiser le générateur de signaux
            self.signal_generator = SignalGenerator("PredictionSignalGenerator")
            self.signal_generator.add_strategy(MLPredictionStrategy("MLPrediction"))
            # Préparer des monitors avec auto-calibration
            calib = AutoThresholdCalibrator()
            for sym in ["BTC/USDT", "ETH/USDT"]:
                self.market_abuse_monitors[sym] = MarketAbuseStreamMonitor(
                    symbol=sym,
                    symbol_thresholds={sym: 0.5},
                    auto_calibrator=calib,
                    on_opportunities=self._on_opportunities_to_strategy,
                )
                # Ajouter sinks Redis pour alertes et opportunités
                try:
                    self.market_abuse_monitors[sym].sinks.append(RedisAlertSink())
                    self.market_abuse_monitors[sym].opportunity_sinks.append(RedisOpportunitySink())
                except Exception:
                    pass
            
            # Charger les modèles pré-entraînés
            await self._load_pretrained_models()
            
            # Démarrer le consumer en arrière-plan
            asyncio.create_task(self._consume_indicators())
            
            self.is_running = True
            self.logger.info("Service de prédiction ML initialisé")
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation service: {e}")
            raise
    
    async def _load_pretrained_models(self):
        """Charge les modèles pré-entraînés"""
        try:
            # Charger les modèles depuis le volume partagé
            model_paths = [
                "models/btc_models.pkl",
                "models/eth_models.pkl",
                "models/bnb_models.pkl"
            ]
            
            for model_path in model_paths:
                try:
                    symbol = model_path.split('/')[-1].split('_')[0].upper()
                    predictor = MLPredictor(f"Predictor_{symbol}")
                    predictor.load_models(model_path)
                    self.ml_predictors[symbol] = predictor
                    self.metrics["models_loaded"] += 1
                    self.logger.info(f"Modèle chargé pour {symbol}")
                except Exception as e:
                    self.logger.warning(f"Impossible de charger le modèle {model_path}: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur chargement modèles: {e}")
    
    async def _consume_indicators(self):
        """Consomme les indicateurs depuis Kafka"""
        try:
            for message in self.kafka_consumer:
                if not self.is_running:
                    break
                
                try:
                    data = message.value
                    symbol = data.get('symbol')
                    indicators = data.get('indicators', {})
                    
                    if symbol and indicators:
                        # Faire des prédictions en arrière-plan
                        asyncio.create_task(self._process_indicators_async(symbol, indicators))
                
                except Exception as e:
                    self.logger.error(f"Erreur traitement message Kafka: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur consumer Kafka: {e}")
    
    async def _process_indicators_async(self, symbol: str, indicators: Dict[str, Any]):
        """Traite les indicateurs de manière asynchrone"""
        try:
            # Faire des prédictions si un modèle est disponible
            if symbol in self.ml_predictors:
                predictions = await self._make_predictions_async(symbol, indicators)
                
                if predictions:
                    # Publier sur Kafka
                    await self._publish_predictions(symbol, predictions)
        
        except Exception as e:
            self.logger.error(f"Erreur traitement indicateurs {symbol}: {e}")
    
    async def make_predictions(self, request: PredictionRequest) -> PredictionResponse:
        """Fait des prédictions pour les données fournies"""
        start_time = time.time()
        
        try:
            # Vérifier le cache
            cache_key = f"predictions:{request.symbol}:{request.model_type}:{request.prediction_horizon}"
            cached_data = await self._get_from_cache(cache_key)
            
            if cached_data:
                self.metrics["cache_hits"] += 1
                return PredictionResponse(
                    symbol=request.symbol,
                    predictions=cached_data["predictions"],
                    model_used=cached_data["model_used"],
                    timestamp=datetime.utcnow(),
                    processing_time=0.0,
                    confidence=cached_data["confidence"],
                    cached=True
                )
            
            # Convertir les données en DataFrame
            df = pd.DataFrame(request.data)
            if df.empty:
                raise HTTPException(status_code=400, detail="Données vides")
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Faire les prédictions
            predictions_data = await self._make_predictions_async(
                request.symbol, 
                df, 
                request.model_type,
                request.prediction_horizon
            )
            
            if not predictions_data:
                raise HTTPException(status_code=500, detail="Erreur lors des prédictions")
            
            processing_time = time.time() - start_time
            
            # Mettre en cache
            cache_data = {
                "predictions": predictions_data,
                "model_used": request.model_type,
                "confidence": np.mean([p.get("confidence", 0.5) for p in predictions_data])
            }
            await self._set_cache(cache_key, cache_data, self.cache_ttl)
            
            # Mettre à jour les métriques
            self.metrics["predictions_processed"] += 1
            self.metrics["cache_misses"] += 1
            self.metrics["avg_prediction_time"] = (
                (self.metrics["avg_prediction_time"] * (self.metrics["predictions_processed"] - 1) + processing_time) /
                self.metrics["predictions_processed"]
            )
            
            return PredictionResponse(
                symbol=request.symbol,
                predictions=predictions_data,
                model_used=request.model_type,
                timestamp=datetime.utcnow(),
                processing_time=processing_time,
                confidence=cache_data["confidence"],
                cached=False
            )
        
        except Exception as e:
            self.metrics["error_count"] += 1
            self.logger.error(f"Erreur prédictions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _make_predictions_async(self, symbol: str, data: Any, 
                                    model_type: str = "ensemble", 
                                    prediction_horizon: int = 5) -> List[Dict[str, Any]]:
        """Fait des prédictions de manière asynchrone"""
        try:
            # Utiliser le prédicteur spécifique au symbole ou créer un nouveau
            if symbol in self.ml_predictors:
                predictor = self.ml_predictors[symbol]
            else:
                predictor = MLPredictor(f"Predictor_{symbol}")
                self.ml_predictors[symbol] = predictor
            
            # Faire les prédictions
            if model_type == "ensemble":
                predictions = predictor.predict_ensemble(data)
            else:
                predictions = predictor.predict(data, model_type)
            
            if not predictions:
                return []
            
            # Convertir en format standard
            predictions_data = []
            for pred in predictions:
                predictions_data.append({
                    "predicted_price": float(pred.predicted_price),
                    "predicted_change": float(pred.predicted_change),
                    "confidence": float(pred.confidence),
                    "timestamp": pred.timestamp.isoformat(),
                    "model_name": pred.model_name,
                    "features_used": pred.features_used,
                    "metadata": pred.metadata or {}
                })
            
            return predictions_data
        
        except Exception as e:
            self.logger.error(f"Erreur prédictions {symbol}: {e}")
            return []
    
    async def train_models(self, request: TrainingRequest) -> TrainingResponse:
        """Entraîne les modèles ML"""
        start_time = time.time()
        
        try:
            # Convertir les données en DataFrame
            df = pd.DataFrame(request.data)
            if df.empty:
                raise HTTPException(status_code=400, detail="Données vides")
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Créer ou récupérer le prédicteur
            if request.symbol in self.ml_predictors:
                predictor = self.ml_predictors[request.symbol]
            else:
                predictor = MLPredictor(f"Predictor_{request.symbol}")
                self.ml_predictors[request.symbol] = predictor
            
            # Entraîner les modèles
            training_results = predictor.train_models(df)
            
            training_time = time.time() - start_time
            
            # Sauvegarder les modèles
            model_path = f"models/{request.symbol.lower()}_models.pkl"
            predictor.save_models(model_path)
            
            # Mettre à jour les métriques
            self.metrics["training_sessions"] += 1
            self.metrics["avg_training_time"] = (
                (self.metrics["avg_training_time"] * (self.metrics["training_sessions"] - 1) + training_time) /
                self.metrics["training_sessions"]
            )
            
            return TrainingResponse(
                symbol=request.symbol,
                results=training_results,
                timestamp=datetime.utcnow(),
                training_time=training_time,
                models_saved=[model_path]
            )
        
        except Exception as e:
            self.metrics["error_count"] += 1
            self.logger.error(f"Erreur entraînement: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Récupère les données du cache Redis"""
        try:
            if not self.redis_client:
                return None
            
            cached_data = await self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        
        except Exception as e:
            self.logger.error(f"Erreur cache Redis: {e}")
            return None
    
    async def _set_cache(self, key: str, data: Dict[str, Any], ttl: int):
        """Met les données en cache Redis"""
        try:
            if not self.redis_client:
                return
            
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(data, default=str)
            )
        
        except Exception as e:
            self.logger.error(f"Erreur mise en cache: {e}")
    
    async def _publish_predictions(self, symbol: str, predictions: List[Dict[str, Any]]):
        """Publie les prédictions sur Kafka"""
        try:
            if not self.kafka_producer:
                return
            
            message = {
                "symbol": symbol,
                "predictions": predictions,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "prediction"
            }
            
            self.kafka_producer.send(
                'predictions-updates',
                value=message,
                key=symbol.encode('utf-8')
            )
            
            self.metrics["kafka_messages_sent"] += 1
        
        except Exception as e:
            self.logger.error(f"Erreur publication Kafka: {e}")
    
    async def get_health(self) -> HealthResponse:
        """Retourne l'état de santé du service"""
        try:
            # Vérifier Redis
            redis_status = "healthy"
            try:
                if self.redis_client:
                    await self.redis_client.ping()
                else:
                    redis_status = "disconnected"
            except:
                redis_status = "unhealthy"
            
            # Vérifier Kafka
            kafka_status = "healthy"
            try:
                if self.kafka_producer:
                    self.kafka_producer.flush(timeout=1)
                else:
                    kafka_status = "disconnected"
            except:
                kafka_status = "unhealthy"
            
            # Vérifier les modèles
            models_status = "healthy"
            if not self.ml_predictors:
                models_status = "no_models"
            
            return HealthResponse(
                status="healthy" if all(s == "healthy" for s in [redis_status, kafka_status, models_status]) else "degraded",
                timestamp=datetime.utcnow(),
                services={
                    "redis": redis_status,
                    "kafka": kafka_status,
                    "models": models_status
                },
                performance=self.metrics
            )
        
        except Exception as e:
            self.logger.error(f"Erreur health check: {e}")
            return HealthResponse(
                status="unhealthy",
                timestamp=datetime.utcnow(),
                services={},
                performance={}
            )
    
    async def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.is_running = False
            
            if self.redis_client:
                await self.redis_client.close()
            
            if self.kafka_producer:
                self.kafka_producer.close()
            
            if self.kafka_consumer:
                self.kafka_consumer.close()
            
            self.process_pool.shutdown(wait=True)
            self.market_abuse_monitors.clear()
            
            self.logger.info("Service de prédiction ML arrêté")
        
        except Exception as e:
            self.logger.error(f"Erreur arrêt service: {e}")

    def _on_opportunities_to_strategy(self, opps):
        try:
            if not self.kafka_producer:
                return
            for o in opps:
                self.kafka_producer.send(
                    'strategy-signals',
                    {
                        "type": "opportunity",
                        "symbol": o.symbol,
                        "kind": o.kind,
                        "confidence": o.confidence,
                        "rationale": o.rationale,
                        "timestamp": o.timestamp.isoformat(),
                    },
                )
                self.metrics["kafka_messages_sent"] += 1
        except Exception as e:
            self.logger.warning(f"Émission de signaux stratégie échouée: {e}")


# Instance globale du service
prediction_service = PredictionService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    # Démarrage
    await prediction_service.initialize()
    yield
    # Arrêt
    await prediction_service.cleanup()


# Créer l'application FastAPI
app = FastAPI(
    title="Prediction Service",
    description="Service de prédiction ML pour CryptoSpreadEdge",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de santé"""
    return await prediction_service.get_health()


@app.post("/predictions", response_model=PredictionResponse)
async def make_predictions(request: PredictionRequest):
    """Endpoint de prédictions"""
    return await prediction_service.make_predictions(request)


@app.post("/training", response_model=TrainingResponse)
async def train_models(request: TrainingRequest):
    """Endpoint d'entraînement"""
    return await prediction_service.train_models(request)


@app.get("/models/available")
async def get_available_models():
    """Liste des modèles disponibles"""
    return {
        "models": list(prediction_service.ml_predictors.keys()),
        "count": len(prediction_service.ml_predictors)
    }


@app.get("/metrics")
async def get_metrics():
    """Endpoint des métriques"""
    return prediction_service.metrics


@app.get("/cache/stats")
async def get_cache_stats():
    """Statistiques du cache"""
    try:
        if prediction_service.redis_client:
            info = await prediction_service.redis_client.info()
            return {
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
            }
        return {"error": "Redis non connecté"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/opportunities/ingest")
async def ingest_opportunity(opp: OpportunityIn, background_tasks: BackgroundTasks):
    """Ingestion d'une opportunité: persiste en DB et notifie la stratégie via Kafka"""
    try:
        # Persistance DB (async)
        async def persist():
            await init_database()
            sink = DatabaseOpportunitySink()
            o = Opportunity(
                timestamp=opp.timestamp or datetime.utcnow(),
                symbol=opp.symbol,
                kind=opp.kind,
                confidence=opp.confidence,
                rationale=opp.rationale or "",
            )
            await sink.emit_async([o])

        background_tasks.add_task(persist)

        # Notifier via Kafka une stratégie (léger)
        if prediction_service.kafka_producer:
            prediction_service.kafka_producer.send(
                'opportunities',
                {
                    "symbol": opp.symbol,
                    "kind": opp.kind,
                    "confidence": opp.confidence,
                    "rationale": opp.rationale or "",
                    "timestamp": (opp.timestamp or datetime.utcnow()).isoformat(),
                },
            )
            prediction_service.metrics["kafka_messages_sent"] += 1

        return {"status": "accepted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Démarrer le service
    uvicorn.run(
        "prediction_service:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Un seul worker pour éviter les conflits
        log_level="info"
    )