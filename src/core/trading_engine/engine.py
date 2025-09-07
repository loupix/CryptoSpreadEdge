"""
Moteur de trading haute fréquence principal
"""

import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..market_data.market_data_manager import MarketDataManager
from ..order_management.order_manager import OrderManager
from ..risk_management.risk_manager import RiskManager
from ...portfolio.portfolio_service import portfolio_aggregator
from ...portfolio.optimizer import optimizer
from ...portfolio.portfolio_service import portfolio_aggregator


class TradingState(Enum):
    """États du moteur de trading"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class TradingConfig:
    """Configuration du moteur de trading"""
    max_positions: int = 10
    max_daily_loss: float = 1000.0
    max_position_size: float = 10000.0
    trading_enabled: bool = True
    risk_management_enabled: bool = True
    # Rebalance automatique
    rebalance_enabled: bool = True
    rebalance_interval_seconds: int = 300
    rebalance_method: str = "rp"  # "mv" ou "rp"
    rebalance_min_weight: float = 0.0
    rebalance_max_weight: float = 0.3
    rebalance_target_leverage: float = 1.0
    rebalance_risk_aversion: float = 3.0
    rebalance_trade_threshold_value: float = 100.0  # Valeur minimale d'ordre
    rebalance_dry_run: bool = False
    rebalance_max_orders_per_cycle: int = 10
    rebalance_per_exchange_cap_value: float = 0.0  # 0 = désactivé
    rebalance_use_real_covariance: bool = False
    # Coûts et contraintes d'exécution
    rebalance_fee_rate: float = 0.001  # 10 bps
    rebalance_slippage_bps: float = 10.0  # 10 bps
    rebalance_min_order_notional: float = 10.0
    # Vol target et backoff
    rebalance_vol_target_enabled: bool = False
    rebalance_vol_target: float = 0.0  # p.ex. 0.01 = 1%/période
    rebalance_backoff_enabled: bool = False
    rebalance_backoff_multiplier: float = 2.0
    rebalance_backoff_max_interval: int = 3600
    # Export métriques
    rebalance_prometheus_enabled: bool = False
    rebalance_prometheus_port: int = 8001


class TradingEngine:
    """
    Moteur de trading haute fréquence principal
    
    Gère l'exécution des stratégies, la gestion des ordres
    et la coordination entre les différents composants.
    """
    
    def __init__(
        self,
        market_data_manager: MarketDataManager,
        order_manager: OrderManager,
        risk_manager: RiskManager,
        config: TradingConfig
    ):
        self.market_data_manager = market_data_manager
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.config = config

        # Overrides via variables d'environnement (CSE_REBALANCE_*)
        try:
            # Charger un fichier .env si spécifié
            env_file = os.environ.get('CSE_REBALANCE_ENV_FILE')
            if env_file and os.path.isfile(env_file):
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue
                            if '=' in line:
                                k, v = line.split('=', 1)
                                os.environ[k.strip()] = v.strip()
                except Exception:
                    pass

            if 'CSE_REBALANCE_ENABLED' in os.environ:
                self.config.rebalance_enabled = os.environ.get('CSE_REBALANCE_ENABLED', '1') not in ['0', 'false', 'False']
            if 'CSE_REBALANCE_INTERVAL' in os.environ:
                self.config.rebalance_interval_seconds = int(os.environ.get('CSE_REBALANCE_INTERVAL', self.config.rebalance_interval_seconds))
            if 'CSE_REBALANCE_METHOD' in os.environ:
                self.config.rebalance_method = str(os.environ.get('CSE_REBALANCE_METHOD', self.config.rebalance_method))
            if 'CSE_REBALANCE_MIN_WEIGHT' in os.environ:
                self.config.rebalance_min_weight = float(os.environ.get('CSE_REBALANCE_MIN_WEIGHT', self.config.rebalance_min_weight))
            if 'CSE_REBALANCE_MAX_WEIGHT' in os.environ:
                self.config.rebalance_max_weight = float(os.environ.get('CSE_REBALANCE_MAX_WEIGHT', self.config.rebalance_max_weight))
            if 'CSE_REBALANCE_LEVERAGE' in os.environ:
                self.config.rebalance_target_leverage = float(os.environ.get('CSE_REBALANCE_LEVERAGE', self.config.rebalance_target_leverage))
            if 'CSE_REBALANCE_RISK_AVERSION' in os.environ:
                self.config.rebalance_risk_aversion = float(os.environ.get('CSE_REBALANCE_RISK_AVERSION', self.config.rebalance_risk_aversion))
            if 'CSE_REBALANCE_TRADE_THRESHOLD' in os.environ:
                self.config.rebalance_trade_threshold_value = float(os.environ.get('CSE_REBALANCE_TRADE_THRESHOLD', self.config.rebalance_trade_threshold_value))
            if 'CSE_REBALANCE_DRY_RUN' in os.environ:
                self.config.rebalance_dry_run = os.environ.get('CSE_REBALANCE_DRY_RUN', '0') not in ['0', 'false', 'False']
            if 'CSE_REBALANCE_MAX_ORDERS' in os.environ:
                self.config.rebalance_max_orders_per_cycle = int(os.environ.get('CSE_REBALANCE_MAX_ORDERS', self.config.rebalance_max_orders_per_cycle))
            if 'CSE_REBALANCE_PER_EXCHANGE_CAP' in os.environ:
                self.config.rebalance_per_exchange_cap_value = float(os.environ.get('CSE_REBALANCE_PER_EXCHANGE_CAP', self.config.rebalance_per_exchange_cap_value))
            if 'CSE_REBALANCE_USE_REAL_COV' in os.environ:
                self.config.rebalance_use_real_covariance = os.environ.get('CSE_REBALANCE_USE_REAL_COV', '0') not in ['0','false','False']
            if 'CSE_REBALANCE_FEE_RATE' in os.environ:
                self.config.rebalance_fee_rate = float(os.environ.get('CSE_REBALANCE_FEE_RATE', self.config.rebalance_fee_rate))
            if 'CSE_REBALANCE_SLIPPAGE_BPS' in os.environ:
                self.config.rebalance_slippage_bps = float(os.environ.get('CSE_REBALANCE_SLIPPAGE_BPS', self.config.rebalance_slippage_bps))
            if 'CSE_REBALANCE_MIN_NOTIONAL' in os.environ:
                self.config.rebalance_min_order_notional = float(os.environ.get('CSE_REBALANCE_MIN_NOTIONAL', self.config.rebalance_min_order_notional))
            if 'CSE_REBALANCE_VOL_TARGET_ENABLED' in os.environ:
                self.config.rebalance_vol_target_enabled = os.environ.get('CSE_REBALANCE_VOL_TARGET_ENABLED', '0') not in ['0','false','False']
            if 'CSE_REBALANCE_VOL_TARGET' in os.environ:
                self.config.rebalance_vol_target = float(os.environ.get('CSE_REBALANCE_VOL_TARGET', self.config.rebalance_vol_target))
            if 'CSE_REBALANCE_BACKOFF_ENABLED' in os.environ:
                self.config.rebalance_backoff_enabled = os.environ.get('CSE_REBALANCE_BACKOFF_ENABLED', '0') not in ['0','false','False']
            if 'CSE_REBALANCE_BACKOFF_MULT' in os.environ:
                self.config.rebalance_backoff_multiplier = float(os.environ.get('CSE_REBALANCE_BACKOFF_MULT', self.config.rebalance_backoff_multiplier))
            if 'CSE_REBALANCE_BACKOFF_MAX' in os.environ:
                self.config.rebalance_backoff_max_interval = int(os.environ.get('CSE_REBALANCE_BACKOFF_MAX', self.config.rebalance_backoff_max_interval))
            if 'CSE_REBALANCE_PROMETHEUS' in os.environ:
                self.config.rebalance_prometheus_enabled = os.environ.get('CSE_REBALANCE_PROMETHEUS', '0') not in ['0','false','False']
        except Exception as _:
            # Ne pas bloquer le démarrage si parsing env échoue
            pass
        
        self.state = TradingState.STOPPED
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._tasks: List[asyncio.Task] = []
        # Compteurs de rebalance (cycle courant)
        self._rebalance_stats = {
            'orders_placed': 0,
            'orders_skipped_threshold': 0,
            'orders_skipped_min_notional': 0,
            'orders_skipped_cap': 0,
            'estimated_costs_total': 0.0,
        }
        self._rebalance_current_interval = self.config.rebalance_interval_seconds
        
    async def start(self) -> None:
        """Démarre le moteur de trading"""
        if self.state != TradingState.STOPPED:
            raise RuntimeError(f"Le moteur est déjà en état {self.state}")
            
        self.logger.info("Démarrage du moteur de trading...")
        self.state = TradingState.STARTING
        
        try:
            # Initialiser les composants
            await self.market_data_manager.start()
            await self.order_manager.start()
            await self.risk_manager.start()
            
            # Démarrer les tâches principales
            self._running = True
            self._tasks = [
                asyncio.create_task(self._main_loop()),
                asyncio.create_task(self._risk_monitoring_loop()),
                asyncio.create_task(self._order_processing_loop()),
                asyncio.create_task(self._rebalance_loop())
            ]
            
            self.state = TradingState.RUNNING
            self.logger.info("Moteur de trading démarré avec succès")
            # Démarrer serveur de métriques si activé
            if self.config.rebalance_prometheus_enabled:
                try:
                    self._start_metrics_server()
                except Exception:
                    self.logger.warning("Impossible de démarrer le serveur de métriques")
            
        except Exception as e:
            self.state = TradingState.ERROR
            self.logger.error(f"Erreur lors du démarrage: {e}")
            raise
    
    async def stop(self) -> None:
        """Arrête le moteur de trading"""
        if self.state not in [TradingState.RUNNING, TradingState.PAUSED]:
            return
            
        self.logger.info("Arrêt du moteur de trading...")
        self.state = TradingState.STOPPING
        
        # Arrêter les tâches
        self._running = False
        for task in self._tasks:
            task.cancel()
        
        # Attendre que les tâches se terminent
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Arrêter les composants
        await self.market_data_manager.stop()
        await self.order_manager.stop()
        await self.risk_manager.stop()
        
        self.state = TradingState.STOPPED
        self.logger.info("Moteur de trading arrêté")
        # Arrêter serveur métriques si démarré
        if hasattr(self, '_metrics_server') and self._metrics_server is not None:
            try:
                self._metrics_server.shutdown()
                self._metrics_server.server_close()
            except Exception:
                pass
            self._metrics_server = None
    
    async def pause(self) -> None:
        """Met en pause le moteur de trading"""
        if self.state != TradingState.RUNNING:
            return
            
        self.state = TradingState.PAUSED
        self.logger.info("Moteur de trading en pause")
    
    async def resume(self) -> None:
        """Reprend le moteur de trading"""
        if self.state != TradingState.PAUSED:
            return
            
        self.state = TradingState.RUNNING
        self.logger.info("Moteur de trading repris")
    
    async def _main_loop(self) -> None:
        """Boucle principale du moteur de trading"""
        while self._running:
            try:
                if self.state == TradingState.RUNNING:
                    # Traiter les signaux de trading
                    await self._process_trading_signals()
                    
                    # Mettre à jour les positions
                    await self._update_positions()
                
                await asyncio.sleep(0.001)  # 1ms de latence
                
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle principale: {e}")
                await asyncio.sleep(0.1)
    
    async def _risk_monitoring_loop(self) -> None:
        """Boucle de monitoring des risques"""
        while self._running:
            try:
                if self.state in [TradingState.RUNNING, TradingState.PAUSED]:
                    # Vérifier les limites de risque
                    await self.risk_manager.check_limits()
                    
                    # Mettre à jour les métriques de risque
                    await self.risk_manager.update_metrics()
                
                await asyncio.sleep(0.1)  # 100ms
                
            except Exception as e:
                self.logger.error(f"Erreur dans le monitoring des risques: {e}")
                await asyncio.sleep(0.1)
    
    async def _order_processing_loop(self) -> None:
        """Boucle de traitement des ordres"""
        while self._running:
            try:
                if self.state == TradingState.RUNNING:
                    # Traiter les ordres en attente
                    await self.order_manager.process_pending_orders()
                    
                    # Mettre à jour le statut des ordres
                    await self.order_manager.update_order_status()
                
                await asyncio.sleep(0.01)  # 10ms
                
            except Exception as e:
                self.logger.error(f"Erreur dans le traitement des ordres: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_trading_signals(self) -> None:
        """Traite les signaux de trading"""
        try:
            # Récupérer les signaux des stratégies d'IA
            signals = await self._get_trading_signals()
            
            for signal in signals:
                # Vérifier les risques avant d'exécuter
                if await self.risk_manager.is_signal_safe(signal):
                    # Créer l'ordre basé sur le signal
                    order = await self._create_order_from_signal(signal)
                    if order:
                        # Placer l'ordre via le gestionnaire d'ordres
                        await self.order_manager.place_order(order)
                        self.logger.info(f"Ordre placé basé sur signal: {signal.symbol}")
                else:
                    self.logger.warning(f"Signal rejeté par gestion des risques: {signal.symbol}")
        
        except Exception as e:
            self.logger.error(f"Erreur traitement signaux: {e}")
    
    async def _get_trading_signals(self) -> List[Any]:
        """Récupère les signaux de trading des stratégies"""
        signals = []
        
        try:
            # Récupérer les données de marché
            market_data = await self.market_data_manager.get_latest_data()
            
            # Analyser les données avec les stratégies d'IA
            # TODO: Intégrer avec les modèles d'IA une fois implémentés
            # Pour l'instant, on simule des signaux basiques
            
            for symbol, data in market_data.items():
                if data and hasattr(data, 'ticker'):
                    # Logique simple de détection de tendance
                    if await self._detect_trend_signal(symbol, data):
                        signal = {
                            'symbol': symbol,
                            'action': 'buy',  # ou 'sell'
                            'confidence': 0.8,
                            'timestamp': datetime.utcnow()
                        }
                        signals.append(signal)
        
        except Exception as e:
            self.logger.error(f"Erreur récupération signaux: {e}")
        
        return signals
    
    async def _detect_trend_signal(self, symbol: str, data: Any) -> bool:
        """Détecte un signal de tendance basique"""
        try:
            # Logique simplifiée pour détecter des tendances
            # Dans une implémentation réelle, on utiliserait des indicateurs techniques
            
            if not data or not hasattr(data, 'ticker'):
                return False
            
            # Vérifier si le prix a augmenté significativement
            # (logique simplifiée - à remplacer par de vrais indicateurs)
            price_change = getattr(data.ticker, 'price_change_percent', 0)
            
            # Signal d'achat si augmentation > 2%
            return price_change > 2.0
        
        except Exception as e:
            self.logger.error(f"Erreur détection tendance {symbol}: {e}")
            return False
    
    async def _create_order_from_signal(self, signal: Dict[str, Any]) -> Optional[Any]:
        """Crée un ordre basé sur un signal"""
        try:
            from ..connectors.common.market_data_types import Order, OrderSide, OrderType
            
            # Calculer la quantité basée sur la gestion des risques
            quantity = await self._calculate_order_quantity(signal)
            if quantity <= 0:
                return None
            
            # Créer l'ordre
            order = Order(
                symbol=signal['symbol'],
                side=OrderSide.BUY if signal['action'] == 'buy' else OrderSide.SELL,
                order_type=OrderType.MARKET,  # Ordre au marché pour l'instant
                quantity=quantity,
                timestamp=datetime.utcnow()
            )
            
            return order
        
        except Exception as e:
            self.logger.error(f"Erreur création ordre: {e}")
            return None
    
    async def _calculate_order_quantity(self, signal: Dict[str, Any]) -> float:
        """Calcule la quantité d'un ordre basée sur la gestion des risques"""
        try:
            # Récupérer le prix actuel
            market_data = await self.market_data_manager.get_latest_data()
            symbol_data = market_data.get(signal['symbol'])
            
            if not symbol_data or not hasattr(symbol_data, 'ticker'):
                return 0.0
            
            current_price = symbol_data.ticker.price
            if current_price <= 0:
                return 0.0
            
            # Calculer la taille de position basée sur les limites de risque
            max_position_value = self.config.max_position_size
            confidence_factor = signal.get('confidence', 0.5)
            
            # Ajuster la taille selon la confiance
            position_value = max_position_value * confidence_factor
            
            # Calculer la quantité
            quantity = position_value / current_price
            
            return round(quantity, 6)  # Arrondir à 6 décimales
        
        except Exception as e:
            self.logger.error(f"Erreur calcul quantité: {e}")
            return 0.0
    
    async def _update_positions(self) -> None:
        """Met à jour les positions"""
        try:
            # Récupérer les positions actuelles depuis les exchanges
            positions = await self._get_current_positions()
            
            # Mettre à jour les positions dans le gestionnaire de risques
            for position in positions:
                await self.risk_manager.update_position(position)
            
            # Vérifier les positions pour des actions nécessaires
            await self._check_position_actions(positions)
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour positions: {e}")
    
    async def _get_current_positions(self) -> List[Any]:
        """Récupère les positions actuelles depuis tous les exchanges"""
        positions = []
        
        try:
            # Récupérer les positions depuis tous les connecteurs
            from ..connectors.connector_factory import connector_factory
            
            for exchange_id, connector in connector_factory.get_all_connectors().items():
                if connector.is_connected():
                    try:
                        exchange_positions = await connector.get_positions()
                        for position in exchange_positions:
                            position.source = exchange_id
                            positions.append(position)
                    except Exception as e:
                        self.logger.debug(f"Erreur récupération positions {exchange_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Erreur récupération positions: {e}")
        
        return positions
    
    async def _check_position_actions(self, positions: List[Any]) -> None:
        """Vérifie les positions pour des actions nécessaires"""
        try:
            for position in positions:
                # Vérifier les positions avec des pertes importantes
                if hasattr(position, 'unrealized_pnl') and position.unrealized_pnl < -1000:
                    self.logger.warning(f"Position avec perte importante: {position.symbol} = {position.unrealized_pnl}")
                
                # Vérifier les positions qui approchent des limites
                if hasattr(position, 'quantity') and abs(position.quantity) > 0:
                    # Calculer la valeur de la position
                    market_data = await self.market_data_manager.get_latest_data()
                    symbol_data = market_data.get(position.symbol)
                    
                    if symbol_data and hasattr(symbol_data, 'ticker'):
                        position_value = abs(position.quantity) * symbol_data.ticker.price
                        
                        # Vérifier si la position dépasse les limites
                        if position_value > self.config.max_position_size:
                            self.logger.warning(f"Position dépasse limite: {position.symbol} = {position_value}")
        
        except Exception as e:
            self.logger.error(f"Erreur vérification actions positions: {e}")

    async def _rebalance_loop(self) -> None:
        """Boucle de rebalance automatique basée sur l'optimiseur de portefeuille."""
        while self._running:
            try:
                if not self.config.rebalance_enabled or self.state != TradingState.RUNNING:
                    await asyncio.sleep(1.0)
                    continue

                # Rafraîchir le portefeuille agrégé
                await portfolio_aggregator.refresh()
                consolidated = portfolio_aggregator.consolidate_positions()

                # Construire un lookup de prix depuis le market data manager
                market_data = await self.market_data_manager.get_latest_data()
                price_lookup: Dict[str, float] = {}
                for sym, data in market_data.items():
                    if data and hasattr(data, 'ticker') and hasattr(data.ticker, 'price'):
                        price_lookup[str(sym).upper()] = float(data.ticker.price)

                # Si pas de données, attendre
                if not consolidated or not price_lookup:
                    await asyncio.sleep(self.config.rebalance_interval_seconds)
                    continue

                # Construire mu/cov (réel ou naïf)
                symbols = list(consolidated.keys())
                expected_returns = {s: 0.0 for s in symbols}
                if self.config.rebalance_use_real_covariance:
                    try:
                        cov_map = await portfolio_aggregator.compute_price_covariance(symbols, points=300)
                    except Exception:
                        cov_map = {}
                else:
                    cov_map = {}
                    for si in symbols:
                        for sj in symbols:
                            cov_map[(si, sj)] = 0.0 if si != sj else 1.0

                # Option: prioriser par volatilité (si cov dispo)
                symbol_order = symbols
                if cov_map:
                    try:
                        vol = {s: (cov_map.get((s, s), 0.0)) ** 0.5 for s in symbols}
                        symbol_order = sorted(symbols, key=lambda s: vol.get(s, 0.0), reverse=True)
                    except Exception:
                        symbol_order = symbols

                # Calculer poids cibles (avec option vol target)
                if self.config.rebalance_method == "mv":
                    target_weights = optimizer.mean_variance_weights(
                        expected_returns=expected_returns,
                        covariance_matrix=cov_map,
                        risk_aversion=self.config.rebalance_risk_aversion,
                        min_weight=self.config.rebalance_min_weight,
                        max_weight=self.config.rebalance_max_weight,
                        target_leverage=self.config.rebalance_target_leverage,
                    )
                else:
                    target_weights = optimizer.risk_parity_weights(
                        covariance_matrix=cov_map,
                        min_weight=self.config.rebalance_min_weight,
                        max_weight=self.config.rebalance_max_weight,
                        target_leverage=self.config.rebalance_target_leverage,
                    )

                # Ajuster leverage pour viser une volatilité cible si activé et cov disponible
                if self.config.rebalance_vol_target_enabled and cov_map:
                    try:
                        syms = list(target_weights.keys())
                        if syms:
                            # Construire vecteur des poids et matrice cov
                            import numpy as _np
                            w = _np.array([target_weights[s] for s in syms], dtype=float)
                            cov_mat = _np.array([[cov_map.get((i, j), cov_map.get((j, i), 0.0)) for j in syms] for i in syms], dtype=float)
                            port_var = float(w.T.dot(cov_mat).dot(w))
                            port_vol = port_var ** 0.5 if port_var > 0 else 0.0
                            if port_vol > 0 and self.config.rebalance_vol_target > 0:
                                scale = self.config.rebalance_vol_target / port_vol
                                # rescaler et recouper min/max
                                w = w * scale
                                # clip et renormaliser à leverage cible
                                w = _np.clip(w, self.config.rebalance_min_weight, self.config.rebalance_max_weight)
                                s = w.sum()
                                if s > 0:
                                    w = w * (self.config.rebalance_target_leverage / s)
                                for i, s in enumerate(syms):
                                    target_weights[s] = float(w[i])
                    except Exception:
                        pass

                # Calculer valeur totale estimée et expositions actuelles
                total_equity = 0.0
                current_value_by_sym: Dict[str, float] = {}
                for sym, info in consolidated.items():
                    price = float(price_lookup.get(sym.upper(), 0.0))
                    qty = float(info.get('quantity', 0.0))
                    val = qty * price
                    current_value_by_sym[sym] = val
                    total_equity += val

                if total_equity <= 0:
                    await asyncio.sleep(self.config.rebalance_interval_seconds)
                    continue

                # Déterminer écarts et créer ordres seuilés
                orders_placed = 0
                # Exposition par exchange (approx): somme des valeurs symboles dont sources contiennent l'exchange
                exposure_by_exchange: Dict[str, float] = {}
                for sym, info in consolidated.items():
                    price = float(price_lookup.get(sym.upper(), 0.0))
                    if price <= 0:
                        continue
                    qty = float(info.get('quantity', 0.0))
                    val = qty * price
                    for ex, ex_qty in info.get('exchanges', {}).items():
                        share = 0.0
                        if qty > 0:
                            share = (ex_qty / qty) * val
                        exposure_by_exchange[ex] = exposure_by_exchange.get(ex, 0.0) + max(share, 0.0)

                # Réinitialiser stats cycle
                self._rebalance_stats.update({
                    'orders_placed': 0,
                    'orders_skipped_threshold': 0,
                    'orders_skipped_min_notional': 0,
                    'orders_skipped_cap': 0,
                    'estimated_costs_total': 0.0,
                })

                for sym in symbol_order:
                    tgt_w = target_weights.get(sym, 0.0)
                    price = float(price_lookup.get(sym.upper(), 0.0))
                    if price <= 0:
                        continue
                    target_value = tgt_w * total_equity
                    delta_value = target_value - current_value_by_sym.get(sym, 0.0)

                    # Ignorer petits ordres
                    if abs(delta_value) < self.config.rebalance_trade_threshold_value:
                        continue

                    qty = abs(delta_value) / price

                    # Respecter limite d'ordres par cycle
                    if self.config.rebalance_max_orders_per_cycle > 0 and orders_placed >= self.config.rebalance_max_orders_per_cycle:
                        break

                    # Respecter plafond par exchange si actif
                    if self.config.rebalance_per_exchange_cap_value > 0:
                        # Choisir un exchange candidat: utiliser la première source si connue
                        target_exchange = None
                        # consolidated[sym] contient 'sources' si présent
                        if sym in consolidated and 'sources' in consolidated[sym] and consolidated[sym]['sources']:
                            target_exchange = consolidated[sym]['sources'][0]
                        if target_exchange:
                            current_exposure = exposure_by_exchange.get(target_exchange, 0.0)
                            projected = current_exposure + max(delta_value, 0.0)
                            if projected > self.config.rebalance_per_exchange_cap_value:
                                self._rebalance_stats['orders_skipped_cap'] += 1
                                continue

                    # Vérifier la taille minimale (notional)
                    notional = qty * price
                    if notional < self.config.rebalance_min_order_notional:
                        self._rebalance_stats['orders_skipped_min_notional'] += 1
                        continue

                    # Estimer coûts: fees + slippage
                    slippage = abs(self.config.rebalance_slippage_bps) / 10000.0
                    fee_rate = max(self.config.rebalance_fee_rate, 0.0)
                    est_fees = fee_rate * notional
                    est_slippage_cost = qty * (price * slippage)
                    est_total_cost = est_fees + est_slippage_cost

                    # Ne pas trader si l'écart cible ne couvre pas les coûts et le seuil
                    if abs(delta_value) <= (self.config.rebalance_trade_threshold_value + est_total_cost):
                        self._rebalance_stats['orders_skipped_threshold'] += 1
                        continue

                    # Construire et placer l'ordre (simplifié: MARKET, côté selon signe)
                    try:
                        from ..connectors.common.market_data_types import Order, OrderSide, OrderType
                        order = Order(
                            symbol=sym,
                            side=OrderSide.BUY if delta_value > 0 else OrderSide.SELL,
                            order_type=OrderType.MARKET,
                            quantity=qty,
                            timestamp=datetime.utcnow()
                        )
                        self._rebalance_stats['estimated_costs_total'] += est_total_cost
                        if self.config.rebalance_dry_run:
                            self.logger.info(f"[DRY-RUN] Rebalance: {order.side.value} {qty:.6f} {sym} @~{price:.4f}")
                        else:
                            await self.order_manager.place_order(order)
                            self.logger.info(f"Rebalance: {order.side.value} {qty:.6f} {sym} @~{price:.4f}")
                            orders_placed += 1
                    except Exception as place_exc:
                        self.logger.warning(f"Échec placement ordre de rebalance {sym}: {place_exc}")

                # Log de synthèse du cycle
                try:
                    self.logger.info(
                        f"Rebalance cycle: placed={orders_placed} "
                        f"skipped_threshold={self._rebalance_stats['orders_skipped_threshold']} "
                        f"skipped_min_notional={self._rebalance_stats['orders_skipped_min_notional']} "
                        f"skipped_cap={self._rebalance_stats['orders_skipped_cap']} "
                        f"est_costs={self._rebalance_stats['estimated_costs_total']:.2f}"
                    )
                except Exception:
                    pass

                # Backoff dynamique si beaucoup d'ordres ignorés
                interval = self.config.rebalance_interval_seconds
                if self.config.rebalance_backoff_enabled:
                    skipped = (
                        self._rebalance_stats['orders_skipped_threshold'] +
                        self._rebalance_stats['orders_skipped_min_notional'] +
                        self._rebalance_stats['orders_skipped_cap']
                    )
                    if skipped > 0 and orders_placed == 0:
                        self._rebalance_current_interval = min(
                            int(self._rebalance_current_interval * self.config.rebalance_backoff_multiplier),
                            self.config.rebalance_backoff_max_interval
                        )
                    else:
                        self._rebalance_current_interval = self.config.rebalance_interval_seconds
                    interval = self._rebalance_current_interval

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Erreur rebalance loop: {e}")
                await asyncio.sleep(self.config.rebalance_interval_seconds)
    
    async def get_portfolio_snapshot(self) -> Dict[str, Any]:
        """Retourne un snapshot agrégé du portefeuille (balances + positions)."""
        try:
            await portfolio_aggregator.refresh()
            consolidated = portfolio_aggregator.consolidate_positions()
            balances = {
                ex: [b.__dict__ for b in bl]
                for ex, bl in portfolio_aggregator.get_balances().items()
            }
            return {
                'positions': consolidated,
                'balances': balances,
            }
        except Exception as e:
            self.logger.error(f"Erreur snapshot portefeuille: {e}")
            return {'positions': {}, 'balances': {}}
    
    def get_status(self) -> Dict:
        """Retourne le statut du moteur"""
        return {
            "state": self.state.value,
            "running": self._running,
            "config": {
                "max_positions": self.config.max_positions,
                "max_daily_loss": self.config.max_daily_loss,
                "trading_enabled": self.config.trading_enabled,
                "risk_management_enabled": self.config.risk_management_enabled
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    # --------- Prometheus metrics ---------
    def _build_metrics_text(self) -> str:
        lines = [
            "# HELP cryptospreadedge_rebalance_orders_placed Number of rebalance orders placed in last cycle",
            "# TYPE cryptospreadedge_rebalance_orders_placed gauge",
            f"cryptospreadedge_rebalance_orders_placed {self._rebalance_stats['orders_placed']}",
            "# HELP cryptospreadedge_rebalance_orders_skipped_threshold Orders skipped due to threshold+costs",
            "# TYPE cryptospreadedge_rebalance_orders_skipped_threshold gauge",
            f"cryptospreadedge_rebalance_orders_skipped_threshold {self._rebalance_stats['orders_skipped_threshold']}",
            "# HELP cryptospreadedge_rebalance_orders_skipped_min_notional Orders skipped due to min notional",
            "# TYPE cryptospreadedge_rebalance_orders_skipped_min_notional gauge",
            f"cryptospreadedge_rebalance_orders_skipped_min_notional {self._rebalance_stats['orders_skipped_min_notional']}",
            "# HELP cryptospreadedge_rebalance_orders_skipped_cap Orders skipped due to per-exchange cap",
            "# TYPE cryptospreadedge_rebalance_orders_skipped_cap gauge",
            f"cryptospreadedge_rebalance_orders_skipped_cap {self._rebalance_stats['orders_skipped_cap']}",
            "# HELP cryptospreadedge_rebalance_estimated_costs_total Estimated total costs of placed orders in last cycle",
            "# TYPE cryptospreadedge_rebalance_estimated_costs_total gauge",
            f"cryptospreadedge_rebalance_estimated_costs_total {self._rebalance_stats['estimated_costs_total']}",
            "# HELP cryptospreadedge_rebalance_interval_seconds Current rebalance interval (with backoff)",
            "# TYPE cryptospreadedge_rebalance_interval_seconds gauge",
            f"cryptospreadedge_rebalance_interval_seconds {self._rebalance_current_interval}",
        ]
        return "\n".join(lines) + "\n"

    def _start_metrics_server(self) -> None:
        if hasattr(self, '_metrics_server') and self._metrics_server is not None:
            return

        engine_ref = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # type: ignore[override]
                if self.path == "/metrics":
                    body = engine_ref._build_metrics_text().encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; version=0.0.4")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                return

        addr = ("0.0.0.0", int(self.config.rebalance_prometheus_port))
        self._metrics_server = HTTPServer(addr, Handler)

        def serve():
            try:
                self._metrics_server.serve_forever()
            except Exception:
                pass

        t = threading.Thread(target=serve, daemon=True)
        t.start()
        self._metrics_thread = t
        self.logger.info(f"Metrics server listening on :{self.config.rebalance_prometheus_port}")