#!/bin/bash
# Setup n8n Environment Variables for LLM Router
# Adds API keys to n8n Docker container

set -e

echo "=========================================="
echo "n8n Environment Variables Setup"
echo "=========================================="
echo ""

# Check if n8n container is running
if ! docker ps | grep -q n8n; then
    echo "❌ n8n container is not running!"
    echo "Start n8n first: docker start n8n"
    exit 1
fi

echo "Reading API keys..."
echo ""

# Prompt for API keys
read -sp "Enter OpenAI API Key (or press Enter to skip): " OPENAI_KEY
echo ""
read -sp "Enter Claude API Key (or press Enter to skip): " CLAUDE_KEY
echo ""
read -sp "Enter Mistral API Key (or press Enter to skip): " MISTRAL_KEY
echo ""

# Stop n8n container
echo "[1/4] Stopping n8n container..."
docker stop n8n

# Update docker-compose or recreate with env vars
echo "[2/4] Updating n8n container with environment variables..."

# Check if docker-compose.yml exists
if [ -f docker-compose.yml ]; then
    # Update docker-compose.yml
    if [ -n "$OPENAI_KEY" ]; then
        sed -i "s/OPENAI_API_KEY:.*/OPENAI_API_KEY: $OPENAI_KEY/" docker-compose.yml || \
        echo "    - OPENAI_API_KEY=$OPENAI_KEY" >> docker-compose.yml
    fi
    if [ -n "$CLAUDE_KEY" ]; then
        sed -i "s/CLAUDE_API_KEY:.*/CLAUDE_API_KEY: $CLAUDE_KEY/" docker-compose.yml || \
        echo "    - CLAUDE_API_KEY=$CLAUDE_KEY" >> docker-compose.yml
    fi
    if [ -n "$MISTRAL_KEY" ]; then
        sed -i "s/MISTRAL_API_KEY:.*/MISTRAL_API_KEY: $MISTRAL_KEY/" docker-compose.yml || \
        echo "    - MISTRAL_API_KEY=$MISTRAL_KEY" >> docker-compose.yml
    fi
    docker-compose up -d n8n
else
    # Recreate container with env vars
    docker rm n8n
    
    # Get existing volume mounts
    VOLUME_MOUNT=$(docker inspect n8n 2>/dev/null | grep -o '"/home/[^"]*/.n8n[^"]*"' | head -1 | tr -d '"' || echo "$HOME/.n8n")
    
    # Build env string
    ENV_ARGS=""
    if [ -n "$OPENAI_KEY" ]; then
        ENV_ARGS="$ENV_ARGS -e OPENAI_API_KEY=$OPENAI_KEY"
    fi
    if [ -n "$CLAUDE_KEY" ]; then
        ENV_ARGS="$ENV_ARGS -e CLAUDE_API_KEY=$CLAUDE_KEY"
    fi
    if [ -n "$MISTRAL_KEY" ]; then
        ENV_ARGS="$ENV_ARGS -e MISTRAL_API_KEY=$MISTRAL_KEY"
    fi
    
    # Recreate container
    docker run -d --name n8n \
      --restart always \
      -p 5678:5678 \
      -v "$VOLUME_MOUNT:/home/node/.n8n" \
      $ENV_ARGS \
      n8nio/n8n:latest
fi

echo "[3/4] Starting n8n container..."
sleep 5

echo "[4/4] Verifying environment variables..."
docker exec n8n env | grep -E "(OPENAI|CLAUDE|MISTRAL)_API_KEY" || echo "⚠️  No API keys found in container"

echo ""
echo "=========================================="
echo "Setup Complete"
echo "=========================================="
echo ""
echo "⚠️  Note: For persistent environment variables,"
echo "   configure them in docker-compose.yml or"
echo "   use n8n's credential management system."
echo ""




