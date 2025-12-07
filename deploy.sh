#!/bin/bash

# Deployment Script for Cortex AI (v0.0.2)

# Stop on error
set -e

echo "Starting deployment..."

# 1. Pull the latest code and checkout the specific tag
echo "Pulling code..."
git fetch --all --tags
git checkout tags/v0.0.2

# 2. (Optional) Check for .env file if needed
# if [ ! -f .env ]; then
#     echo "Warning: .env file not found. Ensure required env vars are set."
# fi

# 3. Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# 4. Build and start new containers
echo "Building and starting containers..."
docker-compose up --build -d

# 5. Check status
echo "Checking status..."
sleep 5
docker-compose ps

echo "Deployment complete! Access the application at http://localhost:3000 (or your server IP)."
