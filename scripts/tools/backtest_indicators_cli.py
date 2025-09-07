import argparse
import json
from typing import List, Dict, Any

from src.ai.feature_engineering.backtest_indicators import backtest_price_only, BacktestConfig


def load_dummy_sequence() -> tuple:
    # Placeholder: l’utilisateur remplacera par ses loaders
    platform_prices_seq: List[Dict[str, Dict[str, Any]]] = []
    price_history_seq: List[List[Dict[str, Any]]] = []
    spread_series_seq: List[List[float]] = []
    return platform_prices_seq, price_history_seq, spread_series_seq


def main():
    parser = argparse.ArgumentParser(description="Backtest simple d'indicateurs prix-only")
    parser.add_argument("symbol", type=str, help="Symbole (ex: BTC)")
    parser.add_argument("buy_exchange", type=str, help="Exchange d'achat")
    parser.add_argument("sell_exchange", type=str, help="Exchange de vente")
    parser.add_argument("--entry", type=float, default=0.0, help="Seuil d'entrée du signal")
    parser.add_argument("--tp", type=float, default=0.005, help="Take profit (fraction)")
    parser.add_argument("--sl", type=float, default=0.005, help="Stop loss (fraction)")

    args = parser.parse_args()

    platform_prices_seq, price_history_seq, spread_series_seq = load_dummy_sequence()

    cfg = BacktestConfig(entry_threshold=args.entry, take_profit=args.tp, stop_loss=args.sl)
    result = backtest_price_only(
        symbol=args.symbol,
        platform_prices_seq=platform_prices_seq,
        buy_platform=args.buy_exchange,
        sell_platform=args.sell_exchange,
        price_history_seq=price_history_seq,
        spread_series_seq=spread_series_seq,
        config=cfg,
    )

    print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":
    main()