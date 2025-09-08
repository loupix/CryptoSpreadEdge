"""
API Gateway avec load balancing pour Docker Swarm
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import redis
import aioredis
from kafka import KafkaProducer, KafkaConsumer
import uvicorn
from contextlib import asynccontextmanager
import hashlib
import random
from ..utils.messaging.redis_bus import RedisEventBus


class ServiceHealth(BaseModel):
    """Santé d'un service"""
    name: str
    status: str
    response_time: float
    last_check: datetime
    endpoint: str


class GatewayHealth(BaseModel):
    """Santé du gateway"""
    status: str
    timestamp: datetime
    services: Dict[str, ServiceHealth]
    total_requests: int
    error_rate: float


class LoadBalancer:
    """Load balancer simple avec health checking"""
    
    def __init__(self):
        self.services = {
            "market-data": {
                "endpoints": [
                    "http://market-data-service:8000",
                    "http://market-data-service-2:8000",
                    "http://market-data-service-3:8000"
                ],
                "current_index": 0,
                "health_checks": {}
            },
            "indicators": {
                "endpoints": [
                    "http://indicators-service:8000",
                    "http://indicators-service-2:8000",
                    "http://indicators-service-3:8000",
                    "http://indicators-service-4:8000",
                    "http://indicators-service-5:8000"
                ],
                "current_index": 0,
                "health_checks": {}
            },
            "prediction": {
                "endpoints": [
                    "http://prediction-service:8000",
                    "http://prediction-service-2:8000"
                ],
                "current_index": 0,
                "health_checks": {}
            },
            "signals": {
                "endpoints": [
                    "http://signals-service:8000",
                    "http://signals-service-2:8000",
                    "http://signals-service-3:8000"
                ],
                "current_index": 0,
                "health_checks": {}
            },
            "positions": {
                "endpoints": [
                    "http://positions-service:8000",
                    "http://positions-service-2:8000"
                ],
                "current_index": 0,
                "health_checks": {}
            },
            "arbitrage": {
                "endpoints": [
                    "http://arbitrage-service:8000",
                    "http://arbitrage-service-2:8000",
                    "http://arbitrage-service-3:8000",
                    "http://arbitrage-service-4:8000"
                ],
                "current_index": 0,
                "health_checks": {}
            },
            "backtesting": {
                "endpoints": [
                    "http://backtesting-service:8000",
                    "http://backtesting-service-2:8000"
                ],
                "current_index": 0,
                "health_checks": {}
            }
        }
        
        self.health_check_interval = 30  # secondes
        self.request_timeout = 30  # secondes
        self.circuit_breaker_threshold = 5  # erreurs consécutives
        self.circuit_breaker_timeout = 60  # secondes
    
    async def get_healthy_endpoint(self, service_name: str) -> Optional[str]:
        """Récupère un endpoint sain pour un service"""
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        healthy_endpoints = []
        
        for endpoint in service["endpoints"]:
            health = service["health_checks"].get(endpoint)
            if health and health["status"] == "healthy":
                healthy_endpoints.append(endpoint)
        
        if not healthy_endpoints:
            return None
        
        # Round-robin simple
        endpoint = healthy_endpoints[service["current_index"] % len(healthy_endpoints)]
        service["current_index"] += 1
        
        return endpoint
    
    async def check_service_health(self, service_name: str, endpoint: str) -> bool:
        """Vérifie la santé d'un endpoint"""
        try:
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(f"{endpoint}/health")
                return response.status_code == 200
        except:
            return False
    
    async def update_health_checks(self):
        """Met à jour les health checks de tous les services"""
        for service_name, service in self.services.items():
            for endpoint in service["endpoints"]:
                start_time = time.time()
                is_healthy = await self.check_service_health(service_name, endpoint)
                response_time = time.time() - start_time
                
                # Mettre à jour le statut
                service["health_checks"][endpoint] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "response_time": response_time,
                    "last_check": datetime.utcnow(),
                    "consecutive_failures": 0 if is_healthy else service["health_checks"].get(endpoint, {}).get("consecutive_failures", 0) + 1
                }
    
    async def start_health_monitoring(self):
        """Démarre le monitoring de santé"""
        while True:
            try:
                await self.update_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logging.error(f"Erreur health monitoring: {e}")
                await asyncio.sleep(10)


