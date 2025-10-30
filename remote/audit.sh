#!/bin/bash
# VPS Audit Script - Phase 7.1
# System health check, disk usage, and service summary

set -e

REPORT_DIR="/backups/VPS_PRE_7_1/audit_reports"
DATE=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/audit_$DATE.txt"

mkdir -p "$REPORT_DIR"

echo "==========================================" > "$REPORT_FILE"
echo "VPS System Audit Report" >> "$REPORT_FILE"
echo "Date: $(date)" >> "$REPORT_FILE"
echo "==========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. System Information
echo "[1] System Information" >> "$REPORT_FILE"
echo "----------------------" >> "$REPORT_FILE"
uname -a >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 2. Disk Usage
echo "[2] Disk Usage" >> "$REPORT_FILE"
echo "---------------" >> "$REPORT_FILE"
df -h >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 3. Memory Usage
echo "[3] Memory Usage" >> "$REPORT_FILE"
echo "----------------" >> "$REPORT_FILE"
free -h >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 4. Running Services
echo "[4] Active Systemd Services" >> "$REPORT_FILE"
echo "---------------------------" >> "$REPORT_FILE"
systemctl list-units --type=service --state=running >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 5. Enabled Services
echo "[5] Enabled Services (Auto-start)" >> "$REPORT_FILE"
echo "----------------------------------" >> "$REPORT_FILE"
systemctl list-unit-files --type=service --state=enabled >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 6. Docker Containers
echo "[6] Docker Containers" >> "$REPORT_FILE"
echo "--------------------" >> "$REPORT_FILE"
if command -v docker &> /dev/null; then
    docker ps -a >> "$REPORT_FILE" 2>&1
else
    echo "Docker not installed" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 7. Listening Ports
echo "[7] Listening Ports" >> "$REPORT_FILE"
echo "-------------------" >> "$REPORT_FILE"
netstat -tlnp 2>/dev/null | grep LISTEN >> "$REPORT_FILE" || ss -tlnp >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 8. Installed Packages Count
echo "[8] Installed Package Count" >> "$REPORT_FILE"
echo "---------------------------" >> "$REPORT_FILE"
dpkg -l | wc -l >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 9. Python Version
echo "[9] Python Version" >> "$REPORT_FILE"
echo "-----------------" >> "$REPORT_FILE"
python3 --version >> "$REPORT_FILE" 2>&1 || echo "Python3 not found" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 10. Uptime
echo "[10] System Uptime" >> "$REPORT_FILE"
echo "-----------------" >> "$REPORT_FILE"
uptime >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 11. Load Average
echo "[11] Load Average" >> "$REPORT_FILE"
echo "-----------------" >> "$REPORT_FILE"
cat /proc/loadavg >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 12. Top Processes (CPU)
echo "[12] Top 10 Processes by CPU" >> "$REPORT_FILE"
echo "---------------------------" >> "$REPORT_FILE"
ps aux --sort=-%cpu | head -11 >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 13. Top Processes (Memory)
echo "[13] Top 10 Processes by Memory" >> "$REPORT_FILE"
echo "-------------------------------" >> "$REPORT_FILE"
ps aux --sort=-%mem | head -11 >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 14. Disk I/O
echo "[14] Disk I/O Statistics" >> "$REPORT_FILE"
echo "-----------------------" >> "$REPORT_FILE"
iostat -x 1 1 2>/dev/null >> "$REPORT_FILE" || echo "iostat not available" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 15. Network Interfaces
echo "[15] Network Interfaces" >> "$REPORT_FILE"
echo "----------------------" >> "$REPORT_FILE"
ip addr show >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# Summary
echo "==========================================" >> "$REPORT_FILE"
echo "Audit Summary" >> "$REPORT_FILE"
echo "==========================================" >> "$REPORT_FILE"
echo "Report generated: $REPORT_FILE" >> "$REPORT_FILE"
echo "Disk Usage: $(df -h / | awk 'NR==2 {print $5 " used (" $4 " free)"}')" >> "$REPORT_FILE"
echo "Memory Usage: $(free -h | awk 'NR==2 {print $3 "/" $2 " used (" $4 " free)"}')" >> "$REPORT_FILE"
echo "Active Services: $(systemctl list-units --type=service --state=running | wc -l)" >> "$REPORT_FILE"
echo "==========================================" >> "$REPORT_FILE"

echo ""
echo "Audit complete! Report saved to: $REPORT_FILE"
cat "$REPORT_FILE"




