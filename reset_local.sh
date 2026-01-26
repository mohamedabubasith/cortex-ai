#!/bin/bash
# Script to reset local database and seed default admin
# Credentials: admin@gmial.com / Apple@123

export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
echo "Starting Local Database Reset..."
python3 backend/reset_db_v2.py
