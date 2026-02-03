# Money Market Celery Tasks

Background tasks for money market operations with 60s cache TTL optimization.

## Overview

Four specialized tasks handle money market caching, alerts, analytics, and cleanup:

1. **Cache Warming** (60s) - Pre-fetch popular rates to ensure cache never expires
2. **Rate Alerts** (5min) - Check alert conditions and send notifications
3. **Analytics Aggregation** (1hr) - Aggregate comparison logs for dashboard
4. **Cache Cleanup** (daily) - Remove expired entries and old logs

## Task Details

### 1. Cache Warming Task

**Task Name:** `money_market.warm_cache`
**Schedule:** Every 60 seconds
**Queue:** `money_market`
**Priority:** High (latency-critical)

**Purpose:**
Pre-fetches rates for popular asset/chain combinations to ensure cache is always warm. This eliminates cold starts and provides consistent sub-200ms response times.

**Strategy:**
- Check if cache exists and is valid (skip if yes)
- Fetch from RPC and store in cache (if miss or expired)
- Track: warmed, skipped, errors

**Popular Combinations:**
- **Assets:** USDC, USDT, ETH, WETH, DAI
- **Chains:** ethereum, base, arbitrum, polygon, optimism
- **Protocols:** Aave V3, Compound V3

**Metrics Returned:**
```json
{
  "warmed": 15,
  "skipped": 35,
  "errors": 0,
  "timestamp": "2026-01-28T12:00:00Z"
}
```

**Manual Execution:**
```bash
# Run once manually
celery -A app.infrastructure.celery.app call money_market.warm_cache

# Run with Celery worker
celery -A app.infrastructure.celery.app worker -Q money_market --loglevel=info
```

---

### 2. Rate Alerts Task

**Task Name:** `money_market.check_alerts`
**Schedule:** Every 5 minutes
**Queue:** `money_market`
**Priority:** Medium

**Purpose:**
Checks rate alert conditions for all users with alerts enabled and sends notifications when thresholds are crossed.

**Process:**
1. Get all users with `enable_rate_alerts = true`
2. For each user's watched assets/chains:
   - Get current rates from cache
   - Compare with previous best rate (from alert history)
   - If change >= threshold, create alert and send notification
3. Track: alerts_triggered, notifications_sent, errors

**Alert Types:**
- `rate_increase` - Supply APY increased (severity: info)
- `rate_decrease` - Supply APY decreased (severity: warning)
- `new_best_rate` - New best protocol detected (severity: info)

**Metrics Returned:**
```json
{
  "users_checked": 42,
  "alerts_triggered": 5,
  "notifications_sent": 5,
  "errors": 0,
  "timestamp": "2026-01-28T12:05:00Z"
}
```

**Manual Execution:**
```bash
celery -A app.infrastructure.celery.app call money_market.check_alerts
```

**Integration Points:**
- TODO: Integrate with notification service (email, push, in-app)
- Currently marks notifications as sent without actual delivery

---

### 3. Analytics Aggregation Task

**Task Name:** `money_market.aggregate_analytics`
**Schedule:** Every hour (at :00)
**Queue:** `money_market`
**Priority:** Low

**Purpose:**
Aggregates money market analytics from comparison logs for dashboard display and trend analysis.

**Metrics Computed:**
- Most popular asset/chain combinations (last 7 days)
- Protocol preference trends
- Average response times
- Cache hit rates
- User engagement patterns

**Aggregation Windows:**
- **Daily:** Last 24 hours
- **Weekly:** Last 7 days

**Metrics Returned:**
```json
{
  "daily": {
    "total_comparisons": 1247,
    "unique_users": 89,
    "avg_latency_ms": 152,
    "cache_hit_rate": 87.3
  },
  "weekly": {
    "total_comparisons": 8542,
    "unique_users": 312
  },
  "popular_comparisons": [
    {"asset": "USDC", "chain": "base", "count": 523},
    {"asset": "USDT", "chain": "ethereum", "count": 412}
  ],
  "timestamp": "2026-01-28T13:00:00Z"
}
```

**Manual Execution:**
```bash
celery -A app.infrastructure.celery.app call money_market.aggregate_analytics
```

**Future Enhancement:**
- TODO: Create `money_market_analytics_snapshots` table for historical tracking
- Store hourly snapshots for trend visualization

---

### 4. Cache Cleanup Task

**Task Name:** `money_market.cleanup_cache`
**Schedule:** Daily at 3:00 AM UTC
**Queue:** `maintenance`
**Priority:** Low

**Purpose:**
Removes expired cache entries and old logs to reclaim disk space and maintain database performance.

**Cleanup Rules:**
- **Cache entries:** Expired > 7 days ago
- **Comparison logs:** Older than 90 days
- **Read alerts:** Read AND older than 30 days

**Note:** The partial index `WHERE valid_until > NOW()` ensures queries don't see expired entries, but this task reclaims disk space.

**Metrics Returned:**
```json
{
  "deleted_rates": 1523,
  "deleted_comparisons": 892,
  "deleted_alerts": 234,
  "timestamp": "2026-01-28T03:00:00Z"
}
```

**Manual Execution:**
```bash
celery -A app.infrastructure.celery.app call money_market.cleanup_cache
```

---

## Deployment

### Starting Celery Workers

**Money Market Queue (High Priority):**
```bash
celery -A app.infrastructure.celery.app worker \
  -Q money_market \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000
```

**Maintenance Queue (Low Priority):**
```bash
celery -A app.infrastructure.celery.app worker \
  -Q maintenance \
  --loglevel=info \
  --concurrency=2 \
  --max-tasks-per-child=500
```

