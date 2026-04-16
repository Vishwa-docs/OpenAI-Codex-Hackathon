from fastapi.testclient import TestClient

from services.api.app.main import app

client = TestClient(app)


def test_workspace_context_exposes_seeded_demo_tenant() -> None:
    response = client.get("/api/v1/workspaces/workspace-demo/context")

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace"]["id"] == "workspace-demo"
    assert payload["workspace"]["mode"] == "demo"
    assert payload["organization"]["id"] == "org-demo"
    assert payload["clientAccounts"]
    assert any(project["id"] == "legacycart" for project in payload["projects"])


def test_workspace_project_creation_persists_and_updates_dashboard() -> None:
    create = client.post(
        "/api/v1/workspaces/workspace-demo/projects",
        json={
            "name": "Phoenix Order Modernization",
            "clientName": "Phoenix Health",
            "sourceSystem": "On-prem VMware estate with PostgreSQL and cron jobs",
            "targetSystem": "AWS landing zone with managed PostgreSQL",
            "businessSummary": "Healthcare order orchestration with regional compliance boundaries.",
            "owner": "Taylor Reed",
            "primaryRegion": "ap-south-1",
            "complianceTags": ["HIPAA", "ISO 27001"],
        },
    )

    assert create.status_code == 201
    created = create.json()
    assert created["clientName"] == "Phoenix Health"
    assert created["phase"] == "Intake"
    assert created["status"] == "Draft intake"

    projects = client.get("/api/v1/workspaces/workspace-demo/projects")
    assert projects.status_code == 200
    project_payload = projects.json()
    assert any(project["id"] == created["id"] for project in project_payload)

    overview = client.get(f"/api/v1/projects/{created['id']}/overview")
    assert overview.status_code == 200
    assert overview.json()["clientName"] == "Phoenix Health"

    dashboard = client.get("/api/v1/dashboard/summary")
    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()
    assert dashboard_payload["activeProjects"] >= 2
    assert any(project["id"] == created["id"] for project in dashboard_payload["topProjects"])

    assessment = client.get(f"/api/v1/projects/{created['id']}/assessment")
    assert assessment.status_code == 200
    assessment_payload = assessment.json()
    assert assessment_payload["status"] == "queued"
    assert assessment_payload["finalRecommendation"]["label"] == "Assessment pending evidence ingestion"
