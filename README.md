# Cloud Migration Cockpit

Cloud Migration Cockpit is an AI-assisted migration assessment platform for MSPs, solution architects, and cloud modernization teams. This repository contains the product website, the authenticated cockpit, the orchestration API, the local worker, shared contracts, and a seeded legacy workload used for demos and testing.

The repo is organized as a polyglot monorepo:

- `apps/web`: Next.js marketing site and authenticated cockpit UI
- `apps/desktop`: desktop companion app
- `services/api`: FastAPI orchestration, reporting, auth, and project APIs
- `services/worker`: local discovery and normalization worker
- `packages/contracts`: shared TypeScript contracts used by the frontend
- `demo-systems/legacycart`: seeded legacy workload for demos and assessments

## Table Of Contents

- [Why This Repo Exists](#why-this-repo-exists)
- [System Overview](#system-overview)
- [Repository Layout](#repository-layout)
- [Core Capabilities](#core-capabilities)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Running The System](#running-the-system)
- [Common Commands](#common-commands)
- [Testing And Quality Checks](#testing-and-quality-checks)
- [Documentation](#documentation)
- [Operational Notes](#operational-notes)
- [Troubleshooting](#troubleshooting)
- [Security And Credentials](#security-and-credentials)

## Why This Repo Exists

Most migration tooling stops at inventory or one-off reporting. Cloud Migration Cockpit is designed as a working control plane:

- capture project and source-system context
- ingest and normalize evidence from a real workload
- generate findings, recommendations, scenarios, and report artifacts
- route operators through approvals, audit history, and follow-up actions
- support a polished product narrative and a runnable local demo from the same codebase

## System Overview

At a high level, the platform has four main runtime surfaces:

1. `apps/web`
   The public product site plus the authenticated migration cockpit.
1. `services/api`
   The orchestration and reporting layer exposed through FastAPI.
1. `services/worker`
   The local worker that scans workloads and produces normalized evidence.
1. `demo-systems/legacycart`
   The seeded legacy application used for the default demo and test flows.

Typical local workflow:

1. Start infrastructure services with Docker.
1. Start the web app, API, and worker.
1. Open the product site or the demo flow at `http://127.0.0.1:3000`.
1. Use the seeded LegacyCart workload or create a new project/workspace flow.
1. Review findings, scenarios, reports, approvals, and cockpit state in the UI.

## Repository Layout

```text
.
├─ apps/
│  ├─ desktop/                # Desktop companion app
│  └─ web/                    # Next.js marketing site + cockpit UI
├─ demo-systems/
│  └─ legacycart/             # Seeded legacy workload used for local demo flows
├─ docs/                      # Product, architecture, and demo documentation
├─ packages/
│  └─ contracts/              # Shared TypeScript contracts
├─ scripts/                   # Local development helpers
├─ services/
│  ├─ api/                    # FastAPI orchestration and reporting service
│  └─ worker/                 # Local scanner / evidence worker
├─ docker-compose.yml         # Local infra services
├─ Makefile                   # Common dev tasks
├─ package.json               # JS workspace root
├─ pyproject.toml             # Python dependency and tooling config
├─ SETUP.md                   # Integration and credential setup details
└─ README.md
```

## Core Capabilities

- Public-facing product marketing site with a consistent design system
- Authenticated cockpit for projects, findings, scenarios, connectors, approvals, and reports
- Workspace and intake flows for migration projects
- FastAPI APIs for orchestration, reporting, auth, and demo workflows
- Local worker scan path for seeded workload analysis
- Report/export surfaces and audit/approval tracking
- Shared contracts between web and backend-facing client code
- Local demo mode that works without live third-party credentials

## Technology Stack

### Frontend

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Vitest and Testing Library

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy
- Psycopg
- Redis
- Dramatiq
- ReportLab

### Infrastructure

- PostgreSQL
- Redis
- MinIO
- Mailpit
- Docker Compose

### Auth And Integrations

- Better Auth
- GitHub and Azure DevOps integration hooks
- OpenAI-backed orchestration hooks
- AWS discovery and dry-run support hooks

## Prerequisites

Install the following locally:

- Node.js 22+
- npm 11+
- Python 3.11+
- `uv`
- Docker Desktop

## Quick Start

### 1. Clone And Enter The Repository

```bash
git clone <your-fork-or-repo-url>
cd OpenAI-Codex-Hackathon
```

### 2. Create Your Local Environment File

```bash
cp .env.example .env
```

For a local demo-only setup, most defaults can stay as-is. See [SETUP.md](SETUP.md) for production-aligned or live integration requirements.

### 3. Install Dependencies

```bash
npm install
uv sync
```

### 4. Start The Full Local Stack

```bash
make stack
```

Expected endpoints:

- Web: `http://127.0.0.1:3000`
- API: `http://127.0.0.1:8000/api/v1`
- Worker: `http://127.0.0.1:8001`
- Mailpit UI: `http://127.0.0.1:8025`
- MinIO UI: `http://127.0.0.1:9001`

## Environment Configuration

Copy `.env.example` to `.env` and adjust values as needed.

Key variables you should know about:

- `NEXT_PUBLIC_APP_URL`
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_WORKER_BASE_URL`
- `DATABASE_URL`
- `REDIS_URL`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET`
- `BETTER_AUTH_URL`
- `BETTER_AUTH_SECRET`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `GITHUB_PAT`
- `AWS_REGION`

For a full breakdown of required credentials by feature area, read [SETUP.md](SETUP.md).

## Running The System

### Full Stack

```bash
make stack
```

### Infrastructure Only

```bash
make infra
```

Equivalent root script:

```bash
npm run infra:up
```

### Frontend Only

```bash
npm run dev:web
```

### API Only

```bash
npm run dev:api
```

### Worker Only

```bash
npm run dev:worker
```

### Run The Seeded Worker Scan

```bash
npm run scan:worker
```

### Desktop App

```bash
npm run dev:desktop
```

## Common Commands

### Web

```bash
npm run dev:web
npm run build:web
npm run lint:web
npm run typecheck:web
npm run test:web
```

### Python Services

```bash
npm run dev:api
npm run dev:worker
npm run lint:py
npm run typecheck:py
npm run test:py
```

### Full Verification

```bash
npm run test
npm run static
```

### Terraform / AWS Demo Helpers

```bash
npm run aws:check
npm run terraform:demo:init
npm run terraform:demo:plan
```

## Testing And Quality Checks

Use these commands before opening a PR:

### Frontend

```bash
npm run lint:web
npm run typecheck:web
npm run test:web
```

### Backend

```bash
npm run lint:py
npm run typecheck:py
npm run test:py
```

### Combined

```bash
npm run static
npm run test
```

## Documentation

Project documentation lives in `docs/`.

Useful starting points:

- [docs/architecture.md](docs/architecture.md)
- [docs/implementation-roadmap.md](docs/implementation-roadmap.md)
- [docs/demo-script.md](docs/demo-script.md)
- [docs/presentation-outline.md](docs/presentation-outline.md)
- [docs/diagrams/system-context.mmd](docs/diagrams/system-context.mmd)
- [docs/diagrams/assessment-flow.mmd](docs/diagrams/assessment-flow.mmd)
- [SETUP.md](SETUP.md)

## Operational Notes

- The local demo should work without live third-party credentials.
- Live GitHub, Azure DevOps, OpenAI, SMTP, and AWS features require explicit environment setup.
- The seeded workload is `demo-systems/legacycart`.
- The repo uses a mixed Node.js + Python toolchain. Install both sides before attempting full-stack work.
- The web app and API share assumptions through `packages/contracts`.

## Troubleshooting

### `better-auth/client` or similar module resolution errors

Usually caused by stale dependencies or a stale Next.js dev server.

Try:

```bash
npm install
rm -rf apps/web/.next .next
npm run dev:web
```

On Windows, if `rm -rf` is not available, remove `.next` directories manually.

### Dev server works but build feels slow

`npm run build:web` runs a full production build, not a fast dev compile. It is expected to take longer than `npm run dev:web`.

### Python service import or dependency failures

Re-sync the environment:

```bash
uv sync
```

### Docker-backed services are not reachable

Bring infra back up:

```bash
npm run infra:up
```

### Tests fail after branch switches

Refresh dependencies and caches:

```bash
npm install
uv sync
```

## Security And Credentials

- Do not commit `.env` files or real credentials.
- Use sandbox or demo credentials for live integration testing.
- Keep production secrets out of local demo environments.
- Treat GitHub, Azure DevOps, AWS, SMTP, and OpenAI credentials as optional unless you are actively validating those integrations.

## Contributing

Recommended workflow:

1. Branch from the latest target branch.
1. Keep frontend and backend changes scoped when possible.
1. Run lint, typecheck, and tests before pushing.
1. Open a PR with a concise summary of user-facing and operational changes.

---

If you are setting up live integrations or production-aligned validation, start with [SETUP.md](SETUP.md). If you want the local demo only, start with [Quick Start](#quick-start).
