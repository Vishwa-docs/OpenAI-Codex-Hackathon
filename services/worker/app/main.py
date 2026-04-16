from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

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


class ConnectorCatalogEntry(WorkerModel):
    kind: Literal["github", "azure_repos"]
    name: str
    required_credentials: bool
    handoff_template: str
    summary: str


app = FastAPI(
    title="Cloud Migration Cockpit Worker",
    version="0.1.0",
    description="Local read-only worker for source scanning, evidence normalization, and connector handoff discovery.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/connectors/catalog", response_model=list[ConnectorCatalogEntry])
def connector_catalog() -> list[ConnectorCatalogEntry]:
    return [
        ConnectorCatalogEntry(
            kind="github",
            name="GitHub source ingestion",
            required_credentials=True,
            handoff_template="github://owner/repo?ref=main",
            summary="Creates a repo metadata handoff while the worker stays read-only against the local checkout.",
        ),
        ConnectorCatalogEntry(
            kind="azure_repos",
            name="Azure Repos source ingestion",
            required_credentials=True,
            handoff_template="azure://org/project/repo?ref=main",
            summary="Provides an approval-gated handoff template for Azure DevOps source discovery.",
        ),
    ]


@app.post("/scan")
def scan(request: ScanRequest) -> dict:
    root = Path(request.root_path)
    if not root.exists():
        raise HTTPException(status_code=404, detail=f"Scan root does not exist: {request.root_path}")
    result = scan_legacycart(root)
    return camelize(result_to_json(result, as_dict=True))