class APIGateway:
    """API Gateway principal"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.kafka_producer = None
        self.load_balancer = LoadBalancer()
        self.is_running = False
        self.event_bus: Optional[RedisEventBus] = None
        
        # Métriques
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "requests_by_service": {},
            "error_rate": 0.0
        }
        
        # Cache pour les réponses
        self.response_cache = {}
        self.cache_ttl = 60  # secondes
    
    async def initialize(self):
        """Initialise le gateway"""
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
                retries=3
            )
            # Event bus
            self.event_bus = RedisEventBus()
            await self.event_bus.connect()
            
            # Démarrer le monitoring de santé
            asyncio.create_task(self.load_balancer.start_health_monitoring())
            
            self.is_running = True
            self.logger.info("API Gateway initialisé")
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation gateway: {e}")
            raise
    
    async def proxy_request(self, service_name: str, path: str, method: str, 
                          headers: Dict[str, str], body: Optional[bytes] = None) -> Response:
        """Proxy une requête vers un service"""
        start_time = time.time()
        
        try:
            # Récupérer un endpoint sain
            endpoint = await self.load_balancer.get_healthy_endpoint(service_name)
            if not endpoint:
                raise HTTPException(status_code=503, detail=f"Service {service_name} non disponible")
            
            # Vérifier le cache
            cache_key = self._generate_cache_key(service_name, path, method, body)
            cached_response = await self._get_from_cache(cache_key)
            
            if cached_response:
                return JSONResponse(
                    content=cached_response,
                    status_code=200,
                    headers={"X-Cache": "HIT"}
                )
            
            # Faire la requête
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method=method,
                    url=f"{endpoint}{path}",
                    headers=headers,
                    content=body
                )
                
                # Traiter la réponse
                response_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                
                # Mettre en cache si c'est une requête GET
                if method == "GET" and response.status_code == 200:
                    await self._set_cache(cache_key, response_data, self.cache_ttl)
                
                # Mettre à jour les métriques
                self._update_metrics(service_name, response.status_code, time.time() - start_time)
                # Publier événement requête
                await self._publish_api_event("api.requests", {
                    "service": service_name,
                    "path": path,
                    "method": method,
                    "status": response.status_code,
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
                return JSONResponse(
                    content=response_data,
                    status_code=response.status_code,
                    headers={"X-Cache": "MISS"}
                )
        
        except httpx.TimeoutException:
            self._update_metrics(service_name, 504, time.time() - start_time)
            await self._publish_api_event("api.errors", {
                "service": service_name,
                "path": path,
                "method": method,
                "error": "timeout",
                "duration_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.utcnow().isoformat(),
            })
            raise HTTPException(status_code=504, detail="Timeout de la requête")
        
        except Exception as e:
            self._update_metrics(service_name, 500, time.time() - start_time)
            self.logger.error(f"Erreur proxy {service_name}: {e}")
            await self._publish_api_event("api.errors", {
                "service": service_name,
                "path": path,
                "method": method,
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000),
                "timestamp": datetime.utcnow().isoformat(),
            })
            raise HTTPException(status_code=500, detail=str(e))
    
    def _generate_cache_key(self, service_name: str, path: str, method: str, body: Optional[bytes]) -> str:
        """Génère une clé de cache"""
        key_data = f"{service_name}:{path}:{method}"
        if body:
            key_data += f":{hashlib.md5(body).hexdigest()}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Récupère les données du cache"""
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
    
    async def _set_cache(self, key: str, data: Any, ttl: int):
        """Met les données en cache"""
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
    
    def _update_metrics(self, service_name: str, status_code: int, response_time: float):
        """Met à jour les métriques"""
        self.metrics["total_requests"] += 1
        
        if 200 <= status_code < 300:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        # Métriques par service
        if service_name not in self.metrics["requests_by_service"]:
            self.metrics["requests_by_service"][service_name] = 0
        self.metrics["requests_by_service"][service_name] += 1
        
        # Temps de réponse moyen
        self.metrics["avg_response_time"] = (
            (self.metrics["avg_response_time"] * (self.metrics["total_requests"] - 1) + response_time) /
            self.metrics["total_requests"]
        )
        
        # Taux d'erreur
        self.metrics["error_rate"] = (
            self.metrics["failed_requests"] / self.metrics["total_requests"] * 100
        )
    
    async def _publish_api_event(self, stream: str, message: Dict[str, Any]):
        try:
            if self.event_bus:
                await self.event_bus.publish(stream, message)
        except Exception:
            pass
    
    async def get_health(self) -> GatewayHealth:
        """Retourne l'état de santé du gateway"""
        try:
            services_health = {}
            
            for service_name, service in self.load_balancer.services.items():
                healthy_endpoints = [
                    endpoint for endpoint, health in service["health_checks"].items()
                    if health["status"] == "healthy"
                ]
                
                if healthy_endpoints:
                    # Prendre le premier endpoint sain
                    endpoint = healthy_endpoints[0]
                    health = service["health_checks"][endpoint]
                    
                    services_health[service_name] = ServiceHealth(
                        name=service_name,
                        status="healthy",
                        response_time=health["response_time"],
                        last_check=health["last_check"],
                        endpoint=endpoint
                    )
                else:
                    services_health[service_name] = ServiceHealth(
                        name=service_name,
                        status="unhealthy",
                        response_time=0.0,
                        last_check=datetime.utcnow(),
                        endpoint=""
                    )
            
            return GatewayHealth(
                status="healthy" if all(s.status == "healthy" for s in services_health.values()) else "degraded",
                timestamp=datetime.utcnow(),
                services=services_health,
                total_requests=self.metrics["total_requests"],
                error_rate=self.metrics["error_rate"]
            )
        
        except Exception as e:
            self.logger.error(f"Erreur health check: {e}")
            return GatewayHealth(
                status="unhealthy",
                timestamp=datetime.utcnow(),
                services={},
                total_requests=0,
                error_rate=100.0
            )
    
    async def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.is_running = False
            
            if self.redis_client:
                await self.redis_client.close()
            
            if self.kafka_producer:
                self.kafka_producer.close()
            
            if self.event_bus:
                self.event_bus.stop()
                await self.event_bus.close()
                self.event_bus = None
            
            self.logger.info("API Gateway arrêté")
        
        except Exception as e:
            self.logger.error(f"Erreur arrêt gateway: {e}")


