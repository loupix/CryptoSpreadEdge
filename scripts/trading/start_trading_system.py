"""
Script de démarrage du système de trading complet CryptoSpreadEdge
"""

import sys
import asyncio
import logging
import signal
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from datetime import datetime, timedelta

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.indicators.base_indicator import IndicatorComposite, indicator_manager
from src.indicators.technical_indicators import (
    MovingAverageIndicator, RSIIndicator, MACDIndicator, 
    BollingerBandsIndicator, StochasticIndicator, VolumeIndicator, ATRIndicator
)
from src.indicators.advanced_indicators import (
    IchimokuIndicator, WilliamsRIndicator, MLPredictionIndicator, 
    SentimentIndicator, VolatilityIndicator
)
from src.prediction.signal_generator import (
    SignalGenerator, TrendFollowingStrategy, MeanReversionStrategy, 
    MLPredictionStrategy
)
from src.prediction.ml_predictor import MLPredictor
from src.position.position_manager import PositionManager
from src.arbitrage.arbitrage_engine import arbitrage_engine
from src.arbitrage.price_monitor import price_monitor
from src.connectors.connector_factory import connector_factory
from src.data_sources.data_aggregator import data_aggregator
from config.api_keys_manager import api_keys_manager


class TradingSystem:
    """Système de trading principal"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.is_running = False
        self.tasks = []
        
        # Composants principaux
        self.indicator_composite = None
        self.signal_generator = None
        self.ml_predictor = None
        self.position_manager = None
        
        # Configuration
        self.symbols = ["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"]
        self.timeframe = "1h"
        self.update_interval = 60  # secondes
    
    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/trading_system.log')
            ]
        )
    
    async def start(self, mode: str = "live"):
        """Démarre le système de trading"""
        try:
            self.logger.info(f"Démarrage du système de trading en mode {mode}")
            self.is_running = True
            
            # Créer le répertoire de logs
            Path("logs").mkdir(exist_ok=True)
            
            # Initialiser les composants
            await self._initialize_components()
            
            # Démarrer les services
            await self._start_services()
            
            # Afficher le statut
            await self._show_status()
            
            # Démarrer la boucle principale
            await self._main_loop()
        
        except Exception as e:
            self.logger.error(f"Erreur démarrage système: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Arrête le système de trading"""
        self.logger.info("Arrêt du système de trading")
        self.is_running = False
        
        # Arrêter tous les services
        await self._stop_services()
        
        # Annuler toutes les tâches
        for task in self.tasks:
            task.cancel()
        
        # Attendre que toutes les tâches se terminent
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.logger.info("Système de trading arrêté")
    
    async def _initialize_components(self):
        """Initialise tous les composants"""
        try:
            self.logger.info("Initialisation des composants...")
            
            # Vérifier les clés API
            api_summary = api_keys_manager.get_summary()
            if api_summary["platforms_ready_for_trading"] == 0:
                self.logger.warning("Aucune plateforme prête pour le trading")
                self.logger.info("Configurez vos clés API avec: python scripts/setup/configure_platforms.py")
            
            # Initialiser l'agrégateur de données
            await data_aggregator.initialize_connectors()
            
            # Initialiser le composite d'indicateurs
            self._initialize_indicators()
            
            # Initialiser le générateur de signaux
            self._initialize_signal_generator()
            
            # Initialiser le prédicteur ML
            self._initialize_ml_predictor()
            
            # Initialiser le gestionnaire de positions
            self._initialize_position_manager()
            
            self.logger.info("Composants initialisés avec succès")
        
        except Exception as e:
            self.logger.error(f"Erreur initialisation composants: {e}")
            raise
    
    def _initialize_indicators(self):
        """Initialise les indicateurs"""
        self.logger.info("Initialisation des indicateurs...")
        
        self.indicator_composite = IndicatorComposite("TradingIndicators")
        
        # Indicateurs techniques
        indicators = [
            MovingAverageIndicator("SMA_20", "SMA", 20),
            MovingAverageIndicator("SMA_50", "SMA", 50),
            MovingAverageIndicator("EMA_20", "EMA", 20),
            RSIIndicator("RSI_14", 14),
            MACDIndicator("MACD", 12, 26, 9),
            BollingerBandsIndicator("BB_20", 20, 2.0),
            StochasticIndicator("STOCH_14", 14, 3),
            VolumeIndicator("VOLUME_20", 20),
            ATRIndicator("ATR_14", 14)
        ]
        
        # Indicateurs avancés
        advanced_indicators = [
            IchimokuIndicator("ICHIMOKU", 9, 26, 52),
            WilliamsRIndicator("WILLIAMS_R", 14),
            VolatilityIndicator("VOLATILITY", 20)
        ]
        
        # Ajouter tous les indicateurs
        for indicator in indicators + advanced_indicators:
            self.indicator_composite.add_indicator(indicator)
        
        self.logger.info(f"Indicateurs initialisés: {len(indicators + advanced_indicators)}")
    
    def _initialize_signal_generator(self):
        """Initialise le générateur de signaux"""
        self.logger.info("Initialisation du générateur de signaux...")
        
        self.signal_generator = SignalGenerator("TradingSignalGenerator")
        
        # Ajouter les stratégies
        strategies = [
            TrendFollowingStrategy("TrendFollowing"),
            MeanReversionStrategy("MeanReversion"),
            MLPredictionStrategy("MLPrediction")
        ]
        
        for strategy in strategies:
            self.signal_generator.add_strategy(strategy)
        
        self.logger.info(f"Stratégies de signaux initialisées: {len(strategies)}")
    
    def _initialize_ml_predictor(self):
        """Initialise le prédicteur ML"""
        self.logger.info("Initialisation du prédicteur ML...")
        
        self.ml_predictor = MLPredictor("TradingMLPredictor")
        
        # Charger un modèle pré-entraîné si disponible
        try:
            self.ml_predictor.load_models("models/trading_models.pkl")
            self.logger.info("Modèles ML chargés depuis le fichier")
        except:
            self.logger.info("Aucun modèle pré-entraîné trouvé, entraînement requis")
    
    def _initialize_position_manager(self):
        """Initialise le gestionnaire de positions"""
        self.logger.info("Initialisation du gestionnaire de positions...")
        
        self.position_manager = PositionManager("TradingPositionManager")
        self.position_manager.set_portfolio_value(100000.0)  # 100k USD
        
        self.logger.info("Gestionnaire de positions initialisé")
    
    async def _start_services(self):
        """Démarre tous les services"""
        try:
            self.logger.info("Démarrage des services...")
            
            # Démarrer le monitoring des prix
            price_task = asyncio.create_task(price_monitor.start())
            self.tasks.append(price_task)
            
            # Démarrer le moteur d'arbitrage
            arbitrage_task = asyncio.create_task(arbitrage_engine.start())
            self.tasks.append(arbitrage_task)
            
            # Démarrer le système de trading
            trading_task = asyncio.create_task(self._trading_loop())
            self.tasks.append(trading_task)
            
            # Démarrer le monitoring du système
            monitoring_task = asyncio.create_task(self._monitor_system())
            self.tasks.append(monitoring_task)
            
            # Démarrer l'affichage des statistiques
            stats_task = asyncio.create_task(self._display_statistics())
            self.tasks.append(stats_task)
            
            self.logger.info("Services démarrés avec succès")
        
        except Exception as e:
            self.logger.error(f"Erreur démarrage services: {e}")
            raise
    
    async def _stop_services(self):
        """Arrête tous les services"""
        try:
            self.logger.info("Arrêt des services...")
            
            # Arrêter le moteur d'arbitrage
            await arbitrage_engine.stop()
            
            # Arrêter le monitoring des prix
            await price_monitor.stop()
            
            self.logger.info("Services arrêtés avec succès")
        
        except Exception as e:
            self.logger.error(f"Erreur arrêt services: {e}")
    
    async def _trading_loop(self):
        """Boucle principale de trading"""
        while self.is_running:
            try:
                # Traiter chaque symbole
                for symbol in self.symbols:
                    await self._process_symbol(symbol)
                
                await asyncio.sleep(self.update_interval)
            
            except Exception as e:
                self.logger.error(f"Erreur boucle de trading: {e}")
                await asyncio.sleep(30)
    
    async def _process_symbol(self, symbol: str):
        """Traite un symbole spécifique"""
        try:
            # Récupérer les données de marché
            market_data = await self._get_market_data(symbol)
            if not market_data or market_data.empty:
                return
            
            # Calculer les indicateurs
            indicator_values = self.indicator_composite.calculate_all(market_data)
            
            # Faire des prédictions ML
            ml_predictions = self.ml_predictor.predict_ensemble(market_data)
            
            # Ajouter les prédictions aux indicateurs
            if ml_predictions:
                # Créer des valeurs d'indicateur à partir des prédictions
                from src.indicators.base_indicator import IndicatorValue
                ml_values = [
                    IndicatorValue(
                        value=pred.predicted_change,
                        timestamp=pred.timestamp,
                        confidence=pred.confidence,
                        metadata=pred.metadata
                    )
                    for pred in ml_predictions
                ]
                indicator_values["ML_PREDICTION"] = ml_values
            
            # Générer des signaux
            current_price = market_data['close'].iloc[-1]
            signals = self.signal_generator.generate_signals(
                indicator_values, current_price, symbol
            )
            
            # Traiter les signaux
            for signal in signals:
                if signal.strength > 0.6 and signal.confidence > 0.7:
                    # Ajouter une demande de position
                    success = self.position_manager.add_position_request(
                        signal, 
                        sizing_strategy="kelly",
                        priority=1 if signal.strength > 0.8 else 2
                    )
                    
                    if success:
                        self.logger.info(f"Signal traité: {symbol} {signal.signal_type.value} "
                                       f"force={signal.strength:.2f}")
            
            # Traiter les demandes de positions
            allocations = self.position_manager.process_position_requests()
            
            if allocations:
                self.logger.info(f"{len(allocations)} positions allouées pour {symbol}")
        
        except Exception as e:
            self.logger.error(f"Erreur traitement {symbol}: {e}")
    
    async def _get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Récupère les données de marché pour un symbole"""
        try:
            # Récupérer les données depuis l'agrégateur
            data = await data_aggregator.get_aggregated_data([symbol])
            
            if symbol in data and data[symbol]:
                # Convertir en DataFrame
                market_data = data[symbol]
                
                # Créer un DataFrame OHLCV
                df_data = []
                for point in market_data:
                    df_data.append({
                        'timestamp': point.timestamp,
                        'open': point.ohlcv.open,
                        'high': point.ohlcv.high,
                        'low': point.ohlcv.low,
                        'close': point.ohlcv.close,
                        'volume': point.ohlcv.volume
                    })
                
                df = pd.DataFrame(df_data)
                df.set_index('timestamp', inplace=True)
                return df
            
            return None
        
        except Exception as e:
            self.logger.error(f"Erreur récupération données {symbol}: {e}")
            return None
    
    async def _monitor_system(self):
        """Surveille le système en continu"""
        while self.is_running:
            try:
                # Vérifier la santé du système
                await self._check_system_health()
                
                # Nettoyer les données anciennes
                await self._cleanup_old_data()
                
                await asyncio.sleep(60)  # Vérification toutes les minutes
            
            except Exception as e:
                self.logger.error(f"Erreur monitoring système: {e}")
                await asyncio.sleep(60)
    
    async def _check_system_health(self):
        """Vérifie la santé du système"""
        try:
            # Vérifier les connecteurs
            connected_exchanges = len([
                connector for connector in connector_factory.get_all_connectors().values()
                if connector.is_connected()
            ])
            
            if connected_exchanges == 0:
                self.logger.warning("Aucun exchange connecté")
            
            # Vérifier les positions
            portfolio_summary = self.position_manager.get_portfolio_summary()
            if portfolio_summary['positions_count'] > 10:
                self.logger.warning(f"Trop de positions ouvertes: {portfolio_summary['positions_count']}")
            
            # Vérifier les métriques de risque
            risk_metrics = self.position_manager.get_position_risk_metrics()
            if risk_metrics and risk_metrics.get('leverage_ratio', 0) > 2.0:
                self.logger.warning(f"Ratio de levier élevé: {risk_metrics['leverage_ratio']:.2f}")
        
        except Exception as e:
            self.logger.error(f"Erreur vérification santé: {e}")
    
    async def _cleanup_old_data(self):
        """Nettoie les données anciennes"""
        try:
            # Nettoyer l'historique des signaux
            if hasattr(self.signal_generator, 'signals_history'):
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.signal_generator.signals_history = [
                    signal for signal in self.signal_generator.signals_history
                    if signal.timestamp > cutoff_time
                ]
        
        except Exception as e:
            self.logger.error(f"Erreur nettoyage données: {e}")
    
    async def _display_statistics(self):
        """Affiche les statistiques périodiquement"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Affichage toutes les 5 minutes
                
                if not self.is_running:
                    break
                
                # Afficher les statistiques
                await self._show_status()
            
            except Exception as e:
                self.logger.error(f"Erreur affichage statistiques: {e}")
    
    async def _show_status(self):
        """Affiche le statut du système"""
        try:
            print("\n" + "="*80)
            print("STATUT DU SYSTÈME DE TRADING CRYPTOSPREADEDGE")
            print("="*80)
            
            # Statut général
            print(f"Mode: {'LIVE' if self.is_running else 'ARRÊTÉ'}")
            print(f"Symboles surveillés: {', '.join(self.symbols)}")
            print(f"Intervalle de mise à jour: {self.update_interval}s")
            
            # Statut des connecteurs
            connected_exchanges = [
                name for name, connector in connector_factory.get_all_connectors().items()
                if connector.is_connected()
            ]
            print(f"Exchanges connectés: {len(connected_exchanges)}")
            if connected_exchanges:
                print(f"  {', '.join(connected_exchanges)}")
            
            # Statut des indicateurs
            if self.indicator_composite:
                print(f"\nIndicateurs:")
                print(f"  Nombre d'indicateurs: {len(self.indicator_composite.indicators)}")
            
            # Statut des signaux
            if self.signal_generator:
                signal_stats = self.signal_generator.get_signal_statistics()
                print(f"\nSignaux:")
                print(f"  Signaux totaux: {signal_stats.get('total_signals', 0)}")
                print(f"  Stratégies actives: {signal_stats.get('strategies_count', 0)}")
                print(f"  Force moyenne: {signal_stats.get('average_strength', 0):.2f}")
                print(f"  Confiance moyenne: {signal_stats.get('average_confidence', 0):.2%}")
            
            # Statut du portefeuille
            if self.position_manager:
                portfolio_summary = self.position_manager.get_portfolio_summary()
                print(f"\nPortefeuille:")
                print(f"  Valeur: {portfolio_summary['portfolio_value']:.2f} USD")
                print(f"  Équité totale: {portfolio_summary['total_equity']:.2f} USD")
                print(f"  PnL non réalisé: {portfolio_summary['unrealized_pnl']:.2f} USD")
                print(f"  Positions ouvertes: {portfolio_summary['positions_count']}")
                print(f"  Demandes en attente: {portfolio_summary['pending_requests']}")
            
            # Statut de l'arbitrage
            arbitrage_stats = arbitrage_engine.get_statistics()
            print(f"\nArbitrage:")
            print(f"  Opportunités trouvées: {arbitrage_stats['opportunities_found']}")
            print(f"  Opportunités exécutées: {arbitrage_stats['opportunities_executed']}")
            print(f"  Taux de succès: {arbitrage_stats['success_rate']:.2%}")
            print(f"  Profit net: {arbitrage_stats['net_profit']:.2f} USD")
            
            print("="*80)
        
        except Exception as e:
            self.logger.error(f"Erreur affichage statut: {e}")
    
    async def _main_loop(self):
        """Boucle principale du système"""
        try:
            self.logger.info("Système de trading démarré avec succès")
            self.logger.info("Appuyez sur Ctrl+C pour arrêter")
            
            # Attendre indéfiniment
            while self.is_running:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            self.logger.info("Arrêt demandé par l'utilisateur")
        except Exception as e:
            self.logger.error(f"Erreur boucle principale: {e}")
        finally:
            await self.stop()


