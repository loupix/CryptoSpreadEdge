import os
import sys
import csv
import subprocess
from datetime import datetime
from pathlib import Path


def test_cli_runs_and_outputs_alerts(tmp_path: Path):
    # Préparer un CSV minimal qui déclenche un pump
    csv_path = tmp_path / "trades.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "symbol", "price", "quantity", "side"])
        writer.writeheader()
        base = datetime.utcnow().isoformat()
        # 20 trades stables
        for i in range(20):
            writer.writerow({"timestamp": base, "symbol": "BTC/USDT", "price": 100.0, "quantity": 1.0, "side": "buy"})
        # 10 trades pump
        for i in range(10):
            writer.writerow({"timestamp": base, "symbol": "BTC/USDT", "price": 105.0, "quantity": 3.0, "side": "buy"})

    # Exécuter le CLI
    cmd = [sys.executable, "scripts/tools/market_abuse_cli.py", "--csv", str(csv_path), "--symbol", "BTC/USDT"]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, cwd=str(Path.cwd()))
    except subprocess.CalledProcessError as e:
        output = e.output
        raise

    # Vérifier que des alertes sont émises
    assert "BTC/USDT" in output
    assert ("PUMP suspect" in output) or ("DUMP suspect" in output)

