"""
Connecteur Uniswap - DEX principal
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp
import json

from ..common.base_connector import BaseConnector
from ..common.market_data_types import MarketData, Ticker, OrderBook, Trade, Order, Position, Balance, OrderSide, OrderType, OrderStatus


class UniswapConnector(BaseConnector):
    """Connecteur pour Uniswap V3 (DEX)"""
    
    def __init__(self, api_key: str = "", secret_key: str = "", network: str = "mainnet"):
        super().__init__(api_key, secret_key)
        self.network = network
        self.logger = logging.getLogger(__name__)
        
        # URLs des APIs Uniswap
        self.base_urls = {
            "mainnet": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
            "polygon": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-polygon",
            "arbitrum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-arbitrum",
            "optimism": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-optimism"
        }
        
        self.base_url = self.base_urls.get(network, self.base_urls["mainnet"])
        
        # Adresses des contrats
        self.contract_addresses = {
            "mainnet": {
                "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
                "router": "0xE592427A0AEce92De3Edee1F18E0157C05861564"
            },
            "polygon": {
                "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
                "router": "0xE592427A0AEce92De3Edee1F18E0157C05861564"
            }
        }
    
    async def connect(self) -> bool:
        """Établit la connexion avec Uniswap"""
        try:
            # Tester la connexion avec une requête simple
            async with aiohttp.ClientSession() as session:
                query = {
                    "query": """
                        query {
                            pools(first: 1) {
                                id
                                token0 {
                                    symbol
                                }
                                token1 {
                                    symbol
                                }
                            }
                        }
                    """
                }
                
                async with session.post(self.base_url, json=query) as response:
                    if response.status == 200:
                        self.connected = True
                        self.logger.info(f"Connecté à Uniswap {self.network} avec succès")
                        return True
                    else:
                        self.logger.error(f"Erreur de connexion à Uniswap: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Erreur de connexion à Uniswap: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Ferme la connexion avec Uniswap"""
        self.connected = False
        self.logger.info("Déconnecté de Uniswap")
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché pour les symboles donnés"""
        market_data = {}
        
        try:
            # Récupérer les données des pools en parallèle
            tasks = []
            for symbol in symbols:
                task = self._get_pool_data(symbol)
                tasks.append((symbol, task))
            
            # Exécuter en parallèle
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            # Traiter les résultats
            for i, (symbol, result) in enumerate(zip(symbols, results)):
                if isinstance(result, Exception):
                    self.logger.error(f"Erreur données {symbol}: {result}")
                    continue
                
                if result:
                    market_data[symbol] = result
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des données de marché: {e}")
        
        return market_data
    
    async def _get_pool_data(self, symbol: str) -> Optional[MarketData]:
        """Récupère les données d'un pool Uniswap"""
        try:
            # Parser le symbole (ex: "ETH/USDC")
            if "/" not in symbol:
                return None
            
            token0_symbol, token1_symbol = symbol.split("/")
            
            # Requête GraphQL pour récupérer les données du pool
            query = {
                "query": f"""
                    query {{
                        pools(
                            first: 1,
                            where: {{
                                token0_: {{symbol: "{token0_symbol}"}},
                                token1_: {{symbol: "{token1_symbol}"}}
                            }}
                        ) {{
                            id
                            token0 {{
                                symbol
                                decimals
                            }}
                            token1 {{
                                symbol
                                decimals
                            }}
                            liquidity
                            sqrtPrice
                            tick
                            volumeUSD
                            feesUSD
                            token0Price
                            token1Price
                        }}
                    }}
                """
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=query) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("data", {}).get("pools"):
                            pool = data["data"]["pools"][0]
                            
                            # Calculer le prix
                            price = float(pool["token0Price"])
                            
                            # Créer le ticker
                            ticker = Ticker(
                                symbol=symbol,
                                price=price,
                                bid=price * 0.999,  # Approximation
                                ask=price * 1.001,  # Approximation
                                volume=float(pool["volumeUSD"]),
                                timestamp=datetime.utcnow(),
                                source=f"uniswap_{self.network}"
                            )
                            
                            return MarketData(
                                symbol=symbol,
                                ticker=ticker,
                                timestamp=datetime.utcnow(),
                                source=f"uniswap_{self.network}"
                            )
        
        except Exception as e:
            self.logger.error(f"Erreur données pool {symbol}: {e}")
            return None
    
    async def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """Récupère le ticker pour un symbole"""
        return await self._get_pool_data(symbol)
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Optional[MarketData]:
        """Récupère le carnet d'ordres pour un symbole (approximation pour DEX)"""
        try:
            # Pour un DEX, on simule un carnet d'ordres basé sur la liquidité
            pool_data = await self._get_pool_data(symbol)
            if not pool_data or not pool_data.ticker:
                return None
            
            price = pool_data.ticker.price
            
            # Créer des ordres simulés basés sur la liquidité
            bids = []
            asks = []
            
            # Générer des ordres autour du prix actuel
            for i in range(limit // 2):
                bid_price = price * (1 - (i + 1) * 0.001)
                ask_price = price * (1 + (i + 1) * 0.001)
                
                bids.append({
                    'price': bid_price,
                    'quantity': 1.0 / (i + 1)  # Quantité décroissante
                })
                
                asks.append({
                    'price': ask_price,
                    'quantity': 1.0 / (i + 1)
                })
            
            orderbook = OrderBook(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=datetime.utcnow(),
                source=f"uniswap_{self.network}"
            )
            
            return MarketData(
                symbol=symbol,
                order_book=orderbook,
                timestamp=datetime.utcnow(),
                source=f"uniswap_{self.network}"
            )
        
        except Exception as e:
            self.logger.error(f"Erreur orderbook {symbol}: {e}")
            return None
    
    async def get_trades(self, symbol: str, limit: int = 100) -> List[MarketData]:
        """Récupère les dernières transactions pour un symbole"""
        try:
            # Parser le symbole
            if "/" not in symbol:
                return []
            
            token0_symbol, token1_symbol = symbol.split("/")
            
            # Requête pour récupérer les swaps récents
            query = {
                "query": f"""
                    query {{
                        swaps(
                            first: {limit},
                            orderBy: timestamp,
                            orderDirection: desc,
                            where: {{
                                pool_: {{
                                    token0_: {{symbol: "{token0_symbol}"}},
                                    token1_: {{symbol: "{token1_symbol}"}}
                                }}
                            }}
                        ) {{
                            id
                            timestamp
                            amount0
                            amount1
                            amountUSD
                            transaction {{
                                id
                            }}
                        }}
                    }}
                """
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=query) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        trades = []
                        for swap in data.get("data", {}).get("swaps", []):
                            # Calculer le prix
                            amount0 = float(swap["amount0"])
                            amount1 = float(swap["amount1"])
                            
                            if amount0 > 0 and amount1 > 0:
                                price = abs(amount1 / amount0)
                                
                                trade = Trade(
                                    symbol=symbol,
                                    price=price,
                                    quantity=abs(amount0),
                                    side=OrderSide.BUY if amount0 > 0 else OrderSide.SELL,
                                    timestamp=datetime.fromtimestamp(int(swap["timestamp"])),
                                    trade_id=swap["id"],
                                    source=f"uniswap_{self.network}"
                                )
                                trades.append(trade)
                        
                        return [MarketData(
                            symbol=symbol,
                            trades=trades,
                            timestamp=datetime.utcnow(),
                            source=f"uniswap_{self.network}"
                        )]
        
        except Exception as e:
            self.logger.error(f"Erreur trades {symbol}: {e}")
            return []
    
    async def place_order(self, order: Order) -> Optional[Order]:
        """Place un ordre sur Uniswap (simulation)"""
        # Uniswap est un DEX, les ordres sont des swaps instantanés
        # Cette méthode simule un ordre pour la compatibilité
        try:
            # Simuler l'exécution de l'ordre
            placed_order = Order(
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                price=order.price,
                order_id=f"uniswap_{int(datetime.utcnow().timestamp())}",
                status=OrderStatus.FILLED,  # Les swaps DEX sont instantanés
                timestamp=datetime.utcnow(),
                source=f"uniswap_{self.network}"
            )
            
            self.logger.info(f"Ordre simulé placé sur Uniswap: {order.symbol}")
            return placed_order
            
        except Exception as e:
            self.logger.error(f"Erreur placement ordre: {e}")
            return None
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Annule un ordre (non applicable pour DEX)"""
        self.logger.warning("Annulation d'ordre non applicable pour Uniswap (DEX)")
        return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        """Récupère le statut d'un ordre (non applicable pour DEX)"""
        self.logger.warning("Statut d'ordre non applicable pour Uniswap (DEX)")
        return None
    
    async def get_positions(self) -> List[Position]:
        """Récupère les positions (non applicable pour DEX)"""
        self.logger.warning("Positions non applicables pour Uniswap (DEX)")
        return []
    
    async def get_balances(self) -> List[Balance]:
        """Récupère les soldes (non applicable pour DEX)"""
        self.logger.warning("Soldes non applicables pour Uniswap (DEX)")
        return []
    
    async def get_historical_data(
        self, 
        symbol: str, 
        timeframe: str, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[MarketData]:
        """Récupère les données historiques"""
        try:
            # Parser le symbole
            if "/" not in symbol:
                return []
            
            token0_symbol, token1_symbol = symbol.split("/")
            
            # Requête pour récupérer les données historiques
            query = {
                "query": f"""
                    query {{
                        poolDayDatas(
                            first: 1000,
                            orderBy: date,
                            orderDirection: asc,
                            where: {{
                                pool_: {{
                                    token0_: {{symbol: "{token0_symbol}"}},
                                    token1_: {{symbol: "{token1_symbol}"}}
                                }},
                                date_gte: {int(start_time.timestamp())},
                                date_lte: {int(end_time.timestamp())}
                            }}
                        ) {{
                            date
                            token0Price
                            token1Price
                            volumeUSD
                            feesUSD
                        }}
                    }}
                """
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=query) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        market_data_list = []
                        for day_data in data.get("data", {}).get("poolDayDatas", []):
                            timestamp = datetime.fromtimestamp(int(day_data["date"]))
                            
                            ticker = Ticker(
                                symbol=symbol,
                                price=float(day_data["token0Price"]),
                                bid=float(day_data["token0Price"]) * 0.999,
                                ask=float(day_data["token0Price"]) * 1.001,
                                volume=float(day_data["volumeUSD"]),
                                timestamp=timestamp,
                                source=f"uniswap_{self.network}"
                            )
                            
                            market_data = MarketData(
                                symbol=symbol,
                                ticker=ticker,
                                timestamp=timestamp,
                                source=f"uniswap_{self.network}"
                            )
                            
                            market_data_list.append(market_data)
                        
                        return market_data_list
        
        except Exception as e:
            self.logger.error(f"Erreur données historiques {symbol}: {e}")
            return []
    
    def get_name(self) -> str:
        """Retourne le nom du connecteur"""
        return f"UniswapConnector_{self.network}"
    
    async def get_liquidity_pools(self, symbol: str) -> List[Dict]:
        """Récupère les pools de liquidité pour un symbole"""
        try:
            if "/" not in symbol:
                return []
            
            token0_symbol, token1_symbol = symbol.split("/")
            
            query = {
                "query": f"""
                    query {{
                        pools(
                            first: 10,
                            where: {{
                                token0_: {{symbol: "{token0_symbol}"}},
                                token1_: {{symbol: "{token1_symbol}"}}
                            }}
                        ) {{
                            id
                            token0 {{
                                symbol
                                decimals
                            }}
                            token1 {{
                                symbol
                                decimals
                            }}
                            liquidity
                            volumeUSD
                            feesUSD
                            token0Price
                            token1Price
                        }}
                    }}
                """
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=query) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("pools", [])
        
        except Exception as e:
            self.logger.error(f"Erreur pools liquidité {symbol}: {e}")
            return []
    
    async def get_token_info(self, token_symbol: str) -> Optional[Dict]:
        """Récupère les informations d'un token"""
        try:
            query = {
                "query": f"""
                    query {{
                        tokens(
                            first: 1,
                            where: {{symbol: "{token_symbol}"}}
                        ) {{
                            id
                            symbol
                            name
                            decimals
                            totalSupply
                            volumeUSD
                            txCount
                        }}
                    }}
                """
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=query) as response:
                    if response.status == 200:
                        data = await response.json()
                        tokens = data.get("data", {}).get("tokens", [])
                        return tokens[0] if tokens else None
        
        except Exception as e:
            self.logger.error(f"Erreur info token {token_symbol}: {e}")
            return None