# Enterprise Telemetry & Analytics

## Overview

The Anvil Backend implements enterprise-grade telemetry and analytics for comprehensive system observability:

- **External API Metrics**: Request counts, latency percentiles, error rates, cache hit rates
- **LLM Provider Metrics**: Token usage, cost tracking, budget alerts per provider/model
- **Database Query Metrics**: Query timing, slow query detection, pattern analysis, connection pool monitoring
- **Distributed Tracing**: OpenTelemetry-compatible tracing with W3C Trace Context
- **Prometheus Export**: Metrics in Prometheus/OpenMetrics format for Grafana dashboards
- **Real-time Alerting**: Configurable thresholds for errors, latency, rate limits, and budget

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API Request                                   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              InstrumentedClient / TelemetryMixin                     │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│   │  Start Timing   │──│  Execute Call   │──│  Record Result  │    │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌───────────────────┐                         ┌───────────────────┐
│   APITelemetry    │                         │  TracingService   │
│   ─────────────   │                         │  ─────────────    │
│   - Metrics       │                         │  - Spans          │
│   - Error rates   │                         │  - Traces         │
│   - Latencies     │                         │  - W3C Context    │
│   - Cost tracking │                         │  - Propagation    │
└───────────────────┘                         └───────────────────┘
        │                                               │
        ▼                                               ▼
┌───────────────────┐                         ┌───────────────────┐
│ PrometheusExport  │                         │   Trace Storage   │
│ /telemetry/prom   │                         │  /telemetry/trace │
└───────────────────┘                         └───────────────────┘
```

## Components

### 1. API Telemetry (`APITelemetry`)

Core telemetry service that tracks all external API calls.

**Location**: `src/app/infrastructure/telemetry/api_telemetry.py`

**Features**:
- Request/response timing
- Error categorization (timeout, rate limit, auth failure, validation)
- Latency percentiles (p50, p95, p99)
- Cache hit rate tracking
- Cost estimation per API
- Real-time alerting

**Usage**:
```python
from app.infrastructure.telemetry import APITelemetry, get_api_telemetry

telemetry = get_api_telemetry()

# Start tracking
ctx = telemetry.start_call("coingecko", "get_price", coin_id="ethereum")

try:
    result = await coingecko.get_price("ethereum")
    ctx.complete(status=APIStatus.SUCCESS, status_code=200)
except Exception as e:
    ctx.complete(status=APIStatus.ERROR, error_message=str(e))
finally:
    await telemetry.record(ctx)

# Get metrics
metrics = telemetry.get_metrics("coingecko")
print(f"Success rate: {metrics['success_rate']}%")
print(f"P95 latency: {metrics['latency_ms']['p95']}ms")
```

### 2. Distributed Tracing (`TracingService`)

OpenTelemetry-compatible distributed tracing with W3C Trace Context propagation.

**Location**: `src/app/infrastructure/telemetry/tracing.py`

**Features**:
- Span creation with attributes
- Automatic context propagation
- W3C Trace Context headers
- Event logging within spans
- Slow trace detection

**Usage**:
```python
from app.infrastructure.telemetry import TracingService, SpanKind, get_tracing_service

tracing = get_tracing_service()

with tracing.start_span("api_call", kind=SpanKind.CLIENT) as span:
    span.set_attribute("api", "coingecko")
    span.set_attribute("operation", "get_price")
    
    try:
        result = await api_call()
        span.add_event("response_received", {"size": len(result)})
    except Exception as e:
        span.set_status(SpanStatus.ERROR, str(e))
        raise

# Get traces
traces = tracing.get_recent_traces(limit=20)
```

### 3. Prometheus Metrics Export (`MetricsExporter`)

Exports metrics in Prometheus/OpenMetrics format for scraping.

**Location**: `src/app/infrastructure/telemetry/metrics_exporter.py`

**Exported Metrics**:
```
# API request counter
anvil_api_requests_total{api="coingecko",operation="all",status="success"} 1234

# API error counter
anvil_api_errors_total{api="coingecko",operation="get_price",error_type="timeout"} 5

# API rate limits
anvil_api_rate_limits_total{api="oneinch"} 3

# Cache hits
anvil_api_cache_hits_total{api="coingecko",operation="all"} 567

