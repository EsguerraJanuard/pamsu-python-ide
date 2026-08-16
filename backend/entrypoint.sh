#!/bin/bash
set -e

echo "Starting backend entrypoint..."

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python seed.py

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
