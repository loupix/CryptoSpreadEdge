#!/usr/bin/env python3
"""
Démonstration du système d'arbitrage CryptoSpreadEdge
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from arbitrage.arbitrage_engine import arbitrage_engine, ArbitrageOpportunity
from arbitrage.price_monitor import price_monitor
from arbitrage.execution_engine import execution_engine
from arbitrage.risk_manager import arbitrage_risk_manager
from arbitrage.profit_calculator import ProfitCalculator


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ArbitrageDemo:
    """Démonstration du système d'arbitrage"""
    
    def __init__(self):
        self.profit_calculator = ProfitCalculator()
        self.demo_opportunities = []
    
    async def run_demo(self):
        """Lance la démonstration"""
        print("🎯 === DÉMONSTRATION DU SYSTÈME D'ARBITRAGE ===")
        print("=" * 60)
        
        # 1. Démontrer le calcul de profit
        await self.demo_profit_calculation()
        
        # 2. Démontrer la détection d'opportunités
        await self.demo_opportunity_detection()
        
        # 3. Démontrer la gestion des risques
        await self.demo_risk_management()
        
        # 4. Démontrer le monitoring des prix
        await self.demo_price_monitoring()
        
        # 5. Démontrer les statistiques
        await self.demo_statistics()
        
        print("\n🎉 Démonstration terminée avec succès!")
    
    async def demo_profit_calculation(self):
        """Démontre le calcul de profit"""
        print("\n💰 === CALCUL DE PROFIT ===")
        
        # Créer une opportunité d'arbitrage fictive
        opportunity = ArbitrageOpportunity(
            symbol="BTC/USDT",
            buy_exchange="binance",
            sell_exchange="okx",
            buy_price=50000.0,
            sell_price=50100.0,
            spread=100.0,
            spread_percentage=0.002,
            volume_available=1.0,
            max_profit=100.0,
            confidence=0.9,
            timestamp=datetime.utcnow(),
            execution_time_estimate=2.0,
            risk_score=0.3
        )
        
        # Calculer le profit
        calculation = self.profit_calculator.calculate_profit(opportunity, 1.0)
        
        print(f"Symbole: {opportunity.symbol}")
        print(f"Achat: {opportunity.buy_exchange} à {opportunity.buy_price:.2f} USD")
        print(f"Vente: {opportunity.sell_exchange} à {opportunity.sell_price:.2f} USD")
        print(f"Spread: {opportunity.spread:.2f} USD ({opportunity.spread_percentage:.2%})")
        print(f"Volume: {opportunity.volume_available:.2f} BTC")
        print(f"Profit brut: {calculation.gross_profit:.2f} USD")
        print(f"Frais: {calculation.total_fees:.2f} USD")
        print(f"Profit net: {calculation.net_profit:.2f} USD")
        print(f"ROI: {calculation.roi_percentage:.2%}")
    
    async def demo_opportunity_detection(self):
        """Démontre la détection d'opportunités"""
        print("\n🔍 === DÉTECTION D'OPPORTUNITÉS ===")
        
        # Créer plusieurs opportunités fictives
        opportunities = [
            ArbitrageOpportunity(
                symbol="ETH/USDT",
                buy_exchange="binance",
                sell_exchange="okx",
                buy_price=3000.0,
                sell_price=3015.0,
                spread=15.0,
                spread_percentage=0.005,
                volume_available=10.0,
                max_profit=150.0,
                confidence=0.95,
                timestamp=datetime.utcnow(),
                execution_time_estimate=1.5,
                risk_score=0.2
            ),
            ArbitrageOpportunity(
                symbol="BNB/USDT",
                buy_exchange="okx",
                sell_exchange="bybit",
                buy_price=300.0,
                sell_price=303.0,
                spread=3.0,
                spread_percentage=0.01,
                volume_available=100.0,
                max_profit=300.0,
                confidence=0.85,
                timestamp=datetime.utcnow(),
                execution_time_estimate=2.5,
                risk_score=0.4
            ),
            ArbitrageOpportunity(
                symbol="ADA/USDT",
                buy_exchange="gateio",
                sell_exchange="huobi",
                buy_price=0.50,
                sell_price=0.52,
                spread=0.02,
                spread_percentage=0.04,
                volume_available=1000.0,
                max_profit=20.0,
                confidence=0.7,
                timestamp=datetime.utcnow(),
                execution_time_estimate=3.0,
                risk_score=0.6
            )
        ]
        
        print("Opportunités détectées:")
        for i, opp in enumerate(opportunities, 1):
            calculation = self.profit_calculator.calculate_profit(opp, opp.volume_available)
            print(f"\n{i}. {opp.symbol}")
            print(f"   {opp.buy_exchange} → {opp.sell_exchange}")
            print(f"   Spread: {opp.spread_percentage:.2%}")
            print(f"   Profit net: {calculation.net_profit:.2f} USD")
            print(f"   Confiance: {opp.confidence:.1%}")
            print(f"   Risque: {opp.risk_score:.1%}")
        
        self.demo_opportunities = opportunities
    
    async def demo_risk_management(self):
        """Démontre la gestion des risques"""
        print("\n🛡️ === GESTION DES RISQUES ===")
        
        # Démarrer le RiskManager
        await arbitrage_risk_manager.start_monitoring()
        
        # Tester la validation des opportunités
        for opp in self.demo_opportunities:
            is_safe = await arbitrage_risk_manager.is_opportunity_safe(opp)
            status = "✅ SÛRE" if is_safe else "❌ RISQUÉE"
            print(f"{opp.symbol}: {status}")
        
        # Afficher le statut des risques
        risk_status = arbitrage_risk_manager.get_risk_status()
        print(f"\nLimites de risque:")
        print(f"  Position max: {risk_status['limits']['max_position_size']:.0f} USD")
        print(f"  Perte quotidienne max: {risk_status['limits']['max_daily_loss']:.0f} USD")
        print(f"  Trades quotidiens max: {risk_status['limits']['max_daily_trades']}")
        
        # Arrêter le RiskManager
        await arbitrage_risk_manager.stop_monitoring()
    
    async def demo_price_monitoring(self):
        """Démontre le monitoring des prix"""
        print("\n📊 === MONITORING DES PRIX ===")
        
        # Démarrer le PriceMonitor
        await price_monitor.start()
        
        # Attendre la collecte de données
        print("Collecte des données de prix...")
        await asyncio.sleep(5)
        
        # Afficher les statistiques
        stats = price_monitor.get_statistics()
        print(f"Plateformes surveillées: {stats['total_platforms']}")
        print(f"Symboles surveillés: {stats['symbols_monitored']}")
        print(f"Mises à jour: {stats['total_updates']}")
        print(f"Temps moyen de mise à jour: {stats['avg_update_time']:.3f}s")
        
        # Afficher un résumé de prix pour BTC
        btc_summary = price_monitor.get_price_summary("BTC")
        if btc_summary:
            print(f"\nRésumé BTC:")
            print(f"  Prix min: {btc_summary['min_price']:.2f} USD")
            print(f"  Prix max: {btc_summary['max_price']:.2f} USD")
            print(f"  Prix moyen: {btc_summary['avg_price']:.2f} USD")
            print(f"  Écart-type: {btc_summary['price_std']:.2f} USD")
        
        # Arrêter le PriceMonitor
        await price_monitor.stop()
    
    async def demo_statistics(self):
        """Démontre les statistiques du système"""
        print("\n📈 === STATISTIQUES DU SYSTÈME ===")
        
        # Statistiques du ProfitCalculator
        calc_stats = self.profit_calculator.stats
        print("ProfitCalculator:")
        print(f"  Calculs totaux: {calc_stats['total_calculations']}")
        print(f"  Opportunités rentables: {calc_stats['profitable_opportunities']}")
        print(f"  Profit brut total: {calc_stats['total_gross_profit']:.2f} USD")
        print(f"  Frais totaux: {calc_stats['total_fees']:.2f} USD")
        print(f"  Profit net total: {calc_stats['total_net_profit']:.2f} USD")
        print(f"  ROI moyen: {calc_stats['avg_profit_percentage']:.2%}")
        
        # Statistiques du RiskManager
        risk_stats = arbitrage_risk_manager.get_risk_status()
        print(f"\nRiskManager:")
        print(f"  Position actuelle: {risk_stats['metrics']['current_position']:.2f} USD")
        print(f"  PnL quotidien: {risk_stats['metrics']['daily_pnl']:.2f} USD")
        print(f"  Trades quotidiens: {risk_stats['metrics']['daily_trades']}")
        print(f"  Taux de réussite: {risk_stats['metrics']['win_rate']:.1%}")
        print(f"  Drawdown max: {risk_stats['metrics']['max_drawdown']:.2f} USD")
        print(f"  Ratio de Sharpe: {risk_stats['metrics']['sharpe_ratio']:.2f}")
    
    def print_header(self, title: str):
        """Affiche un en-tête"""
        print(f"\n{title}")
        print("=" * len(title))


async def main():
    """Fonction principale"""
    demo = ArbitrageDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("🎯 CryptoSpreadEdge - Démonstration du Système d'Arbitrage")
    print("=" * 60)
    print("Cette démonstration montre les capacités du système d'arbitrage")
    print("sans effectuer de vrais trades.")
    print("=" * 60)
    
    asyncio.run(main())