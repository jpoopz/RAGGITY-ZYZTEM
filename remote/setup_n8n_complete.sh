#!/bin/bash
# Complete n8n Setup Script for Hostinger VPS
# Runs discovery, deployment, and configuration

set -e

echo "=========================================="
echo "Complete n8n Setup for Julian Assistant Suite"
echo "=========================================="
echo ""

# Step 1: Discovery
echo "[STEP 1] Discovering n8n..."
chmod +x discover_n8n.sh
./discover_n8n.sh
DISCOVERY_RESULT=$?

if [ $DISCOVERY_RESULT -eq 0 ]; then
    echo "✅ n8n already running - skipping deployment"
else
    echo ""
    echo "[STEP 2] Deploying n8n..."
    chmod +x deploy_n8n.sh
    ./deploy_n8n.sh
    if [ $? -ne 0 ]; then
        echo "❌ Deployment failed"
        exit 1
    fi
fi

# Step 3: Setup nginx and SSL
echo ""
echo "[STEP 3] Setting up nginx and SSL..."
read -p "Do you want to set up HTTPS with nginx? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    chmod +x setup_nginx_n8n.sh
    ./setup_nginx_n8n.sh
else
    echo "Skipping nginx setup"
fi

# Step 4: Show summary
echo ""
echo "=========================================="
echo "Setup Summary"
echo "=========================================="
echo ""
echo "n8n Status:"
docker ps | grep n8n || echo "Container not running"

echo ""
echo "Access Information:"
echo "  Local: http://localhost:5678"
if [ -f ~/.n8n_password.txt ]; then
    echo "  Username: Julian"
    echo "  Password: $(cat ~/.n8n_password.txt)"
fi

echo ""
echo "Next Steps:"
echo "  1. Log into n8n and complete authentication for:"
echo "     - Microsoft Outlook"
echo "     - Google Drive"
echo "     - Discord"
echo "     - Gmail"
echo "  2. Import workflows from /remote/n8n_workflows/"
echo "  3. Configure Julian Assistant Suite with n8n URL and credentials"
echo ""




