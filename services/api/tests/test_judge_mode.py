from pathlib import Path

import pytest

from services.api.app.core.db import get_engine
from services.api.app.core.settings import get_settings
from services.api.app.domain.models import AnalysisQuestionAnswer, ApprovalDecision, PreviewLaunchRequest, ProjectCreate
from services.api.app.domain.repository import SeedRepository
from services.api.app.services.local_preview import LocalPreviewManager
from services.api.app.services.orchestration import AssessmentOrchestrator


@pytest.fixture(autouse=True)
def reset_settings_caches():
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()


def test_judge_mode_starts_with_empty_workspace(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "judge.db"
    monkeypatch.setenv("APP_MODE", "judge")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    get_engine.cache_clear()

    repository = SeedRepository()

    assert repository.list_projects() == []

    context = repository.get_workspace_context("workspace-judge")
    assert context.workspace.id == "workspace-judge"
    assert context.workspace.mode == "judge"
    assert context.projects == []
    assert context.client_accounts == []
    assert context.runtime.app_mode == "judge"


def test_judge_mode_workspace_project_creation_scans_real_local_path(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "judge-scan.db"
    repo_root = tmp_path / "sample-app"
    repo_root.mkdir()
    (repo_root / "package.json").write_text('{"name":"sample-app","private":true}', encoding="utf-8")
    (repo_root / "app.log").write_text(
        "Authorization=Bearer secret-token\nCookie=session=abc123",
        encoding="utf-8",
    )

    monkeypatch.setenv("APP_MODE", "judge")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    get_engine.cache_clear()

    repository = SeedRepository()

    created = repository.create_workspace_project(
        "workspace-judge",
        ProjectCreate(
            name="Judge Ready App",
            client_name="Hackathon Judge",
            source_kind="local_path",
            source_target=str(repo_root),
            expected_users=75,
            preferred_cloud="aws",
            credential_label="Local path",
            credential_kind="none",
        ),
    )

    project = repository.get_project(created.id)
    assert project.intake_profile is not None
    assert project.intake_profile.source_kind == "local_path"
    assert project.intake_profile.source_target == str(repo_root)
    assert project.findings
    assert any(reference.source_uri == "app.log" for reference in project.evidence)


def test_judge_mode_answers_questions_and_launches_local_preview(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "judge-preview.db"
    repo_root = tmp_path / "preview-app"
    repo_root.mkdir()
    (repo_root / "package.json").write_text(
        '{"name":"preview-app","private":true,"scripts":{"start":"node server.js"}}',
        encoding="utf-8",
    )
    (repo_root / "server.js").write_text(
        "const http = require('http');\n"
        "const port = Number(process.env.PORT || 4310);\n"
        "http.createServer((_req, res) => res.end('preview ok')).listen(port, '127.0.0.1');\n",
        encoding="utf-8",
    )
    (repo_root / "app.log").write_text(
        "Authorization=Bearer secret-token\nCookie=session=abc123",
        encoding="utf-8",
    )

    monkeypatch.setenv("APP_MODE", "judge")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    get_engine.cache_clear()

    repository = SeedRepository()
    preview_manager = LocalPreviewManager()
    orchestrator = AssessmentOrchestrator(repository, local_preview_manager=preview_manager)

    created = repository.create_workspace_project(
        "workspace-judge",
        ProjectCreate(
            name="Preview Ready App",
            client_name="Hackathon Judge",
            source_kind="local_path",
            source_target=str(repo_root),
            expected_users=45,
            preferred_cloud="aws",
            credential_label="Local path",
            credential_kind="none",
        ),
    )

    project = repository.get_project(created.id)
    question = project.analysis_questions[0]
    answered = orchestrator.answer_analysis_question(
        created.id,
        question.id,
        AnalysisQuestionAnswer(actor="Judge Operator", answer="Use AWS Secrets Manager with 30-day log retention."),
    )
    assert answered.state == "answered"
    assert repository.get_project(created.id).analysis_questions[0].answer

    planning_approval = next(item for item in project.approvals if "planning" in item.phase.lower())
    decision = orchestrator.decide_approval(
        created.id,
        planning_approval.id,
        ApprovalDecision(decision="approved", actor="Judge Operator", comment="Planning is approved."),
    )
    assert decision.state == "approved"

    try:
        preview = orchestrator.launch_local_preview(
            created.id,
            PreviewLaunchRequest(triggered_by="Judge Operator"),
        )
        assert preview.supported is True
        assert preview.url is not None
        assert preview.status in {"running", "failed"}
    finally:
        preview_manager._terminate(created.id)
