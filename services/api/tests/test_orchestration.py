from services.api.app.domain.repository import SeedRepository
from services.api.app.services.orchestration import AssessmentOrchestrator
from services.api.app.services.reporting import ReportExporter


def test_orchestrator_builds_deterministic_assessment_bundle() -> None:
    orchestrator = AssessmentOrchestrator(SeedRepository())

    bundle = orchestrator.build_assessment("legacycart")

    assert bundle.overview.readiness_score == 52
    assert bundle.run.final_recommendation.decision == "defer"
    assert bundle.run.final_recommendation.recommended_provider == "AWS"
    assert len(bundle.findings) >= 5
    assert all(finding.evidence for finding in bundle.findings)
    assert any(entry.status == "proposed" for entry in bundle.registry_entries)
    critic = next(item for item in bundle.run.agent_outputs if item.agent_key == "citation_evidence_critic")
    assert critic.structured_output["citationCoverage"] == 1.0


def test_report_exporter_generates_pdf_bytes() -> None:
    report = SeedRepository().get_project("legacycart").reports[0]

    payload, media_type = ReportExporter().export(report, "pdf")

    assert media_type == "application/pdf"
    assert payload.startswith(b"%PDF")
