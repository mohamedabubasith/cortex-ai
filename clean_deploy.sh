#!/bin/bash

# Exit on error
set -e

echo "🧹 Starting full clean deployment..."

# 1. Stop containers and remove volumes, networks, and images
echo "🗑️  Removing containers, volumes, and images..."
docker-compose -f docker-compose.prod.yml down -v --rmi all --remove-orphans

# 2. Build and start containers
echo "🏗️  Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Wait for Database to be ready
echo "⏳ Waiting for Database to be healthy..."
# Loop until the db container is healthy
until [ "`docker inspect -f {{.State.Health.Status}} chatbot_db`" == "healthy" ]; do
    sleep 2;
    echo -n "."
done
echo "✅ Database is ready!"

# 4. Run Migrations
echo "🔄 Running Database Migrations..."
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

echo "🚀 Deployment Complete! Services are running."
echo "   - App DB: chat_db (Managed by Alembic)"
echo "   - Cognee DB: cognee_db (Managed by Cognee)"
