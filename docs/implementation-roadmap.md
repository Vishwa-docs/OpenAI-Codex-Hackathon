# Implementation Roadmap

## Milestone 1: Monorepo Spine

- Create the root workspace, environment template, Docker Compose, and developer scripts.
- Add shared contracts, docs, diagrams, and baseline product narrative.
- Scaffold the web app, API service, and worker package boundaries.

## Milestone 2: Seeded Assessment Loop

- Build the local demo system at `demo-systems/legacycart`.
- Implement the worker scanner contract and normalized evidence output.
- Add deterministic assessment orchestration in the API.
- Return seeded findings, recommendations, scenarios, approvals, audit events, and artifacts.

## Milestone 3: Cockpit UI

- Build the marketing homepage, product page, pricing placeholder, and demo CTA.
- Build the authenticated-style cockpit shell and all core project tabs.
- Wire dashboard, overview, findings, provider comparison, cost/ROI, risk, scenarios, artifacts, approvals, audit log, and stakeholder chat to live API responses.

## Milestone 4: Reports and Export

- Generate structured executive and technical reports from assessment results.
- Add PDF export for primary reports.
- Surface report versions, artifact metadata, and audit history in the UI.

## Milestone 5: Factories, Evaluations, and Extensions

- Ship the Agent Factory / Tool Factory registry, disabled scaffold proposals, and approval metadata.
- Add eval summaries for evidence coverage, recommendation consistency, unsupported claim rate, and safety policy compliance.
- Prepare seams for GitHub/Azure Repos connectors and AWS dry-run execution.

## Verification Plan

- API unit tests for assessment orchestration, scenario transforms, report assembly, and registry proposals
- Worker unit tests for evidence extraction and graph normalization
- Web smoke tests for major routes and key view components
- Integration verification with Docker-backed local infra

## Near-Term Extensions After MVP

- Replace seeded auth with real organization membership and session management
- Persist real connector credentials using encrypted storage
- Move assessment execution to Redis-backed background jobs
- Add live GitHub/Azure Repo ingestion and cloud inventory discovery
- Implement AWS adapter write gates after approval flows are proven
