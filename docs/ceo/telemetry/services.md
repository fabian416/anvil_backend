# AI Telemetry System Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The AI Telemetry System provides comprehensive observability through:
- **LLM Telemetry** - Token usage, cost tracking, provider health
- **API Telemetry** - External API call monitoring
- **Database Telemetry** - Query performance tracking
- **Distributed Tracing** - Request flow tracing
- **Metrics Collection** - Prometheus-compatible metrics
- **Alerting** - Budget and error rate alerts

**Total Service Components**: 25+ Python modules

---

## 1. Core Telemetry Services

### 1.1 LLM Telemetry Service
**Path**: `src/app/infrastructure/telemetry/llm_telemetry.py`

Enterprise-grade telemetry for LLM provider monitoring.

```python
class LLMTelemetry:
    """
    Enterprise telemetry service for LLM providers.
    
    Features:
    - Token usage and cost tracking
    - Latency metrics with percentiles (p50, p90, p99)
    - Provider health monitoring
    - Budget alerting
    - Rate limit detection
    """
    
    def start_call(
        self,
        provider: str,
        model: str,
        operation: str = "generate",
        **metadata
    ) -> LLMCallContext
    
    async def record(self, ctx: LLMCallContext) -> None
    
    def get_provider_metrics(self, provider: str) -> LLMProviderMetrics
    def get_all_metrics(self) -> dict[str, LLMProviderMetrics]
    def get_summary(self) -> dict[str, Any]
    def get_alerts(self, severity: AlertSeverity, hours: int) -> list[LLMAlert]
    def get_model_usage(self) -> dict[str, dict[str, Any]]
    def get_cost_breakdown(self) -> dict[str, Any]
```

**Configuration** (`LLMTelemetryConfig`):
```python
@dataclass
class LLMTelemetryConfig:
    enabled: bool = True
    async_recording: bool = True
    retention_hours: int = 24
    max_records: int = 100000
    
    # Cost tracking
    enable_cost_tracking: bool = True
    monthly_budget_usd: float = 1000.0
    budget_alert_threshold: float = 0.8  # 80%
    
    # Error thresholds
    error_rate_threshold: float = 0.05  # 5%
    latency_threshold_ms: int = 30000  # 30s
    rate_limit_alert_count: int = 3
    
    # Model costs (per 1M tokens)
    model_costs: dict[str, dict[str, float]] = {...}
```

**Model Cost Configuration**:
| Model | Input Cost | Output Cost |
|-------|------------|-------------|
| gemini-1.5-pro | $1.25 | $5.00 |
| gemini-1.5-flash | $0.075 | $0.30 |
| gpt-4o | $2.50 | $10.00 |
| claude-3-5-sonnet | $3.00 | $15.00 |
| LLaMA-3.2-70B | $0.52 | $0.75 |

---

### 1.2 API Telemetry Service
**Path**: `src/app/infrastructure/telemetry/api_telemetry.py`

Tracks external API calls (CoinGecko, DeFiLlama, 1inch, etc.).

```python
class APITelemetry:
    """
    External API call telemetry.
    
    Tracks:
    - Request counts (total, successful, failed, cached)
    - Latency statistics (avg, min, max, p50, p95, p99)
    - Error rates and error breakdown
    - Rate limit events
    - Estimated API costs
    """
    
    def record_call(
        self,
        api: str,
        operation: str,
        duration_ms: float,
        status: str,
        cached: bool = False
    ) -> None
    
    def get_metrics(self, api: str) -> dict
    def get_all_metrics(self) -> dict
    def get_slow_calls(self, threshold_ms: float, limit: int) -> list[dict]
    def get_errors(self, api: str, limit: int) -> list[dict]
```

---

### 1.3 Database Telemetry Service
**Path**: `src/app/infrastructure/telemetry/db_telemetry.py`

Tracks database query performance.

```python
class DatabaseTelemetry:
    """
    Database query telemetry.
    
    Tracks:
    - Total query counts (by type)
    - Success/error rates
    - Duration statistics
    - Queries by table
    - Slow query counts
    - Connection pool statistics
    """
    
    def record_query(
        self,
        query: str,
        query_type: str,
        duration_ms: float,
        row_count: int,
        error: str | None = None
    ) -> None
    
    def get_metrics(self) -> dict
    def get_slow_queries(self, limit: int, threshold_ms: float) -> list[dict]
    def get_query_patterns(self, order_by: str, limit: int) -> list[dict]
    def get_pool_stats(self) -> dict
    def get_queries_by_table(self, table: str) -> dict
    def get_recent_errors(self, limit: int) -> list[dict]
    def get_summary(self) -> dict
```

---

### 1.4 Tracing Service
**Path**: `src/app/infrastructure/telemetry/tracing.py`

Distributed tracing for request flow tracking.

