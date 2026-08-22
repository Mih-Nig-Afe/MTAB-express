#!/bin/bash
# ── Mela Express Automated Database Backup Script ──────────────────────────────
# Backs up PostgreSQL database with timestamp and gzip compression.

set -e

BACKUP_DIR="${BACKUP_DIR:-/tmp/mela_backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/mela_express_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[*] Starting Mela Express database backup at $(date)..."

# Dump and compress database
PGPASSWORD="${POSTGRES_PASSWORD:-mela}" pg_dump \
  -h "${POSTGRES_HOST:-localhost}" \
  -p "${POSTGRES_PORT:-5433}" \
  -U "${POSTGRES_USER:-mela}" \
  -d "${POSTGRES_DB:-mela_express}" \
  | gzip > "${BACKUP_FILE}"

echo "[+] Backup successfully written to: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Keep last 30 daily backups
find "${BACKUP_DIR}" -name "mela_express_*.sql.gz" -mtime +30 -delete
echo "[+] Cleaned up backups older than 30 days."
