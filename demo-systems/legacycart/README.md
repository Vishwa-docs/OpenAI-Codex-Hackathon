# LegacyCart Demo System

LegacyCart is a deliberately aging commerce platform used by Cloud Migration Cockpit to seed
migration assessments.

## What it Contains

- `backend/`: a monolith backend with embedded credentials, an outdated runtime, and direct PostgreSQL access.
- `frontend/admin/`: a legacy AngularJS admin surface.
- `jobs/`: nightly reconciliation and invoice export scripts.
- `db/`: schema and seed data that reflect a live order-processing workload.
- `infra/`: Compose, Jenkins, and Nginx configuration that expose migration blockers.
- `integrations/`: SOAP and SFTP dependencies that constrain cutover strategy.
- `logs/`: sample logs with request metadata leakage.

## Intentional Migration Blockers

The fixture intentionally includes:

- hardcoded fake secrets
- unencrypted transport defaults
- shared NFS storage
- weak observability
- static deployment credentials
- legacy frontend/runtime versions

All credentials are redacted placeholders. Nothing here is real production access.

