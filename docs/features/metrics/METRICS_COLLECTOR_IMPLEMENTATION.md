# MetricsCollectorAdapter Implementation

## Overview

This document describes the implementation of the MetricsCollectorAdapter for collecting and storing performance metrics in Redis time-series format, following the Hexagonal Architecture pattern established in the codebase.

## Architecture

### Domain Layer

#### 1. PerformanceMetrics Entity
**Location:** `/home/ubuntu/anvil_backend/src/app/domain/entities/chat/performance_metrics.py`

Comprehensive entity tracking chat system performance with:

- **Response Time Metrics**: p50, p95, p99 percentiles, min/max/avg
- **Error Metrics**: Total errors, error rate, breakdown by error type
- **Cost Metrics**: Total cost, token usage, API call counts
- **Cache Metrics**: Hit/miss rates and totals
- **Aggregation Support**: Minute, hourly, daily, weekly, monthly periods

**Key Components:**
```python
class PerformanceMetrics:
    id: UUID
    agent_name: Optional[str]  # None for global metrics
    period: AggregationPeriod
    period_start: datetime
    period_end: datetime
    response_times: ResponseTimeMetrics
    errors: ErrorMetrics
    costs: CostMetrics
    cache: CacheMetrics
    request_count: int
    user_count: int
```

**Enums:**
- `MetricType`: Response time, request count, error rate, cost, cache hit rate, token usage
- `ErrorType`: Timeout, rate limit, validation, authentication, LLM error, network, internal
- `AggregationPeriod`: Minute, hourly, daily, weekly, monthly

#### 2. MetricsCollector Port
**Location:** `/home/ubuntu/anvil_backend/src/app/domain/ports/metrics_collector.py`

Domain-defined interface for metrics collection with methods for:

**Recording:**
- `record_response_time()`: Track response time measurements
- `record_request()`: Track request occurrences and unique users
- `record_error()`: Track errors by type
- `record_cost()`: Track costs and token usage
- `record_cache_hit()` / `record_cache_miss()`: Track cache performance

**Querying:**
- `get_metrics()`: Aggregated metrics for a time period
- `get_metrics_by_agent()`: Metrics for multiple agents
- `get_response_time_percentiles()`: p50, p95, p99 calculations
- `get_error_counts_by_type()`: Error breakdown
- `get_total_cost()`: Cost aggregation
- `get_cache_hit_rate()`: Cache performance

**Aggregation:**
- `aggregate_hourly()`: Roll up minute data to hourly
- `aggregate_daily()`: Roll up hourly data to daily
- `aggregate_weekly()`: Roll up daily data to weekly

**Analysis:**
- `get_top_agents_by_requests()`: Highest request volume
- `get_top_agents_by_cost()`: Highest costs
- `get_top_agents_by_errors()`: Most errors

#### 3. Value Objects for Aggregation
**Location:** `/home/ubuntu/anvil_backend/src/app/domain/value_objects/chat/metrics_aggregation.py`

**TimeRange:**
- Immutable time range with validation
- Duration calculation
- Split by granularity support

**TimeSeries:**
- Time-series data with aggregation functions
- Filter by time range
- Statistical summaries (avg, sum, min, max)

**MetricsRollup:**
- Pre-aggregated metrics for a period
- Calculated fields (error rate, requests per second, cost per request)

**MetricsTrend:**
- Trend analysis with anomaly detection
- Direction tracking (increasing/decreasing/stable)
- Percentage change calculations

**PercentileBreakdown:**
- Complete percentile distribution (p25, p50, p75, p90, p95, p99)
- SLA compliance checking

**AgentComparison:**
- Cross-agent metric comparison
- Best/worst agent identification
- Agent ranking

### Infrastructure Layer

#### RedisMetricsCollectorAdapter
**Location:** `/home/ubuntu/anvil_backend/src/app/infrastructure/adapters/chat/redis_metrics_collector_adapter.py`

Redis-based implementation using optimized data structures:

**Data Structures:**

1. **Sorted Sets (Time-Series Data):**
   - Response times: `metrics:response_time:{agent}:{period}`
   - Request counts: `metrics:request_count:{agent}:{period}`
   - Errors by type: `metrics:error:{agent}:{error_type}:{period}`
   - Score = timestamp for time-based queries

2. **Hashes (Aggregated Data):**
   - Cost data: `metrics:cost:{agent}:{period}`
   - Aggregated metrics: `metrics:agg:{agent}:{period}:{period_key}`

3. **Counters:**
   - Cache hits: `metrics:cache_hit:{agent}:{period}`
   - Cache misses: `metrics:cache_miss:{agent}:{period}`

