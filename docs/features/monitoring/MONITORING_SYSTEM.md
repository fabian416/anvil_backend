# Comprehensive Monitoring and Alerting System

## Overview

Production-ready monitoring infrastructure for chat features with Prometheus-compatible metrics, intelligent alerting, comprehensive health checks, and structured logging.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Chat    │  │  Agent   │  │   LLM    │  │   API    │        │
│  │ Service  │  │  Squad   │  │ Provider │  │ Gateway  │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
        ┌─────────────▼──────────────┐
        │  Metrics Middleware        │
        │  - Request tracking        │
        │  - Response times          │
        │  - Cost monitoring         │
        │  - Correlation IDs         │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │  Metrics Collector         │
        │  - Counters                │
        │  - Gauges                  │
        │  - Histograms              │
        │  - Labels                  │
        └─────────────┬──────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼─────────┐      ┌──────────▼──────────┐
│ Alert Manager   │      │  Health Service     │
│ - Rules         │      │  - Database         │
│ - Evaluation    │      │  - Redis            │
│ - Notifications │      │  - External APIs    │
└───────┬─────────┘      └──────────┬──────────┘
        │                           │
        │                           │
┌───────▼────────────────────────────▼──────────┐
│          Export & Visualization               │
│  ┌─────────────┐  ┌─────────────┐            │
│  │ Prometheus  │  │   Health    │            │
│  │   /metrics  │  │   /health   │            │
│  └─────────────┘  └─────────────┘            │
│                                               │
│  ┌─────────────┐  ┌─────────────┐            │
│  │  Grafana    │  │   Alerts    │            │
│  │ Dashboards  │  │  /alerts    │            │
│  └─────────────┘  └─────────────┘            │
└───────────────────────────────────────────────┘
```

## Components

### 1. Metrics Collector (`metrics_collector.py`)

Prometheus-compatible metrics collection with:

**Counter Metrics:**
- `chat_requests_total{agent_name, user_id, endpoint, status}`
- `chat_errors_total{agent_name, endpoint, error_type}`
- `chat_cache_hits_total{agent_name, endpoint}`
- `chat_cache_misses_total{agent_name, endpoint}`

**Gauge Metrics:**
- `chat_active_requests{agent_name, endpoint}`
- `chat_agent_available{agent_name}`
- `chat_cost_usd_total{agent_name}`

**Histogram Metrics:**
- `chat_response_time_seconds{agent_name, endpoint, status}`
  - Buckets: 10ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s
- `chat_token_usage{agent_name, provider}`

**Usage:**

```python
from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

collector = get_metrics_collector()

# Record request
collector.increment_request_count(
    agent_name="code-expert",
    user_id="user_123",
    endpoint="/chat/message",
    status="success"
)

# Record response time
collector.record_response_time(
    duration_seconds=0.45,
    agent_name="code-expert",
    endpoint="/chat/message"
)

# Record cost
collector.record_cost(
    cost_usd=0.002,
    agent_name="code-expert",
    prompt_tokens=150,
    completion_tokens=300,
    provider="openai"
)

# Export Prometheus metrics
metrics_text = collector.export_prometheus()
```

### 2. Alert Manager (`alerting.py`)

Intelligent alerting with multiple rule types:

**Alert Rules:**

1. **PerformanceAlert** - Response time degradation
   - P95 threshold (default: 1000ms)
   - P99 threshold (default: 2000ms)
   - Configurable per-agent or global

2. **BudgetAlert** - Cost overruns
   - Daily budget (default: $100)
   - Warning threshold: 80%
   - Critical threshold: 100%

3. **ErrorSpikeAlert** - Error rate spikes
   - Warning threshold: 5%
   - Critical threshold: 10%

4. **CacheEfficiencyAlert** - Low cache hit rate
   - Minimum hit rate: 50%

5. **AgentAvailabilityAlert** - Agent downtime
   - Per-agent monitoring

**Notification Channels:**
- Console (development)
- Webhook (HTTP POST)
- Email (SendGrid/AWS SES)
- Slack (coming soon)
- PagerDuty (coming soon)

**Features:**
- Smart cooldown to prevent alert fatigue
- Alert deduplication
- Contextual enrichment
- Severity levels (INFO, WARNING, ERROR, CRITICAL)

**Usage:**

```python
from app.infrastructure.monitoring.alerting import (
    get_alert_manager,
    PerformanceAlert,
    BudgetAlert,
    WebhookNotificationChannel
)
from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

