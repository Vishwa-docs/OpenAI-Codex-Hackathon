#!/usr/bin/env bash
set -euo pipefail

export PGPASSWORD="REDACTED_FAKE_DB_PASSWORD"
psql -h postgres.legacycart.local -U legacycart_recon -d legacycart -c "select count(*) from orders;"

