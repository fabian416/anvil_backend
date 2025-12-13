#!/bin/bash
set -e

echo "🛡️  Installing LLM Security Auditor..."

# Install from libs directory
AUDITOR_DIR="$(pwd)/libs/llm-security-auditor"

if [ -d "$AUDITOR_DIR" ]; then
    echo "📦 Installing from local repository..."
    cd "$AUDITOR_DIR"
    pip install -e .
    cd -
else
    echo "⚠️  Warning: llm-security-auditor not found in libs/"
    echo "📥 Installing dependencies manually..."
    pip install websockets aiohttp pydantic python-dotenv
fi

# Create config
echo "⚙️  Generating LLM Security Auditor configuration..."
cat > "$(dirname "$0")/../config/llm_auditor_config.yaml" << 'AUDITOR_CONFIG'
# LLM Security Auditor Configuration for Anvil Platform

websocket_endpoint: "wss://staging.anvil.com/v1/user/ws/chat"

test_categories:
  - multi_agent_security
  - agent_isolation
  - transaction_approval
  - streaming_security
  - cswsh_protection

max_tests_per_category: 50

rate_limit:
  requests_per_second: 5
  max_burst: 10

session_timeout_seconds: 300

auth_token_env: "ANVIL_TEST_TOKEN"
AUDITOR_CONFIG

echo "✅ LLM Security Auditor installed successfully!"
echo "📄 Configuration file: $(dirname "$0")/../config/llm_auditor_config.yaml"