# Setup alert manager
manager = get_alert_manager()
metrics = get_metrics_collector()

# Add alert rules
manager.add_rule(PerformanceAlert(
    threshold_p95_ms=1000.0,
    agent_name="code-expert"
))

manager.add_rule(BudgetAlert(
    daily_budget_usd=100.0,
))

# Add notification channel
manager.add_notification_channel(
    WebhookNotificationChannel("https://hooks.slack.com/...")
)

# Evaluate alerts (run periodically)
triggered_alerts = await manager.evaluate_all(metrics)
```

### 3. Health Check Service (`health_checks.py`)

Comprehensive health monitoring:

**Health Checks:**

1. **DatabaseHealthCheck**
   - Connection test (SELECT 1)
   - Query latency
   - Slow query detection

2. **RedisHealthCheck**
   - PING test
   - SET/GET operations
   - Connection info

3. **ExternalAPIHealthCheck**
   - OpenAI API
   - Anthropic API
   - Other external services

4. **WebSocketHealthCheck**
   - Connection pool status
   - Active connections

5. **SystemResourceHealthCheck**
   - Memory usage
   - CPU usage
   - Disk space

**Health Status:**
- `HEALTHY` - Component working normally
- `DEGRADED` - Component working but with issues
- `UNHEALTHY` - Component not working
- `UNKNOWN` - Cannot determine status

**Usage:**

```python
from app.infrastructure.monitoring.health_checks import get_health_service

service = get_health_service()

# Check all components
summary = await service.get_health_summary()
# {
#     "status": "healthy",
#     "components": {
#         "database": {...},
#         "redis": {...},
#         ...
#     },
#     "healthy_count": 4,
#     "degraded_count": 0,
#     "unhealthy_count": 0
# }

# Check specific component
health = await service.check_component("database")
```

### 4. Middleware (`middleware.py`)

Automatic metrics collection via FastAPI middleware:

**MetricsMiddleware:**
- Automatic request counting
- Response time tracking
- Error recording
- Correlation ID generation

**StructuredLoggingMiddleware:**
- Structured logging with correlation IDs
- Request/response logging
- Error tracking

**CostTrackingMiddleware:**
- LLM cost tracking per request
- High-cost request warnings

**Setup:**

```python
from fastapi import FastAPI
from app.infrastructure.monitoring.middleware import setup_monitoring_middleware

app = FastAPI()
setup_monitoring_middleware(app)
```

### 5. Background Tasks (`background_tasks.py`)

Celery tasks for periodic monitoring:

**Tasks:**

1. **Health Checks** (every 60s)
   - Run all health checks
   - Log unhealthy components

2. **Alert Evaluation** (every 60s)
   - Evaluate all alert rules
   - Send notifications

3. **Metrics Aggregation** (hourly)
   - Roll up minute-level data
   - Store hourly summaries

4. **Metrics Cleanup** (daily at 2 AM)
   - Delete old raw metrics
   - Retain aggregated data

5. **Budget Check** (hourly)
   - Check cost against budget
   - Send warnings

6. **Daily Report** (daily at midnight)
   - Generate daily metrics report
   - Email to stakeholders

**Celery Configuration:**

```python
# celeryconfig.py
from celery.schedules import crontab