4. **Sets (Unique Tracking):**
   - Unique users: `metrics:users:{agent}:{period}`

**Key Features:**

- **Efficient Time-Based Queries**: Uses Redis sorted sets with timestamp scores for O(log N) range queries
- **Automatic Expiration**: TTL-based cleanup (1 hour for minute data, 7 days for hourly, etc.)
- **Percentile Calculations**: In-memory percentile computation from sorted data
- **Concurrent-Safe**: Atomic Redis operations for accurate counting
- **Agent Isolation**: Separate keys per agent for independent tracking
- **Global Metrics**: Support for system-wide metrics (agent_name=None)

**Performance Optimizations:**

1. **Redis Pipeline**: Atomic multi-field updates for cost tracking
2. **Lazy Aggregation**: On-demand rollups vs. pre-computed
3. **Scan-Based Cleanup**: Memory-efficient old data removal
4. **Key Expiration**: Automatic TTL management

## Usage Examples

### Recording Metrics

```python
from app.infrastructure.adapters.chat.redis_metrics_collector_adapter import (
    RedisMetricsCollectorAdapter,
)
from app.domain.entities.chat.performance_metrics import ErrorType

# Initialize adapter
collector = RedisMetricsCollectorAdapter(redis_client, key_prefix="metrics")

# Record response time
await collector.record_response_time(
    agent_name="portfolio_agent",
    response_time_ms=150.0,
)

# Record request
await collector.record_request(
    agent_name="portfolio_agent",
    user_id=user_id,
)

# Record error
await collector.record_error(
    agent_name="portfolio_agent",
    error_type=ErrorType.TIMEOUT,
    error_message="Request exceeded 30s timeout",
)

# Record cost
await collector.record_cost(
    agent_name="portfolio_agent",
    cost_usd=0.05,
    prompt_tokens=100,
    completion_tokens=50,
)

# Record cache performance
await collector.record_cache_hit(agent_name="portfolio_agent")
await collector.record_cache_miss(agent_name="portfolio_agent")
```

### Querying Metrics

```python
from datetime import datetime, timedelta
from app.domain.entities.chat.performance_metrics import AggregationPeriod

# Get metrics for past hour
now = datetime.utcnow()
start = now - timedelta(hours=1)

metrics = await collector.get_metrics(
    agent_name="portfolio_agent",
    period=AggregationPeriod.HOURLY,
    start_time=start,
    end_time=now,
)

print(f"Requests: {metrics.request_count}")
print(f"P95 Response Time: {metrics.response_times.p95_ms}ms")
print(f"Error Rate: {metrics.get_error_percentage()}%")
print(f"Cache Hit Rate: {metrics.cache.hit_rate * 100}%")
print(f"Total Cost: ${metrics.costs.total_cost_usd}")

# Get response time percentiles
percentiles = await collector.get_response_time_percentiles(
    agent_name="portfolio_agent",
    start_time=start,
    end_time=now,
)

print(f"P50: {percentiles['p50']}ms")
print(f"P95: {percentiles['p95']}ms")
print(f"P99: {percentiles['p99']}ms")

# Get error breakdown
error_counts = await collector.get_error_counts_by_type(
    agent_name="portfolio_agent",
    start_time=start,
    end_time=now,
)

for error_type, count in error_counts.items():
    print(f"{error_type.value}: {count} errors")

# Get top agents by various metrics
top_by_requests = await collector.get_top_agents_by_requests(
    start_time=start,
    end_time=now,
    limit=10,
)

top_by_cost = await collector.get_top_agents_by_cost(
    start_time=start,
    end_time=now,
    limit=10,
)

top_by_errors = await collector.get_top_agents_by_errors(
    start_time=start,
    end_time=now,
    limit=10,
)
```

### Aggregation

```python
# Aggregate minute-level data into hourly rollups
hours_aggregated = await collector.aggregate_hourly(
    start_time=datetime(2025, 1, 1, 0, 0),
    end_time=datetime(2025, 1, 1, 23, 59),
)

# Aggregate hourly data into daily rollups
days_aggregated = await collector.aggregate_daily(
    start_time=datetime(2025, 1, 1),
    end_time=datetime(2025, 1, 31),
)

# Aggregate daily data into weekly rollups
weeks_aggregated = await collector.aggregate_weekly(
    start_time=datetime(2025, 1, 1),
    end_time=datetime(2025, 3, 31),
)

# Cleanup old metrics (retain last 30 days)
deleted = await collector.cleanup_old_metrics(retention_days=30)
```

### Global Metrics

