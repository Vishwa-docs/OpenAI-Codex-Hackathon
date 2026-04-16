from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from .scanner import scan_legacycart


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def camelize(value: Any) -> Any:
    if isinstance(value, list):
        return [camelize(item) for item in value]
    if isinstance(value, dict):
        return {to_camel(key): camelize(item) for key, item in value.items()}
    return value


class WorkerModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class WorkerSettings(WorkerModel):
    service_name: str = "cloud-migration-cockpit-worker"
    version: str = "0.1.0"
    mode: Literal["local", "hybrid"] = "hybrid"
    project_api_key_header: str = "X-Project-Api-Key"
    project_api_key_mode: Literal["project_scoped"] = "project_scoped"
    supported_connectors: list[str] = Field(
        default_factory=lambda: ["local_directory", "github", "azure_repos"]
    )
    connector_modes: dict[str, str] = Field(
        default_factory=lambda: {
            "local_directory": "ready",
            "github": "prepared_read_only",
            "azure_repos": "prepared_read_only",
        }
    )


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()


class ConnectorCatalogEntry(WorkerModel):
    kind: Literal["local_directory", "github", "azure_repos"]
    name: str
    required_credentials: bool
    handoff_template: str
    summary: str
    validation_endpoint: str
    sync_endpoint: str
    project_scoped_api_key_required: bool


class ConnectorRequest(WorkerModel):
    kind: Literal["local_directory", "github", "azure_repos"]
    project_id: str
    root_path: str | None = None
    repository_url: str | None = None
    organization_url: str | None = None
    project_name: str | None = None
    repository_name: str | None = None
    branch: str | None = None
    commit_ref: str | None = None
    project_api_key: str | None = None


class ValidationCheck(WorkerModel):
    name: str
    status: Literal["pass", "warn", "fail"]
    message: str


class ProjectApiKeyState(WorkerModel):
    header_name: str
    present: bool
    scope: str
    redacted_value: str | None = None


class ConnectorValidationResponse(WorkerModel):
    kind: Literal["local_directory", "github", "azure_repos"]
    project_id: str
    status: Literal["ready", "needs_credentials", "missing_root", "missing_target"]
    api_key: ProjectApiKeyState
    validation_checks: list[ValidationCheck]
    notes: list[str] = Field(default_factory=list)


class ConnectorSyncResponse(WorkerModel):
    kind: Literal["local_directory", "github", "azure_repos"]
    project_id: str
    status: Literal["completed", "prepared", "blocked"]
    api_key: ProjectApiKeyState
    validation_checks: list[ValidationCheck]
    notes: list[str] = Field(default_factory=list)
    scan: dict[str, Any] | None = None
    upstream_record: dict[str, Any] | None = None


CONNECTOR_KINDS: tuple[Literal["local_directory", "github", "azure_repos"], ...] = (
    "local_directory",
    "github",
    "azure_repos",
)


class ConnectorAnalyzer(Protocol):
    def catalog_entry(self) -> ConnectorCatalogEntry: ...

    def validate(self, request: ConnectorRequest, api_key: ProjectApiKeyState) -> ConnectorValidationResponse: ...

    def sync(self, request: ConnectorRequest, validation: ConnectorValidationResponse) -> ConnectorSyncResponse: ...


@dataclass(slots=True)
class PreparedRemoteConnectorConfig:
    kind: Literal["github", "azure_repos"]
    name: str
    handoff_template: str
    summary: str
    required_fields: tuple[str, ...]
    missing_message: str
    source_name_field: str
    validation_endpoint: str
    sync_endpoint: str


