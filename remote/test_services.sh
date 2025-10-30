#!/bin/bash
# Service Testing Script - Phase 7.1
# Tests all core Julian Assistant Suite services

set -e

LOG_FILE="/var/log/julian_service_test.log"
DATE=$(date +%Y%m%d_%H%M%S)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Service Testing Script - Starting"
log "Date: $DATE"
log "=========================================="

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

test_service() {
    local service_name=$1
    local test_command=$2
    
    log "Testing: $service_name"
    if eval "$test_command" >> "$LOG_FILE" 2>&1; then
        log "✅ PASS: $service_name"
        ((TESTS_PASSED++))
        return 0
    else
        log "❌ FAIL: $service_name"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Test SSH connectivity
log ""
log "[Test 1] SSH Service"
if test_service "SSH" "systemctl is-active --quiet ssh || systemctl is-active --quiet sshd"; then
    log "SSH is running"
else
    log "Warning: SSH service check failed"
fi

# 2. Test nginx
log ""
log "[Test 2] Nginx Web Server"
if test_service "Nginx" "systemctl is-active --quiet nginx && curl -s -o /dev/null -w '%{http_code}' http://localhost | grep -q '200\|301\|302'"; then
    log "Nginx is running and responding"
else
    log "Warning: Nginx may not be running or responding"
fi

# 3. Test SSL/HTTPS
log ""
log "[Test 3] SSL/HTTPS"
if test_service "HTTPS" "curl -s -k -o /dev/null -w '%{http_code}' https://localhost 2>/dev/null | grep -q '[0-9]'"; then
    log "HTTPS endpoint is accessible"
else
    log "Warning: HTTPS test failed (may not be configured)"
fi

# 4. Test Docker
log ""
log "[Test 4] Docker"
if test_service "Docker" "command -v docker && docker ps"; then
    log "Docker is running"
else
    log "Warning: Docker may not be installed or running"
fi

# 5. Test n8n (port 5678)
log ""
log "[Test 5] n8n Workflow Automation"
if test_service "n8n" "curl -s -o /dev/null -w '%{http_code}' http://localhost:5678 | grep -q '[0-9]'"; then
    log "n8n is accessible on port 5678"
else
    log "Warning: n8n may not be running (check: systemctl status n8n)"
fi

# 6. Test Cloud Bridge (port 8000)
log ""
log "[Test 6] Cloud Bridge API"
if test_service "Cloud Bridge" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health | grep -q '200'"; then
    log "Cloud Bridge API is responding"
else
    log "Warning: Cloud Bridge may not be running (check: systemctl status cloud_bridge)"
fi

# 7. Test UFW firewall
log ""
log "[Test 7] UFW Firewall"
if test_service "UFW" "command -v ufw && ufw status | grep -q 'Status:'"; then
    UFW_STATUS=$(ufw status | grep -i "Status:" || echo "unknown")
    log "UFW status: $UFW_STATUS"
else
    log "Warning: UFW may not be installed"
fi

# 8. Test fail2ban
log ""
log "[Test 8] Fail2ban"
if test_service "Fail2ban" "command -v fail2ban-client && systemctl is-active --quiet fail2ban"; then
    log "Fail2ban is running"
else
    log "Warning: Fail2ban may not be installed or running"
fi

# 9. Test Python 3.12
log ""
log "[Test 9] Python 3.12"
if test_service "Python 3.12" "python3.12 --version 2>&1 | grep -q 'Python 3.12'"; then
    PYTHON_VERSION=$(python3.12 --version 2>&1 || echo "not found")
    log "Python version: $PYTHON_VERSION"
else
    log "Warning: Python 3.12 may not be installed"
fi

# 10. Test disk space
log ""
log "[Test 10] Disk Space"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    log "✅ PASS: Disk usage is $DISK_USAGE% (below 90%)"
    ((TESTS_PASSED++))
else
    log "❌ FAIL: Disk usage is $DISK_USAGE% (above 90%)"
    ((TESTS_FAILED++))
fi

# 11. Test memory availability
log ""
log "[Test 11] Memory Availability"
MEM_FREE=$(free | awk 'NR==2 {printf "%.0f", $4/$2 * 100}')
if [ "$MEM_FREE" -gt 10 ]; then
    log "✅ PASS: Free memory is ${MEM_FREE}% (above 10%)"
    ((TESTS_PASSED++))
else
    log "❌ FAIL: Free memory is ${MEM_FREE}% (below 10%)"
    ((TESTS_FAILED++))
fi

# Summary
log ""
log "=========================================="
log "Service Testing Summary"
log "=========================================="
log "Tests Passed: $TESTS_PASSED"
log "Tests Failed: $TESTS_FAILED"
log "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
log "=========================================="

if [ $TESTS_FAILED -eq 0 ]; then
    log "✅ All critical tests passed!"
    exit 0
else
    log "⚠️ Some tests failed. Review log at: $LOG_FILE"
    exit 1
fi




