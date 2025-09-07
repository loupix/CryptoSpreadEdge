#!/usr/bin/env python3
"""
Entrée unifiée: indicateurs -> arbitrage -> exécution
"""

import asyncio
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
os.environ.setdefault("PYTHONPATH", "")
os.environ["PYTHONPATH"] = f"{SRC_PATH}{os.pathsep}" + os.environ["PYTHONPATH"]

# Assurer les imports après PYTHONPATH
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_PATH))

from app.cli_options import load_options  # type: ignore
from app.orchestrator import run  # type: ignore


def main() -> None:
    exchanges, symbols, duration, dry_run, no_alt, json_summary = load_options()

    if no_alt:
        os.environ["CSE_NO_ALT"] = "1"

    try:
        asyncio.run(run(exchanges, symbols, duration, dry_run, json_summary))
    except Exception as exc:
        print(f"❌ Erreur: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

