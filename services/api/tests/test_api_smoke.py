from fastapi.testclient import TestClient

from services.api.app.main import app


client = TestClient(app)


def test_healthcheck_and_overview_routes() -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    overview = client.get("/api/v1/projects/legacycart/overview")
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["id"] == "legacycart"
    assert payload["recommendedProvider"] == "AWS"


def test_report_export_route_returns_pdf() -> None:
    response = client.get("/api/v1/projects/legacycart/reports/report-executive/export?format=pdf")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