```python
# Record global metrics (across all agents)
await collector.record_response_time(
    agent_name=None,
    response_time_ms=200.0,
)

# Query global metrics
global_metrics = await collector.get_metrics(
    agent_name=None,
    period=AggregationPeriod.DAILY,
    start_time=start,
    end_time=now,
)
```

## Testing

### Unit Tests
**Location:** `/home/ubuntu/anvil_backend/tests/unit/domain/entities/chat/test_performance_metrics.py`

Comprehensive tests for:
- ResponseTimeMetrics (SLA checking, serialization)
- ErrorMetrics (error tracking, most common error)
- CostMetrics (budget checking, token tracking)
- CacheMetrics (hit rate calculations)
- PerformanceMetrics (request recording, aggregation)
- All enums

**Run tests:**
```bash
pytest tests/unit/domain/entities/chat/test_performance_metrics.py -v
```

### Integration Tests
**Location:** `/home/ubuntu/anvil_backend/tests/integration/chat/test_redis_metrics_collector.py`

Real Redis integration tests for:
- Recording all metric types
- Querying percentiles and aggregations
- Top agents analysis
- Cleanup operations
- Concurrent recordings
- Agent isolation
- Global metrics

**Run tests:**
```bash
# Requires Redis running on localhost:6379
pytest tests/integration/chat/test_redis_metrics_collector.py -v
```

## Data Retention Strategy

**Minute-level data:** 1 hour retention
- High granularity for real-time monitoring
- Automatic cleanup via TTL

**Hourly rollups:** 7 days retention
- Medium granularity for daily analysis
- Balances detail vs. storage

**Daily rollups:** 30 days retention
- Long-term trend analysis
- Historical comparisons

**Weekly rollups:** 90 days retention
- Quarter-over-quarter comparisons
- Capacity planning

**Monthly rollups:** 1 year retention
- Year-over-year comparisons
- Annual reporting

## Redis Memory Optimization

1. **Key Expiration**: Automatic TTL on all keys prevents unbounded growth
2. **Sorted Set Cleanup**: `ZREMRANGEBYSCORE` removes old time-series data
3. **Empty Key Deletion**: Keys with zero elements are automatically deleted
4. **Pipeline Operations**: Reduces round-trips for multi-field updates
5. **Separate Test DB**: Integration tests use DB 15 to avoid pollution

## Performance Characteristics

**Recording Metrics:**
- Response time: O(log N) - sorted set insertion
- Request count: O(log N) - sorted set insertion
- Error: O(log N) - sorted set insertion
- Cost: O(K) where K = number of fields - hash increments
- Cache: O(1) - counter increment

**Querying Metrics:**
- Percentiles: O(M log M) where M = entries in range
- Error counts: O(E) where E = number of error types
- Cost totals: O(1) - hash field retrieval
- Top agents: O(N log N) where N = total agents

**Aggregation:**
- Hourly: O(A × T) where A = agents, T = time buckets
- Daily: O(A × T)
- Weekly: O(A × T)

## Integration Points

### Application Layer
- **Command/Query Handlers**: Record metrics on chat operations
- **Interactors**: Track business logic performance
- **Error Handlers**: Record error occurrences

### Presentation Layer
- **Controllers**: Track HTTP request metrics
- **WebSocket Handlers**: Track real-time connection metrics
- **Middleware**: Automatic request/response time tracking

### Background Jobs
- **Celery Tasks**: Scheduled aggregation jobs
- **Cleanup Tasks**: Daily retention enforcement

## Future Enhancements

1. **Prometheus Export**: Add Prometheus-compatible metrics endpoint
2. **Grafana Dashboards**: Pre-built visualization templates
3. **Alerting**: Threshold-based alerts for anomalies
4. **Machine Learning**: Predictive anomaly detection
5. **Real-time Streaming**: WebSocket-based live metrics
6. **Cost Attribution**: User/organization-level cost tracking
7. **SLA Monitoring**: Automatic SLA violation detection
8. **Correlation Analysis**: Cross-metric correlation detection

## Related Documentation

- [Chat Performance Value Objects](/home/ubuntu/anvil_backend/src/app/domain/value_objects/chat/performance.py)
- [Redis Cache Adapter](/home/ubuntu/anvil_backend/src/app/infrastructure/adapters/chat/redis_cache_adapter.py)
- [Redis Offline Queue Adapter](/home/ubuntu/anvil_backend/src/app/infrastructure/adapters/chat/redis_offline_queue_adapter.py)
- [Hexagonal Architecture Guide](/home/ubuntu/anvil_backend/CLAUDE.md)
