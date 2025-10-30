#!/bin/bash
# VPS Cleanup Script - Phase 7.1
# Safe cleanup of temporary files, caches, and old logs

set -e

BACKUP_DIR="/backups/VPS_PRE_7_1"
LOG_FILE="/var/log/julian_cleanup.log"
DATE=$(date +%Y%m%d_%H%M%S)

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "VPS Cleanup Script - Starting"
log "Date: $DATE"
log "=========================================="

# 1. Backup current state
log "Step 1: Creating backup snapshot..."
mkdir -p "$BACKUP_DIR/pre_cleanup_$DATE"
systemctl list-units --type=service > "$BACKUP_DIR/pre_cleanup_$DATE/services.txt" 2>&1 || true
dpkg -l > "$BACKUP_DIR/pre_cleanup_$DATE/packages.txt" 2>&1 || true
df -h > "$BACKUP_DIR/pre_cleanup_$DATE/disk_usage.txt" 2>&1 || true
log "Backup created at $BACKUP_DIR/pre_cleanup_$DATE"

# 2. Clean apt cache (safe)
log "Step 2: Cleaning apt cache..."
apt-get clean 2>&1 | tee -a "$LOG_FILE" || log "Warning: apt clean failed"

# 3. Remove unused packages
log "Step 3: Removing unused packages..."
apt-get autoremove -y 2>&1 | tee -a "$LOG_FILE" || log "Warning: autoremove failed"
apt-get autoclean -y 2>&1 | tee -a "$LOG_FILE" || log "Warning: autoclean failed"

# 4. Clean pip cache (if exists)
log "Step 4: Cleaning pip cache..."
if command -v pip3 &> /dev/null; then
    pip3 cache purge 2>&1 | tee -a "$LOG_FILE" || log "Warning: pip cache purge failed"
fi

# 5. Clean temporary files (older than 7 days)
log "Step 5: Cleaning temporary files (older than 7 days)..."
find /tmp -type f -atime +7 -delete 2>&1 | tee -a "$LOG_FILE" || log "Warning: temp file cleanup failed"
find /var/tmp -type f -atime +7 -delete 2>&1 | tee -a "$LOG_FILE" || log "Warning: var/tmp cleanup failed"

# 6. Rotate and compress old logs (keep last 30 days)
log "Step 6: Rotating logs..."
journalctl --vacuum-time=30d 2>&1 | tee -a "$LOG_FILE" || log "Warning: journalctl vacuum failed"

# 7. Clean old log files in /var/log
log "Step 7: Cleaning old log files..."
find /var/log -name "*.log" -type f -mtime +30 -exec gzip {} \; 2>&1 | tee -a "$LOG_FILE" || log "Warning: log compression failed"
find /var/log -name "*.gz" -type f -mtime +60 -delete 2>&1 | tee -a "$LOG_FILE" || log "Warning: old compressed log cleanup failed"

# 8. Clean Docker (if unused)
log "Step 8: Cleaning Docker unused resources..."
if command -v docker &> /dev/null; then
    docker system prune -f 2>&1 | tee -a "$LOG_FILE" || log "Warning: docker prune failed"
fi

# 9. Clean Python cache files
log "Step 9: Cleaning Python cache files..."
find /home -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /opt -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /home -type d -name "*.pyc" -exec rm -rf {} + 2>/dev/null || true

# 10. Report disk space saved
log "Step 10: Calculating disk space..."
DISK_BEFORE=$(df -h / | awk 'NR==2 {print $4}')
log "Disk space before: $DISK_BEFORE"
log "Cleanup complete. Check disk usage: df -h"

log "=========================================="
log "VPS Cleanup Script - Complete"
log "Log saved to: $LOG_FILE"
log "=========================================="

echo ""
echo "Cleanup complete! Review log at: $LOG_FILE"




