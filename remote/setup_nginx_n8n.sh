#!/bin/bash
# nginx + SSL Setup for n8n
# Configures reverse proxy and HTTPS for n8n on Hostinger VPS

set -e

DOMAIN="vps.julianassistant.com"
EMAIL="julian.poopat@gmail.com"

echo "=========================================="
echo "nginx + SSL Setup for n8n"
echo "=========================================="
echo ""

# Install nginx and certbot
echo "[1/6] Installing nginx and certbot..."
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Create nginx configuration
echo "[2/6] Creating nginx configuration..."
sudo tee /etc/nginx/sites-available/n8n.conf > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
echo "[3/6] Enabling nginx site..."
sudo ln -sf /etc/nginx/sites-available/n8n.conf /etc/nginx/sites-enabled/

# Test nginx configuration
echo "[4/6] Testing nginx configuration..."
sudo nginx -t

# Reload nginx
echo "[5/6] Reloading nginx..."
sudo systemctl reload nginx

# Obtain SSL certificate
echo "[6/6] Obtaining SSL certificate..."
echo "Note: This requires the domain to point to this server's IP"
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect

# Restart nginx
sudo systemctl restart nginx

echo ""
echo "=========================================="
echo "Setup Complete"
echo "=========================================="
echo "n8n is now accessible at:"
echo "👉 https://$DOMAIN"
echo ""
echo "Check nginx status: sudo systemctl status nginx"
echo "Check certbot certificates: sudo certbot certificates"
echo ""




