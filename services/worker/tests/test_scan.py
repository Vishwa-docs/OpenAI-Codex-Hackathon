from pathlib import Path

from services.worker.app.scanner import scan_legacycart


def test_scan_demo_system_produces_deterministic_assessment() -> None:
    root = Path("demo-systems/legacycart")
    result = scan_legacycart(root)

    assert result.target_name == "LegacyCart"
    assert result.summary.readiness_score == 52
    assert result.summary.recommendation == "defer until blockers are remediated"
    assert len(result.findings) >= 6
    assert len(result.dependencies) >= 4

    titles = {finding.title for finding in result.findings}
    assert "Hardcoded production database credentials are present" in titles
    assert "Shared NFS storage is used for invoice exports" in titles


def test_scan_is_stable() -> None:
    root = Path("demo-systems/legacycart")
    first = scan_legacycart(root).to_dict()
    second = scan_legacycart(root).to_dict()
    assert first == second

