#!/bin/bash
set -e

echo "🎯 Installing OWASP AI Testing Guide tools..."

# Install from libs directory
AI_TESTING_DIR="$(pwd)/libs/www-project-ai-testing-guide"

if [ -d "$AI_TESTING_DIR" ]; then
    echo "📦 Installing from local repository..."
    cd "$AI_TESTING_DIR"
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    cd -
else
    echo "⚠️  Warning: www-project-ai-testing-guide not found in libs/"
    echo "📥 Installing AI/ML testing dependencies..."
    pip install scikit-learn numpy pandas scipy matplotlib jupyter
fi

# Create config
echo "⚙️  Generating OWASP AI Testing configuration..."
cat > "$(dirname "$0")/../config/ai_testing_config.yaml" << 'AI_TESTING_CONFIG'
# OWASP AI Testing Guide Configuration for Anvil Platform

test_categories:
  - model_robustness
  - bias_and_fairness
  - data_privacy
  - explainability
  - adversarial_robustness
  - monitoring_and_logging

models_to_test:
  - name: "Agent Squad"
    type: "LLM"
    endpoint: "https://staging.anvil.com/v1/user/chat/agent-squad/messages"
  - name: "Hunter AI Sentiment"
    type: "ML"
    endpoint: "https://staging.anvil.com/v1/user/hunter/sentiment"
  - name: "Hunter AI Price Prediction"
    type: "ML"
    endpoint: "https://staging.anvil.com/v1/user/hunter/price-prediction"

adversarial_test_count: 100

bias_detection_threshold: 0.1

pii_patterns:
  - wallet_addresses
  - email_addresses
  - api_keys

output_format: json
AI_TESTING_CONFIG

echo "✅ OWASP AI Testing Guide tools installed successfully!"
echo "📄 Configuration file: $(dirname "$0")/../config/ai_testing_config.yaml"
