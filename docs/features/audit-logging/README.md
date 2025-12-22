# Audit Logging System

Enterprise-grade audit logging for compliance, security tracking, and forensic analysis.

## Overview

The audit logging system provides comprehensive tracking of:
- **User Actions**: Login, profile changes, exports, preferences
- **System Events**: Agent executions, background jobs, configuration changes
- **Security Events**: Authentication failures, unauthorized access, rate limiting
- **Data Access**: PII viewing, sensitive data exports, bulk operations

## Architecture

### Hexagonal Architecture Implementation

```
Domain Layer:
├── entities/chat/audit_log.py          # AuditLogEntry entity
├── enums/audit_event_type.py           # Event type enumeration
└── ports/audit_log_repository.py       # Repository interface

Infrastructure Layer:
└── adapters/chat/audit_log_repository_adapter.py  # PostgreSQL adapter
```

### Key Components

1. **AuditLogEntry Entity** (`domain/entities/chat/audit_log.py`)
   - Immutable audit log entry with timestamp
   - Rich metadata support via JSONB
   - Built-in validation and type safety

2. **AuditEventType Enum** (`domain/enums/audit_event_type.py`)
   - 60+ predefined event types
   - Categorized by domain (user, security, data access, system)
   - Properties for classification (is_security_event, requires_retention)

3. **AuditLogRepository Port** (`domain/ports/audit_log_repository.py`)
   - Domain-defined interface for persistence
   - Comprehensive query methods for compliance reporting
   - Retention policy support

4. **PostgreSQL Adapter** (`infrastructure/adapters/chat/audit_log_repository_adapter.py`)
   - Optimized for high-volume logging
   - Indexed for efficient querying
   - JSONB for flexible metadata storage

## Database Schema

### Table: `audit_logs`

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

    -- Additional Data
    metadata JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- Error Details
    error_message TEXT,
    error_code VARCHAR(50),

    -- Timestamp (immutable, indexed)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

Optimized for common query patterns:

1. **User Activity**: `(user_id, created_at)` - User-specific audit trails
2. **Event Type Queries**: `(event_type, created_at)` - Time-range filtering
3. **Security Monitoring**: `(event_type, outcome)` - Failed security events
4. **IP-Based Queries**: `(ip_address, created_at)` - Suspicious activity detection
5. **Resource Activity**: `(resource_id, resource_type)` - Resource access history

## Event Types

### User Actions (16 events)
- `USER_LOGIN`, `USER_LOGOUT`, `USER_REGISTRATION`
- `USER_PROFILE_UPDATE`, `USER_PREFERENCE_CHANGE`
- `USER_PASSWORD_CHANGE`, `USER_EMAIL_CHANGE`, `USER_ROLE_CHANGE`
- `EXPORT_REQUEST`, `EXPORT_DOWNLOAD`, `EXPORT_DELETION`
- `CONVERSATION_CREATE`, `CONVERSATION_DELETE`, `CONVERSATION_SHARE`
- `MESSAGE_CREATE`, `MESSAGE_UPDATE`, `MESSAGE_DELETE`

### Template & Agent Actions (9 events)
- `TEMPLATE_CREATE`, `TEMPLATE_UPDATE`, `TEMPLATE_DELETE`, `TEMPLATE_EXECUTE`
- `AGENT_EXECUTION_START`, `AGENT_EXECUTION_COMPLETE`, `AGENT_EXECUTION_FAILED`
- `VOTING_ROUND_START`, `VOTING_ROUND_COMPLETE`

### Security Events (8 events)
- `AUTH_SUCCESS`, `AUTH_FAILURE`
- `AUTH_TOKEN_REFRESH`, `AUTH_TOKEN_REVOKE`
- `UNAUTHORIZED_ACCESS_ATTEMPT`, `PERMISSION_DENIED`
- `RATE_LIMIT_EXCEEDED`, `SUSPICIOUS_ACTIVITY`

