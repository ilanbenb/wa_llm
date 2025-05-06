#!/bin/bash
set -e

# Initialize database tables using the correct path
PYTHONPATH=/app/src python /app/src/init_db.py

# Stamp the migrations as complete since tables are created
alembic stamp head

# Start the application
python app/main.py
