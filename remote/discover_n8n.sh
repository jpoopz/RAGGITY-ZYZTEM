#!/bin/bash
# n8n Discovery Script for Hostinger VPS
# Checks if n8n is already running or needs deployment

echo "=========================================="
echo "n8n Discovery & Deployment"
echo "=========================================="
echo ""

# Check for Docker container
echo "[1/4] Checking for Docker n8n container..."
if docker ps | grep -q n8n; then
    echo "✅ n8n Docker container found:"
    docker ps | grep n8n
    N8N_PORT=$(docker ps --format "{{.Ports}}" | grep n8n | sed -n 's/.*:\([0-9]*\)->.*/\1/p' | head -1)
    if [ -z "$N8N_PORT" ]; then
        N8N_PORT="5678"
    fi
    echo "   Port: $N8N_PORT"
    
    # Get auth info from container
    AUTH_ACTIVE=$(docker inspect n8n 2>/dev/null | grep -o 'N8N_BASIC_AUTH_ACTIVE=[^,}]*' | cut -d'=' -f2 | tr -d '"' || echo "false")
    echo "   Auth Active: $AUTH_ACTIVE"
    
    N8N_FOUND="docker"
else
    echo "❌ n8n Docker container not found"
    N8N_FOUND="none"
fi

# Check for systemd service
echo ""
echo "[2/4] Checking for n8n systemd service..."
if systemctl list-units --type=service 2>/dev/null | grep -q n8n; then
    echo "✅ n8n systemd service found:"
    systemctl status n8n --no-pager -l
    N8N_FOUND="systemd"
else
    echo "❌ n8n systemd service not found"
fi

# Check for open port 5678
echo ""
echo "[3/4] Checking for port 5678..."
if ss -tlnp 2>/dev/null | grep -q ":5678 " || netstat -tlnp 2>/dev/null | grep -q ":5678 "; then
    echo "✅ Port 5678 is open"
    echo "   Process info:"
    ss -tlnp 2>/dev/null | grep ":5678 " || netstat -tlnp 2>/dev/null | grep ":5678 "
else
    echo "❌ Port 5678 is not in use"
fi

# Check for n8n data directory
echo ""
echo "[4/4] Checking for n8n data directory..."
if [ -d ~/.n8n ] || [ -d /root/.n8n ]; then
    if [ -d ~/.n8n ]; then
        N8N_DATA_DIR="$HOME/.n8n"
    else
        N8N_DATA_DIR="/root/.n8n"
    fi
    echo "✅ n8n data directory found: $N8N_DATA_DIR"
else
    echo "❌ n8n data directory not found"
    N8N_DATA_DIR=""
fi

# Summary
echo ""
echo "=========================================="
echo "Discovery Summary"
echo "=========================================="
echo "n8n Status: $N8N_FOUND"
echo "Port: ${N8N_PORT:-5678}"
echo "Data Directory: ${N8N_DATA_DIR:-Not found}"
echo ""

if [ "$N8N_FOUND" != "none" ]; then
    echo "✅ n8n is already running!"
    echo "Skipping deployment..."
    exit 0
else
    echo "❌ n8n not found. Proceeding with deployment..."
    exit 1
fi