# Estimated cost
anvil_api_estimated_cost_usd{api="coingecko"} 0.0

# Request duration histogram
anvil_api_request_duration_seconds_bucket{api="coingecko",operation="get_price",le="0.5"} 100
anvil_api_request_duration_seconds_sum{api="coingecko",operation="get_price"} 45.2
anvil_api_request_duration_seconds_count{api="coingecko",operation="get_price"} 123
```

### 4. Instrumented Clients

Pre-instrumented API clients with automatic telemetry.

**Location**: `src/app/infrastructure/adapters/external/instrumented/`

**Available Clients**:
- `InstrumentedCoinGeckoClient`
- `InstrumentedDefiLlamaClient`
- `InstrumentedOneInchClient`
- `InstrumentedTheGraphClient`

**Usage**:
```python
from app.infrastructure.adapters.external.instrumented import InstrumentedCoinGeckoClient

# Create instrumented client
client = InstrumentedCoinGeckoClient(api_key="...")

# All calls automatically instrumented
price = await client.get_price("ethereum")
chart = await client.get_market_chart("bitcoin", days=30)
```

## API Endpoints

### Telemetry Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/telemetry/metrics` | GET | Get API telemetry metrics (JSON) |
| `/telemetry/prometheus` | GET | Get Prometheus-format metrics |
| `/telemetry/traces` | GET | Get recent distributed traces |
| `/telemetry/traces/{id}` | GET | Get specific trace details |
| `/telemetry/slow-calls` | GET | Get slow API calls analysis |
| `/telemetry/slow-traces` | GET | Get slow traces analysis |
| `/telemetry/errors` | GET | Get recent error analysis |
| `/telemetry/health` | GET | Get telemetry system health |
| `/telemetry/reset` | POST | Reset telemetry (admin only) |

### Example Responses

**GET /telemetry/metrics**
```json
{
  "summary": {
    "total_requests": 15234,
    "total_errors": 45,
    "overall_error_rate": 0.30,
    "total_estimated_cost_usd": 1.23,
    "apis_tracked": 8
  },
  "by_api": {
    "coingecko": {
      "api": "coingecko",
      "total_requests": 5000,
      "successful_requests": 4980,
      "failed_requests": 20,
      "cached_requests": 3500,
      "success_rate": 99.60,
      "cache_hit_rate": 70.00,
      "latency_ms": {
        "avg": 125.5,
        "min": 45.0,
        "max": 2500.0,
        "p50": 100.0,
        "p95": 350.0,
        "p99": 800.0
      },
      "estimated_cost_usd": 0.0
    }
  }
}
```

**GET /telemetry/traces**
```json
[
  {
    "trace_id": "abc123def456...",
    "root_span": "chat.send_message",
    "duration_ms": 1250.5,
    "status": "ok",
    "start_time": "2025-12-06T12:00:00Z",
    "span_count": 8
  }
]
```

## Configuration

### Local Development (`config/local/config.toml`)

```toml
[telemetry]
ENABLED = true
ASYNC_RECORDING = true
RETENTION_HOURS = 24
MAX_RECORDS = 100000
SAMPLE_RATE = 1.0              # 100% sampling

# Alerting Thresholds
ERROR_RATE_THRESHOLD = 0.05    # 5% triggers alert
LATENCY_THRESHOLD_MS = 5000    # 5s triggers alert
RATE_LIMIT_ALERT_COUNT = 3

[telemetry.tracing]
ENABLED = true
SERVICE_NAME = "anvil-backend-local"
MAX_SPANS = 10000
```

### Production (`config/prod/config.toml`)

```toml
[telemetry]
ENABLED = true
ASYNC_RECORDING = true
RETENTION_HOURS = 168          # 7 days
MAX_RECORDS = 1000000
SAMPLE_RATE = 0.1              # 10% sampling

# Stricter thresholds for production
ERROR_RATE_THRESHOLD = 0.01    # 1% triggers alert
LATENCY_THRESHOLD_MS = 3000    # 3s triggers alert
RATE_LIMIT_ALERT_COUNT = 5

[telemetry.tracing]
ENABLED = true
SERVICE_NAME = "anvil-backend-prod"
MAX_SPANS = 100000
```

## Adding Telemetry to New APIs

