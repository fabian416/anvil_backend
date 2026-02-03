# Chat System Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Chat System uses Celery with Redis as the message broker for background task processing. Tasks handle maintenance, analytics aggregation, and asynchronous operations.

**Configuration**:
- Broker: Redis
- Backend: Redis
- Beat Schedule: Crontab-based periodic tasks

---

## 1. Chat-Specific Celery Tasks

### 1.1 Archive Guest Conversations

**Task Name**: `archive_guest_conversations`  
**Schedule**: Every hour at :00  
**Source**: `src/app/infrastructure/celery/tasks.py`

**Purpose**: Archives inactive guest conversations to keep the database clean.

**Implementation**:
```python
@celery_app.task(name="archive_guest_conversations")
def archive_guest_conversations():
    """
    Archive inactive guest conversations.
    
    Runs every hour at :00 to archive conversations that have been
    inactive for more than 1 hour. This keeps the guest_conversations
    table clean and ensures new sessions get fresh conversations.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        from app.domain.guest.ports.guest_repository import GuestRepository
        
        repository = await container.get(GuestRepository)
        
        # Archive conversations older than 1 hour
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        archived_count = await repository.archive_inactive_conversations(one_hour_ago)
        
        print(f"Guest conversation archival complete: {archived_count} conversations archived")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"archive-guest-conversations": {
    "task": "archive_guest_conversations",
    "schedule": crontab(minute=0),  # Every hour at :00
},
```

---

### 1.2 Process Agent Response

**Task Name**: `process_agent_response`  
**Schedule**: On-demand (triggered by API)  
**Source**: `src/app/infrastructure/celery/tasks.py`

**Purpose**: Background processing of AI agent responses for long-running operations.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | str | Conversation UUID |
| `message_id` | str | Message UUID |

**Implementation**:
```python
@celery_app.task(name="process_agent_response")
def process_agent_response(conversation_id: str, message_id: str):
    """
    Background task to process a user message and generate an AI response.
    """
    async def runner(container):
        from app.domain.ports.ai.agent_gateway import AgentGateway
        from uuid import UUID
        
        gateway = await container.get(AgentGateway)
        
        await gateway.process_message(
            user_id=UUID("00000000-0000-0000-0000-000000000000"),
            session_id=str(conversation_id),
            message="Task processing..."
        )

    asyncio.run(_run_task(runner))
```

---

### 1.3 Update Agent Stats

**Task Name**: `update_agent_stats`  
**Schedule**: Every 5 minutes  
**Source**: `src/app/infrastructure/celery/tasks.py`

**Purpose**: Aggregates agent performance statistics for analytics.

**Beat Schedule**:
```python
"update-agent-stats": {
    "task": "update_agent_stats",
    "schedule": crontab(minute="*/5"),
},
```

---

## 2. User Context Tasks

**Source**: `src/app/infrastructure/celery/tasks/user_context_tasks.py`

### 2.1 Update User Context

**Task Name**: `update_user_context`  
**Schedule**: Every 10 minutes

**Purpose**: Updates user context data for context-aware agent selection.

**Data Updated**:
- Recent intents
- Mentioned tokens/protocols
- Active positions
- Trading patterns
- Preferred chains

**Beat Schedule**:
```python
"update-user-context": {
    "task": "update_user_context",
    "schedule": crontab(minute="*/10"),
},
```

---

### 2.2 Create Missing User Contexts

**Task Name**: `create_missing_user_contexts`  
**Schedule**: On-demand

**Purpose**: Creates context records for users that don't have one.

---

### 2.3 User Context Analytics

**Task Name**: `user_context_analytics`  
**Schedule**: Daily at 6 AM

**Purpose**: Aggregates user context analytics for reporting.

**Beat Schedule**:
```python
"user-context-analytics": {
    "task": "user_context_analytics",
    "schedule": crontab(hour=6, minute=0),
},
```

---

## 3. Distillation Tasks

**Source**: `src/app/infrastructure/celery/tasks/distillation_tasks.py`

### 3.1 Aggregate Distillation Telemetry

**Task Name**: `aggregate_distillation_telemetry`  
**Schedule**: Every hour at :05

**Purpose**: Aggregates LLM response distillation metrics.

**Beat Schedule**:
```python
"aggregate-distillation-telemetry": {
    "task": "aggregate_distillation_telemetry",
    "schedule": crontab(minute=5),
},
```

---

### 3.2 Cleanup Expired Cache

**Task Name**: `cleanup_expired_cache`  
**Schedule**: Daily at 3 AM

**Purpose**: Removes expired cached LLM responses.

**Beat Schedule**:
```python
"cleanup-expired-cache": {
    "task": "cleanup_expired_cache",
    "schedule": crontab(hour=3, minute=0),
},
```

---

### 3.3 Cache LLM Response

**Task Name**: `cache_llm_response`  
**Schedule**: On-demand

**Purpose**: Caches LLM responses for future reuse.

---

## 4. LLM Ranking Tasks

**Source**: `src/app/infrastructure/celery/tasks/llm_ranking.py`

### 4.1 Recalculate All Rankings

**Task Name**: `llm_ranking.recalculate_all_rankings`  
**Schedule**: Daily at 2 AM

**Purpose**: Recalculates LLM provider rankings based on performance.

