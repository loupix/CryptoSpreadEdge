"""
Interface de base pour les connecteurs d'exchanges
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

from .market_data_types import MarketData, Order, Position, Balance


class BaseConnector(ABC):
    """
    Interface de base pour tous les connecteurs d'exchanges
    
    Définit les méthodes communes que tous les connecteurs
    doivent implémenter.
    """
    
    def __init__(self, api_key: str = "", secret_key: str = ""):
        self.api_key = api_key
        self.secret_key = secret_key
        self.connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Établit la connexion avec l'exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Ferme la connexion avec l'exchange"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché pour les symboles donnés"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """Récupère le ticker pour un symbole"""
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 100) -> Optional[MarketData]:
        """Récupère le carnet d'ordres pour un symbole"""
        pass
    
    @abstractmethod
    async def get_trades(self, symbol: str, limit: int = 100) -> List[MarketData]:
        """Récupère les dernières transactions pour un symbole"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> Optional[Order]:
        """Place un ordre sur l'exchange"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Annule un ordre"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        """Récupère le statut d'un ordre"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Récupère les positions ouvertes"""
        pass
    
    @abstractmethod
    async def get_balances(self) -> List[Balance]:
        """Récupère les soldes du compte"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        timeframe: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[MarketData]:
        """Récupère les données historiques"""
        pass
    
    def is_connected(self) -> bool:
        """Vérifie si le connecteur est connecté"""
        return self.connected
    
    def get_name(self) -> str:
        """Retourne le nom du connecteur"""
        return self.__class__.__name__