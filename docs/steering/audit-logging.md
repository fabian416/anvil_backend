# Audit Logging - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El sistema de Audit Logging proporciona trazabilidad enterprise-grade:

1. **Audit Log Entity**: Registro inmutable de eventos con categorización
2. **Event Types**: 45+ tipos de eventos (Security, Data Access, Admin, User)
3. **Repository Pattern**: Port/Adapter para persistencia PostgreSQL
4. **Telemetry Services**: LLM, API, Retry, Distillation tracking
5. **Distributed Tracing**: OpenTelemetry-compatible spans
6. **Security Dashboard**: Agregación de métricas de seguridad
7. **Compliance Reporting**: GDPR, CCPA compliance support
8. **Retention Policies**: Configurable con exclusión de eventos críticos

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           AUDIT LOGGING ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                              ┌────────────────────┐
                              │   User/System      │
                              │   Actions          │
                              └──────────┬─────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│  AuditLogEntry  │            │   Telemetry     │            │  Distributed    │
│  (Domain)       │            │   Collectors    │            │  Tracing        │
└────────┬────────┘            └────────┬────────┘            └────────┬────────┘
         │                              │                              │
         ▼                              ▼                              ▼
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│ AuditLogRepo    │            │  LLM Telemetry  │            │  TracingService │
│ (PostgreSQL)    │            │  API Telemetry  │            │  (In-Memory)    │
│                 │            │  Retry Telemetry│            │                 │
└────────┬────────┘            └────────┬────────┘            └────────┬────────┘
         │                              │                              │
         └───────────────────────┬──────┴──────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Security Dashboard   │
                    │   Admin API            │
                    │   Compliance Reports   │
                    └────────────────────────┘
```

---

## 1. Audit Log Entity

### AuditLogEntry

**Location**: `src/app/domain/entities/chat/audit_log.py`

Entidad inmutable para eventos auditables.

```python
@dataclass
class AuditLogEntry:
    """
    Audit log entry entity.
    
    Represents a single auditable event in the system for compliance and security.
    Immutable after creation with indexed timestamp for efficient querying.
    """
    
    id: UUID = field(default_factory=uuid4)
    event_type: AuditEventType = None
    action: str = None
    outcome: str = "success"  # "success", "failure", "pending"
    
    # Context
    user_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    resource_type: Optional[str] = None
    
    # Additional Data
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Error details (for failed events)
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    # Timestamp (immutable)
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### Entity Methods

```python
# Check event outcome
entry.is_success() -> bool
entry.is_failure() -> bool
entry.is_pending() -> bool

# Check event category
entry.is_security_event() -> bool
entry.is_data_access_event() -> bool
entry.is_admin_action() -> bool

# Compliance
entry.requires_retention() -> bool  # True for security/data/admin events

# Metadata management
entry.add_metadata(key, value)
entry.get_metadata(key, default=None)

# Mark as failed
entry.with_error(error_message, error_code=None)

# Serialization
entry.to_dict() -> Dict[str, Any]
```

### System AuditLog Entity

**Location**: `src/app/domain/entities/system/audit_log.py`

Entidad alternativa para operaciones de sistema.

```python
@dataclass(eq=False, kw_only=True)
class AuditLog(Entity[AuditLogId]):
    actor_user_id: UserId
    action: str
    entity: str
    entity_id: Optional[str]
    payload_json: Optional[dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: CreatedAt
```

---

## 2. Audit Event Types

### AuditEventType Enum

**Location**: `src/app/domain/enums/audit_event_type.py`

