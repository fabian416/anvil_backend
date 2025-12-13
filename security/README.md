# Anvil Security Testing Infrastructure

This directory contains the complete security testing framework for the Anvil platform, implementing 5 OWASP security tools to protect against XSS, prompt injection, network vulnerabilities, and AI-specific attacks.

## Quick Start

```bash
# Install all security tools
./setup/install_all.sh

# Set environment variables
export ANVIL_TEST_TOKEN="your_test_token"
export STAGING_URL="https://staging.anvil.com"

# Run Docker containers
cd docker
docker-compose -f docker-compose.security.yml up -d
```

## Directory Structure

```
security/
├── setup/              # Installation scripts for each tool
├── config/             # Configuration files (auto-generated)
├── docker/             # Docker containers for security tools
├── scripts/            # Scan and report generation scripts
├── reports/            # Security scan results (JSON/HTML)
└── monitoring/         # Prometheus metrics and alerts
```

## Security Tools

1. **Helios** - XSS Testing (150+ attack vectors)
2. **LLMExploiter** - OWASP LLM Top 10 Testing (219 attacks)
3. **Nettacker** - Network/WebSocket Penetration Testing
4. **llm-security-auditor** - Multi-Agent System Security
5. **OWASP AI Testing Guide** - AI Model Robustness & Fairness

## Documentation

- Implementation Plan: `docs/security/IMPLEMENTATION_PLAN.md`
- Master Spec: `docs/security/SECURITY_TESTING_MASTER_SPEC.md`
- Individual tool specs: `libs/*/ANVIL_INTEGRATION_SPEC.md`

## Next Steps

Refer to `docs/security/IMPLEMENTATION_PLAN.md` for the 8-week deployment roadmap.
