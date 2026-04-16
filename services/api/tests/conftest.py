from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

import pytest

from services.api.app.core.db import get_engine
from services.api.app.core.settings import get_settings
from services.api.app.dependencies import (
    get_orchestrator,
    get_report_exporter,
    get_seed_repository,
)

@pytest.fixture(autouse=True)
def reset_seed_state() -> Generator[None, None, None]:
    get_engine.cache_clear()
    get_settings.cache_clear()
    get_orchestrator.cache_clear()
    get_report_exporter.cache_clear()
    get_seed_repository.cache_clear()
    yield
    get_engine.cache_clear()
    get_settings.cache_clear()
    get_orchestrator.cache_clear()
    get_report_exporter.cache_clear()
    get_seed_repository.cache_clear()