def setup_signal_handlers(system: TradingSystem):
    """Configure les gestionnaires de signaux"""
    def signal_handler(signum, frame):
        print(f"\nSignal {signum} reçu, arrêt du système...")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Système de trading CryptoSpreadEdge")
    parser.add_argument('--mode', choices=['live', 'test'], default='live',
                       help='Mode de fonctionnement (défaut: live)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO',
                       help='Niveau de logging (défaut: INFO)')
    parser.add_argument('--symbols', nargs='+', default=['BTC', 'ETH', 'BNB'],
                       help='Symboles à trader (défaut: BTC ETH BNB)')
    parser.add_argument('--update-interval', type=int, default=60,
                       help='Intervalle de mise à jour en secondes (défaut: 60)')

    # Overrides rebalance via CLI -> variables d'environnement
    parser.add_argument('--rebalance-enabled', type=str, choices=['0','1','true','false','True','False'], default=None,
                       help='Activer le rebalance automatique (1/0)')
    parser.add_argument('--rebalance-interval', type=int, default=None,
                       help='Intervalle de rebalance en secondes')
    parser.add_argument('--rebalance-method', type=str, choices=['rp','mv'], default=None,
                       help='Méthode de rebalance: rp ou mv')
    parser.add_argument('--rebalance-min-weight', type=float, default=None,
                       help='Poids minimum par actif')
    parser.add_argument('--rebalance-max-weight', type=float, default=None,
                       help='Poids maximum par actif')
    parser.add_argument('--rebalance-leverage', type=float, default=None,
                       help='Levier cible (somme des poids)')
    parser.add_argument('--rebalance-risk-aversion', type=float, default=None,
                       help='Averseion au risque (mean-variance)')
    parser.add_argument('--rebalance-trade-threshold', type=float, default=None,
                       help='Valeur minimale d\'ordre pour exécuter la correction')
    parser.add_argument('--rebalance-env-file', type=str, default=None,
                       help='Fichier .env à charger (CSE_REBALANCE_*)')
    parser.add_argument('--rebalance-dry-run', type=str, choices=['0','1','true','false','True','False'], default=None, help='Ne pas exécuter les ordres, seulement logguer')
    parser.add_argument('--rebalance-max-orders', type=int, default=None, help='Nombre max d ordres par cycle')
    parser.add_argument('--rebalance-per-exchange-cap', type=float, default=None, help='Plafond de valeur par exchange')
    parser.add_argument('--rebalance-fee-rate', type=float, default=None, help='Taux de fees estimé (ex: 0.001)')
    parser.add_argument('--rebalance-slippage-bps', type=float, default=None, help='Slippage en bps (ex: 10 = 0.10%)')
    parser.add_argument('--rebalance-min-notional', type=float, default=None, help='Taille minimale notionnelle par ordre')
    
    args = parser.parse_args()
    
    # Configurer le logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Appliquer les overrides via variables d'environnement
    import os
    if args.rebalance_enabled is not None:
        os.environ['CSE_REBALANCE_ENABLED'] = args.rebalance_enabled
    if args.rebalance_interval is not None:
        os.environ['CSE_REBALANCE_INTERVAL'] = str(args.rebalance_interval)
    if args.rebalance_method is not None:
        os.environ['CSE_REBALANCE_METHOD'] = args.rebalance_method
    if args.rebalance_min_weight is not None:
        os.environ['CSE_REBALANCE_MIN_WEIGHT'] = str(args.rebalance_min_weight)
    if args.rebalance_max_weight is not None:
        os.environ['CSE_REBALANCE_MAX_WEIGHT'] = str(args.rebalance_max_weight)
    if args.rebalance_leverage is not None:
        os.environ['CSE_REBALANCE_LEVERAGE'] = str(args.rebalance_leverage)
    if args.rebalance_risk_aversion is not None:
        os.environ['CSE_REBALANCE_RISK_AVERSION'] = str(args.rebalance_risk_aversion)
    if args.rebalance_trade_threshold is not None:
        os.environ['CSE_REBALANCE_TRADE_THRESHOLD'] = str(args.rebalance_trade_threshold)
    if args.rebalance_env_file is not None:
        os.environ['CSE_REBALANCE_ENV_FILE'] = args.rebalance_env_file
    if args.rebalance_dry_run is not None:
        os.environ['CSE_REBALANCE_DRY_RUN'] = args.rebalance_dry_run
    if args.rebalance_max_orders is not None:
        os.environ['CSE_REBALANCE_MAX_ORDERS'] = str(args.rebalance_max_orders)
    if args.rebalance_per_exchange_cap is not None:
        os.environ['CSE_REBALANCE_PER_EXCHANGE_CAP'] = str(args.rebalance_per_exchange_cap)
    if args.rebalance_fee_rate is not None:
        os.environ['CSE_REBALANCE_FEE_RATE'] = str(args.rebalance_fee_rate)
    if args.rebalance_slippage_bps is not None:
        os.environ['CSE_REBALANCE_SLIPPAGE_BPS'] = str(args.rebalance_slippage_bps)
    if args.rebalance_min_notional is not None:
        os.environ['CSE_REBALANCE_MIN_NOTIONAL'] = str(args.rebalance_min_notional)
    
    # Créer le système
    system = TradingSystem()
    system.symbols = args.symbols
    system.update_interval = args.update_interval
    
    # Configurer les gestionnaires de signaux
    setup_signal_handlers(system)
    
    try:
        # Démarrer le système
        await system.start(args.mode)
    except Exception as e:
        logging.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())