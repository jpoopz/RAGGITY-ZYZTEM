#!/bin/bash
# VPS Audit + Cleanup Script - Phase 7.5
# Audits and cleans Hostinger VPS, keeping only Julian Assistant Suite components

set -e

BACKUP_DIR="/backups"
AUDIT_FILE="$BACKUP_DIR/VPS_AUDIT_7_5.txt"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$AUDIT_FILE"
}

log "=========================================="
log "VPS Audit + Cleanup - Phase 7.5"
log "Date: $(date)"
log "=========================================="
log ""

# 1. System Information
log "[1] System Information"
log "----------------------"
log "Hostname: $(hostname)"
log "Kernel: $(uname -r)"
log "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
log "Uptime: $(uptime -p)"
log ""

# 2. Active Services Audit
log "[2] Active Services Audit"
log "-------------------------"
log "All running services:"
systemctl list-units --type=service --state=running >> "$AUDIT_FILE" 2>&1
log ""

# 3. Enabled Services Audit
log "[3] Enabled Services (Auto-start)"
log "---------------------------------"
log "Services set to start on boot:"
systemctl list-unit-files --type=service --state=enabled >> "$AUDIT_FILE" 2>&1
log ""

# 4. Docker Containers Audit
log "[4] Docker Containers Audit"
log "---------------------------"
if command -v docker &> /dev/null; then
    log "Docker version: $(docker --version)"
    log ""
    log "Running containers:"
    docker ps >> "$AUDIT_FILE" 2>&1
    log ""
    log "All containers (including stopped):"
    docker ps -a >> "$AUDIT_FILE" 2>&1
else
    log "Docker not installed"
fi
log ""

# 5. Listening Ports Audit
log "[5] Listening Ports Audit"
log "-------------------------"
log "Ports currently listening:"
netstat -tlnp 2>/dev/null | grep LISTEN >> "$AUDIT_FILE" || ss -tlnp >> "$AUDIT_FILE" 2>&1
log ""

# 6. Process Audit
log "[6] Running Processes Audit"
log "--------------------------"
log "Top processes by CPU:"
ps aux --sort=-%cpu | head -20 >> "$AUDIT_FILE" 2>&1
log ""
log "Top processes by memory:"
ps aux --sort=-%mem | head -20 >> "$AUDIT_FILE" 2>&1
log ""

# 7. Disk Usage
log "[7] Disk Usage"
log "-------------"
df -h >> "$AUDIT_FILE" 2>&1
log ""

# 8. Memory Usage
log "[8] Memory Usage"
log "---------------"
free -h >> "$AUDIT_FILE" 2>&1
log ""

# 9. Required Services Check
log "[9] Required Services Status"
log "---------------------------"
REQUIRED_SERVICES=("n8n" "docker" "nginx" "fail2ban" "ufw")
for service in "${REQUIRED_SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "$service"; then
        STATUS=$(systemctl is-active "$service" 2>/dev/null || echo "not-found")
        log "  $service: $STATUS"
    else
        log "  $service: not installed"
    fi
done
log ""

# 10. Julian Assistant Suite Components Check
log "[10] Julian Assistant Suite Components"
log "--------------------------------------"
log "Checking for Julian Suite components..."

# Check for Cloud Bridge
if systemctl list-unit-files | grep -q "cloud_bridge"; then
    log "  Cloud Bridge: found"
elif docker ps -a | grep -q "cloud_bridge"; then
    log "  Cloud Bridge: found (Docker)"
else
    log "  Cloud Bridge: not found"
fi

# Check for Ollama
if command -v ollama &> /dev/null; then
    log "  Ollama: installed"
elif docker ps -a | grep -q "ollama"; then
    log "  Ollama: found (Docker)"
else
    log "  Ollama: not found"
fi

# Check for n8n
if systemctl list-unit-files | grep -q "n8n"; then
    log "  n8n: found (systemd)"
elif docker ps -a | grep -q "n8n"; then
    log "  n8n: found (Docker)"
else
    log "  n8n: not found"
fi
log ""

# 11. Unnecessary Services Identification
log "[11] Unnecessary Services (to potentially remove)"
log "------------------------------------------------"
UNNECESSARY=("mysql" "mariadb" "postfix" "exim4" "sendmail" "apache2" "httpd" "tomcat" "cassandra" "mongodb")
log "Checking for unnecessary services:"
for service in "${UNNECESSARY[@]}"; do
    if systemctl list-unit-files | grep -q "$service"; then
        STATUS=$(systemctl is-active "$service" 2>/dev/null || echo "stopped")
        log "  $service: found (status: $STATUS) - CONSIDER REMOVAL"
    fi
done
log ""

# 12. Cleanup Recommendation
log "[12] Cleanup Recommendations"
log "----------------------------"
log "Services to disable/remove:"
log "  - Review section [11] above"
log "  - Disable: systemctl disable [service]"
log "  - Stop: systemctl stop [service]"
log "  - Remove: apt-get remove --purge [service]"
log ""
log "Docker cleanup:"
log "  - Remove unused: docker system prune -a"
log "  - Remove stopped containers: docker container prune"
log ""
log "Package cleanup:"
log "  - Remove unused: apt-get autoremove --purge"
log "  - Clean cache: apt-get clean"
log ""

# 13. Summary
log "=========================================="
log "Audit Summary"
log "=========================================="
log "Total running services: $(systemctl list-units --type=service --state=running | wc -l)"
log "Total enabled services: $(systemctl list-unit-files --type=service --state=enabled | wc -l)"
log "Docker containers: $(docker ps -q | wc -l 2>/dev/null || echo '0')"
log "Disk usage: $(df -h / | awk 'NR==2 {print $5}')"
log "Memory usage: $(free | awk 'NR==2 {printf "%.1f%%", $3/$2*100}')"
log "=========================================="
log ""
log "Audit complete! Results saved to: $AUDIT_FILE"
log "Review the file and proceed with cleanup if needed."