class LegacyCartConnectorAnalyzer:
    kind: Literal["local_directory"] = "local_directory"

    def catalog_entry(self) -> ConnectorCatalogEntry:
        return ConnectorCatalogEntry(
            kind="local_directory",
            name="Local directory ingestion",
            required_credentials=False,
            handoff_template="file:///path/to/project",
            summary="Scans a checked-out project root and normalizes the legacy dataset in place.",
            validation_endpoint="/connectors/local_directory/validate",
            sync_endpoint="/connectors/local_directory/sync",
            project_scoped_api_key_required=False,
        )

    def validate(self, request: ConnectorRequest, api_key: ProjectApiKeyState) -> ConnectorValidationResponse:
        root_path = Path(request.root_path or "")
        if not request.root_path:
            return ConnectorValidationResponse(
                kind=request.kind,
                project_id=request.project_id,
                status="missing_root",
                api_key=api_key,
                validation_checks=[
                    ValidationCheck(
                        name="root_path",
                        status="fail",
                        message="A root path is required for local directory validation.",
                    ),
                ],
                notes=["Local validation runs against a checked-out project root."],
            )
        if not root_path.exists():
            return ConnectorValidationResponse(
                kind=request.kind,
                project_id=request.project_id,
                status="missing_root",
                api_key=api_key,
                validation_checks=[
                    ValidationCheck(
                        name="root_path_exists",
                        status="fail",
                        message=f"Scan root does not exist: {request.root_path}",
                    )
                ],
                notes=["The worker can only validate local scans when the path exists."],
            )
        return ConnectorValidationResponse(
            kind=request.kind,
            project_id=request.project_id,
            status="ready",
            api_key=api_key,
            validation_checks=[
                ValidationCheck(
                    name="root_path_exists",
                    status="pass",
                    message=f"Scan root exists: {request.root_path}",
                ),
                ValidationCheck(
                    name="api_key_scope",
                    status="pass",
                    message="Local scans do not require a project-scoped API key.",
                ),
            ],
            notes=["Local validation keeps the worker read-only and deterministic."],
        )

    def sync(self, request: ConnectorRequest, validation: ConnectorValidationResponse) -> ConnectorSyncResponse:
        if validation.status != "ready":
            return _blocked_sync_response(request, validation)
        result = scan_legacycart(Path(request.root_path or request.project_id))
        upstream_record = result.to_upstream_record(project_id=request.project_id)
        return ConnectorSyncResponse(
            kind=request.kind,
            project_id=request.project_id,
            status="completed",
            api_key=validation.api_key,
            validation_checks=validation.validation_checks,
            notes=[
                *validation.notes,
                "Local scans are fully executed and can be persisted upstream immediately.",
            ],
            scan=camelize(result.to_dict()),
            upstream_record=camelize(upstream_record),
        )


@dataclass(slots=True)
class PreparedRemoteConnectorAnalyzer:
    config: PreparedRemoteConnectorConfig

    @property
    def kind(self) -> Literal["github", "azure_repos"]:
        return self.config.kind

    def catalog_entry(self) -> ConnectorCatalogEntry:
        return ConnectorCatalogEntry(
            kind=self.config.kind,
            name=self.config.name,
            required_credentials=True,
            handoff_template=self.config.handoff_template,
            summary=self.config.summary,
            validation_endpoint=self.config.validation_endpoint,
            sync_endpoint=self.config.sync_endpoint,
            project_scoped_api_key_required=True,
        )

    def validate(self, request: ConnectorRequest, api_key: ProjectApiKeyState) -> ConnectorValidationResponse:
        if not all(getattr(request, field) for field in self.config.required_fields):
            return ConnectorValidationResponse(
                kind=request.kind,
                project_id=request.project_id,
                status="missing_target",
                api_key=api_key,
                validation_checks=[
                    ValidationCheck(
                        name="connector_target",
                        status="fail",
                        message=self.config.missing_message,
                    ),
                ],
                notes=[self.config.missing_message],
            )
        if not api_key.present:
            return ConnectorValidationResponse(
                kind=request.kind,
                project_id=request.project_id,
                status="needs_credentials",
                api_key=api_key,
                validation_checks=[
                    ValidationCheck(
                        name="project_scoped_api_key",
                        status="fail",
                        message="A project-scoped API key is required for remote connector validation.",
                    )
                ],
                notes=["Project-scoped API keys are not stored by the worker; they are only acknowledged in memory."],
            )
        return ConnectorValidationResponse(
            kind=request.kind,
            project_id=request.project_id,
            status="ready",
            api_key=api_key,
            validation_checks=[
                ValidationCheck(
                    name="connector_target",
                    status="pass",
                    message="Remote connector metadata is complete.",
                ),
                ValidationCheck(
                    name="project_scoped_api_key",
                    status="pass",
                    message="Project-scoped API key was provided and accepted for this request.",
                ),
            ],
            notes=["Remote connectors stay read-only until a real provider sync is wired in."],
        )

    def sync(self, request: ConnectorRequest, validation: ConnectorValidationResponse) -> ConnectorSyncResponse:
        if validation.status != "ready":
            return _blocked_sync_response(request, validation)
        prepared = _build_prepared_remote_sync_record(request, validation, self.config)
        upstream_record = _build_prepared_remote_upstream_record(request, validation, self.config)
        return ConnectorSyncResponse(
            kind=request.kind,
            project_id=request.project_id,
            status="prepared",
            api_key=validation.api_key,
            validation_checks=validation.validation_checks,
            notes=[
                *validation.notes,
                "Remote connector sync returns a prepared read-only record and does not contact external providers yet.",
            ],
            scan=camelize(prepared),
            upstream_record=camelize(upstream_record),
        )


