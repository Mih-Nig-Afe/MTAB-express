#!/bin/sh
set -e
if [ "$FRESH_DB" = "1" ]; then
  echo "Resetting database schema (FRESH_DB=1)..."
  python scripts/reset_db.py
fi
echo "Bootstrapping PostgreSQL enums..."
python scripts/bootstrap_enums.py
echo "Running database migrations..."
alembic upgrade head
if [ "$SEED_DB" = "1" ]; then
  echo "Seeding database..."
  python scripts/seed_branches.py || true
  python scripts/seed_admin.py || true
  python scripts/seed_staff.py || true
fi
if [ "$SEED_SAMPLE" = "1" ]; then
  echo "Seeding sample parcels (SEED_SAMPLE=1)..."
  python scripts/seed_sample_data.py || true
fi
echo "Starting API on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