**All Queues:**
```bash
celery -A app.infrastructure.celery.app worker \
  -Q money_market,maintenance,default \
  --loglevel=info \
  --concurrency=8
```

### Starting Celery Beat (Scheduler)

```bash
celery -A app.infrastructure.celery.app beat \
  --loglevel=info \
  --schedule=/tmp/celerybeat-schedule
```

### Monitoring with Flower

```bash
celery -A app.infrastructure.celery.app flower \
  --port=5555 \
  --broker=redis://localhost:6379/0
```

Access at: http://localhost:5555

---

## Queue Configuration

| Task | Queue | Concurrency | Priority |
|------|-------|-------------|----------|
| `warm_cache` | money_market | 4 | High |
| `check_alerts` | money_market | 4 | Medium |
| `aggregate_analytics` | money_market | 4 | Low |
| `cleanup_cache` | maintenance | 2 | Low |

---

## Monitoring & Debugging

### Check Task Status

```bash
# List active tasks
celery -A app.infrastructure.celery.app inspect active

# List scheduled tasks
celery -A app.infrastructure.celery.app inspect scheduled

# Check worker stats
celery -A app.infrastructure.celery.app inspect stats
```

### View Task Results

```python
from celery.result import AsyncResult

result = AsyncResult('task-id-here')
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # Task return value
```

### Logs

Tasks log to standard Python logging:
```python
import logging
logger = logging.getLogger("app.infrastructure.celery.tasks.money_market_tasks")
```

**Log Levels:**
- `INFO` - Task start/complete, summary stats
- `DEBUG` - Individual cache operations, detailed progress
- `ERROR` - Exceptions with full traceback

---

## Error Handling

All tasks include:
- **Automatic Retry:** 3 retries with exponential backoff
- **Error Logging:** Full traceback logged at ERROR level
- **Metrics Tracking:** Errors counted in return dictionary
- **Graceful Degradation:** Individual failures don't stop batch processing

**Retry Configuration:**
```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
```

---

## Performance Characteristics

### Cache Warming Task
- **Duration:** 5-15 seconds (50 combinations)
- **RPC Calls:** 0-50 (depends on cache hits)
- **Memory:** ~50 MB
- **Database Writes:** 0-50 inserts

### Rate Alerts Task
- **Duration:** 2-10 seconds (depends on user count)
- **Database Reads:** 1 query per user + 2 queries per watched combination
- **Database Writes:** 1 insert per triggered alert
- **Memory:** ~20 MB

### Analytics Aggregation Task
- **Duration:** 1-5 seconds
- **Database Reads:** 3 analytical queries
- **Database Writes:** 0 (TODO: Add snapshots table)
- **Memory:** ~10 MB

### Cache Cleanup Task
- **Duration:** 0.5-2 seconds
- **Database Deletes:** Batch deletes on 3 tables
- **Memory:** ~5 MB

---

## Testing

### Unit Tests

```bash
pytest tests/unit/infrastructure/celery/test_money_market_tasks.py -v
```

### Integration Tests

```bash
# With test database
pytest tests/integration/celery/test_money_market_tasks_integration.py -v
```

### Manual Testing

```python
# Test cache warming
from app.infrastructure.celery.tasks.money_market_tasks import warm_cache_task
result = warm_cache_task()
print(result)

# Test with async
import asyncio
from app.infrastructure.celery.tasks.money_market_tasks import _run_task

async def test_runner(container):
    from app.domain.ports.money_market.money_market_cache_gateway import MoneyMarketCacheGateway
    cache = await container.get(MoneyMarketCacheGateway)
    stats = await cache.get_cache_stats()
    print(stats)

asyncio.run(_run_task(test_runner))
```

---

## Future Enhancements

1. **Dynamic Warming:** Learn popular combinations from analytics
2. **Smart Scheduling:** Adjust frequency based on user activity patterns
3. **Advanced Alerts:** Price threshold alerts, liquidity alerts, multi-asset alerts
4. **Analytics Snapshots:** Historical tracking in dedicated table
5. **Notification Integration:** Email, push, SMS, Discord, Telegram
6. **Rate Prediction:** ML-based rate change predictions for proactive alerts
7. **Cross-Protocol Arbitrage:** Alert users to arbitrage opportunities

---

## Dependencies

- **Celery:** Task queue and scheduler
- **Redis:** Message broker and result backend
- **Dishka:** Dependency injection container
- **SQLAlchemy:** Database ORM for persistence
- **AaveGateway:** Aave V3 rate fetching
- **CompoundGateway:** Compound V3 rate fetching

---

## Troubleshooting

### Task Not Running

1. Check Celery worker is running: `celery -A app.infrastructure.celery.app inspect active`
2. Check task is registered: `celery -A app.infrastructure.celery.app inspect registered`
3. Check Redis connection: `redis-cli ping`
4. Check queue routing: Verify task is routed to correct queue

### High Error Rate

1. Check database connectivity
2. Check RPC endpoint availability (Aave/Compound gateways)
3. Review error logs for specific failures
4. Verify Dishka container providers are registered

### Slow Performance

1. Monitor RPC call count (should be minimal due to caching)
2. Check database query performance (EXPLAIN ANALYZE)
3. Adjust concurrency settings
4. Consider reducing popular combinations list

### Memory Issues

1. Reduce concurrency: `--concurrency=2`
2. Enable max tasks per child: `--max-tasks-per-child=500`
3. Monitor worker memory: `ps aux | grep celery`
4. Check for memory leaks in gateway implementations
