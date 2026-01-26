# AI Telemetry System Metadata & Architecture

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Anvil AI Telemetry System provides comprehensive observability for LLM operations, API calls, database queries, and distributed tracing.

**Supported Metrics**: LLM (tokens, costs, latency), API (requests, errors), DB (queries, pool)  
**Export Formats**: JSON, Prometheus  
**Storage**: In-memory with optional persistence to PostgreSQL/Redis

---

## 1. Module Status

| Component | Status | Health | Notes |
|-----------|--------|--------|-------|
| LLM Telemetry | ✅ Production | Healthy | Full feature set |
| API Telemetry | ✅ Production | Healthy | External API tracking |
| Database Telemetry | ✅ Production | Healthy | Query tracking |
| Tracing Service | ✅ Production | Healthy | Distributed tracing |
| Feature Flags | ✅ Production | Healthy | Runtime configuration |
| Metrics Exporter | ✅ Production | Healthy | Prometheus export |
| Telemetry Router | ✅ Production | Healthy | 30+ endpoints |
| Monitoring Router | ✅ Production | Healthy | Health checks |
| Celery Tasks | ⚠️ Partial | Limited | Only distillation task |
| Test Coverage | ⚠️ Partial | ~20% | Significant gaps |

---

## 2. File Reference Index

### 2.1 Telemetry Services

```
src/app/infrastructure/telemetry/
├── __init__.py
├── llm_telemetry.py          # LLMTelemetry - token/cost/latency tracking
├── api_telemetry.py          # APITelemetry - external API call tracking
├── db_telemetry.py           # DatabaseTelemetry - query tracking
├── tracing.py                # TracingService - distributed tracing
├── metrics_exporter.py       # MetricsExporter - Prometheus export
├── feature_flags.py          # TelemetryFeatureFlags - runtime config
├── alert_destinations.py     # Alert delivery
└── instrumented_client.py    # Base instrumented client class
```

### 2.2 Monitoring Services

```
src/app/infrastructure/monitoring/
├── __init__.py
├── metrics.py                # System metrics
├── metrics_collector.py      # ChatMetricsCollector - chat metrics
├── health_checks.py          # HealthCheckService
├── alerting.py               # AlertingService
├── middleware.py             # TelemetryMiddleware
├── background_tasks.py       # Background monitoring tasks
├── cloudwatch_metrics.py     # AWS CloudWatch integration
└── sentry_config.py          # Sentry configuration
```

### 2.3 Instrumented Clients

```
src/app/infrastructure/adapters/external/instrumented/
├── __init__.py
├── instrumented_coingecko_client.py
├── instrumented_defillama_client.py
├── instrumented_oneinch_client.py
├── instrumented_uniswap_client.py
├── instrumented_aave_client.py
├── instrumented_curve_client.py
├── instrumented_hyperliquid_client.py
├── instrumented_thegraph_client.py
└── instrumented_gas_oracle_client.py
```

### 2.4 Presentation Layer

```
src/app/presentation/http/controllers/telemetry/
├── __init__.py
└── router.py                 # 30+ telemetry endpoints

src/app/presentation/http/controllers/monitoring/
├── __init__.py
└── router.py                 # Health check endpoints
```

### 2.5 Database Mappings

```
src/app/infrastructure/persistence_sqla/mappings/
├── ai_telemetry.py           # 13+ AI telemetry tables
├── retry_telemetry.py        # Retry telemetry tables
├── distillation_telemetry.py # Distillation telemetry tables
├── llm_orchestration.py      # LLM orchestration tables
├── conversation_analytics.py # Conversation analytics tables
└── analytics_snapshot.py     # Analytics snapshot tables
```

### 2.6 Celery Tasks

```
src/app/infrastructure/celery/
├── tasks.py                  # Main tasks file
└── tasks/
    ├── distillation_tasks.py # aggregate_distillation_telemetry
    └── llm_ranking.py        # Uses telemetry data
```

### 2.7 Repositories

