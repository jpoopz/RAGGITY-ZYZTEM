#!/bin/bash
# Pre-Cleanup Backup Script - Phase 7.1
# Backs up current VPS state before optimization

set -e

BACKUP_DIR="/backups/VPS_PRE_7_1"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="$BACKUP_DIR/pre_cleanup_$DATE"

mkdir -p "$BACKUP_ROOT"

echo "=========================================="
echo "Pre-Cleanup Backup Script"
echo "Date: $DATE"
echo "=========================================="

# 1. System information
echo "[1/10] Backing up system information..."
mkdir -p "$BACKUP_ROOT/system"
uname -a > "$BACKUP_ROOT/system/uname.txt"
cat /etc/os-release > "$BACKUP_ROOT/system/os-release.txt" 2>/dev/null || true

# 2. Service configuration
echo "[2/10] Backing up service configurations..."
mkdir -p "$BACKUP_ROOT/services"
systemctl list-units --type=service --all > "$BACKUP_ROOT/services/all_services.txt" 2>&1
systemctl list-unit-files --type=service > "$BACKUP_ROOT/services/enabled_services.txt" 2>&1

# 3. Package list
echo "[3/10] Backing up package list..."
mkdir -p "$BACKUP_ROOT/packages"
dpkg -l > "$BACKUP_ROOT/packages/installed_packages.txt" 2>&1
apt list --installed > "$BACKUP_ROOT/packages/apt_list.txt" 2>&1 || true

# 4. Network configuration
echo "[4/10] Backing up network configuration..."
mkdir -p "$BACKUP_ROOT/network"
ip addr show > "$BACKUP_ROOT/network/interfaces.txt" 2>&1
iptables-save > "$BACKUP_ROOT/network/iptables.txt" 2>&1 || true
ufw status verbose > "$BACKUP_ROOT/network/ufw_status.txt" 2>&1 || true

# 5. Disk and memory usage
echo "[5/10] Backing up disk and memory info..."
mkdir -p "$BACKUP_ROOT/resources"
df -h > "$BACKUP_ROOT/resources/disk_usage.txt" 2>&1
free -h > "$BACKUP_ROOT/resources/memory_usage.txt" 2>&1

# 6. Nginx configuration (if exists)
echo "[6/10] Backing up nginx configuration..."
if [ -d /etc/nginx ]; then
    mkdir -p "$BACKUP_ROOT/nginx"
    cp -r /etc/nginx "$BACKUP_ROOT/nginx/config" 2>/dev/null || true
fi

# 7. Docker configuration (if exists)
echo "[7/10] Backing up Docker configuration..."
if [ -d /etc/docker ]; then
    mkdir -p "$BACKUP_ROOT/docker"
    cp -r /etc/docker "$BACKUP_ROOT/docker/config" 2>/dev/null || true
    docker ps -a > "$BACKUP_ROOT/docker/containers.txt" 2>&1 || true
fi

# 8. n8n configuration (if exists)
echo "[8/10] Backing up n8n configuration..."
if [ -d ~/.n8n ]; then
    mkdir -p "$BACKUP_ROOT/n8n"
    cp -r ~/.n8n "$BACKUP_ROOT/n8n/config" 2>/dev/null || true
fi

# 9. Systemd service files (critical services)
echo "[9/10] Backing up critical systemd service files..."
mkdir -p "$BACKUP_ROOT/systemd"
SERVICES=("n8n" "nginx" "docker" "ufw" "fail2ban" "cloud_bridge")
for service in "${SERVICES[@]}"; do
    if [ -f "/etc/systemd/system/${service}.service" ]; then
        cp "/etc/systemd/system/${service}.service" "$BACKUP_ROOT/systemd/${service}.service" 2>/dev/null || true
    fi
done

# 10. Cron jobs
echo "[10/10] Backing up cron jobs..."
mkdir -p "$BACKUP_ROOT/cron"
crontab -l > "$BACKUP_ROOT/cron/root_crontab.txt" 2>/dev/null || true
if [ -d /var/spool/cron ]; then
    cp -r /var/spool/cron "$BACKUP_ROOT/cron/spool" 2>/dev/null || true
fi

# Create backup manifest
echo "Creating backup manifest..."
cat > "$BACKUP_ROOT/manifest.txt" << EOF
Julian Assistant Suite - Pre-Cleanup Backup
Date: $DATE
Hostname: $(hostname)
Kernel: $(uname -r)
OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2 || echo "Unknown")

Backup Contents:
- System information
- Service configurations
- Package lists
- Network configuration
- Disk/memory usage
- Nginx configuration (if exists)
- Docker configuration (if exists)
- n8n configuration (if exists)
- Systemd service files
- Cron jobs

Restore Instructions:
1. Review backup manifest and files
2. Use systemd service files to restore services if needed
3. Restore configurations from respective directories
4. Reinstall packages from package lists if needed

EOF

# Create compressed archive
echo ""
echo "Creating compressed archive..."
cd "$BACKUP_DIR"
tar -czf "pre_cleanup_$DATE.tar.gz" "pre_cleanup_$DATE" 2>/dev/null || echo "Warning: Compression failed"
echo ""

echo "=========================================="
echo "Backup Complete!"
echo "Location: $BACKUP_ROOT"
echo "Archive: $BACKUP_DIR/pre_cleanup_$DATE.tar.gz"
echo "=========================================="




