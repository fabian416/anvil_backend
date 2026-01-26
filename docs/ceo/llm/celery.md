# LLM Orchestration System Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The LLM Orchestration System has **implemented Celery tasks** for ranking recalculation. Additional tasks are recommended for telemetry aggregation, cost tracking, and cache management.

---

## 1. Existing Celery Tasks

### 1.1 Recalculate All Rankings
**Task Name**: `llm_ranking.recalculate_all_rankings`  
**Location**: `src/app/infrastructure/celery/tasks/llm_ranking.py`

**Purpose**: Recalculate model rankings for all agent types.

**Schedule**: Every 6 hours

**Implementation**:
```python
@celery_app.task(name="llm_ranking.recalculate_all_rankings")
def recalculate_all_rankings():
    """
    Recalculate rankings for all agent types.
    
    - Fetches telemetry from last 24 hours
    - Calculates new ranking scores
    - Updates llm_model_agent_rankings table
    - Respects active overrides
    
    Runs every 6 hours.
    """
    async def runner(container):
        from app.application.llm.ranking.recalculate_all_rankings import (
            RecalculateAllRankings,
        )
        
        interactor = await container.get(RecalculateAllRankings)
        result = await interactor.execute(hours_to_analyze=24)
        
        logger.info(
            f"Recalculated rankings for {result.agent_types_updated} agent types, "
            f"{result.total_models_updated} models updated"
        )
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"recalculate-llm-rankings": {
    "task": "llm_ranking.recalculate_all_rankings",
    "schedule": crontab(hour="*/6"),  # Every 6 hours
},
```

---

### 1.2 Recalculate Agent Rankings
**Task Name**: `llm_ranking.recalculate_agent_rankings`  
**Location**: `src/app/infrastructure/celery/tasks/llm_ranking.py`

**Purpose**: Recalculate rankings for a specific agent type (on-demand).

**Implementation**:
```python
@celery_app.task(name="llm_ranking.recalculate_agent_rankings")
def recalculate_agent_rankings(agent_type: str, hours: int = 24):
    """
    Recalculate rankings for specific agent type.
    
    Triggered manually via admin API or automatically
    after significant metric changes.
    """
    async def runner(container):
        from app.application.llm.ranking.recalculate_agent_rankings import (
            RecalculateAgentRankings,
        )
        
        interactor = await container.get(RecalculateAgentRankings)
        result = await interactor.execute(agent_type, hours_to_analyze=hours)
        
        logger.info(f"Recalculated {result.models_updated} models for {agent_type}")
    
    asyncio.run(_run_task(runner))
```

---

### 1.3 Cache LLM Response
**Task Name**: `cache_llm_response`  
**Location**: `src/app/infrastructure/celery/tasks.py`

**Purpose**: Cache LLM responses for repeated queries.

---

## 2. Recommended Celery Tasks

### 2.1 Aggregate LLM Telemetry (Hourly)

**Task Name**: `aggregate_llm_telemetry_hourly`  
**Priority**: HIGH  
**Schedule**: Every hour

**Purpose**: Aggregate raw telemetry into hourly summaries.

**Implementation Recommendation**:
```python
@celery_app.task(name="aggregate_llm_telemetry_hourly")
def aggregate_llm_telemetry_hourly():
    """
    Aggregate LLM telemetry hourly.
    
    - Aggregates llm_requests into llm_telemetry_hourly
    - Calculates percentiles (p50, p95, p99)
    - Summarizes by provider, model, agent
    
    Runs every hour at :05.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        
        # Get last hour's data
        end_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(hours=1)
        
        # Aggregate telemetry
        aggregations = await aggregate_telemetry_for_period(start_time, end_time)
        
        # Store in hourly table
        await store_hourly_telemetry(aggregations)
        
        logger.info(f"Aggregated telemetry for {start_time} - {end_time}")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"aggregate-llm-telemetry-hourly": {
    "task": "aggregate_llm_telemetry_hourly",
    "schedule": crontab(minute=5),  # Every hour at :05
},
```

---

### 2.2 Aggregate LLM Cost Daily

**Task Name**: `aggregate_llm_cost_daily`  
**Priority**: HIGH  
**Schedule**: Daily at 1 AM UTC

**Purpose**: Calculate daily cost summaries.

