# API REST pour l'application mobile
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import jwt
import hashlib
import secrets

from ...core.security.auth_manager import AuthManager
from ...core.market_data.market_data_manager import MarketDataManager
from ...core.trading_engine.engine import TradingEngine
from ...arbitrage.arbitrage_engine import arbitrage_engine
from ...ai.feature_engineering.indicators import compute_indicator_bundle

router = APIRouter(prefix="/mobile", tags=["mobile"])

# Modèles Pydantic pour les requêtes/réponses
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class LoginResponse(BaseModel):
    user: Dict[str, Any]
    token: str
    refreshToken: str
    expiresIn: int

class MarketDataRequest(BaseModel):
    symbols: List[str]
    timeframe: Optional[str] = "1m"
    limit: Optional[int] = 100
    includeIndicators: Optional[bool] = False

class TradingRequest(BaseModel):
    symbol: str
    side: str  # 'buy' or 'sell'
    type: str  # 'market' or 'limit'
    quantity: float
    price: Optional[float] = None
    platform: str

class AlertRequest(BaseModel):
    symbol: str
    condition: str  # 'above', 'below', 'change'
    value: float
    isActive: bool = True

class UserPreferences(BaseModel):
    theme: Optional[str] = "light"
    currency: Optional[str] = "USD"
    language: Optional[str] = "fr"
    notifications: Optional[Dict[str, bool]] = None

# Gestionnaire d'authentification
auth_manager = AuthManager()

def get_current_user(token: str = Depends(auth_manager.get_token)):
    """Dépendance pour récupérer l'utilisateur actuel"""
    return auth_manager.get_user_from_token(token)

# Endpoints d'authentification
@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Connexion utilisateur"""
    try:
        user = await auth_manager.authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(status_code=401, detail="Identifiants incorrects")
        
        # Générer les tokens
        access_token = auth_manager.create_access_token(user["id"])
        refresh_token = auth_manager.create_refresh_token(user["id"])
        
        return LoginResponse(
            user=user,
            token=access_token,
            refreshToken=refresh_token,
            expiresIn=3600  # 1 heure
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """Inscription utilisateur"""
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = await auth_manager.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        
        # Créer le nouvel utilisateur
        user = await auth_manager.create_user(
            email=request.email,
            password=request.password,
            username=request.username
        )
        
        # Générer les tokens
        access_token = auth_manager.create_access_token(user["id"])
        refresh_token = auth_manager.create_refresh_token(user["id"])
        
        return LoginResponse(
            user=user,
            token=access_token,
            refreshToken=refresh_token,
            expiresIn=3600
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Déconnexion utilisateur"""
    # Ici on pourrait invalider le token côté serveur
    return {"message": "Déconnexion réussie"}

