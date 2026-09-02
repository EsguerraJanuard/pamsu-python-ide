#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Celery worker in the background..."
# We run celery in the background so both Celery and FastAPI share the same Free-Tier container
celery -A app.tasks.celery_worker worker --loglevel=info &

echo "Starting FastAPI server..."
# Uvicorn will bind to the port provided by Render's $PORT environment variable
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
