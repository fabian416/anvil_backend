# Retry & Resilience Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Recommended Implementation  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Retry & Resilience system currently has **no dedicated Celery tasks**. The system operates primarily through:
- **Synchronous retry logic** in the RetryEngine
- **Redis-backed state** for circuit breakers and service overrides
- **Database persistence** for telemetry through direct repository calls

This document outlines **recommended Celery tasks** for enhanced observability and maintenance.

---

## 1. Current State

### No Existing Celery Tasks

The retry system currently operates without background tasks:
- **RetryEngine** executes retries synchronously within request context
- **CircuitBreaker** updates Redis state in real-time
- **TelemetryCollector** writes to database during request processing
- **ServiceRegistry** uses Redis with TTL for auto-expiry

### Current Telemetry Flow (Synchronous)
```
Request → RetryEngine → Success/Failure → TelemetryCollector → DB Write
                              ↓
                      CircuitBreaker (Redis state update)
```

---

## 2. Recommended Celery Tasks

### 2.1 Aggregate Daily Retry Metrics

**Task Name**: `aggregate_retry_metrics_daily`  
**Priority**: HIGH  
**Schedule**: Daily at 3:00 AM

**Purpose**: Calculate daily aggregate metrics from raw retry attempts.

**Recommendation**:
```python
@celery_app.task(name="aggregate_retry_metrics_daily")
def aggregate_retry_metrics_daily():
    """
    Aggregate retry metrics daily for historical analysis.
    
    Calculates:
    - Total requests per service
    - Success/failure rates
    - Average/P50/P95/P99 latency
    - Retry attempt distribution
    - Circuit breaker open counts
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from datetime import datetime, timedelta, UTC
        
        session = await container.get(MainAsyncSession)
        yesterday = datetime.now(UTC).date() - timedelta(days=1)
        
        # Aggregate query from retry_attempts to retry_metrics_aggregate
        query = text("""
            INSERT INTO retry_metrics_aggregate (
                service_name, date, total_requests, successful_requests,
                failed_requests, retry_attempts, avg_latency_ms,
                p50_latency_ms, p95_latency_ms, p99_latency_ms
            )
            SELECT
                service_name,
                :date,
                COUNT(*) as total_requests,
                COUNT(*) FILTER (WHERE success = true) as successful_requests,
                COUNT(*) FILTER (WHERE success = false) as failed_requests,
                SUM(attempt_number) as retry_attempts,
                AVG(latency_ms) as avg_latency_ms,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as p50_latency_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99_latency_ms
            FROM retry_attempts
            WHERE DATE(created_at) = :date
            GROUP BY service_name
            ON CONFLICT (service_name, date) DO UPDATE SET
                total_requests = EXCLUDED.total_requests,
                successful_requests = EXCLUDED.successful_requests,
                failed_requests = EXCLUDED.failed_requests,
                avg_latency_ms = EXCLUDED.avg_latency_ms,
                updated_at = NOW()
        """)
        
        await session.execute(query, {"date": yesterday})
        
        # Count circuit breaker opens from events
        cb_query = text("""
            UPDATE retry_metrics_aggregate rma
            SET circuit_breaker_opens = (
                SELECT COUNT(*)
                FROM circuit_breaker_events cbe
                WHERE cbe.service_name = rma.service_name
                AND DATE(cbe.created_at) = rma.date
                AND cbe.to_state = 'open'
            )
            WHERE rma.date = :date
        """)
        
        await session.execute(cb_query, {"date": yesterday})
        await session.commit()
        
        print(f"[Retry Metrics] Aggregated metrics for {yesterday}")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"aggregate-retry-metrics-daily": {
    "task": "aggregate_retry_metrics_daily",
    "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
},
```

---

### 2.2 Clean Old Retry Telemetry

**Task Name**: `clean_old_retry_telemetry`  
**Priority**: MEDIUM  
**Schedule**: Weekly (Sunday at 4:00 AM)

**Purpose**: Remove old retry attempt records to manage database size.