### Data Access Events (5 events)
- `PII_VIEW`, `PII_EXPORT`, `PII_MODIFICATION`
- `SENSITIVE_DATA_ACCESS`, `BULK_DATA_EXPORT`

### System Events (6 events)
- `SYSTEM_CONFIGURATION_CHANGE`, `SYSTEM_ERROR`, `SYSTEM_WARNING`
- `BACKGROUND_JOB_START`, `BACKGROUND_JOB_COMPLETE`, `BACKGROUND_JOB_FAILED`

### Administrative Actions (6 events)
- `ADMIN_USER_SUSPENSION`, `ADMIN_USER_ACTIVATION`, `ADMIN_USER_DELETION`
- `ADMIN_ROLE_ASSIGNMENT`, `ADMIN_PERMISSION_GRANT`, `ADMIN_PERMISSION_REVOKE`

## Features

### 1. Flexible Metadata Storage

Store arbitrary metadata using JSONB:

```python
entry = AuditLogEntry(
    event_type=AuditEventType.AGENT_EXECUTION_COMPLETE,
    action="Execute trading agent",
    metadata={
        "agent_type": "trading",
        "model": "gpt-4",
        "tokens_used": 1500,
        "execution_time_ms": 2300,
        "result": "success"
    }
)
```

### 2. Compliance Reporting

Generate reports for GDPR, HIPAA, SOC2, etc.:

```python
# Get all PII access for compliance audit
entries = await audit_repo.get_data_access_events(
    start_date=quarter_start,
    end_date=quarter_end
)

# Generate custom compliance report
entries = await audit_repo.get_compliance_report(
    start_date=year_start,
    end_date=year_end,
    event_types=[
        AuditEventType.PII_VIEW,
        AuditEventType.PII_EXPORT,
        AuditEventType.BULK_DATA_EXPORT
    ]
)
```

### 3. Security Monitoring

Detect and respond to security threats:

```python
# Monitor failed authentication attempts
failed_auths = await audit_repo.get_security_events(
    outcome="failure",
    start_date=datetime.utcnow() - timedelta(hours=1)
)

# Track suspicious IP activity
ip_events = await audit_repo.get_by_ip_address(
    ip_address="192.168.1.100",
    start_date=datetime.utcnow() - timedelta(hours=24)
)
```

### 4. Retention Policies

Automated cleanup with configurable retention:

```python
# Delete old logs, preserving critical events
deleted_count = await audit_repo.delete_old_entries(
    retention_days=90,
    exclude_critical=True  # Preserve security/PII events
)
```

**Retention Tiers**:
- Standard events: 90 days
- Security events: 730 days (2 years)
- Data access events: 730 days (2 years)
- Administrative actions: 730 days (2 years)

### 5. High-Performance Batch Operations

Efficient logging for high-volume scenarios:

```python
entries = [
    AuditLogEntry(...),
    AuditLogEntry(...),
    # ... hundreds of entries
]

await audit_repo.save_batch(entries)
```

## Usage

### Basic Logging

```python
from app.domain.entities.chat.audit_log import AuditLogEntry
from app.domain.enums.audit_event_type import AuditEventType
from app.domain.ports.audit_log_repository import AuditLogRepository

# Inject repository via Dishka
async def some_handler(audit_repo: AuditLogRepository, user_id: UUID):
    # Log the operation
    entry = AuditLogEntry(
        event_type=AuditEventType.USER_LOGIN,
        action="User login via email/password",
        outcome="success",
        user_id=user_id,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 ..."
    )

    await audit_repo.save(entry)
```

### Querying Logs

```python
# User activity trail
user_logs = await audit_repo.get_by_user(
    user_id=user_id,
    limit=100,
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31)
)

# Security events
security_logs = await audit_repo.get_security_events(
    outcome="failure",
    limit=50
)

# Resource access history
resource_logs = await audit_repo.get_by_resource(
    resource_id=conversation_id,
    resource_type="conversation"
)
```

### Error Handling

