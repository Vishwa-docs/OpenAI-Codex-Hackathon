# Cloud Migration Cockpit Architecture

## Product Positioning

Cloud Migration Cockpit is an evidence-backed migration assessment and planning SaaS for MSPs and cloud consultancies. It combines a hosted control plane with a local customer-side worker to analyze source systems, normalize evidence, generate migration recommendations, and prepare approval-gated planning artifacts.

## MVP Architecture Decisions

### Experience

- Public marketing surface and private cockpit live in one Next.js App Router application.
- The product shell is optimized for investor-friendly demos: clear KPIs, strong visual hierarchy, concise stakeholder-friendly copy, and deep drill-down views for technical users.
- The included demo tenant runs on the same control-plane surfaces as the product; only the demo workload and demo tenant data are preloaded.

### Control Plane

- FastAPI serves as the orchestration API and report/export backend.
- The assessment engine is sync-first today, but all runs are modeled as `AssessmentRun` records so the same contract can move to async queue execution later.
- Reports, audit events, approvals, and generated artifacts are stored as structured objects rather than only rendered text.

### Local Worker

- The worker scans a local repo or directory and converts raw evidence into canonical evidence records, normalized components, graph edges, and scanner findings.
- The worker powers the included demo workload from the real repository files and can validate local-directory connector requests immediately.
- GitHub and Azure Repos support are exposed as read-only connector contracts that stay in `needs_configuration` until live credentials are supplied.

### Data and Infra

- PostgreSQL is the system of record for organizations, projects, runs, reports, findings, approvals, and audit events.
- Redis is reserved for queueing, cached assessment payloads, and future async orchestration.
- MinIO is used locally as the S3-compatible object store for generated report files and artifact payloads.
- The Python services use a root `uv` environment and the web app uses npm workspaces.

## System Boundaries

### `apps/web`

- Marketing pages: homepage, product, pricing, demo CTA
- Cockpit shell: dashboard, intake wizard, project overview, findings, provider comparison, cost/ROI, risk/compliance, scenarios, artifacts, approvals, audit log, stakeholder chat, settings/connectors
- Type-safe API client using contracts from `packages/contracts`

### `services/api`

- Health and seed/project endpoints
- Assessment orchestration
- Scenario execution
- Report generation and PDF export
- Audit event and approval APIs
- Tool registry and Agent Factory / Tool Factory endpoints

### `services/worker`

- Local scan CLI and HTTP-ready scanner contract
- Evidence normalization and dependency graph extraction
- Rules for secrets, aging runtimes, logging leaks, storage/network risks, and brittle operational workflows

### `packages/contracts`

- Shared TypeScript contracts for API responses, dashboard summaries, graph payloads, findings, scenarios, reports, approvals, audit events, and registry entries

### `demo-systems/legacycart`

- Seeded legacy commerce application with realistic migration blockers:
  - hardcoded secrets
  - legacy runtime versions
  - leaked sensitive logs
  - NFS-based document storage
  - Jenkins deploy keys
  - cron jobs with direct database dependencies
  - SOAP and SFTP integrations

## Assessment Swarm

The current control plane exposes the specialist-agent surfaces with structured outputs:

1. Intake Normalizer Agent
2. Codebase Discovery Agent
3. Infra Manifest Analyzer Agent
4. Dependency Graph Agent
5. Database & Data Store Analyzer Agent
6. Runtime / Ops Readiness Agent
7. Security & Secrets Agent
8. Risk & Compliance Agent
9. Cloud Recommendation Agent
10. Cost & ROI Agent
11. Architecture Planner Agent
12. Container / Kubernetes Planner Agent
13. DevOps Pipeline Agent
14. Scenario / What-if Agent
15. Report Composer Agent
16. Executive Summary Agent
17. Tool Gap Detector Agent
18. Tool / Connector Scaffold Agent
19. Safety Critic Agent
20. Citation / Evidence Critic Agent
21. Final Recommendation Aggregator

Each agent returns:

- machine-readable payload
- human summary
- evidence references
- confidence score
- assumptions and limitations

Critic agents validate coverage, safety, and citation integrity before final recommendation payloads are exposed to the UI.

## Agent Factory / Tool Factory

The internal factory subsystem exists from day one, even in stub form:

- `Tool Gap Detector Agent` identifies unsupported capabilities.
- `Tool / Connector Scaffold Agent` generates a disabled registry entry, manifest, stub implementation, and test placeholder.
- Registry entries record:
  - purpose
  - required permissions
  - safety level
  - approval requirement
  - prompt/tool definition version
  - enablement state

This keeps extension pathways explicit and auditable instead of burying them in undocumented prompts or ad hoc scripts.

## Security and Safety Model

- Read-only discovery by default
- No destructive cloud action in the MVP
- Secrets are redacted before entering model-visible summaries
- Approval records exist for later planning and execution phases
- Audit events are emitted for scan start/end, assessment runs, approval decisions, report generation, and tool factory proposals
- Connectors remain disabled until configured and approved

## Stage Boundaries

### Stage 1 in the current build

- demo-tenant intake flow
- real local worker scan and dossier for the bundled legacy workload
- provider, cost, risk, and scenario views
- reports, artifacts, approvals, audit log, and stakeholder chat

### Stage 2 extension path

- richer planning artifact generation
- Terraform and Kubernetes snippets tailored to chosen scenarios
- queue-backed assessment execution
- report templates with export jobs

### Stage 3 extension path

- AWS execution adapter with dry-run-first enforcement
- short-lived credential workflows
- approval-gated cloud writes
- deeper multi-cloud and connector coverage