# Instance globale du gateway
api_gateway = APIGateway()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    # Démarrage
    await api_gateway.initialize()
    yield
    # Arrêt
    await api_gateway.cleanup()


# Créer l'application FastAPI
app = FastAPI(
    title="CryptoSpreadEdge API Gateway",
    description="API Gateway avec load balancing pour CryptoSpreadEdge",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/health", response_model=GatewayHealth)
async def health_check():
    """Endpoint de santé du gateway"""
    return await api_gateway.get_health()


@app.get("/metrics")
async def get_metrics():
    """Métriques du gateway"""
    return api_gateway.metrics


# Routes de proxy pour chaque service
@app.api_route("/market-data/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_market_data(request: Request, path: str):
    """Proxy pour le service de données de marché"""
    body = await request.body() if request.method in ["POST", "PUT"] else None
    return await api_gateway.proxy_request(
        "market-data",
        f"/{path}",
        request.method,
        dict(request.headers),
        body
    )


@app.api_route("/indicators/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_indicators(request: Request, path: str):
    """Proxy pour le service d'indicateurs"""
    body = await request.body() if request.method in ["POST", "PUT"] else None
    return await api_gateway.proxy_request(
        "indicators",
        f"/{path}",
        request.method,
        dict(request.headers),
        body
    )


@app.api_route("/predictions/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_predictions(request: Request, path: str):
    """Proxy pour le service de prédiction"""
    body = await request.body() if request.method in ["POST", "PUT"] else None
    return await api_gateway.proxy_request(
        "prediction",
        f"/{path}",
        request.method,
        dict(request.headers),
        body
    )


@app.api_route("/signals/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_signals(request: Request, path: str):
    """Proxy pour le service de signaux"""
    body = await request.body() if request.method in ["POST", "PUT"] else None
    return await api_gateway.proxy_request(
        "signals",
        f"/{path}",
        request.method,
        dict(request.headers),
        body
    )


@app.api_route("/positions/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_positions(request: Request, path: str):
    """Proxy pour le service de positions"""
    body = await request.body() if request.method in ["POST", "PUT"] else None
    return await api_gateway.proxy_request(
        "positions",
        f"/{path}",
        request.method,
        dict(request.headers),
        body
    )


@app.api_route("/arbitrage/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_arbitrage(request: Request, path: str):
    """Proxy pour le service d'arbitrage"""
    body = await request.body() if request.method in ["POST", "PUT"] else None
    return await api_gateway.proxy_request(
        "arbitrage",
        f"/{path}",
        request.method,
        dict(request.headers),
        body
    )


@app.api_route("/backtesting/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_backtesting(request: Request, path: str):
    """Proxy pour le service de backtesting"""
    body = await request.body() if request.method in ["POST", "PUT"] else None
    return await api_gateway.proxy_request(
        "backtesting",
        f"/{path}",
        request.method,
        dict(request.headers),
        body
    )


# Route racine
@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "message": "CryptoSpreadEdge API Gateway",
        "version": "1.0.0",
        "status": "running",
        "services": list(api_gateway.load_balancer.services.keys())
    }


if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Démarrer le gateway
    uvicorn.run(
        "api_gateway:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Un seul worker pour éviter les conflits
        log_level="info"
    )