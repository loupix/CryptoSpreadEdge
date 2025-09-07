"""
Connecteur Coinbase (stub minimal pour market data)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..common.base_connector import BaseConnector
from ..common.market_data_types import MarketData, Ticker, OrderBook, Trade, Order, Position, Balance


class CoinbaseConnector(BaseConnector):
    """Stub minimal de connecteur Coinbase pour démos market data.

    Ne place pas d'ordres; fournit des valeurs de ticker factices.
    """

    def __init__(self, api_key: str = "", secret_key: str = "", sandbox: bool = True):
        super().__init__(api_key, secret_key)
        self.sandbox = sandbox
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> bool:
        self.connected = True
        self.logger.info("Connecté à Coinbase (stub)")
        return True

    async def disconnect(self) -> None:
        self.connected = False
        self.logger.info("Déconnecté de Coinbase (stub)")

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        data: Dict[str, MarketData] = {}
        for symbol in symbols:
            md = await self.get_ticker(symbol)
            if md:
                data[symbol] = md
        return data

    async def get_ticker(self, symbol: str) -> Optional[MarketData]:
        try:
            ticker = Ticker(
                symbol=symbol,
                price=0.0,
                bid=0.0,
                ask=0.0,
                volume=0.0,
                timestamp=datetime.utcnow(),
                source="coinbase"
            )
            return MarketData(
                symbol=symbol,
                ticker=ticker,
                order_book=None,
                timestamp=datetime.utcnow(),
                source="coinbase"
            )
        except Exception as e:
            self.logger.error(f"Erreur ticker {symbol} (stub): {e}")
            return None

    async def get_order_book(self, symbol: str, limit: int = 100) -> Optional[MarketData]:
        return None

    async def get_trades(self, symbol: str, limit: int = 100) -> List[MarketData]:
        return []

    async def place_order(self, order: Order) -> Optional[Order]:
        self.logger.warning("place_order non supporté dans le stub Coinbase")
        return None

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        self.logger.warning("cancel_order non supporté dans le stub Coinbase")
        return False

    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        return None

    async def get_positions(self) -> List[Position]:
        return []

    async def get_balances(self) -> List[Balance]:
        return []

    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MarketData]:
        return []

