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
            "alchemy": AlchemySource(),
            # Nouvelles sources publiques par exchange (lecture seule)
            "binance_public": BinancePublicSource(),
            "okx_public": OKXPublicSource(),
            "bybit_public": BybitPublicSource(),
            "kucoin_public": KuCoinPublicSource(),
            "kraken_public": KrakenPublicSource(),
            "bitfinex_public": BitfinexPublicSource(),
            "bitstamp_public": BitstampPublicSource(),
            "gateio_public": GateIOPublicSource(),
            "huobi_public": HuobiPublicSource(),
            "mexc_public": MEXCPublicSource()
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


class _PublicExchangeHelpers:
    """Fonctions utilitaires pour les sources publiques d'exchanges"""
    @staticmethod
    def default_usdt_pair(symbol: str) -> str:
        return f"{symbol.upper()}USDT"

    @staticmethod
    def dash_usdt_pair(symbol: str) -> str:
        return f"{symbol.upper()}-USDT"

    @staticmethod
    def underscore_usdt_pair(symbol: str) -> str:
        return f"{symbol.upper()}_USDT"

    @staticmethod
    def usd_pair(symbol: str) -> str:
        return f"{symbol.upper()}USD"


class BinancePublicSource(BaseDataSource):
    """Ticker public depuis l'API Binance (spot)"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://api.binance.com"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                pair = _PublicExchangeHelpers.default_usdt_pair(symbol)
                data = await self._make_request(f"{self.base_url}/api/v3/ticker/24hr", params={"symbol": pair})
                if not data or "lastPrice" not in data:
                    continue
                price = float(data.get("lastPrice", 0) or 0)
                bid = float(data.get("bidPrice", 0) or 0)
                ask = float(data.get("askPrice", 0) or 0)
                volume = float(data.get("volume", 0) or 0)
                ticker = Ticker(
                    symbol=symbol.upper(),
                    price=price,
                    bid=bid,
                    ask=ask,
                    volume=volume,
                    timestamp=datetime.utcnow(),
                    source="binance_public"
                )
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="binance_public")
        except Exception as e:
            self.logger.debug(f"Erreur BinancePublic: {e}")
        return market_data


class OKXPublicSource(BaseDataSource):
    """Ticker public depuis l'API OKX (spot)"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://www.okx.com"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                inst_id = _PublicExchangeHelpers.dash_usdt_pair(symbol)
                data = await self._make_request(f"{self.base_url}/api/v5/market/ticker", params={"instId": inst_id})
                if not data or "data" not in data or not data["data"]:
                    continue
                row = data["data"][0]
                price = float(row.get("last", 0) or 0)
                bid = float(row.get("bidPx", 0) or 0)
                ask = float(row.get("askPx", 0) or 0)
                volume = float(row.get("vol24h", 0) or 0)
                ticker = Ticker(symbol=symbol.upper(), price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="okx_public")
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="okx_public")
        except Exception as e:
            self.logger.debug(f"Erreur OKXPublic: {e}")
        return market_data


class BybitPublicSource(BaseDataSource):
    """Ticker public depuis Bybit (Unified)"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://api.bybit.com"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                inst_id = _PublicExchangeHelpers.default_usdt_pair(symbol)
                data = await self._make_request(f"{self.base_url}/v5/market/tickers", params={"category": "linear", "symbol": inst_id})
                if not data or data.get("retCode") not in (0, "0"):
                    continue
                rows = data.get("result", {}).get("list", [])
                if not rows:
                    continue
                row = rows[0]
                price = float(row.get("lastPrice", 0) or 0)
                bid = float(row.get("bid1Price", 0) or 0)
                ask = float(row.get("ask1Price", 0) or 0)
                volume = float(row.get("turnover24h", 0) or 0)
                ticker = Ticker(symbol=symbol.upper(), price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="bybit_public")
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="bybit_public")
        except Exception as e:
            self.logger.debug(f"Erreur BybitPublic: {e}")
        return market_data


class KuCoinPublicSource(BaseDataSource):
    """Ticker public depuis KuCoin"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://api.kucoin.com"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                pair = _PublicExchangeHelpers.dash_usdt_pair(symbol)
                data = await self._make_request(f"{self.base_url}/api/v1/market/stats", params={"symbol": pair})
                if not data or data.get("code") != "200000":
                    continue
                row = data.get("data", {})
                price = float(row.get("last", 0) or 0)
                bid = float(row.get("buy", 0) or 0)
                ask = float(row.get("sell", 0) or 0)
                volume = float(row.get("vol", 0) or 0)
                ticker = Ticker(symbol=symbol.upper(), price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="kucoin_public")
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="kucoin_public")
        except Exception as e:
            self.logger.debug(f"Erreur KuCoinPublic: {e}")
        return market_data


