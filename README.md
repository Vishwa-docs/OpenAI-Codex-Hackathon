# Cloud Migration Cockpit

Cloud Migration Cockpit is an AI-native migration assessment and planning control plane for MSPs, solution architects, and cloud operators. This repository ships both first-class deliverables:

- A runnable local product with a Next.js cockpit, FastAPI control plane, worker service, seeded demo system, reports, approvals, and artifacts.
- A polished marketing website that shares the same design system and demo narrative.

## What the MVP Covers

- Marketing site and product shell
- Workspace, project, tenant, and intake scaffolding
- Demo-tenant migration assessment for a legacy commerce system built from the real local scan path
- Evidence, findings, recommendations, and provider comparison views
- Scenario analysis, approvals, audit timeline, and artifact/report surfaces
- Local worker service, local worker CLI contract, and assessment orchestration surfaces
- Agent Factory / Tool Factory scaffolding for future extensibility

## Monorepo Layout

```text
apps/
  web/                     # Next.js marketing site + cockpit UI
packages/
  contracts/               # Shared TypeScript contracts for the web client
services/
  api/                     # FastAPI orchestration and report generation
  worker/                  # Local scanner and evidence normalization worker
demo-systems/
  legacycart/              # Seed on-prem demo system with realistic blockers
docs/
  diagrams/                # Mermaid architecture diagrams
```

## Core Product Slice

The first shipped slice is sync-first and async-ready:

1. Create or open a migration project in the cockpit UI.
2. Scan `demo-systems/legacycart` with the local worker contract.
3. Persist a normalized dossier containing evidence, dependency graph edges, findings, and scenario/report inputs.
4. Run the assessment flow that produces a recommendation, cost/ROI view, provider comparison, compliance/risk summary, and generated artifacts.
5. Review approvals, audit trail, reports, and planning artifacts.

The runtime model already includes run/task metadata, report versions, audit events, and approval gates so we can later move assessment execution to queue-backed workers and add real cloud connectors.

## Local Development

### Prerequisites

- Node.js 22+
- npm 11+
- Python 3.11+
- `uv`
- Docker Desktop

### Environment

Copy `.env.example` to `.env` and adjust only if you want to change ports or use a different database/object store setup.

### One-Command Local Stack

```bash
npm install
uv sync
make stack
```

That single command starts:

- Next.js marketing site + cockpit on `http://127.0.0.1:3000`
- FastAPI control plane on `http://127.0.0.1:8000/api/v1`
- Worker service on `http://127.0.0.1:8001`
- PostgreSQL, Redis, and MinIO through Docker Compose

### Infrastructure Only

```bash
docker compose up -d postgres redis minio
```

### Python Environment

```bash
uv venv
uv sync
```

### Frontend

```bash
npm install
npm run dev:web
```

### API

```bash
uv run uvicorn services.api.app.main:app --reload --port 8000
```

### Worker Demo Scan

```bash
uv run python -m services.worker.app.cli scan demo-systems/legacycart
```

### Worker Service

```bash
uv run uvicorn services.worker.app.main:app --reload --port 8001
```

## Documentation

- [Architecture](docs/architecture.md)
- [Implementation Roadmap](docs/implementation-roadmap.md)
- [Demo Script](docs/demo-script.md)
- [Presentation Outline](docs/presentation-outline.md)
- [System Context Diagram](docs/diagrams/system-context.mmd)
- [Assessment Flow Diagram](docs/diagrams/assessment-flow.mmd)

## Connectors and Keys

The local stack runs without third-party credentials for the included demo tenant. Live GitHub, Azure Repos, OpenAI, email, and AWS validation require the credentials documented in [SETUP.md](SETUP.md). When those credentials are missing, the product surfaces `needs_configuration` instead of claiming a live connection, and the stakeholder chat path will explicitly ask for `OPENAI_API_KEY` instead of fabricating an answer.
