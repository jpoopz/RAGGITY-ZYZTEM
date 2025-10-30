#!/bin/bash
# Security Hardening Script - Phase 7.1
# Ensures firewall, fail2ban, and SSL are properly configured

set -e

LOG_FILE="/var/log/julian_security.log"
BACKUP_DIR="/backups/VPS_PRE_7_1"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Security Hardening Script - Starting"
log "=========================================="

# 1. Verify UFW firewall status
log "Step 1: Checking UFW firewall status..."
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | grep -i "Status:" || echo "Status: unknown")
    log "UFW Status: $UFW_STATUS"
    
    if echo "$UFW_STATUS" | grep -qi "inactive"; then
        log "Warning: UFW is inactive. Enabling..."
        ufw --force enable 2>&1 | tee -a "$LOG_FILE" || log "Warning: UFW enable failed"
    fi
    
    # Allow only necessary ports
    log "Configuring allowed ports..."
    ufw allow 22/tcp comment 'SSH' 2>&1 | tee -a "$LOG_FILE" || log "Warning: SSH rule failed"
    ufw allow 80/tcp comment 'HTTP' 2>&1 | tee -a "$LOG_FILE" || log "Warning: HTTP rule failed"
    ufw allow 443/tcp comment 'HTTPS' 2>&1 | tee -a "$LOG_FILE" || log "Warning: HTTPS rule failed"
    ufw allow 5678/tcp comment 'n8n' 2>&1 | tee -a "$LOG_FILE" || log "Warning: n8n rule failed"
    ufw allow 8000/tcp comment 'Cloud Bridge' 2>&1 | tee -a "$LOG_FILE" || log "Warning: Cloud Bridge rule failed"
    
    log "UFW configured with required ports"
else
    log "Warning: UFW not installed. Install with: apt-get install ufw"
fi

# 2. Check fail2ban status
log "Step 2: Checking fail2ban status..."
if command -v fail2ban-client &> /dev/null; then
    FAIL2BAN_STATUS=$(fail2ban-client status 2>&1 || echo "not running")
    log "Fail2ban status: $FAIL2BAN_STATUS"
    
    # Verify fail2ban is running
    if systemctl is-active --quiet fail2ban; then
        log "Fail2ban is running"
    else
        log "Warning: Fail2ban is not running. Starting..."
        systemctl start fail2ban 2>&1 | tee -a "$LOG_FILE" || log "Warning: Fail2ban start failed"
    fi
    
    # Ensure fail2ban is enabled on boot
    systemctl enable fail2ban 2>&1 | tee -a "$LOG_FILE" || log "Warning: Fail2ban enable failed"
else
    log "Warning: Fail2ban not installed. Install with: apt-get install fail2ban"
fi

# 3. Verify SSL certificates
log "Step 3: Checking SSL certificates..."
if command -v certbot &> /dev/null; then
    CERT_COUNT=$(certbot certificates 2>/dev/null | grep -c "Certificate Name:" || echo "0")
    log "Found $CERT_COUNT SSL certificate(s)"
    
    if [ "$CERT_COUNT" -gt 0 ]; then
        # Check certificate expiry
        certbot certificates 2>/dev/null | tee -a "$LOG_FILE" || log "Warning: certbot certificates failed"
        
        # Test renewal
        log "Testing certificate renewal (dry-run)..."
        certbot renew --dry-run 2>&1 | tee -a "$LOG_FILE" || log "Warning: Certificate renewal test failed"
    else
        log "Warning: No SSL certificates found. Configure with: certbot --nginx"
    fi
else
    log "Warning: Certbot not installed. Install with: apt-get install certbot python3-certbot-nginx"
fi

# 4. Check SSH configuration
log "Step 4: Checking SSH configuration..."
SSH_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSH_CONFIG" ]; then
    # Backup SSH config
    cp "$SSH_CONFIG" "$BACKUP_DIR/sshd_config.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # Check if root login is disabled (recommended)
    if grep -q "^PermitRootLogin yes" "$SSH_CONFIG"; then
        log "Warning: Root SSH login is enabled. Consider disabling for security."
        log "To disable: Set PermitRootLogin no in $SSH_CONFIG"
    else
        log "Root SSH login check passed"
    fi
    
    # Check password authentication
    if grep -q "^PasswordAuthentication yes" "$SSH_CONFIG"; then
        log "Password authentication is enabled"
    fi
    
    log "SSH configuration check complete"
else
    log "Warning: SSH config file not found"
fi

# 5. Check listening ports (security audit)
log "Step 5: Auditing listening ports..."
LISTENING_PORTS=$(netstat -tlnp 2>/dev/null | grep LISTEN || ss -tlnp | grep LISTEN)
log "Currently listening ports:"
echo "$LISTENING_PORTS" | tee -a "$LOG_FILE"

# Warn about unexpected ports
EXPECTED_PORTS=(22 80 443 5678 8000)
for port_info in "$LISTENING_PORTS"; do
    port=$(echo "$port_info" | awk '{print $4}' | cut -d':' -f2 | cut -d' ' -f1 || echo "")
    if [ -n "$port" ] && [[ ! " ${EXPECTED_PORTS[@]} " =~ " ${port} " ]]; then
        log "Warning: Unexpected port $port is listening"
    fi
done

# 6. Check for unnecessary services
log "Step 6: Checking for unnecessary services..."
UNNECESSARY_SERVICES=("mysql" "postfix" "apache2" "exim4" "sendmail")
for service in "${UNNECESSARY_SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        log "Warning: Unnecessary service '$service' is running. Consider stopping: systemctl stop $service && systemctl disable $service"
    fi
done

# 7. Summary
log "Step 7: Security hardening summary..."
log "=========================================="
log "Security Status:"
log "UFW: $(ufw status | grep -i 'Status:' || echo 'Not installed')"
log "Fail2ban: $(systemctl is-active fail2ban 2>/dev/null && echo 'Active' || echo 'Inactive/Not installed')"
log "SSL Certificates: $CERT_COUNT found"
log "=========================================="

log "Security hardening check complete!"
log "Review log at: $LOG_FILE"
log "Recommendation: Review warnings and take action if needed"




