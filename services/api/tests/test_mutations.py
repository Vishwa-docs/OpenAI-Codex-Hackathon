from fastapi.testclient import TestClient

from services.api.app.main import app


client = TestClient(app)


def test_project_resources_can_be_created_and_persisted() -> None:
    source = client.post(
        "/api/v1/projects/legacycart/source-connections",
        json={
            "kind": "github",
            "name": "Northstar GitHub",
            "target": "github.com/northstar-retail/platform",
            "branch": "main",
            "mode": "discovery",
            "credentialLabel": "GitHub app installation",
            "credentialKind": "oauth",
            "notes": ["Repo metadata ingestion approved for discovery."],
        },
    )
    assert source.status_code == 201
    source_payload = source.json()
    assert source_payload["name"] == "Northstar GitHub"
    assert source_payload["status"] == "connected"

    cloud = client.post(
        "/api/v1/projects/legacycart/cloud-connections",
        json={
            "provider": "aws",
            "name": "Northstar AWS Sandbox",
            "accountLabel": "AWS Migration Sandbox",
            "regionScope": ["us-east-1", "ap-south-1"],
            "mode": "dry_run",
            "credentialLabel": "Cockpit dry-run role",
            "credentialKind": "assumed_role",
            "notes": ["Dry-run only until execution approval is granted."],
        },
    )
    assert cloud.status_code == 201
    cloud_payload = cloud.json()
    assert cloud_payload["provider"] == "aws"
    assert cloud_payload["mode"] == "dry_run"

    chat = client.post(
        "/api/v1/projects/legacycart/chat/messages",
        json={
            "author": "Taylor Reed",
            "role": "human",
            "content": "Please queue a fresh assessment after the new source connection is added.",
        },
    )
    assert chat.status_code == 201
    chat_payload = chat.json()
    assert chat_payload["author"] == "Taylor Reed"
    assert chat_payload["role"] == "human"

    source_connections = client.get("/api/v1/projects/legacycart/source-connections").json()
    assert any(item["name"] == "Northstar GitHub" for item in source_connections)

    cloud_connections = client.get("/api/v1/projects/legacycart/cloud-connections").json()
    assert any(item["name"] == "Northstar AWS Sandbox" for item in cloud_connections)

    chat_messages = client.get("/api/v1/projects/legacycart/chat/messages").json()
    assert any(item["content"].startswith("Please queue a fresh assessment") for item in chat_messages)


def test_assessment_run_can_be_requested_and_is_audited() -> None:
    response = client.post(
        "/api/v1/projects/legacycart/assessment-runs",
        json={"mode": "local_worker", "triggeredBy": "Taylor Reed"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["mode"] == "local_worker"
    assert payload["id"].startswith("run-legacycart-local-worker")

    assessment_runs = client.get("/api/v1/projects/legacycart/assessment-runs").json()
    assert any(item["id"] == payload["id"] for item in assessment_runs)

    audit_events = client.get("/api/v1/projects/legacycart/audit-events").json()
    assert any(event["action"] == "assessment.requested" for event in audit_events)
