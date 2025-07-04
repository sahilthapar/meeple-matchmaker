#!/bin/sh
#
# Manual copy commands for the SQLite database:
#
# Copy the latest database from host to the running container (overwrite):
# docker cp ./database/meeple-matchmaker.db <container_name>:/app/database/meeple-matchmaker.db
#
# Copy the database from the running container to the host (backup):
# docker cp <container_name>:/app/database/meeple-matchmaker.db ./backups/meeple-matchmaker-backup-$(date +%Y%m%d-%H%M%S).db
#
# Copy the database directly between the Docker volume and the host using a temporary container:
# docker run --rm -v meeple-matchmaker_sqlite-data:/data -v $(pwd)/backups:/backup busybox cp /data/meeple-matchmaker.db /backup/meeple-matchmaker-backup-$(date +%Y%m%d-%H%M%S).db
#
set -e

# Seed the database if it does not exist in the volume
if [ ! -f /app/database/meeple-matchmaker.db ]; then
  echo "Seeding meeple-matchmaker.db into volume..."
  cp /app/seed/meeple-matchmaker.db /app/database/meeple-matchmaker.db
fi

exec "$@"