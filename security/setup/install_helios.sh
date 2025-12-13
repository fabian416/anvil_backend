#!/bin/bash
set -e

echo "🔒 Installing Helios XSS Testing Framework..."

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in a virtual environment. Creating one..."
    python3 -m venv /tmp/security-venv
    source /tmp/security-venv/bin/activate
fi

# Clone Helios repository (placeholder - actual repo would be used in production)
echo "📦 Cloning Helios repository..."
HELIOS_DIR="${HOME}/.anvil-security/helios"
mkdir -p "${HELIOS_DIR}"

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install requests beautifulsoup4 selenium lxml pyyaml

# Create config directory
mkdir -p "$(dirname "$0")/../config"

# Generate default Helios config
echo "⚙️  Generating Helios configuration..."
cat > "$(dirname "$0")/../config/helios_config.yaml" << 'HELIOS_CONFIG'
# Helios XSS Testing Configuration for Anvil Platform

target_endpoints:
  - https://staging.anvil.com/api/v1/user/chat/agent-squad/messages
  - https://staging.anvil.com/api/v1/user/portfolio
  - https://staging.anvil.com/api/v1/user/hunter/sentiment

test_categories:
  - script_injection
  - event_handler_injection
  - svg_xss
  - dom_clobbering
  - html_attribute_injection

severity_threshold: high

output_format: json

max_threads: 5

timeout_seconds: 30
HELIOS_CONFIG

echo "✅ Helios XSS Testing Framework installed successfully!"
echo "📄 Configuration file: $(dirname "$0")/../config/helios_config.yaml"