```
src/app/infrastructure/persistence_sqla/repositories/
├── retry_telemetry_repository.py
├── distillation_telemetry_repository.py
└── llm/
    └── ranking_repository.py # Uses telemetry data
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                                                                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐     │
│  │ Admin UI  │ │Prometheus │ │ Grafana   │ │ Sentry    │ │CloudWatch │     │
│  │(Dashboard)│ │(Scraping) │ │(Visualize)│ │ (Errors)  │ │ (Metrics) │     │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘     │
└────────┼─────────────┼─────────────┼─────────────┼─────────────┼────────────┘
         │             │             │             │             │
         ▼             ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    Telemetry Router                                  │    │
│  │  /flags • /metrics • /prometheus • /traces • /llm/* • /db/*        │    │
│  │  /slow-calls • /errors • /health • /reset                          │    │
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
│                      TELEMETRY SERVICES LAYER                                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Core Telemetry Services                        │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │  │
│  │  │   LLMTelemetry  │  │  APITelemetry   │  │ DatabaseTelemetry│       │  │
│  │  │                 │  │                 │  │                  │       │  │
│  │  │ • Tokens        │  │ • Requests      │  │ • Queries        │       │  │
│  │  │ • Costs         │  │ • Latency       │  │ • Slow queries   │       │  │
│  │  │ • Latency       │  │ • Errors        │  │ • Pool stats     │       │  │
│  │  │ • Alerts        │  │ • Rate limits   │  │ • Patterns       │       │  │
│  │  │ • Budget        │  │ • Cache hits    │  │                  │       │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │  │
│  │  │ TracingService  │  │ MetricsExporter │  │  FeatureFlags   │       │  │
│  │  │                 │  │                 │  │                  │       │  │
│  │  │ • Traces        │  │ • Prometheus    │  │ • Enable/disable│       │  │
│  │  │ • Spans         │  │ • JSON          │  │ • Sampling rates│       │  │
│  │  │ • Attributes    │  │ • OpenMetrics   │  │ • Per-API config│       │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MONITORING SERVICES LAYER                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ChatMetricsCollector • HealthCheckService • AlertingService         │  │
│  │  TelemetryMiddleware • BackgroundTasks • SentryConfig                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INSTRUMENTED CLIENTS LAYER                              │
│                                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  CoinGecko  │ │ DeFiLlama   │ │   1inch     │ │   Aave      │          │
│  │ Instrumented│ │ Instrumented│ │ Instrumented│ │ Instrumented│          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Curve     │ │ Hyperliquid │ │  The Graph  │ │  Gas Oracle │          │
│  │ Instrumented│ │ Instrumented│ │ Instrumented│ │ Instrumented│          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA STORAGE LAYER                                   │
│                                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐   │
│  │     PostgreSQL       │  │       Redis          │  │   In-Memory     │   │
│  │                      │  │                      │  │                 │   │
│  │  AI Telemetry Tables │  │  Feature Flags       │  │  LLMTelemetry   │   │
│  │  • models            │  │  Session Data        │  │  APITelemetry   │   │
│  │  • llm_conversations │  │  Cache               │  │  DBTelemetry    │   │
│  │  • agent_executions  │  │                      │  │  Traces         │   │
│  │  • agent_tasks       │  │                      │  │                 │   │
│  │  • vertex_api_metrics│  │                      │  │                 │   │
│  │  • deepinfra_metrics │  │                      │  │                 │   │
│  │  • bedrock_metrics   │  │                      │  │                 │   │
│  │  • llm_rate_limits   │  │                      │  │                 │   │
│  │  • llm_cost_alerts   │  │                      │  │                 │   │
│  └──────────────────────┘  └──────────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### 4.1 AI Telemetry Tables

```sql
-- Models (LLM model registry)
CREATE TABLE models (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(20) NOT NULL,  -- LLMProvider enum
    model_name VARCHAR(100) NOT NULL,
    label VARCHAR(255) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    cost_per_1k_input_tokens NUMERIC(10, 8) NOT NULL,
    cost_per_1k_output_tokens NUMERIC(10, 8) NOT NULL,
    max_tokens INTEGER,
    status VARCHAR(20) DEFAULT 'active',  -- ModelStatus enum
    request_count BIGINT DEFAULT 0,
    total_cost_usd NUMERIC(12, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, model_name)
);

-- LLM Conversations
CREATE TABLE llm_conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,
    model_id BIGINT REFERENCES models(id),
    provider VARCHAR(20) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prompt_text TEXT NOT NULL,
    response_text TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd NUMERIC(10, 6),
    latency_ms INTEGER,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent Executions
CREATE TABLE agent_executions (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    conversation_id BIGINT REFERENCES llm_conversations(id),
    agent_type VARCHAR(50) NOT NULL,
    workflow_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- AgentExecutionStatus
    input_params JSON,
    output_result JSON,
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(10, 6) DEFAULT 0,
    execution_time_ms INTEGER,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent Performance Stats
CREATE TABLE agent_performance_stats (
    id BIGSERIAL PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,
    time_window VARCHAR(20) NOT NULL,  -- "1h", "24h", "all_time"
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    canceled_requests INTEGER DEFAULT 0,
    avg_latency_ms INTEGER DEFAULT 0,
    avg_cost_usd NUMERIC(10, 6) DEFAULT 0,
    total_cost_usd NUMERIC(12, 2) DEFAULT 0,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_type, time_window)
);

