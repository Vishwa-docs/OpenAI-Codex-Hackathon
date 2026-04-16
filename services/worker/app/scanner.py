from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .models import (
    Component,
    ConnectorHandoff,
    DependencyEdge,
    Evidence,
    Finding,
    PipelinePhase,
    Recommendation,
    ScanResult,
    ScanSummary,
    Scenario,
    ScenarioOutcome,
    SourceMetadata,
)


@dataclass(slots=True)
class _State:
    evidence: list[Evidence]
    components: dict[str, Component]
    dependencies: list[DependencyEdge]
    findings: list[Finding]
    recommendations: list[Recommendation]


class LegacyCartScanner:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.state = _State(evidence=[], components={}, dependencies=[], findings=[], recommendations=[])
        self._evidence_counter = 1

    def scan(self) -> ScanResult:
        self._discover_components()
        self._scan_all_files()
        self._finalize_components()
        self._derive_findings_and_recommendations()
        source = self._build_source_metadata()
        pipelines = self._build_pipeline_phases()
        connector_handoffs = self._build_connector_handoffs()
        scenarios = self._build_scenarios()
        summary = self._build_summary()
        return ScanResult(
            scan_id=self._scan_id(),
            target_name="LegacyCart",
            root_path=str(self.root),
            project_id=self.root.name.lower(),
            source=source,
            pipelines=pipelines,
            connector_handoffs=connector_handoffs,
            evidence=self.state.evidence,
            components=sorted(self.state.components.values(), key=lambda item: item.id),
            dependencies=sorted(self.state.dependencies, key=lambda item: item.id),
            findings=sorted(self.state.findings, key=lambda item: item.id),
            recommendations=sorted(self.state.recommendations, key=lambda item: item.id),
            scenarios=scenarios,
            summary=summary,
        )

    def _scan_id(self) -> str:
        payload = str(self.root.resolve()).encode("utf-8")
        return f"scan_{sha256(payload).hexdigest()[:12]}"

    def _discover_components(self) -> None:
        self._add_component("frontend", "frontend", "legacycart-admin", "frontend/admin", "AngularJS admin UI")
        self._add_component("backend", "service", "legacycart-backend", "backend", "Monolith backend API")
        self._add_component("jobs", "job", "legacycart-jobs", "jobs", "Batch jobs and scripts")
        self._add_component("database", "database", "legacycart-postgres", "db", "PostgreSQL data store")
        self._add_component("storage", "storage", "legacycart-nfs", "jobs/invoice-export.py", "Shared file storage")
        self._add_component("pipeline", "pipeline", "legacycart-jenkins", "infra/jenkins", "Jenkins delivery pipeline")
        self._add_component("integration", "integration", "payment-gateway", "integrations/payment-gateway", "SOAP payment integration")
        self._add_component("integration", "integration", "erp-sync", "integrations/erp", "SFTP ERP synchronization")

    def _add_component(self, component_id: str, kind: str, name: str, path: str, description: str) -> None:
        self.state.components[component_id] = Component(
            id=component_id,
            kind=kind,  # type: ignore[arg-type]
            name=name,
            path=path,
            description=description,
        )

    def _finalize_components(self) -> None:
        backend = self.state.components["backend"]
        backend.runtime = "Java 8 / Spring Boot 2.x"
        frontend = self.state.components["frontend"]
        frontend.runtime = "AngularJS 1.x"
        jobs = self.state.components["jobs"]
        jobs.runtime = "Python 3.8 / Bash"
        db = self.state.components["database"]
        db.runtime = "PostgreSQL 9.6"
        storage = self.state.components["storage"]
        storage.runtime = "NFS"
        pipeline = self.state.components["pipeline"]
        pipeline.runtime = "Jenkins"
        integration = self.state.components["integration"]
        integration.runtime = "SOAP / SFTP"

    def _scan_all_files(self) -> None:
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            if path.suffix.lower() in {".log", ".yml", ".yaml", ".json", ".sh", ".py", ".sql", ".html", ".js", ".conf", ".wsdl", ".md"}:
                self._scan_file(path)

    def _scan_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(self.root).as_posix()
        lines = text.splitlines()
        if any(token in rel for token in ("application-prod", "jenkins", "docker-compose", "invoice-export", "nightly_reconcile")):
            self._add_file_evidence(rel, "manifest", text)

        patterns = [
            (r"(postgres(?:ql)?://[^ \n]+)", "secret", "Hardcoded database connection string"),
            (r"(AKIA[0-9A-Z]{16}|aws_access_key_id|aws_secret_access_key|deployKey)", "secret", "Long-lived credential material"),
            (r"(password|passwd|secret|token)\s*[:=]\s*['\"]?([^'\"]+)", "secret", "Possible embedded secret"),
            (r"(Authorization|Cookie|X-Auth-Token)", "log_leak", "Sensitive header logging"),
            (r"(NFS|/mnt/shared|shared volume)", "storage_risk", "Shared storage dependency"),
            (r"(Java 8|spring-boot.*2\.)", "runtime", "Unsupported runtime"),
            (r"(AngularJS 1|angular\.js)", "frontend_runtime", "Unsupported frontend runtime"),
            (r"(Jenkins|pipeline)", "pipeline", "Legacy delivery pipeline"),
            (r"(SOAP|wsdl|basic auth|allowlist|allowlisted)", "integration", "Legacy integration constraint"),
            (r"(cron|nightly|reconcile|batch)", "job", "Batch job dependency"),
            (r"(plaintext|unencrypted|sslmode=disable|tls=false)", "transport", "Unencrypted transport"),
        ]

        for idx, line in enumerate(lines, start=1):
            for pattern, evidence_type, normalized_value in patterns:
                if not re.search(pattern, line, flags=re.IGNORECASE):
                    continue
                self._add_evidence(
                    source_type="file",
                    source_uri=rel,
                    evidence_type=evidence_type,
                    excerpt=line.strip(),
                    line_start=idx,
                    normalized_value=normalized_value,
                )

        if path.suffix.lower() in {".yml", ".yaml", ".json", ".conf"}:
            self._infer_config_edges(rel, text)
        if path.suffix.lower() in {".sql"}:
            self._infer_sql_edges(rel, text)
        if path.suffix.lower() in {".log"}:
            self._infer_log_findings(rel, text)

    def _infer_config_edges(self, rel: str, text: str) -> None:
        lower = text.lower()
        if "jdbc:postgresql" in lower or "postgresql://" in lower:
            self._add_edge("backend", "database", "depends_on", rel)
        if "nfs" in lower or "/mnt/shared" in lower:
            self._add_edge("jobs", "storage", "writes_to", rel)
            self._add_edge("backend", "storage", "writes_to", rel)
        if "api.legacycart.local" in lower or "backend" in lower:
            self._add_edge("frontend", "backend", "calls", rel)
        if "jenkins" in lower or "pipeline" in lower or "ssh" in lower:
            self._add_edge("pipeline", "backend", "deployed_via", rel)
        if "soap" in lower or "wsdl" in lower:
            self._add_edge("backend", "integration", "calls", rel)

    def _infer_sql_edges(self, rel: str, text: str) -> None:
        if "orders" in text.lower():
            self._add_edge("backend", "database", "reads_from", rel)
            self._add_edge("jobs", "database", "reads_from", rel)

    def _infer_log_findings(self, rel: str, text: str) -> None:
        if "authorization" in text.lower() or "cookie=" in text.lower():
            evidence_id = self._add_evidence(
                source_type="log",
                source_uri=rel,
                evidence_type="log_leak",
                excerpt=text.splitlines()[0].strip(),
                line_start=1,
                normalized_value="Sensitive request metadata in logs",
            )
            self.state.findings.append(
                Finding(
                    id="F-LOG-LEAK",
                    title="Logs may expose authorization headers or cookies",
                    category="observability",
                    severity="high",
                    confidence=0.93,
                    summary="Production logs contain request metadata that can leak session or auth material.",
                    recommendation="Redact sensitive request headers and cookies before retaining logs.",
                    evidence_ids=[evidence_id],
                    affected_components=["backend"],
                )
            )

    def _add_file_evidence(
        self,
        source_uri: str,
        evidence_type: str,
        excerpt: str,
        line_start: int | None = None,
        normalized_value: str | None = None,
    ) -> str:
        return self._add_evidence(
            source_type="file",
            source_uri=source_uri,
            evidence_type=evidence_type,
            excerpt=excerpt,
            line_start=line_start,
            normalized_value=normalized_value,
        )

    def _add_evidence(
        self,
        source_type: str,
        source_uri: str,
        evidence_type: str,
        excerpt: str,
        line_start: int | None = None,
        normalized_value: str | None = None,
        redaction_applied: bool = False,
        redaction_reason: str | None = None,
    ) -> str:
        evidence_id = f"ev_{self._evidence_counter:04d}"
        self._evidence_counter += 1
        confidence = 0.98 if evidence_type in {"secret", "runtime", "storage_risk", "transport"} else 0.9
        locator: dict[str, int | str] | None = (
            {"lineStart": line_start, "lineEnd": line_start} if line_start else None
        )
        should_redact = redaction_applied or evidence_type in {"secret", "log_leak"}
        stored_excerpt = self._redact_excerpt(evidence_type, excerpt) if should_redact else excerpt
        content_hash = f"sha256:{sha256(f'{source_type}:{source_uri}:{excerpt}'.encode()).hexdigest()}"
        self.state.evidence.append(
            Evidence(
                id=evidence_id,
                source_type=source_type,  # type: ignore[arg-type]
                source_uri=source_uri,
                evidence_type=evidence_type,
                excerpt=stored_excerpt[:240],
                confidence=confidence,
                locator=locator,
                content_hash=content_hash,
                normalized_value=normalized_value,
                redaction_applied=should_redact,
                redaction_reason=redaction_reason
                or (
                    "credential_material"
                    if evidence_type == "secret"
                    else "sensitive_request_metadata"
                    if evidence_type == "log_leak"
                    else None
                ),
            )
        )
        return evidence_id

    def _add_edge(self, source: str, target: str, relation: str, evidence_uri: str) -> None:
        edge_id = f"edge_{len(self.state.dependencies) + 1:03d}"
        evidence_id = self._add_evidence(
            source_type="manifest",
            source_uri=evidence_uri,
            evidence_type="dependency",
            excerpt=f"{source} {relation} {target}",
            normalized_value=f"{source}->{target}:{relation}",
        )
        self.state.dependencies.append(
            DependencyEdge(id=edge_id, source=source, target=target, relation=relation, evidence_ids=[evidence_id])  # type: ignore[arg-type]
        )

    def _derive_findings_and_recommendations(self) -> None:
        finding_specs = [
            (
                "F-001",
                "Hardcoded production database credentials are present",
                "secrets",
                "critical",
                0.98,
                "Production config includes embedded database credentials that should be rotated immediately.",
                "Externalize secrets into a vault or environment store and rotate the exposed credentials.",
                ["backend"],
                [e.id for e in self.state.evidence if e.evidence_type == "secret"][:2],
            ),
            (
                "F-002",
                "Legacy Java 8 and Spring Boot 2 runtime increase migration risk",
                "runtime",
                "high",
                0.96,
                "The backend runs on an outdated runtime that is not a strong foundation for cloud migration.",
                "Upgrade to a supported JDK and containerize the service before migration.",
                ["backend"],
                [e.id for e in self.state.evidence if e.evidence_type == "runtime"][:1],
            ),
            (
                "F-003",
                "Logs contain sensitive request metadata",
                "logging",
                "high",
                0.93,
                "Sample logs show authorization and cookie values that should not be retained in plain text.",
                "Redact sensitive headers at the logging layer and shrink retention windows.",
                ["backend"],
                [e.id for e in self.state.evidence if e.evidence_type == "log_leak"][:1],
            ),
            (
                "F-004",
                "Shared NFS storage is used for invoice exports",
                "storage",
                "high",
                0.95,
                "File output lands on shared storage instead of object storage with lifecycle controls.",
                "Move exported artifacts to encrypted object storage with signed access and retention policies.",
                ["jobs", "storage"],
                [e.id for e in self.state.evidence if e.evidence_type == "storage_risk"][:2],
            ),
            (
                "F-005",
                "Jenkins uses long-lived deployment credentials",
                "delivery",
                "high",
                0.92,
                "The delivery pipeline relies on a long-lived SSH key and static cloud credentials.",
                "Replace static deploy secrets with short-lived role assumption and gated CI/CD actions.",
                ["pipeline"],
                [e.id for e in self.state.evidence if e.evidence_type == "secret"][-2:],
            ),
            (
                "F-006",
                "Payment integration and ERP sync are brittle external dependencies",
                "integration",
                "medium",
                0.88,
                "SOAP and SFTP dependencies create network and modernization constraints.",
                "Wrap external integrations behind adapters and document allowlists before migration.",
                ["integration"],
                [e.id for e in self.state.evidence if e.evidence_type == "integration"][:2],
            ),
            (
                "F-007",
                "Application transport and database connectivity are not clearly encrypted",
                "network",
                "high",
                0.90,
                "Config files reference plaintext connections and weak transport defaults.",
                "Enforce TLS for service-to-database and service-to-service traffic before move day.",
                ["backend", "database"],
                [e.id for e in self.state.evidence if e.evidence_type == "transport"][:2],
            ),
        ]

        for spec in finding_specs:
            finding_id, title, category, severity, confidence, summary, recommendation, affected, evidence_ids = spec
            if not evidence_ids:
                continue
            self.state.findings.append(
                Finding(
                    id=finding_id,
                    title=title,
                    category=category,
                    severity=severity,  # type: ignore[arg-type]
                    confidence=confidence,
                    summary=summary,
                    recommendation=recommendation,
                    evidence_ids=evidence_ids,
                    affected_components=affected,
                )
            )

        rec_specs = [
            ("R-001", "Externalize secrets and rotate exposed credentials", "small", "high", "Reduce immediate compromise risk before any migration work.", ["F-001"]),
            ("R-002", "Upgrade runtime and containerize backend", "large", "high", "Create a supportable deployment target for the cloud landing zone.", ["F-002"]),
            ("R-003", "Redact logs and tighten retention", "small", "medium", "Lower compliance and incident-response risk.", ["F-003"]),
            ("R-004", "Move invoice exports to encrypted object storage", "medium", "high", "Replace fragile shared storage with a cloud-ready artifact flow.", ["F-004"]),
            ("R-005", "Replace Jenkins static secrets with short-lived credentials", "medium", "high", "Enable auditable, approval-gated deployment paths.", ["F-005"]),
            ("R-006", "Wrap external integrations with adapters", "medium", "medium", "Reduce blast radius and simplify phased migration.", ["F-006"]),
            ("R-007", "Enforce TLS for app and database traffic", "small", "high", "Eliminate transport exposure before any cutover.", ["F-007"]),
        ]
        for rec_id, title, effort, impact, rationale, finding_ids in rec_specs:
            linked_findings = [item for item in self.state.findings if item.id in finding_ids]
            if not linked_findings:
                continue
            self.state.recommendations.append(
                Recommendation(
                    id=rec_id,
                    title=title,
                    summary=rationale,
                    confidence=min(linked.confidence for linked in linked_findings),
                    rationale=rationale,
                    effort=effort,  # type: ignore[arg-type]
                    impact=impact,  # type: ignore[arg-type]
                    finding_ids=finding_ids,
                )
            )

    def _build_scenarios(self) -> list[Scenario]:
        return [
            Scenario(
                id="S-001",
                name="Security-first migration",
                description="Remediate secrets, logging, and transport issues before moving any workloads.",
                assumption_set=[
                    "Rotate exposed credentials",
                    "Redact logs",
                    "Enforce TLS",
                ],
                outcome=ScenarioOutcome(
                    readiness=62,
                    risk_delta="risk drops materially after blocker remediation",
                    cost_delta="migration cost rises slightly upfront but avoids rework",
                    summary="Best if the customer prioritizes compliance and minimal surprise risk.",
                ),
                kind="security_first",
            ),
            Scenario(
                id="S-002",
                name="Lift-and-shift with guardrails",
                description="Containerize and move the monolith quickly, then remediate lower-severity items after cutover.",
                assumption_set=[
                    "Accept temporary technical debt",
                    "Keep batch jobs intact",
                    "Add monitoring before cutover",
                ],
                outcome=ScenarioOutcome(
                    readiness=48,
                    risk_delta="operational risk stays elevated until runtime modernization",
                    cost_delta="lowest near-term cost but highest long-term carry cost",
                    summary="Useful only if timeline is tighter than remediation capacity.",
                ),
                kind="lift_shift_guardrails",
            ),
            Scenario(
                id="S-003",
                name="Strangler modernization",
                description="Carve out invoice export, reconciliation, and admin surfaces in phases.",
                assumption_set=[
                    "Modernize the highest-friction seams first",
                    "Use adapter services around integrations",
                    "Preserve business continuity during transition",
                ],
                outcome=ScenarioOutcome(
                    readiness=55,
                    risk_delta="medium-term risk falls as seams are extracted",
                    cost_delta="moderate migration spend with best long-term flexibility",
                    summary="Most balanced plan for an MSP-led modernization engagement.",
                ),
                kind="strangler_modernization",
            ),
        ]

    def _build_summary(self) -> ScanSummary:
        critical = sum(1 for item in self.state.findings if item.severity == "critical")
        blocker_count = sum(1 for item in self.state.findings if item.severity in {"critical", "high"})
        base = 92
        deduction = critical * 12 + blocker_count * 4
        readiness = max(25, min(92, base - deduction))
        if readiness >= 70:
            recommendation = "migrate partially"
        elif readiness >= 50:
            recommendation = "defer until blockers are remediated"
        else:
            recommendation = "re-architect first"
        provider_ranking: list[dict[str, str | int]] = [
            {"provider": "AWS", "score": 84, "best_for": "broad managed service depth and migration tooling"},
            {"provider": "GCP", "score": 76, "best_for": "data and analytics heavy modernization"},
            {"provider": "Azure", "score": 73, "best_for": "Microsoft identity and enterprise integration"},
        ]
        confidence = round(min((item.confidence for item in self.state.findings), default=0.75), 2)
        return ScanSummary(
            readiness_score=readiness,
            recommendation=recommendation,
            confidence=confidence,
            blocker_count=blocker_count,
            critical_finding_count=critical,
            provider_ranking=provider_ranking,
        )

    def _build_source_metadata(self) -> SourceMetadata:
        slug = re.sub(r"[^a-z0-9]+", "-", self.root.name.lower()).strip("-") or "source"
        return SourceMetadata(
            kind="local_directory",
            connection_id=f"source-local-{slug}",
            name="LegacyCart",
            root_path=str(self.root),
        )

    def _build_pipeline_phases(self) -> list[PipelinePhase]:
        return [
            PipelinePhase(pipeline_key="source_registration", name="Source registration", status="succeeded"),
            PipelinePhase(pipeline_key="evidence_ingestion", name="Evidence ingestion", status="succeeded"),
            PipelinePhase(pipeline_key="evidence_normalization", name="Evidence normalization", status="succeeded"),
            PipelinePhase(pipeline_key="graph_construction", name="Dependency graph construction", status="succeeded"),
            PipelinePhase(pipeline_key="risk_scoring", name="Risk scoring", status="succeeded"),
            PipelinePhase(pipeline_key="result_packaging", name="Result packaging", status="succeeded"),
        ]

    def _build_connector_handoffs(self) -> list[ConnectorHandoff]:
        return [
            ConnectorHandoff(
                kind="github",
                name="GitHub repository handoff",
                required_credentials=True,
                template="github-repository-import",
                description="Hand off the scan into a GitHub-backed migration repository for issue and PR tracking.",
            ),
            ConnectorHandoff(
                kind="azure_repos",
                name="Azure Repos handoff",
                required_credentials=True,
                template="azure-repos-import",
                description="Hand off the scan into Azure Repos for enterprise source control workflows.",
            ),
        ]

    def _redact_excerpt(self, evidence_type: str, excerpt: str) -> str:
        redacted = excerpt
        if evidence_type == "secret":
            redacted = re.sub(
                r"(?i)(password|passwd|secret|token)\s*([:=])\s*(\"[^\"]*\"|'[^']*'|[^\s,]+)",
                r"\1\2 <redacted>",
                redacted,
            )
        if evidence_type == "log_leak":
            redacted = re.sub(r"(?i)(Authorization\s*=\s*Bearer)\s+\S+", r"\1 <redacted>", redacted)
            redacted = re.sub(r"(?i)(cookie\s*=\s*)\S+", r"\1<redacted>", redacted)
        return redacted


def scan_legacycart(root: str | Path) -> ScanResult:
    return LegacyCartScanner(Path(root)).scan()


def result_to_json(result: ScanResult, *, as_dict: bool = False) -> str | dict:
    payload = result.to_dict()
    if as_dict:
        return payload
    return json.dumps(payload, indent=2, sort_keys=True)


def iter_supported_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path