**Implementation Recommendation**:
```python
@celery_app.task(name="aggregate_llm_cost_daily")
def aggregate_llm_cost_daily():
    """
    Aggregate daily LLM costs.
    
    - Summarizes costs by provider, model, agent
    - Updates llm_cost_daily table
    - Checks budget thresholds
    - Triggers alerts if needed
    
    Runs daily at 1 AM.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        
        yesterday = (datetime.now(UTC) - timedelta(days=1)).date()
        
        # Calculate daily costs
        costs = await calculate_daily_costs(yesterday)
        
        # Store in daily table
        await store_daily_costs(costs)
        
        # Check budget thresholds
        await check_budget_alerts(costs)
        
        logger.info(f"Aggregated costs for {yesterday}: ${costs.total_usd:.2f}")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"aggregate-llm-cost-daily": {
    "task": "aggregate_llm_cost_daily",
    "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
},
```

---

### 2.3 Check Circuit Breaker Recovery

**Task Name**: `check_circuit_breaker_recovery`  
**Priority**: MEDIUM  
**Schedule**: Every 5 minutes

**Purpose**: Check if open circuit breakers can be closed.

**Implementation Recommendation**:
```python
@celery_app.task(name="check_circuit_breaker_recovery")
def check_circuit_breaker_recovery():
    """
    Check circuit breaker recovery.
    
    - Finds circuit breakers in OPEN state
    - Checks if timeout has expired
    - Transitions to HALF_OPEN for testing
    
    Runs every 5 minutes.
    """
    async def runner(container):
        from app.domain.services.llm.circuit_breaker import CircuitBreakerManager
        
        manager = await container.get(CircuitBreakerManager)
        
        # Get all open circuit breakers
        open_breakers = await manager.get_open_breakers()
        
        for breaker in open_breakers:
            if breaker.timeout_expired:
                await manager.transition_to_half_open(breaker.id)
                logger.info(f"Circuit breaker {breaker.entity_name} -> HALF_OPEN")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"check-circuit-breaker-recovery": {
    "task": "check_circuit_breaker_recovery",
    "schedule": crontab(minute="*/5"),  # Every 5 minutes
},
```

---

### 2.4 Expire Ranking Overrides

**Task Name**: `expire_ranking_overrides`  
**Priority**: MEDIUM  
**Schedule**: Hourly

**Purpose**: Remove expired ranking overrides.

**Implementation Recommendation**:
```python
@celery_app.task(name="expire_ranking_overrides")
def expire_ranking_overrides():
    """
    Remove expired ranking overrides.
    
    - Finds overrides past expiration
    - Removes override
    - Triggers ranking recalculation
    
    Runs hourly.
    """
    async def runner(container):
        from datetime import datetime, UTC
        
        # Get expired overrides
        expired = await get_expired_overrides()
        
        for override in expired:
            await remove_override(override.id)
            
            # Trigger recalculation for agent type
            recalculate_agent_rankings.delay(override.agent_type)
            
            logger.info(
                f"Expired override for {override.model_name} in {override.agent_type}"
            )
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"expire-ranking-overrides": {
    "task": "expire_ranking_overrides",
    "schedule": crontab(minute=30),  # Hourly at :30
},
```

---

### 2.5 Clean Old Telemetry

**Task Name**: `clean_old_llm_telemetry`  
**Priority**: LOW  
**Schedule**: Daily at 3 AM UTC

**Purpose**: Clean up old telemetry data.

**Implementation Recommendation**:
```python
@celery_app.task(name="clean_old_llm_telemetry")
def clean_old_llm_telemetry():
    """
    Clean old LLM telemetry data.
    
    - Removes raw requests older than 30 days
    - Keeps hourly aggregations for 90 days
    - Keeps daily aggregations for 1 year
    
    Runs daily at 3 AM.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        
        # Clean raw requests (30 days)
        raw_cutoff = datetime.now(UTC) - timedelta(days=30)
        deleted_raw = await delete_requests_before(raw_cutoff)
        
        # Clean hourly aggregations (90 days)
        hourly_cutoff = datetime.now(UTC) - timedelta(days=90)
        deleted_hourly = await delete_hourly_before(hourly_cutoff)
        
        logger.info(
            f"Cleaned {deleted_raw} raw requests, {deleted_hourly} hourly records"
        )
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"clean-old-llm-telemetry": {
    "task": "clean_old_llm_telemetry",
    "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
},
```

