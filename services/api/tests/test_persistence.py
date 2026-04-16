from __future__ import annotations

from pathlib import Path

from services.api.app.core.db import get_engine
from services.api.app.core.settings import get_settings
from services.api.app.domain.models import SourceConnectionCreate
from services.api.app.domain.repository import SeedRepository


def test_seed_repository_bootstraps_into_a_real_database_file(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cockpit.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    get_engine.cache_clear()

    repository = SeedRepository()

    projects = repository.list_projects()
    assert [project.id for project in projects] == ["legacycart"]
    assert db_path.exists()


def test_seed_repository_persists_state_across_fresh_instances(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "cockpit.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    get_engine.cache_clear()

    first = SeedRepository()
    first.add_source_connection(
        "legacycart",
        SourceConnectionCreate(
            kind="github",
            name="Northstar GitHub",
            target="github.com/northstar-retail/platform",
            branch="main",
            mode="discovery",
            credential_label="GitHub app installation",
            credential_kind="oauth",
            notes=["Repo metadata ingestion approved for discovery."],
        ),
    )

    second = SeedRepository()
    source_connections = second.get_project("legacycart").source_connections

    assert any(item.name == "Northstar GitHub" for item in source_connections)
    assert Path(db_path).exists()
