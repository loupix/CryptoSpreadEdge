#!/usr/bin/env python3
"""
Entrée unifiée: indicateurs -> arbitrage -> exécution

Options CLI:
  --exchanges: liste d'exchanges séparés par des virgules (ex: binance,coinbase)
  --symbols: liste de symboles séparés par des virgules (ex: BTC,ETH)
  --duration: durée en secondes avant arrêt gracieux
  --dry-run: n'exécute pas d'ordres réels (mode démonstration)
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path
from typing import List

# Assurer l'accès à src/ et racine (pour imports config/*)
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_PATH))

from arbitrage.arbitrage_engine import arbitrage_engine  # type: ignore
from arbitrage.price_monitor import price_monitor  # type: ignore
from arbitrage.execution_engine import execution_engine  # type: ignore
from arbitrage.risk_manager import arbitrage_risk_manager  # type: ignore
from connectors.connector_factory import connector_factory  # type: ignore


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("unified_start")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Démarrage unifié CryptoSpreadEdge")
    parser.add_argument(
        "--exchanges",
        type=str,
        default="binance,coinbase",
        help="Exchanges à connecter (séparés par des virgules)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default="BTC,ETH,BNB",
        help="Symboles à surveiller (séparés par des virgules)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Durée en secondes avant l'arrêt"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode démonstration: pas d'ordres réels"
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Réduire les logs (masquer sources externes et warnings)"
    )
    parser.add_argument(
        "--no-alt",
        action="store_true",
        help="Désactiver les sources alternatives externes"
    )
    return parser.parse_args()


async def connect_platforms(exchanges: List[str]) -> None:
    # Création des connecteurs (sans clés -> mode lecture/échec, selon implémentation)
    await connector_factory.create_multiple_connectors(exchanges)
    await connector_factory.connect_all()


async def unified_run(exchanges: List[str], symbols: List[str], duration: int, dry_run: bool) -> None:
    print("🚀 CryptoSpreadEdge - Démarrage unifié (indicateurs → arbitrage → exécution)")
    print("=" * 72)
    print(f"Exchanges: {', '.join(exchanges)}")
    print(f"Symboles: {', '.join(symbols)}")
    print(f"Durée: {duration}s | Dry-run: {'oui' if dry_run else 'non'}")
    print("=" * 72)

    # Connecter les plateformes
    await connect_platforms(exchanges)

    # Démarrer les composants
    await price_monitor.start()
    await execution_engine.start()
    await arbitrage_risk_manager.start_monitoring()

    quick_mode = os.environ.get("CSE_QUICK", "0") == "1"
    # Toujours démarrer l'arbitrage en tâche de fond pour garantir l'arrêt à durée fixe
    arb_task = asyncio.create_task(arbitrage_engine.start())

    # Boucle de durée fixe
    try:
        remaining = duration
        while remaining > 0:
            await asyncio.sleep(1)
            remaining -= 1
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    finally:
        # Arrêt ordonné
        await arbitrage_engine.stop()
        await arbitrage_risk_manager.stop_monitoring()
        await execution_engine.stop()
        await price_monitor.stop()
        try:
            await asyncio.wait_for(arb_task, timeout=2)
        except Exception:
            pass


def main() -> None:
    # Créer le dossier de logs
    Path("logs").mkdir(exist_ok=True)

    args = parse_args()
    exchanges = [e.strip() for e in args.exchanges.split(",") if e.strip()]
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    # Exposer via variables d'environnement (à exploiter si nécessaire par les composants)
    os.environ["CSE_EXCHANGES"] = ",".join(exchanges)
    os.environ["CSE_SYMBOLS"] = ",".join(symbols)
    os.environ["CSE_DRY_RUN"] = "1" if args.dry_run else "0"

    # Mode rapide automatique pour durées courtes
    if args.duration <= 10:
        os.environ["CSE_QUICK"] = "1"
        os.environ["CSE_NO_ALT"] = "1"

    # Mode silencieux: réduire le bruit des logs externes et warnings
    if args.no_alt:
        os.environ["CSE_NO_ALT"] = "1"

    if args.silent or args.duration <= 10:
        import logging as _logging
        _logging.getLogger("data_sources.alternative_sources").setLevel(_logging.CRITICAL)
        _logging.getLogger("arbitrage.price_monitor").setLevel(_logging.ERROR)
        _logging.getLogger("ccxt").setLevel(_logging.CRITICAL)

    try:
        # S'assurer que PYTHONPATH prend en compte src/ à l'exécution
        os.environ.setdefault("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = f"{SRC_PATH}{os.pathsep}" + os.environ["PYTHONPATH"]
        asyncio.run(unified_run(exchanges, symbols, args.duration, args.dry_run))
    except Exception as exc:
        print(f"❌ Erreur: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