**Beat Schedule**:
```python
"recalculate-llm-rankings": {
    "task": "llm_ranking.recalculate_all_rankings",
    "schedule": crontab(hour=2, minute=0),
},
```

---

### 4.2 Recalculate Agent Rankings

**Task Name**: `recalculate_agent_rankings`  
**Schedule**: On-demand

**Purpose**: Recalculates rankings for specific agents.

---

## 5. Related Maintenance Tasks

### 5.1 Cleanup Expired Sessions

**Task Name**: `cleanup_expired_sessions`  
**Schedule**: Daily at midnight

**Purpose**: Removes expired authentication sessions.

**Impact on Chat**: Ensures invalid sessions don't persist.

---

### 5.2 Check User Risk Alerts

**Task Name**: `check_user_risk_alerts`  
**Schedule**: Every 15 minutes

**Purpose**: Monitors user positions for risk changes.

**Impact on Chat**: May trigger alert notifications in chat.

---

## Complete Beat Schedule

```python
celery_app.conf.beat_schedule = {
    # Chat-specific tasks
    "archive-guest-conversations": {
        "task": "archive_guest_conversations",
        "schedule": crontab(minute=0),  # Every hour
    },
    "update-agent-stats": {
        "task": "update_agent_stats",
        "schedule": crontab(minute="*/5"),  # Every 5 min
    },
    
    # User context tasks
    "update-user-context": {
        "task": "update_user_context",
        "schedule": crontab(minute="*/10"),  # Every 10 min
    },
    "user-context-analytics": {
        "task": "user_context_analytics",
        "schedule": crontab(hour=6, minute=0),  # Daily 6 AM
    },
    
    # Distillation tasks
    "aggregate-distillation-telemetry": {
        "task": "aggregate_distillation_telemetry",
        "schedule": crontab(minute=5),  # Every hour at :05
    },
    "cleanup-expired-cache": {
        "task": "cleanup_expired_cache",
        "schedule": crontab(hour=3, minute=0),  # Daily 3 AM
    },
    
    # LLM ranking
    "recalculate-llm-rankings": {
        "task": "llm_ranking.recalculate_all_rankings",
        "schedule": crontab(hour=2, minute=0),  # Daily 2 AM
    },
    
    # Maintenance
    "cleanup-expired-sessions": {
        "task": "cleanup_expired_sessions",
        "schedule": crontab(hour=0, minute=0),  # Daily midnight
    },
    "check-user-risk-alerts": {
        "task": "check_user_risk_alerts",
        "schedule": crontab(minute="*/15"),  # Every 15 min
    },
}
```

---

## Running Celery

### Development

```bash
# Start worker
make celery.worker

# Start beat scheduler
make celery.beat

# Start Flower monitoring (port 5555)
make celery.flower

# Or with make start-dev (starts all services)
make start-dev
```

### Manual Commands

```bash
# Worker with verbose logging
celery -A app.infrastructure.celery.app worker --loglevel=info

# Beat scheduler
celery -A app.infrastructure.celery.app beat --loglevel=info

# Flower monitoring
celery -A app.infrastructure.celery.app flower --port=5555
```

### Testing Tasks Manually

```python
from app.infrastructure.celery.tasks import archive_guest_conversations

# Trigger immediately
archive_guest_conversations.delay()

# Trigger with countdown (30 seconds)
archive_guest_conversations.apply_async(countdown=30)
```

---

## Task Design Patterns

### Async Runner Pattern

All tasks use a common pattern for async execution with dependency injection:

```python
async def _run_task(coro_factory):
    """Run async task with DI container."""
    settings = load_settings()
    container = create_async_ioc_container(
        providers=(
            ApplicationProvider(),
            infrastructure_provider(),
            PresentationProvider(),
            SettingsProvider(),
        ),
        settings=settings,
    )
    try:
        async with container() as request_container:
            await coro_factory(request_container)
    finally:
        await container.close()

@celery_app.task(name="my_task")
def my_task():
    async def runner(container):
        # Get dependencies
        service = await container.get(MyService)
        # Execute
        await service.do_something()
    
    asyncio.run(_run_task(runner))
```

---

## Monitoring

### Flower Dashboard

Access at `http://localhost:5555` when running Flower.

**Features**:
- Task execution history
- Worker status
- Queue lengths
- Task timing

### Logging

Tasks log to standard output with `print()` statements.

**Example Output**:
```
Guest conversation archival complete: 15 conversations archived
Updating agent stats...
User context update complete: 50 users updated
```

---

## Error Handling

Tasks should implement:
1. **Retry logic** for transient failures
2. **Error logging** for debugging
3. **Graceful degradation** when services unavailable

```python
@celery_app.task(
    name="my_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def my_task(self):
    try:
        # Task logic
        pass
    except TransientError as e:
        self.retry(exc=e)
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise
```

---

## References

- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Main Tasks**: `src/app/infrastructure/celery/tasks.py`
- **User Context Tasks**: `src/app/infrastructure/celery/tasks/user_context_tasks.py`
- **Distillation Tasks**: `src/app/infrastructure/celery/tasks/distillation_tasks.py`
- **LLM Ranking Tasks**: `src/app/infrastructure/celery/tasks/llm_ranking.py`
- **Makefile**: `Makefile` (celery commands)
