#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting app..."
exec python run.py