### Option 1: Use `@instrumented` Decorator

```python
from app.infrastructure.telemetry.instrumented_client import instrumented

class MyAPIClient:
    @instrumented("my_api", "get_data")
    async def get_data(self, param: str):
        # Your API call
        return await self._http_client.get(f"/data/{param}")
```

### Option 2: Use `InstrumentedClient`

```python
from app.infrastructure.telemetry.instrumented_client import InstrumentedClient

client = InstrumentedClient(
    api_name="my_api",
    base_url="https://api.example.com",
)

response = await client.get("/data", operation="get_data", params={"id": "123"})
```

### Option 3: Use `TelemetryMixin`

```python
from app.infrastructure.telemetry.instrumented_client import TelemetryMixin

class MyClientWithTelemetry(TelemetryMixin, MyClient):
    API_NAME = "my_api"
    
    async def get_data(self, param: str):
        return await self._with_telemetry(
            "get_data",
            super().get_data,
            param,
        )
```

## Grafana Dashboard Integration

### Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: 'anvil-backend'
    metrics_path: '/telemetry/prometheus'
    static_configs:
      - targets: ['anvil-backend:9999']
```

### Example Grafana Queries

**API Request Rate**:
```promql
rate(anvil_api_requests_total[5m])
```

**Error Rate by API**:
```promql
sum by (api) (rate(anvil_api_errors_total[5m])) 
/ 
sum by (api) (rate(anvil_api_requests_total[5m])) * 100
```

**P95 Latency**:
```promql
histogram_quantile(0.95, rate(anvil_api_request_duration_seconds_bucket[5m]))
```

**Total Estimated Cost**:
```promql
sum(anvil_api_estimated_cost_usd)
```

## Alerting Rules

### Prometheus Alerting Rules

```yaml
groups:
  - name: anvil_api_alerts
    rules:
      - alert: HighAPIErrorRate
        expr: |
          sum by (api) (rate(anvil_api_errors_total[5m])) 
          / 
          sum by (api) (rate(anvil_api_requests_total[5m])) 
          > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate for {{ $labels.api }}"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: APIRateLimited
        expr: increase(anvil_api_rate_limits_total[5m]) > 3
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API {{ $labels.api }} is being rate limited"
```

## LLM Provider Telemetry

### Overview

Track LLM usage, costs, and performance across all AI providers.

**Location**: `src/app/infrastructure/telemetry/llm_telemetry.py`

### Features

- Per-provider and per-model token tracking
- Cost calculation with configurable model pricing
- Monthly budget tracking with alerts
- Latency percentiles (p50, p90, p99)
- Error rate monitoring
- Rate limit detection

### Usage

```python
from app.infrastructure.telemetry import LLMTelemetry, LLMCallStatus

telemetry = LLMTelemetry()

# Start tracking
ctx = telemetry.start_call(
    provider="vertex_ai",
    model="gemini-1.5-pro",
    operation="generate",
)

try:
    response = await llm.generate(...)
    ctx.complete(
        status=LLMCallStatus.SUCCESS,
        input_tokens=500,
        output_tokens=200,
        cost_usd=0.003,
    )
except Exception as e:
    ctx.complete(
        status=LLMCallStatus.ERROR,
        error_message=str(e),
    )
finally:
    await telemetry.record(ctx)

# Get metrics
metrics = telemetry.get_summary()
print(f"Monthly cost: ${metrics['monthly_cost_usd']:.2f}")
print(f"Budget used: {metrics['budget_used_percent']}%")
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /telemetry/llm/metrics` | Overall LLM metrics |
| `GET /telemetry/llm/costs` | Cost breakdown by provider/model |
| `GET /telemetry/llm/models` | Model usage statistics |
| `GET /telemetry/llm/alerts` | Budget and error alerts |
| `GET /telemetry/llm/providers` | Provider summary |

### Instrumented Gateway

Use `InstrumentedLLMGateway` for automatic instrumentation:

```python
from app.infrastructure.adapters.ai.instrumented_llm_gateway import (
    InstrumentedLLMGateway,
)

instrumented = InstrumentedLLMGateway(
    gateway=existing_gateway,
    telemetry=llm_telemetry,
)

