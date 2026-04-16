from fastapi.testclient import TestClient

from services.api.app.main import app


client = TestClient(app)


def test_vnext_project_resources_are_exposed() -> None:
    source_connections = client.get("/api/v1/projects/legacycart/source-connections")
    assert source_connections.status_code == 200
    source_payload = source_connections.json()
    assert {item["kind"] for item in source_payload} == {"local_path", "github", "azure_repos"}
    assert any(item["status"] == "connected" for item in source_payload)

    cloud_connections = client.get("/api/v1/projects/legacycart/cloud-connections")
    assert cloud_connections.status_code == 200
    cloud_payload = cloud_connections.json()
    assert {item["provider"] for item in cloud_payload} == {"aws", "gcp", "azure"}
    assert next(item for item in cloud_payload if item["provider"] == "aws")["mode"] == "discovery"

    assessment_runs = client.get("/api/v1/projects/legacycart/assessment-runs")
    assert assessment_runs.status_code == 200
    run_payload = assessment_runs.json()
    assert len(run_payload) >= 1
    assert run_payload[0]["pipelineSummaries"]

    agent_runs = client.get("/api/v1/projects/legacycart/agent-runs")
    assert agent_runs.status_code == 200
    agent_payload = agent_runs.json()
    assert any(item["agentKey"] == "iam_secrets_posture" for item in agent_payload)
    assert any(item["critic"] is True for item in agent_payload)

    eval_runs = client.get("/api/v1/projects/legacycart/eval-runs")
    assert eval_runs.status_code == 200
    eval_payload = eval_runs.json()
    assert len(eval_payload) >= 1
    assert any(metric["metricKey"] == "citation_coverage" for metric in eval_payload[0]["metrics"])

    factory_proposals = client.get("/api/v1/projects/legacycart/factory-proposals")
    assert factory_proposals.status_code == 200
    proposal_payload = factory_proposals.json()
    assert proposal_payload
    assert all(item["status"] == "proposed" for item in proposal_payload)
    assert any("requiredPermissions" in item for item in proposal_payload)

    chat_messages = client.get("/api/v1/projects/legacycart/chat/messages")
    assert chat_messages.status_code == 200
    chat_payload = chat_messages.json()
    assert len(chat_payload) >= 2
    assert {item["role"] for item in chat_payload} >= {"human", "ai"}


def test_planning_approval_can_transition_and_writes_audit_event() -> None:
    decision = client.post(
        "/api/v1/projects/legacycart/approvals/approval-planning/decision",
        json={"decision": "approved", "actor": "Taylor Reed", "comment": "Planning package is ready."},
    )

    assert decision.status_code == 200
    decision_payload = decision.json()
    assert decision_payload["state"] == "approved"
    assert decision_payload["approver"] == "Taylor Reed"

    approvals = client.get("/api/v1/projects/legacycart/approvals")
    planning = next(item for item in approvals.json() if item["id"] == "approval-planning")
    assert planning["state"] == "approved"

    audit_events = client.get("/api/v1/projects/legacycart/audit-events")
    assert any(event["action"] == "approval.decided" for event in audit_events.json())


def test_reports_cover_msp_facing_variants() -> None:
    reports = client.get("/api/v1/projects/legacycart/reports")
    assert reports.status_code == 200

    report_kinds = {item["kind"] for item in reports.json()}
    assert {
        "executive_summary",
        "technical_dossier",
        "cost_report",
        "risk_report",
        "architecture_recommendation",
        "migration_wave_plan",
        "cutover_rollback",
        "operations_checklist",
    } <= report_kinds


def test_can_create_local_path_project_and_fetch_mtc_surfaces() -> None:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Demo local migration",
            "clientName": "Founder Studio",
            "sourceKind": "local_directory",
            "sourceTarget": "demo-systems/legacycart",
            "expectedUsers": 25,
            "preferredCloud": "aws",
            "businessConstraints": ["Launch quickly", "Keep ops simple"],
            "complianceNotes": ["PII handling"],
            "credentialLabel": "Local folder",
            "credentialKind": "none",
        },
    )

    assert response.status_code == 201
    project = response.json()
    project_id = project["id"]
    assert project["expectedUsers"] == 25
    assert project["sourceKind"] == "local_path"

    intake = client.get(f"/api/v1/projects/{project_id}/intake")
    assert intake.status_code == 200
    assert intake.json()["sourceTarget"] == "demo-systems/legacycart"

    traces = client.get(f"/api/v1/projects/{project_id}/observability-traces")
    assert traces.status_code == 200
    trace_payload = traces.json()
    assert trace_payload
    assert any(item["stageKey"] == "hosting_fit_recommendation" for item in trace_payload)
    assert any(item["evaluationSummary"] for item in trace_payload)

    deployment = client.get(f"/api/v1/projects/{project_id}/deployment-plan")
    assert deployment.status_code == 200
    deployment_payload = deployment.json()
    assert deployment_payload["executionState"] == "blocked"
    assert deployment_payload["recommendedPlatform"]["platformKey"] == "aws-ec2"
    assert any(option["platformKey"] == "vercel" for option in deployment_payload["platformOptions"])


def test_aws_execution_requires_credentials_then_succeeds_after_connection() -> None:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "AWS deployable project",
            "clientName": "Northstar Labs",
            "sourceKind": "local_directory",
            "sourceTarget": "demo-systems/legacycart",
            "expectedUsers": 400,
            "preferredCloud": "aws",
            "credentialLabel": "Local folder",
            "credentialKind": "none",
        },
    )
    project_id = response.json()["id"]

    blocked = client.post(
        f"/api/v1/projects/{project_id}/deployment-executions",
        json={"provider": "aws", "mode": "dry_run", "triggeredBy": "Ava"},
    )
    assert blocked.status_code == 409
    assert "credentials" in blocked.json()["detail"].lower()

    cloud_connection = client.post(
        f"/api/v1/projects/{project_id}/cloud-connections",
        json={
            "provider": "aws",
            "name": "AWS prod",
            "accountLabel": "Acct 1",
            "regionScope": ["us-east-1"],
            "mode": "dry_run",
            "credentialLabel": "Cockpit role",
            "credentialKind": "assumed_role",
            "notes": ["Ready for demo deployment"],
        },
    )
    assert cloud_connection.status_code == 201

    execution = client.post(
        f"/api/v1/projects/{project_id}/deployment-executions",
        json={"provider": "aws", "mode": "dry_run", "triggeredBy": "Ava"},
    )
    assert execution.status_code == 201
    payload = execution.json()
    assert payload["status"] == "succeeded"
    assert payload["provider"] == "aws"
    assert payload["mode"] == "dry_run"
