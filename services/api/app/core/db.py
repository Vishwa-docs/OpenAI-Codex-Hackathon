from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .settings import get_settings


class Base(DeclarativeBase):
    pass


class ProjectSnapshotRecord(Base):
    __tablename__ = "project_snapshots"

    project_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class OrganizationRecord(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)


class WorkspaceRecord(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)


class ClientAccountRecord(Base):
    __tablename__ = "client_accounts"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_region: Mapped[str] = mapped_column(String(255), nullable=False)
    compliance_tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class ProjectCatalogRecord(Base):
    __tablename__ = "migration_projects"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=False)
    client_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    source_system: Mapped[str] = mapped_column(Text, nullable=False)
    target_system: Mapped[str] = mapped_column(Text, nullable=False)
    business_summary: Mapped[str] = mapped_column(Text, nullable=False)
    readiness_score: Mapped[int] = mapped_column(nullable=False, default=0)
    migration_decision: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    phase: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    recommended_provider: Mapped[str] = mapped_column(String(255), nullable=False)


def _ensure_sqlite_parent(database_url: str) -> None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return
    db_path = Path(database_url.removeprefix(prefix))
    if db_path.parent and str(db_path.parent) not in {"", "."}:
        db_path.parent.mkdir(parents=True, exist_ok=True)


def build_engine():
    database_url = get_settings().database_url
    _ensure_sqlite_parent(database_url)
    return create_engine(database_url, future=True)


@lru_cache
def get_engine(database_url: str):
    _ensure_sqlite_parent(database_url)
    return create_engine(database_url, future=True)


def get_session_local():
    return sessionmaker(
        bind=get_engine(get_settings().database_url),
        autoflush=False,
        autocommit=False,
        future=True,
    )


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine(get_settings().database_url))


@contextmanager
def session_scope() -> Iterator[Session]:
    init_db()
    session = get_session_local()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
