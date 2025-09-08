import os
import pytest


def pytest_collection_modifyitems(session, config, items):
    enable_db = os.getenv("ENABLE_DB_INTEGRATION") == "1"
    enable_swarm = os.getenv("ENABLE_SWARM_TESTS") == "1"

    for item in list(items):
        path = str(item.fspath)
        if path.endswith("test_swarm_deployment.py") and not enable_swarm:
            item.add_marker(pytest.mark.skip(reason="ENABLE_SWARM_TESTS!=1 - skip tests swarm"))
        if path.endswith("test_postgresql_integration.py") and not enable_db:
            item.add_marker(pytest.mark.skip(reason="ENABLE_DB_INTEGRATION!=1 - skip tests DB lourds"))

