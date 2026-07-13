#!/bin/bash
# Daily cron: pg_dump → offsite storage
# TODO: configure S3 destination and DB connection
set -euo pipefail
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="/tmp/mela_express_${TIMESTAMP}.sql"
pg_dump "$DATABASE_URL" > "$DUMP_FILE"
echo "Backup written to $DUMP_FILE"
# TODO: upload $DUMP_FILE to offsite storage
