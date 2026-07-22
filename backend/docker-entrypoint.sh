#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding admin user (if not exists)..."
python -m app.modules.auth.seed

echo "Starting server..."
exec "$@"