```python
class AuditEventType(StrEnum):
    """45+ auditable event types organized by category."""
    
    # =========================================================================
    # USER ACTIONS (8 types)
    # =========================================================================
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    USER_PROFILE_UPDATE = "user_profile_update"
    USER_PREFERENCE_CHANGE = "user_preference_change"
    USER_PASSWORD_CHANGE = "user_password_change"
    USER_EMAIL_CHANGE = "user_email_change"
    USER_ROLE_CHANGE = "user_role_change"
    
    # =========================================================================
    # EXPORT ACTIONS (3 types)
    # =========================================================================
    EXPORT_REQUEST = "export_request"
    EXPORT_DOWNLOAD = "export_download"
    EXPORT_DELETION = "export_deletion"
    
    # =========================================================================
    # CONVERSATION ACTIONS (6 types)
    # =========================================================================
    CONVERSATION_CREATE = "conversation_create"
    CONVERSATION_DELETE = "conversation_delete"
    CONVERSATION_SHARE = "conversation_share"
    MESSAGE_CREATE = "message_create"
    MESSAGE_UPDATE = "message_update"
    MESSAGE_DELETE = "message_delete"
    
    # =========================================================================
    # TEMPLATE ACTIONS (4 types)
    # =========================================================================
    TEMPLATE_CREATE = "template_create"
    TEMPLATE_UPDATE = "template_update"
    TEMPLATE_DELETE = "template_delete"
    TEMPLATE_EXECUTE = "template_execute"
    
    # =========================================================================
    # AGENT ACTIONS (5 types)
    # =========================================================================
    AGENT_EXECUTION_START = "agent_execution_start"
    AGENT_EXECUTION_COMPLETE = "agent_execution_complete"
    AGENT_EXECUTION_FAILED = "agent_execution_failed"
    VOTING_ROUND_START = "voting_round_start"
    VOTING_ROUND_COMPLETE = "voting_round_complete"
    
    # =========================================================================
    # SECURITY EVENTS (8 types) - Requires Long-Term Retention
    # =========================================================================
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_TOKEN_REFRESH = "auth_token_refresh"
    AUTH_TOKEN_REVOKE = "auth_token_revoke"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # =========================================================================
    # DATA ACCESS EVENTS (5 types) - Requires Long-Term Retention
    # =========================================================================
    PII_VIEW = "pii_view"
    PII_EXPORT = "pii_export"
    PII_MODIFICATION = "pii_modification"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    BULK_DATA_EXPORT = "bulk_data_export"
    
    # =========================================================================
    # SYSTEM EVENTS (6 types)
    # =========================================================================
    SYSTEM_CONFIGURATION_CHANGE = "system_configuration_change"
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    BACKGROUND_JOB_START = "background_job_start"
    BACKGROUND_JOB_COMPLETE = "background_job_complete"
    BACKGROUND_JOB_FAILED = "background_job_failed"
    
    # =========================================================================
    # ADMINISTRATIVE ACTIONS (6 types) - Requires Long-Term Retention
    # =========================================================================
    ADMIN_USER_SUSPENSION = "admin_user_suspension"
    ADMIN_USER_ACTIVATION = "admin_user_activation"
    ADMIN_USER_DELETION = "admin_user_deletion"
    ADMIN_ROLE_ASSIGNMENT = "admin_role_assignment"
    ADMIN_PERMISSION_GRANT = "admin_permission_grant"
    ADMIN_PERMISSION_REVOKE = "admin_permission_revoke"
```

### Event Type Properties

```python
@property
def is_security_event(self) -> bool:
    """True for AUTH_*, UNAUTHORIZED_*, RATE_LIMIT_*, SUSPICIOUS_*"""
    ...

@property
def is_data_access_event(self) -> bool:
    """True for PII_*, SENSITIVE_DATA_*, BULK_DATA_*"""
    ...

@property
def is_admin_action(self) -> bool:
    """True for ADMIN_*"""
    ...

@property
def requires_retention(self) -> bool:
    """True for security, data access, or admin events."""
    return self.is_security_event or self.is_data_access_event or self.is_admin_action
```

---

## 3. Audit Log Repository

### AuditLogRepository Port

**Location**: `src/app/domain/ports/audit_log_repository.py`

