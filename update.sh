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
# 3. Run Migrations (just in case)
./migrate.sh

# 4. Create Admin User (idempotent, ensures it exists)
echo "👤 Ensuring Default Admin User exists..."
docker exec chatbot_backend python -m app.core.startup

# 5. Seed RBAC Permissions (System Roles & Permissions)
echo "🛡️  Seeding RBAC Permissions..."
docker exec chatbot_backend python -m scripts.seed_rbac

echo "✅ Update Complete! Services are running with latest code."