```python
class TracingService:
    """
    Distributed tracing service.
    
    Features:
    - Trace creation and span management
    - Parent-child span relationships
    - Attributes and events
    - Trace retrieval and search
    """
    
    def start_trace(self, name: str, attributes: dict = None) -> TraceContext
    def start_span(self, trace_id: str, name: str, parent_id: str = None) -> Span
    def end_span(self, span: Span) -> None
    
    def get_recent_traces(self, limit: int) -> list[dict]
    def get_trace(self, trace_id: str) -> list[dict]
    def get_slow_traces(self, threshold_ms: float, limit: int) -> list[dict]
```

---

### 1.5 Metrics Exporter
**Path**: `src/app/infrastructure/telemetry/metrics_exporter.py`

Exports metrics in Prometheus format.

```python
class MetricsExporter:
    """
    Prometheus metrics exporter.
    
    Exports:
    - anvil_api_requests_total
    - anvil_api_request_duration_seconds
    - anvil_api_errors_total
    - anvil_api_rate_limits_total
    - anvil_api_cache_hits_total
    - anvil_api_estimated_cost_usd
    - anvil_llm_requests_total
    - anvil_llm_tokens_total
    - anvil_llm_cost_usd
    """
    
    def export(self) -> str
    def export_llm_metrics(self) -> str
    def export_api_metrics(self) -> str
    def export_db_metrics(self) -> str
```

---

### 1.6 Feature Flags Service
**Path**: `src/app/infrastructure/telemetry/feature_flags.py`

Runtime telemetry configuration.

```python
@dataclass
class TelemetryFeatureFlags:
    """Runtime telemetry configuration."""
    
    global_enabled: bool = True
    api_telemetry_enabled: bool = True
    llm_telemetry_enabled: bool = True
    db_telemetry_enabled: bool = True
    tracing_enabled: bool = True
    
    api_sample_rate: float = 1.0  # 100%
    llm_sample_rate: float = 1.0  # 100%
    db_sample_rate: float = 0.1  # 10%
    
    disabled_apis: set[str] = field(default_factory=set)
    disabled_llm_providers: set[str] = field(default_factory=set)
    
    def to_dict(self) -> dict
    def is_api_enabled(self, api: str) -> bool
    def is_llm_provider_enabled(self, provider: str) -> bool


def get_feature_flags() -> TelemetryFeatureFlags
def set_feature_flags(flags: TelemetryFeatureFlags) -> None
async def save_flags_to_redis(flags: TelemetryFeatureFlags, redis: Redis) -> bool
async def load_flags_from_redis(redis: Redis) -> TelemetryFeatureFlags | None
async def delete_flags_from_redis(redis: Redis) -> bool
```

---

### 1.7 Alert Destinations
**Path**: `src/app/infrastructure/telemetry/alert_destinations.py`

Alert delivery to external systems.

---

### 1.8 Instrumented Client Base
**Path**: `src/app/infrastructure/telemetry/instrumented_client.py`

Base class for instrumented API clients.

```python
class InstrumentedClient:
    """
    Base class for instrumented API clients.
    
    Automatically tracks:
    - Request count
    - Latency
    - Error rates
    - Rate limits
    """
    
    async def _instrumented_call(
        self,
        operation: str,
        call_fn: Callable,
        **kwargs
    ) -> Any
```

---

## 2. Monitoring Services

### 2.1 Metrics Service
**Path**: `src/app/infrastructure/monitoring/metrics.py`

System-wide metrics collection.

---

### 2.2 Metrics Collector (Chat)
**Path**: `src/app/infrastructure/monitoring/metrics_collector.py`

Prometheus-compatible metrics collector for chat features.

```python
class ChatMetricsCollector:
    """
    Production-ready metrics collector for chat features.
    
    Metrics:
    - chat_requests_total (counter)
    - chat_errors_total (counter)
    - chat_response_time_seconds (histogram)
    - chat_cache_hits_total (counter)
    - chat_cache_misses_total (counter)
    - chat_cost_usd_total (gauge)
    - chat_agent_available (gauge)
    - chat_active_requests (gauge)
    """
    
    def increment_request_count(
        self,
        agent_name: str,
        user_id: str,
        endpoint: str,
        status: str
    ) -> None
    
    def record_response_time(
        self,
        duration_seconds: float,
        agent_name: str,
        endpoint: str
    ) -> None
    
    def record_cost(
        self,
        cost_usd: float,
        agent_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> None
    
    def export_prometheus(self) -> str
```

---

### 2.3 Health Checks
**Path**: `src/app/infrastructure/monitoring/health_checks.py`

System health check services.

```python
class HealthCheckService:
    """
    Health check service for system components.
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - LLM provider availability
    - External API availability
    """
    
    async def check_database(self) -> HealthStatus
    async def check_redis(self) -> HealthStatus
    async def check_llm_providers(self) -> dict[str, HealthStatus]
    async def get_overall_health(self) -> SystemHealth
```

---

### 2.4 Alerting Service
**Path**: `src/app/infrastructure/monitoring/alerting.py`

Alert generation and notification.

