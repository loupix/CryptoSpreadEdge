import asyncio
import os
import json
from typing import List

from connectors.connector_factory import connector_factory
from arbitrage.arbitrage_engine import arbitrage_engine
from arbitrage.price_monitor import price_monitor
from arbitrage.execution_engine import execution_engine
from arbitrage.risk_manager import arbitrage_risk_manager


async def connect_platforms(exchanges: List[str]) -> None:
    await connector_factory.create_multiple_connectors(exchanges)
    await connector_factory.connect_all()


async def run(exchanges: List[str], symbols: List[str], duration: int, dry_run: bool, json_summary: bool) -> None:
    os.environ["CSE_EXCHANGES"] = ",".join(exchanges)
    os.environ["CSE_SYMBOLS"] = ",".join(symbols)
    os.environ["CSE_DRY_RUN"] = "1" if dry_run else "0"

    if duration <= 10:
        os.environ["CSE_QUICK"] = "1"
        os.environ["CSE_NO_ALT"] = "1"

    await connect_platforms(exchanges)

    await price_monitor.start()
    await execution_engine.start()
    await arbitrage_risk_manager.start_monitoring()

    arb_task = asyncio.create_task(arbitrage_engine.start())

    try:
        remaining = duration
        while remaining > 0:
            await asyncio.sleep(1)
            remaining -= 1
    finally:
        await arbitrage_engine.stop()
        await arbitrage_risk_manager.stop_monitoring()
        await execution_engine.stop()
        await price_monitor.stop()
        try:
            await asyncio.wait_for(arb_task, timeout=2)
        except Exception:
            pass

        stats = getattr(arbitrage_engine, "get_statistics", lambda: {})()
        if json_summary:
            print(json.dumps({
                "opportunities_found": stats.get("opportunities_found", 0),
                "opportunities_executed": stats.get("opportunities_executed", 0),
                "net_profit": stats.get("net_profit", 0.0)
            }))
        else:
            print("\nRésumé:")
            if stats:
                print(f"  Opportunités: {stats.get('opportunities_found', 0)} | Exécutées: {stats.get('opportunities_executed', 0)} | Profit net: {stats.get('net_profit', 0.0)}")
            else:
                print("  (Pas de statistiques disponibles)")

