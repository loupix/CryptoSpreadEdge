import asyncio
import pytest
import os
import sys

# Ajouter la racine du projet et `src/` au PYTHONPATH pour permettre `import src...` et `import connectors...`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_ROOT = os.path.join(PROJECT_ROOT, 'src')
for path in [PROJECT_ROOT, SRC_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