@lru_cache
def _connector_analyzers() -> dict[str, ConnectorAnalyzer]:
    analyzers: dict[str, ConnectorAnalyzer] = {
        "local_directory": LegacyCartConnectorAnalyzer(),
    }
    analyzers["github"] = PreparedRemoteConnectorAnalyzer(
        PreparedRemoteConnectorConfig(
            kind="github",
            name="GitHub source ingestion",
            handoff_template="github://owner/repo?ref=main",
            summary="Validates GitHub project-scoped access before staging a read-only sync record.",
            required_fields=("repository_url",),
            missing_message="GitHub repository URL is required for validation.",
            source_name_field="repository_name",
            validation_endpoint="/connectors/github/validate",
            sync_endpoint="/connectors/github/sync",
        )
    )
    analyzers["azure_repos"] = PreparedRemoteConnectorAnalyzer(
        PreparedRemoteConnectorConfig(
            kind="azure_repos",
            name="Azure Repos source ingestion",
            handoff_template="azure://org/project/repo?ref=main",
            summary="Validates Azure Repos metadata before staging a read-only sync record.",
            required_fields=("organization_url", "project_name", "repository_name"),
            missing_message="Azure Repos organization, project, and repository names are required.",
            source_name_field="repository_name",
            validation_endpoint="/connectors/azure_repos/validate",
            sync_endpoint="/connectors/azure_repos/sync",
        )
    )
    return analyzers


def _get_connector_analyzer(kind: str) -> ConnectorAnalyzer:
    try:
        return _connector_analyzers()[kind]
    except KeyError as exc:  # pragma: no cover - guarded by request schema
        raise ValueError(f"Unsupported connector kind: {kind}") from exc


def build_worker_health() -> dict[str, Any]:
    settings = get_worker_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
        "mode": settings.mode,
        "project_api_key_header": settings.project_api_key_header,
        "project_api_key_mode": settings.project_api_key_mode,
        "supported_connectors": settings.supported_connectors,
        "connector_modes": settings.connector_modes,
    }


def build_connector_catalog() -> list[ConnectorCatalogEntry]:
    return [_get_connector_analyzer(kind).catalog_entry() for kind in CONNECTOR_KINDS]


def validate_connector_request(request: ConnectorRequest) -> ConnectorValidationResponse:
    api_key = _api_key_state(request)
    return _get_connector_analyzer(request.kind).validate(request, api_key)


def sync_connector_request(request: ConnectorRequest) -> ConnectorSyncResponse:
    validation = validate_connector_request(request)
    return _get_connector_analyzer(request.kind).sync(request, validation)


