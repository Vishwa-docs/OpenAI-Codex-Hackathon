from pathlib import Path

from services.worker.app.scanner import scan_legacycart


def test_scan_tracks_source_metadata_and_pipeline_phases() -> None:
    result = scan_legacycart(Path("demo-systems/legacycart"))

    assert result.source.kind == "local_directory"
    assert result.source.connection_id == "source-local-legacycart"
    assert len(result.pipelines) == 6
    assert result.pipelines[1].pipeline_key == "evidence_ingestion"
    assert result.pipelines[-1].status == "succeeded"


def test_scan_redacts_secret_material_in_normalized_evidence() -> None:
    result = scan_legacycart(Path("demo-systems/legacycart"))

    secret_evidence = [item for item in result.evidence if item.evidence_type == "secret"]
    assert secret_evidence
    assert all("legacycart-prod-password" not in item.excerpt for item in secret_evidence)
    assert any(item.redaction_applied for item in secret_evidence)
    assert all(item.normalized_value for item in secret_evidence)


def test_scan_exposes_repo_connector_handoff_templates() -> None:
    result = scan_legacycart(Path("demo-systems/legacycart"))

    connector_kinds = {item.kind for item in result.connector_handoffs}
    assert connector_kinds == {"github", "azure_repos"}
    assert any(item.required_credentials for item in result.connector_handoffs)
