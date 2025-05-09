#!/bin/bash
set -e

# Stamp the migrations as complete since tables are created
alembic stamp head

# Start the application
python app/main.py
