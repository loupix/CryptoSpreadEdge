"""
Factory pour créer et gérer tous les connecteurs d'exchanges
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Any
from abc import ABC, abstractmethod

from .common.base_connector import BaseConnector
from .supported_exchanges import ALL_EXCHANGES, get_arbitrage_candidates, get_market_data_sources
from .common.market_data_types import MarketData, Order, Position, Balance
from utils.common.decorators import retry, timeout


class ConnectorFactory:
    """Factory pour créer et gérer les connecteurs d'exchanges"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._connectors: Dict[str, BaseConnector] = {}
        self._connector_classes: Dict[str, Type[BaseConnector]] = {}
        self._register_connectors()
    
    def _register_connectors(self):
        """Enregistre tous les connecteurs disponibles"""
        # Tier 1 Exchanges
        self._register_connector("binance", "BinanceConnector")
        self._register_connector("coinbase", "CoinbaseConnector")
        self._register_connector("kraken", "KrakenConnector")
        self._register_connector("okx", "OKXConnector")
        
        # Tier 2 Exchanges
        self._register_connector("bybit", "BybitConnector")
        self._register_connector("bitget", "BitgetConnector")
        self._register_connector("gateio", "GateIOConnector")
        self._register_connector("huobi", "HuobiConnector")
        self._register_connector("kucoin", "KuCoinConnector")
        
        # Tier 3 Exchanges
        self._register_connector("bitfinex", "BitfinexConnector")
        self._register_connector("bitstamp", "BitstampConnector")
        self._register_connector("gemini", "GeminiConnector")
        self._register_connector("bittrex", "BittrexConnector")
        
        # Emerging Exchanges
        self._register_connector("mexc", "MEXCConnector")
        self._register_connector("whitebit", "WhiteBITConnector")
        self._register_connector("phemex", "PhemexConnector")
        
        # DEX
        self._register_connector("uniswap", "UniswapConnector")
        self._register_connector("pancakeswap", "PancakeSwapConnector")
        self._register_connector("sushiswap", "SushiSwapConnector")
    
    def _register_connector(self, exchange_id: str, class_name: str):
        """Enregistre un connecteur"""
        self._connector_classes[exchange_id] = class_name
    
    async def create_connector(
        self, 
        exchange_id: str, 
        api_key: str = "", 
        secret_key: str = "",
        **kwargs
    ) -> Optional[BaseConnector]:
        """Crée un connecteur pour l'exchange spécifié"""
        try:
            if exchange_id not in self._connector_classes:
                self.logger.error(f"Connecteur non supporté: {exchange_id}")
                return None
            
            # Import dynamique du connecteur
            connector_class = await self._import_connector_class(exchange_id)
            if not connector_class:
                return None
            
            # Créer l'instance du connecteur
            connector = connector_class(api_key=api_key, secret_key=secret_key, **kwargs)

            # Appliquer des wrappers de résilience sur méthodes I/O critiques si absentes
            for attr in ["get_ticker", "get_order_book", "get_trades", "place_order", "get_market_data"]:
                if hasattr(connector, attr):
                    fn = getattr(connector, attr)
                    if callable(fn):
                        wrapped = retry((Exception,), attempts=3, delay_seconds=0.2, backoff=2.0)(
                            timeout(5.0)(fn)
                        )
                        setattr(connector, attr, wrapped)
            
            # Stocker le connecteur
            self._connectors[exchange_id] = connector
            
            self.logger.info(f"Connecteur {exchange_id} créé avec succès")
            return connector
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la création du connecteur {exchange_id}: {e}")
            return None
    
    async def _import_connector_class(self, exchange_id: str) -> Optional[Type[BaseConnector]]:
        """Importe dynamiquement la classe du connecteur"""
        try:
            if exchange_id == "binance":
                from .binance.binance_connector import BinanceConnector
                return BinanceConnector
            elif exchange_id == "coinbase":
                from .coinbase.coinbase_connector import CoinbaseConnector
                return CoinbaseConnector
            elif exchange_id == "kraken":
                from .kraken.kraken_connector import KrakenConnector
                return KrakenConnector
            elif exchange_id == "okx":
                from .okx.okx_connector import OKXConnector
                return OKXConnector
            elif exchange_id == "bybit":
                from .bybit.bybit_connector import BybitConnector
                return BybitConnector
            elif exchange_id == "bitget":
                from .bitget.bitget_connector import BitgetConnector
                return BitgetConnector
            elif exchange_id == "gateio":
                from .gateio.gateio_connector import GateIOConnector
                return GateIOConnector
            elif exchange_id == "huobi":
                from .huobi.huobi_connector import HuobiConnector
                return HuobiConnector
            elif exchange_id == "kucoin":
                from .kucoin.kucoin_connector import KuCoinConnector
                return KuCoinConnector
            elif exchange_id == "bitfinex":
                from .bitfinex.bitfinex_connector import BitfinexConnector
                return BitfinexConnector
            elif exchange_id == "bitstamp":
                from .bitstamp.bitstamp_connector import BitstampConnector
                return BitstampConnector
            elif exchange_id == "gemini":
                from .gemini.gemini_connector import GeminiConnector
                return GeminiConnector
            elif exchange_id == "bittrex":
                from .bittrex.bittrex_connector import BittrexConnector
                return BittrexConnector
            elif exchange_id == "mexc":
                from .mexc.mexc_connector import MEXCConnector
                return MEXCConnector
            elif exchange_id == "whitebit":
                from .whitebit.whitebit_connector import WhiteBITConnector
                return WhiteBITConnector
            elif exchange_id == "phemex":
                from .phemex.phemex_connector import PhemexConnector
                return PhemexConnector
            elif exchange_id == "uniswap":
                from .dex.uniswap_connector import UniswapConnector
                return UniswapConnector
            elif exchange_id == "pancakeswap":
                from .dex.pancakeswap_connector import PancakeSwapConnector
                return PancakeSwapConnector
            elif exchange_id == "sushiswap":
                from .dex.sushiswap_connector import SushiSwapConnector
                return SushiSwapConnector
            else:
                self.logger.error(f"Connecteur non implémenté: {exchange_id}")
                return None
                
        except ImportError as e:
            self.logger.error(f"Impossible d'importer le connecteur {exchange_id}: {e}")
            return None
    
    async def create_multiple_connectors(
        self, 
        exchange_ids: List[str], 
        credentials: Dict[str, Dict[str, str]] = None
    ) -> Dict[str, BaseConnector]:
        """Crée plusieurs connecteurs en parallèle"""
        tasks = []
        
        for exchange_id in exchange_ids:
            creds = credentials.get(exchange_id, {}) if credentials else {}
            task = self.create_connector(
                exchange_id=exchange_id,
                api_key=creds.get("api_key", ""),
                secret_key=creds.get("secret_key", ""),
                **creds.get("extra", {})
            )
            tasks.append((exchange_id, task))
        
        # Exécuter en parallèle
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        connectors = {}
        for i, (exchange_id, result) in enumerate(zip([ex_id for ex_id, _ in tasks], results)):
            if isinstance(result, Exception):
                self.logger.error(f"Erreur lors de la création du connecteur {exchange_id}: {result}")
            elif result:
                connectors[exchange_id] = result
        
        return connectors
    
    async def create_arbitrage_connectors(
        self, 
        credentials: Dict[str, Dict[str, str]] = None
    ) -> Dict[str, BaseConnector]:
        """Crée les connecteurs recommandés pour l'arbitrage"""
        arbitrage_exchanges = get_arbitrage_candidates()
        return await self.create_multiple_connectors(arbitrage_exchanges, credentials)
    
    async def create_market_data_connectors(
        self, 
        credentials: Dict[str, Dict[str, str]] = None
    ) -> Dict[str, BaseConnector]:
        """Crée les connecteurs pour les données de marché"""
        data_exchanges = get_market_data_sources()
        return await self.create_multiple_connectors(data_exchanges, credentials)
    
    def get_connector(self, exchange_id: str) -> Optional[BaseConnector]:
        """Récupère un connecteur existant"""
        return self._connectors.get(exchange_id)
    
    def get_all_connectors(self) -> Dict[str, BaseConnector]:
        """Récupère tous les connecteurs créés"""
        return self._connectors.copy()
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connecte tous les connecteurs"""
        results = {}
        
        for exchange_id, connector in self._connectors.items():
            try:
                success = await connector.connect()
                results[exchange_id] = success
                if success:
                    self.logger.info(f"Connecté à {exchange_id}")
                else:
                    self.logger.warning(f"Échec de connexion à {exchange_id}")
            except Exception as e:
                self.logger.error(f"Erreur de connexion à {exchange_id}: {e}")
                results[exchange_id] = False
        
        return results
    
    async def disconnect_all(self):
        """Déconnecte tous les connecteurs"""
        for exchange_id, connector in self._connectors.items():
            try:
                await connector.disconnect()
                self.logger.info(f"Déconnecté de {exchange_id}")
            except Exception as e:
                self.logger.error(f"Erreur de déconnexion de {exchange_id}: {e}")
    
    async def get_market_data_from_all(
        self, 
        symbols: List[str]
    ) -> Dict[str, Dict[str, MarketData]]:
        """Récupère les données de marché de tous les connecteurs"""
        results = {}
        
        tasks = []
        for exchange_id, connector in self._connectors.items():
            if connector.is_connected():
                task = self._get_market_data_safe(connector, symbols, exchange_id)
                tasks.append(task)
        
        if tasks:
            market_data_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(market_data_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Erreur lors de la récupération des données: {result}")
                elif result:
                    exchange_id, data = result
                    results[exchange_id] = data
        
        return results
    
    async def _get_market_data_safe(
        self, 
        connector: BaseConnector, 
        symbols: List[str], 
        exchange_id: str
    ) -> Optional[tuple]:
        """Récupère les données de marché de manière sécurisée"""
        try:
            data = await connector.get_market_data(symbols)
            return (exchange_id, data)
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des données de {exchange_id}: {e}")
            return None
    
    async def place_orders_on_exchanges(
        self, 
        orders: Dict[str, Order]
    ) -> Dict[str, Dict[str, Any]]:
        """Place des ordres sur plusieurs exchanges"""
        results = {}
        
        for exchange_id, order in orders.items():
            connector = self.get_connector(exchange_id)
            if connector and connector.is_connected():
                try:
                    result = await connector.place_order(order)
                    results[exchange_id] = {
                        "success": result is not None,
                        "order": result,
                        "error": None
                    }
                except Exception as e:
                    results[exchange_id] = {
                        "success": False,
                        "order": None,
                        "error": str(e)
                    }
            else:
                results[exchange_id] = {
                    "success": False,
                    "order": None,
                    "error": f"Connecteur {exchange_id} non disponible"
                }
        
        return results
    
    def get_connector_status(self) -> Dict[str, Dict[str, Any]]:
        """Retourne le statut de tous les connecteurs"""
        status = {}
        
        for exchange_id, connector in self._connectors.items():
            status[exchange_id] = {
                "connected": connector.is_connected(),
                "name": connector.get_name(),
                "exchange_info": ALL_EXCHANGES.get(exchange_id)
            }
        
        return status
    
    def get_available_exchanges(self) -> List[str]:
        """Retourne la liste des exchanges disponibles"""
        return list(self._connector_classes.keys())
    
    def get_connected_exchanges(self) -> List[str]:
        """Retourne la liste des exchanges connectés"""
        return [
            exchange_id for exchange_id, connector in self._connectors.items()
            if connector.is_connected()
        ]
    
    def get_exchange_info(self, exchange_id: str) -> Optional[Dict[str, Any]]:
        """Retourne les informations d'un exchange"""
        return ALL_EXCHANGES.get(exchange_id)
    
    def get_exchanges_by_feature(self, feature: str) -> List[str]:
        """Retourne les exchanges ayant une fonctionnalité spécifique"""
        feature_map = {
            "websocket": lambda ex: ex.has_websocket,
            "futures": lambda ex: ex.has_futures,
            "margin": lambda ex: ex.has_margin,
            "staking": lambda ex: ex.has_staking,
            "fiat": lambda ex: len(ex.fiat_support) > 0
        }
        
        if feature not in feature_map:
            return []
        
        return [
            exchange_id for exchange_id, exchange_info in ALL_EXCHANGES.items()
            if feature_map[feature](exchange_info)
        ]
    
    def get_best_exchanges_for_arbitrage(self, limit: int = 5) -> List[str]:
        """Retourne les meilleurs exchanges pour l'arbitrage"""
        # Critères : volume élevé, frais bas, fiabilité
        candidates = []
        
        for exchange_id in get_arbitrage_candidates():
            if exchange_id in ALL_EXCHANGES:
                exchange_info = ALL_EXCHANGES[exchange_id]
                score = (
                    exchange_info.trust_score * 0.4 +
                    (1 / exchange_info.fees["taker"]) * 0.3 +
                    min(exchange_info.volume_24h_usd / 1000000000, 10) * 0.3
                )
                candidates.append((exchange_id, score))
        
        # Trier par score et retourner les meilleurs
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [exchange_id for exchange_id, _ in candidates[:limit]]
    
    def cleanup(self):
        """Nettoie les ressources"""
        self._connectors.clear()
        self._connector_classes.clear()


# Instance globale de la factory
connector_factory = ConnectorFactory()