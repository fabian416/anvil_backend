# Agent Sessions Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Recommended Implementation  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Agent Sessions module currently has **no dedicated Celery tasks**. Agent operations are synchronous within the request lifecycle.

This document outlines **recommended Celery tasks** for improved performance, telemetry, and background processing.

---

## 1. Current State

### No Existing Celery Tasks

Agent Sessions currently operates synchronously:
- **Agent execution** within HTTP request
- **Telemetry tracking** is in-memory (TODO in code)
- **Session cleanup** not automated
- **Context expiration** handled by Redis TTL only

### Current Flow (Synchronous)
```
HTTP Request → Agent Orchestrator → Agent Execution → Response
                     ↓
              No background processing
              No async telemetry
              No session maintenance
```

---

## 2. Recommended Celery Tasks

### 2.1 Track Agent Telemetry

**Task Name**: `track_agent_telemetry`  
**Priority**: HIGH  
**Schedule**: Triggered after each agent call

**Purpose**: Async telemetry tracking to avoid request latency.

**Recommendation**:
```python
@celery_app.task(name="track_agent_telemetry")
def track_agent_telemetry(
    conversation_id: str,
    user_id: str,
    agent_type: str,
    intent_category: str | None,
    latency_ms: int,
    tokens_used: int | None,
    tools_used: list[str],
    success: bool,
    error_message: str | None = None,
):
    """
    Track agent telemetry asynchronously.
    
    This allows the main request to return immediately while
    telemetry is persisted in the background.
    """
    async def runner(container):
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.persistence_sqla.registry import mapping_registry
        from uuid import UUID
        import uuid
        
        session = await container.get(MainAsyncSession)
        
        # Map agent_session_table for telemetry
        AgentTelemetry = mapping_registry.metadata.tables.get("agent_telemetry")
        if not AgentTelemetry:
            from app.infrastructure.persistence_sqla.mappings.agent_session import map_agent_session_table
            map_agent_session_table()
            AgentTelemetry = mapping_registry.metadata.tables["agent_telemetry"]
        
        # Insert telemetry record
        await session.execute(
            AgentTelemetry.insert().values(
                id=uuid.uuid4(),
                agent_type=agent_type,
                conversation_id=UUID(conversation_id) if conversation_id else None,
                intent_classification=intent_category,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                tools_used=tools_used,
                success=success,
                error_message=error_message,
            )
        )
        await session.commit()
        
        print(f"[Agent Telemetry] {agent_type}: {latency_ms}ms, success={success}")
    
    return asyncio.run(_run_task(runner))
```

**Usage in SendAgentSquadMessage**:
```python
# Replace synchronous telemetry with async task
track_agent_telemetry.delay(
    conversation_id=str(conversation_id),
    user_id=str(user_id),
    agent_type=agent_type.value,
    intent_category=intent_classification.intent_category.value if intent_classification else None,
    latency_ms=latency_ms,
    tokens_used=tokens_used,
    tools_used=agent_response.tools_used,
    success=True,
)
```

---

### 2.2 Cleanup Expired Agent Sessions

**Task Name**: `cleanup_expired_agent_sessions`  
**Priority**: MEDIUM  
**Schedule**: Daily at 3:00 AM

**Purpose**: Clean up old agent sessions to prevent database bloat.

**Recommendation**:
```python
@celery_app.task(name="cleanup_expired_agent_sessions")
def cleanup_expired_agent_sessions(retention_days: int = 30):
    """
    Clean up agent sessions older than retention period.
    
    Agent sessions are tied to conversations. Once a conversation
    is old enough, associated sessions can be cleaned.
    
    Args:
        retention_days: Days to retain sessions (default 30)
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from datetime import datetime, timedelta, UTC
        
        session = await container.get(MainAsyncSession)
        
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
        
        # Delete old agent sessions
        # Note: These are conversation-specific state, not needed after inactivity
        query = text("""
            DELETE FROM agent_sessions
            WHERE updated_at < :cutoff
        """)
        
        result = await session.execute(query, {"cutoff": cutoff_date})
        deleted_sessions = result.rowcount
        
        await session.commit()
        
        print(f"[Agent Sessions Cleanup] Deleted {deleted_sessions} expired sessions")
        return {"deleted_sessions": deleted_sessions}
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"cleanup-expired-agent-sessions": {
    "task": "cleanup_expired_agent_sessions",
    "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
},
```

---

### 2.3 Aggregate Telemetry Metrics

**Task Name**: `aggregate_agent_telemetry`  
**Priority**: MEDIUM  
**Schedule**: Hourly

