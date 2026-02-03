# Security & Compliance Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Security & Compliance system provides enterprise-grade security through:
- **XSSGuardMiddleware** - Cross-site scripting prevention (150+ patterns)
- **PromptInjectionGuard** - LLM prompt injection detection (219 patterns)
- **PIIRedactionService** - PII detection and redaction (GDPR/CCPA)
- **AgentIsolationGuard** - Multi-agent RBAC and isolation
- **TransactionApprovalService** - Human oversight for high-risk actions
- **ScanResultAggregator** - Security scan result aggregation

**Total Service Components**: 10+ Python modules

---

## 1. Security Middleware Services

### 1.1 XSSGuardMiddleware
**Path**: `src/app/infrastructure/security/middleware/xss_guard.py`

FastAPI middleware for XSS protection using Helios attack patterns.

```python
class XSSGuardMiddleware(BaseHTTPMiddleware):
    """
    Protects against:
    - Script injection (<script> tags)
    - Event handler injection (onclick, onerror, onload)
    - SVG-based XSS
    - Data URI XSS
    - JavaScript protocol handlers
    - HTML entity encoding attacks
    - DOM clobbering
    - Attribute-based XSS
    """
    
    # 25+ danger patterns
    DANGER_PATTERNS = [
        r'<\s*script[^>]*>.*?</\s*script\s*>',
        r'on\w+\s*=\s*["\']?[^"\']*["\']?',
        r'javascript\s*:',
        r'<\s*svg[^>]*>',
        r'<\s*iframe[^>]*>',
        ...
    ]
    
    def __init__(
        self,
        app,
        enabled: bool = True,
        block_on_detection: bool = True,
        log_suspicious: bool = True,
        excluded_paths: Optional[List[str]] = None
    ): ...
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through XSS guard."""
```

**Key Methods**:
- `_check_query_params()` - Check query parameters for XSS
- `_check_request_body()` - Check JSON body for XSS
- `_check_headers()` - Check HTTP headers for XSS
- `_check_json_recursive()` - Recursively check nested JSON

**Security Headers Added**:
```python
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Content-Security-Policy"] = "default-src 'self'"
```

---

### 1.2 PromptInjectionGuard
**Path**: `src/app/infrastructure/security/middleware/prompt_injection_guard.py`

Guards against prompt injection attacks based on OWASP LLM01.

```python
class PromptInjectionGuard:
    """
    Detects patterns from OWASP LLM01 including:
    - Direct prompt injection (system override attempts)
    - Indirect prompt injection (via external data)
    - Jailbreaking attempts
    - Role manipulation
    - Instruction override
    - Delimiter attacks
    """
    
    # 30+ injection patterns
    INJECTION_PATTERNS = [
        r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)',
        r'you\s+are\s+now\s+(a|an)\s+\w+',
        r'DAN\s+mode',
        r'\[\s*SYSTEM\s*\]',
        r'print\s+(your\s+)?(instructions|system\s+prompt)',
        ...
    ]
    
    def __init__(
        self,
        enabled: bool = True,
        block_on_detection: bool = True,
        log_attempts: bool = True,
        sensitivity: str = "medium"  # low, medium, high
    ): ...
    
    def check_prompt(self, prompt: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Check a prompt for injection attempts."""
    
    async def check_request(self, request: Request) -> Dict[str, Any]:
        """Check an HTTP request for prompt injection."""
    
    def check_request_data(self, data: Any, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Recursively check request data for prompts."""
```

**Risk Levels**:
| Level | Detection | Action |
|-------|-----------|--------|
| `critical` | Injection patterns | Block |
| `high` | Extraction patterns | Block (medium+) |
| `medium` | Suspicious patterns | Block (high only) |
| `none` | Safe | Allow |

---

## 2. Data Protection Services

### 2.1 PIIRedactionService
**Path**: `src/app/infrastructure/security/pii_redaction.py`

PII detection and redaction for GDPR/CCPA compliance.