```python
try:
    # Perform sensitive operation
    result = await perform_sensitive_operation()

    # Log success
    entry = AuditLogEntry(
        event_type=AuditEventType.PII_EXPORT,
        action="Export user PII data",
        outcome="success",
        user_id=admin_user_id,
        resource_id=target_user_id
    )
    await audit_repo.save(entry)

except Exception as e:
    # Log failure with error details
    entry = AuditLogEntry(
        event_type=AuditEventType.PII_EXPORT,
        action="Export user PII data",
        outcome="failure",
        user_id=admin_user_id,
        resource_id=target_user_id,
        error_message=str(e),
        error_code=type(e).__name__
    )
    await audit_repo.save(entry)
    raise
```

## Migration

Apply the database migration:

```bash
# Ensure database is running
make up.db

# Run migration
alembic upgrade head
```

Migration file: `2025_12_16_0001-add_audit_logs_table.py`

## Dependency Injection

The repository is automatically registered in the Dishka container:

```python
# src/app/setup/ioc/infrastructure.py

audit_log_repo = provide(
    source=AuditLogRepositoryAdapter,
    provides=AuditLogRepository,
    scope=Scope.REQUEST,
)
```

Inject in handlers, interactors, or services:

```python
class SomeInteractor:
    def __init__(self, audit_repo: AuditLogRepository):
        self._audit_repo = audit_repo
```

## Performance Considerations

### Write Performance
- Asynchronous writes with SQLAlchemy async
- Batch operations for bulk logging
- Minimal validation overhead

### Read Performance
- Optimized composite indexes
- Query result pagination
- Efficient time-range filtering

### Storage Optimization
- JSONB for flexible metadata
- Automatic cleanup via retention policies
- Index-only scans for common queries

## Compliance Support

### GDPR
- Track all PII access with `PII_VIEW`, `PII_EXPORT`, `PII_MODIFICATION`
- Generate data access reports
- Audit trail for data deletion requests

### HIPAA
- Log all PHI access with detailed metadata
- Preserve audit logs for required retention period
- Monitor unauthorized access attempts

### SOC 2
- Comprehensive security event logging
- User activity tracking
- System configuration change auditing

### ISO 27001
- Access control monitoring
- Incident detection and response
- Audit trail for security events

## Monitoring & Alerting

Recommended alerts:

1. **Failed Authentication Spike**: >10 failures from single IP in 1 hour
2. **Suspicious Access Pattern**: Multiple PII views from single user
3. **Unauthorized Access Attempts**: Any `PERMISSION_DENIED` events
4. **Rate Limiting**: Excessive `RATE_LIMIT_EXCEEDED` events
5. **System Errors**: Critical `SYSTEM_ERROR` events

## Testing

Unit tests for domain logic:
```bash
pytest tests/unit/domain/entities/test_audit_log.py
```

Integration tests for adapter:
```bash
pytest tests/integration/adapters/test_audit_log_repository_adapter.py
```

## Best Practices

1. **Log Everything Important**: When in doubt, log it
2. **Include Context**: IP address, user agent, metadata
3. **Use Appropriate Event Types**: Choose the most specific type
4. **Handle Failures Gracefully**: Don't let logging block operations
5. **Monitor Regularly**: Set up dashboards and alerts
6. **Preserve Critical Events**: Never delete security/PII logs
7. **Review Periodically**: Audit logs are only useful if reviewed

## Future Enhancements

- [ ] Real-time streaming to SIEM systems
- [ ] Advanced anomaly detection
- [ ] Machine learning for threat detection
- [ ] Elasticsearch integration for advanced search
- [ ] GraphQL API for log querying
- [ ] Automated compliance report generation
- [ ] Webhook notifications for critical events

## See Also

- [Usage Examples](./USAGE_EXAMPLES.md) - Comprehensive code examples
- [Event Types Reference](../../domain/enums/audit_event_type.py) - All event types
- [Database Schema](../../../infrastructure/persistence_sqla/alembic/versions/2025_12_16_0001-add_audit_logs_table.py) - Migration file
