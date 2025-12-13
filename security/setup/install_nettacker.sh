#!/bin/bash
set -e

echo "🌐 Installing OWASP Nettacker..."

# Nettacker runs via Docker
echo "🐳 Pulling Nettacker Docker image..."
docker pull owasp/nettacker:latest

# Create config
echo "⚙️  Generating Nettacker configuration..."
cat > "$(dirname "$0")/../config/nettacker_config.yaml" << 'NETTACKER_CONFIG'
# OWASP Nettacker Configuration for Anvil Platform

targets:
  - api.anvil.com
  - staging.anvil.com

modules:
  - websocket_scan
  - port_scan
  - http_status_scan
  - ssl_scan
  - subdomain_scan
  - dir_scan
  - http_auth_scan

ports: "80,443,8000-9000"

parallel_scans: 10

output_dir: /reports

timeout: 300
NETTACKER_CONFIG

echo "✅ OWASP Nettacker installed successfully!"
echo "📄 Configuration file: $(dirname "$0")/../config/nettacker_config.yaml"
echo "🐳 Docker image: owasp/nettacker:latest"
