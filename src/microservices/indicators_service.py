"""
Service d'indicateurs optimisé pour Docker Swarm
"""

import asyncio
import logging
import json
import time
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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing

from ..indicators.base_indicator import IndicatorComposite, IndicatorFactory
from ..indicators.technical_indicators import (
    MovingAverageIndicator, RSIIndicator, MACDIndicator,
    BollingerBandsIndicator, StochasticIndicator, VolumeIndicator, ATRIndicator
)
from ..indicators.advanced_indicators import (
    IchimokuIndicator, WilliamsRIndicator, VolatilityIndicator
)


class IndicatorRequest(BaseModel):
    """Requête de calcul d'indicateurs"""
    symbol: str
    data: List[Dict[str, Any]]
    indicators: List[str]
    timeframe: str = "1h"


class IndicatorResponse(BaseModel):
    """Réponse de calcul d'indicateurs"""
    symbol: str
    indicators: Dict[str, List[Dict[str, Any]]]
    timestamp: datetime
    processing_time: float
    cached: bool = False


class HealthResponse(BaseModel):
    """Réponse de santé"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    performance: Dict[str, Any]


class IndicatorsService:
    """Service d'indicateurs distribué"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.kafka_producer = None
        self.kafka_consumer = None
        self.is_running = False
        self.cache_ttl = 600  # 10 minutes
        self.batch_size = 50
        
        # Pool de processus pour les calculs intensifs
        self.process_pool = ProcessPoolExecutor(max_workers=4)
        self.thread_pool = ThreadPoolExecutor(max_workers=8)
        
        # Indicateurs disponibles
        self.indicators_registry = {}
        self._initialize_indicators()
        
        # Métriques de performance
        self.metrics = {
            "calculations_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "kafka_messages_sent": 0,
            "avg_processing_time": 0.0,
            "error_count": 0,
            "indicators_available": len(self.indicators_registry)
        }
    
    def _initialize_indicators(self):
        """Initialise le registre des indicateurs"""
        try:
            # Indicateurs techniques
            technical_indicators = {
                "SMA_20": lambda: MovingAverageIndicator("SMA_20", "SMA", 20),
                "SMA_50": lambda: MovingAverageIndicator("SMA_50", "SMA", 50),
                "EMA_20": lambda: MovingAverageIndicator("EMA_20", "EMA", 20),
                "RSI_14": lambda: RSIIndicator("RSI_14", 14),
                "MACD": lambda: MACDIndicator("MACD", 12, 26, 9),
                "BB_20": lambda: BollingerBandsIndicator("BB_20", 20, 2.0),
                "STOCH_14": lambda: StochasticIndicator("STOCH_14", 14, 3),
                "VOLUME_20": lambda: VolumeIndicator("VOLUME_20", 20),
                "ATR_14": lambda: ATRIndicator("ATR_14", 14)
            }
            
            # Indicateurs avancés
            advanced_indicators = {
                "ICHIMOKU": lambda: IchimokuIndicator("ICHIMOKU", 9, 26, 52),
                "WILLIAMS_R": lambda: WilliamsRIndicator("WILLIAMS_R", 14),
                "VOLATILITY": lambda: VolatilityIndicator("VOLATILITY", 20)
            }
            
            self.indicators_registry = {**technical_indicators, **advanced_indicators}
            self.logger.info(f"Indicateurs initialisés: {len(self.indicators_registry)}")
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation indicateurs: {e}")
    
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
                'market-data-updates',
                bootstrap_servers=['kafka-cluster:9092'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='indicators-service',
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            # Démarrer le consumer en arrière-plan
            asyncio.create_task(self._consume_market_data())
            
            self.is_running = True
            self.logger.info("Service d'indicateurs initialisé")
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation service: {e}")
            raise
    
    async def _consume_market_data(self):
        """Consomme les données de marché depuis Kafka"""
        try:
            for message in self.kafka_consumer:
                if not self.is_running:
                    break
                
                try:
                    data = message.value
                    symbol = data.get('symbol')
                    market_data = data.get('data', [])
                    
                    if symbol and market_data:
                        # Calculer les indicateurs en arrière-plan
                        asyncio.create_task(self._process_market_data_async(symbol, market_data))
                
                except Exception as e:
                    self.logger.error(f"Erreur traitement message Kafka: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur consumer Kafka: {e}")
    
    async def _process_market_data_async(self, symbol: str, market_data: List[Dict[str, Any]]):
        """Traite les données de marché de manière asynchrone"""
        try:
            # Convertir en DataFrame
            df = pd.DataFrame(market_data)
            if df.empty:
                return
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Calculer tous les indicateurs
            indicators_data = await self._calculate_indicators_parallel(symbol, df)
            
            # Mettre en cache
            await self._cache_indicators(symbol, indicators_data)
            
            # Publier sur Kafka
            await self._publish_indicators(symbol, indicators_data)
        
        except Exception as e:
            self.logger.error(f"Erreur traitement données {symbol}: {e}")
    
    async def calculate_indicators(self, request: IndicatorRequest) -> IndicatorResponse:
        """Calcule les indicateurs pour les données fournies"""
        start_time = time.time()
        
        try:
            # Vérifier le cache
            cache_key = f"indicators:{request.symbol}:{':'.join(request.indicators)}"
            cached_data = await self._get_from_cache(cache_key)
            
            if cached_data:
                self.metrics["cache_hits"] += 1
                return IndicatorResponse(
                    symbol=request.symbol,
                    indicators=cached_data,
                    timestamp=datetime.utcnow(),
                    processing_time=0.0,
                    cached=True
                )
            
            # Convertir les données en DataFrame
            df = pd.DataFrame(request.data)
            if df.empty:
                raise HTTPException(status_code=400, detail="Données vides")
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Calculer les indicateurs
            indicators_data = await self._calculate_indicators_parallel(request.symbol, df, request.indicators)
            
            # Mettre en cache
            await self._set_cache(cache_key, indicators_data, self.cache_ttl)
            
            processing_time = time.time() - start_time
            
            # Mettre à jour les métriques
            self.metrics["calculations_processed"] += 1
            self.metrics["cache_misses"] += 1
            self.metrics["avg_processing_time"] = (
                (self.metrics["avg_processing_time"] * (self.metrics["calculations_processed"] - 1) + processing_time) /
                self.metrics["calculations_processed"]
            )
            
            return IndicatorResponse(
                symbol=request.symbol,
                indicators=indicators_data,
                timestamp=datetime.utcnow(),
                processing_time=processing_time,
                cached=False
            )
        
        except Exception as e:
            self.metrics["error_count"] += 1
            self.logger.error(f"Erreur calcul indicateurs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _calculate_indicators_parallel(self, symbol: str, df: pd.DataFrame, 
                                           requested_indicators: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Calcule les indicateurs en parallèle"""
        try:
            if requested_indicators is None:
                requested_indicators = list(self.indicators_registry.keys())
            
            # Filtrer les indicateurs disponibles
            available_indicators = [ind for ind in requested_indicators if ind in self.indicators_registry]
            
            if not available_indicators:
                return {}
            
            # Créer les tâches de calcul
            tasks = []
            for indicator_name in available_indicators:
                task = asyncio.create_task(
                    self._calculate_single_indicator(indicator_name, df)
                )
                tasks.append((indicator_name, task))
            
            # Attendre tous les calculs
            results = {}
            for indicator_name, task in tasks:
                try:
                    indicator_values = await task
                    if indicator_values:
                        results[indicator_name] = [
                            {
                                "value": float(val.value),
                                "timestamp": val.timestamp.isoformat(),
                                "confidence": float(val.confidence),
                                "metadata": val.metadata or {}
                            }
                            for val in indicator_values
                        ]
                except Exception as e:
                    self.logger.error(f"Erreur calcul {indicator_name}: {e}")
                    results[indicator_name] = []
            
            return results
        
        except Exception as e:
            self.logger.error(f"Erreur calcul parallèle: {e}")
            return {}
    
    async def _calculate_single_indicator(self, indicator_name: str, df: pd.DataFrame) -> List[Any]:
        """Calcule un indicateur unique"""
        try:
            # Créer l'indicateur
            indicator = self.indicators_registry[indicator_name]()
            
            # Calculer les valeurs
            values = indicator.calculate(df)
            
            return values
        
        except Exception as e:
            self.logger.error(f"Erreur calcul {indicator_name}: {e}")
            return []
    
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
    
    async def _cache_indicators(self, symbol: str, indicators_data: Dict[str, Any]):
        """Met les indicateurs en cache"""
        try:
            for indicator_name, values in indicators_data.items():
                cache_key = f"indicators:{symbol}:{indicator_name}"
                await self._set_cache(cache_key, values, self.cache_ttl)
        
        except Exception as e:
            self.logger.error(f"Erreur cache indicateurs: {e}")
    
    async def _publish_indicators(self, symbol: str, indicators_data: Dict[str, Any]):
        """Publie les indicateurs sur Kafka"""
        try:
            if not self.kafka_producer:
                return
            
            message = {
                "symbol": symbol,
                "indicators": indicators_data,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "indicators"
            }
            
            self.kafka_producer.send(
                'indicators-updates',
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
            
            return HealthResponse(
                status="healthy" if all(s == "healthy" for s in [redis_status, kafka_status]) else "degraded",
                timestamp=datetime.utcnow(),
                services={
                    "redis": redis_status,
                    "kafka": kafka_status,
                    "indicators": "healthy"
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
            self.thread_pool.shutdown(wait=True)
            
            self.logger.info("Service d'indicateurs arrêté")
        
        except Exception as e:
            self.logger.error(f"Erreur arrêt service: {e}")


# Instance globale du service
indicators_service = IndicatorsService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    # Démarrage
    await indicators_service.initialize()
    yield
    # Arrêt
    await indicators_service.cleanup()


# Créer l'application FastAPI
app = FastAPI(
    title="Indicators Service",
    description="Service d'indicateurs pour CryptoSpreadEdge",
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
    return await indicators_service.get_health()


@app.post("/indicators", response_model=IndicatorResponse)
async def calculate_indicators(request: IndicatorRequest):
    """Endpoint de calcul d'indicateurs"""
    return await indicators_service.calculate_indicators(request)


@app.get("/indicators/available")
async def get_available_indicators():
    """Liste des indicateurs disponibles"""
    return {
        "indicators": list(indicators_service.indicators_registry.keys()),
        "count": len(indicators_service.indicators_registry)
    }


@app.get("/metrics")
async def get_metrics():
    """Endpoint des métriques"""
    return indicators_service.metrics


@app.get("/cache/stats")
async def get_cache_stats():
    """Statistiques du cache"""
    try:
        if indicators_service.redis_client:
            info = await indicators_service.redis_client.info()
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


if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Démarrer le service
    uvicorn.run(
        "indicators_service:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Un seul worker pour éviter les conflits
        log_level="info"
    )