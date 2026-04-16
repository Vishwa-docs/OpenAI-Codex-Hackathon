from __future__ import annotations

from functools import lru_cache

from .domain.repository import SeedRepository
from .services.orchestration import AssessmentOrchestrator
from .services.reporting import ReportExporter


@lru_cache
def get_seed_repository() -> SeedRepository:
    return SeedRepository()


@lru_cache
def get_orchestrator() -> AssessmentOrchestrator:
    return AssessmentOrchestrator(get_seed_repository())


@lru_cache
def get_report_exporter() -> ReportExporter:
    return ReportExporter()

