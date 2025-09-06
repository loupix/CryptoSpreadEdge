"""
Sources de données alternatives pour CryptoSpreadEdge
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import json

from ..connectors.common.market_data_types import MarketData, Ticker, OrderBook, Trade


class AlternativeDataSources:
    """Gestionnaire des sources de données alternatives"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sources = {
            "coinmarketcap": CoinMarketCapSource(),
            "coingecko": CoinGeckoSource(),
            "cryptocompare": CryptoCompareSource(),
            "messari": MessariSource(),
            "glassnode": GlassnodeSource(),
            "defillama": DeFiLlamaSource(),
            "dune": DuneSource(),
            "thegraph": TheGraphSource(),
            "moralis": MoralisSource(),
            "alchemy": AlchemySource()
        }
    
    async def get_market_data(self, symbols: List[str], source: str = "coinmarketcap") -> Dict[str, MarketData]:
        """Récupère les données de marché depuis une source alternative"""
        if source not in self.sources:
            self.logger.error(f"Source non supportée: {source}")
            return {}
        
        try:
            return await self.sources[source].get_market_data(symbols)
        except Exception as e:
            self.logger.error(f"Erreur récupération données {source}: {e}")
            return {}
    
    async def get_all_sources_data(self, symbols: List[str]) -> Dict[str, Dict[str, MarketData]]:
        """Récupère les données de toutes les sources"""
        results = {}
        
        tasks = []
        for source_name, source in self.sources.items():
            task = self._get_source_data_safe(source_name, source, symbols)
            tasks.append(task)
        
        if tasks:
            source_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(source_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Erreur source {list(self.sources.keys())[i]}: {result}")
                elif result:
                    source_name, data = result
                    results[source_name] = data
        
        return results
    
    async def _get_source_data_safe(self, source_name: str, source, symbols: List[str]) -> Optional[tuple]:
        """Récupère les données d'une source de manière sécurisée"""
        try:
            data = await source.get_market_data(symbols)
            return (source_name, data)
        except Exception as e:
            self.logger.error(f"Erreur source {source_name}: {e}")
            return None


class BaseDataSource:
    """Classe de base pour les sources de données"""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché"""
        raise NotImplementedError
    
    async def _make_request(self, url: str, headers: Dict = None, params: Dict = None) -> Optional[Dict]:
        """Effectue une requête HTTP"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.error(f"Erreur HTTP {response.status}: {url}")
                        return None
        except Exception as e:
            self.logger.error(f"Erreur requête {url}: {e}")
            return None


class CoinMarketCapSource(BaseDataSource):
    """Source de données CoinMarketCap"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            "X-CMC_PRO_API_KEY": api_key,
            "Accept": "application/json"
        }
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché depuis CoinMarketCap"""
        market_data = {}
        
        try:
            # Récupérer les données des cryptos
            params = {
                "symbol": ",".join(symbols),
                "convert": "USD"
            }
            
            data = await self._make_request(
                f"{self.base_url}/cryptocurrency/quotes/latest",
                headers=self.headers,
                params=params
            )
            
            if data and "data" in data:
                for symbol, crypto_data in data["data"].items():
                    quote = crypto_data["quote"]["USD"]
                    
                    ticker = Ticker(
                        symbol=symbol,
                        price=quote["price"],
                        bid=quote.get("price", 0) * 0.999,
                        ask=quote.get("price", 0) * 1.001,
                        volume=quote.get("volume_24h", 0),
                        market_cap=quote.get("market_cap", 0),
                        timestamp=datetime.utcnow(),
                        source="coinmarketcap"
                    )
                    
                    market_data[symbol] = MarketData(
                        symbol=symbol,
                        ticker=ticker,
                        timestamp=datetime.utcnow(),
                        source="coinmarketcap"
                    )
        
        except Exception as e:
            self.logger.error(f"Erreur CoinMarketCap: {e}")
        
        return market_data


class CoinGeckoSource(BaseDataSource):
    """Source de données CoinGecko"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://api.coingecko.com/api/v3"
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché depuis CoinGecko"""
        market_data = {}
        
        try:
            # Récupérer les données des cryptos
            params = {
                "ids": ",".join(symbols).lower(),
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true"
            }
            
            data = await self._make_request(
                f"{self.base_url}/simple/price",
                params=params
            )
            
            if data:
                for symbol, crypto_data in data.items():
                    usd_data = crypto_data.get("usd", {})
                    
                    ticker = Ticker(
                        symbol=symbol.upper(),
                        price=usd_data.get("usd", 0),
                        bid=usd_data.get("usd", 0) * 0.999,
                        ask=usd_data.get("usd", 0) * 1.001,
                        volume=usd_data.get("usd_24h_vol", 0),
                        market_cap=usd_data.get("usd_market_cap", 0),
                        change_24h=usd_data.get("usd_24h_change", 0),
                        timestamp=datetime.utcnow(),
                        source="coingecko"
                    )
                    
                    market_data[symbol.upper()] = MarketData(
                        symbol=symbol.upper(),
                        ticker=ticker,
                        timestamp=datetime.utcnow(),
                        source="coingecko"
                    )
        
        except Exception as e:
            self.logger.error(f"Erreur CoinGecko: {e}")
        
        return market_data


class CryptoCompareSource(BaseDataSource):
    """Source de données CryptoCompare"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://min-api.cryptocompare.com/data"
        self.headers = {
            "authorization": f"Apikey {api_key}" if api_key else None
        }
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché depuis CryptoCompare"""
        market_data = {}
        
        try:
            # Récupérer les données des cryptos
            params = {
                "fsyms": ",".join(symbols),
                "tsyms": "USD"
            }
            
            data = await self._make_request(
                f"{self.base_url}/pricemultifull",
                headers=self.headers,
                params=params
            )
            
            if data and "RAW" in data:
                for symbol, crypto_data in data["RAW"].items():
                    usd_data = crypto_data.get("USD", {})
                    
                    ticker = Ticker(
                        symbol=symbol,
                        price=usd_data.get("PRICE", 0),
                        bid=usd_data.get("BID", 0),
                        ask=usd_data.get("ASK", 0),
                        volume=usd_data.get("VOLUME24HOUR", 0),
                        market_cap=usd_data.get("MKTCAP", 0),
                        change_24h=usd_data.get("CHANGEPCT24HOUR", 0),
                        timestamp=datetime.utcnow(),
                        source="cryptocompare"
                    )
                    
                    market_data[symbol] = MarketData(
                        symbol=symbol,
                        ticker=ticker,
                        timestamp=datetime.utcnow(),
                        source="cryptocompare"
                    )
        
        except Exception as e:
            self.logger.error(f"Erreur CryptoCompare: {e}")
        
        return market_data


class MessariSource(BaseDataSource):
    """Source de données Messari"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://data.messari.io/api/v1"
        self.headers = {
            "x-messari-api-key": api_key
        }
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché depuis Messari"""
        market_data = {}
        
        try:
            # Récupérer les données des cryptos
            params = {
                "fields": "id,symbol,metrics/market_data/price_usd,metrics/market_data/volume_last_24_hours,metrics/market_data/market_cap_last_24_hours"
            }
            
            data = await self._make_request(
                f"{self.base_url}/assets",
                headers=self.headers,
                params=params
            )
            
            if data and "data" in data:
                for crypto_data in data["data"]:
                    symbol = crypto_data.get("symbol", "").upper()
                    if symbol in symbols:
                        metrics = crypto_data.get("metrics", {}).get("market_data", {})
                        
                        ticker = Ticker(
                            symbol=symbol,
                            price=metrics.get("price_usd", 0),
                            bid=metrics.get("price_usd", 0) * 0.999,
                            ask=metrics.get("price_usd", 0) * 1.001,
                            volume=metrics.get("volume_last_24_hours", 0),
                            market_cap=metrics.get("market_cap_last_24_hours", 0),
                            timestamp=datetime.utcnow(),
                            source="messari"
                        )
                        
                        market_data[symbol] = MarketData(
                            symbol=symbol,
                            ticker=ticker,
                            timestamp=datetime.utcnow(),
                            source="messari"
                        )
        
        except Exception as e:
            self.logger.error(f"Erreur Messari: {e}")
        
        return market_data


class GlassnodeSource(BaseDataSource):
    """Source de données Glassnode (on-chain)"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://api.glassnode.com/v1"
        self.headers = {
            "X-API-KEY": api_key
        }
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données on-chain depuis Glassnode"""
        market_data = {}
        
        try:
            # Récupérer les données on-chain pour Bitcoin
            if "BTC" in symbols:
                btc_data = await self._get_btc_onchain_data()
                if btc_data:
                    market_data["BTC"] = btc_data
        
        except Exception as e:
            self.logger.error(f"Erreur Glassnode: {e}")
        
        return market_data
    
    async def _get_btc_onchain_data(self) -> Optional[MarketData]:
        """Récupère les données on-chain Bitcoin"""
        try:
            # Récupérer plusieurs métriques on-chain
            metrics = [
                "market/price_usd_close",
                "market/marketcap_usd",
                "market/volume_usd",
                "network/active_addresses",
                "network/transaction_count",
                "mining/hash_rate_mean"
            ]
            
            all_data = {}
            for metric in metrics:
                params = {
                    "a": "BTC",
                    "f": "JSON",
                    "timestamp_format": "unix"
                }
                
                data = await self._make_request(
                    f"{self.base_url}/metrics/{metric}",
                    headers=self.headers,
                    params=params
                )
                
                if data:
                    all_data[metric] = data
            
            if all_data:
                # Créer un ticker avec les données on-chain
                price_data = all_data.get("market/price_usd_close", [])
                if price_data:
                    latest_price = price_data[-1].get("v", 0)
                    
                    ticker = Ticker(
                        symbol="BTC",
                        price=latest_price,
                        bid=latest_price * 0.999,
                        ask=latest_price * 1.001,
                        volume=all_data.get("market/volume_usd", [{}])[-1].get("v", 0),
                        market_cap=all_data.get("market/marketcap_usd", [{}])[-1].get("v", 0),
                        timestamp=datetime.utcnow(),
                        source="glassnode"
                    )
                    
                    return MarketData(
                        symbol="BTC",
                        ticker=ticker,
                        timestamp=datetime.utcnow(),
                        source="glassnode"
                    )
        
        except Exception as e:
            self.logger.error(f"Erreur données on-chain BTC: {e}")
        
        return None


class DeFiLlamaSource(BaseDataSource):
    """Source de données DeFiLlama (DeFi)"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://api.llama.fi"
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données DeFi depuis DeFiLlama"""
        market_data = {}
        
        try:
            # Récupérer les données des protocoles DeFi
            data = await self._make_request(f"{self.base_url}/protocols")
            
            if data:
                for protocol in data:
                    symbol = protocol.get("symbol", "").upper()
                    if symbol in symbols:
                        ticker = Ticker(
                            symbol=symbol,
                            price=protocol.get("tvl", 0),
                            bid=protocol.get("tvl", 0) * 0.999,
                            ask=protocol.get("tvl", 0) * 1.001,
                            volume=protocol.get("volume24h", 0),
                            market_cap=protocol.get("tvl", 0),
                            timestamp=datetime.utcnow(),
                            source="defillama"
                        )
                        
                        market_data[symbol] = MarketData(
                            symbol=symbol,
                            ticker=ticker,
                            timestamp=datetime.utcnow(),
                            source="defillama"
                        )
        
        except Exception as e:
            self.logger.error(f"Erreur DeFiLlama: {e}")
        
        return market_data


class DuneSource(BaseDataSource):
    """Source de données Dune Analytics"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://api.dune.com/api/v1"
        self.headers = {
            "x-dune-api-key": api_key
        }
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données depuis Dune Analytics"""
        # Dune Analytics nécessite des requêtes spécifiques
        # Cette implémentation est un exemple
        return {}


class TheGraphSource(BaseDataSource):
    """Source de données The Graph (blockchain)"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://api.thegraph.com/subgraphs/name"
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données depuis The Graph"""
        # The Graph nécessite des requêtes GraphQL spécifiques
        # Cette implémentation est un exemple
        return {}


class MoralisSource(BaseDataSource):
    """Source de données Moralis (Web3)"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://deep-index.moralis.io/api/v2"
        self.headers = {
            "X-API-Key": api_key
        }
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données Web3 depuis Moralis"""
        # Moralis nécessite des requêtes spécifiques
        # Cette implémentation est un exemple
        return {}


class AlchemySource(BaseDataSource):
    """Source de données Alchemy (blockchain)"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(api_key)
        self.base_url = "https://eth-mainnet.g.alchemy.com/v2"
        self.api_key = api_key
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données blockchain depuis Alchemy"""
        # Alchemy nécessite des requêtes spécifiques
        # Cette implémentation est un exemple
        return {}


# Instance globale des sources de données alternatives
alternative_sources = AlternativeDataSources()