#!/bin/bash

# clean_db.sh - Helper script to clean the database
# Wraps backend/scripts/purge_db.py

# Navigate to backend directory or stay in current if already there
if [ -d "backend" ]; then
    cd backend
fi

# Determine python command
if [ -d ".venv" ]; then
    PYTHON_CMD=".venv/bin/python"
elif [ -d "venv" ]; then
    PYTHON_CMD="venv/bin/python"
elif [ -f "../.venv/bin/python" ]; then
    PYTHON_CMD="../.venv/bin/python"
elif [ -f "../venv/bin/python" ]; then
    PYTHON_CMD="../venv/bin/python"
else
    echo "❌ Could not find virtual environment (.venv or venv)"
    echo "Please ensure you have set up the backend environment."
    exit 1
fi

# Run the purge script
echo "🧹 Running database purge..."
$PYTHON_CMD scripts/purge_db.py "$@"
