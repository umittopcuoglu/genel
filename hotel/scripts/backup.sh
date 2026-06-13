#!/usr/bin/env bash
set -euo pipefail

# PostgreSQL backup — 30-day retention
# crontab: 0 2 * * * /opt/hotel/scripts/backup.sh

DB_HOST="${PGHOST:-localhost}"
DB_NAME="${PGDATABASE:-hotelops}"
DB_USER="${PGUSER:-hotelops}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/hotel-backups}"
S3_BUCKET="${S3_BUCKET:-}"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="hotelops_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"
pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$FILENAME"
echo "[$(date)] Backup: $FILENAME ($(du -h "$BACKUP_DIR/$FILENAME" | cut -f1))"

if [ -n "$S3_BUCKET" ]; then
    aws s3 cp "$BACKUP_DIR/$FILENAME" "s3://$S3_BUCKET/backups/$FILENAME"
fi

find "$BACKUP_DIR" -name "hotelops_*.sql.gz" -mtime +$RETENTION_DAYS -delete