# All calls are automatically instrumented
response = await instrumented.generate_response(
    model_name="gemini-1.5-pro",
    messages=[{"role": "user", "content": "Hello"}],
)
```

---

## Database Query Telemetry

### Overview

Monitor database query performance, detect slow queries, and analyze patterns.

**Location**: `src/app/infrastructure/telemetry/db_telemetry.py`

### Features

- Query execution timing via SQLAlchemy event listeners
- Slow query detection with configurable thresholds
- Query pattern analysis and normalization
- Connection pool monitoring
- Error categorization (timeout, deadlock)
- Per-table query statistics

### Usage

```python
from app.infrastructure.telemetry import (
    DatabaseTelemetry,
    setup_engine_telemetry,
)

# Setup with SQLAlchemy engine
db_telemetry = DatabaseTelemetry()
setup_engine_telemetry(engine, db_telemetry)

# Queries are automatically tracked via event listeners

# Get metrics
metrics = db_telemetry.get_metrics()
print(f"Total queries: {metrics['total_queries']}")
print(f"Slow queries: {metrics['slow_queries']}")

# Get slow queries
slow = db_telemetry.get_slow_queries(threshold_ms=100)
for query in slow:
    print(f"{query['duration_ms']}ms: {query['query_text'][:50]}...")

# Get query patterns
patterns = db_telemetry.get_query_patterns(order_by="avg_duration")
for pattern in patterns:
    print(f"{pattern['avg_duration_ms']}ms avg: {pattern['query_template'][:50]}...")
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /telemetry/db/metrics` | Overall database metrics |
| `GET /telemetry/db/slow-queries` | Slow query list |
| `GET /telemetry/db/patterns` | Query pattern analysis |
| `GET /telemetry/db/pool` | Connection pool stats |
| `GET /telemetry/db/tables/{table}` | Per-table statistics |
| `GET /telemetry/db/errors` | Recent query errors |
| `GET /telemetry/db/summary` | Comprehensive summary |

### Configuration

```toml
[telemetry]
# Database telemetry
DB_SLOW_QUERY_THRESHOLD_MS = 100
DB_VERY_SLOW_QUERY_THRESHOLD_MS = 1000
DB_TRACK_QUERY_PATTERNS = true
DB_LOG_SLOW_QUERIES = true
```

---

## Best Practices

1. **Use Instrumented Clients**: Prefer `InstrumentedClient` variants for automatic telemetry
2. **Set Appropriate Sampling**: Use 100% sampling in dev, 10% in production
3. **Monitor Rate Limits**: Critical for APIs like 1inch with strict rate limits
4. **Track Costs**: Use cost estimates for budget planning (especially LLM costs)
5. **Review Slow Calls**: Regularly check `/telemetry/slow-calls` and `/telemetry/db/slow-queries`
6. **Set Budget Alerts**: Configure LLM budget alerts to prevent cost overruns
7. **Monitor Query Patterns**: Use pattern analysis to identify optimization opportunities
8. **Set Up Dashboards**: Use Grafana for real-time monitoring
9. **Configure Alerts**: Set up alerts for errors, latency, rate limits, and budget

## Files Reference

| File | Purpose |
|------|---------|
| `src/app/infrastructure/telemetry/__init__.py` | Module exports |
| `src/app/infrastructure/telemetry/api_telemetry.py` | Core API telemetry service |
| `src/app/infrastructure/telemetry/llm_telemetry.py` | LLM provider telemetry |
| `src/app/infrastructure/telemetry/db_telemetry.py` | Database query telemetry |
| `src/app/infrastructure/telemetry/metrics_exporter.py` | Prometheus export |
| `src/app/infrastructure/telemetry/tracing.py` | Distributed tracing |
| `src/app/infrastructure/telemetry/instrumented_client.py` | HTTP client with telemetry |
| `src/app/infrastructure/adapters/external/instrumented/` | Pre-instrumented API clients |
| `src/app/infrastructure/adapters/ai/instrumented_llm_gateway.py` | Instrumented LLM gateway |
| `src/app/setup/ioc/telemetry.py` | DI provider |
| `src/app/presentation/http/controllers/telemetry/` | API endpoints |
| `config/local/config.toml` | Local telemetry config |
| `config/prod/config.toml` | Production telemetry config |