```python
class AuditLogRepository(ABC):
    """Port for audit log persistence."""
    
    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def save(self, entry: AuditLogEntry) -> AuditLogEntry:
        """Save single audit log entry."""
        ...
    
    @abstractmethod
    async def save_batch(self, entries: List[AuditLogEntry]) -> List[AuditLogEntry]:
        """Save multiple entries in batch (optimized for high volume)."""
        ...
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    @abstractmethod
    async def get_by_id(self, entry_id: UUID) -> Optional[AuditLogEntry]:
        """Get by ID."""
        ...
    
    @abstractmethod
    async def get_by_user(
        self, user_id: UUID, limit: int = 100, offset: int = 0,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[AuditLogEntry]:
        """Get logs for specific user (most recent first)."""
        ...
    
    @abstractmethod
    async def get_by_event_type(
        self, event_type: AuditEventType, limit: int = 100, offset: int = 0,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[AuditLogEntry]:
        """Get logs by event type."""
        ...
    
    @abstractmethod
    async def get_by_resource(
        self, resource_id: UUID, resource_type: Optional[str] = None,
        limit: int = 100, offset: int = 0
    ) -> List[AuditLogEntry]:
        """Get logs for specific resource."""
        ...
    
    @abstractmethod
    async def get_by_ip_address(
        self, ip_address: str, limit: int = 100, offset: int = 0,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[AuditLogEntry]:
        """Get logs from specific IP."""
        ...
    
    # =========================================================================
    # SECURITY QUERIES
    # =========================================================================
    
    @abstractmethod
    async def get_security_events(
        self, limit: int = 100, offset: int = 0,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
        outcome: Optional[str] = None
    ) -> List[AuditLogEntry]:
        """Get security-related events."""
        ...
    
    @abstractmethod
    async def get_data_access_events(
        self, limit: int = 100, offset: int = 0,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[AuditLogEntry]:
        """Get PII/sensitive data access events."""
        ...
    
    @abstractmethod
    async def get_failed_events(
        self, limit: int = 100, offset: int = 0,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None
    ) -> List[AuditLogEntry]:
        """Get failed events."""
        ...
    
    # =========================================================================
    # AGGREGATION
    # =========================================================================
    
    @abstractmethod
    async def count_by_user(
        self, user_id: UUID,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> int:
        """Count entries for user."""
        ...
    
    @abstractmethod
    async def count_by_event_type(
        self, event_type: AuditEventType,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> int:
        """Count entries by event type."""
        ...
    
    # =========================================================================
    # COMPLIANCE
    # =========================================================================
    
    @abstractmethod
    async def delete_old_entries(
        self, retention_days: int, exclude_critical: bool = True
    ) -> int:
        """Delete old entries (respecting retention for critical events)."""
        ...
    
    @abstractmethod
    async def get_compliance_report(
        self, start_date: datetime, end_date: datetime,
        event_types: Optional[List[AuditEventType]] = None
    ) -> List[AuditLogEntry]:
        """Get logs for compliance reporting."""
        ...
```

### SQLAlchemy Adapter

**Location**: `src/app/infrastructure/adapters/chat/audit_log_repository_adapter.py`

```python
class AuditLogRepositoryAdapter(AuditLogRepository):
    """
    SQLAlchemy adapter for audit logs.
    
    Optimized for high-volume logging with JSONB metadata storage
    and indexed queries for compliance reporting.
    """
    
    def __init__(self, session: MainAsyncSession) -> None:
        self._session = session
    
    async def save(self, entry: AuditLogEntry) -> AuditLogEntry:
        model = self._to_model(entry)
        self._session.add(model)
        await self._session.commit()
        return entry
    
    # ... other methods implement the port
```

---

## 4. Database Schema

### audit_logs Table

**Migration**: `src/app/infrastructure/persistence_sqla/alembic/versions/2025_12_16_0001-add_audit_logs_table.py`

