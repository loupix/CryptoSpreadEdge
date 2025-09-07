"""
Connecteur Bitget - Exchange majeur
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import ccxt.async_support as ccxt_async

from ..common.base_connector import BaseConnector
from ..common.market_data_types import MarketData, Ticker, OrderBook, Trade, Order, Position, Balance, OrderSide, OrderType, OrderStatus


class BitgetConnector(BaseConnector):
    """Connecteur pour Bitget (Spot, Futures, Margin)"""
    
    def __init__(self, api_key: str = "", secret_key: str = "", passphrase: str = "", sandbox: bool = True):
        super().__init__(api_key, secret_key)
        self.passphrase = passphrase
        self.sandbox = sandbox
        self.logger = logging.getLogger(__name__)
        
        # Initialiser CCXT
        self.exchange = ccxt_async.bitget({
            'apiKey': api_key,
            'secret': secret_key,
            'password': passphrase,
            'sandbox': sandbox,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # spot, future, margin
            }
        })
    
    async def connect(self) -> bool:
        """Établit la connexion avec Bitget"""
        try:
            await self.exchange.fetch_markets()
            self.connected = True
            self.logger.info("Connecté à Bitget avec succès")
            return True
        except Exception as e:
            self.logger.error(f"Erreur de connexion à Bitget: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Ferme la connexion avec Bitget"""
        try:
            await self.exchange.close()
            self.connected = False
            self.logger.info("Déconnecté de Bitget")
        except Exception as e:
            self.logger.error(f"Erreur de déconnexion de Bitget: {e}")
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données de marché pour les symboles donnés"""
        market_data = {}
        
        try:
            for symbol in symbols:
                try:
                    # Récupérer le ticker
                    ticker_data = await self.exchange.fetch_ticker(symbol)
                    
                    if ticker_data:
                        ticker = Ticker(
                            symbol=symbol,
                            price=ticker_data.get('last', 0),
                            bid=ticker_data.get('bid', 0),
                            ask=ticker_data.get('ask', 0),
                            volume=ticker_data.get('baseVolume', 0),
                            timestamp=datetime.utcnow()
                        )
                        
                        market_data[symbol] = MarketData(
                            symbol=symbol,
                            ticker=ticker,
                            timestamp=datetime.utcnow(),
                            source="bitget"
                        )
                
                except Exception as e:
                    self.logger.debug(f"Erreur récupération données {symbol}: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur récupération données de marché: {e}")
        
        return market_data
    
    async def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """Récupère le ticker pour un symbole"""
        try:
            ticker_data = await self.exchange.fetch_ticker(symbol)
            
            if ticker_data:
                ticker = Ticker(
                    symbol=symbol,
                    price=ticker_data.get('last', 0),
                    bid=ticker_data.get('bid', 0),
                    ask=ticker_data.get('ask', 0),
                    volume=ticker_data.get('baseVolume', 0),
                    timestamp=datetime.utcnow()
                )
                
                return MarketData(
                    symbol=symbol,
                    ticker=ticker,
                    timestamp=datetime.utcnow(),
                    source="bitget"
                )
        
        except Exception as e:
            self.logger.error(f"Erreur récupération ticker {symbol}: {e}")
        
        return None
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Optional[OrderBook]:
        """Récupère le carnet d'ordres pour un symbole"""
        try:
            order_book_data = await self.exchange.fetch_order_book(symbol, limit)
            
            if order_book_data:
                return OrderBook(
                    symbol=symbol,
                    bids=order_book_data.get('bids', []),
                    asks=order_book_data.get('asks', []),
                    timestamp=datetime.utcnow(),
                    source="bitget"
                )
        
        except Exception as e:
            self.logger.error(f"Erreur récupération carnet d'ordres {symbol}: {e}")
        
        return None
    
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Trade]:
        """Récupère les trades récents pour un symbole"""
        trades = []
        
        try:
            trades_data = await self.exchange.fetch_trades(symbol, limit=limit)
            
            for trade_data in trades_data:
                trade = Trade(
                    id=trade_data.get('id', ''),
                    symbol=symbol,
                    price=trade_data.get('price', 0),
                    quantity=trade_data.get('amount', 0),
                    side=trade_data.get('side', ''),
                    timestamp=datetime.fromtimestamp(trade_data.get('timestamp', 0) / 1000),
                    source="bitget"
                )
                trades.append(trade)
        
        except Exception as e:
            self.logger.error(f"Erreur récupération trades {symbol}: {e}")
        
        return trades
    
    async def place_order(self, order: Order) -> Optional[Order]:
        """Place un ordre"""
        try:
            if not self.connected:
                self.logger.error("Non connecté à Bitget")
                return None
            
            # Convertir l'ordre au format Bitget
            order_params = {
                'symbol': order.symbol,
                'type': order.order_type.value.lower(),
                'side': order.side.value.lower(),
                'amount': order.quantity,
            }
            
            if order.order_type == OrderType.LIMIT:
                order_params['price'] = order.price
            
            # Placer l'ordre
            result = await self.exchange.create_order(**order_params)
            
            if result:
                # Mettre à jour l'ordre avec les informations de Bitget
                order.order_id = result.get('id', '')
                order.status = OrderStatus.PENDING
                order.timestamp = datetime.utcnow()
                
                self.logger.info(f"Ordre placé sur Bitget: {order.symbol} {order.side.value} {order.quantity}")
                return order
        
        except Exception as e:
            self.logger.error(f"Erreur placement ordre: {e}")
        
        return None
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Annule un ordre"""
        try:
            if not self.connected:
                self.logger.error("Non connecté à Bitget")
                return False
            
            result = await self.exchange.cancel_order(order_id, symbol)
            
            if result:
                self.logger.info(f"Ordre annulé sur Bitget: {order_id}")
                return True
        
        except Exception as e:
            self.logger.error(f"Erreur annulation ordre {order_id}: {e}")
        
        return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        """Récupère le statut d'un ordre"""
        try:
            if not self.connected:
                return None
            
            order_data = await self.exchange.fetch_order(order_id, symbol)
            
            if order_data:
                order = Order(
                    order_id=order_id,
                    symbol=symbol,
                    side=OrderSide.BUY if order_data.get('side') == 'buy' else OrderSide.SELL,
                    order_type=OrderType.MARKET if order_data.get('type') == 'market' else OrderType.LIMIT,
                    quantity=order_data.get('amount', 0),
                    price=order_data.get('price', 0),
                    status=OrderStatus.FILLED if order_data.get('status') == 'closed' else OrderStatus.PENDING,
                    timestamp=datetime.fromtimestamp(order_data.get('timestamp', 0) / 1000),
                    source="bitget"
                )
                
                return order
        
        except Exception as e:
            self.logger.error(f"Erreur récupération statut ordre {order_id}: {e}")
        
        return None
    
    async def get_positions(self) -> List[Position]:
        """Récupère les positions"""
        positions = []
        
        try:
            if not self.connected:
                return positions
            
            positions_data = await self.exchange.fetch_positions()
            
            for pos_data in positions_data:
                if pos_data.get('contracts', 0) != 0:  # Position non nulle
                    position = Position(
                        symbol=pos_data.get('symbol', ''),
                        quantity=pos_data.get('contracts', 0),
                        average_price=pos_data.get('entryPrice', 0),
                        unrealized_pnl=pos_data.get('unrealizedPnl', 0),
                        timestamp=datetime.utcnow(),
                        source="bitget"
                    )
                    positions.append(position)
        
        except Exception as e:
            self.logger.error(f"Erreur récupération positions: {e}")
        
        return positions
    
    async def get_balance(self) -> List[Balance]:
        """Récupère le solde"""
        balances = []
        
        try:
            if not self.connected:
                return balances
            
            balance_data = await self.exchange.fetch_balance()
            
            for currency, balance_info in balance_data.items():
                if isinstance(balance_info, dict) and balance_info.get('total', 0) > 0:
                    balance = Balance(
                        currency=currency,
                        available=balance_info.get('free', 0),
                        total=balance_info.get('total', 0),
                        timestamp=datetime.utcnow(),
                        source="bitget"
                    )
                    balances.append(balance)
        
        except Exception as e:
            self.logger.error(f"Erreur récupération solde: {e}")
        
        return balances
    
    def get_exchange_info(self) -> Dict[str, any]:
        """Retourne les informations sur l'exchange"""
        return {
            "name": "Bitget",
            "id": "bitget",
            "connected": self.connected,
            "sandbox": self.sandbox,
            "rate_limit": 600,
            "features": ["spot", "futures", "margin"]
        }