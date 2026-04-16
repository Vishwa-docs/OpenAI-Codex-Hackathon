# Cloud Migration Cockpit Setup

This file is the required handoff for live integrations. The product must run locally without third-party credentials for the seeded demo tenant, but the real SaaS features below need valid sandbox credentials before live integration tests can pass.

## 1. Local Tooling

- Node.js 22+
- npm 11+
- Python 3.11+
- `uv`
- Docker Desktop

## 2. Core Environment

Copy `.env.example` to `.env` and fill these values.

### Required for local app startup

- `DATABASE_URL`
- `REDIS_URL`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET`
- `APP_ENCRYPTION_KEY`
- `INTERNAL_SERVICE_TOKEN_SECRET`
- `BETTER_AUTH_URL`
- `BETTER_AUTH_SECRET`
- `NEXT_PUBLIC_APP_URL`
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_WORKER_BASE_URL`
- `NEXT_PUBLIC_DEFAULT_WORKSPACE_ID`

### Required for OpenAI-backed orchestration

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL` if you are routing through a compatible gateway instead of the default OpenAI API

### Required for email and auth flows

Use one of:

- SMTP:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USERNAME`
  - `SMTP_PASSWORD`
  - `SMTP_FROM`
- or AWS SES:
  - `AWS_SES_REGION`
  - `AWS_SES_FROM`

### Required for GitHub live validation

Use one of:

- GitHub App:
  - `GITHUB_APP_ID`
  - `GITHUB_APP_PRIVATE_KEY`
  - `GITHUB_WEBHOOK_SECRET`
- or PAT:
  - `GITHUB_PAT`

### Required for Azure Repos live validation

Use one of:

- PAT:
  - `AZURE_DEVOPS_PAT`
- or OAuth app:
  - `AZURE_DEVOPS_CLIENT_ID`
  - `AZURE_DEVOPS_CLIENT_SECRET`
  - `AZURE_DEVOPS_TENANT_ID`

### Required for AWS discovery and dry-run execution

- `AWS_REGION`
- `AWS_DISCOVERY_ROLE_ARN`
- `AWS_DRY_RUN_ROLE_ARN`
- `AWS_EXTERNAL_ID` if your sandbox requires it
- `AWS_S3_BUCKET` for production-aligned artifact validation
- `AWS_KMS_KEY_ID` for production-aligned encryption validation

## 3. Local Services

Start the infra services:

```bash
docker compose up -d postgres redis minio mailpit
```

Mailpit UI:

- Web: `http://127.0.0.1:8025`

MinIO UI:

- Web: `http://127.0.0.1:9001`

## 4. Install Dependencies

```bash
npm install
uv sync
```

## 5. Run the Stack

```bash
make stack
```

Expected local endpoints:

- Web: `http://127.0.0.1:3000`
- API: `http://127.0.0.1:8000/api/v1`
- Worker: `http://127.0.0.1:8001`

## 6. Validation Commands

### Static checks

```bash
uv run ruff check services
uv run mypy services
npm run lint:web
npm run typecheck:web
```

### Functional tests

```bash
python3 -m pytest services/api/tests services/worker/tests -q
npm run test:web
```

### Live-marked integration suites

These should be skipped until the corresponding credentials are set.

```bash
python3 -m pytest -m live_openai -q
python3 -m pytest -m live_github -q
python3 -m pytest -m live_azure_repos -q
python3 -m pytest -m live_aws -q
```

## 7. Sandbox Guidance

- Use sandbox-only GitHub, Azure DevOps, and AWS accounts.
- Grant read-only access for discovery integrations.
- Use separate AWS roles for discovery and dry-run planning.
- Do not use production secrets in `.env`.

## 8. Demo Seed

The only seeded content in the final product should be:

- the demo tenant/bootstrap flow
- the `demo-systems/legacycart` workload

Everything else must run through the same real auth, persistence, orchestration, reporting, approval, and artifact paths as non-demo tenants.
