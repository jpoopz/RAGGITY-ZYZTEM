#!/bin/bash
set -e
echo "🚀 Deploying RAGGITY-ZYZTEM (with HTTPS)..."
git pull origin main
docker compose -f docker-compose.prod.yml down --remove-orphans
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker system prune -f
echo "✅ Deployment complete. Accessible at https://yourdomain.com"


