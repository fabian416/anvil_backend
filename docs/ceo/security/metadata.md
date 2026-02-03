# Security & Compliance Module Metadata

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

| Attribute | Value |
|-----------|-------|
| **Module Name** | Security & Compliance |
| **Version** | 1.0.0 |
| **Status** | ✅ Production |
| **Primary Owner** | Security Team |
| **OWASP References** | LLM01, LLM08, A03:2021 |
| **Compliance** | GDPR, CCPA |

---

## 1. Module Overview

### Purpose
Enterprise-grade security and compliance system providing:
- **Attack Prevention** - XSS, Prompt Injection (OWASP coverage)
- **Data Protection** - PII redaction (GDPR/CCPA compliance)
- **Agent Security** - Multi-agent RBAC and isolation
- **Transaction Safety** - Human oversight for high-risk actions
- **Security Monitoring** - Vulnerability scanning and dashboards

### Key Capabilities
| Capability | Description | Status |
|------------|-------------|--------|
| XSS Protection | 150+ attack patterns (Helios) | ✅ Active |
| Prompt Injection | 219 attack patterns (LLMExploiter) | ✅ Active |
| PII Redaction | Email, Phone, SSN, CC, Wallet | ✅ Active |
| Agent Isolation | RBAC for multi-agent systems | ✅ Active |
| Transaction Approval | Human oversight for high-risk | ✅ Active |
| Security Dashboard | Admin monitoring | ✅ Active |
| Automated Scanning | OWASP tools integration | ⚠️ Manual |
| Audit Logging | Compliance tracking | ✅ Active |

---

## 2. File Reference Index

### Infrastructure Layer

#### Security Middleware
| File | Description | Lines |
|------|-------------|-------|
| `src/app/infrastructure/security/__init__.py` | Package exports | ~10 |
| `src/app/infrastructure/security/middleware/__init__.py` | Middleware exports | ~5 |
| `src/app/infrastructure/security/middleware/xss_guard.py` | XSS protection middleware | ~377 |
| `src/app/infrastructure/security/middleware/prompt_injection_guard.py` | Prompt injection detection | ~382 |

#### Security Services
| File | Description | Lines |
|------|-------------|-------|
| `src/app/infrastructure/security/pii_redaction.py` | PII detection and redaction | ~335 |
| `src/app/infrastructure/security/agent_isolation.py` | Agent RBAC and isolation | ~412 |
| `src/app/infrastructure/security/transaction_approval.py` | Transaction approval workflow | ~402 |
| `src/app/infrastructure/security/scan_result_aggregator.py` | Scan result aggregation | ~333 |
| `src/app/infrastructure/security/dashboard_service.py` | Dashboard metrics service | ~387 |

### Presentation Layer

| File | Description | Lines |
|------|-------------|-------|
| `src/app/presentation/http/controllers/admin/security_dashboard_router.py` | Dashboard API endpoints | ~428 |
| `src/app/presentation/http/controllers/admin/security_dashboard_schemas.py` | Pydantic schemas | ~150 |

### Domain Layer

| File | Description | Lines |
|------|-------------|-------|
| `src/app/domain/entities/chat/audit_log.py` | Audit log entity | ~161 |
| `src/app/domain/enums/audit_event_type.py` | Audit event types enum | ~50 |

### External Tools

| File | Description |
|------|-------------|
| `security/scripts/run_security_scan.sh` | Main scan orchestrator |
| `security/scripts/attack_simulations.py` | Attack simulation runner |
| `security/scripts/check_vulnerabilities.py` | Vulnerability checker |
| `security/monitoring/prometheus_metrics.py` | Prometheus metrics |
| `security/config/alerting-rules.yml` | Alerting configuration |
| `security/docker/Dockerfile.security-tools` | Security tools Docker |
| `security/docker/docker-compose.security.yml` | Compose for security tools |

### Tests

