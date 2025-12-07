#!/bin/bash

# Deployment Script for Cortex AI (v0.0.2)

# Stop on error
set -e

# Detect Docker Compose command
if command -v docker-compose > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "Error: Docker Compose not found. Please install it."
    exit 1
fi

echo "Using: $DOCKER_COMPOSE_CMD"

echo "Starting deployment..."

# 1. Pull the latest code and checkout the specific tag
echo "Pulling code..."
git fetch origin --tags --force
git checkout tags/v0.0.2

# 2. (Optional) Check for .env file if needed
# if [ ! -f .env ]; then
#     echo "Warning: .env file not found. Ensure required env vars are set."
# fi

# 3. Stop existing containers
echo "Stopping existing containers..."
$DOCKER_COMPOSE_CMD down

# 4. Build and start new containers
echo "Building and starting containers..."
$DOCKER_COMPOSE_CMD up --build -d

# 5. Check status
echo "Checking status..."
sleep 5
$DOCKER_COMPOSE_CMD ps

echo "Deployment complete! Access the application at http://localhost:3000 (or your server IP)."