```sql
CREATE TABLE audit_logs (
    entry_id UUID PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    action VARCHAR(200) NOT NULL,
    outcome VARCHAR(20) NOT NULL,
    
    -- Context
    user_id UUID,
    resource_id UUID,
    resource_type VARCHAR(50),
    
    -- Flexible metadata (JSONB)
    metadata JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Error details
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Single-column indexes
CREATE INDEX ix_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX ix_audit_logs_outcome ON audit_logs(outcome);
CREATE INDEX ix_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX ix_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX ix_audit_logs_ip_address ON audit_logs(ip_address);
CREATE INDEX ix_audit_logs_created_at ON audit_logs(created_at);

-- Composite indexes for common query patterns
CREATE INDEX ix_audit_logs_user_created ON audit_logs(user_id, created_at);
CREATE INDEX ix_audit_logs_event_created ON audit_logs(event_type, created_at);
CREATE INDEX ix_audit_logs_event_outcome ON audit_logs(event_type, outcome);
CREATE INDEX ix_audit_logs_ip_created ON audit_logs(ip_address, created_at);
CREATE INDEX ix_audit_logs_resource ON audit_logs(resource_id, resource_type);
```

---

## 5. Telemetry Collectors

### LLM Telemetry Collector

**Location**: `src/app/domain/services/llm/telemetry_collector.py`

```python
class TelemetryCollector:
    """
    Collects LLM orchestration metrics.
    
    Metrics:
    - Request count (by endpoint, provider, model)
    - Request duration
    - Error count (by type)
    - Cost tracking
    - Token usage
    - Cache hit rate
    - Retry rate
    """
    
    async def record_request(
        self,
        request_id: str,
        agent_type: str,
        provider_name: str,
        model_name: str,
        status: str,
        latency_ms: int,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
        attempt_count: int = 1,
        error_type: Optional[str] = None,
    ): ...
    
    async def record_cache_hit(self): ...
    async def record_cache_miss(self): ...
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return {
            "uptime_seconds": ...,
            "timestamp": ...,
            "requests": {
                "total": ...,
                "by_key": ...,
                "avg_duration_ms": ...,
            },
            "errors": {
                "total": ...,
                "by_type": ...,
            },
            "cost": {
                "total_usd": ...,
                "avg_per_request": ...,
            },
            "tokens": {
                "input": ...,
                "output": ...,
                "total": ...,
            },
            "cache": {
                "hits": ...,
                "misses": ...,
                "hit_rate": ...,
            },
            "retry_rate": ...,
        }
```

### Retry Telemetry Collector

**Location**: `src/app/domain/services/retry/telemetry_collector.py`

```python
class RetryTelemetryCollector:
    """
    Telemetry for retry system.
    
    Tracks:
    - Retry attempts and outcomes
    - Circuit breaker state changes
    - Service overrides
    - Performance metrics
    """
    
    async def record_attempt_start(
        self, service_name: str, attempt_number: int,
        context: Optional[Dict] = None,
    ): ...
    
    async def record_success(
        self, service_name: str, attempt_number: int,
        latency_ms: int, context: Optional[Dict] = None,
    ): ...
    
    async def record_failure(
        self, service_name: str, attempt_number: int,
        error_type: str, error_message: str,
        context: Optional[Dict] = None,
    ): ...
    
    async def record_circuit_state_change(
        self, service_name: str, from_state: str, to_state: str,
        reason: str, failure_count: int = 0, success_count: int = 0,
    ): ...
    
    async def record_service_override(
        self, service_name: str, action: str,  # 'enable' or 'disable'
        user_id: UUID, reason: str,
        duration_minutes: Optional[int] = None,
    ): ...
```

### API Telemetry

**Location**: `src/app/infrastructure/telemetry/api_telemetry.py`

```python
class APITelemetry:
    """
    Enterprise-grade API telemetry.
    
    Features:
    - Request/response tracking with timing
    - Error categorization and rate tracking
    - Rate limit detection and handling
    - Cost estimation per API
    - Percentile latency (p50, p95, p99)
    - Real-time alerting
    - Async recording
    """
    
    def start_call(self, api: str, operation: str, **params) -> APICallContext:
        """Start tracking API call."""
        ...
    
    async def record(self, ctx: APICallContext):
        """Record completed call."""
        ...
    
    def get_metrics(self, api: Optional[str] = None) -> dict:
        """Get metrics (all or specific API)."""
        ...
    
    def get_all_metrics(self) -> dict:
        """Comprehensive metrics summary."""
        return {
            "summary": {
                "total_requests": ...,
                "total_errors": ...,
                "overall_error_rate": ...,
                "total_estimated_cost_usd": ...,
                "apis_tracked": ...,
            },
            "by_api": {...},
        }
    
    def get_slow_calls(self, threshold_ms: float = 1000, limit: int = 10) -> list:
        """Get slowest API calls."""
        ...
    
    def get_errors(self, api: Optional[str] = None, limit: int = 20) -> list:
        """Get recent errors."""
        ...
```