beat_schedule = {
    'health-checks': {
        'task': 'monitoring.health_checks',
        'schedule': 60.0,  # Every 60 seconds
    },
    'alert-evaluation': {
        'task': 'monitoring.alert_evaluation',
        'schedule': 60.0,
    },
    'aggregate-metrics': {
        'task': 'monitoring.aggregate_metrics',
        'schedule': crontab(minute=0),  # Every hour
    },
    'cleanup-metrics': {
        'task': 'monitoring.cleanup_metrics',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

## HTTP Endpoints

### Metrics Endpoint

```
GET /monitoring/metrics
```

Returns Prometheus-compatible metrics:

```
# HELP chat_requests_total Total number of requests
# TYPE chat_requests_total counter
chat_requests_total{agent_name="code-expert",endpoint="/chat/message",status="success"} 1523

# HELP chat_response_time_seconds Response time in seconds
# TYPE chat_response_time_seconds histogram
chat_response_time_seconds_bucket{agent_name="code-expert",le="0.1"} 1234
chat_response_time_seconds_bucket{agent_name="code-expert",le="0.5"} 1450
chat_response_time_seconds_bucket{agent_name="code-expert",le="1.0"} 1500
chat_response_time_seconds_sum{agent_name="code-expert"} 678.5
chat_response_time_seconds_count{agent_name="code-expert"} 1523
```

### Health Endpoints

```
GET /monitoring/health
```

Returns overall health status:

```json
{
  "status": "healthy",
  "timestamp": "2025-12-16T12:34:56Z",
  "components": {
    "database": {
      "status": "healthy",
      "message": "Database connection healthy",
      "latency_ms": 12.5
    },
    "redis": {
      "status": "healthy",
      "message": "Redis connection healthy",
      "latency_ms": 3.2
    }
  },
  "healthy_count": 4,
  "degraded_count": 0,
  "unhealthy_count": 0
}
```

```
GET /monitoring/health/{component}
```

Check specific component health.

### Alert Endpoints

```
GET /monitoring/alerts
```

Get active alerts:

```json
[
  {
    "id": "performance_degradation_all_1702734896",
    "rule_name": "performance_degradation_all",
    "severity": "warning",
    "condition": "threshold_exceeded",
    "message": "Response time P95 (1234ms) exceeds threshold (1000ms)",
    "context": {
      "current_value": 1234.5,
      "threshold": 1000.0,
      "window": "P95"
    },
    "timestamp": "2025-12-16T12:34:56Z",
    "resolved": false
  }
]
```

```
GET /monitoring/alerts/history?limit=100&severity=error
```

Get alert history with filters.

```
POST /monitoring/alerts/{rule_name}/resolve
```

Resolve an alert.

### Metrics Summary

```
GET /monitoring/metrics/summary
```

Get overall metrics summary:

```json
{
  "total_requests": 15234,
  "total_errors": 234,
  "error_rate": 0.0153,
  "cache_hit_rate": 0.75,
  "total_cost_usd": 45.67,
  "response_time_p50": 0.234,
  "response_time_p95": 0.876,
  "response_time_p99": 1.234
}
```

```
GET /monitoring/metrics/agent/{agent_name}
```

Get agent-specific metrics.

## Grafana Dashboards

### Setup

1. **Add Prometheus Data Source:**
   ```yaml
   datasources:
     - name: Prometheus
       type: prometheus
       url: http://prometheus:9090
   ```

2. **Import Dashboard:**
   - Use pre-built dashboard JSON (coming soon)
   - Or create custom dashboards

### Recommended Panels

**Overview:**
- Total requests (graph)
- Error rate (graph)
- P95 response time (graph)
- Active alerts (stat)
- Cost per hour (graph)

**Performance:**
- Response time percentiles (heatmap)
- Response time by endpoint (graph)
- Response time by agent (table)

**Errors:**
- Error rate by type (pie chart)
- Error count by endpoint (graph)
- Recent errors (logs)

**Costs:**
- Cost over time (graph)
- Cost by agent (pie chart)
- Token usage (graph)
- Budget utilization (gauge)

**Cache:**
- Hit rate over time (graph)
- Cache operations (graph)
- Hit rate by agent (table)

**Health:**
- Component status (stat grid)
- Health check latency (graph)
- Uptime (stat)

## Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'anvil-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/monitoring/metrics'
    scrape_interval: 30s
```

## Alert Rules (Prometheus)

```yaml
# alert_rules.yml
groups:
  - name: chat_performance
    interval: 30s
    rules:
      - alert: HighResponseTime
        expr: chat_response_time_seconds{quantile="0.95"} > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "P95 response time is {{ $value }}s"

      - alert: HighErrorRate
        expr: rate(chat_errors_total[5m]) / rate(chat_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: error
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: BudgetExceeded
        expr: chat_cost_usd_total > 100
        labels:
          severity: critical
        annotations:
          summary: "Daily budget exceeded"
          description: "Current cost: ${{ $value }}"
```

## Best Practices

### 1. Metric Naming

Follow Prometheus naming conventions:
- Use lowercase with underscores
- Include unit suffixes (`_seconds`, `_total`, `_bytes`)
- Use descriptive labels

### 2. Cardinality Management

Avoid high-cardinality labels:
- ❌ Don't use: `user_id`, `session_id`, `request_id`
- ✅ Use: `agent_name`, `endpoint`, `status`, `error_type`

### 3. Alert Design

- Set appropriate thresholds based on SLAs
- Use multiple severity levels
- Include contextual information
- Implement cooldown periods

### 4. Health Checks

- Keep checks fast (< 5s timeout)
- Check only critical dependencies
- Use appropriate degradation states
- Cache results when possible

### 5. Cost Tracking

- Track costs per request
- Set budget alerts
- Monitor by agent and user
- Review daily/weekly reports

## Troubleshooting

### High Memory Usage

Metrics collector uses in-memory storage. For production:
- Use external time-series DB (InfluxDB, TimescaleDB)
- Implement data retention policies
- Aggregate old data

### Missing Metrics

- Check middleware is installed
- Verify Prometheus scraping
- Review log files for errors
- Check metric label consistency

### Alert Fatigue

- Tune thresholds based on actual data
- Increase cooldown periods
- Implement smart grouping
- Use severity levels appropriately

### Slow Health Checks

- Reduce timeout values
- Check network connectivity
- Review database query performance
- Consider async health checks

## Integration Examples

### With Existing Code

```python
# In your chat endpoint
from app.infrastructure.monitoring.metrics_collector import get_metrics_collector
from app.infrastructure.monitoring.middleware import get_correlation_id

@router.post("/chat/message")
async def send_message(request: ChatRequest):
    collector = get_metrics_collector()
    correlation_id = get_correlation_id()

    # Track cache hit
    if cached_response := cache.get(request.message):
        collector.record_cache_hit(
            agent_name=request.agent_name,
            endpoint="/chat/message"
        )
        return cached_response

    collector.record_cache_miss(
        agent_name=request.agent_name,
        endpoint="/chat/message"
    )

    # Process request...
    response = await process_chat(request)

    # Track cost (set in request.state by LLM middleware)
    if hasattr(request.state, "llm_cost"):
        collector.record_cost(
            cost_usd=request.state.llm_cost,
            agent_name=request.agent_name,
            prompt_tokens=request.state.prompt_tokens,
            completion_tokens=request.state.completion_tokens
        )

    return response
```

### With Celery

```python
# celeryconfig.py
from app.infrastructure.monitoring.background_tasks import setup_monitoring_schedule

beat_schedule = setup_monitoring_schedule()
```

### With Kubernetes

```yaml
# deployment.yaml
apiVersion: v1
kind: Service
metadata:
  name: anvil-backend
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/monitoring/metrics"
spec:
  ports:
    - port: 8000
      name: http
  selector:
    app: anvil-backend

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anvil-backend
spec:
  template:
    spec:
      containers:
        - name: api
          image: anvil-backend:latest
          ports:
            - containerPort: 8000
          livenessProbe:
            httpGet:
              path: /monitoring/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /monitoring/health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
```

## Future Enhancements

- [ ] OpenTelemetry integration
- [ ] Distributed tracing with Jaeger
- [ ] Custom metric exporters (InfluxDB, TimescaleDB)
- [ ] Advanced anomaly detection
- [ ] Machine learning-based alerting
- [ ] Auto-scaling based on metrics
- [ ] SLO/SLI tracking
- [ ] Business metrics dashboards
- [ ] Multi-region aggregation

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Celery Beat](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
