"""
Connecteur Binance - Exchange principal
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import ccxt.async_support as ccxt_async

from ..common.base_connector import BaseConnector
from ..common.market_data_types import MarketData, Ticker, OrderBook, Trade, Order, Position, Balance, OrderSide, OrderType, OrderStatus


class BinanceConnector(BaseConnector):
    """Connecteur pour Binance (Spot, Futures, Margin)"""
    
    def __init__(self, api_key: str = "", secret_key: str = "", sandbox: bool = True):
        super().__init__(api_key, secret_key)
        self.sandbox = sandbox
        self.logger = logging.getLogger(__name__)
        
        # Initialiser CCXT
        self.exchange = ccxt_async.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': sandbox,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # spot, future, margin
                'adjustForTimeDifference': True,
            }
        })
        
        # Exchanges pour différents types
        self.spot_exchange = self.exchange
        self.futures_exchange = None
        self.margin_exchange = None
        
        if api_key and secret_key:
            self._init_futures_exchange()
            self._init_margin_exchange()
    
    def _init_futures_exchange(self):
        """Initialise l'exchange futures"""
        try:
            self.futures_exchange = ccxt_async.binance({
                'apiKey': self.api_key,
                'secret': self.secret_key,
                'sandbox': self.sandbox,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                }
            })
        except Exception as e:
            self.logger.warning(f"Impossible d'initialiser l'exchange futures: {e}")
    
    def _init_margin_exchange(self):
        """Initialise l'exchange margin"""
        try:
            self.margin_exchange = ccxt_async.binance({
                'apiKey': self.api_key,
                'secret': self.secret_key,
                'sandbox': self.sandbox,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'margin',
                }
            })
        except Exception as e:
            self.logger.warning(f"Impossible d'initialiser l'exchange margin: {e}")
    
    async def connect(self) -> bool:
        """Établit la connexion avec Binance"""
        try:
            # Tester la connexion avec une requête simple
            await self.exchange.fetch_markets()
            self.connected = True
            self.logger.info("Connecté à Binance avec succès")
            return True
        except Exception as e:
            self.logger.error(f"Erreur de connexion à Binance: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Ferme la connexion avec Binance"""
        try:
            await self.exchange.close()
            if self.futures_exchange:
                await self.futures_exchange.close()
            if self.margin_exchange:
                await self.margin_exchange.close()
            self.connected = False
            self.logger.info("Déconnecté de Binance")
        except Exception as e:
            self.logger.error(f"Erreur de déconnexion de Binance: {e}")
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché pour les symboles donnés"""
        market_data = {}
        
        try:
            # Récupérer les tickers en parallèle
            ticker_tasks = []
            for symbol in symbols:
                task = self._get_ticker_data(symbol)
                ticker_tasks.append((symbol, task))
            
            # Récupérer les carnets d'ordres en parallèle
            orderbook_tasks = []
            for symbol in symbols:
                task = self._get_orderbook_data(symbol)
                orderbook_tasks.append((symbol, task))
            
            # Exécuter en parallèle
            ticker_results = await asyncio.gather(*[task for _, task in ticker_tasks], return_exceptions=True)
            orderbook_results = await asyncio.gather(*[task for _, task in orderbook_tasks], return_exceptions=True)
            
            # Traiter les résultats
            for i, (symbol, result) in enumerate(zip(symbols, ticker_results)):
                if isinstance(result, Exception):
                    self.logger.error(f"Erreur ticker {symbol}: {result}")
                    continue
                
                ticker = result
                orderbook = orderbook_results[i] if not isinstance(orderbook_results[i], Exception) else None
                
                market_data[symbol] = MarketData(
                    symbol=symbol,
                    ticker=ticker,
                    order_book=orderbook,
                    timestamp=datetime.utcnow(),
                    source="binance"
                )
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des données de marché: {e}")
        
        return market_data
    
    async def _get_ticker_data(self, symbol: str) -> Optional[Ticker]:
        """Récupère les données de ticker pour un symbole"""
        try:
            ticker_data = await self.exchange.fetch_ticker(symbol)
            
            return Ticker(
                symbol=symbol,
                price=ticker_data['last'],
                bid=ticker_data['bid'],
                ask=ticker_data['ask'],
                volume=ticker_data['baseVolume'],
                timestamp=datetime.fromtimestamp(ticker_data['timestamp'] / 1000),
                source="binance"
            )
        except Exception as e:
            self.logger.error(f"Erreur ticker {symbol}: {e}")
            return None
    
    async def _get_orderbook_data(self, symbol: str, limit: int = 100) -> Optional[OrderBook]:
        """Récupère le carnet d'ordres pour un symbole"""
        try:
            orderbook_data = await self.exchange.fetch_order_book(symbol, limit)
            
            # Convertir les données
            bids = [{'price': price, 'quantity': qty} for price, qty in orderbook_data['bids']]
            asks = [{'price': price, 'quantity': qty} for price, qty in orderbook_data['asks']]
            
            return OrderBook(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=datetime.fromtimestamp(orderbook_data['timestamp'] / 1000),
                source="binance"
            )
        except Exception as e:
            self.logger.error(f"Erreur orderbook {symbol}: {e}")
            return None
    
    async def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """Récupère le ticker pour un symbole"""
        try:
            ticker = await self._get_ticker_data(symbol)
            if ticker:
                return MarketData(
                    symbol=symbol,
                    ticker=ticker,
                    timestamp=datetime.utcnow(),
                    source="binance"
                )
        except Exception as e:
            self.logger.error(f"Erreur ticker {symbol}: {e}")
        return None
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Optional[MarketData]:
        """Récupère le carnet d'ordres pour un symbole"""
        try:
            orderbook = await self._get_orderbook_data(symbol, limit)
            if orderbook:
                return MarketData(
                    symbol=symbol,
                    order_book=orderbook,
                    timestamp=datetime.utcnow(),
                    source="binance"
                )
        except Exception as e:
            self.logger.error(f"Erreur orderbook {symbol}: {e}")
        return None
    
    async def get_trades(self, symbol: str, limit: int = 100) -> List[MarketData]:
        """Récupère les dernières transactions pour un symbole"""
        try:
            trades_data = await self.exchange.fetch_trades(symbol, limit=limit)
            
            trades = []
            for trade_data in trades_data:
                trade = Trade(
                    symbol=symbol,
                    price=trade_data['price'],
                    quantity=trade_data['amount'],
                    side=OrderSide.BUY if trade_data['side'] == 'buy' else OrderSide.SELL,
                    timestamp=datetime.fromtimestamp(trade_data['timestamp'] / 1000),
                    trade_id=str(trade_data['id']),
                    source="binance"
                )
                trades.append(trade)
            
            return [MarketData(
                symbol=symbol,
                trades=trades,
                timestamp=datetime.utcnow(),
                source="binance"
            )]
        except Exception as e:
            self.logger.error(f"Erreur trades {symbol}: {e}")
            return []
    
    async def place_order(self, order: Order) -> Optional[Order]:
        """Place un ordre sur Binance"""
        try:
            # Convertir l'ordre en format CCXT
            ccxt_order = {
                'symbol': order.symbol,
                'type': order.order_type.value,
                'side': order.side.value,
                'amount': order.quantity,
            }
            
            if order.price:
                ccxt_order['price'] = order.price
            
            if order.stop_price:
                ccxt_order['stopPrice'] = order.stop_price
            
            # Placer l'ordre
            result = await self.exchange.create_order(**ccxt_order)
            
            # Convertir le résultat
            placed_order = Order(
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                price=order.price,
                order_id=str(result['id']),
                status=OrderStatus.OPEN if result['status'] == 'open' else OrderStatus.PENDING,
                timestamp=datetime.utcnow(),
                source="binance"
            )
            
            return placed_order
            
        except Exception as e:
            self.logger.error(f"Erreur placement ordre: {e}")
            return None
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Annule un ordre"""
        try:
            await self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            self.logger.error(f"Erreur annulation ordre {order_id}: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        """Récupère le statut d'un ordre"""
        try:
            order_data = await self.exchange.fetch_order(order_id, symbol)
            
            # Convertir en objet Order
            order = Order(
                symbol=symbol,
                side=OrderSide.BUY if order_data['side'] == 'buy' else OrderSide.SELL,
                order_type=OrderType(order_data['type']),
                quantity=order_data['amount'],
                price=order_data.get('price'),
                order_id=str(order_data['id']),
                status=OrderStatus(order_data['status']),
                filled_quantity=order_data['filled'],
                average_price=order_data.get('average'),
                timestamp=datetime.fromtimestamp(order_data['timestamp'] / 1000),
                source="binance"
            )
            
            return order
        except Exception as e:
            self.logger.error(f"Erreur statut ordre {order_id}: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Récupère les positions ouvertes"""
        positions = []
        
        try:
            # Positions spot (balances non nulles)
            balances = await self.get_balances()
            for balance in balances:
                if balance.total > 0:
                    position = Position(
                        symbol=balance.currency,
                        side=OrderSide.BUY,  # Par défaut
                        quantity=balance.total,
                        average_price=0,  # Non disponible pour les positions spot
                        timestamp=datetime.utcnow(),
                        source="binance"
                    )
                    positions.append(position)
            
            # Positions futures (si disponible)
            if self.futures_exchange:
                try:
                    futures_positions = await self.futures_exchange.fetch_positions()
                    for pos_data in futures_positions:
                        if pos_data['contracts'] > 0:
                            position = Position(
                                symbol=pos_data['symbol'],
                                side=OrderSide.BUY if pos_data['side'] == 'long' else OrderSide.SELL,
                                quantity=pos_data['contracts'],
                                average_price=pos_data['entryPrice'],
                                unrealized_pnl=pos_data['unrealizedPnl'],
                                timestamp=datetime.utcnow(),
                                source="binance_futures"
                            )
                            positions.append(position)
                except Exception as e:
                    self.logger.warning(f"Erreur positions futures: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur récupération positions: {e}")
        
        return positions
    
    async def get_balances(self) -> List[Balance]:
        """Récupère les soldes du compte"""
        try:
            balances_data = await self.exchange.fetch_balance()
            
            balances = []
            for currency, balance_info in balances_data.items():
                if isinstance(balance_info, dict) and 'total' in balance_info:
                    balance = Balance(
                        currency=currency,
                        free=balance_info['free'],
                        used=balance_info['used'],
                        total=balance_info['total'],
                        timestamp=datetime.utcnow(),
                        source="binance"
                    )
                    balances.append(balance)
            
            return balances
        except Exception as e:
            self.logger.error(f"Erreur récupération soldes: {e}")
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
            ohlcv_data = await self.exchange.fetch_ohlcv(
                symbol, 
                timeframe, 
                since=int(start_time.timestamp() * 1000),
                limit=1000
            )
            
            market_data_list = []
            for ohlcv in ohlcv_data:
                # Convertir OHLCV en MarketData
                timestamp = datetime.fromtimestamp(ohlcv[0] / 1000)
                
                # Créer un ticker basé sur les données OHLCV
                ticker = Ticker(
                    symbol=symbol,
                    price=ohlcv[4],  # Close price
                    bid=ohlcv[2],    # High
                    ask=ohlcv[3],    # Low
                    volume=ohlcv[5], # Volume
                    timestamp=timestamp,
                    source="binance"
                )
                
                market_data = MarketData(
                    symbol=symbol,
                    ticker=ticker,
                    timestamp=timestamp,
                    source="binance"
                )
                
                market_data_list.append(market_data)
            
            return market_data_list
        except Exception as e:
            self.logger.error(f"Erreur données historiques {symbol}: {e}")
            return []
    
    def get_name(self) -> str:
        """Retourne le nom du connecteur"""
        return "BinanceConnector"
    
    async def get_futures_data(self, symbol: str) -> Optional[MarketData]:
        """Récupère les données futures"""
        if not self.futures_exchange:
            return None
        
        try:
            ticker_data = await self.futures_exchange.fetch_ticker(symbol)
            
            ticker = Ticker(
                symbol=symbol,
                price=ticker_data['last'],
                bid=ticker_data['bid'],
                ask=ticker_data['ask'],
                volume=ticker_data['baseVolume'],
                timestamp=datetime.fromtimestamp(ticker_data['timestamp'] / 1000),
                source="binance_futures"
            )
            
            return MarketData(
                symbol=symbol,
                ticker=ticker,
                timestamp=datetime.utcnow(),
                source="binance_futures"
            )
        except Exception as e:
            self.logger.error(f"Erreur données futures {symbol}: {e}")
            return None
    
    async def get_margin_data(self, symbol: str) -> Optional[MarketData]:
        """Récupère les données margin"""
        if not self.margin_exchange:
            return None
        
        try:
            ticker_data = await self.margin_exchange.fetch_ticker(symbol)
            
            ticker = Ticker(
                symbol=symbol,
                price=ticker_data['last'],
                bid=ticker_data['bid'],
                ask=ticker_data['ask'],
                volume=ticker_data['baseVolume'],
                timestamp=datetime.fromtimestamp(ticker_data['timestamp'] / 1000),
                source="binance_margin"
            )
            
            return MarketData(
                symbol=symbol,
                ticker=ticker,
                timestamp=datetime.utcnow(),
                source="binance_margin"
            )
        except Exception as e:
            self.logger.error(f"Erreur données margin {symbol}: {e}")
            return None