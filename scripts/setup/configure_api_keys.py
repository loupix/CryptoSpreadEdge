#!/usr/bin/env python3

"""
Script CLI simple pour gérer les clés API avec APIKeysManager.
Usage:
  - Ajouter/mettre à jour: python scripts/setup/configure_api_keys.py set <platform> <api_key> [secret_key] [passphrase]
  - Lister:               python scripts/setup/configure_api_keys.py list
  - Exporter:             python scripts/setup/configure_api_keys.py export <path>
  - Importer:             python scripts/setup/configure_api_keys.py import <path>
  - Depuis env:           python scripts/setup/configure_api_keys.py load-env

Plateformes supportées pour data sources: coinmarketcap, coingecko, cryptocompare, messari, glassnode, dune, thegraph, moralis, alchemy,
ainsi que les sources publiques nommées *_public si besoin.
"""

import sys
from pathlib import Path

# Assurer que le dossier src est importable
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config.api_keys_manager import api_keys_manager


def cmd_set(args):
    if len(args) < 2:
        print("Usage: set <platform> <api_key> [secret_key] [passphrase]")
        return 1
    platform = args[0]
    api_key = args[1]
    secret_key = args[2] if len(args) > 2 else ""
    passphrase = args[3] if len(args) > 3 else ""
    ok = api_keys_manager.add_api_key(
        platform=platform,
        api_key=api_key,
        secret_key=secret_key,
        passphrase=passphrase,
        enabled=True,
    )
    print("OK" if ok else "ERROR")
    return 0 if ok else 1


def cmd_list(_):
    keys = api_keys_manager.get_all_api_keys()
    if not keys:
        print("No API keys stored")
        return 0
    for platform, key in keys.items():
        masked_api = (key.api_key[:4] + "***" + key.api_key[-4:]) if key.api_key else ""
        print(f"{platform}: enabled={key.enabled} api={masked_api} secret={'***' if key.secret_key else ''} passphrase={'***' if key.passphrase else ''}")
    return 0


def cmd_export(args):
    if len(args) < 1:
        print("Usage: export <path>")
        return 1
    ok = api_keys_manager.export_keys(args[0], include_secrets=False)
    print("OK" if ok else "ERROR")
    return 0 if ok else 1


def cmd_import(args):
    if len(args) < 1:
        print("Usage: import <path>")
        return 1
    ok = api_keys_manager.import_keys(args[0])
    print("OK" if ok else "ERROR")
    return 0 if ok else 1


def cmd_load_env(_):
    """Charge un set basique depuis les variables d'environnement si présentes."""
    import os
    candidates = [
        "coinmarketcap", "cryptocompare", "glassnode", "messari",
    ]
    mapping = {
        "coinmarketcap": "CMC_API_KEY",
        "cryptocompare": "CRYPTOCOMPARE_API_KEY",
        "glassnode": "GLASSNODE_API_KEY",
        "messari": "MESSARI_API_KEY",
    }
    count = 0
    for platform in candidates:
        env_var = mapping.get(platform)
        value = os.getenv(env_var, "")
        if value:
            api_keys_manager.add_api_key(platform=platform, api_key=value, enabled=True)
            count += 1
    print(f"Loaded {count} keys from environment")
    return 0


COMMANDS = {
    "set": cmd_set,
    "list": cmd_list,
    "export": cmd_export,
    "import": cmd_import,
    "load-env": cmd_load_env,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd not in COMMANDS:
        print(__doc__)
        return 1
    return COMMANDS[cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())