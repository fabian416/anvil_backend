# AI Telemetry System Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Limited Coverage  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The AI Telemetry System has **limited dedicated test coverage**. Most telemetry functionality is tested indirectly through integration tests for other systems. Significant test gaps exist for telemetry endpoints, services, and Celery tasks.

**Total Test Files**: ~5 files with telemetry-related tests  
**Coverage**: ~20% (estimated)

---

## 1. Existing Tests

### 1.1 Unit Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/unit/application/test_llm_dashboard_query.py` | Dashboard query | GetDashboardData |
| `tests/unit/domain/entities/chat/test_performance_metrics.py` | Performance metrics | Metric entities |
| `tests/unit/presentation/admin/test_llm_management_controllers.py` | LLM admin controllers | Endpoints |

---

### 1.2 Integration Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/integration/retry/test_circuit_breaker.py` | Circuit breaker | State transitions |
| `tests/integration/retry/test_retry_engine.py` | Retry engine | Retry logic |
| `tests/integration/celery/test_celery_tasks.py` | Celery tasks | Task execution |
| `tests/integration/distillation/test_request_distillator.py` | Distillation | Telemetry recording |

---

### 1.3 Indirect Telemetry Tests

Some tests indirectly verify telemetry functionality:

| File | Relevance |
|------|-----------|
| `tests/integration/agno/test_agent_retry.py` | Tests retry telemetry |
| `tests/integration/hunter/test_risk_analysis.py` | Tests metrics collection |
| `tests/integration/ultra/test_auto_executor_risk.py` | Tests monitoring |

---

## 2. Missing Tests (Gaps Analysis)

### 2.1 Critical Missing Tests

| Area | Missing Test | Priority | Description |
|------|-------------|----------|-------------|
| **LLM Telemetry** | Unit tests | HIGH | Core telemetry logic |
| **API Telemetry** | Unit tests | HIGH | API tracking |
| **DB Telemetry** | Unit tests | HIGH | Query tracking |
| **Telemetry Router** | E2E tests | HIGH | All endpoints |
| **Feature Flags** | Unit tests | MEDIUM | Flag management |
| **Metrics Exporter** | Unit tests | MEDIUM | Prometheus export |

---

### 2.2 Missing LLM Telemetry Tests

```python
# tests/unit/infrastructure/telemetry/test_llm_telemetry.py (MISSING)

class TestLLMTelemetry:
    def test_start_call_creates_context(self):
        """Test start_call creates proper context."""
        
    async def test_record_updates_metrics(self):
        """Test record updates provider metrics."""
        
    def test_cost_calculation(self):
        """Test cost estimation for different models."""
        
    def test_latency_percentiles(self):
        """Test p50, p90, p99 calculations."""
        
    def test_budget_tracking(self):
        """Test monthly budget tracking."""
        
    def test_budget_alert_on_threshold(self):
        """Test alert when budget threshold reached."""
        
    def test_error_rate_alert(self):
        """Test alert when error rate exceeds threshold."""
        
    def test_rate_limit_detection(self):
        """Test rate limit event detection."""
        
    def test_retention_cleanup(self):
        """Test old record cleanup."""
        
    def test_model_usage_aggregation(self):
        """Test model usage aggregation."""
        
    def test_provider_metrics_to_dict(self):
        """Test metrics serialization."""


class TestLLMTelemetryConfig:
    def test_default_config(self):
        """Test default configuration values."""
        
    def test_custom_model_costs(self):
        """Test custom model cost configuration."""
        
    def test_budget_alert_threshold(self):
        """Test budget alert threshold configuration."""
```

---

### 2.3 Missing API Telemetry Tests

```python
# tests/unit/infrastructure/telemetry/test_api_telemetry.py (MISSING)

class TestAPITelemetry:
    def test_record_call_success(self):
        """Test recording successful API call."""
        
    def test_record_call_error(self):
        """Test recording failed API call."""
        
    def test_record_call_cached(self):
        """Test recording cached response."""
        
    def test_latency_histogram(self):
        """Test latency histogram recording."""
        
    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        
    def test_get_slow_calls(self):
        """Test slow call retrieval."""
        
    def test_get_errors_filtered(self):
        """Test error retrieval with filter."""
```

