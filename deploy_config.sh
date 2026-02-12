#!/bin/bash
# Script to deploy production configuration files to server
# Usage: ./deploy_config.sh

set -e

REMOTE_USER="ec2-user"
REMOTE_HOST="getrampy.com"
REMOTE_DIR="/opt/docker/anvil/config/prod"

echo "📦 Deploying configuration to $REMOTE_HOST..."

# Check if files exist locally
if [ ! -f "config/prod/config.toml" ]; then
    echo "❌ Error: config/prod/config.toml not found"
    exit 1
fi

if [ ! -f "config/prod/.secrets.toml" ]; then
    echo "❌ Error: config/prod/.secrets.toml not found"
    exit 1
fi

# Create remote directory
echo "📁 Creating remote directory..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}"

# Copy configuration files
echo "📤 Uploading config.toml..."
scp config/prod/config.toml ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/

echo "📤 Uploading .secrets.toml..."
scp config/prod/.secrets.toml ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/

# Set proper permissions
echo "🔒 Setting permissions..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "chmod 600 ${REMOTE_DIR}/.secrets.toml"
ssh ${REMOTE_USER}@${REMOTE_HOST} "chmod 644 ${REMOTE_DIR}/config.toml"

# Verify files
echo "✅ Verifying deployment..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "ls -lah ${REMOTE_DIR}"

echo ""
echo "✅ Configuration deployed successfully!"
echo ""
echo "⚠️  IMPORTANT: Edit ${REMOTE_DIR}/.secrets.toml on the server to:"
echo "   1. Set secure POSTGRES_PASSWORD (match .env file)"
echo "   2. Set secure JWT_SECRET (min 32 random chars)"
echo "   3. Set secure PASSWORD_PEPPER (min 32 random chars)"
echo ""
echo "Then restart services:"
echo "   cd /opt/docker/anvil"
echo "   docker compose -f docker-compose.production.yaml restart"
echo ""
