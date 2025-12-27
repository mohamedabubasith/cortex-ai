#!/bin/bash

# Exit on error
set -e

echo "🔄 Starting application update..."

# 1. Pull latest changes
echo "📥 Pulling latest code..."
git pull origin main

# 2. Rebuild and restart services (without deleting volumes)
echo "🏗️  Rebuilding and restarting services..."
docker compose -f docker-compose.prod.yml up -d --build

# 3. Run Migrations (just in case)
echo "🔄 Running Database Migrations..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

echo "✅ Update Complete! Services are running with latest code."
