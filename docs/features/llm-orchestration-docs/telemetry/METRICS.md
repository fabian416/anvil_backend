# Telemetry & Metrics

## Overview

The telemetry system provides comprehensive observability for the LLM orchestration layer, enabling real-time monitoring, cost tracking, and performance optimization.

---

## Metrics Collection Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TELEMETRY COLLECTION PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │   Orchestrator  │────▶│   Collector     │────▶│   Aggregator    │       │
│  │   (Events)      │     │   (In-Memory)   │     │   (Hourly)      │       │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                   │                       │                  │
│                                   ▼                       ▼                  │
│                          ┌─────────────────┐     ┌─────────────────┐       │
│                          │   PostgreSQL    │     │   TimescaleDB   │       │
│                          │   (Raw Events)  │     │   (Aggregated)  │       │
│                          └─────────────────┘     └─────────────────┘       │
│                                   │                       │                  │
│                                   └───────────┬───────────┘                  │
│                                               │                              │
│                                               ▼                              │
│                          ┌───────────────────────────────────────┐          │
│                          │            PROMETHEUS                  │          │
│                          │     (Real-time Metrics Export)        │          │
│                          └───────────────────────────────────────┘          │
│                                               │                              │
│                    ┌──────────────────────────┼──────────────────────────┐  │
│                    ▼                          ▼                          ▼  │
│           ┌───────────────┐          ┌───────────────┐          ┌─────────┐│
│           │    Grafana    │          │   AlertMgr    │          │   API   ││
│           │  (Dashboards) │          │   (Alerts)    │          │(Queries)││
│           └───────────────┘          └───────────────┘          └─────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Metrics Catalog

### Request Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `llm_requests_total` | Counter | provider, model, agent, status | Total request count |
| `llm_request_duration_seconds` | Histogram | provider, model, agent | Request duration |
| `llm_time_to_first_token_seconds` | Histogram | provider, model | Time to first token (streaming) |
| `llm_request_attempts_total` | Counter | provider, model, attempt_number | Retry attempts |
| `llm_active_requests` | Gauge | agent | Currently processing requests |

### Token Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `llm_tokens_total` | Counter | provider, model, direction | Token usage (input/output) |
| `llm_tokens_per_request` | Histogram | provider, model, direction | Tokens per request |
| `llm_context_utilization` | Histogram | provider, model | % of context window used |

### Cost Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `llm_cost_usd_total` | Counter | provider, model, agent | Cumulative cost |
| `llm_cost_per_request_usd` | Histogram | provider, model, agent | Cost distribution |
| `llm_budget_usage_ratio` | Gauge | budget_name | Current budget utilization |
| `llm_budget_remaining_usd` | Gauge | budget_name | Remaining budget |

### Error Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `llm_errors_total` | Counter | provider, model, error_type | Error count |
| `llm_retries_total` | Counter | provider, model, error_type | Retry count |
| `llm_circuit_breaker_state` | Gauge | entity_type, entity_name | Circuit breaker state (0=closed, 1=open, 0.5=half_open) |
| `llm_circuit_breaker_trips_total` | Counter | entity_type, entity_name | Circuit breaker trip count |

### Ranking Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `llm_model_ranking_score` | Gauge | agent, model | Current ranking score |
| `llm_model_selection_total` | Counter | agent, model, reason | Model selection events |
| `llm_ranking_recalculation_duration_seconds` | Histogram | agent | Ranking recalculation time |

### System Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `llm_provider_health` | Gauge | provider | Provider health (1=healthy, 0.5=degraded, 0=down) |
| `llm_provider_latency_seconds` | Histogram | provider | Provider response latency |
| `llm_queue_depth` | Gauge | - | Request queue size |

---

## Telemetry Collector Implementation

