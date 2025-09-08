from datetime import datetime, timedelta

from src.monitoring.market_abuse.calibration import AutoThresholdCalibrator


def test_auto_threshold_calibration_adjusts_up_and_down():
    calib = AutoThresholdCalibrator(target_alerts_per_minute=1.0, window_minutes=1, adjust_step=0.1)
    now = datetime.utcnow()
    # Trop d'alertes -> seuil monte
    calib.record_alerts("BTC/USDT", count=5, now=now)
    t1 = calib.get_threshold("BTC/USDT")
    assert t1 > 0.5
    # Peu d'alertes -> seuil baisse
    calib.record_alerts("BTC/USDT", count=0, now=now + timedelta(seconds=10))
    calib.record_alerts("BTC/USDT", count=0, now=now + timedelta(seconds=20))
    calib.record_alerts("BTC/USDT", count=0, now=now + timedelta(seconds=30))
    calib.record_alerts("BTC/USDT", count=0, now=now + timedelta(seconds=40))
    t2 = calib.get_threshold("BTC/USDT")
    assert t2 <= t1