```python
class PIIType(str, Enum):
    """Types of PII that can be detected"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    WALLET_ADDRESS = "wallet_address"
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"

class PIIRedactionService:
    """
    Protects against:
    - Accidental PII disclosure in LLM prompts
    - PII leakage in LLM responses
    - Logging sensitive data
    - Training data contamination
    """
    
    PII_PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.]?)?(?:\(?\d{3}\)?[-.]?)?\d{3}[-.]?\d{4}\b',
        PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        PIIType.CREDIT_CARD: r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        PIIType.WALLET_ADDRESS: r'\b0x[a-fA-F0-9]{40}\b',
        PIIType.JWT_TOKEN: r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b',
    }
    
    def __init__(
        self,
        enabled: bool = True,
        redact_emails: bool = True,
        redact_phones: bool = True,
        redact_financial: bool = True,
        redact_crypto: bool = True,
        redact_credentials: bool = True,
        log_detections: bool = True
    ): ...
    
    def detect_pii(self, text: str) -> List[Tuple[PIIType, str]]:
        """Detect PII in text."""
    
    def redact_pii(self, text: str, preserve_structure: bool = False) -> Tuple[str, List[PIIType]]:
        """Redact PII from text."""
    
    def redact_pii_recursive(self, data: Any) -> Tuple[Any, List[PIIType]]:
        """Recursively redact PII from nested data structures."""
    
    def check_pii_risk(self, text: str) -> Dict[str, Any]:
        """Assess PII risk in text without redacting."""
```

**Risk Scoring**:
| PII Type | Risk Score |
|----------|------------|
| SSN | 10 |
| Credit Card | 10 |
| Passport | 9 |
| API Key | 8 |
| JWT Token | 8 |
| Wallet Address | 7 |
| Email | 5 |
| Phone | 5 |
| IP Address | 3 |

---

## 3. Agent Security Services

### 3.1 AgentIsolationGuard
**Path**: `src/app/infrastructure/security/agent_isolation.py`

Role-based access control for multi-agent systems (OWASP LLM08).

```python
class AgentRole(str, Enum):
    """Predefined agent roles with different privilege levels"""
    READ_ONLY = "read_only"
    STANDARD = "standard"
    PRIVILEGED = "privileged"
    ADMIN = "admin"

class ResourceType(str, Enum):
    """Types of resources that can be accessed"""
    USER_DATA = "user_data"
    SYSTEM_CONFIG = "system_config"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    WALLET = "wallet"
    AGENT_COMMUNICATION = "agent_communication"

class AgentIsolationGuard:
    """
    Implements:
    - Role-based access control (RBAC) for agents
    - Resource isolation between agents
    - Action whitelisting
    - Cross-agent communication controls
    """
    
    # High-risk actions requiring extra validation
    HIGH_RISK_ACTIONS = {
        "delete", "transfer", "execute", "terminate", "broadcast", "elevate"
    }
    
    def register_agent(
        self, agent_id: str, role: AgentRole, custom_permissions: Optional[List] = None
    ): ...
    
    def check_permission(
        self, agent_id: str, resource_type: ResourceType, action: str, scope: Optional[str] = None
    ) -> Dict[str, Any]: ...
    
    def check_agent_communication(
        self, sender_agent_id: str, recipient_agent_id: str, message_type: str = "standard"
    ) -> Dict[str, Any]: ...
    
    def validate_agent_routing(
        self, user_message: str, requested_agents: List[str]
    ) -> Dict[str, Any]: ...
    
    def get_agent_capabilities(self, agent_id: str) -> Dict[str, Any]: ...
    
    def revoke_agent_access(self, agent_id: str): ...
```

**Default Role Permissions**:
| Role | USER_DATA | SYSTEM_CONFIG | WALLET | AGENT_COMM |
|------|-----------|---------------|--------|------------|
| READ_ONLY | read | - | - | read, send |
| STANDARD | read, write | - | - | read, send |
| PRIVILEGED | read, write, delete | - | - | read, send, broadcast |
| ADMIN | read, write, delete | read, write | read, transfer | all |

---

### 3.2 TransactionApprovalService
**Path**: `src/app/infrastructure/security/transaction_approval.py`

Human oversight for high-risk LLM-initiated actions (OWASP LLM08).

