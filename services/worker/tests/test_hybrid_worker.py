from pathlib import Path

from fastapi.testclient import TestClient

from services.worker.app.main import app
from services.worker.app.scanner import scan_legacycart

client = TestClient(app)


def test_worker_health_reports_connector_modes_and_api_key_hooks() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "cloud-migration-cockpit-worker"
    assert payload["projectApiKeyHeader"] == "X-Project-Api-Key"
    assert set(payload["supportedConnectors"]) == {"local_directory", "github", "azure_repos"}
    assert payload["connectorModes"]["github"] == "prepared_read_only"


def test_worker_connector_validation_and_sync_support_local_github_and_azure_repos() -> None:
    local_request = {"kind": "local_directory", "projectId": "legacycart", "rootPath": "demo-systems/legacycart"}
    local_validation = client.post("/connectors/validate", json=local_request)
    assert local_validation.status_code == 200
    validation_payload = local_validation.json()
    assert validation_payload["kind"] == "local_directory"
    assert validation_payload["status"] == "ready"
    assert validation_payload["validationChecks"]

    local_sync = client.post("/connectors/sync", json=local_request)
    assert local_sync.status_code == 200
    sync_payload = local_sync.json()
    assert sync_payload["status"] == "completed"
    assert sync_payload["scan"]["summary"]["readinessScore"] == 52
    assert sync_payload["upstreamRecord"]["projectId"] == "legacycart"

    github_request = {
        "kind": "github",
        "projectId": "legacycart",
        "repositoryUrl": "https://github.com/northstar/legacycart",
        "branch": "main",
        "projectApiKey": "proj-test-1234",
    }
    github_validation = client.post("/connectors/validate", json=github_request)
    assert github_validation.status_code == 200
    assert github_validation.json()["status"] == "ready"

    github_sync = client.post("/connectors/sync", json=github_request)
    assert github_sync.status_code == 200
    github_sync_payload = github_sync.json()
    assert github_sync_payload["status"] == "prepared"
    assert github_sync_payload["scan"]["status"] == "prepared_read_only"
    assert github_sync_payload["scan"]["readOnly"] is True
    assert github_sync_payload["upstreamRecord"]["source"]["kind"] == "git_repository"
    assert github_sync_payload["upstreamRecord"]["connectorHandoffs"][0]["kind"] == "github"

    azure_request = {
        "kind": "azure_repos",
        "projectId": "legacycart",
        "organizationUrl": "https://dev.azure.com/northstar",
        "projectName": "LegacyCart",
        "repositoryName": "legacycart",
        "branch": "main",
        "projectApiKey": "proj-test-5678",
    }
    azure_sync = client.post("/connectors/sync", json=azure_request)
    assert azure_sync.status_code == 200
    azure_sync_payload = azure_sync.json()
    assert azure_sync_payload["status"] == "prepared"
    assert azure_sync_payload["scan"]["readOnly"] is True
    assert azure_sync_payload["upstreamRecord"]["source"]["kind"] == "git_repository"


def test_worker_connector_validation_blocks_remote_sync_without_api_key() -> None:
    request = {
        "kind": "github",
        "projectId": "legacycart",
        "repositoryUrl": "https://github.com/northstar/legacycart",
        "branch": "main",
    }

    validation = client.post("/connectors/validate", json=request)
    assert validation.status_code == 200
    assert validation.json()["status"] == "needs_credentials"

    sync_response = client.post("/connectors/sync", json=request)
    assert sync_response.status_code == 200
    sync_payload = sync_response.json()
    assert sync_payload["status"] == "blocked"
    assert sync_payload["upstreamRecord"] is None


def test_scan_result_includes_persistable_upstream_record() -> None:
    result = scan_legacycart(Path("demo-systems/legacycart"))

    upstream_record = result.to_upstream_record()
    assert upstream_record["projectId"] == "legacycart"
    assert upstream_record["scanId"] == result.scan_id
    assert upstream_record["summary"]["readinessScore"] == result.summary.readiness_score
    assert len(upstream_record["findings"]) == len(result.findings)
    assert upstream_record["connectorHandoffs"]