---

### 2.4 Missing Database Telemetry Tests

```python
# tests/unit/infrastructure/telemetry/test_db_telemetry.py (MISSING)

class TestDatabaseTelemetry:
    def test_record_query_select(self):
        """Test recording SELECT query."""
        
    def test_record_query_insert(self):
        """Test recording INSERT query."""
        
    def test_slow_query_detection(self):
        """Test slow query threshold detection."""
        
    def test_query_pattern_normalization(self):
        """Test query pattern normalization."""
        
    def test_pool_stats(self):
        """Test connection pool statistics."""
        
    def test_table_metrics(self):
        """Test per-table metrics."""
```

---

### 2.5 Missing Feature Flags Tests

```python
# tests/unit/infrastructure/telemetry/test_feature_flags.py (MISSING)

class TestTelemetryFeatureFlags:
    def test_default_flags(self):
        """Test default feature flag values."""
        
    def test_global_disable(self):
        """Test global telemetry disable."""
        
    def test_api_disable_specific(self):
        """Test disabling specific API telemetry."""
        
    def test_llm_provider_disable(self):
        """Test disabling specific LLM provider."""
        
    def test_sampling_rate(self):
        """Test sampling rate application."""
        
    async def test_save_to_redis(self):
        """Test saving flags to Redis."""
        
    async def test_load_from_redis(self):
        """Test loading flags from Redis."""
        
    async def test_delete_from_redis(self):
        """Test deleting flags from Redis."""
```

---

### 2.6 Missing Telemetry Router E2E Tests

```python
# tests/e2e/telemetry/test_telemetry_api.py (MISSING)

class TestTelemetryAPI:
    async def test_get_flags(self, client):
        """Test GET /telemetry/flags."""
        
    async def test_update_flags_admin_only(self, client):
        """Test PUT /telemetry/flags requires auth."""
        
    async def test_get_api_metrics(self, client):
        """Test GET /telemetry/metrics."""
        
    async def test_get_prometheus_metrics(self, client):
        """Test GET /telemetry/prometheus."""
        
    async def test_get_traces(self, client):
        """Test GET /telemetry/traces."""
        
    async def test_get_trace_detail(self, client):
        """Test GET /telemetry/traces/{trace_id}."""
        
    async def test_get_llm_metrics(self, client):
        """Test GET /telemetry/llm/metrics."""
        
    async def test_get_llm_costs(self, client):
        """Test GET /telemetry/llm/costs."""
        
    async def test_get_llm_alerts(self, client):
        """Test GET /telemetry/llm/alerts."""
        
    async def test_get_db_metrics(self, client):
        """Test GET /telemetry/db/metrics."""
        
    async def test_get_db_slow_queries(self, client):
        """Test GET /telemetry/db/slow-queries."""
        
    async def test_reset_telemetry_admin_only(self, client):
        """Test POST /telemetry/reset requires auth."""
```

---

### 2.7 Missing Metrics Collector Tests

```python
# tests/unit/infrastructure/monitoring/test_metrics_collector.py (MISSING)

class TestChatMetricsCollector:
    def test_increment_request_count(self):
        """Test request count increment."""
        
    def test_record_response_time(self):
        """Test response time histogram recording."""
        
    def test_record_cost(self):
        """Test cost recording."""
        
    def test_cache_hit_rate(self):
        """Test cache hit rate calculation."""
        
    def test_error_rate(self):
        """Test error rate calculation."""
        
    def test_agent_metrics(self):
        """Test per-agent metrics."""
        
    def test_export_prometheus(self):
        """Test Prometheus format export."""
```

---

### 2.8 Missing Celery Task Tests

```python
# tests/integration/celery/test_telemetry_tasks.py (MISSING)

class TestTelemetryTasks:
    def test_aggregate_distillation_telemetry(self):
        """Test distillation telemetry aggregation task."""
        
    # Future tasks (when implemented)
    def test_aggregate_llm_telemetry_hourly(self):
        """Test LLM telemetry aggregation task."""
        
    def test_aggregate_api_telemetry_hourly(self):
        """Test API telemetry aggregation task."""
        
    def test_check_llm_budget_alerts(self):
        """Test budget alert checking task."""
        
    def test_clean_old_telemetry(self):
        """Test telemetry cleanup task."""
```

