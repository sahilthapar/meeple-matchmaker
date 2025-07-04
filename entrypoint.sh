#!/bin/sh
set -e

echo "Copying latest meeple-matchmaker.db into volume (overwriting any existing file)..."
cp /app/seed/meeple-matchmaker.db /app/database/meeple-matchmaker.db

exec "$@"