```python
# src/llm/telemetry/collector.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import asyncio
from prometheus_client import Counter, Histogram, Gauge


@dataclass
class RequestTelemetry:
    """Telemetry data for a single request."""
    request_id: str
    user_id: Optional[str]
    agent_type: str
    provider: str
    model: str
    status: str
    
    # Timing
    total_latency_ms: int
    time_to_first_token_ms: Optional[int]
    
    # Tokens
    input_tokens: int
    output_tokens: int
    
    # Cost
    cost_usd: float
    
    # Attempts
    attempt_count: int
    
    # Error info (if failed)
    error_type: Optional[str]
    error_message: Optional[str]
    
    timestamp: datetime


class TelemetryCollector:
    """
    Collects and processes telemetry from LLM requests.
    
    Responsibilities:
    - Capture request metrics
    - Export to Prometheus
    - Aggregate for storage
    - Track budgets
    """
    
    def __init__(self, db_session, config: dict = None):
        self.db = db_session
        self.config = config or {}
        
        # Initialize Prometheus metrics
        self._init_prometheus_metrics()
        
        # In-memory buffer for batch writes
        self._buffer = []
        self._buffer_size = self.config.get("buffer_size", 100)
        self._flush_interval = self.config.get("flush_interval", 10)  # seconds
        
        # Start background flush task
        asyncio.create_task(self._periodic_flush())
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metric collectors."""
        
        # Request metrics
        self.requests_total = Counter(
            'llm_requests_total',
            'Total LLM requests',
            ['provider', 'model', 'agent', 'status']
        )
        
        self.request_duration = Histogram(
            'llm_request_duration_seconds',
            'Request duration in seconds',
            ['provider', 'model', 'agent'],
            buckets=[0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60]
        )
        
        self.time_to_first_token = Histogram(
            'llm_time_to_first_token_seconds',
            'Time to first token for streaming requests',
            ['provider', 'model'],
            buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5]
        )
        
        # Token metrics
        self.tokens_total = Counter(
            'llm_tokens_total',
            'Total tokens processed',
            ['provider', 'model', 'direction']
        )
        
        # Cost metrics
        self.cost_total = Counter(
            'llm_cost_usd_total',
            'Total cost in USD',
            ['provider', 'model', 'agent']
        )
        
        self.budget_usage = Gauge(
            'llm_budget_usage_ratio',
            'Budget utilization ratio',
            ['budget_name']
        )
        
        # Error metrics
        self.errors_total = Counter(
            'llm_errors_total',
            'Total errors',
            ['provider', 'model', 'error_type']
        )
        
        self.retries_total = Counter(
            'llm_retries_total',
            'Total retry attempts',
            ['provider', 'model', 'error_type']
        )
        
        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            'llm_circuit_breaker_state',
            'Circuit breaker state',
            ['entity_type', 'entity_name']
        )
        
        # System metrics
        self.active_requests = Gauge(
            'llm_active_requests',
            'Currently active requests',
            ['agent']
        )
        
        self.provider_health = Gauge(
            'llm_provider_health',
            'Provider health status',
            ['provider']
        )
    
    async def record_success(
        self,
        tracking: 'RequestTracking',
        response: 'LLMResponse'
    ):
        """Record successful request."""
        
        telemetry = RequestTelemetry(
            request_id=tracking.request_id,
            user_id=tracking.user_id,
            agent_type=tracking.agent_type,
            provider=response.provider,
            model=response.model_id,
            status="completed",
            total_latency_ms=response.latency_ms,
            time_to_first_token_ms=tracking.time_to_first_token_ms,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=tracking.actual_cost_usd,
            attempt_count=tracking.attempt_count,
            error_type=None,
            error_message=None,
            timestamp=datetime.utcnow()
        )
        
        await self._record(telemetry)
    
    async def record_failure(
        self,
        tracking: 'RequestTracking',
        error: Exception
    ):
        """Record failed request."""
        
        error_type = self._classify_error(error)
        
        telemetry = RequestTelemetry(
            request_id=tracking.request_id,
            user_id=tracking.user_id,
            agent_type=tracking.agent_type,
            provider=tracking.selected_provider_name or "unknown",
            model=tracking.selected_model_id or "unknown",
            status="failed",
            total_latency_ms=tracking.total_latency_ms or 0,
            time_to_first_token_ms=None,
            input_tokens=tracking.input_tokens or 0,
            output_tokens=0,
            cost_usd=0,
            attempt_count=tracking.attempt_count,
            error_type=error_type,
            error_message=str(error),
            timestamp=datetime.utcnow()
        )
        
        await self._record(telemetry)
    
    async def record_attempt(
        self,
        request_id: str,
        provider: str,
        model: str,
        attempt_number: int,
        status: str,
        latency_ms: Optional[int] = None,
        error_type: Optional[str] = None
    ):
        """Record individual attempt."""
        
        # Update Prometheus counters
        if status == "failed":
            self.errors_total.labels(
                provider=provider,
                model=model,
                error_type=error_type or "unknown"
            ).inc()
        
        if attempt_number > 1:
            self.retries_total.labels(
                provider=provider,
                model=model,
                error_type=error_type or "retry"
            ).inc()
    
    async def _record(self, telemetry: RequestTelemetry):
        """Process and record telemetry."""
        
        # Update Prometheus metrics immediately
        self._update_prometheus(telemetry)
        
        # Buffer for batch database write
        self._buffer.append(telemetry)
        
        if len(self._buffer) >= self._buffer_size:
            await self._flush_buffer()
    
    def _update_prometheus(self, t: RequestTelemetry):
        """Update Prometheus metrics."""
        
        # Request counter
        self.requests_total.labels(
            provider=t.provider,
            model=t.model,
            agent=t.agent_type,
            status=t.status
        ).inc()
        
        # Duration histogram
        self.request_duration.labels(
            provider=t.provider,
            model=t.model,
            agent=t.agent_type
        ).observe(t.total_latency_ms / 1000)
        
        # Time to first token
        if t.time_to_first_token_ms:
            self.time_to_first_token.labels(
                provider=t.provider,
                model=t.model
            ).observe(t.time_to_first_token_ms / 1000)
        
        # Tokens
        self.tokens_total.labels(
            provider=t.provider,
            model=t.model,
            direction="input"
        ).inc(t.input_tokens)
        
        self.tokens_total.labels(
            provider=t.provider,
            model=t.model,
            direction="output"
        ).inc(t.output_tokens)
        
        # Cost
        if t.cost_usd > 0:
            self.cost_total.labels(
                provider=t.provider,
                model=t.model,
                agent=t.agent_type
            ).inc(t.cost_usd)
        
        # Errors
        if t.error_type:
            self.errors_total.labels(
                provider=t.provider,
                model=t.model,
                error_type=t.error_type
            ).inc()
    
    async def _flush_buffer(self):
        """Flush buffered telemetry to database."""
        if not self._buffer:
            return
        
        batch = self._buffer
        self._buffer = []
        
        # Batch insert to database
        await self._batch_insert(batch)
    
    async def _batch_insert(self, batch: list):
        """Insert batch of telemetry records."""
        # Implementation would insert to llm_requests table
        pass
    
    async def _periodic_flush(self):
        """Background task to flush buffer periodically."""
        while True:
            await asyncio.sleep(self._flush_interval)
            await self._flush_buffer()
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type."""
        error_str = str(error).lower()
        
        if "rate limit" in error_str:
            return "rate_limit"
        elif "timeout" in error_str:
            return "timeout"
        elif "unavailable" in error_str:
            return "service_unavailable"
        else:
            return "internal_error"
    
    # Circuit breaker telemetry
    
    def update_circuit_breaker(
        self,
        entity_type: str,
        entity_name: str,
        state: str
    ):
        """Update circuit breaker state metric."""
        state_value = {
            "closed": 0,
            "half_open": 0.5,
            "open": 1
        }.get(state, 0)
        
        self.circuit_breaker_state.labels(
            entity_type=entity_type,
            entity_name=entity_name
        ).set(state_value)
    
    # Provider health telemetry
    
    def update_provider_health(self, provider: str, status: str):
        """Update provider health metric."""
        health_value = {
            "healthy": 1,
            "degraded": 0.5,
            "down": 0
        }.get(status, 0)
        
        self.provider_health.labels(provider=provider).set(health_value)
    
    # Budget tracking
    
    async def update_budget_metrics(self):
        """Update budget utilization metrics."""
        budgets = await self._get_budgets()
        
        for budget in budgets:
            ratio = budget.current_spend / budget.budget_amount
            self.budget_usage.labels(
                budget_name=budget.name
            ).set(ratio)
```

