"""
Script de test du système de prédiction et d'indicateurs CryptoSpreadEdge
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.indicators.base_indicator import IndicatorFactory, IndicatorComposite, indicator_manager
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
    MLPredictionStrategy, StrategyFactory
)
from src.prediction.ml_predictor import MLPredictor
from src.backtesting.backtesting_engine import BacktestingEngine, SimpleBacktestStrategy
from src.position.position_manager import PositionManager


class PredictionSystemTester:
    """Testeur du système de prédiction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.test_results = {}
    
    def setup_logging(self):
        """Configure le logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def generate_test_data(self, symbol: str = "BTC", days: int = 365) -> pd.DataFrame:
        """Génère des données de test"""
        print(f"\n📊 Génération de données de test pour {symbol} ({days} jours)")
        
        # Générer des données OHLCV réalistes
        np.random.seed(42)
        
        # Prix de base
        base_price = 50000.0 if symbol == "BTC" else 3000.0
        
        # Générer des retours avec tendance et volatilité
        returns = np.random.normal(0.0001, 0.02, days * 24)  # Retours horaires
        
        # Ajouter une tendance
        trend = np.linspace(0, 0.3, days * 24)  # Tendance haussière de 30%
        returns += trend / (days * 24)
        
        # Générer les prix
        prices = [base_price]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        # Créer OHLCV
        data = []
        for i in range(1, len(prices)):
            close = prices[i]
            open_price = prices[i-1]
            
            # High et Low basés sur la volatilité
            volatility = abs(returns[i-1]) * 2
            high = close * (1 + volatility * np.random.random())
            low = close * (1 - volatility * np.random.random())
            
            # Volume basé sur la volatilité
            volume = 1000 + volatility * 10000 * np.random.random()
            
            timestamp = datetime.utcnow() - timedelta(hours=len(prices)-i)
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        print(f"✅ Données générées: {len(df)} points")
        print(f"   Prix min: {df['close'].min():.2f}")
        print(f"   Prix max: {df['close'].max():.2f}")
        print(f"   Volume moyen: {df['volume'].mean():.0f}")
        
        return df
    
    async def test_technical_indicators(self) -> bool:
        """Teste les indicateurs techniques"""
        print("\n" + "="*60)
        print("TEST DES INDICATEURS TECHNIQUES")
        print("="*60)
        
        try:
            # Générer des données de test
            data = self.generate_test_data("BTC", 100)
            
            # Créer les indicateurs
            indicators = {
                "SMA_20": MovingAverageIndicator("SMA_20", "SMA", 20),
                "EMA_20": MovingAverageIndicator("EMA_20", "EMA", 20),
                "RSI_14": RSIIndicator("RSI_14", 14),
                "MACD": MACDIndicator("MACD", 12, 26, 9),
                "BB_20": BollingerBandsIndicator("BB_20", 20, 2.0),
                "STOCH_14": StochasticIndicator("STOCH_14", 14, 3),
                "VOLUME_20": VolumeIndicator("VOLUME_20", 20),
                "ATR_14": ATRIndicator("ATR_14", 14)
            }
            
            # Calculer les indicateurs
            results = {}
            for name, indicator in indicators.items():
                try:
                    values = indicator.calculate(data)
                    results[name] = values
                    print(f"✅ {name}: {len(values)} valeurs calculées")
                    
                    if values:
                        latest = values[-1]
                        print(f"   Dernière valeur: {latest.value:.4f} (confiance: {latest.confidence:.2%})")
                
                except Exception as e:
                    print(f"❌ {name}: Erreur - {e}")
                    results[name] = []
            
            # Tester le composite d'indicateurs
            composite = IndicatorComposite("TestComposite")
            for indicator in indicators.values():
                composite.add_indicator(indicator)
            
            composite_results = composite.calculate_all(data)
            print(f"\n✅ Composite: {len(composite_results)} indicateurs calculés")
            
            # Tester la génération de signaux
            all_signals = composite.get_combined_signals(data)
            print(f"✅ Signaux générés: {len(all_signals)}")
            
            for signal in all_signals[:5]:  # Afficher les 5 premiers
                print(f"   Signal: {signal.signal_type} force={signal.strength:.2f} "
                      f"confiance={signal.confidence:.2%}")
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test indicateurs techniques: {e}")
            return False
    
    async def test_advanced_indicators(self) -> bool:
        """Teste les indicateurs avancés"""
        print("\n" + "="*60)
        print("TEST DES INDICATEURS AVANCÉS")
        print("="*60)
        
        try:
            # Générer des données de test
            data = self.generate_test_data("ETH", 200)
            
            # Créer les indicateurs avancés
            indicators = {
                "ICHIMOKU": IchimokuIndicator("ICHIMOKU", 9, 26, 52),
                "WILLIAMS_R": WilliamsRIndicator("WILLIAMS_R", 14),
                "VOLATILITY": VolatilityIndicator("VOLATILITY", 20)
            }
            
            # Calculer les indicateurs
            for name, indicator in indicators.items():
                try:
                    values = indicator.calculate(data)
                    print(f"✅ {name}: {len(values)} valeurs calculées")
                    
                    if values:
                        latest = values[-1]
                        print(f"   Dernière valeur: {latest.value:.4f}")
                        if latest.metadata:
                            print(f"   Métadonnées: {list(latest.metadata.keys())}")
                
                except Exception as e:
                    print(f"❌ {name}: Erreur - {e}")
            
            # Tester l'indicateur de sentiment
            sentiment_indicator = SentimentIndicator("SENTIMENT")
            
            # Ajouter des données de sentiment simulées
            for i in range(10):
                sentiment_score = np.random.uniform(-1, 1)
                timestamp = datetime.utcnow() - timedelta(hours=i)
                sentiment_indicator.add_sentiment_data(sentiment_score, timestamp, f"source_{i}")
            
            sentiment_values = sentiment_indicator.calculate(data)
            print(f"✅ SENTIMENT: {len(sentiment_values)} valeurs calculées")
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test indicateurs avancés: {e}")
            return False
    
    async def test_ml_prediction(self) -> bool:
        """Teste le système de prédiction ML"""
        print("\n" + "="*60)
        print("TEST DU SYSTÈME DE PRÉDICTION ML")
        print("="*60)
        
        try:
            # Générer des données de test
            data = self.generate_test_data("BTC", 300)
            
            # Créer le prédicteur ML
            ml_predictor = MLPredictor("TestMLPredictor")
            
            # Entraîner les modèles
            print("🧠 Entraînement des modèles ML...")
            training_results = ml_predictor.train_models(data)
            
            print("Résultats d'entraînement:")
            for model_name, result in training_results.items():
                if 'error' not in result:
                    print(f"  {model_name}: R² = {result['r2_score']:.4f}, "
                          f"MSE = {result['mse']:.6f}")
                else:
                    print(f"  {model_name}: Erreur - {result['error']}")
            
            # Faire des prédictions
            print("\n🔮 Génération de prédictions...")
            predictions = ml_predictor.predict_ensemble(data)
            
            if predictions:
                print(f"✅ {len(predictions)} prédictions générées")
                
                # Afficher les dernières prédictions
                for i, pred in enumerate(predictions[-5:]):
                    print(f"  Prédiction {i+1}: {pred.predicted_change:.2%} "
                          f"(confiance: {pred.confidence:.2%})")
                
                # Statistiques des prédictions
                changes = [p.predicted_change for p in predictions]
                confidences = [p.confidence for p in predictions]
                
                print(f"\nStatistiques des prédictions:")
                print(f"  Changement moyen: {np.mean(changes):.2%}")
                print(f"  Confiance moyenne: {np.mean(confidences):.2%}")
                print(f"  Prédictions positives: {sum(1 for c in changes if c > 0)}")
                print(f"  Prédictions négatives: {sum(1 for c in changes if c < 0)}")
            else:
                print("❌ Aucune prédiction générée")
                return False
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test prédiction ML: {e}")
            return False
    
    async def test_signal_generation(self) -> bool:
        """Teste la génération de signaux"""
        print("\n" + "="*60)
        print("TEST DE LA GÉNÉRATION DE SIGNAUX")
        print("="*60)
        
        try:
            # Générer des données de test
            data = self.generate_test_data("BTC", 200)
            
            # Créer les indicateurs
            indicators = {
                "SMA_20": MovingAverageIndicator("SMA_20", "SMA", 20),
                "SMA_50": MovingAverageIndicator("SMA_50", "SMA", 50),
                "RSI_14": RSIIndicator("RSI_14", 14),
                "MACD": MACDIndicator("MACD", 12, 26, 9),
                "BB_20": BollingerBandsIndicator("BB_20", 20, 2.0),
                "STOCH_14": StochasticIndicator("STOCH_14", 14, 3)
            }
            
            # Calculer les indicateurs
            indicator_values = {}
            for name, indicator in indicators.items():
                values = indicator.calculate(data)
                indicator_values[name] = values
            
            # Créer le générateur de signaux
            signal_generator = SignalGenerator("TestSignalGenerator")
            
            # Ajouter les stratégies
            strategies = [
                TrendFollowingStrategy("TrendFollowing"),
                MeanReversionStrategy("MeanReversion"),
                MLPredictionStrategy("MLPrediction")
            ]
            
            for strategy in strategies:
                signal_generator.add_strategy(strategy)
            
            # Générer des signaux
            current_price = data['close'].iloc[-1]
            signals = signal_generator.generate_signals(indicator_values, current_price, "BTC")
            
            print(f"✅ {len(signals)} signaux générés")
            
            # Afficher les signaux
            for i, signal in enumerate(signals[:10]):  # Afficher les 10 premiers
                print(f"  Signal {i+1}: {signal.signal_type.value} "
                      f"force={signal.strength:.2f} confiance={signal.confidence:.2%}")
                if signal.reasoning:
                    print(f"    Raison: {', '.join(signal.reasoning[:2])}")
            
            # Statistiques des signaux
            signal_types = {}
            for signal in signals:
                signal_type = signal.signal_type.value
                signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
            
            print(f"\nTypes de signaux:")
            for signal_type, count in signal_types.items():
                print(f"  {signal_type}: {count}")
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test génération signaux: {e}")
            return False
    
    async def test_backtesting(self) -> bool:
        """Teste le système de backtesting"""
        print("\n" + "="*60)
        print("TEST DU SYSTÈME DE BACKTESTING")
        print("="*60)
        
        try:
            # Générer des données de test
            data = self.generate_test_data("BTC", 100)
            
            # Créer des signaux de test
            signals = []
            for i in range(20, len(data), 10):
                if i >= len(data):
                    break
                
                # Signal d'achat si prix > SMA 20
                sma_20 = data['close'].rolling(20).mean().iloc[i]
                current_price = data['close'].iloc[i]
                
                if current_price > sma_20:
                    signal_type = "buy"
                    strength = 0.7
                else:
                    signal_type = "sell"
                    strength = 0.6
                
                from src.prediction.signal_generator import TradingSignal, SignalType
                
                signal = TradingSignal(
                    signal_type=SignalType.BUY if signal_type == "buy" else SignalType.SELL,
                    strength=strength,
                    confidence=0.8,
                    timestamp=data.index[i],
                    symbol="BTC",
                    price=current_price,
                    stop_loss=current_price * 0.95,
                    take_profit=current_price * 1.05
                )
                signals.append(signal)
            
            print(f"✅ {len(signals)} signaux de test créés")
            
            # Créer le moteur de backtesting
            backtest_engine = BacktestingEngine("TestBacktestEngine")
            
            # Définir la stratégie
            strategy = SimpleBacktestStrategy(
                max_position_size=0.1,
                stop_loss_pct=0.05,
                take_profit_pct=0.10,
                max_hold_days=10
            )
            backtest_engine.set_strategy(strategy)
            
            # Charger les données et signaux
            backtest_engine.load_data(data)
            backtest_engine.load_signals(signals)
            
            # Exécuter le backtest
            print("🏃 Exécution du backtest...")
            results = backtest_engine.run_backtest(initial_capital=10000.0)
            
            if results:
                print(f"✅ Backtest terminé")
                print(f"\nRésultats du backtest:")
                print(f"  Trades totaux: {results.total_trades}")
                print(f"  Taux de réussite: {results.win_rate:.2%}")
                print(f"  PnL total: {results.total_pnl:.2f} USD")
                print(f"  Profit net: {results.net_profit:.2f} USD")
                print(f"  Frais totaux: {results.total_fees:.2f} USD")
                print(f"  Drawdown max: {results.max_drawdown:.2%}")
                print(f"  Ratio de Sharpe: {results.sharpe_ratio:.2f}")
                print(f"  Retour total: {results.total_return:.2%}")
                print(f"  Retour annualisé: {results.annualized_return:.2%}")
                
                if results.trades:
                    print(f"\nDétails des trades:")
                    for i, trade in enumerate(results.trades[:5]):  # Afficher les 5 premiers
                        print(f"  Trade {i+1}: {trade.symbol} {trade.position_type.value} "
                              f"PnL={trade.net_pnl:.2f} durée={trade.duration.days}j")
            else:
                print("❌ Aucun résultat de backtest")
                return False
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test backtesting: {e}")
            return False
    
    async def test_position_management(self) -> bool:
        """Teste le système de gestion des positions"""
        print("\n" + "="*60)
        print("TEST DE LA GESTION DES POSITIONS")
        print("="*60)
        
        try:
            # Créer le gestionnaire de positions
            position_manager = PositionManager("TestPositionManager")
            position_manager.set_portfolio_value(100000.0)
            
            # Créer des signaux de test
            from src.prediction.signal_generator import TradingSignal, SignalType
            
            signals = []
            for i in range(5):
                signal = TradingSignal(
                    signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                    strength=0.7 + i * 0.05,
                    confidence=0.8,
                    timestamp=datetime.utcnow() - timedelta(hours=i),
                    symbol=f"SYMBOL_{i}",
                    price=50000.0 + i * 1000,
                    stop_loss=48000.0 + i * 1000,
                    take_profit=52000.0 + i * 1000
                )
                signals.append(signal)
            
            print(f"✅ {len(signals)} signaux de test créés")
            
            # Ajouter des demandes de positions
            for i, signal in enumerate(signals):
                success = position_manager.add_position_request(
                    signal, 
                    sizing_strategy="percentage",
                    priority=i + 1
                )
                print(f"  Demande {i+1}: {'✅ Ajoutée' if success else '❌ Rejetée'}")
            
            # Traiter les demandes
            print("\n🔄 Traitement des demandes de positions...")
            allocations = position_manager.process_position_requests()
            
            print(f"✅ {len(allocations)} positions allouées")
            
            for allocation in allocations:
                print(f"  {allocation.symbol}: {allocation.position_type.value} "
                      f"size={allocation.allocated_size:.4f} "
                      f"risk/reward={allocation.risk_reward_ratio:.2f}")
            
            # Afficher le résumé du portefeuille
            summary = position_manager.get_portfolio_summary()
            print(f"\nRésumé du portefeuille:")
            print(f"  Valeur du portefeuille: {summary['portfolio_value']:.2f} USD")
            print(f"  Équité totale: {summary['total_equity']:.2f} USD")
            print(f"  PnL non réalisé: {summary['unrealized_pnl']:.2f} USD")
            print(f"  Nombre de positions: {summary['positions_count']}")
            
            # Afficher les métriques de risque
            risk_metrics = position_manager.get_position_risk_metrics()
            if risk_metrics:
                print(f"\nMétriques de risque:")
                print(f"  VaR 95%: {risk_metrics['var_95']:.2f} USD")
                print(f"  Risque de corrélation: {risk_metrics['correlation_risk']:.2f}")
                print(f"  Risque de concentration: {risk_metrics['concentration_risk']:.2%}")
                print(f"  Ratio de levier: {risk_metrics['leverage_ratio']:.2f}")
            
            return True
        
        except Exception as e:
            print(f"❌ Erreur test gestion positions: {e}")
            return False
    
    async def run_all_tests(self):
        """Exécute tous les tests"""
        print("="*60)
        print("DÉMARRAGE DES TESTS DU SYSTÈME DE PRÉDICTION")
        print("="*60)
        
        start_time = time.time()
        
        # Liste des tests
        tests = [
            ("Indicateurs techniques", self.test_technical_indicators),
            ("Indicateurs avancés", self.test_advanced_indicators),
            ("Prédiction ML", self.test_ml_prediction),
            ("Génération de signaux", self.test_signal_generation),
            ("Backtesting", self.test_backtesting),
            ("Gestion des positions", self.test_position_management)
        ]
        
        # Exécuter les tests
        results = {}
        for test_name, test_func in tests:
            print(f"\n🧪 Test: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                print(f"✅ {test_name}: {'Réussi' if result else 'Échoué'}")
            except Exception as e:
                print(f"❌ {test_name}: Erreur - {e}")
                results[test_name] = False
        
        # Calculer le temps total
        total_time = time.time() - start_time
        
        # Afficher le résumé
        print("\n" + "="*60)
        print("RÉSUMÉ DES TESTS")
        print("="*60)
        
        successful_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        print(f"Tests réussis: {successful_tests}/{total_tests}")
        print(f"Temps total: {total_time:.2f}s")
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
        
        if successful_tests == total_tests:
            print("\n🎉 Tous les tests sont passés avec succès!")
            print("Le système de prédiction est prêt pour le trading!")
        else:
            print(f"\n⚠️  {total_tests - successful_tests} test(s) ont échoué")
            print("Des corrections sont nécessaires avant de pouvoir utiliser le système")
        
        return successful_tests == total_tests


async def main():
    """Fonction principale"""
    tester = PredictionSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Le système de prédiction est opérationnel!")
    else:
        print("\n🔧 Des corrections sont nécessaires")


if __name__ == "__main__":
    asyncio.run(main())