**Purpose**: Aggregate telemetry for dashboard and analytics.

**Recommendation**:
```python
@celery_app.task(name="aggregate_agent_telemetry")
def aggregate_agent_telemetry():
    """
    Aggregate agent telemetry metrics for analytics dashboard.
    
    Calculates:
    - Average latency per agent
    - Success rate per agent
    - Total tokens used
    - Most used tools
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.cache.redis_client import RedisClient
        import json
        
        session = await container.get(MainAsyncSession)
        redis_client = await container.get(RedisClient)
        
        # Aggregate metrics for last 24 hours
        query = text("""
            SELECT 
                agent_type,
                COUNT(*) as total_calls,
                AVG(latency_ms) as avg_latency_ms,
                SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate,
                SUM(COALESCE(tokens_used, 0)) as total_tokens
            FROM agent_telemetry
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY agent_type
            ORDER BY total_calls DESC
        """)
        
        result = await session.execute(query)
        metrics = result.fetchall()
        
        # Build metrics dict
        metrics_dict = {
            "timestamp": datetime.now(UTC).isoformat(),
            "agents": [
                {
                    "agent_type": row.agent_type,
                    "total_calls": row.total_calls,
                    "avg_latency_ms": round(row.avg_latency_ms, 2) if row.avg_latency_ms else 0,
                    "success_rate": round(row.success_rate * 100, 2) if row.success_rate else 0,
                    "total_tokens": row.total_tokens,
                }
                for row in metrics
            ],
        }
        
        # Store in Redis for dashboard
        redis_client.set(
            "agent_squad:telemetry:aggregated",
            json.dumps(metrics_dict),
            ex=3600  # 1 hour TTL
        )
        
        print(f"[Telemetry Aggregation] Aggregated metrics for {len(metrics)} agents")
        return metrics_dict
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"aggregate-agent-telemetry": {
    "task": "aggregate_agent_telemetry",
    "schedule": crontab(minute=0),  # Every hour
},
```

---

### 2.4 Process Enterprise Compliance Screening

**Task Name**: `process_compliance_screening`  
**Priority**: HIGH (Enterprise)  
**Schedule**: On-demand (triggered by wallet connection)

**Purpose**: Async AML/KYC screening for enterprise customers.

**Recommendation**:
```python
@celery_app.task(name="process_compliance_screening")
def process_compliance_screening(
    user_id: str,
    wallet_address: str,
):
    """
    Process compliance screening for enterprise wallet.
    
    Integrates with:
    - Chainalysis for transaction analysis
    - TRM Labs for risk scoring
    - OFAC sanction list check
    
    Args:
        user_id: User UUID
        wallet_address: Ethereum wallet address (0x...)
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        from uuid import UUID
        import uuid
        
        session = await container.get(MainAsyncSession)
        
        # TODO: Integrate with actual Chainalysis/TRM Labs API
        # For now, simulate screening
        screening_result = {
            "risk_score": 15,
            "ofac_status": "clear",
            "pep_status": "clear",
            "mixer_exposure_pct": 0.0,
            "high_risk_sources_pct": 0.5,
            "screening_result": "approved",
            "screening_data": {
                "provider": "simulated",
                "checked_at": datetime.now(UTC).isoformat(),
            },
        }
        
        # Insert compliance log
        ComplianceLog = mapping_registry.metadata.tables.get("compliance_screening_logs")
        if ComplianceLog:
            await session.execute(
                ComplianceLog.insert().values(
                    id=uuid.uuid4(),
                    user_id=UUID(user_id),
                    wallet_address=wallet_address,
                    risk_score=screening_result["risk_score"],
                    ofac_status=screening_result["ofac_status"],
                    pep_status=screening_result["pep_status"],
                    mixer_exposure_pct=screening_result["mixer_exposure_pct"],
                    high_risk_sources_pct=screening_result["high_risk_sources_pct"],
                    screening_result=screening_result["screening_result"],
                    screening_data=screening_result["screening_data"],
                )
            )
            await session.commit()
        
        print(f"[Compliance Screening] User {user_id}: {screening_result['screening_result']}")
        return screening_result
    
    return asyncio.run(_run_task(runner))
```

---

### 2.5 Crisis Event Monitoring

**Task Name**: `monitor_crisis_events`  
**Priority**: CRITICAL (Enterprise)  
**Schedule**: Every 5 minutes

**Purpose**: Monitor for DeFi crisis events (exploits, depegs, etc.).