---

### 2.6 Sync Provider Health

**Task Name**: `sync_provider_health`  
**Priority**: HIGH  
**Schedule**: Every 2 minutes

**Purpose**: Check LLM provider health status.

**Implementation Recommendation**:
```python
@celery_app.task(name="sync_provider_health")
def sync_provider_health():
    """
    Sync LLM provider health status.
    
    - Pings each provider's health endpoint
    - Updates provider status in database
    - Triggers alerts on status changes
    
    Runs every 2 minutes.
    """
    async def runner(container):
        providers = ["vertex_ai", "deepinfra", "bedrock"]
        
        for provider_name in providers:
            try:
                is_healthy = await check_provider_health(provider_name)
                await update_provider_status(provider_name, is_healthy)
                
                if not is_healthy:
                    await trigger_provider_alert(provider_name)
                    
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")
                await update_provider_status(provider_name, False)
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"sync-provider-health": {
    "task": "sync_provider_health",
    "schedule": crontab(minute="*/2"),  # Every 2 minutes
},
```

---

## 3. Complete Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # Existing tasks
    "recalculate-llm-rankings": {
        "task": "llm_ranking.recalculate_all_rankings",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
    
    # Recommended tasks (to be implemented)
    "aggregate-llm-telemetry-hourly": {
        "task": "aggregate_llm_telemetry_hourly",
        "schedule": crontab(minute=5),  # Hourly at :05
    },
    "aggregate-llm-cost-daily": {
        "task": "aggregate_llm_cost_daily",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    "check-circuit-breaker-recovery": {
        "task": "check_circuit_breaker_recovery",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "expire-ranking-overrides": {
        "task": "expire_ranking_overrides",
        "schedule": crontab(minute=30),  # Hourly at :30
    },
    "clean-old-llm-telemetry": {
        "task": "clean_old_llm_telemetry",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    "sync-provider-health": {
        "task": "sync_provider_health",
        "schedule": crontab(minute="*/2"),  # Every 2 minutes
    },
})
```

---

## 4. Implementation Priority

| Task | Status | Priority | Effort | Business Impact |
|------|--------|----------|--------|-----------------|
| recalculate_all_rankings | ✅ Done | - | - | Model selection |
| recalculate_agent_rankings | ✅ Done | - | - | On-demand recalc |
| cache_llm_response | ✅ Done | - | - | Response caching |
| aggregate_llm_telemetry_hourly | ❌ Missing | HIGH | Medium | Dashboard metrics |
| aggregate_llm_cost_daily | ❌ Missing | HIGH | Medium | Cost tracking |
| sync_provider_health | ❌ Missing | HIGH | Low | Provider monitoring |
| check_circuit_breaker_recovery | ❌ Missing | MEDIUM | Low | Fault recovery |
| expire_ranking_overrides | ❌ Missing | MEDIUM | Low | Override cleanup |
| clean_old_llm_telemetry | ❌ Missing | LOW | Low | Data management |

---

## 5. Task Design Patterns

### 5.1 Idempotency
All LLM tasks should be idempotent - running multiple times should not cause issues.

### 5.2 Error Handling
```python
@celery_app.task(name="task_name", bind=True, max_retries=3)
def task_name(self):
    try:
        # Task logic
    except ExternalAPIError as e:
        # Retry with exponential backoff
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    except Exception as e:
        # Log and don't retry for unknown errors
        logger.error(f"Task failed: {e}")
```

### 5.3 Metrics Collection
Each task should emit metrics for monitoring:
- Task duration
- Records processed
- Errors encountered

---

## 6. Running Celery

### Start Worker
```bash
make celery.worker
# or
celery -A app.infrastructure.celery.app worker --loglevel=info
```

### Start Beat Scheduler
```bash
make celery.beat
# or
celery -A app.infrastructure.celery.app beat --loglevel=info
```

### Monitor with Flower
```bash
make celery.flower
# Access at http://localhost:5555
```

---

## References

- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Main Tasks**: `src/app/infrastructure/celery/tasks.py`
- **LLM Ranking Tasks**: `src/app/infrastructure/celery/tasks/llm_ranking.py`
- **Ranking Engine**: `src/app/domain/services/llm/ranking_engine.py`