```python
class TransactionRisk(str, Enum):
    """Risk levels for LLM-initiated transactions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ApprovalStatus(str, Enum):
    """Status of transaction approval"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TransactionApprovalService:
    """
    Protects against OWASP LLM08 (Excessive Agency) by ensuring
    human oversight for high-risk actions.
    """
    
    # High-risk transaction types requiring approval
    HIGH_RISK_TYPES = [
        "wallet_transaction",
        "fund_transfer",
        "contract_deployment",
        "token_swap",
        "liquidity_provision",
        "stake_assets",
        "governance_vote",
        "data_export",
        "system_config_change",
        "user_data_deletion"
    ]
    
    def __init__(
        self,
        approval_timeout_minutes: int = 5,
        require_approval_for_high_risk: bool = True
    ): ...
    
    def assess_risk(self, transaction_type: str, details: Dict) -> TransactionRisk: ...
    
    def requires_approval(self, transaction_type: str, details: Dict) -> bool: ...
    
    def request_approval(
        self, transaction_id: str, user_id: str, transaction_type: str, details: Dict
    ) -> TransactionApprovalRequest: ...
    
    def approve_transaction(self, transaction_id: str, approver_id: str) -> bool: ...
    
    def reject_transaction(self, transaction_id: str, rejector_id: str) -> bool: ...
    
    def check_approval_status(self, transaction_id: str) -> Optional[ApprovalStatus]: ...
    
    def get_pending_approvals(self, user_id: Optional[str] = None) -> List[TransactionApprovalRequest]: ...
    
    def cleanup_expired(self): ...
```

---

## 4. Security Analytics Services

### 4.1 ScanResultAggregator
**Path**: `src/app/infrastructure/security/scan_result_aggregator.py`

Aggregates security scan results from multiple OWASP tools.

```python
class ScanStatus(str, Enum):
    """Status of a security scan"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"

class ScanResultAggregator:
    """Aggregates security scan results from multiple tools"""
    
    def __init__(self, reports_base_dir: Path): ...
    
    def get_latest_scan(self) -> Optional[SecurityScanResult]: ...
    
    def get_scan_by_id(self, scan_id: str) -> Optional[SecurityScanResult]: ...
    
    def get_scan_history(self, limit: int = 10) -> List[SecurityScanResult]: ...
    
    def get_vulnerability_trends(self, days: int = 30) -> Dict[str, List[int]]: ...
    
    def get_tool_results(self, scan_id: str) -> List[ToolScanResult]: ...
```

---

### 4.2 SecurityDashboardService
**Path**: `src/app/infrastructure/security/dashboard_service.py`

Aggregates security metrics for monitoring dashboard.

```python
class SecurityDashboardService:
    """
    Aggregates security metrics from all defense middleware and scanning tools.
    
    Provides unified dashboard view of:
    - Attack statistics (XSS, Prompt Injection)
    - Transaction approval metrics
    - PII protection statistics
    - Agent isolation violations
    - Security scan results
    - Overall security posture
    """
    
    def get_dashboard_summary(self) -> Dict[str, Any]: ...
    
    def _get_security_posture(self) -> Dict[str, Any]:
        """Calculate overall security posture score (0-100)."""
    
    def _get_attack_statistics(self) -> Dict[str, Any]:
        """Get 24-hour attack detection and blocking statistics."""
    
    def _get_transaction_approval_stats(self) -> Dict[str, Any]: ...
    
    def _get_pii_protection_stats(self) -> Dict[str, Any]: ...
    
    def _get_agent_isolation_stats(self) -> Dict[str, Any]: ...
    
    def _get_latest_scan_results(self) -> Optional[Dict[str, Any]]: ...
    
    def _get_vulnerability_summary(self) -> Dict[str, Any]: ...
    
    def _get_active_security_tools(self) -> List[Dict[str, Any]]: ...
    
    def get_vulnerability_trends(self, days: int = 30) -> Dict[str, Any]: ...
```

---

## 5. Domain Entities

### 5.1 AuditLogEntry
**Path**: `src/app/domain/entities/chat/audit_log.py`

Enterprise-grade audit logging for compliance.

```python
@dataclass
class AuditLogEntry:
    """
    Represents a single auditable event for compliance and security.
    """
    id: UUID
    event_type: AuditEventType
    action: str
    outcome: str  # "success", "failure", "pending"
    
    # Context
    user_id: Optional[UUID]
    resource_id: Optional[UUID]
    resource_type: Optional[str]
    
    # Additional Data
    metadata: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    # Error details
    error_message: Optional[str]
    error_code: Optional[str]
    
    # Timestamps
    created_at: datetime
    
    def is_security_event(self) -> bool: ...
    def is_data_access_event(self) -> bool: ...
    def is_admin_action(self) -> bool: ...
    def requires_retention(self) -> bool: ...
```

---

