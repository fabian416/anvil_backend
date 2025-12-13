#!/bin/bash
set -e

echo "🔒 Installing All Anvil Security Testing Tools"
echo "=============================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Track failures
FAILED_INSTALLS=()

# Install each tool
tools=("helios" "llmexploiter" "nettacker" "llm_security_auditor" "owasp_ai_testing")
for tool in "${tools[@]}"; do
    echo "📦 Installing $tool..."
    if bash "${SCRIPT_DIR}/install_${tool}.sh"; then
        echo "✅ $tool installed successfully"
    else
        echo "❌ $tool installation failed"
        FAILED_INSTALLS+=("$tool")
    fi
    echo ""
done

# Summary
echo "=============================================="
echo "Installation Summary:"
echo "Total tools: ${#tools[@]}"
echo "Successful: $((${#tools[@]} - ${#FAILED_INSTALLS[@]}))"
echo "Failed: ${#FAILED_INSTALLS[@]}"

if [ ${#FAILED_INSTALLS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed installations:"
    for failed in "${FAILED_INSTALLS[@]}"; do
        echo "  - $failed"
    done
    exit 1
else
    echo ""
    echo "✅ All security tools installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review configuration files in security/config/"
    echo "2. Set up environment variables (ANVIL_TEST_TOKEN, etc.)"
    echo "3. Run security/docker/docker-compose.security.yml"
    exit 0
fi
