# Retry & Resilience Metadata & Architecture

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Anvil Retry & Resilience system provides enterprise-grade fault tolerance:
- **EnterpriseRetryEngine** - Intelligent retry with exponential backoff
- **CircuitBreaker** - Cascade failure prevention (Redis-backed)
- **ServiceRegistry** - Manual service override for maintenance
- **TelemetryCollector** - Comprehensive metrics tracking

**Database Tables**: 4 tables  
**Total Modules**: 20+ Python files

---

## 1. Module Status

| Component | Status | Health | Notes |
|-----------|--------|--------|-------|
| EnterpriseRetryEngine | ✅ Production | Healthy | Full retry logic |
| CircuitBreaker | ✅ Production | Healthy | Redis-backed state |
| CircuitBreakerManager | ✅ Production | Healthy | Multi-service management |
| ServiceRegistry | ✅ Production | Healthy | Manual override |
| TelemetryCollector | ✅ Production | Healthy | Event tracking |
| RetryConfig | ✅ Production | Healthy | Configuration presets |
| Admin Router | ✅ Production | Healthy | 7 endpoints |
| Telemetry Repository | ✅ Production | Healthy | DB persistence |
| Test Coverage | ⚠️ Good | ~70% | Gaps in E2E tests |
| Celery Tasks | ❌ None | N/A | Recommended tasks |

---

## 2. File Reference Index

### 2.1 Domain Layer

```
src/app/domain/services/retry/
├── __init__.py
├── retry_engine.py           # EnterpriseRetryEngine
├── circuit_breaker.py        # CircuitBreaker, CircuitBreakerManager
├── service_registry.py       # ServiceRegistry for manual override
└── telemetry_collector.py    # RetryTelemetryCollector

src/app/domain/value_objects/
├── retry_config.py           # RetryConfig value object
└── retry_count.py            # RetryCount value object
```

### 2.2 Application Layer

```
src/app/application/admin/retry/
├── __init__.py
├── get_service_list.py       # List all services
├── get_service_status.py     # Get specific service status
├── disable_service.py        # Manually disable service
├── enable_service.py         # Manually enable service
├── get_circuit_status.py     # Get circuit breaker statuses
├── reset_circuit_breaker.py  # Reset circuit breaker
└── get_service_metrics.py    # Get aggregated metrics
```

### 2.3 Presentation Layer

```
src/app/presentation/http/controllers/admin/retry/
├── __init__.py
├── router.py                 # Admin retry API router
└── schemas.py                # Request/response schemas
```

### 2.4 Infrastructure Layer

```
src/app/infrastructure/persistence_sqla/
├── mappings/
│   └── retry_telemetry.py    # SQLAlchemy table definitions
├── repositories/
│   └── retry_telemetry_repository.py  # Telemetry repository
└── alembic/versions/
    └── 2025_12_01_1500-add_retry_telemetry_tables.py  # Migration

src/app/infrastructure/adapters/ai/llm/
└── retry_handler.py          # LLM provider retry handler

src/app/infrastructure/mcp/
└── base_retry.py             # MCP server retry base class
```

### 2.5 Tests

```
tests/integration/retry/
├── __init__.py
├── test_retry_engine.py      # RetryEngine integration tests
└── test_circuit_breaker.py   # CircuitBreaker integration tests
```

### 2.6 Integration Points

