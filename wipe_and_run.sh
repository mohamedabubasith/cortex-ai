#!/bin/bash

# Exit on error
set -e

echo "🧹 Starting full clean deployment..."

# 1. Stop containers and remove volumes, networks, and images
echo "🗑️  Removing containers, volumes, and images..."
docker compose -f docker-compose.prod.yml down -v --rmi all --remove-orphans

# 2. Build and start Database first
echo "🏗️  Building and starting Database..."
docker compose -f docker-compose.prod.yml build --no-cache db
docker compose -f docker-compose.prod.yml up -d db

# 3. Wait for Database to be ready
echo "⏳ Waiting for Database to be healthy..."
# Loop until the db container is healthy
MAX_RETRIES=60 # 2 minutes total (60 * 2s)
count=0
until [ "`docker inspect -f {{.State.Health.Status}} chatbot_db`" = "healthy" ]; do
    sleep 2;
    echo -n "."
    count=$((count+1))
    if [ $count -ge $MAX_RETRIES ]; then
        echo ""
        echo "❌ Timeout waiting for database to be healthy."
        echo "   Checking logs for chatbot_db:"
        docker logs --tail 50 chatbot_db
        exit 1
    fi
done
echo "✅ Database is ready!"

# 3.1 Ensure chat_db exists (Robustness fallback)
echo "🛠️  Verifying database 'chat_db' exists..."
if docker exec chatbot_db psql -U admin -lqt | cut -d \| -f 1 | grep -qw chat_db; then
    echo "   - Database 'chat_db' already exists."
else
    echo "   - Database 'chat_db' not found. Creating it..."
    docker exec chatbot_db createdb -U admin chat_db
    echo "   - Database 'chat_db' created."
fi

# 4. Build and start Backend, Frontend, and Nginx
echo "🚀 Building Backend (with fresh dependencies)..."
docker compose -f docker-compose.prod.yml build --no-cache backend
echo "🚀 Starting Backend, Frontend, and Nginx services..."
docker compose -f docker-compose.prod.yml up -d backend frontend nginx

# 5. Run Migrations
./migrate.sh

# 6. Create Admin User (must run after migrations)
echo "👤 Creating Default Admin User..."
docker exec chatbot_backend python -m app.core.startup

echo "🚀 Deployment Complete! Services are running."
echo "   - App DB: chat_db (Managed by Alembic)"
echo "   - Cognee DB: cognee_db (Managed by Cognee)"