**Recommendation**:
```python
@celery_app.task(name="monitor_crisis_events")
def monitor_crisis_events():
    """
    Monitor for DeFi crisis events affecting enterprise users.
    
    Integrations:
    - Forta Network for exploit detection
    - DeFiLlama for TVL crashes
    - Price oracles for depeg detection
    
    When crisis detected:
    - Log event to crisis_events table
    - Trigger CrisisManager agent
    - Send alerts to affected users
    """
    async def runner(container):
        from sqlalchemy import text
        from app.infrastructure.adapters.types import MainAsyncSession
        
        session = await container.get(MainAsyncSession)
        
        # TODO: Integrate with Forta Network API
        # For now, check for simulated crisis conditions
        
        # Example: Check for TVL crash
        # Example: Check for stablecoin depeg
        # Example: Check for protocol exploit
        
        crisis_detected = False
        events_logged = 0
        
        if crisis_detected:
            # Log crisis event
            # Trigger automated response
            pass
        
        print(f"[Crisis Monitoring] Checked - {events_logged} events detected")
        return {"events_detected": events_logged}
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"monitor-crisis-events": {
    "task": "monitor_crisis_events",
    "schedule": crontab(minute="*/5"),  # Every 5 minutes
},
```

---

### 2.6 Sync Redis Context to Database

**Task Name**: `sync_context_to_database`  
**Priority**: LOW  
**Schedule**: Every 6 hours

**Purpose**: Backup Redis context to PostgreSQL for durability.

**Recommendation**:
```python
@celery_app.task(name="sync_context_to_database")
def sync_context_to_database():
    """
    Sync high-value Redis context to PostgreSQL.
    
    Redis has 24h TTL, but some conversations may need
    longer persistence for compliance or analytics.
    """
    async def runner(container):
        from app.infrastructure.cache.redis_client import RedisClient
        from app.infrastructure.adapters.types import MainAsyncSession
        
        redis_client = await container.get(RedisClient)
        session = await container.get(MainAsyncSession)
        
        # Find active conversations in Redis
        # For each, save snapshot to database if important
        
        synced_count = 0
        
        # TODO: Implement selective sync based on:
        # - Enterprise users
        # - High-value transactions
        # - Compliance requirements
        
        print(f"[Context Sync] Synced {synced_count} conversations to database")
        return {"synced_count": synced_count}
    
    return asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"sync-context-to-database": {
    "task": "sync_context_to_database",
    "schedule": crontab(hour="*/6"),  # Every 6 hours
},
```

---

## 3. Complete Recommended Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # Hourly telemetry aggregation
    "aggregate-agent-telemetry": {
        "task": "aggregate_agent_telemetry",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Daily session cleanup
    "cleanup-expired-agent-sessions": {
        "task": "cleanup_expired_agent_sessions",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    
    # Enterprise: Crisis monitoring (every 5 min)
    "monitor-crisis-events": {
        "task": "monitor_crisis_events",
        "schedule": crontab(minute="*/5"),
    },
    
    # Context backup (every 6 hours)
    "sync-context-to-database": {
        "task": "sync_context_to_database",
        "schedule": crontab(hour="*/6"),
    },
})
```

---

## 4. Task Summary

| Task | Status | Schedule | Description | Priority |
|------|--------|----------|-------------|----------|
| `track_agent_telemetry` | ❌ Missing | On-demand | Async telemetry tracking | HIGH |
| `cleanup_expired_agent_sessions` | ❌ Missing | Daily 3 AM | Clean old sessions | MEDIUM |
| `aggregate_agent_telemetry` | ❌ Missing | Hourly | Dashboard metrics | MEDIUM |
| `process_compliance_screening` | ❌ Missing | On-demand | AML/KYC (Enterprise) | HIGH |
| `monitor_crisis_events` | ❌ Missing | Every 5 min | Crisis detection (Enterprise) | CRITICAL |
| `sync_context_to_database` | ❌ Missing | Every 6 hours | Context backup | LOW |

---

## 5. Implementation Priority

### Phase 1 (High Priority)
1. `track_agent_telemetry` - Reduce request latency
2. `process_compliance_screening` - Enterprise compliance

### Phase 2 (Medium Priority)
3. `cleanup_expired_agent_sessions` - Database maintenance
4. `aggregate_agent_telemetry` - Analytics dashboard

### Phase 3 (Enterprise)
5. `monitor_crisis_events` - Real-time protection
6. `sync_context_to_database` - Durability

---

## References

- **Main Tasks File**: `src/app/infrastructure/celery/tasks.py`
- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Agent Session Mapping**: `src/app/infrastructure/persistence_sqla/mappings/agent_session.py`
- **SendAgentSquadMessage**: `src/app/application/agent_squad/commands/send_agent_squad_message.py`
