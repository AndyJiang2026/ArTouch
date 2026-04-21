#!/bin/bash
# ArtTouch Backend Entrypoint Script
# Runs Alembic migrations before starting the application

set -e

echo "=========================================="
echo "ArtTouch Backend - Starting..."
echo "=========================================="

# Wait for database to be ready (only if using PostgreSQL)
if [[ "$DATABASE_URL" == *"postgresql"* ]]; then
    echo "Waiting for PostgreSQL to be ready..."
    max_attempts=30
    attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        if pg_isready -h "${DATABASE_URL##*@}" -p 5432 > /dev/null 2>&1; then
            echo "PostgreSQL is ready!"
            break
        fi
        attempt=$((attempt + 1))
        echo "Waiting for PostgreSQL... ($attempt/$max_attempts)"
        sleep 2
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        echo "ERROR: PostgreSQL did not become ready in time"
        exit 1
    fi
fi

# Run Alembic migrations
echo "Running database migrations..."
cd /app
alembic upgrade head

echo "=========================================="
echo "Database migrations complete!"
echo "Starting uvicorn server..."
echo "=========================================="

# Start uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