---

## Aggregation Jobs

### Hourly Aggregation

```python
# src/llm/telemetry/aggregation.py

async def aggregate_hourly_telemetry(hour: datetime = None):
    """
    Aggregate raw telemetry into hourly buckets.
    
    Runs every hour via scheduler.
    """
    target_hour = hour or (datetime.utcnow() - timedelta(hours=1)).replace(
        minute=0, second=0, microsecond=0
    )
    
    # Execute aggregation SQL
    await db.execute("""
        INSERT INTO llm_telemetry_hourly (
            hour_bucket, provider_id, model_id, agent_type,
            total_requests, successful_requests, failed_requests,
            latency_p50_ms, latency_p95_ms, latency_p99_ms, avg_latency_ms,
            total_input_tokens, total_output_tokens,
            total_cost_usd, avg_cost_per_request, retry_rate
        )
        SELECT 
            :hour_bucket,
            selected_provider_id,
            selected_model_id,
            agent_type,
            COUNT(*),
            COUNT(*) FILTER (WHERE status = 'completed'),
            COUNT(*) FILTER (WHERE status = 'failed'),
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_latency_ms),
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_latency_ms),
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_latency_ms),
            AVG(total_latency_ms),
            SUM(input_tokens),
            SUM(output_tokens),
            SUM(actual_cost_usd),
            AVG(actual_cost_usd),
            COUNT(*) FILTER (WHERE attempt_count > 1)::float / NULLIF(COUNT(*), 0)
        FROM llm_requests
        WHERE created_at >= :hour_start
            AND created_at < :hour_end
        GROUP BY selected_provider_id, selected_model_id, agent_type
        ON CONFLICT (hour_bucket, provider_id, model_id, agent_type) 
        DO UPDATE SET ...
    """, {
        "hour_bucket": target_hour,
        "hour_start": target_hour,
        "hour_end": target_hour + timedelta(hours=1)
    })
```

