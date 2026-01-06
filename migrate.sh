#!/bin/bash

# Exit on error
set -e

echo "🔄 Running Database Migrations..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
echo "✅ Migrations applied successfully."
