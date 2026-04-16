from __future__ import annotations

from functools import lru_cache

from .core.settings import get_settings
from .domain.repository import SeedRepository
from .services.chat import EvidenceGroundedChatService
from .services.orchestration import AssessmentOrchestrator
from .services.reporting import ReportExporter


@lru_cache
def get_seed_repository() -> SeedRepository:
    return SeedRepository()


@lru_cache
def get_orchestrator() -> AssessmentOrchestrator:
    return AssessmentOrchestrator(get_seed_repository(), get_chat_service())


@lru_cache
def get_report_exporter() -> ReportExporter:
    return ReportExporter()


@lru_cache
def get_chat_service() -> EvidenceGroundedChatService:
    return EvidenceGroundedChatService(get_settings())
