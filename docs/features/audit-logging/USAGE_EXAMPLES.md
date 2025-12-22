# Audit Logging Usage Examples

This document provides comprehensive examples of using the audit logging system for compliance and security tracking.

## Overview

The audit logging system tracks:
- User actions (login, exports, preferences)
- System events (agent executions, background jobs)
- Security events (auth failures, unauthorized access)
- Data access (PII viewing, sensitive data exports)

## Basic Usage

### 1. Logging User Actions

```python
from uuid import uuid4
from app.domain.entities.chat.audit_log import AuditLogEntry
from app.domain.enums.audit_event_type import AuditEventType
from app.domain.ports.audit_log_repository import AuditLogRepository

async def log_user_login(
    audit_repo: AuditLogRepository,
    user_id: UUID,
    ip_address: str,
    user_agent: str,
    success: bool = True
) -> None:
    """Log a user login attempt."""
    entry = AuditLogEntry(
        event_type=AuditEventType.USER_LOGIN,
        action="User login attempt",
        outcome="success" if success else "failure",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={
            "login_method": "email_password",
            "session_duration": "24h"
        }
    )

    await audit_repo.save(entry)
```

### 2. Logging Export Requests

```python
async def log_export_request(
    audit_repo: AuditLogRepository,
    user_id: UUID,
    conversation_id: UUID,
    export_format: str,
    includes_pii: bool
) -> None:
    """Log a conversation export request."""
    entry = AuditLogEntry(
        event_type=AuditEventType.EXPORT_REQUEST,
        action=f"Export conversation to {export_format}",
        outcome="success",
        user_id=user_id,
        resource_id=conversation_id,
        resource_type="conversation",
        metadata={
            "export_format": export_format,
            "includes_pii": includes_pii,
            "redacted": not includes_pii
        }
    )

    await audit_repo.save(entry)
```

### 3. Logging Security Events

```python
async def log_unauthorized_access(
    audit_repo: AuditLogRepository,
    user_id: UUID,
    resource_id: UUID,
    resource_type: str,
    ip_address: str
) -> None:
    """Log an unauthorized access attempt."""
    entry = AuditLogEntry(
        event_type=AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
        action=f"Attempted to access {resource_type}",
        outcome="failure",
        user_id=user_id,
        resource_id=resource_id,
        resource_type=resource_type,
        ip_address=ip_address,
        error_message="User does not have permission to access this resource"
    )

    await audit_repo.save(entry)
```

### 4. Logging Agent Executions

```python
async def log_agent_execution(
    audit_repo: AuditLogRepository,
    user_id: UUID,
    agent_type: str,
    execution_id: UUID,
    success: bool,
    execution_time_ms: int
) -> None:
    """Log an agent execution."""
    entry = AuditLogEntry(
        event_type=AuditEventType.AGENT_EXECUTION_COMPLETE if success
                    else AuditEventType.AGENT_EXECUTION_FAILED,
        action=f"Execute {agent_type} agent",
        outcome="success" if success else "failure",
        user_id=user_id,
        resource_id=execution_id,
        resource_type="agent_execution",
        metadata={
            "agent_type": agent_type,
            "execution_time_ms": execution_time_ms,
            "model_used": "gpt-4"
        }
    )

    await audit_repo.save(entry)
```

### 5. Logging PII Access

```python
async def log_pii_access(
    audit_repo: AuditLogRepository,
    user_id: UUID,
    viewed_user_id: UUID,
    pii_fields: List[str],
    ip_address: str
) -> None:
    """Log PII data access."""
    entry = AuditLogEntry(
        event_type=AuditEventType.PII_VIEW,
        action="View user PII data",
        outcome="success",
        user_id=user_id,
        resource_id=viewed_user_id,
        resource_type="user",
        ip_address=ip_address,
        metadata={
            "pii_fields_accessed": pii_fields,
            "reason": "customer_support_ticket"
        }
    )

    await audit_repo.save(entry)
```

## Querying Audit Logs

### 1. Get User Activity

```python
from datetime import datetime, timedelta

async def get_user_activity_report(
    audit_repo: AuditLogRepository,
    user_id: UUID,
    days: int = 30
) -> List[AuditLogEntry]:
    """Get all activity for a user in the last N days."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    entries = await audit_repo.get_by_user(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=1000
    )

    return entries
```

### 2. Get Security Events

```python
async def get_recent_auth_failures(
    audit_repo: AuditLogRepository,
    hours: int = 24
) -> List[AuditLogEntry]:
    """Get all authentication failures in the last N hours."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=hours)

    entries = await audit_repo.get_security_events(
        outcome="failure",
        start_date=start_date,
        end_date=end_date,
        limit=500
    )

    return entries
```

### 3. Get Data Access Events

```python
async def get_pii_access_report(
    audit_repo: AuditLogRepository,
    start_date: datetime,
    end_date: datetime
) -> List[AuditLogEntry]:
    """Get all PII access events for compliance reporting."""
    entries = await audit_repo.get_data_access_events(
        start_date=start_date,
        end_date=end_date,
        limit=10000
    )

    return entries
```