### API Cost Configuration

```python
@dataclass
class TelemetryConfig:
    # Cost per 1000 requests
    api_costs: dict = field(default_factory=lambda: {
        "coingecko": 0.0,      # Free tier
        "defillama": 0.0,      # Free
        "oneinch": 0.05,       # ~$49/mo for 10 req/sec
        "thegraph": 0.10,      # ~$99/mo
        "etherscan": 0.02,
        "hyperliquid": 0.0,
        "forta": 0.03,
        "chainalysis": 2.0,    # Enterprise
        "trm_labs": 2.0,
        "opensea": 0.01,
        "snapshot": 0.0,
        "axelar": 0.0,
        "layerzero": 0.0,
        "twilio": 0.0075,      # Per SMS
        "privy": 0.01,
    })
```

---

## 6. Distributed Tracing

### TracingService

**Location**: `src/app/infrastructure/telemetry/tracing.py`

OpenTelemetry-compatible distributed tracing.

```python
class TracingService:
    """
    Distributed tracing service.
    
    Integrates with:
    - Jaeger
    - Zipkin
    - Datadog
    - AWS X-Ray
    """
    
    def __init__(
        self,
        service_name: str = "anvil-backend",
        enabled: bool = True,
        sample_rate: float = 1.0,
        max_spans: int = 10000,
    ): ...
    
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[dict] = None,
    ) -> SpanContextManager:
        """Start new span."""
        ...
    
    def get_trace(self, trace_id: str) -> list[dict]:
        """Get all spans for a trace."""
        ...
    
    def get_recent_traces(self, limit: int = 20) -> list[dict]:
        """Get recent traces."""
        ...
    
    def get_slow_traces(self, threshold_ms: float = 1000, limit: int = 10) -> list[dict]:
        """Get slowest traces."""
        ...
    
    def inject_context(self, headers: dict) -> dict:
        """Inject trace context for propagation (W3C Trace Context)."""
        ...
    
    def extract_context(self, headers: dict) -> Optional[SpanContext]:
        """Extract trace context from headers."""
        ...
```

### SpanContext

```python
@dataclass
class SpanContext:
    """OpenTelemetry-compatible span context."""
    
    trace_id: str  # 32 hex chars
    span_id: str   # 16 hex chars
    parent_span_id: Optional[str] = None
    
    name: str = ""
    kind: SpanKind = SpanKind.INTERNAL
    
    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # Status
    status: SpanStatus = SpanStatus.UNSET
    status_message: Optional[str] = None
    
    # Attributes
    attributes: dict = field(default_factory=dict)
    
    # Events (logs within span)
    events: list = field(default_factory=list)
    
    def set_attribute(self, key: str, value: Any): ...
    def add_event(self, name: str, attributes: dict = None): ...
    def set_status(self, status: SpanStatus, message: str = None): ...
    def end(self): ...
    
    def to_w3c_traceparent(self) -> str:
        """Generate W3C Trace Context header."""
        return f"00-{self.trace_id}-{self.span_id}-01"
```

### Usage Example

```python
tracing = TracingService()

# Start a trace
with tracing.start_span("api_call", kind=SpanKind.CLIENT) as span:
    span.set_attribute("api", "coingecko")
    span.set_attribute("operation", "get_price")
    
    try:
        result = await api_call()
        span.add_event("response_received", {"size": len(result)})
    except Exception as e:
        span.set_status(SpanStatus.ERROR, str(e))
        raise

# Get trace for debugging
trace = tracing.get_trace(trace_id)
```

