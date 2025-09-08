import asyncio
import pytest

from src.database.database import init_database
from src.database.repositories import MarketAbuseAlertRepository, OpportunityRepository
from src.monitoring.market_abuse.types import MarketAbuseAlert, MarketAbuseType
from src.monitoring.market_abuse.sinks import DatabaseAlertSink
from src.monitoring.market_abuse.opportunities import Opportunity
from src.monitoring.market_abuse.opportunity_sinks import DatabaseOpportunitySink
from datetime import datetime


@pytest.mark.asyncio
async def test_db_persistence_alerts_and_opportunities_or_skip():
    # Tente d'initialiser la DB, skip si indisponible
    try:
        db = await init_database()
    except Exception:
        pytest.skip("Base de données indisponible - test d'intégration sauté")
        return

    # Persister une alerte via sink DB
    alert = MarketAbuseAlert(
        timestamp=datetime.utcnow(),
        symbol="BTC/USDT",
        type=MarketAbuseType.PUMP_AND_DUMP,
        severity=0.7,
        message="PUMP suspect",
        metadata={"price_change": 0.05},
    )
    alert_sink = DatabaseAlertSink()
    await alert_sink.emit_async([alert])

    # Persister une opportunité via sink DB
    opp = Opportunity(
        timestamp=datetime.utcnow(),
        symbol="BTC/USDT",
        kind="volatility_breakout_long",
        confidence=0.8,
        rationale="from test",
    )
    opp_sink = DatabaseOpportunitySink()
    await opp_sink.emit_async([opp])

    # Vérifier lecture via repositories
    async with db.get_session() as session:
        ar = MarketAbuseAlertRepository(session)
        orp = OpportunityRepository(session)
        alerts = await ar.get_recent(symbol="BTC/USDT", limit=5)
        opps = await orp.get_recent(symbol="BTC/USDT", limit=5)
        assert len(alerts) >= 1
        assert len(opps) >= 1

