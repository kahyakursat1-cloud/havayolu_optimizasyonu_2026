#!/bin/bash
# Aviation Singularity - Production DB Backup Script

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/aviation_db_$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"

echo "🚀 Starting backup of aviation_db..."

# Extract DB credentials from current environment or use defaults
DB_USER=${POSTGRES_USER:-aviation_user}
DB_NAME=${POSTGRES_DB:-aviation_db}

docker exec aviation-db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup completed: $BACKUP_FILE"
    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
    echo "🧹 Old backups cleaned up."
else
    echo "❌ Backup failed!"
    exit 1
fi