| File | Description |
|------|-------------|
| `tests/security/test_xss_guard.py` | XSS guard unit tests |
| `tests/security/test_all_middleware.py` | All middleware tests |
| `tests/security/test_security_validation.py` | Security validation tests |
| `tests/security/test_auth_security.py` | Auth security tests |
| `tests/integration/security/test_security_comprehensive.py` | E2E security tests |

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               CLIENT REQUESTS                                        │
│                                                                                      │
│                   HTTP Requests → All Endpoints → Responses                          │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         SECURITY MIDDLEWARE PIPELINE                                 │
│ ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                                  │ │
│ │  Request → [XSS Guard] → [Prompt Injection Guard] → Handler → Response          │ │
│ │            ↓ BLOCK 400       ↓ BLOCK 400                                         │ │
│ │          XSS detected    Injection detected                                      │ │
│ │                                                                                  │ │
│ │  Security Headers Added: X-Content-Type-Options, X-Frame-Options, CSP           │ │
│ │                                                                                  │ │
│ └─────────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │
                  ┌─────────────────────┼─────────────────────┐
                  │                     │                     │
                  ▼                     ▼                     ▼
┌─────────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   PRESENTATION LAYER    │  │   PRESENTATION LAYER │  │   PRESENTATION LAYER │
│                         │  │                       │  │                       │
│  Security Dashboard     │  │   Chat Endpoints      │  │   Transaction         │
│  /admin/security/*      │  │   (PII Protected)     │  │   Endpoints           │
│                         │  │                       │  │   (Approval Required) │
│  • Dashboard            │  │  • Messages           │  │                       │
│  • Scans                │  │  • Conversations      │  │  • Wallet ops         │
│  • Trends               │  │  • Search             │  │  • Token swaps        │
│  • Health               │  │                       │  │  • Transfers          │
└───────────┬─────────────┘  └───────────┬───────────┘  └───────────┬───────────┘
            │                            │                          │
            ▼                            ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            INFRASTRUCTURE LAYER                                      │
│                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                         DATA PROTECTION SERVICES                               │  │
│  │                                                                                │  │
│  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐   │  │
│  │  │  PIIRedactionService│  │ AgentIsolationGuard │  │TransactionApproval  │   │  │
│  │  │                     │  │                     │  │      Service        │   │  │
│  │  │ • detect_pii()      │  │ • register_agent()  │  │ • assess_risk()     │   │  │
│  │  │ • redact_pii()      │  │ • check_permission()│  │ • requires_approval()│  │  │
│  │  │ • check_pii_risk()  │  │ • validate_routing()│  │ • request_approval()│   │  │
│  │  │                     │  │                     │  │ • approve/reject()  │   │  │
│  │  │ Patterns:           │  │ Roles:              │  │                     │   │  │
│  │  │ • Email, Phone      │  │ • READ_ONLY         │  │ High-Risk Types:    │   │  │
│  │  │ • SSN, Credit Card  │  │ • STANDARD          │  │ • wallet_transaction│   │  │
│  │  │ • Wallet Address    │  │ • PRIVILEGED        │  │ • fund_transfer     │   │  │
│  │  │ • API Key, JWT      │  │ • ADMIN             │  │ • contract_deploy   │   │  │
│  │  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                         SECURITY ANALYTICS                                     │  │
│  │                                                                                │  │
│  │  ┌─────────────────────┐  ┌─────────────────────────────────────────────────┐ │  │
│  │  │ScanResultAggregator │  │          SecurityDashboardService               │ │  │
│  │  │                     │  │                                                  │ │  │
│  │  │ • get_latest_scan() │  │ • get_dashboard_summary()                       │ │  │
│  │  │ • get_scan_by_id()  │  │ • _get_security_posture() → Score 0-100        │ │  │
│  │  │ • get_scan_history()│  │ • _get_attack_statistics()                      │ │  │
│  │  │ • get_tool_results()│  │ • _get_transaction_approval_stats()            │ │  │
│  │  │ • get_trends()      │  │ • _get_pii_protection_stats()                  │ │  │
│  │  │                     │  │ • _get_agent_isolation_stats()                  │ │  │
│  │  │ Tool Reports:       │  │ • _get_vulnerability_summary()                  │ │  │
│  │  │ • Bandit            │  │ • _get_active_security_tools()                  │ │  │
│  │  │ • Safety            │  │                                                  │ │  │
│  │  │ • Helios            │  │ Active Tools: Helios, LLMExploiter, Bandit,     │ │  │
│  │  │ • LLMExploiter      │  │              Safety, Nettacker                   │ │  │
│  │  │ • Nettacker         │  │                                                  │ │  │
│  │  └─────────────────────┘  └─────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DOMAIN LAYER                                            │
│                                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                            AUDIT LOGGING                                       │  │
│  │                                                                                │  │
│  │  AuditLogEntry                    AuditEventType                              │  │
│  │  ┌─────────────────────┐          ┌─────────────────────────────────────────┐ │  │
│  │  │ • id: UUID          │          │ • SECURITY (requires_retention=True)    │ │  │
│  │  │ • event_type        │──────────│ • DATA_ACCESS (requires_retention=True) │ │  │
│  │  │ • action            │          │ • ADMIN_ACTION (requires_retention=True)│ │  │
│  │  │ • outcome           │          │ • AUTHENTICATION                         │ │  │
│  │  │ • user_id           │          │ • CHAT_MESSAGE                           │ │  │
│  │  │ • resource_id       │          │ • TRANSACTION                            │ │  │
│  │  │ • metadata          │          └─────────────────────────────────────────┘ │  │
│  │  │ • ip_address        │                                                      │  │
│  │  │ • created_at        │          Compliance Retention:                       │  │
│  │  └─────────────────────┘          • Security: 7 years                         │  │
│  │                                   • Data Access: 3 years                      │  │
│  │                                   • Other: 90 days                            │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SECURITY TOOLS                                    │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐     ││
│  │  │  Helios   │  │LLMExploiter│  │  Bandit   │  │  Safety   │  │ Nettacker │     ││
│  │  │           │  │           │  │           │  │           │  │           │     ││
│  │  │ XSS Tests │  │ LLM Tests │  │ Python    │  │ Dependency│  │ Network   │     ││
│  │  │ 150+      │  │ 219       │  │ Static    │  │ Vuln Scan │  │ Security  │     ││
│  │  │ patterns  │  │ attacks   │  │ Analysis  │  │           │  │ Scan      │     ││
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘     ││
│  │        │              │              │              │              │            ││
│  │        └──────────────┴──────────────┴──────────────┴──────────────┘            ││
│  │                                      │                                           ││
│  │                                      ▼                                           ││
│  │                    security/reports/{scan_id}/*.json                            ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

> **Note**: No dedicated security tables exist. Security uses application tables for audit logging.

### Audit Logs Table (Recommended)
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    outcome VARCHAR(20) DEFAULT 'success',
    
    -- Context
    user_id UUID REFERENCES users(id),
    resource_id UUID,
    resource_type VARCHAR(50),
    
    -- Additional Data
    metadata JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Error Details
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Indexes for compliance queries
    INDEX idx_audit_event_type (event_type),
    INDEX idx_audit_user_id (user_id),
    INDEX idx_audit_created_at (created_at),
    INDEX idx_audit_resource (resource_type, resource_id)
);
```

### Security Scan Results Table (Recommended)
```sql
CREATE TABLE security_scan_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id VARCHAR(20) UNIQUE NOT NULL,
    scan_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL,
    
    -- Tools
    tools_executed TEXT[], -- Array of tool names
    
    -- Vulnerabilities
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    info_count INTEGER DEFAULT 0,
    
    -- Reports
    reports_path VARCHAR(255),
    duration_seconds FLOAT,
    errors JSONB DEFAULT '[]',
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    INDEX idx_scan_date (scan_date DESC),
    INDEX idx_scan_status (status)
);
```

### Security Posture History Table (Recommended)
```sql
CREATE TABLE security_posture_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    level VARCHAR(20) NOT NULL,
    factors JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    INDEX idx_posture_created_at (created_at DESC)
);
```

---

## 5. Configuration

### Environment Variables
```bash
# Security Middleware
SECURITY_XSS_ENABLED=true
SECURITY_XSS_BLOCK_ON_DETECTION=true
SECURITY_PROMPT_INJECTION_ENABLED=true
SECURITY_PROMPT_INJECTION_SENSITIVITY=medium  # low, medium, high

# PII Redaction
PII_REDACTION_ENABLED=true
PII_REDACT_EMAILS=true
PII_REDACT_PHONES=true
PII_REDACT_FINANCIAL=true
PII_REDACT_CRYPTO=true

# Transaction Approval
TRANSACTION_APPROVAL_ENABLED=true
TRANSACTION_APPROVAL_TIMEOUT_MINUTES=5

# Security Reports
SECURITY_REPORTS_DIR=security/reports
```

### Default Security Configuration
```python
# src/app/setup/config/security.py

SECURITY_CONFIG = {
    "xss_guard": {
        "enabled": True,
        "block_on_detection": True,
        "excluded_paths": [r"/api/admin/.*", r"/health", r"/metrics"],
    },
    "prompt_injection": {
        "enabled": True,
        "block_on_detection": True,
        "sensitivity": "medium",
    },
    "pii_redaction": {
        "enabled": True,
        "redact_emails": True,
        "redact_phones": True,
        "redact_financial": True,
        "redact_crypto": True,
        "redact_credentials": True,
        "log_detections": True,
    },
    "agent_isolation": {
        "enabled": True,
        "enforce_isolation": True,
    },
    "transaction_approval": {
        "enabled": True,
        "timeout_minutes": 5,
        "require_for_high_risk": True,
    },
}
```

---

## 6. OWASP Compliance Matrix

| OWASP Reference | Description | Implementation | Status |
|-----------------|-------------|----------------|--------|
| **LLM01** | Prompt Injection | PromptInjectionGuard | ✅ |
| **LLM08** | Excessive Agency | TransactionApprovalService, AgentIsolationGuard | ✅ |
| **A03:2021** | Injection | XSSGuardMiddleware | ✅ |
| **Data Privacy** | GDPR/CCPA | PIIRedactionService | ✅ |

---

## 7. Improvements Roadmap

### Phase 1: Automation (High Priority)
| Improvement | Description | Effort |
|-------------|-------------|--------|
| Automated Scanning | Daily security scans via Celery | Medium |
| Alert Integration | PagerDuty/Slack integration | Low |
| Posture Tracking | Historical security score | Low |

### Phase 2: Enhanced Detection (Medium Priority)
| Improvement | Description | Effort |
|-------------|-------------|--------|
| ML-based Detection | Machine learning for anomaly detection | High |
| Rate Limiting | Attack-specific rate limits | Medium |
| IP Blacklisting | Automatic IP blocking | Medium |

### Phase 3: Compliance (Lower Priority)
| Improvement | Description | Effort |
|-------------|-------------|--------|
| Audit Log Retention | Automated archival/deletion | Medium |
| Compliance Reports | GDPR/SOC2 reporting | High |
| Data Lineage | Track PII through system | High |

### Technical Debt
| Item | Description | Priority |
|------|-------------|----------|
| Dashboard DI | Proper Dishka injection for aggregator | Medium |
| Test Coverage | Security dashboard API tests | High |
| Database Tables | Create security scan tables | Medium |

---

## 8. Security Considerations

### Current Protections
- ✅ XSS protection on all endpoints (150+ patterns)
- ✅ Prompt injection detection (219 patterns)
- ✅ PII redaction before logging/display
- ✅ Agent permission isolation
- ✅ Human oversight for high-risk actions
- ✅ Security headers on all responses

### Known Limitations
- ⚠️ Security scans run manually (not automated)
- ⚠️ No real-time attack rate limiting
- ⚠️ No automatic IP blacklisting
- ⚠️ Limited audit log retention policy

### Recommendations
1. **Implement automated daily scanning** via Celery
2. **Add rate limiting** for attack patterns
3. **Create security database tables** for persistence
4. **Implement audit log retention policy** for compliance

---

## References

- **XSS Guard**: `src/app/infrastructure/security/middleware/xss_guard.py`
- **Prompt Injection Guard**: `src/app/infrastructure/security/middleware/prompt_injection_guard.py`
- **PII Redaction**: `src/app/infrastructure/security/pii_redaction.py`
- **Agent Isolation**: `src/app/infrastructure/security/agent_isolation.py`
- **Transaction Approval**: `src/app/infrastructure/security/transaction_approval.py`
- **Dashboard Router**: `src/app/presentation/http/controllers/admin/security_dashboard_router.py`
- **Scan Aggregator**: `src/app/infrastructure/security/scan_result_aggregator.py`
- **Dashboard Service**: `src/app/infrastructure/security/dashboard_service.py`
- **Audit Log Entity**: `src/app/domain/entities/chat/audit_log.py`
- **Security Tools**: `security/` directory