---

## 3. Test Commands

### Run All Telemetry-Related Tests

```bash
# All telemetry tests
pytest -k "telemetry or metrics or monitoring or tracing" -v

# Unit tests only
pytest tests/unit -k "telemetry or metrics" -v

# Integration tests
pytest tests/integration -k "telemetry or retry or circuit" -v

# E2E tests (when created)
pytest tests/e2e/telemetry/ -v
```

### Run with Coverage

```bash
pytest tests/ \
  -k "telemetry or metrics or monitoring" \
  --cov=src/app/infrastructure/telemetry \
  --cov=src/app/infrastructure/monitoring \
  --cov=src/app/presentation/http/controllers/telemetry \
  --cov-report=html
```

---

## 4. Test Coverage Goals

| Layer | Current | Target | Gap |
|-------|---------|--------|-----|
| LLM Telemetry | ~10% | 80% | 70% |
| API Telemetry | ~5% | 70% | 65% |
| DB Telemetry | ~5% | 70% | 65% |
| Feature Flags | ~0% | 80% | 80% |
| Metrics Exporter | ~0% | 60% | 60% |
| Telemetry Router | ~10% | 70% | 60% |
| Metrics Collector | ~5% | 70% | 65% |
| Celery Tasks | ~10% | 60% | 50% |

---

## 5. Test Fixtures

### 5.1 Mock LLM Telemetry
```python
@pytest.fixture
def mock_llm_telemetry():
    """Mock LLM telemetry service."""
    from app.infrastructure.telemetry.llm_telemetry import LLMTelemetry, LLMTelemetryConfig
    
    config = LLMTelemetryConfig(
        enabled=True,
        monthly_budget_usd=1000.0,
        budget_alert_threshold=0.8,
    )
    return LLMTelemetry(config)
```

### 5.2 Mock API Telemetry
```python
@pytest.fixture
def mock_api_telemetry():
    """Mock API telemetry service."""
    from app.infrastructure.telemetry.api_telemetry import APITelemetry
    return APITelemetry()
```

### 5.3 Mock Feature Flags
```python
@pytest.fixture
def mock_feature_flags():
    """Mock telemetry feature flags."""
    from app.infrastructure.telemetry.feature_flags import TelemetryFeatureFlags
    return TelemetryFeatureFlags(
        global_enabled=True,
        api_telemetry_enabled=True,
        llm_telemetry_enabled=True,
    )
```

### 5.4 Sample LLM Call Context
```python
@pytest.fixture
def sample_llm_call():
    """Sample LLM call context."""
    from app.infrastructure.telemetry.llm_telemetry import LLMCallContext, LLMCallStatus
    
    ctx = LLMCallContext(
        call_id="test-123",
        provider="vertex_ai",
        model="gemini-1.5-pro",
        operation="generate",
        start_time=time.time() - 1.5,
    )
    ctx.complete(
        status=LLMCallStatus.SUCCESS,
        input_tokens=500,
        output_tokens=200,
        cost_usd=0.003,
    )
    return ctx
```

---

## 6. Test Markers

```python
# pytest.ini or pyproject.toml markers
markers = [
    "telemetry: Telemetry tests",
    "llm_telemetry: LLM telemetry tests",
    "api_telemetry: API telemetry tests",
    "db_telemetry: Database telemetry tests",
    "metrics: Metrics collection tests",
    "tracing: Distributed tracing tests",
    "monitoring: Monitoring tests",
    "feature_flags: Feature flag tests",
]
```

---

## References

- **Unit Tests**: `tests/unit/`
- **Integration Tests**: `tests/integration/`
- **E2E Tests**: `tests/e2e/`
- **Test Fixtures**: `tests/fixtures/`
- **Telemetry Services**: `src/app/infrastructure/telemetry/`