def _api_key_state(request: ConnectorRequest) -> ProjectApiKeyState:
    settings = get_worker_settings()
    api_key = request.project_api_key
    provided = bool(api_key)
    redacted_value = None
    if api_key:
        suffix = api_key[-4:] if len(api_key) >= 4 else api_key
        redacted_value = f"****{suffix}"
    return ProjectApiKeyState(
        header_name=settings.project_api_key_header,
        present=provided,
        scope=request.project_id,
        redacted_value=redacted_value,
    )


def _blocked_sync_response(request: ConnectorRequest, validation: ConnectorValidationResponse) -> ConnectorSyncResponse:
    return ConnectorSyncResponse(
        kind=request.kind,
        project_id=request.project_id,
        status="blocked",
        api_key=validation.api_key,
        validation_checks=validation.validation_checks,
        notes=validation.notes,
    )


def _build_prepared_remote_sync_record(
    request: ConnectorRequest,
    validation: ConnectorValidationResponse,
    config: PreparedRemoteConnectorConfig,
) -> dict[str, Any]:
    source_name = _remote_source_name(request, config)
    source_uri = _remote_source_uri(request)
    return {
        "scan_id": f"prepared-{request.kind}-{request.project_id}",
        "project_id": request.project_id,
        "connector_kind": request.kind,
        "status": "prepared_read_only",
        "read_only": True,
        "source": {
            "kind": "git_repository",
            "connection_id": f"{request.kind}-{request.project_id}",
            "name": source_name,
            "root_path": source_uri,
        },
        "validation": {
            "status": validation.status,
            "checks": [item.model_dump(by_alias=True) for item in validation.validation_checks],
        },
        "connector_handoffs": [
            {
                "kind": request.kind,
                "name": config.name,
                "required_credentials": True,
                "template": config.handoff_template,
                "description": config.summary,
            }
        ],
        "summary": {
            "readiness_score": 0,
            "recommendation": "defer until upstream sync executes",
            "confidence": 0.0,
            "blocker_count": 0,
            "critical_finding_count": 0,
            "provider_ranking": [],
        },
        "notes": [
            "This is a read-only prepared sync record.",
            "The worker has not contacted the remote provider yet.",
        ],
    }


def _build_prepared_remote_upstream_record(
    request: ConnectorRequest,
    validation: ConnectorValidationResponse,
    config: PreparedRemoteConnectorConfig,
) -> dict[str, Any]:
    source_name = _remote_source_name(request, config)
    source_uri = _remote_source_uri(request)
    return {
        "project_id": request.project_id,
        "scan_id": f"prepared-{request.kind}-{request.project_id}",
        "scan_version": "connector-sync-v2",
        "source": {
            "kind": "git_repository",
            "connection_id": f"{request.kind}-{request.project_id}",
            "name": source_name,
            "root_path": source_uri,
        },
        "pipelines": [],
        "connector_handoffs": [
            {
                "kind": request.kind,
                "name": config.name,
                "required_credentials": True,
                "template": config.handoff_template,
                "description": config.summary,
            }
        ],
        "evidence": [],
        "components": [],
        "dependencies": [],
        "findings": [],
        "recommendations": [],
        "scenarios": [],
        "summary": {
            "readiness_score": 0,
            "recommendation": "defer until upstream sync executes",
            "confidence": 0.0,
            "blocker_count": 0,
            "critical_finding_count": 0,
            "provider_ranking": [],
        },
        "validation": {
            "status": validation.status,
            "checks": [item.model_dump(by_alias=True) for item in validation.validation_checks],
        },
    }


def _remote_source_name(request: ConnectorRequest, config: PreparedRemoteConnectorConfig) -> str:
    candidate = getattr(request, config.source_name_field, None)
    if candidate:
        return candidate
    if request.project_name:
        return request.project_name
    if request.repository_name:
        return request.repository_name
    return request.project_id


def _remote_source_uri(request: ConnectorRequest) -> str:
    return request.repository_url or request.organization_url or request.root_path or request.project_id