---

## 7. Security Dashboard

### SecurityDashboardService

**Location**: `src/app/infrastructure/security/dashboard_service.py`

```python
class SecurityDashboardService:
    """
    Aggregates security metrics from all defense middleware.
    
    Provides:
    - Attack statistics (XSS, Prompt Injection)
    - Transaction approval metrics
    - PII protection stats
    - Agent isolation violations
    - Security scan results
    - Overall security posture
    """
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        return {
            "timestamp": ...,
            "security_posture": self._get_security_posture(),
            "attack_statistics": self._get_attack_statistics(),
            "transaction_approvals": self._get_transaction_approval_stats(),
            "pii_protection": self._get_pii_protection_stats(),
            "agent_isolation": self._get_agent_isolation_stats(),
            "scan_results": self._get_latest_scan_results(),
            "vulnerability_summary": self._get_vulnerability_summary(),
            "active_security_tools": self._get_active_security_tools(),
        }
```

### Security Posture Score

```python
def _get_security_posture(self) -> Dict[str, Any]:
    """
    Calculate overall security posture (0-100).
    
    Score calculation:
    - Base: 100
    - -10 per critical vulnerability
    - -5 per high severity vulnerability
    - -2 per medium severity vulnerability
    - -10 per agent isolation violation
    - +5 for high block rate (>95%)
    
    Levels:
    - EXCELLENT: 90-100
    - GOOD: 75-89
    - FAIR: 60-74
    - POOR: 40-59
    - CRITICAL: 0-39
    """
    ...
```

### Admin Endpoints

**Location**: `src/app/presentation/http/controllers/admin/security_router.py`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/admin/security/dashboard` | Full dashboard summary |
| `GET /api/v1/admin/security/scans/latest` | Latest security scan results |
| `GET /api/v1/admin/security/scans/{scan_id}` | Specific scan details |
| `GET /api/v1/admin/security/trends` | Vulnerability trends (1-90 days) |
| `GET /api/v1/admin/security/posture` | Current security posture score |
| `GET /api/v1/admin/security/attacks` | 24-hour attack statistics |
| `GET /api/v1/admin/security/approvals` | Transaction approval stats |
| `GET /api/v1/admin/security/pii-protection` | PII redaction statistics |
| `GET /api/v1/admin/security/agent-isolation` | Agent isolation stats |
| `GET /api/v1/admin/security/tools` | Active security tools status |

---

## 8. Usage Examples

### Creating Audit Log Entry

```python
from app.domain.entities.chat.audit_log import AuditLogEntry
from app.domain.enums.audit_event_type import AuditEventType

# Create entry
entry = AuditLogEntry(
    event_type=AuditEventType.USER_LOGIN,
    action="user_authenticated",
    outcome="success",
    user_id=user.id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    metadata={
        "auth_method": "privy",
        "wallet_address": wallet_address,
    },
)

# Save via repository
await audit_log_repository.save(entry)
```

### Recording Failed Event

```python
entry = AuditLogEntry(
    event_type=AuditEventType.AUTH_FAILURE,
    action="login_attempt_failed",
    ip_address=request.client.host,
    metadata={"email": email},
)
entry.with_error("Invalid credentials", error_code="INVALID_CREDS")

await audit_log_repository.save(entry)
```

### Querying Security Events

```python
# Get failed auth attempts in last 24 hours
from datetime import datetime, timedelta

entries = await audit_log_repository.get_security_events(
    limit=100,
    start_date=datetime.utcnow() - timedelta(hours=24),
    outcome="failure",
)

