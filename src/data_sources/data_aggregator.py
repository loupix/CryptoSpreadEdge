"""
Agrégateur de données pour CryptoSpreadEdge
Combine les données de toutes les sources (exchanges + sources alternatives)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from ..connectors.common.market_data_types import MarketData, Ticker, OrderBook, Trade
from ..connectors.connector_factory import connector_factory
from .alternative_sources import alternative_sources
from ...config.arbitrage_config import DATA_SOURCES


@dataclass
class AggregatedData:
    """Données agrégées d'une source"""
    symbol: str
    price: float
    volume: float
    market_cap: float
    change_24h: float
    bid: float
    ask: float
    spread: float
    sources: List[str]
    confidence: float
    timestamp: datetime


class DataAggregator:
    """Agrégateur de données de marché"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.exchange_connectors = {}
        self.alternative_sources = alternative_sources
        self.data_cache = {}
        self.cache_ttl = 30  # secondes
    
    async def initialize_connectors(self, credentials: Dict[str, Dict[str, str]] = None):
        """Initialise tous les connecteurs"""
        try:
            # Créer les connecteurs d'exchanges
            self.exchange_connectors = await connector_factory.create_arbitrage_connectors(credentials)
            
            # Connecter tous les exchanges
            connection_results = await connector_factory.connect_all()
            
            connected_count = sum(1 for success in connection_results.values() if success)
            self.logger.info(f"Connecté à {connected_count} exchanges sur {len(connection_results)}")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation connecteurs: {e}")
    
    async def get_aggregated_data(self, symbols: List[str]) -> Dict[str, AggregatedData]:
        """Récupère les données agrégées pour les symboles donnés"""
        aggregated_data = {}
        
        try:
            # Récupérer les données de toutes les sources en parallèle
            tasks = []
            
            # Données des exchanges
            for exchange_id, connector in self.exchange_connectors.items():
                if connector.is_connected():
                    task = self._get_exchange_data(connector, symbols, exchange_id)
                    tasks.append(task)
            
            # Données des sources alternatives (pilotées par la config)
            for source_name, cfg in DATA_SOURCES.items():
                if not cfg.enabled:
                    continue
                task = self._get_alternative_data(source_name, symbols)
                tasks.append(task)
            
            # Exécuter toutes les tâches en parallèle
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Traiter les résultats
                all_data = {}
                for result in results:
                    if isinstance(result, Exception):
                        self.logger.error(f"Erreur récupération données: {result}")
                    elif result:
                        source_name, data = result
                        all_data[source_name] = data
                
                # Agréger les données par symbole
                for symbol in symbols:
                    aggregated = self._aggregate_symbol_data(symbol, all_data)
                    if aggregated:
                        aggregated_data[symbol] = aggregated
        
        except Exception as e:
            self.logger.error(f"Erreur agrégation données: {e}")
        
        return aggregated_data
    
    async def _get_exchange_data(self, connector, symbols: List[str], exchange_id: str) -> Optional[Tuple[str, Dict[str, MarketData]]]:
        """Récupère les données d'un exchange"""
        try:
            data = await connector.get_market_data(symbols)
            return (exchange_id, data)
        except Exception as e:
            self.logger.error(f"Erreur données {exchange_id}: {e}")
            return None
    
    async def _get_alternative_data(self, source_name: str, symbols: List[str]) -> Optional[Tuple[str, Dict[str, MarketData]]]:
        """Récupère les données d'une source alternative"""
        try:
            data = await self.alternative_sources.get_market_data(symbols, source_name)
            return (source_name, data)
        except Exception as e:
            self.logger.error(f"Erreur données {source_name}: {e}")
            return None
    
    def _aggregate_symbol_data(self, symbol: str, all_data: Dict[str, Dict[str, MarketData]]) -> Optional[AggregatedData]:
        """Agrège les données d'un symbole depuis toutes les sources"""
        try:
            prices = []
            volumes = []
            market_caps = []
            changes_24h = []
            bids = []
            asks = []
            sources = []
            
            # Collecter les données de toutes les sources
            for source_name, source_data in all_data.items():
                if symbol in source_data:
                    market_data = source_data[symbol]
                    
                    if market_data.ticker:
                        ticker = market_data.ticker
                        
                        if ticker.price > 0:
                            prices.append(ticker.price)
                            sources.append(source_name)
                        
                        if ticker.volume > 0:
                            volumes.append(ticker.volume)
                        
                        if hasattr(ticker, 'market_cap') and ticker.market_cap > 0:
                            market_caps.append(ticker.market_cap)
                        
                        if hasattr(ticker, 'change_24h'):
                            changes_24h.append(ticker.change_24h)
                        
                        if ticker.bid > 0:
                            bids.append(ticker.bid)
                        
                        if ticker.ask > 0:
                            asks.append(ticker.ask)
            
            if not prices:
                return None
            
            # Calculer les moyennes et statistiques
            avg_price = statistics.mean(prices)
            median_price = statistics.median(prices)
            price_std = statistics.stdev(prices) if len(prices) > 1 else 0
            
            # Calculer la confiance basée sur la cohérence des prix
            confidence = self._calculate_confidence(prices, price_std)
            
            # Calculer le spread moyen
            avg_bid = statistics.mean(bids) if bids else avg_price * 0.999
            avg_ask = statistics.mean(asks) if asks else avg_price * 1.001
            spread = avg_ask - avg_bid
            
            # Calculer les moyennes des autres métriques
            avg_volume = statistics.mean(volumes) if volumes else 0
            avg_market_cap = statistics.mean(market_caps) if market_caps else 0
            avg_change_24h = statistics.mean(changes_24h) if changes_24h else 0
            
            return AggregatedData(
                symbol=symbol,
                price=avg_price,
                volume=avg_volume,
                market_cap=avg_market_cap,
                change_24h=avg_change_24h,
                bid=avg_bid,
                ask=avg_ask,
                spread=spread,
                sources=sources,
                confidence=confidence,
                timestamp=datetime.utcnow()
            )
        
        except Exception as e:
            self.logger.error(f"Erreur agrégation {symbol}: {e}")
            return None
    
    def _calculate_confidence(self, prices: List[float], std_dev: float) -> float:
        """Calcule la confiance basée sur la cohérence des prix"""
        if not prices or len(prices) < 2:
            return 0.5
        
        # Plus la variance est faible, plus la confiance est élevée
        avg_price = statistics.mean(prices)
        cv = std_dev / avg_price if avg_price > 0 else 1.0
        
        # Confiance entre 0 et 1
        confidence = max(0.0, min(1.0, 1.0 - cv))
        
        # Bonus pour plus de sources
        source_bonus = min(0.2, len(prices) * 0.05)
        confidence = min(1.0, confidence + source_bonus)
        
        return confidence
    
    async def get_arbitrage_opportunities(self, symbols: List[str], min_spread: float = 0.001) -> List[Dict[str, Any]]:
        """Identifie les opportunités d'arbitrage"""
        opportunities = []
        
        try:
            # Récupérer les données agrégées
            aggregated_data = await self.get_aggregated_data(symbols)
            
            for symbol, data in aggregated_data.items():
                if data.confidence < 0.7:  # Seulement les données fiables
                    continue
                
                # Récupérer les prix par source
                source_prices = await self._get_source_prices(symbol)
                
                if len(source_prices) < 2:
                    continue
                
                # Trouver les prix min et max
                min_price = min(source_prices.values())
                max_price = max(source_prices.values())
                
                # Calculer le spread
                spread = (max_price - min_price) / min_price
                
                if spread >= min_spread:
                    opportunity = {
                        "symbol": symbol,
                        "spread": spread,
                        "min_price": min_price,
                        "max_price": max_price,
                        "min_source": min(source_prices, key=source_prices.get),
                        "max_source": max(source_prices, key=source_prices.get),
                        "confidence": data.confidence,
                        "timestamp": datetime.utcnow()
                    }
                    opportunities.append(opportunity)
        
        except Exception as e:
            self.logger.error(f"Erreur recherche arbitrage: {e}")
        
        return opportunities
    
    async def _get_source_prices(self, symbol: str) -> Dict[str, float]:
        """Récupère les prix d'un symbole par source"""
        source_prices = {}
        
        try:
            # Prix des exchanges
            for exchange_id, connector in self.exchange_connectors.items():
                if connector.is_connected():
                    try:
                        market_data = await connector.get_ticker(symbol)
                        if market_data and market_data.ticker:
                            source_prices[exchange_id] = market_data.ticker.price
                    except Exception as e:
                        self.logger.debug(f"Erreur prix {exchange_id} {symbol}: {e}")
            
            # Prix des sources alternatives (pilotées par la config)
            for source_name, cfg in DATA_SOURCES.items():
                if not cfg.enabled:
                    continue
                try:
                    data = await self.alternative_sources.get_market_data([symbol], source_name)
                    if symbol in data and data[symbol].ticker:
                        source_prices[source_name] = data[symbol].ticker.price
                except Exception as e:
                    self.logger.debug(f"Erreur prix {source_name} {symbol}: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur récupération prix {symbol}: {e}")
        
        return source_prices
    
    async def get_market_overview(self, symbols: List[str]) -> Dict[str, Any]:
        """Récupère un aperçu du marché"""
        try:
            aggregated_data = await self.get_aggregated_data(symbols)
            
            overview = {
                "total_symbols": len(symbols),
                "data_sources": len(self.exchange_connectors) + len(self.alternative_sources.sources),
                "connected_exchanges": len([c for c in self.exchange_connectors.values() if c.is_connected()]),
                "symbols_data": {},
                "market_summary": {
                    "total_volume": 0,
                    "total_market_cap": 0,
                    "avg_change_24h": 0,
                    "high_confidence_symbols": 0
                }
            }
            
            # Analyser les données par symbole
            volumes = []
            market_caps = []
            changes_24h = []
            
            for symbol, data in aggregated_data.items():
                overview["symbols_data"][symbol] = {
                    "price": data.price,
                    "volume": data.volume,
                    "market_cap": data.market_cap,
                    "change_24h": data.change_24h,
                    "confidence": data.confidence,
                    "sources_count": len(data.sources),
                    "spread": data.spread
                }
                
                if data.volume > 0:
                    volumes.append(data.volume)
                
                if data.market_cap > 0:
                    market_caps.append(data.market_cap)
                
                if data.change_24h != 0:
                    changes_24h.append(data.change_24h)
                
                if data.confidence > 0.8:
                    overview["market_summary"]["high_confidence_symbols"] += 1
            
            # Calculer les totaux
            overview["market_summary"]["total_volume"] = sum(volumes)
            overview["market_summary"]["total_market_cap"] = sum(market_caps)
            overview["market_summary"]["avg_change_24h"] = statistics.mean(changes_24h) if changes_24h else 0
            
            return overview
        
        except Exception as e:
            self.logger.error(f"Erreur aperçu marché: {e}")
            return {}
    
    async def get_real_time_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les données en temps réel (avec cache)"""
        try:
            # Vérifier le cache
            cache_key = f"realtime_{','.join(sorted(symbols))}"
            if cache_key in self.data_cache:
                cached_data, timestamp = self.data_cache[cache_key]
                if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_data
            
            # Récupérer les données fraîches
            real_time_data = {}
            
            # Données des exchanges connectés
            for exchange_id, connector in self.exchange_connectors.items():
                if connector.is_connected():
                    try:
                        data = await connector.get_market_data(symbols)
                        real_time_data.update(data)
                    except Exception as e:
                        self.logger.debug(f"Erreur données temps réel {exchange_id}: {e}")
            
            # Mettre en cache
            self.data_cache[cache_key] = (real_time_data, datetime.utcnow())
            
            return real_time_data
        
        except Exception as e:
            self.logger.error(f"Erreur données temps réel: {e}")
            return {}
    
    def get_available_sources(self) -> Dict[str, List[str]]:
        """Retourne les sources disponibles"""
        return {
            "exchanges": list(self.exchange_connectors.keys()),
            "alternative_sources": list(self.alternative_sources.sources.keys()),
            "connected_exchanges": [
                name for name, connector in self.exchange_connectors.items()
                if connector.is_connected()
            ]
        }
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """Retourne le statut de toutes les sources"""
        status = {}
        
        # Statut des exchanges
        for exchange_id, connector in self.exchange_connectors.items():
            status[exchange_id] = {
                "type": "exchange",
                "connected": connector.is_connected(),
                "name": connector.get_name()
            }
        
        # Statut des sources alternatives
        for source_name in self.alternative_sources.sources.keys():
            status[source_name] = {
                "type": "alternative",
                "connected": True,  # Les sources alternatives sont toujours disponibles
                "name": source_name
            }
        
        return status
    
    async def cleanup(self):
        """Nettoie les ressources"""
        try:
            # Déconnecter tous les exchanges
            await connector_factory.disconnect_all()
            
            # Vider le cache
            self.data_cache.clear()
            
            self.logger.info("Nettoyage des ressources terminé")
        
        except Exception as e:
            self.logger.error(f"Erreur nettoyage: {e}")


# Instance globale de l'agrégateur
data_aggregator = DataAggregator()