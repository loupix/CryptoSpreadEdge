import argparse
from typing import List, Tuple

from utils.symbols.normalizer import SymbolNormalizer


def load_options() -> Tuple[List[str], List[str], int, bool, bool, bool]:
    parser = argparse.ArgumentParser(description="Démarrage unifié CryptoSpreadEdge")
    parser.add_argument("--exchanges", type=str, default="binance,coinbase")
    parser.add_argument("--symbols", type=str, default="BTC,ETH,BNB")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--no-alt", action="store_true")
    parser.add_argument("--json-summary", action="store_true")

    args = parser.parse_args()
    exchanges = [e.strip() for e in args.exchanges.split(",") if e.strip()]
    raw_symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    symbols = SymbolNormalizer().normalize_for_exchanges(exchanges, raw_symbols)

    return exchanges, symbols, args.duration, args.dry_run, args.no_alt, args.json_summary

