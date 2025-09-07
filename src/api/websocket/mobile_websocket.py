# WebSocket pour l'application mobile
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
import logging
from datetime import datetime

from ...core.market_data.market_data_manager import MarketDataManager
from ...arbitrage.arbitrage_engine import arbitrage_engine
from ...core.trading_engine.engine import TradingEngine

logger = logging.getLogger(__name__)

class MobileWebSocketManager:
    """Gestionnaire WebSocket pour l'application mobile"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
        self.subscriptions: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accepter une nouvelle connexion WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
            
        self.subscriptions[websocket] = {
            "channels": set(),
            "symbols": set(),
            "user_id": user_id
        }
        
        logger.info(f"WebSocket connecté. Total: {len(self.active_connections)}")
        
        # Envoyer un message de bienvenue
        await self.send_personal_message({
            "type": "connected",
            "message": "Connexion WebSocket établie",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Déconnecter un WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        # Nettoyer les souscriptions
        if websocket in self.subscriptions:
            subscription = self.subscriptions[websocket]
            user_id = subscription.get("user_id")
            
            if user_id and user_id in self.user_connections:
                if websocket in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(websocket)
                    
            del self.subscriptions[websocket]
            
        logger.info(f"WebSocket déconnecté. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Envoyer un message à une connexion spécifique"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Erreur envoi message WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Diffuser un message à toutes les connexions actives"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Erreur diffusion WebSocket: {e}")
                disconnected.append(connection)
        
        # Nettoyer les connexions défaillantes
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Envoyer un message à un utilisateur spécifique"""
        if user_id in self.user_connections:
            disconnected = []
            
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Erreur envoi message utilisateur: {e}")
                    disconnected.append(connection)
            
            # Nettoyer les connexions défaillantes
            for connection in disconnected:
                self.disconnect(connection)
    
    async def handle_subscription(self, websocket: WebSocket, data: Dict[str, Any]):
        """Gérer les souscriptions aux canaux"""
        if websocket not in self.subscriptions:
            return
            
        subscription = self.subscriptions[websocket]
        action = data.get("type")
        channel = data.get("channel")
        
        if action == "subscribe":
            if channel:
                subscription["channels"].add(channel)
                
                # Souscrire aux symboles spécifiques si fournis
                symbols = data.get("symbols", [])
                if symbols:
                    subscription["symbols"].update(symbols)
                
                await self.send_personal_message({
                    "type": "subscription_confirmed",
                    "channel": channel,
                    "symbols": list(symbols) if symbols else "all",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
        elif action == "unsubscribe":
            if channel:
                subscription["channels"].discard(channel)
                
                await self.send_personal_message({
                    "type": "unsubscription_confirmed",
                    "channel": channel,
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
    
    async def send_market_data(self, symbol: str, data: Dict[str, Any]):
        """Envoyer des données de marché aux clients abonnés"""
        message = {
            "type": "market_data",
            "data": {
                "symbol": symbol,
                "price": data.get("price"),
                "change24h": data.get("change24h"),
                "changePercent24h": data.get("changePercent24h"),
                "volume24h": data.get("volume24h"),
                "high24h": data.get("high24h"),
                "low24h": data.get("low24h"),
                "timestamp": datetime.utcnow().isoformat(),
                "platform": data.get("platform", "unknown")
            }
        }
        
        # Envoyer aux connexions abonnées aux données de marché
        for websocket, subscription in self.subscriptions.items():
            if "market_data" in subscription["channels"]:
                if not subscription["symbols"] or symbol in subscription["symbols"]:
                    await self.send_personal_message(message, websocket)
    
    async def send_order_update(self, user_id: str, order_data: Dict[str, Any]):
        """Envoyer une mise à jour d'ordre à un utilisateur"""
        message = {
            "type": "order_update",
            "data": order_data
        }
        
        await self.send_to_user(message, user_id)
    
    async def send_portfolio_update(self, user_id: str, portfolio_data: Dict[str, Any]):
        """Envoyer une mise à jour de portefeuille à un utilisateur"""
        message = {
            "type": "portfolio_update",
            "data": portfolio_data
        }
        
        await self.send_to_user(message, user_id)
    
    async def send_arbitrage_opportunity(self, opportunity_data: Dict[str, Any]):
        """Envoyer une opportunité d'arbitrage aux clients abonnés"""
        message = {
            "type": "arbitrage_opportunity",
            "data": opportunity_data
        }
        
        # Envoyer aux connexions abonnées à l'arbitrage
        for websocket, subscription in self.subscriptions.items():
            if "arbitrage" in subscription["channels"]:
                await self.send_personal_message(message, websocket)

# Instance globale du gestionnaire WebSocket
ws_manager = MobileWebSocketManager()

async def websocket_endpoint(websocket: WebSocket, user_id: str = None):
    """Endpoint WebSocket principal"""
    await ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Recevoir les messages du client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Gérer les souscriptions
            if message.get("type") in ["subscribe", "unsubscribe"]:
                await ws_manager.handle_subscription(websocket, message)
            
            # Gérer d'autres types de messages si nécessaire
            elif message.get("type") == "ping":
                await ws_manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
        ws_manager.disconnect(websocket)

# Fonctions utilitaires pour l'intégration avec les autres services
async def broadcast_market_data(symbol: str, data: Dict[str, Any]):
    """Diffuser des données de marché (à appeler depuis les autres services)"""
    await ws_manager.send_market_data(symbol, data)

async def broadcast_arbitrage_opportunity(opportunity: Dict[str, Any]):
    """Diffuser une opportunité d'arbitrage (à appeler depuis les autres services)"""
    await ws_manager.send_arbitrage_opportunity(opportunity)

async def send_user_order_update(user_id: str, order: Dict[str, Any]):
    """Envoyer une mise à jour d'ordre à un utilisateur (à appeler depuis les autres services)"""
    await ws_manager.send_order_update(user_id, order)

async def send_user_portfolio_update(user_id: str, portfolio: Dict[str, Any]):
    """Envoyer une mise à jour de portefeuille à un utilisateur (à appeler depuis les autres services)"""
    await ws_manager.send_portfolio_update(user_id, portfolio)