"""
Système de monitoring des prix pour l'arbitrage
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
import time

from ..connectors.common.market_data_types import MarketData, Ticker
from ..connectors.connector_factory import connector_factory
from ..data_sources.data_aggregator import data_aggregator


@dataclass
class PriceData:
    """Données de prix d'une plateforme"""
    symbol: str
    platform: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime
    confidence: float
    source: str


@dataclass
class PriceAlert:
    """Alerte de prix"""
    symbol: str
    platform: str
    price: float
    threshold: float
    direction: str  # "above" or "below"
    timestamp: datetime
    message: str


class PriceMonitor:
    """Moniteur de prix pour l'arbitrage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.price_cache: Dict[str, Dict[str, PriceData]] = {}
        self.price_history: Dict[str, List[PriceData]] = {}
        self.alerts: List[PriceAlert] = []
        
        # Configuration
        self.update_interval = 1.0  # secondes
        self.history_length = 1000  # nombre de points d'historique
        self.price_change_threshold = 0.05  # 5% de changement
        self.volume_spike_threshold = 2.0  # 2x le volume moyen
        
        # Statistiques
        self.stats = {
            "total_updates": 0,
            "price_changes_detected": 0,
            "volume_spikes_detected": 0,
            "alerts_triggered": 0,
            "avg_update_time": 0.0
        }
    
    async def start(self):
        """Démarre le monitoring des prix"""
        self.logger.info("Démarrage du monitoring des prix")
        self.is_running = True
        
        # Démarrer les tâches de monitoring
        tasks = [
            self._monitor_exchange_prices(),
            self._monitor_data_sources(),
            self._detect_price_changes(),
            self._detect_volume_spikes(),
            self._cleanup_old_data()
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Arrête le monitoring des prix"""
        self.logger.info("Arrêt du monitoring des prix")
        self.is_running = False
    
    async def _monitor_exchange_prices(self):
        """Surveille les prix des exchanges"""
        while self.is_running:
            try:
                start_time = time.time()
                
                # Symboles à surveiller
                symbols = ["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"]
                
                # Récupérer les prix de tous les exchanges connectés
                for exchange_id, connector in connector_factory.get_all_connectors().items():
                    if not connector.is_connected():
                        continue
                    
                    try:
                        for symbol in symbols:
                            market_data = await connector.get_ticker(symbol)
                            if market_data and market_data.ticker:
                                price_data = PriceData(
                                    symbol=symbol,
                                    platform=exchange_id,
                                    price=market_data.ticker.price,
                                    bid=market_data.ticker.bid,
                                    ask=market_data.ticker.ask,
                                    volume=market_data.ticker.volume,
                                    timestamp=market_data.timestamp,
                                    confidence=1.0,
                                    source="exchange"
                                )
                                
                                await self._update_price_cache(price_data)
                    
                    except Exception as e:
                        self.logger.debug(f"Erreur monitoring {exchange_id}: {e}")
                
                # Mettre à jour les statistiques
                update_time = time.time() - start_time
                self.stats["total_updates"] += 1
                self.stats["avg_update_time"] = (
                    (self.stats["avg_update_time"] * (self.stats["total_updates"] - 1) + update_time) /
                    self.stats["total_updates"]
                )
                
                await asyncio.sleep(self.update_interval)
            
            except Exception as e:
                self.logger.error(f"Erreur monitoring exchanges: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_data_sources(self):
        """Surveille les sources de données alternatives"""
        while self.is_running:
            try:
                symbols = ["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"]
                
                # Récupérer les données des sources alternatives
                for source_name in [
                    "coinmarketcap", "coingecko", "cryptocompare", "messari",
                    # Sources publiques par exchange
                    "binance_public", "okx_public", "bybit_public", "kucoin_public",
                    "kraken_public", "bitfinex_public", "bitstamp_public", "gateio_public",
                    "huobi_public", "mexc_public"
                ]:
                    try:
                        data = await data_aggregator.alternative_sources.get_market_data(symbols, source_name)
                        
                        for symbol, market_data in data.items():
                            if market_data and market_data.ticker:
                                price_data = PriceData(
                                    symbol=symbol,
                                    platform=source_name,
                                    price=market_data.ticker.price,
                                    bid=market_data.ticker.bid,
                                    ask=market_data.ticker.ask,
                                    volume=market_data.ticker.volume,
                                    timestamp=market_data.timestamp,
                                    confidence=0.8,  # Confiance plus faible pour les sources alternatives
                                    source="data_source"
                                )
                                
                                await self._update_price_cache(price_data)
                    
                    except Exception as e:
                        self.logger.debug(f"Erreur monitoring {source_name}: {e}")
                
                await asyncio.sleep(5)  # Mise à jour moins fréquente pour les sources alternatives
            
            except Exception as e:
                self.logger.error(f"Erreur monitoring sources: {e}")
                await asyncio.sleep(10)
    
    async def _update_price_cache(self, price_data: PriceData):
        """Met à jour le cache des prix"""
        try:
            symbol = price_data.symbol
            platform = price_data.platform
            
            # Initialiser le cache pour le symbole si nécessaire
            if symbol not in self.price_cache:
                self.price_cache[symbol] = {}
            
            # Mettre à jour le cache
            self.price_cache[symbol][platform] = price_data
            
            # Ajouter à l'historique
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append(price_data)
            
            # Limiter la taille de l'historique
            if len(self.price_history[symbol]) > self.history_length:
                self.price_history[symbol] = self.price_history[symbol][-self.history_length:]
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour cache: {e}")
    
    async def _detect_price_changes(self):
        """Détecte les changements de prix significatifs"""
        while self.is_running:
            try:
                for symbol, platform_prices in self.price_cache.items():
                    if len(platform_prices) < 2:
                        continue
                    
                    # Calculer le prix moyen
                    prices = [data.price for data in platform_prices.values() if data.price > 0]
                    if len(prices) < 2:
                        continue
                    
                    avg_price = statistics.mean(prices)
                    
                    # Vérifier les changements significatifs
                    for platform, price_data in platform_prices.items():
                        if price_data.price <= 0:
                            continue
                        
                        price_change = abs(price_data.price - avg_price) / avg_price
                        
                        if price_change > self.price_change_threshold:
                            self.stats["price_changes_detected"] += 1
                            
                            # Créer une alerte
                            alert = PriceAlert(
                                symbol=symbol,
                                platform=platform,
                                price=price_data.price,
                                threshold=avg_price * (1 + self.price_change_threshold),
                                direction="above" if price_data.price > avg_price else "below",
                                timestamp=datetime.utcnow(),
                                message=f"Changement de prix significatif: {price_change:.2%}"
                            )
                            
                            self.alerts.append(alert)
                            self.stats["alerts_triggered"] += 1
                            
                            self.logger.warning(
                                f"Alerte prix {symbol} {platform}: {price_data.price:.2f} "
                                f"(changement: {price_change:.2%})"
                            )
                
                await asyncio.sleep(2)  # Vérification toutes les 2 secondes
            
            except Exception as e:
                self.logger.error(f"Erreur détection changements prix: {e}")
                await asyncio.sleep(5)
    
    async def _detect_volume_spikes(self):
        """Détecte les pics de volume"""
        while self.is_running:
            try:
                for symbol, price_history in self.price_history.items():
                    if len(price_history) < 10:
                        continue
                    
                    # Calculer le volume moyen des 10 dernières minutes
                    recent_data = [
                        data for data in price_history[-10:]
                        if data.timestamp > datetime.utcnow() - timedelta(minutes=10)
                    ]
                    
                    if len(recent_data) < 5:
                        continue
                    
                    volumes = [data.volume for data in recent_data if data.volume > 0]
                    if len(volumes) < 3:
                        continue
                    
                    avg_volume = statistics.mean(volumes)
                    current_volume = recent_data[-1].volume
                    
                    if current_volume > avg_volume * self.volume_spike_threshold:
                        self.stats["volume_spikes_detected"] += 1
                        
                        # Créer une alerte
                        alert = PriceAlert(
                            symbol=symbol,
                            platform=recent_data[-1].platform,
                            price=recent_data[-1].price,
                            threshold=avg_volume * self.volume_spike_threshold,
                            direction="above",
                            timestamp=datetime.utcnow(),
                            message=f"Pic de volume détecté: {current_volume:.0f} vs {avg_volume:.0f} moyen"
                        )
                        
                        self.alerts.append(alert)
                        self.stats["alerts_triggered"] += 1
                        
                        self.logger.warning(
                            f"Alerte volume {symbol} {recent_data[-1].platform}: "
                            f"{current_volume:.0f} (pic: {current_volume/avg_volume:.1f}x)"
                        )
                
                await asyncio.sleep(10)  # Vérification toutes les 10 secondes
            
            except Exception as e:
                self.logger.error(f"Erreur détection pics volume: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_old_data(self):
        """Nettoie les données anciennes"""
        while self.is_running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                # Nettoyer les alertes anciennes
                self.alerts = [
                    alert for alert in self.alerts
                    if alert.timestamp > cutoff_time
                ]
                
                # Nettoyer l'historique des prix
                for symbol in self.price_history:
                    self.price_history[symbol] = [
                        data for data in self.price_history[symbol]
                        if data.timestamp > cutoff_time
                    ]
                
                await asyncio.sleep(300)  # Nettoyage toutes les 5 minutes
            
            except Exception as e:
                self.logger.error(f"Erreur nettoyage données: {e}")
                await asyncio.sleep(300)
    
    async def get_all_prices(self, symbols: List[str]) -> Dict[str, Dict[str, PriceData]]:
        """Récupère tous les prix pour les symboles donnés"""
        result = {}
        
        for symbol in symbols:
            if symbol in self.price_cache:
                result[symbol] = self.price_cache[symbol].copy()
        
        return result
    
    async def get_price(self, symbol: str, platform: str) -> Optional[PriceData]:
        """Récupère le prix d'un symbole sur une plateforme"""
        if symbol in self.price_cache and platform in self.price_cache[symbol]:
            return self.price_cache[symbol][platform]
        return None
    
    async def get_best_prices(self, symbol: str) -> Dict[str, PriceData]:
        """Récupère les meilleurs prix (achat et vente) pour un symbole"""
        if symbol not in self.price_cache:
            return {}
        
        platform_prices = self.price_cache[symbol]
        if not platform_prices:
            return {}
        
        # Trouver le meilleur prix d'achat (ask le plus bas)
        best_buy = min(
            platform_prices.values(),
            key=lambda x: x.ask if x.ask > 0 else float('inf')
        )
        
        # Trouver le meilleur prix de vente (bid le plus élevé)
        best_sell = max(
            platform_prices.values(),
            key=lambda x: x.bid if x.bid > 0 else 0
        )
        
        return {
            "best_buy": best_buy,
            "best_sell": best_sell
        }
    
    async def get_price_spread(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Calcule l'écart de prix entre les plateformes"""
        best_prices = await self.get_best_prices(symbol)
        
        if not best_prices or "best_buy" not in best_prices or "best_sell" not in best_prices:
            return None
        
        best_buy = best_prices["best_buy"]
        best_sell = best_prices["best_sell"]
        
        if best_buy.platform == best_sell.platform:
            return None  # Même plateforme, pas d'arbitrage possible
        
        spread = best_sell.bid - best_buy.ask
        spread_percentage = spread / best_buy.ask if best_buy.ask > 0 else 0
        
        return {
            "symbol": symbol,
            "buy_platform": best_buy.platform,
            "sell_platform": best_sell.platform,
            "buy_price": best_buy.ask,
            "sell_price": best_sell.bid,
            "spread": spread,
            "spread_percentage": spread_percentage,
            "timestamp": datetime.utcnow()
        }
    
    async def get_price_trend(self, symbol: str, minutes: int = 10) -> Optional[Dict[str, Any]]:
        """Analyse la tendance des prix sur une période"""
        if symbol not in self.price_history:
            return None
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_data = [
            data for data in self.price_history[symbol]
            if data.timestamp > cutoff_time
        ]
        
        if len(recent_data) < 3:
            return None
        
        # Calculer la tendance
        prices = [data.price for data in recent_data if data.price > 0]
        if len(prices) < 3:
            return None
        
        # Régression linéaire simple
        n = len(prices)
        x = list(range(n))
        y = prices
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculer la volatilité
        mean_price = statistics.mean(prices)
        variance = statistics.variance(prices) if len(prices) > 1 else 0
        volatility = (variance ** 0.5) / mean_price if mean_price > 0 else 0
        
        return {
            "symbol": symbol,
            "period_minutes": minutes,
            "data_points": len(recent_data),
            "slope": slope,
            "intercept": intercept,
            "volatility": volatility,
            "price_change": (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0,
            "current_price": prices[-1],
            "timestamp": datetime.utcnow()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du monitoring"""
        return {
            **self.stats,
            "is_running": self.is_running,
            "symbols_monitored": len(self.price_cache),
            "total_platforms": sum(len(platforms) for platforms in self.price_cache.values()),
            "active_alerts": len(self.alerts),
            "cache_size": sum(len(platforms) for platforms in self.price_cache.values())
        }
    
    def get_recent_alerts(self, limit: int = 10) -> List[PriceAlert]:
        """Retourne les alertes récentes"""
        return sorted(
            self.alerts,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]
    
    def get_price_summary(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retourne un résumé des prix pour un symbole"""
        if symbol not in self.price_cache:
            return None
        
        platform_prices = self.price_cache[symbol]
        if not platform_prices:
            return None
        
        prices = [data.price for data in platform_prices.values() if data.price > 0]
        if not prices:
            return None
        
        return {
            "symbol": symbol,
            "platforms_count": len(platform_prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": statistics.mean(prices),
            "median_price": statistics.median(prices),
            "price_std": statistics.stdev(prices) if len(prices) > 1 else 0,
            "last_update": max(data.timestamp for data in platform_prices.values()),
            "timestamp": datetime.utcnow()
        }


# Instance globale du moniteur de prix
price_monitor = PriceMonitor()