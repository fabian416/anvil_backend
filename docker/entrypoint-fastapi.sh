#!/bin/bash
set -e

echo "🚀 Starting FastAPI entrypoint..."

# Wait for Postgres to be ready
echo "⏳ Waiting for Postgres..."
max_attempts=30
attempt=0
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ $attempt -eq $max_attempts ]; then
    echo "❌ Postgres did not become ready in time"
    exit 1
  fi
  echo "   Postgres is unavailable - sleeping (attempt $attempt/$max_attempts)"
  sleep 2
done

echo "✅ Postgres is ready!"

# Run database migrations
echo "📦 Running Alembic migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
  echo "✅ Migrations completed successfully"
else
  echo "❌ Migrations failed"
  exit 1
fi

# Start FastAPI
echo "🎯 Starting Uvicorn..."
exec uvicorn app.run:make_app --factory --host 0.0.0.0 --port 8080 --loop uvloop
