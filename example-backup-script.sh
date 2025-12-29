#!/bin/bash
#
# Example backup script using pve-backup-by-tag
# This demonstrates how to set up automated backups in production
#

# Configuration
SCRIPT_DIR="/opt/pve-backup-by-tag"
LOG_DIR="/var/log/pve-backup"
DATE=$(date +%Y%m%d-%H%M%S)

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Example 1: Backup production VMs
echo "Starting production backup..."
python3 "${SCRIPT_DIR}/pve-backup-by-tag.py" \
    --config "${SCRIPT_DIR}/config.yaml" \
    --tag production \
    --storage backup_storage \
    --order size \
    --log-file "${LOG_DIR}/production-${DATE}.log" \
    --log-level INFO

# Example 2: Backup database servers with exclude tag
echo "Starting database backup..."
python3 "${SCRIPT_DIR}/pve-backup-by-tag.py" \
    --config "${SCRIPT_DIR}/config.yaml" \
    --tag database \
    --exclude-tag maintenance \
    --storage db_backup_storage \
    --mode suspend \
    --log-file "${LOG_DIR}/database-${DATE}.log"

# Example 3: List all tags (useful for verification)
echo "Listing all available tags..."
python3 "${SCRIPT_DIR}/pve-backup-by-tag.py" \
    --config "${SCRIPT_DIR}/config.yaml" \
    --get-tags

echo "Backup operations completed."
