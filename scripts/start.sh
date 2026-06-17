#!/bin/sh
set -e

echo "=== Celestra Finance AI — startup check ==="

if [ -z "$DATABASE_URL" ] && [ -z "$DATABASE_URL_SYNC" ] && [ -z "$POSTGRES_URL" ]; then
  echo ""
  echo "ERROR: No database URL found."
  echo ""
  echo "In Render dashboard:"
  echo "  1. Open your WEB SERVICE (not the database)"
  echo "  2. Environment → Add Environment Variable"
  echo "  3. Choose 'Add from database' → select your existing Postgres"
  echo "     OR paste Internal Database URL as DATABASE_URL"
  echo "  4. Add SECRET_KEY (any random string)"
  echo "  5. Manual Deploy"
  echo ""
  exit 1
fi

if [ -z "$SECRET_KEY" ] && [ "$APP_ENV" = "production" ]; then
  echo "ERROR: SECRET_KEY is required in production."
  exit 1
fi

echo "Database URL: configured"
echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
