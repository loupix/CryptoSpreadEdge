"""
Calculateur de profit pour l'arbitrage
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from .arbitrage_engine import ArbitrageOpportunity, ArbitrageExecution


@dataclass
class ProfitCalculation:
    """Calcul de profit d'arbitrage"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    quantity: float
    gross_profit: float
    fees: float
    net_profit: float
    profit_percentage: float
    roi: float
    timestamp: datetime


@dataclass
class FeeStructure:
    """Structure des frais d'une plateforme"""
    maker_fee: float
    taker_fee: float
    withdrawal_fee: float
    deposit_fee: float
    minimum_fee: float
    maximum_fee: float


class ProfitCalculator:
    """Calculateur de profit pour l'arbitrage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Structures de frais par plateforme
        self.fee_structures = {
            "binance": FeeStructure(0.001, 0.001, 0.0005, 0.0, 0.0, 0.0),
            "okx": FeeStructure(0.0008, 0.001, 0.0005, 0.0, 0.0, 0.0),
            "coinbase": FeeStructure(0.005, 0.005, 0.001, 0.0, 0.0, 0.0),
            "kraken": FeeStructure(0.0016, 0.0026, 0.0005, 0.0, 0.0, 0.0),
            "bybit": FeeStructure(0.001, 0.001, 0.0005, 0.0, 0.0, 0.0),
            "bitget": FeeStructure(0.001, 0.001, 0.0005, 0.0, 0.0, 0.0),
            "gateio": FeeStructure(0.002, 0.002, 0.001, 0.0, 0.0, 0.0),
            "huobi": FeeStructure(0.002, 0.002, 0.001, 0.0, 0.0, 0.0),
            "kucoin": FeeStructure(0.001, 0.001, 0.0005, 0.0, 0.0, 0.0),
            "bitfinex": FeeStructure(0.001, 0.002, 0.001, 0.0, 0.0, 0.0),
            "bitstamp": FeeStructure(0.0025, 0.0025, 0.001, 0.0, 0.0, 0.0),
            "gemini": FeeStructure(0.0025, 0.0025, 0.001, 0.0, 0.0, 0.0),
            "bittrex": FeeStructure(0.0025, 0.0025, 0.001, 0.0, 0.0, 0.0),
            "mexc": FeeStructure(0.002, 0.002, 0.001, 0.0, 0.0, 0.0),
            "whitebit": FeeStructure(0.001, 0.001, 0.0005, 0.0, 0.0, 0.0),
            "phemex": FeeStructure(0.0001, 0.0006, 0.0005, 0.0, 0.0, 0.0)
        }
        
        # Historique des calculs
        self.calculation_history: List[ProfitCalculation] = []
        
        # Statistiques
        self.stats = {
            "total_calculations": 0,
            "profitable_opportunities": 0,
            "total_gross_profit": 0.0,
            "total_fees": 0.0,
            "total_net_profit": 0.0,
            "avg_profit_percentage": 0.0,
            "best_profit_percentage": 0.0,
            "worst_profit_percentage": 0.0
        }
    
    def calculate_profit(self, opportunity: ArbitrageOpportunity, quantity: float) -> ProfitCalculation:
        """Calcule le profit d'une opportunité d'arbitrage"""
        try:
            # Calculer le profit brut
            gross_profit = (opportunity.sell_price - opportunity.buy_price) * quantity
            
            # Calculer les frais
            fees = self._calculate_fees(opportunity, quantity)
            
            # Calculer le profit net
            net_profit = gross_profit - fees
            
            # Calculer les pourcentages
            profit_percentage = (net_profit / (opportunity.buy_price * quantity)) * 100 if opportunity.buy_price > 0 else 0
            roi = (net_profit / (opportunity.buy_price * quantity)) * 100 if opportunity.buy_price > 0 else 0
            
            # Créer le calcul
            calculation = ProfitCalculation(
                symbol=opportunity.symbol,
                buy_exchange=opportunity.buy_exchange,
                sell_exchange=opportunity.sell_exchange,
                buy_price=opportunity.buy_price,
                sell_price=opportunity.sell_price,
                quantity=quantity,
                gross_profit=gross_profit,
                fees=fees,
                net_profit=net_profit,
                profit_percentage=profit_percentage,
                roi=roi,
                timestamp=datetime.utcnow()
            )
            
            # Ajouter à l'historique
            self.calculation_history.append(calculation)
            
            # Mettre à jour les statistiques
            self._update_statistics(calculation)
            
            return calculation
        
        except Exception as e:
            self.logger.error(f"Erreur calcul profit: {e}")
            return None
    
    def _calculate_fees(self, opportunity: ArbitrageOpportunity, quantity: float) -> float:
        """Calcule les frais totaux"""
        try:
            total_fees = 0.0
            
            # Frais d'achat
            buy_fee_structure = self.fee_structures.get(opportunity.buy_exchange)
            if buy_fee_structure:
                buy_fees = quantity * opportunity.buy_price * buy_fee_structure.taker_fee
                total_fees += buy_fees
            
            # Frais de vente
            sell_fee_structure = self.fee_structures.get(opportunity.sell_exchange)
            if sell_fee_structure:
                sell_fees = quantity * opportunity.sell_price * sell_fee_structure.taker_fee
                total_fees += sell_fees
            
            # Frais de retrait (si applicable)
            if buy_fee_structure and buy_fee_structure.withdrawal_fee > 0:
                total_fees += buy_fee_structure.withdrawal_fee
            
            if sell_fee_structure and sell_fee_structure.withdrawal_fee > 0:
                total_fees += sell_fee_structure.withdrawal_fee
            
            return total_fees
        
        except Exception as e:
            self.logger.error(f"Erreur calcul frais: {e}")
            return 0.0
    
    def calculate_optimal_quantity(self, opportunity: ArbitrageOpportunity, max_investment: float) -> float:
        """Calcule la quantité optimale pour un investissement maximum"""
        try:
            # Quantité basée sur l'investissement maximum
            max_quantity = max_investment / opportunity.buy_price
            
            # Limiter par le volume disponible
            optimal_quantity = min(max_quantity, opportunity.volume_available)
            
            # Ajuster selon le score de risque
            risk_factor = 1.0 - opportunity.risk_score
            optimal_quantity *= risk_factor
            
            # Ajuster selon la confiance
            confidence_factor = opportunity.confidence
            optimal_quantity *= confidence_factor
            
            # Arrondir à 4 décimales
            return round(optimal_quantity, 4)
        
        except Exception as e:
            self.logger.error(f"Erreur calcul quantité optimale: {e}")
            return 0.0
    
    def calculate_breakeven_quantity(self, opportunity: ArbitrageOpportunity) -> float:
        """Calcule la quantité minimum pour atteindre le seuil de rentabilité"""
        try:
            # Calculer les frais fixes
            buy_fee_structure = self.fee_structures.get(opportunity.buy_exchange)
            sell_fee_structure = self.fee_structures.get(opportunity.sell_exchange)
            
            fixed_fees = 0.0
            if buy_fee_structure:
                fixed_fees += buy_fee_structure.withdrawal_fee
            if sell_fee_structure:
                fixed_fees += sell_fee_structure.withdrawal_fee
            
            # Calculer le spread net (après frais variables)
            buy_fee_rate = buy_fee_structure.taker_fee if buy_fee_structure else 0.001
            sell_fee_rate = sell_fee_structure.taker_fee if sell_fee_structure else 0.001
            
            net_spread = opportunity.sell_price - opportunity.buy_price
            net_spread -= opportunity.buy_price * buy_fee_rate
            net_spread -= opportunity.sell_price * sell_fee_rate
            
            if net_spread <= 0:
                return float('inf')  # Pas rentable
            
            # Calculer la quantité minimum
            breakeven_quantity = fixed_fees / net_spread
            
            return breakeven_quantity
        
        except Exception as e:
            self.logger.error(f"Erreur calcul seuil de rentabilité: {e}")
            return float('inf')
    
    def calculate_risk_adjusted_profit(self, opportunity: ArbitrageOpportunity, quantity: float) -> Dict[str, float]:
        """Calcule le profit ajusté au risque"""
        try:
            # Calcul de base
            base_calculation = self.calculate_profit(opportunity, quantity)
            if not base_calculation:
                return {}
            
            # Facteurs d'ajustement
            risk_factor = 1.0 - opportunity.risk_score
            confidence_factor = opportunity.confidence
            volatility_factor = self._get_volatility_factor(opportunity.symbol)
            
            # Profit ajusté
            adjusted_profit = base_calculation.net_profit * risk_factor * confidence_factor * volatility_factor
            
            # Probabilité de succès
            success_probability = risk_factor * confidence_factor
            
            # Valeur attendue
            expected_value = adjusted_profit * success_probability
            
            return {
                "base_profit": base_calculation.net_profit,
                "adjusted_profit": adjusted_profit,
                "success_probability": success_probability,
                "expected_value": expected_value,
                "risk_factor": risk_factor,
                "confidence_factor": confidence_factor,
                "volatility_factor": volatility_factor
            }
        
        except Exception as e:
            self.logger.error(f"Erreur calcul profit ajusté: {e}")
            return {}
    
    def _get_volatility_factor(self, symbol: str) -> float:
        """Obtient le facteur de volatilité pour un symbole"""
        try:
            # Facteurs de volatilité basés sur l'historique
            volatility_factors = {
                "BTC": 0.9,
                "ETH": 0.85,
                "BNB": 0.8,
                "ADA": 0.75,
                "DOT": 0.7,
                "LINK": 0.75,
                "LTC": 0.8,
                "BCH": 0.7,
                "XRP": 0.75,
                "EOS": 0.7
            }
            
            return volatility_factors.get(symbol, 0.8)
        
        except Exception as e:
            self.logger.error(f"Erreur facteur volatilité: {e}")
            return 0.8
    
    def calculate_portfolio_profit(self, opportunities: List[ArbitrageOpportunity], total_investment: float) -> Dict[str, Any]:
        """Calcule le profit d'un portefeuille d'opportunités"""
        try:
            if not opportunities:
                return {}
            
            # Trier par profit attendu
            opportunities_with_profit = []
            for opp in opportunities:
                quantity = self.calculate_optimal_quantity(opp, total_investment / len(opportunities))
                calculation = self.calculate_profit(opp, quantity)
                if calculation:
                    opportunities_with_profit.append((opp, calculation))
            
            # Trier par profit net
            opportunities_with_profit.sort(key=lambda x: x[1].net_profit, reverse=True)
            
            # Calculer les totaux
            total_gross_profit = sum(calc.gross_profit for _, calc in opportunities_with_profit)
            total_fees = sum(calc.fees for _, calc in opportunities_with_profit)
            total_net_profit = sum(calc.net_profit for _, calc in opportunities_with_profit)
            total_quantity = sum(calc.quantity for _, calc in opportunities_with_profit)
            
            # Calculer les moyennes
            avg_profit_percentage = statistics.mean([calc.profit_percentage for _, calc in opportunities_with_profit])
            avg_roi = statistics.mean([calc.roi for _, calc in opportunities_with_profit])
            
            # Calculer la diversification
            exchanges_used = set()
            for opp, _ in opportunities_with_profit:
                exchanges_used.add(opp.buy_exchange)
                exchanges_used.add(opp.sell_exchange)
            
            diversification_score = len(exchanges_used) / (len(opportunities_with_profit) * 2)
            
            return {
                "total_opportunities": len(opportunities_with_profit),
                "total_gross_profit": total_gross_profit,
                "total_fees": total_fees,
                "total_net_profit": total_net_profit,
                "total_quantity": total_quantity,
                "avg_profit_percentage": avg_profit_percentage,
                "avg_roi": avg_roi,
                "diversification_score": diversification_score,
                "exchanges_used": len(exchanges_used),
                "best_opportunity": opportunities_with_profit[0][1] if opportunities_with_profit else None,
                "worst_opportunity": opportunities_with_profit[-1][1] if opportunities_with_profit else None
            }
        
        except Exception as e:
            self.logger.error(f"Erreur calcul profit portefeuille: {e}")
            return {}
    
    def analyze_execution_result(self, execution: ArbitrageExecution) -> Dict[str, Any]:
        """Analyse le résultat d'une exécution"""
        try:
            if not execution.buy_order or not execution.sell_order:
                return {}
            
            # Calculer les métriques d'exécution
            execution_time = execution.execution_time
            slippage = self._calculate_slippage(execution)
            efficiency = self._calculate_efficiency(execution)
            
            # Comparer avec les attentes
            expected_profit = execution.opportunity.max_profit
            actual_profit = execution.actual_profit
            profit_ratio = actual_profit / expected_profit if expected_profit > 0 else 0
            
            # Calculer la performance
            performance_score = self._calculate_performance_score(execution)
            
            return {
                "execution_time": execution_time,
                "slippage": slippage,
                "efficiency": efficiency,
                "expected_profit": expected_profit,
                "actual_profit": actual_profit,
                "profit_ratio": profit_ratio,
                "performance_score": performance_score,
                "fees_paid": execution.fees_paid,
                "net_profit": execution.net_profit,
                "success": execution.status == "completed"
            }
        
        except Exception as e:
            self.logger.error(f"Erreur analyse résultat exécution: {e}")
            return {}
    
    def _calculate_slippage(self, execution: ArbitrageExecution) -> Dict[str, float]:
        """Calcule le slippage d'une exécution"""
        try:
            buy_slippage = 0.0
            sell_slippage = 0.0
            
            if execution.buy_order and execution.buy_order.average_price:
                expected_buy_price = execution.opportunity.buy_price
                actual_buy_price = execution.buy_order.average_price
                buy_slippage = (actual_buy_price - expected_buy_price) / expected_buy_price
            
            if execution.sell_order and execution.sell_order.average_price:
                expected_sell_price = execution.opportunity.sell_price
                actual_sell_price = execution.sell_order.average_price
                sell_slippage = (expected_sell_price - actual_sell_price) / expected_sell_price
            
            return {
                "buy_slippage": buy_slippage,
                "sell_slippage": sell_slippage,
                "total_slippage": buy_slippage + sell_slippage
            }
        
        except Exception as e:
            self.logger.error(f"Erreur calcul slippage: {e}")
            return {"buy_slippage": 0.0, "sell_slippage": 0.0, "total_slippage": 0.0}
    
    def _calculate_efficiency(self, execution: ArbitrageExecution) -> float:
        """Calcule l'efficacité d'une exécution"""
        try:
            if execution.execution_time <= 0:
                return 0.0
            
            # Efficacité basée sur le temps d'exécution
            expected_time = execution.opportunity.execution_time_estimate
            time_efficiency = min(1.0, expected_time / execution.execution_time) if execution.execution_time > 0 else 0.0
            
            # Efficacité basée sur le profit
            expected_profit = execution.opportunity.max_profit
            profit_efficiency = execution.actual_profit / expected_profit if expected_profit > 0 else 0.0
            
            # Efficacité combinée
            combined_efficiency = (time_efficiency + profit_efficiency) / 2
            
            return min(1.0, max(0.0, combined_efficiency))
        
        except Exception as e:
            self.logger.error(f"Erreur calcul efficacité: {e}")
            return 0.0
    
    def _calculate_performance_score(self, execution: ArbitrageExecution) -> float:
        """Calcule le score de performance d'une exécution"""
        try:
            score = 0.0
            
            # Score basé sur le succès
            if execution.status == "completed":
                score += 0.4
            elif execution.status == "partial":
                score += 0.2
            
            # Score basé sur le profit
            if execution.net_profit > 0:
                score += 0.3
            elif execution.net_profit > -execution.fees_paid:
                score += 0.1
            
            # Score basé sur l'efficacité
            efficiency = self._calculate_efficiency(execution)
            score += efficiency * 0.3
            
            return min(1.0, score)
        
        except Exception as e:
            self.logger.error(f"Erreur calcul score performance: {e}")
            return 0.0
    
    def _update_statistics(self, calculation: ProfitCalculation):
        """Met à jour les statistiques"""
        try:
            self.stats["total_calculations"] += 1
            
            if calculation.net_profit > 0:
                self.stats["profitable_opportunities"] += 1
            
            self.stats["total_gross_profit"] += calculation.gross_profit
            self.stats["total_fees"] += calculation.fees
            self.stats["total_net_profit"] += calculation.net_profit
            
            # Mettre à jour les moyennes
            if self.stats["total_calculations"] > 0:
                self.stats["avg_profit_percentage"] = (
                    self.stats["total_net_profit"] / 
                    (self.stats["total_calculations"] * calculation.quantity * calculation.buy_price) * 100
                )
            
            # Mettre à jour les meilleurs/pires
            if calculation.profit_percentage > self.stats["best_profit_percentage"]:
                self.stats["best_profit_percentage"] = calculation.profit_percentage
            
            if calculation.profit_percentage < self.stats["worst_profit_percentage"]:
                self.stats["worst_profit_percentage"] = calculation.profit_percentage
        
        except Exception as e:
            self.logger.error(f"Erreur mise à jour statistiques: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du calculateur"""
        return {
            **self.stats,
            "profitability_rate": (
                self.stats["profitable_opportunities"] / self.stats["total_calculations"] * 100
                if self.stats["total_calculations"] > 0 else 0
            ),
            "avg_fees_per_trade": (
                self.stats["total_fees"] / self.stats["total_calculations"]
                if self.stats["total_calculations"] > 0 else 0
            )
        }
    
    def get_recent_calculations(self, limit: int = 10) -> List[ProfitCalculation]:
        """Retourne les calculs récents"""
        return sorted(
            self.calculation_history,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]
    
    def get_best_opportunities(self, limit: int = 10) -> List[ProfitCalculation]:
        """Retourne les meilleures opportunités"""
        return sorted(
            self.calculation_history,
            key=lambda x: x.net_profit,
            reverse=True
        )[:limit]


# Instance globale du calculateur de profit
profit_calculator = ProfitCalculator()