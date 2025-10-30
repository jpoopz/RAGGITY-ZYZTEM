#!/bin/bash
# n8n Installation and Setup Script - Phase 7.5

set -e

LOG_FILE="/var/log/julian_n8n_setup.log"
N8N_DIR="$HOME/.n8n"
SYSTEMD_DIR="/etc/systemd/system"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "n8n Installation and Setup - Phase 7.5"
log "=========================================="

# 1. Check if n8n is already installed
log "Step 1: Checking for existing n8n installation..."

if systemctl is-active --quiet n8n 2>/dev/null; then
    log "n8n systemd service is already running"
    exit 0
elif docker ps -a | grep -q n8n; then
    log "n8n Docker container found"
    if docker ps | grep -q n8n; then
        log "n8n container is running"
        exit 0
    else
        log "Starting existing n8n container..."
        docker start $(docker ps -a | grep n8n | awk '{print $1}')
        exit 0
    fi
fi

# 2. Check for Docker
log "Step 2: Checking for Docker..."
if ! command -v docker &> /dev/null; then
    log "Docker not found. Installing Docker..."
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl start docker
    systemctl enable docker
    log "Docker installed and started"
else
    log "Docker is installed: $(docker --version)"
fi

# 3. Create n8n data directory
log "Step 3: Creating n8n data directory..."
mkdir -p "$N8N_DIR"
chmod 755 "$N8N_DIR"

# 4. Run n8n Docker container
log "Step 4: Starting n8n Docker container..."
docker run -d \
    --name n8n \
    --restart always \
    -p 5678:5678 \
    -v "$N8N_DIR:/home/node/.n8n" \
    -e N8N_BASIC_AUTH_ACTIVE=true \
    -e N8N_BASIC_AUTH_USER=admin \
    -e N8N_BASIC_AUTH_PASSWORD=$(openssl rand -base64 12) \
    n8nio/n8n

log "n8n container started"
sleep 5

# 5. Verify n8n is running
log "Step 5: Verifying n8n is running..."
if docker ps | grep -q n8n; then
    log "✅ n8n container is running"
else
    log "❌ Error: n8n container failed to start"
    docker logs n8n
    exit 1
fi

# 6. Create systemd service (optional, for easier management)
log "Step 6: Creating systemd service for n8n..."
cat > "$SYSTEMD_DIR/n8n.service" << 'EOF'
[Unit]
Description=n8n workflow automation
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker start n8n
ExecStop=/usr/bin/docker stop n8n
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable n8n
log "n8n systemd service created and enabled"

# 7. Configure firewall
log "Step 7: Configuring firewall..."
if command -v ufw &> /dev/null; then
    # Get user's local IP (if provided as argument)
    LOCAL_IP="${1:-any}"
    
    if [ "$LOCAL_IP" != "any" ]; then
        ufw allow from "$LOCAL_IP" to any port 5678 comment 'n8n from local IP'
        log "UFW rule added for IP: $LOCAL_IP"
    else
        # Allow from anywhere (less secure, but configurable)
        ufw allow 5678/tcp comment 'n8n workflow automation'
        log "UFW rule added for port 5678 (all IPs)"
    fi
    
    ufw reload
    log "Firewall configured"
else
    log "UFW not found, skipping firewall configuration"
fi

# 8. Get n8n access info
log "Step 8: Retrieving n8n access information..."
N8N_IP=$(hostname -I | awk '{print $1}')
CONTAINER_ID=$(docker ps | grep n8n | awk '{print $1}')
N8N_PASSWORD=$(docker exec "$CONTAINER_ID" env | grep N8N_BASIC_AUTH_PASSWORD | cut -d'=' -f2)

log ""
log "=========================================="
log "n8n Setup Complete!"
log "=========================================="
log "Access n8n at: http://$N8N_IP:5678"
log "Username: admin"
log "Password: $N8N_PASSWORD"
log ""
log "Save these credentials in config/n8n_config.json"
log "=========================================="

# 9. Test n8n endpoint
log "Step 9: Testing n8n endpoint..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5678 | grep -q "[23]"; then
    log "✅ n8n endpoint is responding"
else
    log "⚠️ Warning: n8n endpoint may not be ready yet. Wait a few seconds and check."
fi

log ""
log "Setup complete! Log saved to: $LOG_FILE"
log "Next: Configure n8n webhooks and create workflows"




