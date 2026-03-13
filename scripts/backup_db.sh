#!/bin/bash
# Description: Automated PostgreSQL backup script for Docker setup.
# Usage: ./scripts/backup_db.sh

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER_NAME=$(docker-compose ps -q db)
BACKUP_FILENAME="db_backup_${TIMESTAMP}.sql"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Starting backup of database to ${BACKUP_DIR}/${BACKUP_FILENAME}..."

# Perform backup using pg_dump
# Note: We use 'db' if the container is running via docker-compose
docker-compose exec -T db pg_dump -U postgres korean_app > "${BACKUP_DIR}/${BACKUP_FILENAME}"

if [ $? -eq 0 ]; then
    echo "Backup successful!"
    # Optional: Keep only last 7 days of backups
    find "$BACKUP_DIR" -type f -name "*.sql" -mtime +7 -delete
    echo "Old backups cleaned up (older than 7 days)."
else
    echo "Backup failed!"
    exit 1
fi
