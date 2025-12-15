# Security Infrastructure Deployment Guide

## Overview

This guide covers the deployment of the complete OWASP security infrastructure for the Anvil platform.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- Access to GitHub Actions
- Staging and production environments configured

## Phase 1: Infrastructure Setup

### 1.1 Install Security Tools

```bash
cd security/setup
chmod +x install_all.sh
./install_all.sh
```

This installs all 5 OWASP security tools:
- Helios (XSS testing)
- LLMExploiter (LLM security)
- Nettacker (Network scanning)
- llm-security-auditor (Multi-agent security)
- OWASP AI Testing Guide

### 1.2 Configure Environment Variables

```bash
# Set in .env or environment
export ANVIL_TEST_TOKEN="your_test_token"
export STAGING_URL="https://staging.anvil.com"
export SLACK_SECURITY_WEBHOOK="https://hooks.slack.com/..."
```

### 1.3 Start Docker Containers

```bash
cd security/docker
docker-compose -f docker-compose.security.yml up -d
```

## Phase 2: Defense Middleware Integration

### 2.1 Enable XSS Guard Middleware

Add to your FastAPI application:

```python
from src.app.infrastructure.security.middleware.xss_guard import XSSGuardMiddleware

app.add_middleware(
    XSSGuardMiddleware,
    enabled=True,
    block_on_detection=True,
    log_suspicious=True
)
```

### 2.2 Enable Prompt Injection Guard

For LLM endpoints:

```python
from src.app.infrastructure.security.middleware.prompt_injection_guard import PromptInjectionGuard

# Initialize guard
prompt_guard = PromptInjectionGuard(
    enabled=True,
    block_on_detection=True,
    sensitivity="medium"  # low/medium/high
)

# Check prompts before sending to LLM
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Check for prompt injection
    check_result = prompt_guard.check_prompt(request.message)
    
    if check_result["should_block"]:
        raise HTTPException(
            status_code=400,
            detail="Potential prompt injection detected"
        )
    
    # Process request...
```

### 2.3 Enable Transaction Approval

For high-risk operations:

```python
from src.app.infrastructure.security.transaction_approval import (
    TransactionApprovalService,
    TransactionRisk
)

# Initialize service
approval_service = TransactionApprovalService(
    approval_timeout_minutes=5,
    require_approval_for_high_risk=True
)

# Check if approval required
if approval_service.requires_approval("wallet_transaction", details):
    # Request approval
    approval_request = approval_service.request_approval(
        transaction_id=tx_id,
        user_id=user.id,
        transaction_type="wallet_transaction",
        details=details
    )
    return {"status": "approval_required", "request": approval_request}
```

### 2.4 Enable PII Redaction

```python
from src.app.infrastructure.security.pii_redaction import PIIRedactionService

# Initialize service
pii_service = PIIRedactionService(
    enabled=True,
    redact_emails=True,
    redact_phones=True,
    redact_financial=True
)

# Redact PII before logging or LLM processing
redacted_text, pii_types = pii_service.redact_pii(user_input)
logger.info(f"User input: {redacted_text}")
```

### 2.5 Enable Agent Isolation

```python
from src.app.infrastructure.security.agent_isolation import (
    AgentIsolationGuard,
    AgentRole,
    ResourceType
)

# Initialize guard
isolation_guard = AgentIsolationGuard(
    enabled=True,
    enforce_isolation=True
)

# Register agents
isolation_guard.register_agent("agent_1", AgentRole.STANDARD)
isolation_guard.register_agent("admin_agent", AgentRole.ADMIN)

# Check permissions before agent actions
check_result = isolation_guard.check_permission(
    agent_id="agent_1",
    resource_type=ResourceType.USER_DATA,
    action="write"
)

if not check_result["allowed"]:
    raise PermissionError("Agent not authorized")
```

## Phase 3: Testing

### 3.1 Run Security Tests

```bash
# Run security test suite
pytest tests/security/ -v

# Run with coverage
pytest tests/security/ --cov=src/app/infrastructure/security --cov-report=html
```

### 3.2 Manual Attack Simulation

Use the attack simulation scripts:

```bash
cd security/scripts
python attack_simulations.py --target staging --type xss
python attack_simulations.py --target staging --type prompt_injection
```

### 3.3 Performance Testing

Ensure security middleware doesn't significantly impact performance:

```bash
# Benchmark with middleware
locust -f tests/performance/security_load_test.py --host https://staging.anvil.com

# Target: <5ms overhead per request
```

## Phase 4: Production Deployment

### 4.1 Gradual Rollout

**Week 1: Monitoring Mode**
- Enable all middleware in log-only mode
- `block_on_detection=False`
- Monitor logs for false positives

**Week 2: Partial Enforcement**
- Enable blocking for XSS and Prompt Injection
- Keep Transaction Approval in testing mode
- Monitor error rates

**Week 3: Full Enforcement**
- Enable all blocking
- Monitor for 48 hours
- Adjust sensitivity if needed

**Week 4: Optimization**
- Fine-tune detection patterns
- Update excluded paths
- Optimize performance

### 4.2 Monitoring Setup

Configure Prometheus metrics:

```python
from prometheus_client import Counter, Histogram

# XSS detections
xss_detections = Counter(
    'xss_attacks_detected',
    'Number of XSS attacks detected',
    ['endpoint', 'severity']
)

# Prompt injection detections
prompt_injection_detections = Counter(
    'prompt_injection_detected',
    'Number of prompt injection attempts',
    ['risk_level']
)

# Response time impact
security_middleware_latency = Histogram(
    'security_middleware_seconds',
    'Security middleware processing time',
    ['middleware_type']
)
```

### 4.3 Alerting

Configure alerts in your monitoring system:

**Critical Alerts:**
- More than 10 XSS attacks in 5 minutes
- Critical prompt injection detected
- PII detected in logs
- Agent isolation violation

**Warning Alerts:**
- Security middleware response time > 50ms
- High rate of transaction approval requests
- Repeated failed permission checks

### 4.4 Dashboard Setup

The security dashboard is available at:
```
GET /api/admin/security/dashboard
```

Key metrics to monitor:
- Latest scan results
- Vulnerability trends
- Active security tools
- Overall security posture

## Rollback Procedure

If issues arise:

1. **Immediate:** Set `enabled=False` on problematic middleware
2. **Quick:** Restart application with environment variable:
   ```bash
   SECURITY_MIDDLEWARE_ENABLED=false
   ```
3. **Investigation:** Review logs:
   ```bash
   grep "XSS_ATTACK_DETECTED" /var/log/anvil/security.log
   ```

## Maintenance

### Weekly Tasks
- Review security scan results
- Check for tool updates
- Review blocked requests log

### Monthly Tasks
- Update attack patterns
- Review false positive rate
- Update documentation
- Team training

### Quarterly Tasks
- Full security audit
- Penetration testing
- Update OWASP tool versions
- Review and update policies

## Support

For issues or questions:
- Security team: security@anvil.com
- GitHub Issues: https://github.com/Anvil-com/anvil_backend/issues
- Slack: #security-alerts

## References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- Implementation Plan: docs/security/IMPLEMENTATION_PLAN.md
- Master Spec: docs/security/SECURITY_TESTING_MASTER_SPEC.md
