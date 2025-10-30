#!/bin/bash
# Cloud Bridge Server Deployment Script for Hostinger VPS (Ubuntu 25.04)

set -e

echo "=========================================="
echo "Julian Assistant Cloud Bridge Deployment"
echo "=========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python: $PYTHON_VERSION"

# Create directory structure
ASSISTANT_DIR="$HOME/assistant"
mkdir -p "$ASSISTANT_DIR"
mkdir -p "$ASSISTANT_DIR/context_storage"
mkdir -p "$ASSISTANT_DIR/backups"
mkdir -p "$ASSISTANT_DIR/keys"

echo "✅ Created directories:"
echo "   - $ASSISTANT_DIR"
echo "   - $ASSISTANT_DIR/context_storage"
echo "   - $ASSISTANT_DIR/backups"
echo "   - $ASSISTANT_DIR/keys"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install --user fastapi uvicorn cryptography python-multipart

# Copy server file
if [ -f "cloud_bridge_server.py" ]; then
    cp cloud_bridge_server.py "$ASSISTANT_DIR/"
    echo "✅ Copied cloud_bridge_server.py"
else
    echo "⚠️  cloud_bridge_server.py not found in current directory"
fi

# Setup systemd service
SERVICE_FILE="/etc/systemd/system/julian-cloud-bridge.service"
if [ -w "$SERVICE_FILE" ] || [ "$EUID" -eq 0 ]; then
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Julian Assistant Cloud Bridge Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$ASSISTANT_DIR
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="VPS_AUTH_TOKEN=\$(cat $ASSISTANT_DIR/.auth_token 2>/dev/null || echo '')"
Environment="VPS_HOST=0.0.0.0"
Environment="VPS_PORT=8000"
ExecStart=/usr/bin/python3 $ASSISTANT_DIR/cloud_bridge_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo "✅ Created systemd service file"
    echo ""
    echo "To enable and start service (requires sudo):"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable julian-cloud-bridge"
    echo "  sudo systemctl start julian-cloud-bridge"
else
    echo "⚠️  Cannot create systemd service (requires root)"
    echo "   Service file template saved to: $SERVICE_FILE"
fi

# Generate auth token if not exists
if [ ! -f "$ASSISTANT_DIR/.auth_token" ]; then
    TOKEN=$(openssl rand -hex 32)
    echo "$TOKEN" > "$ASSISTANT_DIR/.auth_token"
    chmod 600 "$ASSISTANT_DIR/.auth_token"
    echo "✅ Generated auth token: $ASSISTANT_DIR/.auth_token"
    echo ""
    echo "⚠️  IMPORTANT: Save this token and update config/vps_config.json on local machine"
    echo "   Token: $TOKEN"
fi

# Copy public key if exists
if [ -f "keys/public.pem" ]; then
    cp keys/public.pem "$ASSISTANT_DIR/keys/public.pem"
    echo "✅ Copied RSA public key"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Set VPS_AUTH_TOKEN environment variable (if not using systemd)"
echo "2. Update config/vps_config.json on local machine with:"
echo "   - vps_url: https://your-domain"
echo "   - api_token: (token from .auth_token)"
echo "3. Start server manually:"
echo "   cd $ASSISTANT_DIR && python3 cloud_bridge_server.py"
echo ""
echo "Or use systemd (if enabled):"
echo "   sudo systemctl start julian-cloud-bridge"
echo "   sudo systemctl status julian-cloud-bridge"
echo ""
