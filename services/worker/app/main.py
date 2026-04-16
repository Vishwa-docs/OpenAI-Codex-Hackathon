from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from .connectors import (
    ConnectorCatalogEntry,
    ConnectorRequest,
    build_connector_catalog,
    build_worker_health,
    sync_connector_request,
    validate_connector_request,
)
from .scanner import result_to_json, scan_legacycart


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def camelize(value):
    if isinstance(value, list):
        return [camelize(item) for item in value]
    if isinstance(value, dict):
        return {to_camel(key): camelize(item) for key, item in value.items()}
    return value


class WorkerModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ScanRequest(WorkerModel):
    root_path: str


app = FastAPI(
    title="Cloud Migration Cockpit Worker",
    version="0.1.0",
    description="Local read-only worker for source scanning, evidence normalization, and connector handoff discovery.",
)


@app.get("/health")
def health() -> dict[str, object]:
    return camelize(build_worker_health())


@app.get("/connectors/catalog", response_model=list[ConnectorCatalogEntry])
def connector_catalog() -> list[ConnectorCatalogEntry]:
    return build_connector_catalog()


@app.post("/connectors/validate")
def validate_connector(request: ConnectorRequest) -> dict:
    return validate_connector_request(request).model_dump(by_alias=True)


@app.post("/connectors/sync")
def sync_connector(request: ConnectorRequest) -> dict:
    return sync_connector_request(request).model_dump(by_alias=True)


def _require_connector_kind(request: ConnectorRequest, kind: Literal["local_directory", "github", "azure_repos"]) -> None:
    if request.kind != kind:
        raise HTTPException(status_code=400, detail=f"Expected connector kind {kind}, got {request.kind}")


@app.post("/connectors/local_directory/validate")
def validate_local_directory_connector(request: ConnectorRequest) -> dict:
    _require_connector_kind(request, "local_directory")
    return validate_connector_request(request).model_dump(by_alias=True)


@app.post("/connectors/github/validate")
def validate_github_connector(request: ConnectorRequest) -> dict:
    _require_connector_kind(request, "github")
    return validate_connector_request(request).model_dump(by_alias=True)


@app.post("/connectors/azure_repos/validate")
def validate_azure_repos_connector(request: ConnectorRequest) -> dict:
    _require_connector_kind(request, "azure_repos")
    return validate_connector_request(request).model_dump(by_alias=True)


@app.post("/connectors/local_directory/sync")
def sync_local_directory_connector(request: ConnectorRequest) -> dict:
    _require_connector_kind(request, "local_directory")
    return sync_connector_request(request).model_dump(by_alias=True)


@app.post("/connectors/github/sync")
def sync_github_connector(request: ConnectorRequest) -> dict:
    _require_connector_kind(request, "github")
    return sync_connector_request(request).model_dump(by_alias=True)


@app.post("/connectors/azure_repos/sync")
def sync_azure_repos_connector(request: ConnectorRequest) -> dict:
    _require_connector_kind(request, "azure_repos")
    return sync_connector_request(request).model_dump(by_alias=True)


@app.post("/scan")
def scan(request: ScanRequest) -> dict:
    root = Path(request.root_path)
    if not root.exists():
        raise HTTPException(status_code=404, detail=f"Scan root does not exist: {request.root_path}")
    result = scan_legacycart(root)
    return camelize(result_to_json(result, as_dict=True))
