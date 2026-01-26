# Retry & Resilience Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Good Coverage  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Retry & Resilience system has **good test coverage** (~70%) with comprehensive integration tests for the retry engine and circuit breaker. Some gaps exist for admin endpoints and telemetry persistence.

**Total Test Files**: 3 files  
**Total Tests**: ~30 tests

---

## 1. Existing Tests

### 1.1 Integration Tests

| File | Tests | Coverage |
|------|-------|----------|
| `tests/integration/retry/test_retry_engine.py` | Retry logic, circuit breaker integration, telemetry | 14 tests |
| `tests/integration/retry/test_circuit_breaker.py` | Circuit breaker state machine, manager | 16 tests |

---

### 1.2 RetryEngine Test Coverage

**File**: `tests/integration/retry/test_retry_engine.py`

```python
class TestEnterpriseRetryEngine:
    async def test_successful_execution_no_retry(self)
    async def test_retry_on_failure_then_success(self)
    async def test_all_retries_exhausted(self)
    async def test_non_retryable_error_no_retry(self)
    async def test_circuit_breaker_integration(self)
    async def test_circuit_breaker_success_recorded(self)
    async def test_circuit_breaker_failure_recorded(self)
    async def test_service_registry_disabled_service(self)
    async def test_telemetry_records_success(self)
    async def test_telemetry_records_failure(self)
    async def test_exponential_backoff_applied(self)
    async def test_error_classification(self)
    async def test_full_integration_success_after_failures(self)
```

**Key Test Areas**:
- ✅ Successful execution without retry
- ✅ Retry on transient failure
- ✅ All retries exhausted scenario
- ✅ Non-retryable error classification
- ✅ Circuit breaker blocking
- ✅ Circuit breaker state updates
- ✅ Service registry override
- ✅ Telemetry recording
- ✅ Exponential backoff timing
- ✅ Error type classification
- ✅ Full integration flow

---

### 1.3 CircuitBreaker Test Coverage

**File**: `tests/integration/retry/test_circuit_breaker.py`

```python
class TestCircuitBreaker:
    def test_initial_state_is_closed(self)
    def test_record_success_in_closed_state(self)
    def test_transition_to_open_on_failure_threshold(self)
    def test_circuit_stays_closed_below_threshold(self)
    def test_transition_to_half_open_after_timeout(self)
    def test_success_in_half_open_closes_circuit(self)
    def test_failure_in_half_open_reopens_circuit(self)
    def test_manual_reset(self)
    def test_get_status(self)
    async def test_telemetry_on_state_transitions(self)

class TestCircuitBreakerManager:
    def test_get_or_create_breaker(self)
    def test_is_open_delegates_to_breaker(self)
    def test_record_success_delegates_to_breaker(self)
    def test_record_failure_delegates_to_breaker(self)
    def test_reset_delegates_to_breaker(self)
    def test_get_all_statuses(self)
    def test_count_open_breakers(self)
    def test_multiple_services_independent_state(self)
```

**Key Test Areas**:
- ✅ Initial CLOSED state
- ✅ Success resets failure counter
- ✅ CLOSED → OPEN transition on threshold
- ✅ Below-threshold stays CLOSED
- ✅ OPEN → HALF_OPEN on timeout
- ✅ HALF_OPEN → CLOSED on success threshold
- ✅ HALF_OPEN → OPEN on failure
- ✅ Manual reset functionality
- ✅ Status retrieval
- ✅ Telemetry on state changes
- ✅ Manager delegation
- ✅ Multiple services independent

---

## 2. Missing Tests (Gaps Analysis)

### 2.1 Critical Missing Tests

| Area | Missing Test | Priority | Description |
|------|-------------|----------|-------------|
| **Admin Router** | E2E tests | HIGH | All admin endpoints |
| **ServiceRegistry** | Unit tests | HIGH | Enable/disable logic |
| **RetryConfig** | Unit tests | MEDIUM | Configuration validation |
| **Telemetry Repository** | Integration tests | MEDIUM | Database persistence |
| **Interactors** | Unit tests | MEDIUM | Application layer logic |

---

### 2.2 Missing ServiceRegistry Tests

