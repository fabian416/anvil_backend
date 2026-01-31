#!/bin/bash
set -e

echo "🔧 Running migrations locally (no Docker build needed)..."

# Load environment from .env file if exists
if [ -f ".env" ]; then
    echo "📋 Loading .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Replace 'postgres' hostname with 'localhost' for local execution
if [ ! -z "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's/@postgres:/@localhost:/g')
    echo "🔄 Adjusted DATABASE_URL for local: $DATABASE_URL"
fi

# Check if virtual env is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "   Run: source env/bin/activate"
    exit 1
fi

# Check if Postgres is accessible
echo "⏳ Checking Postgres connection..."
if ! python -c "import psycopg; psycopg.connect('$DATABASE_URL').close()" 2>/dev/null; then
    echo "❌ Cannot connect to Postgres"
    echo "   DATABASE_URL: $DATABASE_URL"
    echo ""
    echo "   Make sure docker-compose postgres is running:"
    echo "   docker compose up -d postgres"
    exit 1
fi

echo "✅ Postgres is accessible!"
echo ""
echo "📦 Running Alembic migrations..."
cd src/app/infrastructure/persistence_sqla
alembic upgrade head

echo ""
echo "✅ Migrations completed successfully!"
echo ""
echo "💡 To rollback one migration: alembic downgrade -1"
echo "💡 To see current version: alembic current"
echo "💡 To see history: alembic history"