**Recommendation**:
```python
@celery_app.task(name="clean_old_retry_telemetry")
def clean_old_retry_telemetry(retention_days: int = 30):
    """
    Clean retry telemetry data older than retention period.
    
    Keeps:
    - retry_metrics_aggregate (never deleted - historical data)
    
    Cleans:
    - retry_attempts (older than retention_days)
    - circuit_breaker_events (older than retention_days)
    - service_override_events (older than retention_days)
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from datetime import datetime, timedelta, UTC
        
        session = await container.get(MainAsyncSession)
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
        
        # Clean retry_attempts
        attempts_query = text("""
            DELETE FROM retry_attempts
            WHERE created_at < :cutoff
        """)
        result1 = await session.execute(attempts_query, {"cutoff": cutoff_date})
        deleted_attempts = result1.rowcount
        
        # Clean circuit_breaker_events
        cb_query = text("""
            DELETE FROM circuit_breaker_events
            WHERE created_at < :cutoff
        """)
        result2 = await session.execute(cb_query, {"cutoff": cutoff_date})
        deleted_cb_events = result2.rowcount
        
        # Clean service_override_events
        override_query = text("""
            DELETE FROM service_override_events
            WHERE created_at < :cutoff
        """)
        result3 = await session.execute(override_query, {"cutoff": cutoff_date})
        deleted_overrides = result3.rowcount
        
        await session.commit()
        
        print(
            f"[Retry Cleanup] Deleted {deleted_attempts} attempts, "
            f"{deleted_cb_events} CB events, {deleted_overrides} overrides "
            f"(older than {retention_days} days)"
        )
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"clean-old-retry-telemetry": {
    "task": "clean_old_retry_telemetry",
    "schedule": crontab(hour=4, minute=0, day_of_week=0),  # Sunday at 4 AM
},
```

---

### 2.3 Monitor Circuit Breaker Health

**Task Name**: `monitor_circuit_breaker_health`  
**Priority**: HIGH  
**Schedule**: Every 5 minutes

**Purpose**: Alert on open circuit breakers and extended outages.

**Recommendation**:
```python
@celery_app.task(name="monitor_circuit_breaker_health")
def monitor_circuit_breaker_health():
    """
    Monitor circuit breaker health and alert on issues.
    
    Alerts on:
    - Circuit breakers open for > 10 minutes
    - Multiple services open simultaneously
    - Services stuck in HALF_OPEN (recovery failing)
    """
    async def runner(container):
        from app.domain.services.retry.circuit_breaker import CircuitBreakerManager
        from app.infrastructure.monitoring.alerting import AlertingService
        from datetime import datetime, timedelta, UTC
        import redis
        
        redis_client = await container.get(redis.Redis)
        alert_service = await container.get(AlertingService)
        
        manager = CircuitBreakerManager(redis_client)
        statuses = manager.get_all_statuses()
        
        open_count = 0
        half_open_count = 0
        long_open_services = []
        
        threshold = datetime.now(UTC) - timedelta(minutes=10)
        
        for service_name, status in statuses.items():
            if status["state"] == "open":
                open_count += 1
                
                # Check if open for too long
                if status.get("opened_at"):
                    opened_at = datetime.fromisoformat(status["opened_at"])
                    if opened_at < threshold:
                        long_open_services.append({
                            "service": service_name,
                            "opened_at": opened_at,
                            "duration_minutes": (datetime.now(UTC) - opened_at).seconds // 60,
                        })
            
            elif status["state"] == "half_open":
                half_open_count += 1
        
        # Alert conditions
        if open_count >= 3:
            await alert_service.send_alert(
                severity="critical",
                title=f"Multiple Circuit Breakers Open: {open_count}",
                message=f"{open_count} services have open circuit breakers",
                services=[s for s, st in statuses.items() if st["state"] == "open"],
            )
        
        for service in long_open_services:
            await alert_service.send_alert(
                severity="warning",
                title=f"Extended Circuit Breaker Open: {service['service']}",
                message=f"Circuit breaker open for {service['duration_minutes']} minutes",
            )
        
        print(
            f"[CB Health] Open: {open_count}, Half-open: {half_open_count}, "
            f"Long-open: {len(long_open_services)}"
        )
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"monitor-circuit-breaker-health": {
    "task": "monitor_circuit_breaker_health",
    "schedule": crontab(minute="*/5"),  # Every 5 minutes
},
```

---

### 2.4 Sync Redis Circuit State to DB

**Task Name**: `sync_circuit_state_to_db`  
**Priority**: LOW  
**Schedule**: Hourly

**Purpose**: Persist Redis circuit breaker state to database for historical analysis.

**Recommendation**:
```python
@celery_app.task(name="sync_circuit_state_to_db")
def sync_circuit_state_to_db():
    """
    Sync current Redis circuit breaker state to database.
    
    Creates point-in-time snapshot of all circuit breaker states
    for historical analysis and dashboards.
    """
    async def runner(container):
        from app.domain.services.retry.circuit_breaker import CircuitBreakerManager
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from datetime import datetime, UTC
        import redis
        
        redis_client = await container.get(redis.Redis)
        session = await container.get(MainAsyncSession)
        
        manager = CircuitBreakerManager(redis_client)
        statuses = manager.get_all_statuses()
        
        now = datetime.now(UTC)
        
        for service_name, status in statuses.items():
            # Store state snapshot
            query = text("""
                INSERT INTO circuit_breaker_snapshots (
                    service_name, state, failure_count, success_count,
                    snapshot_at
                ) VALUES (
                    :service_name, :state, :failure_count, :success_count,
                    :snapshot_at
                )
            """)
            
            await session.execute(query, {
                "service_name": service_name,
                "state": status["state"],
                "failure_count": status["failure_count"],
                "success_count": status["success_count"],
                "snapshot_at": now,
            })
        
        await session.commit()
        print(f"[CB Sync] Synced {len(statuses)} circuit breaker states")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"sync-circuit-state-to-db": {
    "task": "sync_circuit_state_to_db",
    "schedule": crontab(minute=0),  # Every hour
},
```