```python
# tests/unit/domain/services/retry/test_service_registry.py (MISSING)

class TestServiceRegistry:
    def test_is_enabled_default_true(self):
        """Test service is enabled by default."""
        
    def test_is_enabled_with_override_disabled(self):
        """Test service is disabled when override set."""
        
    async def test_disable_service(self):
        """Test disabling a service."""
        
    async def test_disable_service_with_duration(self):
        """Test disabling with auto-expiry."""
        
    async def test_enable_service(self):
        """Test re-enabling a service."""
        
    def test_get_service_status(self):
        """Test getting service status."""
        
    def test_get_service_status_with_ttl(self):
        """Test status includes TTL for auto-expiry."""
        
    def test_get_all_service_statuses(self):
        """Test getting all services with overrides."""
        
    def test_count_disabled(self):
        """Test counting disabled services."""
        
    async def test_telemetry_on_disable(self):
        """Test telemetry recorded on disable."""
        
    async def test_telemetry_on_enable(self):
        """Test telemetry recorded on enable."""
```

---

### 2.3 Missing RetryConfig Tests

```python
# tests/unit/domain/value_objects/test_retry_config.py (MISSING)

class TestRetryConfig:
    def test_default_values(self):
        """Test default configuration values."""
        
    def test_validation_max_retries_non_negative(self):
        """Test max_retries must be non-negative."""
        
    def test_validation_backoff_positive(self):
        """Test initial_backoff_seconds must be positive."""
        
    def test_validation_max_backoff_gte_initial(self):
        """Test max_backoff >= initial_backoff."""
        
    def test_validation_exponential_base_gt_1(self):
        """Test exponential_base must be > 1."""
        
    def test_calculate_delay_exponential(self):
        """Test delay increases exponentially."""
        
    def test_calculate_delay_capped_at_max(self):
        """Test delay is capped at max_backoff."""
        
    def test_calculate_delay_with_jitter(self):
        """Test jitter adds randomness."""
        
    def test_calculate_delay_without_jitter(self):
        """Test deterministic delay without jitter."""
        
    def test_for_mcp_servers_preset(self):
        """Test MCP server preset configuration."""
        
    def test_for_agno_agents_preset(self):
        """Test Agno agent preset configuration."""
        
    def test_for_testing_preset(self):
        """Test testing preset configuration."""
        
    def test_to_dict(self):
        """Test serialization to dictionary."""
        
    def test_from_dict(self):
        """Test deserialization from dictionary."""
```

---

### 2.4 Missing Admin Router E2E Tests

```python
# tests/e2e/admin/retry/test_retry_admin_api.py (MISSING)

class TestRetryAdminAPI:
    async def test_list_services(self, client, admin_token):
        """Test GET /admin/retry/services."""
        
    async def test_get_service_status(self, client, admin_token):
        """Test GET /admin/retry/services/{service_name}."""
        
    async def test_get_service_status_not_found(self, client, admin_token):
        """Test 404 for unknown service."""
        
    async def test_disable_service(self, client, admin_token):
        """Test POST /admin/retry/services/{service_name}/disable."""
        
    async def test_disable_service_with_duration(self, client, admin_token):
        """Test disable with auto-expiry."""
        
    async def test_enable_service(self, client, admin_token):
        """Test POST /admin/retry/services/{service_name}/enable."""
        
    async def test_get_circuit_breakers(self, client, admin_token):
        """Test GET /admin/retry/circuit-breakers."""
        
    async def test_reset_circuit_breaker(self, client, admin_token):
        """Test POST /admin/retry/circuit-breakers/{service_name}/reset."""
        
    async def test_get_service_metrics(self, client, admin_token):
        """Test GET /admin/retry/metrics/{service_name}."""
        
    async def test_get_service_metrics_with_days(self, client, admin_token):
        """Test metrics with custom days parameter."""
        
    async def test_unauthorized_access(self, client):
        """Test endpoints require admin auth."""
```

---

### 2.5 Missing Telemetry Repository Tests

```python
# tests/integration/infrastructure/repositories/test_retry_telemetry_repository.py (MISSING)

class TestRetryTelemetryRepository:
    async def test_create_attempt_success(self):
        """Test creating successful attempt record."""
        
    async def test_create_attempt_failure(self):
        """Test creating failed attempt record."""
        
    async def test_create_circuit_event(self):
        """Test creating circuit breaker event."""
        
    async def test_create_override_event(self):
        """Test creating service override event."""
        
    async def test_increment_success(self):
        """Test incrementing success counter."""
        
    async def test_increment_failure(self):
        """Test incrementing failure counter."""
        
    async def test_increment_circuit_open(self):
        """Test incrementing circuit open counter."""
        
    async def test_get_aggregated_metrics(self):
        """Test retrieving aggregated metrics."""
        
    async def test_get_aggregated_metrics_empty(self):
        """Test metrics for service with no data."""
        
    async def test_get_aggregated_metrics_date_range(self):
        """Test metrics respect date range."""
```

---

### 2.6 Missing Interactor Tests