@router.post("/auth/refresh", response_model=LoginResponse)
async def refresh_token(refresh_token: str):
    """Rafraîchir le token d'accès"""
    try:
        user_id = auth_manager.verify_refresh_token(refresh_token)
        user = await auth_manager.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Générer un nouveau token d'accès
        access_token = auth_manager.create_access_token(user_id)
        
        return LoginResponse(
            user=user,
            token=access_token,
            refreshToken=refresh_token,
            expiresIn=3600
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token invalide")

@router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Récupérer les informations de l'utilisateur actuel"""
    return current_user

# Endpoints de données de marché
@router.get("/market/data")
async def get_market_data(
    symbols: str = Query(..., description="Symboles séparés par des virgules"),
    timeframe: str = Query("1m", description="Période de temps"),
    limit: int = Query(100, description="Nombre de points de données"),
    includeIndicators: bool = Query(False, description="Inclure les indicateurs"),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les données de marché"""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        
        # Récupérer les données de marché
        market_data = []
        for symbol in symbol_list:
            # Simuler des données de marché (à remplacer par la vraie logique)
            data = {
                "symbol": symbol,
                "price": 50000.0 + (hash(symbol) % 10000),  # Prix simulé
                "change24h": (hash(symbol) % 2000) - 1000,  # Changement simulé
                "changePercent24h": ((hash(symbol) % 20) - 10) / 100,
                "volume24h": (hash(symbol) % 1000000) + 100000,
                "high24h": 51000.0 + (hash(symbol) % 1000),
                "low24h": 49000.0 + (hash(symbol) % 1000),
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "binance"
            }
            market_data.append(data)
        
        return market_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/pairs")
async def get_trading_pairs(current_user: dict = Depends(get_current_user)):
    """Récupérer les paires de trading disponibles"""
    return [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT",
        "XRP/USDT", "DOT/USDT", "LINK/USDT", "LTC/USDT", "BCH/USDT"
    ]

# Endpoints de trading
@router.post("/trading/orders")
async def place_order(
    request: TradingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Placer un ordre de trading"""
    try:
        # Simuler la création d'un ordre
        order = {
            "id": secrets.token_hex(16),
            "symbol": request.symbol,
            "side": request.side,
            "type": request.type,
            "quantity": request.quantity,
            "price": request.price,
            "status": "pending",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": request.platform,
            "userId": current_user["id"]
        }
        
        # Ici on pourrait intégrer avec le vrai moteur de trading
        # trading_engine.place_order(order)
        
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trading/orders")
async def get_orders(
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les ordres de l'utilisateur"""
    try:
        # Simuler des ordres (à remplacer par la vraie logique)
        orders = [
            {
                "id": "order1",
                "symbol": "BTC/USDT",
                "side": "buy",
                "type": "market",
                "quantity": 0.001,
                "price": None,
                "status": "filled",
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "binance"
            }
        ]
        
        if symbol:
            orders = [o for o in orders if o["symbol"] == symbol]
        
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/trading/orders/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Annuler un ordre"""
    try:
        # Ici on pourrait intégrer avec le vrai moteur de trading
        # trading_engine.cancel_order(order_id, current_user["id"])
        
        return {"message": "Ordre annulé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de portefeuille
@router.get("/portfolio")
async def get_portfolio(current_user: dict = Depends(get_current_user)):
    """Récupérer le portefeuille de l'utilisateur"""
    try:
        # Simuler un portefeuille (à remplacer par la vraie logique)
        portfolio = {
            "totalValue": 10000.0,
            "totalValueChange": 250.0,
            "totalValueChangePercent": 2.5,
            "positions": [],
            "cash": 5000.0,
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/positions")
async def get_positions(current_user: dict = Depends(get_current_user)):
    """Récupérer les positions de l'utilisateur"""
    try:
        # Simuler des positions (à remplacer par la vraie logique)
        positions = [
            {
                "symbol": "BTC/USDT",
                "quantity": 0.1,
                "averagePrice": 45000.0,
                "currentPrice": 50000.0,
                "value": 5000.0,
                "pnl": 500.0,
                "pnlPercent": 11.11,
                "platform": "binance"
            }
        ]
        
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints d'arbitrage
@router.get("/arbitrage/opportunities")
async def get_arbitrage_opportunities(current_user: dict = Depends(get_current_user)):
    """Récupérer les opportunités d'arbitrage"""
    try:
        # Récupérer les opportunités depuis le moteur d'arbitrage
        opportunities = arbitrage_engine.get_opportunities()
        
        # Formater pour l'API mobile
        formatted_opportunities = []
        for opp in opportunities:
            formatted_opp = {
                "id": opp.get("id", secrets.token_hex(8)),
                "symbol": opp.get("symbol", "BTC/USDT"),
                "buyPlatform": opp.get("buy_platform", "binance"),
                "sellPlatform": opp.get("sell_platform", "okx"),
                "buyPrice": opp.get("buy_price", 50000.0),
                "sellPrice": opp.get("sell_price", 50100.0),
                "spread": opp.get("spread", 100.0),
                "spreadPercent": opp.get("spread_percent", 0.2),
                "profit": opp.get("profit", 50.0),
                "confidence": opp.get("confidence", 0.8),
                "timestamp": datetime.utcnow().isoformat(),
                "isActive": True
            }
            formatted_opportunities.append(formatted_opp)
        
        return formatted_opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/arbitrage/history")
async def get_arbitrage_history(current_user: dict = Depends(get_current_user)):
    """Récupérer l'historique des arbitrages"""
    try:
        # Simuler l'historique (à remplacer par la vraie logique)
        history = []
        
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints d'alertes
@router.post("/alerts")
async def create_alert(
    request: AlertRequest,
    current_user: dict = Depends(get_current_user)
):
    """Créer une alerte"""
    try:
        alert = {
            "id": secrets.token_hex(8),
            "userId": current_user["id"],
            "symbol": request.symbol,
            "condition": request.condition,
            "value": request.value,
            "isActive": request.isActive,
            "createdAt": datetime.utcnow().isoformat()
        }
        
        # Ici on pourrait sauvegarder l'alerte en base de données
        
        return alert
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    """Récupérer les alertes de l'utilisateur"""
    try:
        # Simuler des alertes (à remplacer par la vraie logique)
        alerts = []
        
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/alerts/{alert_id}")
async def update_alert(
    alert_id: str,
    request: AlertRequest,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une alerte"""
    try:
        # Ici on pourrait mettre à jour l'alerte en base de données
        
        return {"message": "Alerte mise à jour avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprimer une alerte"""
    try:
        # Ici on pourrait supprimer l'alerte de la base de données
        
        return {"message": "Alerte supprimée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de configuration
@router.put("/user/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour les préférences utilisateur"""
    try:
        # Ici on pourrait sauvegarder les préférences en base de données
        
        updated_user = current_user.copy()
        updated_user["preferences"] = preferences.dict()
        
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint de santé
@router.get("/health")
async def health_check():
    """Vérifier la santé de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }