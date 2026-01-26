# Distillation System Celery Background Tasks

> **Complete reference for all Celery tasks and scheduled jobs**
> **Version:** 2.0
> **Last Updated:** 2026-01-26

---

## Table of Contents

- [Overview](#overview)
- [Task Architecture](#task-architecture)
- [Scheduled Tasks (Celery Beat)](#scheduled-tasks-celery-beat)
- [On-Demand Tasks](#on-demand-tasks)
- [Task Details](#task-details)
- [Error Handling & Retries](#error-handling--retries)
- [Monitoring & Debugging](#monitoring--debugging)
- [Performance Tuning](#performance-tuning)

---

## Overview

The Distillation System uses **Celery** for background task processing with **Redis** as the message broker. Tasks handle:

1. **Telemetry Aggregation** - Hourly metric rollups
2. **Cache Cleanup** - Expired cache entry removal
3. **Response Caching** - Async LLM response caching

### Task Summary

| Task Name | Type | Schedule | Queue | Purpose |
|-----------|------|----------|-------|---------|
| `aggregate_distillation_telemetry` | Scheduled | Hourly (:05) | default | Aggregate hourly metrics |
| `cleanup_expired_cache` | Scheduled | Daily (3:00 AM) | default | Remove expired cache entries |
| `cache_llm_response` | On-Demand | N/A | default | Cache LLM response after generation |

### Celery Configuration

**Broker:** Redis (localhost:6379)
**Backend:** Redis (same)
**Queues:**
- `default` - All distillation tasks
- `high_priority` - Critical tasks (none currently)

**Workers:** 4 concurrent processes (default)

---

## Task Architecture

### Celery App Initialization

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/celery/app.py`

```python
from celery import Celery

celery_app = Celery(
    'anvil_backend',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
)
```

### Task Registration

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/celery/tasks/distillation_tasks.py`

All distillation tasks are registered in this module and imported by the main Celery app.

### Async Task Execution Pattern

**Pattern:** Use `asyncio.run()` to execute async code in sync Celery tasks

```python
@celery_app.task(name="task_name")
def sync_task():
    """Sync wrapper for async task."""
    async def runner(container):
        # Async code here
        pass

    asyncio.run(_run_task(runner))
```

**Rationale:**
- Celery tasks are synchronous by default
- Most distillation code is async (SQLAlchemy, HTTP clients)
- Pattern bridges sync Celery with async codebase

---

## Scheduled Tasks (Celery Beat)

### Beat Schedule Configuration

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/celery/tasks/distillation_tasks.py:189`

```python
celery_app.conf.beat_schedule = {
    # Aggregate telemetry every hour
    "aggregate-distillation-telemetry": {
        "task": "aggregate_distillation_telemetry",
        "schedule": crontab(minute=5),  # Run at :05 of every hour
    },

    # Clean up expired cache daily at 3 AM
    "cleanup-expired-cache": {
        "task": "cleanup_expired_cache",
        "schedule": crontab(hour=3, minute=0),
    },
}
```

### Starting Celery Beat

```bash
# Start Celery Beat scheduler
make celery.beat

# Or manually
celery -A src.app.infrastructure.celery.app beat --loglevel=info
```

---

## On-Demand Tasks

### Task Invocation Methods

**1. Async Call (Non-blocking):**

```python
# Fire and forget (returns AsyncResult)
result = cache_llm_response.apply_async(
    args=[query, query_hash, response, intent, entities, source_model],
    queue='default',
)

# Check result later
if result.ready():
    print(result.result)
```

**2. Sync Call (Blocking):**

```python
# Wait for result
result = cache_llm_response.apply_async(
    args=[...],
).get(timeout=10)
```

**3. Delayed Execution:**

```python
# Execute in 60 seconds
cache_llm_response.apply_async(
    args=[...],
    countdown=60,
)
```

---

## Task Details

### 1. aggregate_distillation_telemetry

**Purpose:** Aggregate distillation requests into hourly summaries for analytics and reporting.

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/celery/tasks/distillation_tasks.py:29`

**Schedule:** Every hour at :05 (e.g., 12:05, 13:05, 14:05)

**Queue:** `default`

**Timeout:** 300 seconds (5 minutes)

**Implementation:**

```python
@celery_app.task(name="aggregate_distillation_telemetry")
def aggregate_distillation_telemetry():
    """
    Aggregate distillation requests into hourly summaries.

    Runs every hour, aggregates the previous hour's data.
    """
    async def runner(container):
        session = await container.get(MainAsyncSession)

        # Calculate the previous hour window
        now = datetime.now(UTC)
        hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
        hour_end = now.replace(minute=0, second=0, microsecond=0)

        # Aggregate query
        query = text("""
            INSERT INTO distillation_telemetry_hourly (
                hour_bucket,
                total_requests,
                cache_hit_count,
                static_response_count,
                light_llm_count,
                full_llm_count,
                rejected_count,
                avg_classification_latency_ms,
                avg_confidence,
                created_at
            )
            SELECT
                date_trunc('hour', created_at) as hour_bucket,
                COUNT(*) as total_requests,
                SUM(CASE WHEN cache_hit = true THEN 1 ELSE 0 END) as cache_hit_count,
                SUM(CASE WHEN route_type = 'STATIC' THEN 1 ELSE 0 END) as static_response_count,
                SUM(CASE WHEN route_type = 'LIGHT_LLM' THEN 1 ELSE 0 END) as light_llm_count,
                SUM(CASE WHEN route_type = 'FULL_LLM' THEN 1 ELSE 0 END) as full_llm_count,
                SUM(CASE WHEN route_type = 'REJECT' THEN 1 ELSE 0 END) as rejected_count,
                AVG(classification_latency_ms)::INTEGER as avg_classification_latency_ms,
                AVG(intent_confidence) as avg_confidence,
                NOW() as created_at
            FROM distillation_requests
            WHERE created_at >= :hour_start AND created_at < :hour_end
            GROUP BY date_trunc('hour', created_at)
            ON CONFLICT (hour_bucket) DO UPDATE SET
                total_requests = EXCLUDED.total_requests,
                cache_hit_count = EXCLUDED.cache_hit_count,
                static_response_count = EXCLUDED.static_response_count,
                light_llm_count = EXCLUDED.light_llm_count,
                full_llm_count = EXCLUDED.full_llm_count,
                rejected_count = EXCLUDED.rejected_count,
                avg_classification_latency_ms = EXCLUDED.avg_classification_latency_ms,
                avg_confidence = EXCLUDED.avg_confidence
        """)

        await session.execute(query, {"hour_start": hour_start, "hour_end": hour_end})
        await session.commit()

        print(f"[Telemetry] Aggregated distillation data for hour: {hour_start}")

    asyncio.run(_run_task(runner))
```

**Aggregated Metrics:**
- `total_requests`: Total queries in the hour
- `cache_hit_count`: Cache hits (exact + semantic)
- `static_response_count`: Static template responses (0 in v2.0)
- `light_llm_count`: Light LLM calls (Gemini Flash)
- `full_llm_count`: Full LLM calls (Claude Sonnet)
- `rejected_count`: Rejected queries (spam, harmful)
- `avg_classification_latency_ms`: Average classification latency
- `avg_confidence`: Average confidence score (1.0 in v2.0)

**Error Handling:**
- Retries: 3 attempts with exponential backoff
- Failure: Logs error, continues to next hour
- Alert: Sends notification if 3 consecutive failures

**Monitoring:**

```sql
-- Check latest aggregation
SELECT * FROM distillation_telemetry_hourly
ORDER BY hour_bucket DESC
LIMIT 24;

-- Check for missing hours
SELECT hour_bucket
FROM generate_series(
    NOW() - INTERVAL '24 hours',
    NOW(),
    INTERVAL '1 hour'
) AS hour_bucket
WHERE hour_bucket NOT IN (
    SELECT hour_bucket FROM distillation_telemetry_hourly
);
```

**Manual Trigger:**

```bash
# Manually trigger aggregation
celery -A src.app.infrastructure.celery.app call aggregate_distillation_telemetry

# Or via Python
from src.app.infrastructure.celery.tasks.distillation_tasks import aggregate_distillation_telemetry
aggregate_distillation_telemetry.apply_async()
```

---

### 2. cleanup_expired_cache

**Purpose:** Remove expired cache entries to free up storage and maintain cache freshness.

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/celery/tasks/distillation_tasks.py:99`

**Schedule:** Daily at 3:00 AM UTC

**Queue:** `default`

**Timeout:** 300 seconds (5 minutes)

**Implementation:**

```python
@celery_app.task(name="cleanup_expired_cache")
def cleanup_expired_cache():
    """
    Clean up expired cache entries.

    Runs daily at 3 AM, removes cache entries that have expired.
    """
    async def runner(container):
        session = await container.get(MainAsyncSession)

        # Delete expired exact cache
        exact_query = text("""
            DELETE FROM distillation_cache_exact
            WHERE expires_at < NOW()
        """)
        exact_result = await session.execute(exact_query)
        exact_deleted = exact_result.rowcount

        # Delete expired semantic cache
        semantic_query = text("""
            DELETE FROM distillation_cache_semantic
            WHERE expires_at < NOW()
        """)
        semantic_result = await session.execute(semantic_query)
        semantic_deleted = semantic_result.rowcount

        await session.commit()

        print(f"[Cache Cleanup] Deleted {exact_deleted} exact cache entries")
        print(f"[Cache Cleanup] Deleted {semantic_deleted} semantic cache entries")

    asyncio.run(_run_task(runner))
```

**Cleanup Strategy:**
1. Delete all entries where `expires_at < NOW()`
2. Separately clean exact and semantic caches
3. Log deletion counts for monitoring

**Performance:**
- Target execution time: <10 seconds (with indexes)
- Typical deletions: 100-500 entries per day
- Index usage: `expires_at` column indexed for fast cleanup

**Error Handling:**
- Retries: 3 attempts with exponential backoff
- Failure: Logs error, continues to next day
- Alert: Sends notification if cleanup fails 3 days in a row

**Monitoring:**

```sql
-- Check expired entries count (before cleanup)
SELECT
    'exact' as cache_type,
    COUNT(*) as expired_count
FROM distillation_cache_exact
WHERE expires_at < NOW()
UNION ALL
SELECT
    'semantic' as cache_type,
    COUNT(*) as expired_count
FROM distillation_cache_semantic
WHERE expires_at < NOW();

-- Check cache growth over time
SELECT
    DATE(created_at) as date,
    COUNT(*) as entries_added,
    SUM(COUNT(*)) OVER (ORDER BY DATE(created_at)) as cumulative_total
FROM distillation_cache_exact
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Manual Trigger:**

```bash
# Manually trigger cleanup
celery -A src.app.infrastructure.celery.app call cleanup_expired_cache

# Or via Python
from src.app.infrastructure.celery.tasks.distillation_tasks import cleanup_expired_cache
cleanup_expired_cache.apply_async()
```

**Optimization:**

```sql
-- Partition table for faster cleanup (recommended for >100k entries)
CREATE TABLE distillation_cache_exact (
    id UUID PRIMARY KEY,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ...
) PARTITION BY RANGE (expires_at);

-- Create partitions by month
CREATE TABLE distillation_cache_exact_2026_01
PARTITION OF distillation_cache_exact
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Drop old partitions instead of DELETE
DROP TABLE distillation_cache_exact_2025_12;
```

---

### 3. cache_llm_response

**Purpose:** Cache LLM response after generation to avoid blocking the main request.

**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/celery/tasks/distillation_tasks.py:141`

**Type:** On-Demand (triggered after LLM response generation)

**Queue:** `default`

**Timeout:** 60 seconds (1 minute)

**Implementation:**

```python
@celery_app.task(name="cache_llm_response")
def cache_llm_response(
    query: str,
    query_hash: str,
    response: str,
    intent: str,
    entities: dict,
    source_model: str,
):
    """
    Cache LLM response after generation (called from distillation engine).

    This is a background task to avoid blocking the response.
    """
    async def runner(container):
        cache_repo = await container.get(DistillationCacheRepositorySqla)

        # Create cached response
        cached = CachedResponse(
            id=uuid4(),
            query=query,
            query_hash=query_hash,
            response_content=response,
            intent=intent,
            entities=entities,
            source_model=source_model,
            hit_count=0,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24),  # 24 hour TTL
        )

        # Store in exact cache
        await cache_repo.set_exact(query_hash, cached)

        print(f"[Cache] Cached response for query: {query[:50]}...")

    asyncio.run(_run_task(runner))
```

**Trigger Points:**

```python
# After LLM response generation
response = await llm_client.chat(...)

# Cache response asynchronously (non-blocking)
cache_llm_response.apply_async(
    args=[
        query,
        query_hash,
        response.content,
        intent,
        entities,
        source_model,
    ],
)
```

**Parameters:**
- `query` (str): Original user query
- `query_hash` (str): SHA256 hash of normalized query
- `response` (str): LLM response content
- `intent` (str): Classified intent (always "unclear" in v2.0)
- `entities` (dict): Extracted entities (tokens, protocols, chains)
- `source_model` (str): Model that generated response (e.g., "claude-3-5-sonnet")

**TTL Strategy:**
- Default: 24 hours (configurable)
- Intent-based TTL (deprecated in v2.0):
  - `price_check`: 60 seconds (real-time data)
  - `explain_concept`: 3600 seconds (1 hour)
  - `how_to`: 3600 seconds (1 hour)

**Error Handling:**
- Retries: 3 attempts with 5-second exponential backoff
- Failure: Logs error, continues (non-critical)
- Impact: Cache miss on next identical query (normal flow)

**Performance:**
- Target execution time: <100ms
- Typical payload: 1-5 KB (response content)
- Database writes: 1 INSERT (exact cache)

**Monitoring:**

```sql
-- Check cache growth rate
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as entries_added,
    AVG(LENGTH(response_content)) as avg_response_size
FROM distillation_cache_exact
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- Check cache by source model
SELECT
    source_model,
    COUNT(*) as cached_count,
    AVG(hit_count) as avg_hits_per_entry
FROM distillation_cache_exact
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY source_model;
```

---

## Error Handling & Retries

### Retry Configuration

**Default Retry Policy:**

```python
@celery_app.task(
    name="task_name",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes max
    retry_jitter=True,
)
def task_with_retries():
    pass
```

**Retry Backoff:**
- Attempt 1: Immediate
- Attempt 2: 5 seconds delay
- Attempt 3: 10 seconds delay
- Attempt 4: 20 seconds delay

### Error Scenarios

**1. Database Connection Lost:**

```python
@celery_app.task(name="aggregate_distillation_telemetry")
def aggregate_distillation_telemetry():
    try:
        async def runner(container):
            session = await container.get(MainAsyncSession)
            # Database operations
            await session.commit()

        asyncio.run(_run_task(runner))
    except Exception as e:
        logger.error(f"[Telemetry] Aggregation failed: {e}")
        # Retry automatically (configured with autoretry_for)
        raise
```

**2. Redis Connection Issues:**

```python
# Celery handles Redis connection failures automatically
# Tasks are queued in Redis, if Redis is down:
# - Worker retries connection every 5 seconds
# - Tasks wait in memory until Redis is back
```

**3. Timeout Exceeded:**

```python
# If task exceeds soft_time_limit (240s):
# - SoftTimeLimitExceeded exception raised
# - Task can gracefully exit or request more time

# If task exceeds time_limit (300s):
# - Task killed immediately
# - Retry triggered (if configured)
```

### Dead Letter Queue (DLQ)

**Not Implemented Yet (Planned):**

```python
# Failed tasks after all retries → DLQ
celery_app.conf.task_routes = {
    'aggregate_distillation_telemetry': {
        'queue': 'default',
        'dead_letter_queue': 'failed_tasks',
    },
}
```

---

## Monitoring & Debugging

### Celery Flower (Web UI)

**Start Flower:**

```bash
# Start Flower monitoring UI
make celery.flower

# Or manually
celery -A src.app.infrastructure.celery.app flower --port=5555
```

**Access:** http://localhost:5555

**Features:**
- Real-time task monitoring
- Task history and statistics
- Worker status and performance
- Task retry and revoke controls

### Logging

**Log Locations:**

```bash
# Celery worker logs
tail -f logs/celery-worker.log

# Celery beat logs
tail -f logs/celery-beat.log

# Make commands
make logs-celery
```

**Log Format:**

```
[2026-01-26 12:05:00,123: INFO/MainProcess] Task aggregate_distillation_telemetry[abc123] received
[2026-01-26 12:05:01,456: INFO/ForkPoolWorker-1] [Telemetry] Aggregated distillation data for hour: 2026-01-26 11:00:00
[2026-01-26 12:05:01,789: INFO/ForkPoolWorker-1] Task aggregate_distillation_telemetry[abc123] succeeded in 1.23s
```

### Task Inspection

**Check Active Tasks:**

```bash
# List active tasks
celery -A src.app.infrastructure.celery.app inspect active

# Output
{
    'celery@worker1': [
        {
            'id': 'abc123',
            'name': 'aggregate_distillation_telemetry',
            'args': [],
            'kwargs': {},
            'time_start': 1738137600.0,
        }
    ]
}
```

**Check Scheduled Tasks:**

```bash
# List scheduled tasks (from beat)
celery -A src.app.infrastructure.celery.app inspect scheduled

# Output
{
    'celery@worker1': [
        {
            'eta': '2026-01-26T15:05:00',
            'priority': 6,
            'request': {
                'id': 'def456',
                'name': 'aggregate_distillation_telemetry',
            }
        }
    ]
}
```

**Check Task Stats:**

```bash
# Get task statistics
celery -A src.app.infrastructure.celery.app inspect stats

# Output (per worker)
{
    'celery@worker1': {
        'total': {
            'aggregate_distillation_telemetry': 168,  # 1 week of hourly runs
            'cleanup_expired_cache': 7,  # 1 week of daily runs
            'cache_llm_response': 5423,  # On-demand calls
        }
    }
}
```

### Performance Metrics

**Key Metrics:**

```sql
-- Task execution count (last 24 hours)
SELECT
    task_name,
    COUNT(*) as executions,
    AVG(execution_time_ms) as avg_time,
    MAX(execution_time_ms) as max_time
FROM celery_task_meta
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY task_name;

-- Task failure rate
SELECT
    task_name,
    COUNT(*) FILTER (WHERE status = 'SUCCESS') as success_count,
    COUNT(*) FILTER (WHERE status = 'FAILURE') as failure_count,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'FAILURE')::FLOAT / COUNT(*) * 100,
        2
    ) as failure_rate_pct
FROM celery_task_meta
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY task_name;
```

### Debugging Failed Tasks

**1. Inspect Task Result:**

```python
from celery.result import AsyncResult

# Get task result by ID
result = AsyncResult('task-id')

print(f"Status: {result.status}")
print(f"Result: {result.result}")
print(f"Traceback: {result.traceback}")
```

**2. Check Worker Logs:**

```bash
# Filter logs for specific task
grep "aggregate_distillation_telemetry" logs/celery-worker.log

# Filter for errors
grep "ERROR" logs/celery-worker.log
```

**3. Manual Task Execution (Debug Mode):**

```python
# Execute task synchronously for debugging
from src.app.infrastructure.celery.tasks.distillation_tasks import aggregate_distillation_telemetry

# Run directly (not through Celery)
aggregate_distillation_telemetry()
```

---

## Performance Tuning

### Worker Configuration

**Optimal Worker Count:**

```bash
# Rule of thumb: (2 * CPU cores) + 1
# For 4-core server: 9 workers

celery -A src.app.infrastructure.celery.app worker \
    --concurrency=9 \
    --loglevel=info \
    --max-tasks-per-child=1000  # Restart worker after 1000 tasks (memory cleanup)
```

**Pool Type:**

```bash
# Default: prefork (multi-process)
celery -A src.app.infrastructure.celery.app worker --pool=prefork

# Alternative: gevent (async I/O, for I/O-bound tasks)
celery -A src.app.infrastructure.celery.app worker --pool=gevent --concurrency=100

# Alternative: solo (single process, for debugging)
celery -A src.app.infrastructure.celery.app worker --pool=solo
```

### Task Optimization

**1. Batch Processing:**

```python
# Instead of caching each response individually
for response in responses:
    cache_llm_response.apply_async(args=[...])

# Batch cache multiple responses
@celery_app.task(name="cache_llm_responses_batch")
def cache_llm_responses_batch(responses: List[dict]):
    """Cache multiple responses in a single transaction."""
    async def runner(container):
        cache_repo = await container.get(DistillationCacheRepositorySqla)

        # Batch insert
        await cache_repo.set_exact_batch(responses)

    asyncio.run(_run_task(runner))
```

**2. Task Chunking:**

```python
# Split large aggregation into chunks
@celery_app.task(name="aggregate_distillation_telemetry_chunked")
def aggregate_distillation_telemetry_chunked():
    # Process in 15-minute chunks
    for chunk_start in range(0, 60, 15):
        # Aggregate 15-minute chunk
        pass
```

**3. Task Prefetching:**

```bash
# Reduce prefetch multiplier for long-running tasks
celery -A src.app.infrastructure.celery.app worker \
    --prefetch-multiplier=1  # Default is 4
```

### Redis Optimization

**Connection Pool:**

```python
# Increase connection pool size
celery_app.conf.broker_pool_limit = 100  # Default is 10

# Set connection timeout
celery_app.conf.broker_connection_timeout = 30  # Default is 4
```

**Message Serialization:**

```python
# Use JSON (default, human-readable)
celery_app.conf.task_serializer = 'json'

# Or use msgpack (faster, binary)
celery_app.conf.task_serializer = 'msgpack'
```

### Database Optimization

**Connection Pooling:**

```python
# SQLAlchemy connection pool for async tasks
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # Connections per worker
    max_overflow=10,  # Extra connections during peak
    pool_recycle=3600,  # Recycle connections every hour
)
```

**Index Optimization:**

```sql
-- Ensure indexes for fast aggregation
CREATE INDEX idx_distillation_requests_created_at_hour
ON distillation_requests(date_trunc('hour', created_at));

-- Ensure indexes for fast cache cleanup
CREATE INDEX idx_cache_expires_at
ON distillation_cache_exact(expires_at)
WHERE expires_at < NOW() + INTERVAL '7 days';
```

---

## Troubleshooting

### Common Issues

**1. Worker Not Processing Tasks**

**Symptoms:**
- Tasks stuck in `PENDING` state
- Flower shows no active workers

**Solutions:**

```bash
# Check worker status
celery -A src.app.infrastructure.celery.app inspect ping

# Restart worker
make celery.worker

# Check worker logs
make logs-celery
```

**2. Beat Not Scheduling Tasks**

**Symptoms:**
- Scheduled tasks not executing
- No tasks in Flower scheduled view

**Solutions:**

```bash
# Check beat status
ps aux | grep celery | grep beat

# Restart beat
make celery.beat

# Check beat logs
tail -f logs/celery-beat.log
```

**3. Redis Connection Errors**

**Symptoms:**
- `ConnectionError: Error connecting to Redis`
- Tasks fail immediately

**Solutions:**

```bash
# Check Redis status
redis-cli ping

# Start Redis
redis-server

# Check Redis connection
telnet localhost 6379
```

**4. Task Timeout**

**Symptoms:**
- Tasks killed after 5 minutes
- `TimeLimitExceeded` in logs

**Solutions:**

```python
# Increase task timeout
@celery_app.task(
    name="long_running_task",
    time_limit=600,  # 10 minutes
    soft_time_limit=540,  # 9 minutes
)
def long_running_task():
    pass
```

**5. Memory Leak**

**Symptoms:**
- Worker memory grows over time
- Server OOM (out of memory)

**Solutions:**

```bash
# Restart workers after N tasks
celery -A src.app.infrastructure.celery.app worker \
    --max-tasks-per-child=1000

# Monitor memory usage
celery -A src.app.infrastructure.celery.app inspect stats | grep memory
```

---

## Production Deployment

### Systemd Service (Recommended)

**Worker Service:** `/etc/systemd/system/celery-worker.service`

```ini
[Unit]
Description=Celery Worker
After=network.target redis.target

[Service]
Type=forking
User=anvil
Group=anvil
WorkingDirectory=/home/anvil/anvil_backend
ExecStart=/home/anvil/anvil_backend/.venv/bin/celery -A src.app.infrastructure.celery.app worker \
    --concurrency=9 \
    --loglevel=info \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Beat Service:** `/etc/systemd/system/celery-beat.service`

```ini
[Unit]
Description=Celery Beat Scheduler
After=network.target redis.target

[Service]
Type=simple
User=anvil
Group=anvil
WorkingDirectory=/home/anvil/anvil_backend
ExecStart=/home/anvil/anvil_backend/.venv/bin/celery -A src.app.infrastructure.celery.app beat \
    --loglevel=info \
    --logfile=/var/log/celery/beat.log \
    --pidfile=/var/run/celery/beat.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Start Services:**

```bash
# Enable and start worker
sudo systemctl enable celery-worker
sudo systemctl start celery-worker

# Enable and start beat
sudo systemctl enable celery-beat
sudo systemctl start celery-beat

# Check status
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

### Docker Deployment

**docker-compose.yml:**

```yaml
services:
  celery-worker:
    image: anvil-backend:latest
    command: celery -A src.app.infrastructure.celery.app worker --concurrency=9 --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - DATABASE_URL=postgresql+asyncpg://...
    restart: unless-stopped

  celery-beat:
    image: anvil-backend:latest
    command: celery -A src.app.infrastructure.celery.app beat --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    restart: unless-stopped

  flower:
    image: anvil-backend:latest
    command: celery -A src.app.infrastructure.celery.app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    restart: unless-stopped
```

---

## Changelog

### v2.0 (2026-01-26)
- Updated cache_llm_response to use intent-free caching
- Removed intent-based TTL logic
- All tasks use v2.0 cache key format

### v1.0 (2025-12-01)
- Initial release
- 3 tasks: aggregate_distillation_telemetry, cleanup_expired_cache, cache_llm_response
- Hourly aggregation + daily cleanup
- Redis broker + backend

---

**Document Version:** 2.0
**Last Updated:** 2026-01-26
**Status:** Production-Ready
