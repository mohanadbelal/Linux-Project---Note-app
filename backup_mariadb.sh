#!/bin/bash
# =============================================================================
# MariaDB Backup Script
# Dumps the notesdb database to the backup EBS volume mounted at /mnt/backup
# =============================================================================

set -euo pipefail

# --- Configuration ---
DB_USER="noteuser"
DB_PASS="notepassword"
DB_NAME="notesdb"
BACKUP_DIR="/mnt/backup/mariadb"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${TIMESTAMP}.sql.gz"

# --- Ensure backup directory exists ---
mkdir -p "${BACKUP_DIR}"

# --- Perform the backup ---
echo "[$(date)] Starting backup of '${DB_NAME}'..."
mysqldump -u "${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"
echo "[$(date)] Backup saved to: ${BACKUP_FILE}"

# --- Verify the backup file is non-empty ---
if [ -s "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date)] Backup successful (${SIZE})."
else
    echo "[$(date)] ERROR: Backup file is empty!" >&2
    exit 1
fi

# --- Remove backups older than retention period ---
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Cleanup complete."

# --- List remaining backups ---
echo ""
echo "Current backups on volume:"
ls -lh "${BACKUP_DIR}"
