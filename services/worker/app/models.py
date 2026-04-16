from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Severity = Literal["critical", "high", "medium", "low"]
EvidenceSourceType = Literal["file", "log", "manifest", "command_output"]
ComponentKind = Literal["service", "job", "database", "storage", "frontend", "pipeline", "integration"]
EdgeRelation = Literal["depends_on", "calls", "writes_to", "reads_from", "deployed_via", "schedules"]
ScenarioKind = Literal["security_first", "lift_shift_guardrails", "strangler_modernization"]
SourceKind = Literal["local_directory", "git_repository", "archive"]
PipelineStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]
ConnectorKind = Literal["github", "azure_repos"]


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def camelize(value):
    if isinstance(value, list):
        return [camelize(item) for item in value]
    if isinstance(value, dict):
        return {to_camel(key): camelize(item) for key, item in value.items()}
    return value


@dataclass(slots=True)
class SourceMetadata:
    kind: SourceKind
    connection_id: str
    name: str
    root_path: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PipelinePhase:
    pipeline_key: str
    name: str
    status: PipelineStatus

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ConnectorHandoff:
    kind: ConnectorKind
    name: str
    required_credentials: bool
    template: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class Evidence:
    id: str
    source_type: EvidenceSourceType
    source_uri: str
    evidence_type: str
    excerpt: str
    confidence: float
    locator: dict[str, int | str] | None = None
    content_hash: str | None = None
    normalized_value: str | None = None
    redaction_applied: bool = False
    redaction_reason: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class Component:
    id: str
    kind: ComponentKind
    name: str
    path: str
    runtime: str | None = None
    description: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class DependencyEdge:
    id: str
    source: str
    target: str
    relation: EdgeRelation
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class Finding:
    id: str
    title: str
    category: str
    severity: Severity
    confidence: float
    summary: str
    recommendation: str
    evidence_ids: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class Recommendation:
    id: str
    title: str
    summary: str
    confidence: float
    rationale: str
    effort: Literal["small", "medium", "large"]
    impact: Literal["high", "medium", "low"]
    finding_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ScenarioOutcome:
    readiness: int
    risk_delta: str
    cost_delta: str
    summary: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class Scenario:
    id: str
    name: str
    description: str
    assumption_set: list[str]
    outcome: ScenarioOutcome
    kind: ScenarioKind

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["outcome"] = self.outcome.to_dict()
        return payload


@dataclass(slots=True)
class ScanSummary:
    readiness_score: int
    recommendation: str
    confidence: float
    blocker_count: int
    critical_finding_count: int
    provider_ranking: list[dict[str, str | int]]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class UpstreamScanRecord:
    project_id: str
    scan_id: str
    scan_version: str
    source: SourceMetadata
    pipelines: list[PipelinePhase]
    connector_handoffs: list[ConnectorHandoff]
    evidence: list[Evidence]
    components: list[Component]
    dependencies: list[DependencyEdge]
    findings: list[Finding]
    recommendations: list[Recommendation]
    scenarios: list[Scenario]
    summary: ScanSummary

    def to_dict(self) -> dict:
        return camelize(asdict(self))


@dataclass(slots=True)
class ScanResult:
    scan_id: str
    target_name: str
    root_path: str
    project_id: str | None
    source: SourceMetadata
    pipelines: list[PipelinePhase]
    connector_handoffs: list[ConnectorHandoff]
    evidence: list[Evidence]
    components: list[Component]
    dependencies: list[DependencyEdge]
    findings: list[Finding]
    recommendations: list[Recommendation]
    scenarios: list[Scenario]
    summary: ScanSummary

    def to_upstream_record(self, project_id: str | None = None) -> dict:
        upstream_project_id = project_id or self.project_id or self.target_name.lower()
        return UpstreamScanRecord(
            project_id=upstream_project_id,
            scan_id=self.scan_id,
            scan_version="mvp-2",
            source=self.source,
            pipelines=self.pipelines,
            connector_handoffs=self.connector_handoffs,
            evidence=self.evidence,
            components=self.components,
            dependencies=self.dependencies,
            findings=self.findings,
            recommendations=self.recommendations,
            scenarios=self.scenarios,
            summary=self.summary,
        ).to_dict()

    def to_dict(self) -> dict:
        return {
            "scan_id": self.scan_id,
            "project_id": self.project_id,
            "target": {
                "name": self.target_name,
                "root_path": self.root_path,
                "scan_version": "mvp-1",
            },
            "source": self.source.to_dict(),
            "pipelines": [item.to_dict() for item in self.pipelines],
            "connector_handoffs": [item.to_dict() for item in self.connector_handoffs],
            "evidence": [item.to_dict() for item in self.evidence],
            "components": [item.to_dict() for item in self.components],
            "dependencies": [item.to_dict() for item in self.dependencies],
            "findings": [item.to_dict() for item in self.findings],
            "recommendations": [item.to_dict() for item in self.recommendations],
            "scenarios": [item.to_dict() for item in self.scenarios],
            "summary": self.summary.to_dict(),
            "upstream_record": self.to_upstream_record(),
        }
