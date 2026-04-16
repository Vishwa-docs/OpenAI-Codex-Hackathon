from fastapi.testclient import TestClient

from services.worker.app.main import app

client = TestClient(app)


def test_worker_service_exposes_health_and_connector_catalog() -> None:
    health = client.get("/health")
    assert health.status_code == 200
    health_payload = health.json()
    assert health_payload["status"] == "ok"
    assert health_payload["service"] == "cloud-migration-cockpit-worker"
    assert health_payload["projectApiKeyHeader"] == "X-Project-Api-Key"

    catalog = client.get("/connectors/catalog")
    assert catalog.status_code == 200
    catalog_payload = catalog.json()
    assert {item["kind"] for item in catalog_payload} == {"local_directory", "github", "azure_repos"}
    assert any(item["validationEndpoint"] for item in catalog_payload)


def test_worker_service_scans_legacycart_and_returns_redacted_evidence() -> None:
    response = client.post("/scan", json={"rootPath": "demo-systems/legacycart"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"]["kind"] == "local_directory"
    assert len(payload["pipelines"]) == 6
    secret_evidence = [item for item in payload["evidence"] if item["evidenceType"] == "secret"]
    assert secret_evidence
    assert all(item["redactionApplied"] for item in secret_evidence)