### Daily Cost Rollup

```python
async def rollup_daily_costs(date: datetime.date = None):
    """Rollup costs for daily budget tracking."""
    target_date = date or (datetime.utcnow() - timedelta(days=1)).date()
    
    await db.execute("""
        INSERT INTO llm_cost_daily (
            date, provider_id,
            total_cost_usd, total_requests, total_tokens
        )
        SELECT 
            :target_date,
            provider_id,
            SUM(total_cost_usd),
            SUM(total_requests),
            SUM(total_input_tokens + total_output_tokens)
        FROM llm_telemetry_hourly
        WHERE hour_bucket >= :date_start
            AND hour_bucket < :date_end
        GROUP BY provider_id
        ON CONFLICT (date, provider_id) DO UPDATE SET ...
    """, {
        "target_date": target_date,
        "date_start": datetime.combine(target_date, datetime.min.time()),
        "date_end": datetime.combine(target_date + timedelta(days=1), datetime.min.time())
    })
```

---

## Dashboard Queries

### Overview Metrics

```sql
-- Last 24h summary
SELECT 
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status = 'completed') as successful,
    ROUND(AVG(total_latency_ms)::numeric, 0) as avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_latency_ms) as p95_latency_ms,
    ROUND(SUM(actual_cost_usd)::numeric, 2) as total_cost_usd,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 2) as success_rate
FROM llm_requests
WHERE created_at > NOW() - INTERVAL '24 hours';
```

### Provider Comparison

```sql
-- Provider performance comparison
SELECT 
    p.display_name as provider,
    COUNT(*) as requests,
    ROUND(100.0 * COUNT(*) FILTER (WHERE r.status = 'completed') / COUNT(*), 2) as success_rate,
    ROUND(AVG(r.total_latency_ms)::numeric, 0) as avg_latency_ms,
    ROUND(SUM(r.actual_cost_usd)::numeric, 2) as total_cost
FROM llm_requests r
JOIN llm_providers p ON r.selected_provider_id = p.id
WHERE r.created_at > NOW() - INTERVAL '24 hours'
GROUP BY p.id, p.display_name
ORDER BY requests DESC;
```

### Cost Trend

```sql
-- Daily cost trend (last 30 days)
SELECT 
    DATE_TRUNC('day', hour_bucket) as date,
    SUM(total_cost_usd) as daily_cost,
    SUM(total_requests) as daily_requests
FROM llm_telemetry_hourly
WHERE hour_bucket > NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', hour_bucket)
ORDER BY date;
```

---

## Alerting Rules

### Prometheus Alerting Rules

```yaml
# alerts/llm_alerts.yml

groups:
  - name: llm_orchestration
    rules:
      # High error rate
      - alert: LLMHighErrorRate
        expr: |
          sum(rate(llm_errors_total[5m])) / sum(rate(llm_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LLM error rate above 5%"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      # Provider down
      - alert: LLMProviderDown
        expr: llm_provider_health == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "LLM provider {{ $labels.provider }} is down"
      
      # High latency
      - alert: LLMHighLatency
        expr: |
          histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LLM P95 latency above 10 seconds"
      
      # Budget warning
      - alert: LLMBudgetWarning
        expr: llm_budget_usage_ratio > 0.8
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "LLM budget {{ $labels.budget_name }} at {{ $value | humanizePercentage }}"
      
      # Circuit breaker open
      - alert: LLMCircuitBreakerOpen
        expr: llm_circuit_breaker_state == 1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker open for {{ $labels.entity_name }}"
```

---

## Grafana Dashboard

### Dashboard JSON

See `dashboard/llm_orchestration.json` for the complete Grafana dashboard definition.

Key panels include:
- Request rate and success rate
- Latency percentiles (P50, P95, P99)
- Cost tracking by provider/model
- Token usage
- Error breakdown
- Circuit breaker status
- Provider health