---

### 2.5 Auto-Reset Stuck Circuit Breakers

**Task Name**: `auto_reset_stuck_circuit_breakers`  
**Priority**: MEDIUM  
**Schedule**: Every 30 minutes

**Purpose**: Automatically reset circuit breakers stuck in HALF_OPEN state.

**Recommendation**:
```python
@celery_app.task(name="auto_reset_stuck_circuit_breakers")
def auto_reset_stuck_circuit_breakers():
    """
    Auto-reset circuit breakers stuck in HALF_OPEN for too long.
    
    If a circuit breaker has been in HALF_OPEN state for > 30 minutes,
    reset it to CLOSED to attempt normal operation.
    """
    async def runner(container):
        from app.domain.services.retry.circuit_breaker import CircuitBreakerManager
        from datetime import datetime, timedelta, UTC
        import redis
        
        redis_client = await container.get(redis.Redis)
        manager = CircuitBreakerManager(redis_client)
        statuses = manager.get_all_statuses()
        
        threshold = datetime.now(UTC) - timedelta(minutes=30)
        reset_services = []
        
        for service_name, status in statuses.items():
            if status["state"] == "half_open":
                # Check if stuck in half-open
                opened_at_str = status.get("opened_at")
                if opened_at_str:
                    opened_at = datetime.fromisoformat(opened_at_str)
                    if opened_at < threshold:
                        manager.reset(service_name)
                        reset_services.append(service_name)
        
        if reset_services:
            print(f"[Auto-Reset] Reset stuck circuit breakers: {reset_services}")
        else:
            print("[Auto-Reset] No stuck circuit breakers found")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"auto-reset-stuck-circuit-breakers": {
    "task": "auto_reset_stuck_circuit_breakers",
    "schedule": crontab(minute="*/30"),  # Every 30 minutes
},
```

---

## 3. Complete Recommended Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # Aggregate retry metrics daily at 3 AM
    "aggregate-retry-metrics-daily": {
        "task": "aggregate_retry_metrics_daily",
        "schedule": crontab(hour=3, minute=0),
    },
    
    # Clean old telemetry weekly (Sunday at 4 AM)
    "clean-old-retry-telemetry": {
        "task": "clean_old_retry_telemetry",
        "schedule": crontab(hour=4, minute=0, day_of_week=0),
    },
    
    # Monitor circuit breaker health every 5 minutes
    "monitor-circuit-breaker-health": {
        "task": "monitor_circuit_breaker_health",
        "schedule": crontab(minute="*/5"),
    },
    
    # Sync Redis state to DB hourly
    "sync-circuit-state-to-db": {
        "task": "sync_circuit_state_to_db",
        "schedule": crontab(minute=0),
    },
    
    # Auto-reset stuck circuit breakers every 30 minutes
    "auto-reset-stuck-circuit-breakers": {
        "task": "auto_reset_stuck_circuit_breakers",
        "schedule": crontab(minute="*/30"),
    },
})
```

---

## 4. Task Summary

| Task | Status | Schedule | Description | Priority |
|------|--------|----------|-------------|----------|
| `aggregate_retry_metrics_daily` | ❌ Missing | Daily 3 AM | Calculate daily aggregates | HIGH |
| `clean_old_retry_telemetry` | ❌ Missing | Sunday 4 AM | Remove old telemetry | MEDIUM |
| `monitor_circuit_breaker_health` | ❌ Missing | Every 5 min | Alert on CB issues | HIGH |
| `sync_circuit_state_to_db` | ❌ Missing | Hourly | Snapshot CB state | LOW |
| `auto_reset_stuck_circuit_breakers` | ❌ Missing | Every 30 min | Reset stuck HO | MEDIUM |

---

## 5. Implementation Priority

### Phase 1 (High Priority)
1. `aggregate_retry_metrics_daily` - Essential for dashboards
2. `monitor_circuit_breaker_health` - Critical for alerting

### Phase 2 (Medium Priority)
3. `clean_old_retry_telemetry` - Database maintenance
4. `auto_reset_stuck_circuit_breakers` - Self-healing

### Phase 3 (Low Priority)
5. `sync_circuit_state_to_db` - Historical analysis

---

## References

- **Main Tasks File**: `src/app/infrastructure/celery/tasks.py`
- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Database Mappings**: `src/app/infrastructure/persistence_sqla/mappings/retry_telemetry.py`