### 4. Monitor IP Address Activity

```python
async def check_suspicious_ip_activity(
    audit_repo: AuditLogRepository,
    ip_address: str,
    hours: int = 1
) -> dict:
    """Check for suspicious activity from an IP address."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=hours)

    entries = await audit_repo.get_by_ip_address(
        ip_address=ip_address,
        start_date=start_date,
        end_date=end_date
    )

    # Analyze for suspicious patterns
    failed_logins = sum(
        1 for e in entries
        if e.event_type == AuditEventType.AUTH_FAILURE
    )

    return {
        "total_events": len(entries),
        "failed_logins": failed_logins,
        "is_suspicious": failed_logins > 5
    }
```

### 5. Generate Compliance Report

```python
async def generate_gdpr_compliance_report(
    audit_repo: AuditLogRepository,
    start_date: datetime,
    end_date: datetime
) -> List[AuditLogEntry]:
    """Generate GDPR compliance report for data access."""
    # Get all data access and PII events
    event_types = [
        AuditEventType.PII_VIEW,
        AuditEventType.PII_EXPORT,
        AuditEventType.PII_MODIFICATION,
        AuditEventType.EXPORT_REQUEST,
        AuditEventType.USER_PROFILE_UPDATE
    ]

    entries = await audit_repo.get_compliance_report(
        start_date=start_date,
        end_date=end_date,
        event_types=event_types
    )

    return entries
```

## Advanced Usage

### Batch Logging for Performance

```python
async def log_bulk_operations(
    audit_repo: AuditLogRepository,
    user_id: UUID,
    operations: List[dict]
) -> None:
    """Log multiple operations in a single batch."""
    entries = [
        AuditLogEntry(
            event_type=AuditEventType(op["event_type"]),
            action=op["action"],
            outcome="success",
            user_id=user_id,
            resource_id=op.get("resource_id"),
            resource_type=op.get("resource_type"),
            metadata=op.get("metadata", {})
        )
        for op in operations
    ]

    await audit_repo.save_batch(entries)
```

### Error Handling with Audit Logging

```python
async def execute_with_audit(
    audit_repo: AuditLogRepository,
    user_id: UUID,
    operation: Callable,
    event_type: AuditEventType,
    action_description: str
) -> Any:
    """Execute an operation with automatic audit logging."""
    try:
        result = await operation()

        # Log success
        entry = AuditLogEntry(
            event_type=event_type,
            action=action_description,
            outcome="success",
            user_id=user_id
        )
        await audit_repo.save(entry)

        return result

    except Exception as e:
        # Log failure with error details
        entry = AuditLogEntry(
            event_type=event_type,
            action=action_description,
            outcome="failure",
            user_id=user_id,
            error_message=str(e),
            error_code=type(e).__name__
        )
        await audit_repo.save(entry)
        raise
```

## Retention Policy Implementation

### Cleanup Task

```python
from celery import shared_task

@shared_task
async def cleanup_old_audit_logs(retention_days: int = 90) -> int:
    """
    Celery task to clean up old audit logs.

    Runs daily to maintain compliance with retention policies.
    Critical events (security, PII access) are preserved longer.
    """
    from app.setup.ioc import get_container

    container = get_container()
    audit_repo = await container.get(AuditLogRepository)

    # Delete old entries, but preserve critical events
    deleted_count = await audit_repo.delete_old_entries(
        retention_days=retention_days,
        exclude_critical=True  # Preserve security/PII events
    )

    return deleted_count
```

## Integration with FastAPI

### Middleware for Automatic Logging

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log HTTP requests."""

    async def dispatch(self, request: Request, call_next):
        # Get dependencies
        audit_repo = request.state.audit_repo
        user_id = getattr(request.state, "user_id", None)

        # Log request
        if user_id and request.url.path.startswith("/api/"):
            entry = AuditLogEntry(
                event_type=AuditEventType.SENSITIVE_DATA_ACCESS,
                action=f"{request.method} {request.url.path}",
                outcome="pending",
                user_id=user_id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                metadata={
                    "method": request.method,
                    "path": request.url.path
                }
            )
            await audit_repo.save(entry)

        response = await call_next(request)
        return response
```

## Best Practices

1. **Always log security events**: Authentication, authorization, and access control
2. **Include context**: IP addresses, user agents, and metadata for forensics
3. **Use batch operations**: For high-volume logging scenarios
4. **Implement retention policies**: Balance compliance needs with storage costs
5. **Monitor failed events**: Set up alerts for security anomalies
6. **Preserve critical events**: Never delete security or PII access logs
7. **Regular audits**: Review logs regularly for compliance and security

## Configuration

### Environment Variables

```toml
# config/local/config.toml

[audit_logging]
enabled = true
retention_days = 90
critical_retention_days = 730  # 2 years for security/PII events
batch_size = 100
```

### Celery Task Schedule

```python
# Configure in Celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'cleanup-audit-logs': {
        'task': 'cleanup_old_audit_logs',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': (90,)  # 90 days retention
    }
}
```