# Get events from suspicious IP
entries = await audit_log_repository.get_by_ip_address(
    ip_address="192.168.1.100",
    start_date=datetime.utcnow() - timedelta(hours=1),
)
```

### Compliance Reporting

```python
# Generate compliance report for Q4
report_entries = await audit_log_repository.get_compliance_report(
    start_date=datetime(2025, 10, 1),
    end_date=datetime(2025, 12, 31),
    event_types=[
        AuditEventType.PII_VIEW,
        AuditEventType.PII_EXPORT,
        AuditEventType.ADMIN_USER_DELETION,
    ],
)
```

### Retention Cleanup

```python
# Delete entries older than 90 days (excluding security/compliance events)
deleted_count = await audit_log_repository.delete_old_entries(
    retention_days=90,
    exclude_critical=True,  # Preserve security, data access, admin events
)
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Entity** | `domain/entities/chat/audit_log.py` | AuditLogEntry entity |
| **Entity (Alt)** | `domain/entities/system/audit_log.py` | System AuditLog entity |
| **Enum** | `domain/enums/audit_event_type.py` | 45+ event types |
| **Port** | `domain/ports/audit_log_repository.py` | Repository interface |
| **Adapter** | `infrastructure/adapters/chat/audit_log_repository_adapter.py` | SQLAlchemy impl |
| **Migration** | `persistence_sqla/alembic/versions/2025_12_16_0001-add_audit_logs_table.py` | DB schema |
| **LLM Telemetry** | `domain/services/llm/telemetry_collector.py` | LLM metrics |
| **Retry Telemetry** | `domain/services/retry/telemetry_collector.py` | Retry/circuit metrics |
| **API Telemetry** | `infrastructure/telemetry/api_telemetry.py` | External API metrics |
| **Tracing** | `infrastructure/telemetry/tracing.py` | Distributed tracing |
| **Dashboard** | `infrastructure/security/dashboard_service.py` | Security dashboard |
| **Admin API** | `presentation/http/controllers/admin/security_router.py` | Security endpoints |

---

## Compliance Features

### GDPR Compliance

| Requirement | Implementation |
|-------------|----------------|
| **Data Access Logging** | `PII_VIEW`, `PII_EXPORT`, `SENSITIVE_DATA_ACCESS` events |
| **Retention Control** | Configurable retention with `delete_old_entries()` |
| **Right to Erasure** | `ADMIN_USER_DELETION` tracking |
| **Data Portability** | `EXPORT_REQUEST`, `EXPORT_DOWNLOAD` tracking |

### CCPA Compliance

| Requirement | Implementation |
|-------------|----------------|
| **Access Requests** | `PII_VIEW` event logging |
| **Deletion Requests** | `ADMIN_USER_DELETION` with metadata |
| **Opt-Out Tracking** | `USER_PREFERENCE_CHANGE` events |

### SOC 2 Type II

| Control | Implementation |
|---------|----------------|
| **CC6.1 (Access Control)** | `AUTH_*`, `PERMISSION_DENIED` events |
| **CC7.1 (Change Management)** | `SYSTEM_CONFIGURATION_CHANGE`, `ADMIN_*` events |
| **CC7.2 (Incident Response)** | `SUSPICIOUS_ACTIVITY`, security dashboard |

---

## Best Practices

### 1. Always Log Security Events

```python
# ✅ DO: Log authentication attempts
if auth_success:
    await log(AuditEventType.AUTH_SUCCESS, ...)
else:
    await log(AuditEventType.AUTH_FAILURE, ...)
```

### 2. Include Context Metadata

```python
# ✅ DO: Include relevant metadata
entry = AuditLogEntry(
    event_type=AuditEventType.PII_EXPORT,
    action="export_user_data",
    metadata={
        "export_format": "csv",
        "fields_included": ["email", "wallet_address"],
        "requester_role": "admin",
    },
)
```

### 3. Use Appropriate Retention

```python
# ✅ DO: Respect retention requirements
await audit_log_repository.delete_old_entries(
    retention_days=90,
    exclude_critical=True,  # Keep security/compliance events longer
)
```

### 4. Never Log Sensitive Data

```python
# ❌ DON'T: Log passwords or private keys
metadata={"password": password}  # NEVER DO THIS

# ✅ DO: Log references, not values
metadata={"password_changed": True}
```

---

**Last Updated**: January 2, 2026
