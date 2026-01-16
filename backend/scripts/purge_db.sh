#!/bin/bash

# Database Purge Script - Drops and recreates the database

set -e

echo "============================================================"
echo "DATABASE PURGE - WARNING"
echo "============================================================"
echo "This will DELETE ALL DATA in the database!"
echo ""
read -p "Are you sure? Type 'yes' to continue: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Purging database..."

# Get database name from .env or use default
DB_NAME=${DATABASE_NAME:-cortex_ai}
DB_USER=${DATABASE_USER:-abu}

echo "Database: $DB_NAME"

# Drop database
echo "Dropping database..."
dropdb $DB_NAME 2>/dev/null || echo "Database didn't exist"

# Create database
echo "Creating fresh database..."
createdb $DB_NAME

# Enable pgvector extension
echo "Enabling pgvector extension..."
psql $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
echo "Running migrations..."
cd "$(dirname "$0")/.."
alembic upgrade head

echo ""
echo "============================================================"
echo "✅ DATABASE PURGED SUCCESSFULLY"
echo "============================================================"
echo "Database: $DB_NAME"
echo "Status: Fresh and empty"
echo ""
echo "Next steps:"
echo "1. Restart backend: lsof -ti:8000 | xargs kill -9 && .venv/bin/uvicorn app.main:app --reload"
echo "2. Create admin user: .venv/bin/python -m scripts.create_admin"
echo "============================================================"