-- Vertex AI API Metrics
CREATE TABLE vertex_api_metrics (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT REFERENCES models(id) ON DELETE CASCADE,
    region VARCHAR(50) NOT NULL,
    requests_count INTEGER DEFAULT 0,
    tokens_consumed BIGINT DEFAULT 0,
    cost_usd NUMERIC(10, 6) DEFAULT 0,
    quota_exceeded_count INTEGER DEFAULT 0,
    rate_limit_count INTEGER DEFAULT 0,
    avg_latency_ms INTEGER,
    p95_latency_ms INTEGER,
    p99_latency_ms INTEGER,
    error_count INTEGER DEFAULT 0,
    success_rate NUMERIC(5, 2),
    failover_to_bedrock_count INTEGER DEFAULT 0,
    time_window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, region, time_window_start)
);

-- LLM Rate Limit Events
CREATE TABLE llm_rate_limit_events (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(20) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(20) NOT NULL,  -- RateLimitEventType
    user_id INTEGER REFERENCES users(id),
    error_code VARCHAR(50),
    error_message TEXT,
    retry_after_seconds INTEGER,
    fallback_used BOOLEAN DEFAULT FALSE,
    fallback_provider VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- LLM Cost Alerts
CREATE TABLE llm_cost_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_type VARCHAR(20) NOT NULL,  -- CostAlertType
    threshold_usd NUMERIC(10, 2) NOT NULL,
    actual_cost_usd NUMERIC(10, 2) NOT NULL,
    time_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    provider VARCHAR(20),
    alert_sent BOOLEAN DEFAULT FALSE,
    alert_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Improvements Roadmap

### 5.1 High Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Telemetry Persistence** | Background tasks for DB storage | Medium | Data durability |
| **Budget Alert Tasks** | Celery tasks for budget monitoring | Low | Cost control |
| **Unit Tests** | LLMTelemetry, APITelemetry tests | Medium | Code quality |
| **E2E Tests** | Telemetry endpoint tests | Medium | Quality |

### 5.2 Medium Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Dashboard UI** | Admin telemetry dashboard | High | UX |
| **Alert Notifications** | Email/Slack for alerts | Medium | Ops |
| **Retention Policies** | Automatic data cleanup | Low | Storage |
| **Historical Comparison** | Compare metrics over time | High | Analytics |

### 5.3 Low Priority

| Improvement | Description | Effort | Impact |
|-------------|-------------|--------|--------|
| **Custom Dashboards** | User-defined dashboards | High | Feature |
| **Export Formats** | CSV/Excel export | Medium | Feature |
| **Real-time WebSocket** | Live metrics streaming | High | UX |

---

## 6. Performance Metrics

### 6.1 LLM Telemetry Metrics

| Metric | Sample Value | Target |
|--------|--------------|--------|
| Tokens tracked/day | 15M+ | No limit |
| Cost tracked/day | $100+ | No limit |
| Latency percentiles | p50: 1100ms, p99: 3000ms | Tracked |
| Alert latency | <1 minute | <5 minutes |

### 6.2 API Telemetry Metrics

| Metric | Sample Value | Target |
|--------|--------------|--------|
| APIs tracked | 9 | - |
| Requests/day | 100K+ | No limit |
| Error rate tracking | <5% | Tracked |

### 6.3 System Overhead

| Component | Memory Usage | CPU Impact |
|-----------|--------------|------------|
| LLM Telemetry | ~50MB | <1% |
| API Telemetry | ~20MB | <0.5% |
| DB Telemetry | ~10MB | <0.5% |
| Tracing | ~30MB | <0.5% |

---

## 7. Security Considerations

### 7.1 Implemented

- ✅ Admin-only write endpoints
- ✅ No PII in telemetry data
- ✅ Sampling to reduce data volume
- ✅ Feature flags for runtime control

### 7.2 Recommendations

- ⚠️ Add audit logging for flag changes
- ⚠️ Implement data retention policies
- ⚠️ Review sensitive data in traces
- ⚠️ Add access control for cost data

---

## References

- **Endpoints Spec**: `docs/ceo/telemetry/endpoints.md`
- **Services Spec**: `docs/ceo/telemetry/services.md`
- **Celery Spec**: `docs/ceo/telemetry/celery.md`
- **Test Spec**: `docs/ceo/telemetry/test.md`
- **Prometheus Docs**: https://prometheus.io/docs/
- **OpenTelemetry Docs**: https://opentelemetry.io/docs/
