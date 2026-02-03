# AI Brain Celery Background Tasks

**Version:** 1.0.0
**Last Updated:** 2026-01-26
**Status:** Production-Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Task Categories](#task-categories)
4. [Core Background Tasks](#core-background-tasks)
5. [Task Dependencies](#task-dependencies)
6. [Configuration](#configuration)
7. [Error Handling](#error-handling)
8. [Monitoring](#monitoring)
9. [Performance Tuning](#performance-tuning)
10. [Manual Operations](#manual-operations)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Brain module leverages **Celery** for background task processing to handle:
- Knowledge cache warming and invalidation
- Integration health monitoring
- Cache statistics aggregation
- Prompt performance analysis
- Configuration auditing
- Data consistency checks
- Maintenance operations

### Key Features

- **Async Task Execution**: All tasks use async/await with proper DI container management
- **Queue Segregation**: Tasks assigned to specialized queues (ai_brain, health_checks, analytics, maintenance)
- **Retry Strategies**: Exponential backoff with max retry limits
- **Result Backend**: Redis-based result storage with TTL
- **Beat Scheduling**: Cron-based periodic task execution
- **Monitoring**: Flower UI and Prometheus metrics integration

### Design Principles

1. **Separation of Concerns**: Each task has a single, well-defined responsibility
2. **Idempotency**: Tasks can be safely retried without side effects
3. **Graceful Degradation**: Failures don't cascade across system
4. **Observability**: Comprehensive logging and metrics at every step
5. **Resource Efficiency**: Tasks use connection pooling and batch operations

---

## Architecture

### Task Execution Flow

```
┌─────────────────┐
│  Celery Beat    │ ◄─── Cron-based scheduling
│   (Scheduler)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Redis Broker  │ ◄─── Task queue storage
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Celery Worker   │ ◄─── Task execution
│  (ai_brain)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DI Container   │ ◄─── Dishka dependency injection
│   (REQUEST)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Task Logic     │ ◄─── Business operations
│  (Interactors)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Result Backend  │ ◄─── Redis result storage
│    (Redis)      │
└─────────────────┘
```

### Queue Architecture

```
┌──────────────────────────────────────────────────┐
│                 Redis Broker                      │
└──────────────────────────────────────────────────┘
           │         │         │         │
           ▼         ▼         ▼         ▼
      ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
      │ai_brain│ │ health │ │analytic│ │maintain│
      │ queue  │ │ queue  │ │ queue  │ │ queue  │
      └────────┘ └────────┘ └────────┘ └────────┘
           │         │         │         │
           ▼         ▼         ▼         ▼
      ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
      │Worker 1│ │Worker 2│ │Worker 3│ │Worker 4│
      └────────┘ └────────┘ └────────┘ └────────┘
```

### Task Lifecycle

1. **Scheduling**: Beat scheduler adds task to queue
2. **Queueing**: Redis broker stores task message
3. **Picking**: Worker retrieves task from queue
4. **Execution**: Worker runs task with DI container
5. **Result Storage**: Result saved to backend
6. **Cleanup**: Container closed, resources released

---

## Task Categories

### 1. Cache Management Tasks
- Knowledge cache warming
- Cache statistics aggregation
- Expired cache cleanup
- Cache consistency checks

### 2. Health Monitoring Tasks
- Integration health checks
- System health aggregation
- Alert generation

### 3. Analytics Tasks
- Prompt performance analysis
- Usage statistics aggregation
- A/B test result processing

### 4. Audit Tasks
- Configuration change auditing
- Access log aggregation
- Compliance reporting

### 5. Maintenance Tasks
- Database cleanup
- Cache eviction
- Data archival

---

## Core Background Tasks

### Task 1: Knowledge Cache Warming

**Purpose**: Pre-populate Redis cache with frequently accessed knowledge to reduce database load and improve response times.

**Business Value**:
- Reduces average query latency by 80%
- Decreases database load during peak hours
- Improves user experience with faster responses

#### Task Definition

```python
# src/app/infrastructure/celery/tasks/ai_brain_tasks.py

import asyncio
from typing import Optional
from celery import Task
from app.infrastructure.celery.app import celery_app
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings
from app.setup.ioc.application import ApplicationProvider
from app.setup.ioc.infrastructure import infrastructure_provider
from app.setup.ioc.presentation import PresentationProvider
from app.setup.ioc.settings import SettingsProvider


async def _run_task(coro_factory):
    """Helper to run async tasks with DI container."""
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


@celery_app.task(
    name="warm_knowledge_cache_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def warm_knowledge_cache_task(
    self: Task,
    agent_ids: Optional[list[str]] = None,
    priority: str = "normal",
) -> dict[str, int]:
    """
    Warm Redis cache with frequently accessed knowledge entries.

    Args:
        agent_ids: Optional list of agent UUIDs to warm cache for.
                   If None, warms cache for all active agents.
        priority: Cache warming priority ("low", "normal", "high")

    Returns:
        Dict with cache warming statistics:
        {
            "agents_processed": int,
            "entries_cached": int,
            "cache_hits": int,
            "cache_misses": int,
            "duration_seconds": float
        }

    Raises:
        CacheWarmingError: If cache warming fails
    """
    async def runner(container):
        from app.application.ai_brain.cache.interactors import (
            WarmKnowledgeCacheInteractor,
        )
        from app.application.ai_brain.cache.commands import WarmCacheCommand

        interactor = await container.get(WarmKnowledgeCacheInteractor)

        command = WarmCacheCommand(
            agent_ids=agent_ids,
            priority=priority,
        )

        result = await interactor.execute(command)

        # Log metrics
        self.update_state(
            state="SUCCESS",
            meta={
                "agents_processed": result.agents_processed,
                "entries_cached": result.entries_cached,
                "duration_seconds": result.duration_seconds,
            }
        )

        return {
            "agents_processed": result.agents_processed,
            "entries_cached": result.entries_cached,
            "cache_hits": result.cache_hits,
            "cache_misses": result.cache_misses,
            "duration_seconds": result.duration_seconds,
        }

    try:
        return asyncio.run(_run_task(runner))
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### Interactor Implementation

```python
# src/app/application/ai_brain/cache/interactors.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.application.ai_brain.cache.commands import WarmCacheCommand
from app.application.ai_brain.cache.ports import KnowledgeCacheGateway
from app.domain.ai_brain.ports.agent_configuration_gateway import (
    AgentConfigurationGateway,
)
from app.domain.ai_brain.ports.knowledge_entry_gateway import (
    KnowledgeEntryGateway,
)


@dataclass
class WarmCacheResult:
    """Result of cache warming operation."""
    agents_processed: int
    entries_cached: int
    cache_hits: int
    cache_misses: int
    duration_seconds: float


class WarmKnowledgeCacheInteractor:
    """Warm knowledge cache with frequently accessed data."""

    def __init__(
        self,
        agent_config_gateway: AgentConfigurationGateway,
        knowledge_gateway: KnowledgeEntryGateway,
        cache_gateway: KnowledgeCacheGateway,
    ):
        self._agent_config_gateway = agent_config_gateway
        self._knowledge_gateway = knowledge_gateway
        self._cache_gateway = cache_gateway

    async def execute(self, command: WarmCacheCommand) -> WarmCacheResult:
        """Execute cache warming."""
        start_time = datetime.utcnow()

        # Get agents to warm
        if command.agent_ids:
            agent_ids = [UUID(aid) for aid in command.agent_ids]
            agents = []
            for aid in agent_ids:
                agent = await self._agent_config_gateway.get_by_id(aid)
                if agent and agent.is_active:
                    agents.append(agent)
        else:
            agents = await self._agent_config_gateway.get_all_active()

        agents_processed = 0
        entries_cached = 0
        cache_hits = 0
        cache_misses = 0

        # Determine batch size based on priority
        batch_size = {
            "low": 50,
            "normal": 100,
            "high": 200,
        }.get(command.priority, 100)

        # Warm cache for each agent
        for agent in agents:
            # Get knowledge entries for this agent
            entries = await self._knowledge_gateway.get_by_agent_id(
                agent.id,
                limit=batch_size,
            )

            # Cache each entry
            for entry in entries:
                cache_key = f"knowledge:{agent.id}:{entry.id}"

                # Check if already cached
                cached = await self._cache_gateway.get(cache_key)
                if cached:
                    cache_hits += 1
                    continue

                # Cache the entry
                await self._cache_gateway.set(
                    key=cache_key,
                    value=entry.to_dict(),
                    ttl=3600,  # 1 hour TTL
                )

                entries_cached += 1
                cache_misses += 1

            agents_processed += 1

        # Calculate duration
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()

        return WarmCacheResult(
            agents_processed=agents_processed,
            entries_cached=entries_cached,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            duration_seconds=duration_seconds,
        )
```

#### Command Definition

```python
# src/app/application/ai_brain/cache/commands.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class WarmCacheCommand:
    """Command to warm knowledge cache."""
    agent_ids: Optional[list[str]] = None
    priority: str = "normal"  # low, normal, high
```

#### Beat Schedule Configuration

```python
# In main_tasks.py beat_schedule dict:

"warm-knowledge-cache": {
    "task": "warm_knowledge_cache_task",
    "schedule": crontab(hour=2, minute=0),  # Daily at 2:00 AM UTC
    "options": {
        "queue": "ai_brain",
        "priority": 5,  # Medium priority
    },
    "kwargs": {
        "priority": "high",  # Warm with high priority
    },
},
```

#### Performance Considerations

**Database Query Optimization**:
```sql
-- Use index on agent_id and created_at for efficient querying
CREATE INDEX idx_knowledge_entries_agent_created
ON ai_brain_knowledge_entries(agent_id, created_at DESC);

-- Query plan should use index scan
EXPLAIN ANALYZE
SELECT * FROM ai_brain_knowledge_entries
WHERE agent_id = '...' AND is_active = true
ORDER BY created_at DESC
LIMIT 100;
```

**Redis Memory Management**:
- Use LRU eviction policy: `maxmemory-policy allkeys-lru`
- Set appropriate TTL (1-4 hours based on update frequency)
- Monitor memory usage: `INFO memory`

**Batch Processing**:
```python
# Use pipeline for bulk cache operations
async def cache_batch(entries: list[Entry]) -> None:
    pipeline = redis_client.pipeline()
    for entry in entries:
        pipeline.setex(
            f"knowledge:{entry.agent_id}:{entry.id}",
            3600,
            entry.to_json(),
        )
    await pipeline.execute()
```

#### Monitoring Queries

**Check Cache Warming Success Rate**:
```sql
SELECT
    DATE_TRUNC('day', executed_at) as date,
    COUNT(*) as total_runs,
    COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful_runs,
    AVG((result->>'entries_cached')::int) as avg_entries_cached,
    AVG((result->>'duration_seconds')::float) as avg_duration_seconds
FROM celery_task_results
WHERE task_name = 'warm_knowledge_cache_task'
    AND executed_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', executed_at)
ORDER BY date DESC;
```

**Monitor Cache Hit Rate**:
```sql
SELECT
    agent_id,
    SUM(hits) as total_hits,
    SUM(misses) as total_misses,
    ROUND(100.0 * SUM(hits) / NULLIF(SUM(hits) + SUM(misses), 0), 2) as hit_rate_pct
FROM ai_brain_knowledge_cache_metadata
WHERE updated_at >= NOW() - INTERVAL '24 hours'
GROUP BY agent_id
ORDER BY hit_rate_pct DESC;
```

#### Manual Trigger

```bash
# Warm cache for all agents
celery -A app.infrastructure.celery.app call warm_knowledge_cache_task

# Warm cache for specific agents
celery -A app.infrastructure.celery.app call warm_knowledge_cache_task \
    --kwargs='{"agent_ids": ["agent-uuid-1", "agent-uuid-2"], "priority": "high"}'

# Using Python
from app.infrastructure.celery.tasks.ai_brain_tasks import warm_knowledge_cache_task

# Trigger task
result = warm_knowledge_cache_task.apply_async(
    kwargs={
        "agent_ids": ["agent-uuid-1"],
        "priority": "high",
    },
    queue="ai_brain",
)

# Get result
print(result.get(timeout=300))  # Wait up to 5 minutes
```

---

### Task 2: Integration Health Check

**Purpose**: Continuously monitor external integration health and update status in the database.

**Business Value**:
- Early detection of integration failures
- Automatic failover to backup providers
- Proactive alerting for operations team
- Historical uptime tracking

#### Task Definition

```python
@celery_app.task(
    name="check_integration_health_task",
    bind=True,
    max_retries=5,
    default_retry_delay=60,  # 1 minute
    soft_time_limit=240,  # 4 minutes
    time_limit=300,  # 5 minutes hard limit
)
def check_integration_health_task(
    self: Task,
    integration_ids: Optional[list[str]] = None,
) -> dict[str, any]:
    """
    Check health of external integrations and update status.

    Args:
        integration_ids: Optional list of integration UUIDs to check.
                        If None, checks all active integrations.

    Returns:
        Dict with health check results:
        {
            "integrations_checked": int,
            "healthy_count": int,
            "unhealthy_count": int,
            "degraded_count": int,
            "alerts_generated": int,
            "checks": [
                {
                    "integration_id": str,
                    "name": str,
                    "status": str,  # "healthy", "degraded", "unhealthy"
                    "response_time_ms": float,
                    "error": Optional[str]
                }
            ]
        }

    Raises:
        IntegrationHealthCheckError: If health check fails
    """
    async def runner(container):
        from app.application.ai_brain.monitoring.interactors import (
            CheckIntegrationHealthInteractor,
        )
        from app.application.ai_brain.monitoring.commands import (
            CheckHealthCommand,
        )

        interactor = await container.get(CheckIntegrationHealthInteractor)

        command = CheckHealthCommand(
            integration_ids=integration_ids,
        )

        result = await interactor.execute(command)

        # Update task state with progress
        self.update_state(
            state="SUCCESS",
            meta={
                "integrations_checked": result.integrations_checked,
                "healthy_count": result.healthy_count,
                "unhealthy_count": result.unhealthy_count,
            }
        )

        return result.to_dict()

    try:
        return asyncio.run(_run_task(runner))
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### Interactor Implementation

```python
# src/app/application/ai_brain/monitoring/interactors.py

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.application.ai_brain.monitoring.commands import CheckHealthCommand
from app.domain.ai_brain.ports.integration_configuration_gateway import (
    IntegrationConfigurationGateway,
)
from app.domain.ai_brain.services.integration_health_service import (
    IntegrationHealthService,
)
from app.infrastructure.integrations.health_checker import HealthChecker


@dataclass
class IntegrationHealthCheck:
    """Result of single integration health check."""
    integration_id: UUID
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    error: Optional[str] = None


@dataclass
class CheckHealthResult:
    """Result of integration health checks."""
    integrations_checked: int
    healthy_count: int
    unhealthy_count: int
    degraded_count: int
    alerts_generated: int
    checks: list[IntegrationHealthCheck]

    def to_dict(self) -> dict:
        return {
            "integrations_checked": self.integrations_checked,
            "healthy_count": self.healthy_count,
            "unhealthy_count": self.unhealthy_count,
            "degraded_count": self.degraded_count,
            "alerts_generated": self.alerts_generated,
            "checks": [
                {
                    "integration_id": str(c.integration_id),
                    "name": c.name,
                    "status": c.status,
                    "response_time_ms": c.response_time_ms,
                    "error": c.error,
                }
                for c in self.checks
            ],
        }


class CheckIntegrationHealthInteractor:
    """Check health of external integrations."""

    def __init__(
        self,
        integration_gateway: IntegrationConfigurationGateway,
        health_service: IntegrationHealthService,
        health_checker: HealthChecker,
    ):
        self._integration_gateway = integration_gateway
        self._health_service = health_service
        self._health_checker = health_checker

    async def execute(self, command: CheckHealthCommand) -> CheckHealthResult:
        """Execute integration health checks."""
        # Get integrations to check
        if command.integration_ids:
            integration_ids = [UUID(iid) for iid in command.integration_ids]
            integrations = []
            for iid in integration_ids:
                integration = await self._integration_gateway.get_by_id(iid)
                if integration and integration.is_active:
                    integrations.append(integration)
        else:
            integrations = await self._integration_gateway.get_all_active()

        # Check each integration concurrently
        check_tasks = [
            self._check_single_integration(integration)
            for integration in integrations
        ]

        checks = await asyncio.gather(*check_tasks, return_exceptions=True)

        # Filter out exceptions
        valid_checks = [
            c for c in checks if isinstance(c, IntegrationHealthCheck)
        ]

        # Count status types
        healthy_count = sum(1 for c in valid_checks if c.status == "healthy")
        degraded_count = sum(1 for c in valid_checks if c.status == "degraded")
        unhealthy_count = sum(1 for c in valid_checks if c.status == "unhealthy")

        # Generate alerts for unhealthy integrations
        alerts_generated = await self._generate_alerts(valid_checks)

        return CheckHealthResult(
            integrations_checked=len(integrations),
            healthy_count=healthy_count,
            unhealthy_count=unhealthy_count,
            degraded_count=degraded_count,
            alerts_generated=alerts_generated,
            checks=valid_checks,
        )

    async def _check_single_integration(
        self,
        integration,
    ) -> IntegrationHealthCheck:
        """Check health of a single integration."""
        start_time = datetime.utcnow()

        try:
            # Perform health check
            is_healthy, error_msg = await self._health_checker.check(
                integration.endpoint_url,
                integration.api_key,
                timeout=10.0,
            )

            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Determine status
            if is_healthy and response_time < 1000:
                status = "healthy"
            elif is_healthy and response_time < 3000:
                status = "degraded"
            else:
                status = "unhealthy"

            # Update integration status in database
            await self._health_service.update_health_status(
                integration_id=integration.id,
                status=status,
                response_time_ms=response_time,
                error_message=error_msg,
            )

            return IntegrationHealthCheck(
                integration_id=integration.id,
                name=integration.name,
                status=status,
                response_time_ms=response_time,
                error=error_msg,
            )

        except Exception as exc:
            # Mark as unhealthy
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            await self._health_service.update_health_status(
                integration_id=integration.id,
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(exc),
            )

            return IntegrationHealthCheck(
                integration_id=integration.id,
                name=integration.name,
                status="unhealthy",
                response_time_ms=response_time,
                error=str(exc),
            )

    async def _generate_alerts(
        self,
        checks: list[IntegrationHealthCheck],
    ) -> int:
        """Generate alerts for unhealthy integrations."""
        alerts_count = 0

        for check in checks:
            if check.status == "unhealthy":
                await self._health_service.create_alert(
                    integration_id=check.integration_id,
                    severity="critical",
                    message=f"Integration {check.name} is unhealthy: {check.error}",
                )
                alerts_count += 1
            elif check.status == "degraded":
                await self._health_service.create_alert(
                    integration_id=check.integration_id,
                    severity="warning",
                    message=f"Integration {check.name} is degraded (response time: {check.response_time_ms:.2f}ms)",
                )
                alerts_count += 1

        return alerts_count
```

#### Health Checker Implementation

```python
# src/app/infrastructure/integrations/health_checker.py

import aiohttp
from typing import Tuple


class HealthChecker:
    """Check health of external integrations."""

    async def check(
        self,
        endpoint_url: str,
        api_key: str,
        timeout: float = 10.0,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if integration endpoint is healthy.

        Returns:
            Tuple of (is_healthy, error_message)
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {api_key}"}

                async with session.get(
                    endpoint_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    if response.status == 200:
                        return (True, None)
                    else:
                        return (False, f"HTTP {response.status}")

        except asyncio.TimeoutError:
            return (False, "Request timeout")
        except aiohttp.ClientError as exc:
            return (False, f"Client error: {exc}")
        except Exception as exc:
            return (False, f"Unexpected error: {exc}")
```

#### Beat Schedule Configuration

```python
"check-integration-health": {
    "task": "check_integration_health_task",
    "schedule": crontab(minute="*/5"),  # Every 5 minutes
    "options": {
        "queue": "health_checks",
        "priority": 9,  # High priority
    },
},
```

#### Monitoring Queries

**Integration Uptime Report**:
```sql
SELECT
    ic.name,
    ic.provider_type,
    COUNT(*) FILTER (WHERE status = 'healthy') as healthy_checks,
    COUNT(*) FILTER (WHERE status = 'degraded') as degraded_checks,
    COUNT(*) FILTER (WHERE status = 'unhealthy') as unhealthy_checks,
    COUNT(*) as total_checks,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'healthy') / COUNT(*),
        2
    ) as uptime_percentage,
    AVG(response_time_ms) as avg_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms
FROM ai_brain_integration_configurations ic
JOIN ai_brain_integration_health_logs ihl ON ic.id = ihl.integration_id
WHERE ihl.checked_at >= NOW() - INTERVAL '24 hours'
GROUP BY ic.id, ic.name, ic.provider_type
ORDER BY uptime_percentage ASC;
```

**Recent Integration Failures**:
```sql
SELECT
    ic.name,
    ihl.status,
    ihl.response_time_ms,
    ihl.error_message,
    ihl.checked_at
FROM ai_brain_integration_health_logs ihl
JOIN ai_brain_integration_configurations ic ON ihl.integration_id = ic.id
WHERE ihl.status IN ('degraded', 'unhealthy')
    AND ihl.checked_at >= NOW() - INTERVAL '1 hour'
ORDER BY ihl.checked_at DESC
LIMIT 50;
```

#### Manual Trigger

```bash
# Check all integrations
celery -A app.infrastructure.celery.app call check_integration_health_task

# Check specific integrations
celery -A app.infrastructure.celery.app call check_integration_health_task \
    --kwargs='{"integration_ids": ["integration-uuid-1", "integration-uuid-2"]}'
```

---

### Task 3: Cache Statistics Aggregation

**Purpose**: Aggregate cache hit/miss statistics to identify optimization opportunities.

**Business Value**:
- Identify low-performing cache entries
- Optimize cache TTL settings
- Predict cache memory requirements
- Improve overall system performance

#### Task Definition

```python
@celery_app.task(
    name="aggregate_cache_stats_task",
    bind=True,
    max_retries=3,
    default_retry_delay=120,  # 2 minutes
)
def aggregate_cache_stats_task(
    self: Task,
    time_window: str = "1h",  # "1h", "24h", "7d"
) -> dict[str, any]:
    """
    Aggregate cache statistics for analysis.

    Args:
        time_window: Time window for aggregation ("1h", "24h", "7d")

    Returns:
        Dict with cache statistics:
        {
            "total_requests": int,
            "cache_hits": int,
            "cache_misses": int,
            "hit_rate_pct": float,
            "avg_response_time_ms": float,
            "top_cached_agents": [...],
            "cache_efficiency_score": float
        }
    """
    async def runner(container):
        from app.application.ai_brain.analytics.interactors import (
            AggregateCacheStatsInteractor,
        )
        from app.application.ai_brain.analytics.commands import (
            AggregateCacheStatsCommand,
        )

        interactor = await container.get(AggregateCacheStatsInteractor)

        command = AggregateCacheStatsCommand(
            time_window=time_window,
        )

        result = await interactor.execute(command)

        self.update_state(
            state="SUCCESS",
            meta={
                "hit_rate_pct": result.hit_rate_pct,
                "total_requests": result.total_requests,
            }
        )

        return result.to_dict()

    try:
        return asyncio.run(_run_task(runner))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### Interactor Implementation

```python
# src/app/application/ai_brain/analytics/interactors.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.application.ai_brain.analytics.commands import (
    AggregateCacheStatsCommand,
)
from app.application.ai_brain.cache.ports import KnowledgeCacheGateway
from app.domain.ai_brain.ports.cache_metadata_gateway import (
    CacheMetadataGateway,
)


@dataclass
class CacheStatsResult:
    """Result of cache statistics aggregation."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate_pct: float
    avg_response_time_ms: float
    top_cached_agents: list[dict]
    cache_efficiency_score: float

    def to_dict(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_pct": self.hit_rate_pct,
            "avg_response_time_ms": self.avg_response_time_ms,
            "top_cached_agents": self.top_cached_agents,
            "cache_efficiency_score": self.cache_efficiency_score,
        }


class AggregateCacheStatsInteractor:
    """Aggregate cache statistics for analysis."""

    def __init__(
        self,
        cache_gateway: KnowledgeCacheGateway,
        metadata_gateway: CacheMetadataGateway,
    ):
        self._cache_gateway = cache_gateway
        self._metadata_gateway = metadata_gateway

    async def execute(
        self,
        command: AggregateCacheStatsCommand,
    ) -> CacheStatsResult:
        """Execute cache statistics aggregation."""
        # Parse time window
        window_delta = self._parse_time_window(command.time_window)
        start_time = datetime.utcnow() - window_delta

        # Get cache statistics from Redis
        redis_stats = await self._cache_gateway.get_stats()

        # Get historical stats from database
        db_stats = await self._metadata_gateway.get_stats_since(start_time)

        # Aggregate metrics
        total_requests = db_stats.get("total_requests", 0)
        cache_hits = db_stats.get("hits", 0)
        cache_misses = db_stats.get("misses", 0)

        hit_rate_pct = (
            100.0 * cache_hits / total_requests
            if total_requests > 0
            else 0.0
        )

        avg_response_time_ms = db_stats.get("avg_response_time_ms", 0.0)

        # Get top cached agents
        top_agents = await self._metadata_gateway.get_top_cached_agents(
            start_time=start_time,
            limit=10,
        )

        # Calculate efficiency score (0-100)
        efficiency_score = self._calculate_efficiency_score(
            hit_rate_pct=hit_rate_pct,
            avg_response_time_ms=avg_response_time_ms,
        )

        # Update metadata table with aggregated stats
        await self._metadata_gateway.update_aggregated_stats(
            period_start=start_time,
            period_end=datetime.utcnow(),
            total_requests=total_requests,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate_pct=hit_rate_pct,
            avg_response_time_ms=avg_response_time_ms,
        )

        return CacheStatsResult(
            total_requests=total_requests,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate_pct=hit_rate_pct,
            avg_response_time_ms=avg_response_time_ms,
            top_cached_agents=top_agents,
            cache_efficiency_score=efficiency_score,
        )

    def _parse_time_window(self, window: str) -> timedelta:
        """Parse time window string to timedelta."""
        mapping = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
        }
        return mapping.get(window, timedelta(hours=1))

    def _calculate_efficiency_score(
        self,
        hit_rate_pct: float,
        avg_response_time_ms: float,
    ) -> float:
        """
        Calculate cache efficiency score (0-100).

        Formula:
        - Hit rate contributes 70%
        - Response time contributes 30%
        """
        # Normalize response time (target: <100ms)
        response_score = max(0, 100 - (avg_response_time_ms / 10))

        # Weighted average
        efficiency = (0.7 * hit_rate_pct) + (0.3 * response_score)

        return round(efficiency, 2)
```

#### Beat Schedule Configuration

```python
"aggregate-cache-stats": {
    "task": "aggregate_cache_stats_task",
    "schedule": crontab(minute=5),  # Every hour at :05
    "options": {
        "queue": "analytics",
        "priority": 4,  # Medium-low priority
    },
    "kwargs": {
        "time_window": "1h",
    },
},
```

#### Monitoring Queries

**Cache Performance Trends**:
```sql
SELECT
    DATE_TRUNC('hour', period_start) as hour,
    total_requests,
    cache_hits,
    cache_misses,
    hit_rate_pct,
    avg_response_time_ms
FROM ai_brain_knowledge_cache_metadata
WHERE period_start >= NOW() - INTERVAL '24 hours'
ORDER BY period_start DESC;
```

**Identify Low-Performing Cache Entries**:
```sql
SELECT
    agent_id,
    cache_key,
    hits,
    misses,
    ROUND(100.0 * hits / NULLIF(hits + misses, 0), 2) as hit_rate_pct,
    last_accessed_at
FROM ai_brain_knowledge_cache_metadata
WHERE last_accessed_at >= NOW() - INTERVAL '7 days'
    AND (hits + misses) > 100  -- Significant usage
ORDER BY hit_rate_pct ASC
LIMIT 20;
```

---

### Task 4: Prompt Performance Analysis

**Purpose**: Analyze A/B test results for prompts and identify winning variants.

**Business Value**:
- Data-driven prompt optimization
- Improve AI response quality
- Reduce token costs with better prompts
- Automated prompt variant selection

#### Task Definition

```python
@celery_app.task(
    name="analyze_prompt_performance_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def analyze_prompt_performance_task(
    self: Task,
    prompt_ids: Optional[list[str]] = None,
) -> dict[str, any]:
    """
    Analyze prompt performance and A/B test results.

    Args:
        prompt_ids: Optional list of prompt UUIDs to analyze.
                   If None, analyzes all prompts with active A/B tests.

    Returns:
        Dict with analysis results:
        {
            "prompts_analyzed": int,
            "winning_variants": [
                {
                    "prompt_id": str,
                    "winning_variant": str,
                    "improvement_pct": float,
                    "confidence_score": float
                }
            ],
            "recommendations": [...],
            "total_token_savings": int
        }
    """
    async def runner(container):
        from app.application.ai_brain.analytics.interactors import (
            AnalyzePromptPerformanceInteractor,
        )
        from app.application.ai_brain.analytics.commands import (
            AnalyzePromptPerformanceCommand,
        )

        interactor = await container.get(AnalyzePromptPerformanceInteractor)

        command = AnalyzePromptPerformanceCommand(
            prompt_ids=prompt_ids,
        )

        result = await interactor.execute(command)

        self.update_state(
            state="SUCCESS",
            meta={
                "prompts_analyzed": result.prompts_analyzed,
                "winning_variants_count": len(result.winning_variants),
            }
        )

        return result.to_dict()

    try:
        return asyncio.run(_run_task(runner))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### Interactor Implementation

```python
# src/app/application/ai_brain/analytics/interactors.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import statistics

from app.application.ai_brain.analytics.commands import (
    AnalyzePromptPerformanceCommand,
)
from app.domain.ai_brain.ports.prompt_template_gateway import (
    PromptTemplateGateway,
)
from app.domain.ai_brain.ports.prompt_usage_gateway import (
    PromptUsageGateway,
)


@dataclass
class WinningVariant:
    """Information about a winning prompt variant."""
    prompt_id: UUID
    prompt_name: str
    winning_variant: str
    control_variant: str
    improvement_pct: float
    confidence_score: float
    sample_size: int
    avg_response_quality: float
    token_savings: int


@dataclass
class AnalyzePromptPerformanceResult:
    """Result of prompt performance analysis."""
    prompts_analyzed: int
    winning_variants: list[WinningVariant]
    recommendations: list[str]
    total_token_savings: int

    def to_dict(self) -> dict:
        return {
            "prompts_analyzed": self.prompts_analyzed,
            "winning_variants": [
                {
                    "prompt_id": str(wv.prompt_id),
                    "prompt_name": wv.prompt_name,
                    "winning_variant": wv.winning_variant,
                    "improvement_pct": wv.improvement_pct,
                    "confidence_score": wv.confidence_score,
                    "sample_size": wv.sample_size,
                    "avg_response_quality": wv.avg_response_quality,
                    "token_savings": wv.token_savings,
                }
                for wv in self.winning_variants
            ],
            "recommendations": self.recommendations,
            "total_token_savings": self.total_token_savings,
        }


class AnalyzePromptPerformanceInteractor:
    """Analyze prompt performance and A/B test results."""

    MIN_SAMPLE_SIZE = 100  # Minimum usage count for statistical significance
    CONFIDENCE_THRESHOLD = 0.95  # 95% confidence required

    def __init__(
        self,
        prompt_gateway: PromptTemplateGateway,
        usage_gateway: PromptUsageGateway,
    ):
        self._prompt_gateway = prompt_gateway
        self._usage_gateway = usage_gateway

    async def execute(
        self,
        command: AnalyzePromptPerformanceCommand,
    ) -> AnalyzePromptPerformanceResult:
        """Execute prompt performance analysis."""
        # Get prompts to analyze
        if command.prompt_ids:
            prompt_ids = [UUID(pid) for pid in command.prompt_ids]
            prompts = []
            for pid in prompt_ids:
                prompt = await self._prompt_gateway.get_by_id(pid)
                if prompt and prompt.ab_testing_enabled:
                    prompts.append(prompt)
        else:
            prompts = await self._prompt_gateway.get_all_with_ab_testing()

        winning_variants = []
        recommendations = []
        total_token_savings = 0

        # Analyze each prompt
        for prompt in prompts:
            # Get usage data for last 7 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            usage_data = await self._usage_gateway.get_by_prompt_id(
                prompt_id=prompt.id,
                start_date=start_date,
                end_date=end_date,
            )

            # Group by variant
            variant_stats = self._group_by_variant(usage_data)

            # Skip if insufficient data
            if not self._has_sufficient_data(variant_stats):
                recommendations.append(
                    f"Prompt '{prompt.name}': Insufficient data for analysis "
                    f"(need {self.MIN_SAMPLE_SIZE}+ samples per variant)"
                )
                continue

            # Perform statistical analysis
            winning_variant = self._identify_winning_variant(
                variant_stats,
                prompt.name,
            )

            if winning_variant:
                winning_variants.append(winning_variant)
                total_token_savings += winning_variant.token_savings

                # Generate recommendation
                recommendations.append(
                    f"Activate variant '{winning_variant.winning_variant}' "
                    f"for prompt '{prompt.name}' "
                    f"({winning_variant.improvement_pct:.1f}% improvement, "
                    f"{winning_variant.confidence_score:.0%} confidence)"
                )

        return AnalyzePromptPerformanceResult(
            prompts_analyzed=len(prompts),
            winning_variants=winning_variants,
            recommendations=recommendations,
            total_token_savings=total_token_savings,
        )

    def _group_by_variant(self, usage_data: list) -> dict:
        """Group usage data by variant."""
        variant_stats = {}

        for usage in usage_data:
            variant = usage.variant_name

            if variant not in variant_stats:
                variant_stats[variant] = {
                    "usages": [],
                    "response_qualities": [],
                    "token_counts": [],
                }

            variant_stats[variant]["usages"].append(usage)
            variant_stats[variant]["response_qualities"].append(
                usage.response_quality_score
            )
            variant_stats[variant]["token_counts"].append(
                usage.total_tokens
            )

        return variant_stats

    def _has_sufficient_data(self, variant_stats: dict) -> bool:
        """Check if there's sufficient data for analysis."""
        for variant, stats in variant_stats.items():
            if len(stats["usages"]) < self.MIN_SAMPLE_SIZE:
                return False
        return len(variant_stats) >= 2  # Need at least 2 variants

    def _identify_winning_variant(
        self,
        variant_stats: dict,
        prompt_name: str,
    ) -> Optional[WinningVariant]:
        """Identify winning variant using statistical analysis."""
        # Calculate metrics for each variant
        variant_metrics = {}

        for variant, stats in variant_stats.items():
            variant_metrics[variant] = {
                "sample_size": len(stats["usages"]),
                "avg_quality": statistics.mean(stats["response_qualities"]),
                "quality_stdev": statistics.stdev(stats["response_qualities"]),
                "avg_tokens": statistics.mean(stats["token_counts"]),
            }

        # Identify control and treatment
        control_variant = min(variant_metrics.keys())  # Alphabetically first
        treatment_variants = [
            v for v in variant_metrics.keys() if v != control_variant
        ]

        control_metrics = variant_metrics[control_variant]

        # Find best performing treatment
        best_treatment = None
        best_improvement = 0
        best_confidence = 0

        for treatment_variant in treatment_variants:
            treatment_metrics = variant_metrics[treatment_variant]

            # Calculate improvement
            quality_improvement = (
                (treatment_metrics["avg_quality"] - control_metrics["avg_quality"])
                / control_metrics["avg_quality"]
                * 100
            )

            # Calculate confidence using two-sample t-test approximation
            # Simplified version - in production use scipy.stats.ttest_ind
            pooled_stdev = (
                (control_metrics["quality_stdev"] + treatment_metrics["quality_stdev"])
                / 2
            )

            # Z-score approximation
            z_score = (
                (treatment_metrics["avg_quality"] - control_metrics["avg_quality"])
                / (pooled_stdev / (control_metrics["sample_size"] ** 0.5))
            )

            # Confidence (simplified)
            confidence = min(0.99, abs(z_score) / 3)  # Rough approximation

            # Check if this is the best treatment
            if (
                quality_improvement > best_improvement
                and confidence >= self.CONFIDENCE_THRESHOLD
            ):
                best_treatment = treatment_variant
                best_improvement = quality_improvement
                best_confidence = confidence

        # Return winning variant if found
        if best_treatment:
            treatment_metrics = variant_metrics[best_treatment]

            # Calculate token savings
            token_diff = control_metrics["avg_tokens"] - treatment_metrics["avg_tokens"]
            token_savings = int(token_diff * treatment_metrics["sample_size"])

            # Extract prompt_id from first usage
            first_usage = variant_stats[best_treatment]["usages"][0]

            return WinningVariant(
                prompt_id=first_usage.prompt_id,
                prompt_name=prompt_name,
                winning_variant=best_treatment,
                control_variant=control_variant,
                improvement_pct=best_improvement,
                confidence_score=best_confidence,
                sample_size=treatment_metrics["sample_size"],
                avg_response_quality=treatment_metrics["avg_quality"],
                token_savings=token_savings,
            )

        return None
```

#### Beat Schedule Configuration

```python
"analyze-prompt-performance": {
    "task": "analyze_prompt_performance_task",
    "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM UTC
    "options": {
        "queue": "ai_brain",
        "priority": 3,  # Low-medium priority
    },
},
```

#### Monitoring Queries

**Prompt A/B Test Results**:
```sql
SELECT
    pt.name as prompt_name,
    pu.variant_name,
    COUNT(*) as usage_count,
    AVG(pu.response_quality_score) as avg_quality,
    AVG(pu.total_tokens) as avg_tokens,
    STDDEV(pu.response_quality_score) as quality_stddev
FROM ai_brain_prompt_usage pu
JOIN ai_brain_prompt_templates pt ON pu.prompt_id = pt.id
WHERE pu.created_at >= NOW() - INTERVAL '7 days'
    AND pt.ab_testing_enabled = true
GROUP BY pt.id, pt.name, pu.variant_name
ORDER BY pt.name, pu.variant_name;
```

**Token Savings from Optimizations**:
```sql
SELECT
    DATE_TRUNC('day', analyzed_at) as date,
    SUM(token_savings) as daily_token_savings,
    COUNT(DISTINCT prompt_id) as prompts_optimized,
    AVG(improvement_pct) as avg_improvement_pct
FROM ai_brain_prompt_analysis_results
WHERE analyzed_at >= NOW() - INTERVAL '30 days'
    AND winning_variant IS NOT NULL
GROUP BY DATE_TRUNC('day', analyzed_at)
ORDER BY date DESC;
```

#### Manual Trigger

```bash
# Analyze all prompts with A/B testing
celery -A app.infrastructure.celery.app call analyze_prompt_performance_task

# Analyze specific prompts
celery -A app.infrastructure.celery.app call analyze_prompt_performance_task \
    --kwargs='{"prompt_ids": ["prompt-uuid-1", "prompt-uuid-2"]}'
```

---

## Configuration

### Celery App Configuration

```python
# src/app/infrastructure/celery/app.py

from celery import Celery
from kombu import Exchange, Queue
from app.setup.config.settings import load_settings


settings = load_settings()

# Create Celery app
celery_app = Celery(
    "anvil_backend",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_backend=settings.redis_url,
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store task metadata

    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Requeue on worker crash
    task_track_started=True,  # Track task started state

    # Worker settings
    worker_prefetch_multiplier=1,  # Prefetch 1 task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_disable_rate_limits=False,

    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Queue definitions
    task_queues=(
        Queue("ai_brain", Exchange("ai_brain"), routing_key="ai_brain"),
        Queue("health_checks", Exchange("health"), routing_key="health"),
        Queue("analytics", Exchange("analytics"), routing_key="analytics"),
        Queue("maintenance", Exchange("maintenance"), routing_key="maintenance"),
        Queue("admin", Exchange("admin"), routing_key="admin"),
    ),

    # Default queue
    task_default_queue="ai_brain",
    task_default_exchange="ai_brain",
    task_default_routing_key="ai_brain",

    # Task routes
    task_routes={
        "warm_knowledge_cache_task": {"queue": "ai_brain"},
        "check_integration_health_task": {"queue": "health_checks"},
        "aggregate_cache_stats_task": {"queue": "analytics"},
        "analyze_prompt_performance_task": {"queue": "ai_brain"},
        "audit_configuration_changes_task": {"queue": "admin"},
        "check_knowledge_consistency_task": {"queue": "maintenance"},
        "cleanup_expired_cache_task": {"queue": "maintenance"},
    },
)
```

### Environment Configuration

```toml
# config/local/config.toml

[celery]
broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"
worker_concurrency = 4
worker_max_tasks_per_child = 1000
task_soft_time_limit = 300  # 5 minutes
task_time_limit = 600  # 10 minutes

[celery.queues]
ai_brain = {priority = 5, max_length = 10000}
health_checks = {priority = 9, max_length = 1000}
analytics = {priority = 3, max_length = 5000}
maintenance = {priority = 1, max_length = 2000}
admin = {priority = 7, max_length = 500}
```

---

---

### Task 5: Configuration Audit Task

**Purpose**: Generate audit reports for configuration changes to maintain compliance and track system modifications.

**Business Value**:
- Compliance with SOC 2 and audit requirements
- Track who changed what and when
- Identify unauthorized changes
- Historical configuration tracking

#### Task Definition

```python
@celery_app.task(
    name="audit_configuration_changes_task",
    bind=True,
    max_retries=2,
    default_retry_delay=600,  # 10 minutes
)
def audit_configuration_changes_task(
    self: Task,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, any]:
    """
    Generate configuration change audit reports.

    Args:
        start_date: Start date in ISO format (default: 7 days ago)
        end_date: End date in ISO format (default: now)

    Returns:
        Dict with audit results:
        {
            "total_changes": int,
            "by_user": {...},
            "by_entity_type": {...},
            "critical_changes": [...],
            "report_path": str
        }
    """
    async def runner(container):
        from app.application.ai_brain.audit.interactors import (
            AuditConfigurationChangesInteractor,
        )
        from app.application.ai_brain.audit.commands import (
            AuditConfigurationCommand,
        )
        from datetime import datetime, timedelta

        interactor = await container.get(AuditConfigurationChangesInteractor)

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.utcnow() - timedelta(days=7)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.utcnow()

        command = AuditConfigurationCommand(
            start_date=start,
            end_date=end,
        )

        result = await interactor.execute(command)

        self.update_state(
            state="SUCCESS",
            meta={
                "total_changes": result.total_changes,
                "critical_changes": len(result.critical_changes),
            }
        )

        return result.to_dict()

    try:
        return asyncio.run(_run_task(runner))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### Interactor Implementation

```python
# src/app/application/ai_brain/audit/interactors.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from collections import defaultdict

from app.application.ai_brain.audit.commands import AuditConfigurationCommand
from app.domain.ai_brain.ports.configuration_change_log_gateway import (
    ConfigurationChangeLogGateway,
)


@dataclass
class AuditConfigurationResult:
    """Result of configuration audit."""
    total_changes: int
    by_user: dict[str, int]
    by_entity_type: dict[str, int]
    critical_changes: list[dict]
    report_path: str

    def to_dict(self) -> dict:
        return {
            "total_changes": self.total_changes,
            "by_user": self.by_user,
            "by_entity_type": self.by_entity_type,
            "critical_changes": self.critical_changes,
            "report_path": self.report_path,
        }


class AuditConfigurationChangesInteractor:
    """Generate configuration change audit reports."""

    def __init__(
        self,
        change_log_gateway: ConfigurationChangeLogGateway,
    ):
        self._change_log_gateway = change_log_gateway

    async def execute(
        self,
        command: AuditConfigurationCommand,
    ) -> AuditConfigurationResult:
        """Execute configuration audit."""
        # Get all changes in date range
        changes = await self._change_log_gateway.get_changes_in_range(
            start_date=command.start_date,
            end_date=command.end_date,
        )

        # Aggregate by user
        by_user = defaultdict(int)
        for change in changes:
            by_user[change.modified_by] += 1

        # Aggregate by entity type
        by_entity_type = defaultdict(int)
        for change in changes:
            by_entity_type[change.entity_type] += 1

        # Identify critical changes
        critical_changes = [
            {
                "entity_type": c.entity_type,
                "entity_id": str(c.entity_id),
                "change_type": c.change_type,
                "modified_by": c.modified_by,
                "modified_at": c.modified_at.isoformat(),
                "changes": c.changes_json,
            }
            for c in changes
            if c.is_critical
        ]

        # Generate report file
        report_path = await self._generate_report(
            changes=changes,
            start_date=command.start_date,
            end_date=command.end_date,
        )

        return AuditConfigurationResult(
            total_changes=len(changes),
            by_user=dict(by_user),
            by_entity_type=dict(by_entity_type),
            critical_changes=critical_changes,
            report_path=report_path,
        )

    async def _generate_report(
        self,
        changes: list,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Generate CSV report file."""
        import csv
        from pathlib import Path

        # Create reports directory
        reports_dir = Path("/tmp/ai_brain_audit_reports")
        reports_dir.mkdir(exist_ok=True)

        # Generate filename
        filename = (
            f"config_audit_{start_date.strftime('%Y%m%d')}_"
            f"{end_date.strftime('%Y%m%d')}.csv"
        )
        report_path = reports_dir / filename

        # Write CSV
        with open(report_path, "w", newline="") as csvfile:
            fieldnames = [
                "modified_at",
                "entity_type",
                "entity_id",
                "change_type",
                "modified_by",
                "is_critical",
                "changes",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for change in changes:
                writer.writerow({
                    "modified_at": change.modified_at.isoformat(),
                    "entity_type": change.entity_type,
                    "entity_id": str(change.entity_id),
                    "change_type": change.change_type,
                    "modified_by": change.modified_by,
                    "is_critical": change.is_critical,
                    "changes": change.changes_json,
                })

        return str(report_path)
```

#### Beat Schedule Configuration

```python
"audit-configuration-changes": {
    "task": "audit_configuration_changes_task",
    "schedule": crontab(hour=1, minute=0, day_of_week=1),  # Weekly Monday 1:00 AM
    "options": {
        "queue": "admin",
        "priority": 6,  # Medium-high priority
    },
},
```

#### Monitoring Queries

**Configuration Change Summary**:
```sql
SELECT
    DATE_TRUNC('day', modified_at) as date,
    entity_type,
    change_type,
    COUNT(*) as change_count,
    COUNT(DISTINCT modified_by) as unique_users
FROM ai_brain_configuration_change_log
WHERE modified_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', modified_at), entity_type, change_type
ORDER BY date DESC, change_count DESC;
```

**Critical Changes Requiring Review**:
```sql
SELECT
    modified_at,
    entity_type,
    entity_id,
    change_type,
    modified_by,
    changes_json
FROM ai_brain_configuration_change_log
WHERE is_critical = true
    AND modified_at >= NOW() - INTERVAL '7 days'
ORDER BY modified_at DESC;
```

---

### Task 6: Knowledge Consistency Check

**Purpose**: Verify consistency between database and cache to prevent data corruption.

**Business Value**:
- Prevent serving stale data
- Detect cache invalidation issues
- Auto-repair inconsistencies
- Maintain data integrity

#### Task Definition

```python
@celery_app.task(
    name="check_knowledge_consistency_task",
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
    soft_time_limit=1800,  # 30 minutes soft limit
    time_limit=2400,  # 40 minutes hard limit
)
def check_knowledge_consistency_task(self: Task) -> dict[str, any]:
    """
    Check consistency between database and cache.

    Returns:
        Dict with consistency check results:
        {
            "total_checked": int,
            "consistent_count": int,
            "inconsistent_count": int,
            "repaired_count": int,
            "errors": [...]
        }
    """
    async def runner(container):
        from app.application.ai_brain.maintenance.interactors import (
            CheckKnowledgeConsistencyInteractor,
        )

        interactor = await container.get(CheckKnowledgeConsistencyInteractor)

        result = await interactor.execute()

        self.update_state(
            state="SUCCESS",
            meta={
                "total_checked": result.total_checked,
                "inconsistent_count": result.inconsistent_count,
                "repaired_count": result.repaired_count,
            }
        )

        return result.to_dict()

    try:
        return asyncio.run(_run_task(runner))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### Interactor Implementation

```python
# src/app/application/ai_brain/maintenance/interactors.py

from dataclasses import dataclass
from typing import Optional
import json

from app.application.ai_brain.cache.ports import KnowledgeCacheGateway
from app.domain.ai_brain.ports.knowledge_entry_gateway import (
    KnowledgeEntryGateway,
)


@dataclass
class ConsistencyCheckResult:
    """Result of consistency check."""
    total_checked: int
    consistent_count: int
    inconsistent_count: int
    repaired_count: int
    errors: list[dict]

    def to_dict(self) -> dict:
        return {
            "total_checked": self.total_checked,
            "consistent_count": self.consistent_count,
            "inconsistent_count": self.inconsistent_count,
            "repaired_count": self.repaired_count,
            "errors": self.errors,
        }


class CheckKnowledgeConsistencyInteractor:
    """Check consistency between database and cache."""

    def __init__(
        self,
        knowledge_gateway: KnowledgeEntryGateway,
        cache_gateway: KnowledgeCacheGateway,
    ):
        self._knowledge_gateway = knowledge_gateway
        self._cache_gateway = cache_gateway

    async def execute(self) -> ConsistencyCheckResult:
        """Execute consistency check."""
        total_checked = 0
        consistent_count = 0
        inconsistent_count = 0
        repaired_count = 0
        errors = []

        # Get all knowledge entries (in batches)
        batch_size = 1000
        offset = 0

        while True:
            entries = await self._knowledge_gateway.get_all(
                limit=batch_size,
                offset=offset,
            )

            if not entries:
                break

            # Check each entry
            for entry in entries:
                total_checked += 1

                cache_key = f"knowledge:{entry.agent_id}:{entry.id}"

                # Get cached version
                cached_data = await self._cache_gateway.get(cache_key)

                if cached_data is None:
                    # Missing from cache - not necessarily inconsistent
                    consistent_count += 1
                    continue

                # Compare database vs cache
                try:
                    cached_entry = json.loads(cached_data)

                    # Check critical fields
                    if self._is_consistent(entry, cached_entry):
                        consistent_count += 1
                    else:
                        inconsistent_count += 1

                        # Auto-repair by updating cache
                        await self._cache_gateway.set(
                            key=cache_key,
                            value=entry.to_json(),
                            ttl=3600,
                        )
                        repaired_count += 1

                        errors.append({
                            "entry_id": str(entry.id),
                            "agent_id": str(entry.agent_id),
                            "issue": "Cache data inconsistent with database",
                            "action": "Repaired",
                        })

                except Exception as exc:
                    errors.append({
                        "entry_id": str(entry.id),
                        "agent_id": str(entry.agent_id),
                        "issue": f"Error checking consistency: {exc}",
                        "action": "Skipped",
                    })

            offset += batch_size

        return ConsistencyCheckResult(
            total_checked=total_checked,
            consistent_count=consistent_count,
            inconsistent_count=inconsistent_count,
            repaired_count=repaired_count,
            errors=errors,
        )

    def _is_consistent(self, db_entry, cached_entry: dict) -> bool:
        """Check if database entry matches cache."""
        # Compare critical fields
        critical_fields = [
            "id",
            "agent_id",
            "content_hash",
            "updated_at",
            "is_active",
        ]

        for field in critical_fields:
            db_value = getattr(db_entry, field, None)
            cache_value = cached_entry.get(field)

            # Convert for comparison
            if hasattr(db_value, "isoformat"):
                db_value = db_value.isoformat()

            if str(db_value) != str(cache_value):
                return False

        return True
```

#### Beat Schedule Configuration

```python
"check-knowledge-consistency": {
    "task": "check_knowledge_consistency_task",
    "schedule": crontab(hour=4, minute=0),  # Daily at 4:00 AM UTC
    "options": {
        "queue": "maintenance",
        "priority": 2,  # Low-medium priority
    },
},
```

#### Monitoring Queries

**Consistency Check History**:
```sql
SELECT
    DATE_TRUNC('day', executed_at) as date,
    AVG((result->>'total_checked')::int) as avg_checked,
    AVG((result->>'inconsistent_count')::int) as avg_inconsistent,
    AVG((result->>'repaired_count')::int) as avg_repaired
FROM celery_task_results
WHERE task_name = 'check_knowledge_consistency_task'
    AND executed_at >= NOW() - INTERVAL '30 days'
    AND status = 'SUCCESS'
GROUP BY DATE_TRUNC('day', executed_at)
ORDER BY date DESC;
```

---

### Task 7: Expired Cache Cleanup

**Purpose**: Remove stale cache entries to free up Redis memory and improve performance.

**Business Value**:
- Optimize Redis memory usage
- Improve cache lookup performance
- Prevent memory exhaustion
- Automatic cache maintenance

#### Task Definition

```python
@celery_app.task(
    name="cleanup_expired_cache_task",
    bind=True,
    max_retries=3,
    default_retry_delay=180,  # 3 minutes
)
def cleanup_expired_cache_task(self: Task) -> dict[str, any]:
    """
    Clean up expired cache entries.

    Returns:
        Dict with cleanup results:
        {
            "keys_scanned": int,
            "keys_deleted": int,
            "memory_freed_mb": float,
            "orphaned_keys": int
        }
    """
    async def runner(container):
        from app.application.ai_brain.maintenance.interactors import (
            CleanupExpiredCacheInteractor,
        )

        interactor = await container.get(CleanupExpiredCacheInteractor)

        result = await interactor.execute()

        self.update_state(
            state="SUCCESS",
            meta={
                "keys_deleted": result.keys_deleted,
                "memory_freed_mb": result.memory_freed_mb,
            }
        )

        return result.to_dict()

    try:
        return asyncio.run(_run_task(runner))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### Interactor Implementation

```python
# src/app/application/ai_brain/maintenance/interactors.py

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.application.ai_brain.cache.ports import KnowledgeCacheGateway
from app.domain.ai_brain.ports.cache_metadata_gateway import (
    CacheMetadataGateway,
)


@dataclass
class CleanupExpiredCacheResult:
    """Result of cache cleanup."""
    keys_scanned: int
    keys_deleted: int
    memory_freed_mb: float
    orphaned_keys: int

    def to_dict(self) -> dict:
        return {
            "keys_scanned": self.keys_scanned,
            "keys_deleted": self.keys_deleted,
            "memory_freed_mb": self.memory_freed_mb,
            "orphaned_keys": self.orphaned_keys,
        }


class CleanupExpiredCacheInteractor:
    """Clean up expired cache entries."""

    def __init__(
        self,
        cache_gateway: KnowledgeCacheGateway,
        metadata_gateway: CacheMetadataGateway,
    ):
        self._cache_gateway = cache_gateway
        self._metadata_gateway = metadata_gateway

    async def execute(self) -> CleanupExpiredCacheResult:
        """Execute cache cleanup."""
        keys_scanned = 0
        keys_deleted = 0
        orphaned_keys = 0

        # Get memory before cleanup
        memory_before = await self._cache_gateway.get_memory_usage()

        # Scan for knowledge cache keys
        pattern = "knowledge:*"
        cursor = 0

        while True:
            cursor, keys = await self._cache_gateway.scan(
                cursor=cursor,
                match=pattern,
                count=1000,
            )

            keys_scanned += len(keys)

            # Check each key
            for key in keys:
                # Get TTL
                ttl = await self._cache_gateway.ttl(key)

                # Delete if expired (TTL = -1) or about to expire (< 60s)
                if ttl == -1 or (ttl != -2 and ttl < 60):
                    await self._cache_gateway.delete(key)
                    keys_deleted += 1

                # Check if orphaned (no corresponding database entry)
                # Extract IDs from key: "knowledge:{agent_id}:{entry_id}"
                parts = key.split(":")
                if len(parts) == 3:
                    agent_id = parts[1]
                    entry_id = parts[2]

                    # Check if entry exists in metadata
                    exists = await self._metadata_gateway.exists(
                        agent_id=agent_id,
                        entry_id=entry_id,
                    )

                    if not exists:
                        await self._cache_gateway.delete(key)
                        keys_deleted += 1
                        orphaned_keys += 1

            # Break if we've scanned all keys
            if cursor == 0:
                break

        # Get memory after cleanup
        memory_after = await self._cache_gateway.get_memory_usage()
        memory_freed_mb = (memory_before - memory_after) / (1024 * 1024)

        # Update metadata
        await self._metadata_gateway.record_cleanup(
            cleaned_at=datetime.utcnow(),
            keys_deleted=keys_deleted,
            memory_freed_bytes=memory_before - memory_after,
        )

        return CleanupExpiredCacheResult(
            keys_scanned=keys_scanned,
            keys_deleted=keys_deleted,
            memory_freed_mb=round(memory_freed_mb, 2),
            orphaned_keys=orphaned_keys,
        )
```

#### Beat Schedule Configuration

```python
"cleanup-expired-cache": {
    "task": "cleanup_expired_cache_task",
    "schedule": crontab(hour=5, minute=0),  # Daily at 5:00 AM UTC
    "options": {
        "queue": "maintenance",
        "priority": 1,  # Low priority
    },
},
```

#### Monitoring Queries

**Cache Cleanup Effectiveness**:
```sql
SELECT
    DATE_TRUNC('day', cleaned_at) as date,
    SUM(keys_deleted) as total_keys_deleted,
    SUM(memory_freed_bytes) / (1024 * 1024) as total_memory_freed_mb,
    COUNT(*) as cleanup_runs
FROM ai_brain_cache_cleanup_log
WHERE cleaned_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', cleaned_at)
ORDER BY date DESC;
```

---

## Task Dependencies

### Dependency Graph

```
┌─────────────────────────────────────────┐
│   warm_knowledge_cache_task             │
│   (Daily 2:00 AM)                       │
└────────────────┬────────────────────────┘
                 │
                 ├── Depends on: None
                 │
                 └── Enables: Fast cache lookups
                             for users


┌─────────────────────────────────────────┐
│   check_integration_health_task         │
│   (Every 5 minutes)                     │
└────────────────┬────────────────────────┘
                 │
                 ├── Depends on: Integration configs
                 │
                 └── Triggers: Alerts for failures


┌─────────────────────────────────────────┐
│   aggregate_cache_stats_task            │
│   (Hourly at :05)                       │
└────────────────┬────────────────────────┘
                 │
                 ├── Depends on: Cache operations
                 │
                 └── Updates: Cache metadata table


┌─────────────────────────────────────────┐
│   analyze_prompt_performance_task       │
│   (Daily 3:00 AM)                       │
└────────────────┬────────────────────────┘
                 │
                 ├── Depends on: 7 days of usage data
                 │
                 └── Generates: Optimization recommendations


┌─────────────────────────────────────────┐
│   audit_configuration_changes_task      │
│   (Weekly Monday 1:00 AM)               │
└────────────────┬────────────────────────┘
                 │
                 ├── Depends on: Change log entries
                 │
                 └── Generates: CSV audit reports


┌─────────────────────────────────────────┐
│   check_knowledge_consistency_task      │
│   (Daily 4:00 AM)                       │
└────────────────┬────────────────────────┘
                 │
                 ├── Depends on: Database + Cache
                 │
                 └── Repairs: Inconsistent entries


┌─────────────────────────────────────────┐
│   cleanup_expired_cache_task            │
│   (Daily 5:00 AM)                       │
└────────────────┬────────────────────────┘
                 │
                 ├── Runs After: Consistency check
                 │
                 └── Frees: Redis memory
```

### Task Execution Order

**Daily Schedule (Typical Day)**:

```
00:00 UTC - [Maintenance] cleanup_expired_sessions
01:00 UTC - [Admin] audit_configuration_changes_task (Monday only)
02:00 UTC - [AI Brain] warm_knowledge_cache_task
03:00 UTC - [AI Brain] analyze_prompt_performance_task
04:00 UTC - [Maintenance] check_knowledge_consistency_task
05:00 UTC - [Maintenance] cleanup_expired_cache_task

Every 5 min - [Health] check_integration_health_task
Every hour - [Analytics] aggregate_cache_stats_task (at :05)
```

### Chain Dependencies

```python
# Example: Chain cache warming → stats aggregation → cleanup

from celery import chain

# Create task chain
cache_maintenance_chain = chain(
    warm_knowledge_cache_task.s(),
    aggregate_cache_stats_task.s(),
    cleanup_expired_cache_task.s(),
)

# Execute chain
result = cache_maintenance_chain.apply_async()
```

---

## Error Handling

### Retry Strategies

**Exponential Backoff Pattern**:

```python
@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
)
def example_task(self, arg):
    try:
        # Task logic
        pass
    except SomeRecoverableError as exc:
        # Retry with exponential backoff
        # Attempt 1: 60s, 2: 120s, 3: 240s, 4: 480s, 5: 960s
        raise self.retry(
            exc=exc,
            countdown=2 ** self.request.retries * 60
        )
    except SomeFatalError as exc:
        # Don't retry, log and fail
        logger.error(f"Fatal error in task: {exc}")
        raise
```

### Error Classification

**1. Transient Errors** (Retry):
- Network timeouts
- Database connection failures
- Redis connection errors
- External API rate limits

**2. Permanent Errors** (Don't Retry):
- Invalid configuration
- Missing required data
- Permission errors
- Logic errors

**3. Degraded State** (Retry with Alerts):
- High response times
- Partial failures
- Resource constraints

### Error Handling Example

```python
@celery_app.task(bind=True, max_retries=3)
def robust_task(self, arg):
    """Task with comprehensive error handling."""
    try:
        # Main logic
        result = perform_operation(arg)
        return result

    except TransientError as exc:
        # Log and retry
        logger.warning(
            f"Transient error in task {self.request.id}: {exc}"
        )
        raise self.retry(exc=exc, countdown=min(2 ** self.request.retries * 60, 3600))

    except PermanentError as exc:
        # Log as error and fail
        logger.error(
            f"Permanent error in task {self.request.id}: {exc}",
            extra={"task_id": self.request.id, "args": self.request.args}
        )
        # Send alert
        send_alert(f"Task {self.name} failed permanently: {exc}")
        raise

    except Exception as exc:
        # Unknown error - log extensively
        logger.exception(
            f"Unknown error in task {self.request.id}",
            extra={"task_id": self.request.id, "args": self.request.args}
        )

        # Retry with caution
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=300)
        else:
            # Max retries exceeded
            send_alert(f"Task {self.name} failed after {self.max_retries} retries")
            raise
```

### Task Failure Callbacks

```python
@celery_app.task
def on_failure_callback(task_id, exception, traceback, args, kwargs):
    """Called when task fails."""
    logger.error(
        f"Task {task_id} failed",
        extra={
            "exception": str(exception),
            "traceback": traceback,
            "args": args,
            "kwargs": kwargs,
        }
    )

    # Send notification
    send_slack_alert(
        channel="#ai-brain-alerts",
        message=f"❌ Task {task_id} failed: {exception}"
    )


# Register callback
celery_app.conf.task_failure = on_failure_callback
```

---

## Monitoring

### Flower Dashboard

**Setup**:

```bash
# Start Flower
make celery.flower

# Or manually
celery -A app.infrastructure.celery.app flower --port=5555
```

**Access**: http://localhost:5555

**Key Metrics**:
- Task success/failure rates
- Task execution time
- Queue lengths
- Worker status
- Task retry counts

### Prometheus Metrics

**Configuration**:

```python
# src/app/infrastructure/celery/monitoring.py

from prometheus_client import Counter, Histogram, Gauge

# Task metrics
task_started = Counter(
    "celery_task_started_total",
    "Total tasks started",
    ["task_name", "queue"]
)

task_succeeded = Counter(
    "celery_task_succeeded_total",
    "Total tasks succeeded",
    ["task_name", "queue"]
)

task_failed = Counter(
    "celery_task_failed_total",
    "Total tasks failed",
    ["task_name", "queue"]
)

task_duration = Histogram(
    "celery_task_duration_seconds",
    "Task execution duration",
    ["task_name", "queue"]
)

# Queue metrics
queue_length = Gauge(
    "celery_queue_length",
    "Number of tasks in queue",
    ["queue"]
)

# Worker metrics
worker_active_tasks = Gauge(
    "celery_worker_active_tasks",
    "Number of active tasks per worker",
    ["worker"]
)
```

### Custom Monitoring Queries

**Task Performance Dashboard**:

```sql
-- Task success rate by type
SELECT
    task_name,
    COUNT(*) FILTER (WHERE status = 'SUCCESS') as success_count,
    COUNT(*) FILTER (WHERE status = 'FAILURE') as failure_count,
    COUNT(*) as total_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'SUCCESS') / COUNT(*),
        2
    ) as success_rate_pct,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM celery_task_results
WHERE started_at >= NOW() - INTERVAL '24 hours'
GROUP BY task_name
ORDER BY total_count DESC;
```

**Slow Tasks Report**:

```sql
SELECT
    task_id,
    task_name,
    started_at,
    completed_at,
    EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds,
    status
FROM celery_task_results
WHERE completed_at >= NOW() - INTERVAL '24 hours'
    AND EXTRACT(EPOCH FROM (completed_at - started_at)) > 300  -- > 5 minutes
ORDER BY duration_seconds DESC
LIMIT 20;
```

**Task Retry Analysis**:

```sql
SELECT
    task_name,
    COUNT(*) as total_retries,
    AVG(retry_count) as avg_retry_count,
    MAX(retry_count) as max_retry_count
FROM celery_task_results
WHERE retry_count > 0
    AND started_at >= NOW() - INTERVAL '7 days'
GROUP BY task_name
ORDER BY total_retries DESC;
```

### Alerting Rules

**Critical Alerts**:

```yaml
# prometheus_rules.yml

groups:
  - name: celery_ai_brain_alerts
    interval: 30s
    rules:
      # High failure rate
      - alert: CeleryTaskHighFailureRate
        expr: |
          rate(celery_task_failed_total{queue="ai_brain"}[5m]) /
          rate(celery_task_started_total{queue="ai_brain"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High task failure rate in AI Brain queue"
          description: "{{ $value | humanizePercentage }} of tasks failing"

      # Queue length too high
      - alert: CeleryQueueTooLong
        expr: celery_queue_length{queue="ai_brain"} > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "AI Brain queue length exceeds 1000"
          description: "Current queue length: {{ $value }}"

      # Task duration too long
      - alert: CeleryTaskSlow
        expr: |
          histogram_quantile(0.95,
            rate(celery_task_duration_seconds_bucket{task_name="warm_knowledge_cache_task"}[5m])
          ) > 600
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Cache warming task taking too long"
          description: "P95 duration: {{ $value | humanizeDuration }}"

      # No tasks processed (dead worker)
      - alert: CeleryWorkerDead
        expr: |
          rate(celery_task_started_total{queue="ai_brain"}[5m]) == 0
        for: 15m
        labels:
          severity: critical
        annotations:
          summary: "No tasks processed in AI Brain queue"
          description: "Worker may be dead or stuck"
```

---

## Performance Tuning

### Worker Configuration

**Optimal Settings**:

```bash
# Start worker with performance tuning
celery -A app.infrastructure.celery.app worker \
    --queue=ai_brain \
    --concurrency=4 \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=1000 \
    --time-limit=600 \
    --soft-time-limit=540 \
    --loglevel=INFO
```

**Configuration Explanations**:

- `--concurrency=4`: Number of worker processes (= CPU cores)
- `--prefetch-multiplier=1`: Prefetch 1 task per worker (prevents task hoarding)
- `--max-tasks-per-child=1000`: Restart worker after 1000 tasks (prevent memory leaks)
- `--time-limit=600`: Hard timeout at 10 minutes
- `--soft-time-limit=540`: Soft timeout at 9 minutes (allow graceful cleanup)

### Queue Optimization

**Priority Queues**:

```python
# High priority for critical tasks
celery_app.conf.task_routes = {
    "check_integration_health_task": {
        "queue": "health_checks",
        "priority": 10,  # Highest
    },
    "warm_knowledge_cache_task": {
        "queue": "ai_brain",
        "priority": 5,  # Medium
    },
    "cleanup_expired_cache_task": {
        "queue": "maintenance",
        "priority": 1,  # Lowest
    },
}
```

**Queue Length Limits**:

```python
# Prevent queue overflow
celery_app.conf.task_queues = (
    Queue(
        "ai_brain",
        Exchange("ai_brain"),
        routing_key="ai_brain",
        queue_arguments={"x-max-length": 10000}  # Max 10k tasks
    ),
    Queue(
        "health_checks",
        Exchange("health"),
        routing_key="health",
        queue_arguments={
            "x-max-length": 1000,
            "x-message-ttl": 300000,  # 5 minute TTL
        }
    ),
)
```

### Database Query Optimization

**Connection Pooling**:

```python
# SQLAlchemy engine configuration
engine = create_async_engine(
    database_url,
    pool_size=10,  # Max 10 connections
    max_overflow=20,  # Allow 20 overflow connections
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)
```

**Batch Operations**:

```python
# Instead of individual queries
for entry in entries:
    await knowledge_gateway.save(entry)  # N queries

# Use bulk operations
await knowledge_gateway.bulk_save(entries)  # 1 query
```

**Query Optimization**:

```sql
-- Add indexes for frequent queries
CREATE INDEX CONCURRENTLY idx_knowledge_entries_agent_active
ON ai_brain_knowledge_entries(agent_id, is_active)
WHERE is_active = true;

-- Use covering indexes
CREATE INDEX CONCURRENTLY idx_knowledge_entries_cache_lookup
ON ai_brain_knowledge_entries(agent_id, id, content_hash, updated_at)
WHERE is_active = true;
```

### Redis Performance

**Connection Pooling**:

```python
# Redis client configuration
redis_client = aioredis.from_url(
    redis_url,
    encoding="utf-8",
    decode_responses=True,
    max_connections=50,  # Connection pool size
)
```

**Pipeline Operations**:

```python
# Batch cache operations
pipeline = redis_client.pipeline()

for entry in entries:
    key = f"knowledge:{entry.agent_id}:{entry.id}"
    pipeline.setex(key, 3600, entry.to_json())

await pipeline.execute()  # Execute all at once
```

**Memory Optimization**:

```conf
# redis.conf

maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Enable compression
list-compress-depth 1
```

---

## Manual Operations

### Trigger Tasks Manually

**Via CLI**:

```bash
# Basic task execution
celery -A app.infrastructure.celery.app call warm_knowledge_cache_task

# With arguments
celery -A app.infrastructure.celery.app call warm_knowledge_cache_task \
    --kwargs='{"agent_ids": ["uuid-1", "uuid-2"], "priority": "high"}'

# With specific queue
celery -A app.infrastructure.celery.app call check_integration_health_task \
    --queue=health_checks

# Schedule for later
celery -A app.infrastructure.celery.app call cleanup_expired_cache_task \
    --eta="2026-01-27T02:00:00"
```

**Via Python**:

```python
from app.infrastructure.celery.tasks.ai_brain_tasks import (
    warm_knowledge_cache_task,
    check_integration_health_task,
)

# Immediate execution (blocking)
result = warm_knowledge_cache_task.apply()
print(result.get())

# Async execution
async_result = warm_knowledge_cache_task.apply_async(
    kwargs={"priority": "high"},
    queue="ai_brain",
)

# Get result (blocking with timeout)
result = async_result.get(timeout=300)
print(f"Cached {result['entries_cached']} entries")

# Check status
print(async_result.status)  # PENDING, STARTED, SUCCESS, FAILURE

# Get task ID
print(async_result.id)
```

### Inspect Tasks

```bash
# List active tasks
celery -A app.infrastructure.celery.app inspect active

# List scheduled tasks
celery -A app.infrastructure.celery.app inspect scheduled

# List registered tasks
celery -A app.infrastructure.celery.app inspect registered

# Worker statistics
celery -A app.infrastructure.celery.app inspect stats

# Revoke a task
celery -A app.infrastructure.celery.app control revoke <task-id>

# Terminate a task
celery -A app.infrastructure.celery.app control revoke <task-id> --terminate
```

### Pause/Resume Queues

```bash
# Pause queue (workers won't pick new tasks)
celery -A app.infrastructure.celery.app control cancel_consumer ai_brain

# Resume queue
celery -A app.infrastructure.celery.app control add_consumer ai_brain

# Purge queue (delete all pending tasks)
celery -A app.infrastructure.celery.app purge -Q ai_brain
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Tasks Not Executing

**Symptoms**:
- Tasks queued but not processing
- Worker appears idle

**Diagnosis**:

```bash
# Check worker status
celery -A app.infrastructure.celery.app inspect active

# Check queue length
celery -A app.infrastructure.celery.app inspect reserved

# Check broker connection
redis-cli PING
```

**Solutions**:

1. Restart workers:
   ```bash
   make celery.restart
   ```

2. Check worker logs:
   ```bash
   tail -f /var/log/celery/worker.log
   ```

3. Verify broker connectivity:
   ```bash
   celery -A app.infrastructure.celery.app inspect ping
   ```

#### Issue 2: High Task Failure Rate

**Symptoms**:
- Many tasks failing
- Error logs show exceptions

**Diagnosis**:

```sql
SELECT
    task_name,
    COUNT(*) as failure_count,
    exception_type,
    exception_message
FROM celery_task_results
WHERE status = 'FAILURE'
    AND started_at >= NOW() - INTERVAL '1 hour'
GROUP BY task_name, exception_type, exception_message
ORDER BY failure_count DESC;
```

**Solutions**:

1. Check error types and fix root cause
2. Increase retry limits if transient errors
3. Add error handling for edge cases
4. Scale up resources if resource-constrained

#### Issue 3: Tasks Taking Too Long

**Symptoms**:
- Tasks timeout
- Soft/hard time limit exceeded

**Diagnosis**:

```sql
SELECT
    task_id,
    task_name,
    EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
FROM celery_task_results
WHERE completed_at >= NOW() - INTERVAL '24 hours'
ORDER BY duration_seconds DESC
LIMIT 10;
```

**Solutions**:

1. Optimize database queries (add indexes)
2. Use batch operations instead of loops
3. Increase time limits if legitimately slow
4. Break task into smaller subtasks

#### Issue 4: Memory Leaks

**Symptoms**:
- Worker memory grows over time
- Worker crashes with OOM

**Diagnosis**:

```bash
# Monitor worker memory
ps aux | grep celery

# Check task execution count
celery -A app.infrastructure.celery.app inspect stats
```

**Solutions**:

1. Lower `max-tasks-per-child`:
   ```python
   celery_app.conf.worker_max_tasks_per_child = 100
   ```

2. Profile memory usage:
   ```python
   import tracemalloc
   tracemalloc.start()
   # ... task code ...
   snapshot = tracemalloc.take_snapshot()
   ```

3. Close database connections explicitly
4. Clear large objects from memory

#### Issue 5: Queue Backup

**Symptoms**:
- Queue length growing
- Tasks delayed significantly

**Diagnosis**:

```bash
# Check queue lengths
celery -A app.infrastructure.celery.app inspect reserved

# Monitor queue growth
watch -n 5 'redis-cli LLEN celery:ai_brain'
```

**Solutions**:

1. Scale up workers:
   ```bash
   # Start additional workers
   celery -A app.infrastructure.celery.app worker --queue=ai_brain --concurrency=8
   ```

2. Optimize task execution time
3. Increase `prefetch_multiplier` temporarily
4. Purge old tasks if safe:
   ```bash
   celery -A app.infrastructure.celery.app purge -Q ai_brain
   ```

### Debug Mode

**Enable Verbose Logging**:

```bash
celery -A app.infrastructure.celery.app worker \
    --queue=ai_brain \
    --loglevel=DEBUG
```

**Task Tracing**:

```python
@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
    print(f"Task ID: {self.request.id}")
    print(f"Args: {self.request.args}")
    print(f"Kwargs: {self.request.kwargs}")
    print(f"Retries: {self.request.retries}")
```

### Health Checks

**Worker Health Check**:

```python
# src/app/infrastructure/monitoring/celery_health.py

async def check_celery_health() -> dict:
    """Check Celery worker health."""
    from app.infrastructure.celery.app import celery_app

    try:
        # Ping workers
        result = celery_app.control.inspect().ping()

        if not result:
            return {
                "status": "unhealthy",
                "message": "No workers responding",
            }

        worker_count = len(result)

        # Check queue lengths
        queue_stats = {}
        for queue_name in ["ai_brain", "health_checks", "analytics"]:
            length = await redis_client.llen(f"celery:{queue_name}")
            queue_stats[queue_name] = length

        return {
            "status": "healthy",
            "worker_count": worker_count,
            "queue_stats": queue_stats,
        }

    except Exception as exc:
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {exc}",
        }
```

---

## Summary

The AI Brain Celery background tasks system provides:

✅ **7 Core Background Tasks**:
1. Knowledge Cache Warming (daily 2 AM)
2. Integration Health Checks (every 5 min)
3. Cache Statistics Aggregation (hourly)
4. Prompt Performance Analysis (daily 3 AM)
5. Configuration Auditing (weekly Monday 1 AM)
6. Knowledge Consistency Checks (daily 4 AM)
7. Expired Cache Cleanup (daily 5 AM)

✅ **Production-Ready Features**:
- Exponential backoff retry strategies
- Comprehensive error handling
- Prometheus metrics integration
- Flower monitoring dashboard
- Task dependency management
- Performance optimization

✅ **Operational Excellence**:
- Manual trigger commands
- Debug mode support
- Health check endpoints
- Detailed troubleshooting guide
- Monitoring queries

✅ **Scalability**:
- Queue segregation
- Priority-based scheduling
- Connection pooling
- Batch operations
- Memory management

This background task system ensures the AI Brain module operates efficiently, maintains data consistency, and provides valuable analytics for continuous improvement.