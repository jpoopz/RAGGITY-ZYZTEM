#!/bin/bash
# VPS Optimization Script - Phase 7.1
# Auto-tune memory and CPU limits for Julian Assistant Suite

set -e

BACKUP_DIR="/backups/VPS_PRE_7_1"
LOG_FILE="/var/log/julian_optimize.log"
DATE=$(date +%Y%m%d_%H%M%S)

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "VPS Optimization Script - Starting"
log "Date: $DATE"
log "=========================================="

# 1. Backup current sysctl settings
log "Step 1: Backing up current sysctl settings..."
cp /etc/sysctl.conf "$BACKUP_DIR/sysctl.conf.$DATE" 2>/dev/null || log "Warning: sysctl.conf backup failed"

# 2. Optimize swap usage (swappiness)
log "Step 2: Optimizing swap usage..."
CURRENT_SWAPPINESS=$(cat /proc/sys/vm/swappiness 2>/dev/null || echo "60")
log "Current swappiness: $CURRENT_SWAPPINESS"

# Set swappiness to 10 (reduce swap usage, prefer RAM)
if [ "$CURRENT_SWAPPINESS" -gt 10 ]; then
    echo "vm.swappiness=10" >> /etc/sysctl.conf
    sysctl -w vm.swappiness=10
    log "Swappiness set to 10"
else
    log "Swappiness already optimized ($CURRENT_SWAPPINESS)"
fi

# 3. Optimize file handle limits
log "Step 3: Optimizing file handle limits..."
if ! grep -q "fs.file-max = 2097152" /etc/sysctl.conf; then
    echo "fs.file-max = 2097152" >> /etc/sysctl.conf
    sysctl -w fs.file-max=2097152
    log "File handle limit increased"
fi

# 4. Optimize TCP settings for better network performance
log "Step 4: Optimizing TCP settings..."
if ! grep -q "# Julian Assistant Suite TCP optimizations" /etc/sysctl.conf; then
    cat >> /etc/sysctl.conf << EOF

# Julian Assistant Suite TCP optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_syn_backlog = 8192
EOF
    sysctl -p
    log "TCP settings optimized"
fi

# 5. Optimize I/O scheduler (if SSD detected)
log "Step 5: Checking disk type and optimizing I/O..."
if [ -e /sys/block/sda/queue/scheduler ]; then
    CURRENT_SCHEDULER=$(cat /sys/block/sda/queue/scheduler | grep -o '\[.*\]' | tr -d '[]')
    log "Current I/O scheduler: $CURRENT_SCHEDULER"
    
    # For SSDs, use noop or none scheduler
    if grep -q "nvme\|ssd" /proc/mounts 2>/dev/null || [ -d /sys/block/nvme0n1 ]; then
        if [ "$CURRENT_SCHEDULER" != "none" ] && [ "$CURRENT_SCHEDULER" != "noop" ]; then
            echo none > /sys/block/sda/queue/scheduler 2>/dev/null || log "Warning: Could not change scheduler"
            log "I/O scheduler set to none (SSD detected)"
        fi
    fi
fi

# 6. Set CPU governor to performance (if available)
log "Step 6: Checking CPU governor..."
if command -v cpupower &> /dev/null; then
    cpupower frequency-set -g performance 2>&1 | tee -a "$LOG_FILE" || log "Warning: CPU governor change failed"
    log "CPU governor set to performance"
elif [ -d /sys/devices/system/cpu/cpu0/cpufreq ]; then
    CURRENT_GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "unknown")
    log "Current CPU governor: $CURRENT_GOV"
fi

# 7. Optimize memory limits for Docker (if Docker is running)
log "Step 7: Optimizing Docker memory limits..."
if command -v docker &> /dev/null; then
    # Check if docker-compose or docker has memory limits set
    log "Docker detected. Review docker-compose.yml for memory limits."
    log "Recommended: Set memory limits per service in docker-compose.yml"
fi

# 8. Optimize nginx worker processes
log "Step 8: Optimizing nginx configuration..."
if command -v nginx &> /dev/null; then
    CPU_COUNT=$(nproc)
    NGINX_CONF="/etc/nginx/nginx.conf"
    
    if [ -f "$NGINX_CONF" ] && [ ! -f "$BACKUP_DIR/nginx.conf.$DATE" ]; then
        cp "$NGINX_CONF" "$BACKUP_DIR/nginx.conf.$DATE"
        
        # Update worker_processes if needed
        if grep -q "worker_processes auto" "$NGINX_CONF"; then
            log "Nginx worker_processes already optimized"
        else
            sed -i 's/worker_processes.*/worker_processes auto;/' "$NGINX_CONF" 2>/dev/null || log "Warning: nginx config update failed"
            log "Nginx worker_processes optimized"
        fi
    fi
fi

# 9. Apply all sysctl changes
log "Step 9: Applying all sysctl changes..."
sysctl -p >> "$LOG_FILE" 2>&1 || log "Warning: sysctl -p failed"

# 10. Summary
log "Step 10: Optimization summary..."
log "Current swappiness: $(cat /proc/sys/vm/swappiness)"
log "File handle limit: $(cat /proc/sys/fs/file-max)"
log "CPU cores: $(nproc)"
log "Total memory: $(free -h | awk 'NR==2{print $2}')"

log "=========================================="
log "VPS Optimization Script - Complete"
log "Log saved to: $LOG_FILE"
log "Review changes before next reboot"
log "=========================================="

echo ""
echo "Optimization complete! Review log at: $LOG_FILE"
echo "Recommendation: Test system stability before rebooting"