class KrakenPublicSource(BaseDataSource):
    """Ticker public depuis Kraken"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://api.kraken.com"

    @staticmethod
    def _kraken_pair(symbol: str) -> str:
        base = symbol.upper()
        # Kraken a des noms particuliers, mais pour BTC/ETH les paires XBTUSD, ETHUSD
        if base == "BTC":
            return "XBTUSD"
        return f"{base}USD"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            pairs = ",".join([self._kraken_pair(s) for s in symbols])
            data = await self._make_request(f"{self.base_url}/0/public/Ticker", params={"pair": pairs})
            if not data or "result" not in data:
                return market_data
            result = data["result"]
            rev = {self._kraken_pair(s): s.upper() for s in symbols}
            for pair, row in result.items():
                sym = rev.get(pair)
                if not sym:
                    continue
                price = float((row.get("c", [0])[0]) or 0)
                bid = float((row.get("b", [0])[0]) or 0)
                ask = float((row.get("a", [0])[0]) or 0)
                volume = float((row.get("v", [0])[1]) or 0)
                ticker = Ticker(symbol=sym, price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="kraken_public")
                market_data[sym] = MarketData(symbol=sym, ticker=ticker, timestamp=datetime.utcnow(), source="kraken_public")
        except Exception as e:
            self.logger.debug(f"Erreur KrakenPublic: {e}")
        return market_data


class BitfinexPublicSource(BaseDataSource):
    """Ticker public depuis Bitfinex"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://api-pub.bitfinex.com"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                pair = _PublicExchangeHelpers.usd_pair(symbol)
                data = await self._make_request(f"{self.base_url}/v2/ticker/t{pair}")
                if not data or not isinstance(data, list) or len(data) < 10:
                    continue
                bid = float(data[0] or 0)
                ask = float(data[2] or 0)
                price = float((bid + ask) / 2 if (bid and ask) else data[6] or 0)
                volume = float(data[7] or 0)
                ticker = Ticker(symbol=symbol.upper(), price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="bitfinex_public")
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="bitfinex_public")
        except Exception as e:
            self.logger.debug(f"Erreur BitfinexPublic: {e}")
        return market_data


class BitstampPublicSource(BaseDataSource):
    """Ticker public depuis Bitstamp"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://www.bitstamp.net/api/v2"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                pair = _PublicExchangeHelpers.usd_pair(symbol).lower()
                data = await self._make_request(f"{self.base_url}/ticker/{pair}")
                if not data or "last" not in data:
                    continue
                price = float(data.get("last", 0) or 0)
                bid = float(data.get("bid", 0) or 0)
                ask = float(data.get("ask", 0) or 0)
                volume = float(data.get("volume", 0) or 0)
                ticker = Ticker(symbol=symbol.upper(), price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="bitstamp_public")
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="bitstamp_public")
        except Exception as e:
            self.logger.debug(f"Erreur BitstampPublic: {e}")
        return market_data


class GateIOPublicSource(BaseDataSource):
    """Ticker public depuis Gate.io"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://api.gateio.ws/api/v4"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                pair = _PublicExchangeHelpers.usd_pair(symbol)
                # Gate utilise USDT en spot avec '_' comme séparateur
                spot_pair = _PublicExchangeHelpers.underscore_usdt_pair(symbol)
                data = await self._make_request(f"{self.base_url}/spot/tickers", params={"currency_pair": spot_pair})
                if not data or not isinstance(data, list) or not data:
                    continue
                row = data[0]
                price = float(row.get("last", 0) or 0)
                bid = float(row.get("highest_bid", 0) or 0)
                ask = float(row.get("lowest_ask", 0) or 0)
                volume = float(row.get("base_volume", 0) or 0)
                ticker = Ticker(symbol=symbol.upper(), price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="gateio_public")
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="gateio_public")
        except Exception as e:
            self.logger.debug(f"Erreur GateIOPublic: {e}")
        return market_data


class HuobiPublicSource(BaseDataSource):
    """Ticker public depuis Huobi (HTX)"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://api.huobi.pro"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                pair = _PublicExchangeHelpers.default_usdt_pair(symbol).lower()
                data = await self._make_request(f"{self.base_url}/market/detail/merged", params={"symbol": pair})
                if not data or data.get("status") != "ok":
                    continue
                tick = data.get("tick", {})
                price = float(tick.get("close", 0) or 0)
                bids = tick.get("bid", [0, 0])
                asks = tick.get("ask", [0, 0])
                bid = float(bids[0] or 0)
                ask = float(asks[0] or 0)
                volume = float(tick.get("amount", 0) or 0)
                ticker = Ticker(symbol=symbol.upper(), price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="huobi_public")
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="huobi_public")
        except Exception as e:
            self.logger.debug(f"Erreur HuobiPublic: {e}")
        return market_data


class MEXCPublicSource(BaseDataSource):
    """Ticker public depuis MEXC"""
    def __init__(self):
        super().__init__(api_key="")
        self.base_url = "https://api.mexc.com"

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        market_data: Dict[str, MarketData] = {}
        try:
            for symbol in symbols:
                pair = _PublicExchangeHelpers.default_usdt_pair(symbol)
                data = await self._make_request(f"{self.base_url}/api/v3/ticker/bookTicker", params={"symbol": pair})
                if not data or "bidPrice" not in data:
                    continue
                bid = float(data.get("bidPrice", 0) or 0)
                ask = float(data.get("askPrice", 0) or 0)
                price = float((bid + ask) / 2 if (bid and ask) else 0)
                volume_data = await self._make_request(f"{self.base_url}/api/v3/ticker/24hr", params={"symbol": pair})
                volume = float((volume_data or {}).get("volume", 0) or 0)
                ticker = Ticker(symbol=symbol.upper(), price=price, bid=bid, ask=ask, volume=volume, timestamp=datetime.utcnow(), source="mexc_public")
                market_data[symbol.upper()] = MarketData(symbol=symbol.upper(), ticker=ticker, timestamp=datetime.utcnow(), source="mexc_public")
        except Exception as e:
            self.logger.debug(f"Erreur MEXCPublic: {e}")
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