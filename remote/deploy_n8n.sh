#!/bin/bash
# n8n Deployment Script for Hostinger VPS
# Deploys n8n via Docker with security settings

set -e

echo "=========================================="
echo "n8n Deployment Script"
echo "=========================================="
echo ""

# Generate random password
N8N_PASSWORD=$(openssl rand -base64 16)

echo "[1/6] Generating authentication credentials..."
echo "Username: Julian"
echo "Password: $N8N_PASSWORD"
echo ""
echo "⚠️  SAVE THIS PASSWORD - you'll need it to access n8n!"
echo ""

# Create n8n data directory
echo "[2/6] Creating n8n data directory..."
mkdir -p ~/.n8n
chmod 755 ~/.n8n

# Stop existing container if any
echo "[3/6] Stopping any existing n8n containers..."
docker stop n8n 2>/dev/null || true
docker rm n8n 2>/dev/null || true

# Deploy n8n container
echo "[4/6] Deploying n8n Docker container..."
docker run -d --name n8n \
  --restart always \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=Julian \
  -e N8N_BASIC_AUTH_PASSWORD="$N8N_PASSWORD" \
  n8nio/n8n:latest

# Wait for container to start
echo "[5/6] Waiting for n8n to start..."
sleep 10

# Verify container is running
echo "[6/6] Verifying deployment..."
if docker ps | grep -q n8n; then
    echo "✅ n8n container is running!"
    echo ""
    echo "=========================================="
    echo "Deployment Complete"
    echo "=========================================="
    echo "n8n URL: http://localhost:5678"
    echo "Username: Julian"
    echo "Password: $N8N_PASSWORD"
    echo ""
    echo "⚠️  IMPORTANT: Save this password!"
    echo ""
    
    # Save password to file
    echo "$N8N_PASSWORD" > ~/.n8n_password.txt
    chmod 600 ~/.n8n_password.txt
    echo "Password saved to ~/.n8n_password.txt"
    
    exit 0
else
    echo "❌ Deployment failed - container not running"
    docker logs n8n
    exit 1
fi




