#!/bin/bash
# Start cloud bridge server on VPS/remote machine

echo "Starting RAGGITY Cloud Bridge Server..."

# Set environment variables
export CLOUD_KEY="${CLOUD_KEY:-changeme}"
export BACKUP_DIR="${BACKUP_DIR:-backups}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Install dependencies if needed
if ! command -v uvicorn &> /dev/null; then
    echo "Installing uvicorn..."
    pip install fastapi uvicorn
fi

# Start server
uvicorn remote.cloud_bridge_server:app --host 0.0.0.0 --port 9000