```python
# tests/unit/application/admin/retry/test_retry_interactors.py (MISSING)

class TestGetServiceList:
    async def test_returns_all_services(self):
        """Test listing all services."""
        
    async def test_combines_registry_and_circuit_status(self):
        """Test combining service registry and circuit breaker status."""

class TestGetServiceStatus:
    async def test_returns_detailed_status(self):
        """Test detailed status includes all fields."""
        
    async def test_service_not_found(self):
        """Test error for unknown service."""

class TestDisableService:
    async def test_disables_service(self):
        """Test service is disabled in registry."""
        
    async def test_records_telemetry(self):
        """Test telemetry is recorded."""

class TestEnableService:
    async def test_enables_service(self):
        """Test service is enabled in registry."""
        
    async def test_records_telemetry(self):
        """Test telemetry is recorded."""

class TestGetCircuitStatus:
    async def test_returns_all_circuit_breakers(self):
        """Test listing all circuit breakers."""

class TestResetCircuitBreaker:
    async def test_resets_circuit(self):
        """Test circuit breaker is reset."""
        
    async def test_records_telemetry(self):
        """Test telemetry is recorded."""

class TestGetServiceMetrics:
    async def test_returns_metrics_with_summary(self):
        """Test metrics include summary statistics."""
        
    async def test_calculates_success_rate(self):
        """Test success rate calculation."""
        
    async def test_handles_empty_metrics(self):
        """Test handling no metrics data."""
```

---

## 3. Test Commands

### Run All Retry Tests

```bash
# All retry tests
pytest tests/integration/retry/ -v

# With coverage
pytest tests/integration/retry/ \
  --cov=src/app/domain/services/retry \
  --cov=src/app/application/admin/retry \
  --cov=src/app/presentation/http/controllers/admin/retry \
  --cov-report=html
```

### Run Specific Test Categories

```bash
# RetryEngine tests
pytest tests/integration/retry/test_retry_engine.py -v

# CircuitBreaker tests
pytest tests/integration/retry/test_circuit_breaker.py -v

# Async tests only
pytest tests/integration/retry/ -m asyncio -v
```

---

## 4. Test Coverage Goals

| Layer | Current | Target | Gap |
|-------|---------|--------|-----|
| RetryEngine | ~80% | 90% | 10% |
| CircuitBreaker | ~85% | 90% | 5% |
| ServiceRegistry | ~20% | 80% | 60% |
| RetryConfig | ~30% | 80% | 50% |
| Admin Router | ~10% | 80% | 70% |
| Telemetry Repository | ~20% | 70% | 50% |
| Interactors | ~30% | 80% | 50% |

---

## 5. Test Fixtures

### 5.1 MockRedis Fixture

```python
@pytest.fixture
def mock_redis():
    """Create mock Redis client for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        def get(self, key):
            value = self.data.get(key)
            return value.encode() if isinstance(value, str) else None
        
        def set(self, key, value):
            self.data[key] = value
        
        def delete(self, key):
            self.data.pop(key, None)
        
        def incr(self, key):
            current = int(self.data.get(key, 0))
            self.data[key] = current + 1
            return self.data[key]
        
        def ttl(self, key):
            return -1
        
        def keys(self, pattern):
            return [k.encode() for k in self.data.keys()]
        
        def expire(self, key, seconds):
            pass
    
    return MockRedis()
```

### 5.2 RetryConfig Fixtures

```python
@pytest.fixture
def testing_config():
    """Create testing-optimized retry config."""
    return RetryConfig.for_testing()

@pytest.fixture
def mcp_config():
    """Create MCP server retry config."""
    return RetryConfig.for_mcp_servers()
```

### 5.3 Mock Service Dependencies

```python
@pytest.fixture
def mock_telemetry():
    """Create mock telemetry collector."""
    return AsyncMock()

@pytest.fixture
def mock_circuit_breaker():
    """Create mock circuit breaker manager."""
    mock = MagicMock()
    mock.is_open.return_value = False
    return mock

@pytest.fixture
def mock_service_registry():
    """Create mock service registry."""
    mock = MagicMock()
    mock.is_enabled.return_value = True
    return mock
```

---

## 6. Test Markers

```python
# pytest.ini or pyproject.toml markers
markers = [
    "retry: Retry system tests",
    "circuit_breaker: Circuit breaker tests",
    "service_registry: Service registry tests",
    "telemetry: Telemetry tests",
    "admin_api: Admin API tests",
    "llm_validation: LLM-based validation tests",
]
```

---

## References

- **Integration Tests**: `tests/integration/retry/`
- **RetryEngine Tests**: `tests/integration/retry/test_retry_engine.py`
- **CircuitBreaker Tests**: `tests/integration/retry/test_circuit_breaker.py`
