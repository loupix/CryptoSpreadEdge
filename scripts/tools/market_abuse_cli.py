import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime

# Rendre le script autonome pour les imports lorsqu'il est exécuté en direct
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for p in (str(_ROOT), str(_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from src.monitoring.market_abuse.stream_monitor import MarketAbuseStreamMonitor
from src.monitoring.market_abuse.sinks import FileAlertSink, PrometheusAlertSink
from src.monitoring.market_abuse.types import TradeEvent


def parse_row(row, symbol_col, price_col, qty_col, ts_col, side_col):
    ts = datetime.fromisoformat(row[ts_col])
    return TradeEvent(
        timestamp=ts,
        symbol=row[symbol_col],
        price=float(row[price_col]),
        quantity=float(row[qty_col]),
        side=row.get(side_col, "buy") or "buy",
    )


def main():
    parser = argparse.ArgumentParser(description="Analyse CSV pour détection d'abus de marché")
    parser.add_argument("--csv", required=True, help="Chemin du fichier CSV")
    parser.add_argument("--symbol", required=True, help="Symbole à analyser, ex: BTC/USDT")
    parser.add_argument("--ts-col", default="timestamp")
    parser.add_argument("--symbol-col", default="symbol")
    parser.add_argument("--price-col", default="price")
    parser.add_argument("--qty-col", default="quantity")
    parser.add_argument("--side-col", default="side")
    args = parser.parse_args()

    monitor = MarketAbuseStreamMonitor(symbol=args.symbol, sinks=[FileAlertSink(), PrometheusAlertSink()])
    with open(args.csv, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get(args.symbol_col) != args.symbol:
                continue
            trade = parse_row(row, args.symbol_col, args.price_col, args.qty_col, args.ts_col, args.side_col)
            alerts = monitor.on_trade(trade)
            for a in alerts:
                print(f"{a.timestamp.isoformat()} {a.symbol} {a.type.value} sev={a.severity:.2f} - {a.message}")


if __name__ == "__main__":
    main()

