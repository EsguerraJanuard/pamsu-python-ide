#!/bin/bash
set -e

echo "Starting backend entrypoint..."

echo "Running database migrations..."
alembic upgrade head

# Local Docker stack only (docker-compose sets the flag): reset and reseed
# the demo data on every start. Anywhere else this step is skipped.
if [ "${PAMSU_ALLOW_DATABASE_RESET:-}" = "true" ]; then
    echo "Resetting and seeding the local database..."
    python seed.py --reset --unattended
fi

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
