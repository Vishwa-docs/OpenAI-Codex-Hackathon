#!/usr/bin/env bash
set -euo pipefail

sftp -oPort=22 legacycart_erp@erp.partner.local <<'EOF'
put export/orders.csv /incoming/orders.csv
EOF