```python
class AlertingService:
    """
    Alerting service for system events.
    
    Alert types:
    - Budget alerts (threshold reached)
    - Error rate alerts (spike detected)
    - Latency alerts (threshold exceeded)
    - Provider health alerts
    """
    
    async def check_budget_alerts(self) -> list[Alert]
    async def check_error_rate_alerts(self) -> list[Alert]
    async def send_alert(self, alert: Alert) -> None
```

---

### 2.5 Middleware
**Path**: `src/app/infrastructure/monitoring/middleware.py`

Request telemetry middleware.

```python
class TelemetryMiddleware:
    """
    FastAPI middleware for request telemetry.
    
    Tracks:
    - Request count
    - Response time
    - Error rates
    - Request/response size
    """
```

---

### 2.6 Background Tasks
**Path**: `src/app/infrastructure/monitoring/background_tasks.py`

Background monitoring tasks.

---

### 2.7 CloudWatch Metrics
**Path**: `src/app/infrastructure/monitoring/cloudwatch_metrics.py`

AWS CloudWatch metrics integration.

---

### 2.8 Sentry Configuration
**Path**: `src/app/infrastructure/monitoring/sentry_config.py`

Sentry error tracking configuration.

---

## 3. Instrumented External Clients

**Path**: `src/app/infrastructure/adapters/external/instrumented/`

| Client | File | Description |
|--------|------|-------------|
| CoinGecko | `instrumented_coingecko_client.py` | Price data API |
| DeFiLlama | `instrumented_defillama_client.py` | TVL and yield data |
| 1inch | `instrumented_oneinch_client.py` | DEX aggregator |
| Uniswap | `instrumented_uniswap_client.py` | DEX API |
| Aave | `instrumented_aave_client.py` | Lending protocol |
| Curve | `instrumented_curve_client.py` | AMM API |
| Hyperliquid | `instrumented_hyperliquid_client.py` | Perps API |
| The Graph | `instrumented_thegraph_client.py` | Subgraph API |
| Gas Oracle | `instrumented_gas_oracle_client.py` | Gas price API |

---

## 4. Database Repositories

### 4.1 Retry Telemetry Repository
**Path**: `src/app/infrastructure/persistence_sqla/repositories/retry_telemetry_repository.py`

Stores retry telemetry data.

---

### 4.2 Distillation Telemetry Repository
**Path**: `src/app/infrastructure/persistence_sqla/repositories/distillation_telemetry_repository.py`

Stores distillation telemetry data.

---

### 4.3 Analytics Repository
**Path**: `src/app/infrastructure/adapters/analytics_repository_sqla.py`

Stores analytics snapshots.

---

## 5. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    Telemetry Router                                  │    │
│  │  /flags • /metrics • /traces • /llm/* • /db/* • /prometheus        │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    Monitoring Router                                 │    │
│  │  /health • /metrics                                                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TELEMETRY SERVICES                                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Core Telemetry                                    │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │    LLM      │  │    API      │  │  Database   │  │  Tracing    │  │  │
│  │  │  Telemetry  │  │  Telemetry  │  │  Telemetry  │  │  Service    │  │  │
│  │  │             │  │             │  │             │  │             │  │  │
│  │  │ • Tokens    │  │ • Requests  │  │ • Queries   │  │ • Traces    │  │  │
│  │  │ • Costs     │  │ • Latency   │  │ • Latency   │  │ • Spans     │  │  │
│  │  │ • Latency   │  │ • Errors    │  │ • Patterns  │  │ • Attrs     │  │  │
│  │  │ • Alerts    │  │ • Rate Lim  │  │ • Pool      │  │             │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Support Services                                 │  │
│  │                                                                        │  │
│  │  MetricsExporter • FeatureFlags • AlertDestinations                  │  │
│  │  InstrumentedClient • ChatMetricsCollector                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MONITORING SERVICES                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  HealthChecks • AlertingService • TelemetryMiddleware               │  │
│  │  BackgroundTasks • CloudWatchMetrics • SentryConfig                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INSTRUMENTED CLIENTS                                    │
│                                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  CoinGecko  │ │ DeFiLlama   │ │   1inch     │ │   Aave      │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Curve     │ │ Hyperliquid │ │  The Graph  │ │  Gas Oracle │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA STORAGE                                           │
│                                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐   │
│  │     PostgreSQL       │  │       Redis          │  │   Prometheus    │   │
│  │                      │  │                      │  │                 │   │
│  │  AI Telemetry Tables │  │  Feature Flags       │  │  Metrics        │   │
│  │  (13+ tables)        │  │  Session Data        │  │  Scraping       │   │
│  └──────────────────────┘  └──────────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## References

- **Telemetry Services**: `src/app/infrastructure/telemetry/`
- **Monitoring Services**: `src/app/infrastructure/monitoring/`
- **Instrumented Clients**: `src/app/infrastructure/adapters/external/instrumented/`
- **Telemetry Router**: `src/app/presentation/http/controllers/telemetry/router.py`
