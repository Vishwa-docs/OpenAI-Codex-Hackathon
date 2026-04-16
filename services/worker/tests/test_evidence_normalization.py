from pathlib import Path

from services.worker.app.scanner import LegacyCartScanner


def test_secret_evidence_is_normalized_from_config_file() -> None:
    root = Path("demo-systems/legacycart")
    scanner = LegacyCartScanner(root)
    scanner._discover_components()
    scanner._scan_file(root / "backend" / "config" / "application-prod.yml")

    evidence = [item for item in scanner.state.evidence if item.evidence_type == "secret"]

    assert evidence, "expected at least one normalized secret evidence item"
    assert evidence[0].source_uri == "backend/config/application-prod.yml"
    assert evidence[0].normalized_value == "Hardcoded database connection string"
    assert evidence[0].confidence >= 0.98