```
# MCP Servers
src/app/infrastructure/mcp/servers/
├── defillama_mcp.py          # Uses retry engine
├── oneinch_mcp.py            # Uses retry engine
├── coingecko_mcp.py          # Uses retry engine
└── [all other MCP servers]

# LLM Providers
src/app/infrastructure/llm/providers/
├── vertex_ai_adapter.py      # Uses retry handler
├── deepinfra_adapter.py      # Uses retry handler
└── bedrock_adapter.py        # Uses retry handler

# Agno Agents
src/app/infrastructure/agno/
├── base_agent.py             # Uses retry engine
├── pool.py                   # Pool with retry
└── batch.py                  # Batch with retry
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Admin Retry Router                                 │  │
│  │                    /api/v1/admin/retry/*                              │  │
│  │                                                                        │  │
│  │  GET  /services              - List all services                      │  │
│  │  GET  /services/{name}       - Get service status                     │  │
│  │  POST /services/{name}/disable - Disable service                      │  │
│  │  POST /services/{name}/enable  - Enable service                       │  │
│  │  GET  /circuit-breakers      - Get all circuit statuses               │  │
│  │  POST /circuit-breakers/{name}/reset - Reset circuit                  │  │
│  │  GET  /metrics/{name}        - Get service metrics                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Interactors                                   │  │
│  │                                                                        │  │
│  │  GetServiceList     GetServiceStatus     DisableService               │  │
│  │  EnableService      GetCircuitStatus     ResetCircuitBreaker          │  │
│  │  GetServiceMetrics                                                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Core Services                                     │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                  EnterpriseRetryEngine                          │ │  │
│  │  │                                                                   │ │  │
│  │  │  Flow:                                                           │ │  │
│  │  │  1. Check ServiceRegistry (manual disable?)                      │ │  │
│  │  │  2. Check CircuitBreaker (too many failures?)                    │ │  │
│  │  │  3. Execute function                                             │ │  │
│  │  │  4. Record telemetry                                             │ │  │
│  │  │  5. Update circuit breaker state                                 │ │  │
│  │  │                                                                   │ │  │
│  │  │  Features:                                                       │ │  │
│  │  │  • Exponential backoff with jitter                               │ │  │
│  │  │  • Error classification (retryable vs non-retryable)             │ │  │
│  │  │  • Configurable max retries, backoff, timeouts                   │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                        │  │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │  │
│  │  │  CircuitBreaker   │  │  ServiceRegistry  │  │   Telemetry     │  │  │
│  │  │                   │  │                   │  │   Collector     │  │  │
│  │  │ • CLOSED → OPEN   │  │ • Manual disable  │  │                 │  │  │
│  │  │ • OPEN → HALF_OPEN│  │ • Manual enable   │  │ • Record attempts│ │  │
│  │  │ • HALF_OPEN →     │  │ • Auto-expiry     │  │ • Record CB state│ │  │
│  │  │   CLOSED/OPEN     │  │ • TTL support     │  │ • Record overrides│ │  │
│  │  └───────────────────┘  └───────────────────┘  └─────────────────┘  │  │
│  │                                                                        │  │
│  │  ┌──────────────────────────────────────────────────────────────┐    │  │
│  │  │                      Value Objects                            │    │  │
│  │  │  RetryConfig (with presets: MCP, Agno, Testing)               │    │  │
│  │  │  CircuitBreakerConfig (thresholds, timeouts)                  │    │  │
│  │  │  RetryEventType (ATTEMPT_START, SUCCESS, FAILURE, etc.)       │    │  │
│  │  │  CircuitState (CLOSED, OPEN, HALF_OPEN)                       │    │  │
│  │  └──────────────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Redis (Real-time State)                           │   │
│  │                                                                       │   │
│  │  circuit:{service}:state         - Circuit breaker state             │   │
│  │  circuit:{service}:failures      - Failure counter                   │   │
│  │  circuit:{service}:half_open_successes - Half-open success counter   │   │
│  │  circuit:{service}:opened_at     - Timestamp when circuit opened     │   │
│  │  service:{service}:override      - Manual override (enabled/disabled)│   │
│  │  service:{service}:override_metadata - Override metadata (JSON)      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   RetryTelemetryRepository                           │   │
│  │                                                                       │   │
│  │  • create_attempt()           • increment_success()                  │   │
│  │  • create_circuit_event()     • increment_failure()                  │   │
│  │  • create_override_event()    • get_aggregated_metrics()             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Integration Points                                │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │   │
│  │  │   MCP Servers   │  │  LLM Providers  │  │    Agno Agents      │ │   │
│  │  │                 │  │                 │  │                     │ │   │
│  │  │ • defillama_mcp │  │ • vertex_ai     │  │ • base_agent        │ │   │
│  │  │ • 1inch_mcp     │  │ • deepinfra     │  │ • pool              │ │   │
│  │  │ • coingecko_mcp │  │ • bedrock       │  │ • batch             │ │   │
│  │  │ • [11 total]    │  │ • openai        │  │                     │ │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA STORAGE                                        │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      PostgreSQL Tables (4)                             │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    retry_attempts                                │  │ │
│  │  │                                                                   │  │ │
│  │  │  id               | UUID PRIMARY KEY                             │  │ │
│  │  │  service_name     | VARCHAR(255) NOT NULL                        │  │ │
│  │  │  attempt_number   | INTEGER NOT NULL                             │  │ │
│  │  │  request_context  | JSONB                                        │  │ │
│  │  │  error_type       | VARCHAR(100)                                 │  │ │
│  │  │  error_message    | TEXT                                         │  │ │
│  │  │  latency_ms       | INTEGER                                      │  │ │
│  │  │  success          | BOOLEAN                                      │  │ │
│  │  │  created_at       | TIMESTAMP NOT NULL                           │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │                 circuit_breaker_events                           │  │ │
│  │  │                                                                   │  │ │
│  │  │  id               | UUID PRIMARY KEY                             │  │ │
│  │  │  service_name     | VARCHAR(255) NOT NULL                        │  │ │
│  │  │  from_state       | VARCHAR(20) NOT NULL                         │  │ │
│  │  │  to_state         | VARCHAR(20) NOT NULL                         │  │ │
│  │  │  reason           | TEXT                                         │  │ │
│  │  │  failure_count    | INTEGER DEFAULT 0                            │  │ │
│  │  │  success_count    | INTEGER DEFAULT 0                            │  │ │
│  │  │  created_at       | TIMESTAMP NOT NULL                           │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │                service_override_events                           │  │ │
│  │  │                                                                   │  │ │
│  │  │  id               | UUID PRIMARY KEY                             │  │ │
│  │  │  service_name     | VARCHAR(255) NOT NULL                        │  │ │
│  │  │  action           | VARCHAR(20) NOT NULL (disable/enable)        │  │ │
│  │  │  user_id          | UUID NOT NULL                                │  │ │
│  │  │  reason           | TEXT                                         │  │ │
│  │  │  duration_minutes | INTEGER (NULL = permanent)                   │  │ │
│  │  │  created_at       | TIMESTAMP NOT NULL                           │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │                retry_metrics_aggregate                           │  │ │
│  │  │                                                                   │  │ │
│  │  │  id               | UUID PRIMARY KEY                             │  │ │
│  │  │  service_name     | VARCHAR(255) NOT NULL                        │  │ │
│  │  │  date             | DATE NOT NULL                                │  │ │
│  │  │  total_requests   | INTEGER DEFAULT 0                            │  │ │
│  │  │  successful_requests | INTEGER DEFAULT 0                         │  │ │
│  │  │  failed_requests  | INTEGER DEFAULT 0                            │  │ │
│  │  │  retry_attempts   | INTEGER DEFAULT 0                            │  │ │
│  │  │  avg_latency_ms   | FLOAT                                        │  │ │
│  │  │  p50/p95/p99_latency_ms | INTEGER                                │  │ │
│  │  │  circuit_breaker_opens | INTEGER DEFAULT 0                       │  │ │
│  │  │  created_at       | TIMESTAMP NOT NULL                           │  │ │
│  │  │  updated_at       | TIMESTAMP NOT NULL                           │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Configuration Presets

| Preset | Max Retries | Initial Backoff | Max Backoff | Circuit Threshold | Use Case |
|--------|-------------|-----------------|-------------|-------------------|----------|
| MCP Servers | 3 | 2.0s | 10.0s | 5 failures | External API calls |
| Agno Agents | 2 | 1.0s | 5.0s | 3 failures | Agent tool calls |
| Testing | 2 | 0.1s | 0.5s | 2 failures | Unit/integration tests |
| Default | 3 | 2.0s | 10.0s | 5 failures | General purpose |

---

## 5. Improvements Roadmap

### 5.1 High Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Celery Tasks** | Add metric aggregation, cleanup, monitoring tasks | Medium | Observability |
| **E2E Test Coverage** | Add admin API endpoint tests | Medium | Code quality |
| **Dashboard Integration** | Grafana dashboard for retry metrics | Medium | Monitoring |

### 5.2 Medium Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Alerting** | PagerDuty/Slack alerts on open circuits | Medium | Operations |
| **ServiceRegistry Unit Tests** | Complete test coverage | Low | Code quality |
| **Prometheus Metrics** | Export metrics for Prometheus | Low | Monitoring |

### 5.3 Low Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Circuit Breaker Snapshots** | Hourly state snapshots to DB | Low | Analytics |
| **Auto-Reset Stuck Circuits** | Auto-heal stuck HALF_OPEN | Low | Reliability |
| **Rate Limit Detection** | Auto-detect rate limit patterns | Medium | Intelligence |

---

## 6. Security Considerations

### 6.1 Implemented

- ✅ Admin-only API endpoints
- ✅ Reason logging for all overrides
- ✅ User ID tracking for audit
- ✅ Redis key isolation per service

### 6.2 Recommendations

- ⚠️ Add rate limiting on admin endpoints
- ⚠️ Audit logging for sensitive operations
- ⚠️ IP allowlisting for admin access
- ⚠️ Two-factor authentication for critical operations

---

## 7. Error Classification Reference

| Error Type | Pattern | Retryable | Example |
|------------|---------|-----------|---------|
| `rate_limit` | "rate limit", "429" | Yes | API rate limit exceeded |
| `timeout` | "timeout" | Yes | Request timed out |
| `service_unavailable` | "503", "unavailable" | Yes | Service temporarily down |
| `model_overloaded` | "overloaded" | Yes | LLM model at capacity |
| `authentication_error` | "401", "403" | No | Invalid API key |
| `invalid_request` | "400", "invalid" | No | Malformed request |
| `content_policy` | "content", "policy" | No | Content violation |
| `internal_error` | (default) | Yes | Unknown error |

---

## References

- **Endpoints Spec**: `docs/ceo/retry/endpoints.md`
- **Services Spec**: `docs/ceo/retry/services.md`
- **Celery Spec**: `docs/ceo/retry/celery.md`
- **Test Spec**: `docs/ceo/retry/test.md`
- **Database Migration**: `src/app/infrastructure/persistence_sqla/alembic/versions/2025_12_01_1500-add_retry_telemetry_tables.py`
