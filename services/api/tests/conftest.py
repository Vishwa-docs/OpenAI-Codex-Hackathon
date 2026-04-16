from __future__ import annotations

import sys
from pathlib import Path

import pytest

from services.api.app.dependencies import (
    get_orchestrator,
    get_report_exporter,
    get_seed_repository,
)


ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)


@pytest.fixture(autouse=True)
def reset_seed_state() -> None:
    get_orchestrator.cache_clear()
    get_report_exporter.cache_clear()
    get_seed_repository.cache_clear()
    yield
    get_orchestrator.cache_clear()
    get_report_exporter.cache_clear()
    get_seed_repository.cache_clear()