## 6. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                 Security Dashboard Router                             │  │
│  │  /admin/security/dashboard • /scans • /trends • /health              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    All HTTP Endpoints                                 │  │
│  │  (XSS Guard + Prompt Injection Guard applied transparently)          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                   Security Middleware                                 │  │
│  │                                                                        │  │
│  │  ┌─────────────────────┐  ┌─────────────────────────────────────────┐│  │
│  │  │  XSSGuardMiddleware │  │       PromptInjectionGuard              ││  │
│  │  │                     │  │                                          ││  │
│  │  │ • 150+ XSS patterns │  │ • 219 LLM injection patterns            ││  │
│  │  │ • Query params      │  │ • System override detection              ││  │
│  │  │ • Request body      │  │ • Jailbreak detection                    ││  │
│  │  │ • Headers           │  │ • Role manipulation                      ││  │
│  │  │ • Security headers  │  │ • Extraction attempts                    ││  │
│  │  └─────────────────────┘  └─────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                   Data Protection                                     │  │
│  │                                                                        │  │
│  │  ┌─────────────────────┐  ┌─────────────────────────────────────────┐│  │
│  │  │  PIIRedactionService│  │    TransactionApprovalService           ││  │
│  │  │                     │  │                                          ││  │
│  │  │ • Email redaction   │  │ • Risk assessment                        ││  │
│  │  │ • Phone redaction   │  │ • Approval workflow                      ││  │
│  │  │ • SSN/CC redaction  │  │ • Expiration handling                    ││  │
│  │  │ • Wallet addresses  │  │ • Pending approvals                      ││  │
│  │  │ • Risk scoring      │  │ • High-risk types                        ││  │
│  │  └─────────────────────┘  └─────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                   Agent Security                                      │  │
│  │                                                                        │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │               AgentIsolationGuard                              │  │  │
│  │  │                                                                  │  │  │
│  │  │ • Role-based access control (READ_ONLY, STANDARD, PRIVILEGED)  │  │  │
│  │  │ • Resource isolation (USER_DATA, WALLET, SYSTEM_CONFIG)        │  │  │
│  │  │ • Cross-agent communication controls                            │  │  │
│  │  │ • Routing validation (prevent admin escalation)                 │  │  │
│  │  │ • Permission checking and violation tracking                    │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                   Security Analytics                                  │  │
│  │                                                                        │  │
│  │  ┌─────────────────────┐  ┌─────────────────────────────────────────┐│  │
│  │  │ ScanResultAggregator│  │   SecurityDashboardService              ││  │
│  │  │                     │  │                                          ││  │
│  │  │ • Parse tool reports│  │ • Security posture score                 ││  │
│  │  │ • Aggregate vulns   │  │ • Attack statistics                      ││  │
│  │  │ • Scan history      │  │ • PII protection stats                   ││  │
│  │  │ • Trends            │  │ • Agent isolation stats                  ││  │
│  │  └─────────────────────┘  └─────────────────────────────────────────┘│  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Audit Logging                                      │  │
│  │                                                                        │  │
│  │  AuditLogEntry • AuditEventType • AuditLogRepository                 │  │
│  │                                                                        │  │
│  │  Events: SECURITY, DATA_ACCESS, ADMIN_ACTION, AUTHENTICATION         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL TOOLS                                         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                   OWASP Security Tools                              │    │
│  │                                                                      │    │
│  │  Helios (XSS) • LLMExploiter (LLM) • Bandit (Python)               │    │
│  │  Safety (Dependencies) • Nettacker (Network)                        │    │
│  │                                                                      │    │
│  │  Reports: security/reports/{scan_id}/*.json                         │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## References

- **XSS Guard**: `src/app/infrastructure/security/middleware/xss_guard.py`
- **Prompt Injection Guard**: `src/app/infrastructure/security/middleware/prompt_injection_guard.py`
- **PII Redaction**: `src/app/infrastructure/security/pii_redaction.py`
- **Agent Isolation**: `src/app/infrastructure/security/agent_isolation.py`
- **Transaction Approval**: `src/app/infrastructure/security/transaction_approval.py`
- **Scan Aggregator**: `src/app/infrastructure/security/scan_result_aggregator.py`
- **Dashboard Service**: `src/app/infrastructure/security/dashboard_service.py`
- **Audit Log Entity**: `src/app/domain/entities/chat/audit_log.py`
