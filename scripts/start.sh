#!/bin/sh
set -e

echo "=== Celestra Finance AI — startup check ==="

if [ -z "$DATABASE_URL" ] && [ -z "$DATABASE_URL_SYNC" ] && [ -z "$POSTGRES_URL" ]; then
  echo "ERROR: No database URL found. Link Postgres to this web service as DATABASE_URL."
  exit 1
fi

if [ -z "$SECRET_KEY" ] && [ "$APP_ENV" = "production" ]; then
  echo "ERROR: SECRET_KEY is required in production."
  exit 1
fi

echo "Database URL: configured"
echo "Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
