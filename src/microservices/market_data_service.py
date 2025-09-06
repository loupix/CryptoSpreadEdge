"""
Service de données de marché optimisé pour Docker Swarm
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

from ..connectors.connector_factory import connector_factory
from ..data_sources.data_aggregator import data_aggregator
from ..arbitrage.price_monitor import price_monitor


class MarketDataRequest(BaseModel):
    """Requête de données de marché"""
    symbols: List[str]
    timeframe: str = "1h"
    limit: int = 1000
    include_indicators: bool = False


class MarketDataResponse(BaseModel):
    """Réponse de données de marché"""
    symbol: str
    data: List[Dict[str, Any]]
    timestamp: datetime
    source: str
    cached: bool = False


class HealthResponse(BaseModel):
    """Réponse de santé"""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    performance: Dict[str, Any]


class MarketDataService:
    """Service de données de marché distribué"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.kafka_producer = None
        self.kafka_consumer = None
        self.is_running = False
        self.cache_ttl = 300  # 5 minutes
        self.batch_size = 100
        self.update_interval = 1  # seconde
        
        # Métriques de performance
        self.metrics = {
            "requests_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "kafka_messages_sent": 0,
            "avg_response_time": 0.0,
            "error_count": 0
        }
    
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
            
            # Initialiser les connecteurs
            await data_aggregator.initialize_connectors()
            
            # Démarrer le monitoring des prix
            await price_monitor.start()
            
            self.is_running = True
            self.logger.info("Service de données de marché initialisé")
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation service: {e}")
            raise
    
    async def get_market_data(self, request: MarketDataRequest) -> List[MarketDataResponse]:
        """Récupère les données de marché"""
        start_time = time.time()
        
        try:
            responses = []
            
            for symbol in request.symbols:
                # Vérifier le cache Redis
                cache_key = f"market_data:{symbol}:{request.timeframe}:{request.limit}"
                cached_data = await self._get_from_cache(cache_key)
                
                if cached_data and not request.include_indicators:
                    # Retourner les données du cache
                    response = MarketDataResponse(
                        symbol=symbol,
                        data=cached_data,
                        timestamp=datetime.utcnow(),
                        source="cache",
                        cached=True
                    )
                    responses.append(response)
                    self.metrics["cache_hits"] += 1
                else:
                    # Récupérer les données fraîches
                    fresh_data = await self._fetch_fresh_data(symbol, request)
                    
                    # Mettre en cache
                    await self._set_cache(cache_key, fresh_data, self.cache_ttl)
                    
                    response = MarketDataResponse(
                        symbol=symbol,
                        data=fresh_data,
                        timestamp=datetime.utcnow(),
                        source="live",
                        cached=False
                    )
                    responses.append(response)
                    self.metrics["cache_misses"] += 1
                    
                    # Publier sur Kafka pour les autres services
                    await self._publish_to_kafka(symbol, fresh_data)
            
            # Mettre à jour les métriques
            self.metrics["requests_processed"] += 1
            response_time = time.time() - start_time
            self.metrics["avg_response_time"] = (
                (self.metrics["avg_response_time"] * (self.metrics["requests_processed"] - 1) + response_time) /
                self.metrics["requests_processed"]
            )
            
            return responses
        
        except Exception as e:
            self.metrics["error_count"] += 1
            self.logger.error(f"Erreur récupération données: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_from_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
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
    
    async def _set_cache(self, key: str, data: List[Dict[str, Any]], ttl: int):
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
    
    async def _fetch_fresh_data(self, symbol: str, request: MarketDataRequest) -> List[Dict[str, Any]]:
        """Récupère les données fraîches depuis les exchanges"""
        try:
            # Récupérer les données depuis l'agrégateur
            data = await data_aggregator.get_aggregated_data([symbol])
            
            if symbol not in data or not data[symbol]:
                return []
            
            # Convertir en format standard
            market_data = []
            for point in data[symbol][-request.limit:]:
                market_data.append({
                    "timestamp": point.timestamp.isoformat(),
                    "open": float(point.ohlcv.open),
                    "high": float(point.ohlcv.high),
                    "low": float(point.ohlcv.low),
                    "close": float(point.ohlcv.close),
                    "volume": float(point.ohlcv.volume),
                    "source": point.source
                })
            
            return market_data
        
        except Exception as e:
            self.logger.error(f"Erreur récupération données fraîches {symbol}: {e}")
            return []
    
    async def _publish_to_kafka(self, symbol: str, data: List[Dict[str, Any]]):
        """Publie les données sur Kafka"""
        try:
            if not self.kafka_producer:
                return
            
            message = {
                "symbol": symbol,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "market-data"
            }
            
            self.kafka_producer.send(
                'market-data-updates',
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
            
            # Vérifier les connecteurs
            connectors_status = "healthy"
            try:
                connected_count = sum(
                    1 for connector in connector_factory.get_all_connectors().values()
                    if connector.is_connected()
                )
                if connected_count == 0:
                    connectors_status = "no_connections"
            except:
                connectors_status = "unhealthy"
            
            return HealthResponse(
                status="healthy" if all(s == "healthy" for s in [redis_status, kafka_status, connectors_status]) else "degraded",
                timestamp=datetime.utcnow(),
                services={
                    "redis": redis_status,
                    "kafka": kafka_status,
                    "connectors": connectors_status
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
            if self.redis_client:
                await self.redis_client.close()
            
            if self.kafka_producer:
                self.kafka_producer.close()
            
            if self.kafka_consumer:
                self.kafka_consumer.close()
            
            await price_monitor.stop()
            
            self.is_running = False
            self.logger.info("Service de données de marché arrêté")
        
        except Exception as e:
            self.logger.error(f"Erreur arrêt service: {e}")


# Instance globale du service
market_data_service = MarketDataService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    # Démarrage
    await market_data_service.initialize()
    yield
    # Arrêt
    await market_data_service.cleanup()


# Créer l'application FastAPI
app = FastAPI(
    title="Market Data Service",
    description="Service de données de marché pour CryptoSpreadEdge",
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
    return await market_data_service.get_health()


@app.post("/market-data", response_model=List[MarketDataResponse])
async def get_market_data(request: MarketDataRequest):
    """Endpoint de récupération des données de marché"""
    return await market_data_service.get_market_data(request)


@app.get("/metrics")
async def get_metrics():
    """Endpoint des métriques"""
    return market_data_service.metrics


@app.get("/cache/stats")
async def get_cache_stats():
    """Statistiques du cache"""
    try:
        if market_data_service.redis_client:
            info = await market_data_service.redis_client.info()
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
        "market_data_service:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Un seul worker pour éviter les conflits
        log_level="info"
    )