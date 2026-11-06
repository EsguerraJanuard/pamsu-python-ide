#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Running database migrations..."
# A migration that needs a busy table waits only briefly for its lock, then
# rolls back (see b7e4c2a91f03). Whatever holds the table is usually done
# within a minute, so try a few times before giving up.
attempt=1
until alembic upgrade head; do
  if [ "$attempt" -ge 5 ]; then
    echo "Database migrations failed after $attempt attempts." >&2
    exit 1
  fi
  echo "Migration attempt $attempt failed; trying again in 20 seconds..."
  attempt=$((attempt + 1))
  sleep 20
done

echo "Starting Celery worker in the background..."
# We run celery in the background so both Celery and FastAPI share the same Free-Tier container
celery -A app.tasks.celery_worker worker --loglevel=info &

echo "Starting FastAPI server..."
# Uvicorn will bind to the port provided by Render's $PORT environment variable
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
