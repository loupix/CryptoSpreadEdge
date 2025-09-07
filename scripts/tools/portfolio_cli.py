import argparse
import asyncio
import json
import logging
from typing import Dict

from src.portfolio.portfolio_service import portfolio_aggregator
from src.portfolio.optimizer import optimizer


async def cmd_show(args: argparse.Namespace) -> int:
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    await portfolio_aggregator.refresh()
    positions = portfolio_aggregator.consolidate_positions()
    balances = {ex: [b.__dict__ for b in bl] for ex, bl in portfolio_aggregator.get_balances().items()}
    out = {
        "last_refresh": "done",
        "positions": positions,
        "balances": balances,
    }
    print(json.dumps(out, indent=2))
    return 0


async def cmd_rebalance(args: argparse.Namespace) -> int:
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    await portfolio_aggregator.refresh()
    positions = portfolio_aggregator.consolidate_positions()

    # Charger mu et cov simples depuis un fichier JSON si fourni, sinon fallback naïf
    expected_returns: Dict[str, float] = {}
    covariance: Dict[str, Dict[str, float]] = {}

    if args.inputs_json:
        with open(args.inputs_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            expected_returns = data.get("expected_returns", {})
            covariance = data.get("covariance", {})
    else:
        # naive: mu = 0.0 et cov diagonale pour les symboles présents
        for sym in positions.keys():
            expected_returns[sym] = 0.0
        for si in positions.keys():
            covariance.setdefault(si, {})
            for sj in positions.keys():
                covariance[si][sj] = 0.0 if si != sj else 1.0

    cov_map = {(i, j): float(covariance.get(i, {}).get(j, 0.0)) for i in covariance for j in covariance[i]}

    if args.method == "mv":
        weights = optimizer.mean_variance_weights(
            expected_returns=expected_returns,
            covariance_matrix=cov_map,
            risk_aversion=args.risk_aversion,
            min_weight=args.min_weight,
            max_weight=args.max_weight,
            target_leverage=args.target_leverage,
        )
    else:
        weights = optimizer.risk_parity_weights(
            covariance_matrix=cov_map,
            min_weight=args.min_weight,
            max_weight=args.max_weight,
            target_leverage=args.target_leverage,
            iterations=args.iterations,
            lr=args.lr,
        )

    print(json.dumps({"weights": weights}, indent=2))
    return 0


async def cmd_cov(args: argparse.Namespace) -> int:
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    symbols = args.symbols
    cov = await portfolio_aggregator.compute_price_covariance(symbols, points=args.points)
    # sérialiser en dict de dict
    out = {}
    for (i, j), v in cov.items():
        out.setdefault(i, {})[j] = v
    print(json.dumps({"covariance": out}, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI Portefeuille CryptoSpreadEdge")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")

    p_show = sub.add_parser("show", parents=[common], help="Afficher portefeuille agrégé")
    p_show.set_defaults(func=lambda a: asyncio.run(cmd_show(a)))

    p_reb = sub.add_parser("rebalance", parents=[common], help="Calculer une allocation cible")
    p_reb.add_argument("--method", choices=["mv", "rp"], default="mv", help="mv=mean-variance, rp=risk-parity")
    p_reb.add_argument("--inputs-json", type=str, default=None, help="Fichier JSON {expected_returns, covariance}")
    p_reb.add_argument("--risk-aversion", type=float, default=3.0)
    p_reb.add_argument("--min-weight", type=float, default=0.0)
    p_reb.add_argument("--max-weight", type=float, default=0.3)
    p_reb.add_argument("--target-leverage", type=float, default=1.0)
    p_reb.add_argument("--iterations", type=int, default=200)
    p_reb.add_argument("--lr", type=float, default=0.1)
    p_reb.set_defaults(func=lambda a: asyncio.run(cmd_rebalance(a)))

    p_cov = sub.add_parser("cov", parents=[common], help="Exporter covariance des rendements log")
    p_cov.add_argument('--symbols', nargs='+', required=True)
    p_cov.add_argument('--points', type=int, default=300)
    p_cov.set_defaults(func=lambda a: asyncio.run(cmd_cov(a)))

    args = parser.parse_args()
    exit_code = args.func(args)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()

