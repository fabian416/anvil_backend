# Retry & Resilience Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Retry & Resilience system provides enterprise-grade fault tolerance:
- **EnterpriseRetryEngine** - Intelligent retry logic with exponential backoff
- **CircuitBreaker** - Cascade failure prevention with Redis-backed state
- **ServiceRegistry** - Manual service override for maintenance/outages
- **RetryTelemetryCollector** - Comprehensive metrics and event tracking

**Total Service Components**: 20+ Python modules

---

## 1. Core Domain Services

### 1.1 EnterpriseRetryEngine
**Path**: `src/app/domain/services/retry/retry_engine.py`

Intelligent retry logic with circuit breaker integration and telemetry.

```python
class EnterpriseRetryEngine:
    """
    Enterprise retry engine with circuit breaker and telemetry.
    
    Features:
    - Exponential backoff with jitter
    - Circuit breaker integration
    - Comprehensive telemetry
    - Manual service override
    - Service health tracking
    
    Flow:
    1. Check manual override (service disabled?)
    2. Check circuit breaker (too many failures?)
    3. Execute with retry
    4. Record telemetry
    5. Update circuit breaker state
    """
    
    def __init__(
        self,
        config: RetryConfig,
        circuit_breaker: Optional[CircuitBreakerManager] = None,
        telemetry: Optional[RetryTelemetryCollector] = None,
        service_registry: Optional[ServiceRegistry] = None,
    ): ...
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff delay with exponential growth and jitter."""
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if error should trigger retry."""
    
    def classify_error(self, error: Exception) -> str:
        """Classify error type (rate_limit, timeout, auth_error, etc.)."""
    
    async def execute_with_retry(
        self,
        service_name: str,
        func: Callable,
        context: Optional[Dict] = None,
    ) -> Any:
        """Execute function with retry, circuit breaker, and telemetry."""
    
    def create_retry_decorator(self, service_name: str) -> Callable:
        """Create tenacity-based retry decorator for a service."""
```

**Error Classification**:
| Error Type | Pattern | Retryable |
|------------|---------|-----------|
| `rate_limit` | "rate limit", "429" | Yes |
| `timeout` | "timeout" | Yes |
| `service_unavailable` | "503", "unavailable" | Yes |
| `model_overloaded` | "overloaded" | Yes |
| `authentication_error` | "authentication", "401", "403" | No |
| `invalid_request` | "invalid", "400" | No |
| `content_policy` | "content", "policy" | No |
| `internal_error` | (default) | Yes |

---

### 1.2 CircuitBreaker
**Path**: `src/app/domain/services/retry/circuit_breaker.py`

Redis-backed circuit breaker for cascade failure prevention.

```python
class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5    # Failures before opening
    success_threshold: int = 2    # Successes in half-open to close
    timeout_seconds: int = 60     # Time before trying half-open
    half_open_max_calls: int = 3  # Max calls in half-open state

class CircuitBreaker:
    """
    Circuit breaker with Redis-backed state.
    
    Pattern: CLOSED → OPEN → HALF_OPEN → CLOSED
    
    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Failures exceeded threshold, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(
        self,
        redis_client: Any,
        config: Optional[CircuitBreakerConfig] = None,
        telemetry: Optional[RetryTelemetryCollector] = None,
    ): ...
    
    def is_open(self, service_name: str) -> bool:
        """Check if circuit is open (auto-transitions to half-open after timeout)."""
    
    def is_half_open(self, service_name: str) -> bool:
        """Check if circuit is in testing recovery state."""
    
    def record_success(self, service_name: str) -> None:
        """Record successful call (resets failure counter or closes circuit)."""
    
    def record_failure(self, service_name: str) -> None:
        """Record failed call (may open circuit if threshold exceeded)."""
    
    def reset(self, service_name: str) -> None:
        """Manually reset circuit breaker to closed state."""
    
    def get_status(self, service_name: str) -> Dict[str, Any]:
        """Get detailed circuit breaker status."""
```

**State Machine**:
```
                    ┌─────────────────────┐
                    │       CLOSED        │
                    │  (Normal operation) │
                    └──────────┬──────────┘
                               │
                    failure_threshold exceeded
                               │
                               ▼
                    ┌─────────────────────┐
                    │        OPEN         │
                    │  (Blocking requests)│
                    └──────────┬──────────┘
                               │
                    timeout_seconds passed
                               │
                               ▼
                    ┌─────────────────────┐
                    │     HALF_OPEN       │
                    │  (Testing recovery) │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┴───────────────────┐
           │                                       │
    success_threshold met                   any failure
           │                                       │
           ▼                                       ▼
    ┌─────────────────────┐             ┌─────────────────────┐
    │       CLOSED        │             │        OPEN         │
    └─────────────────────┘             └─────────────────────┘
```

---

### 1.3 CircuitBreakerManager
**Path**: `src/app/domain/services/retry/circuit_breaker.py`

Centralized management of all circuit breakers.

```python
class CircuitBreakerManager:
    """
    Manages circuit breakers for all services.
    Provides centralized access to circuit breaker state.
    """
    
    def get_or_create(self, service_name: str) -> CircuitBreaker
    def is_open(self, service_name: str) -> bool
    def record_success(self, service_name: str) -> None
    def record_failure(self, service_name: str) -> None
    def reset(self, service_name: str) -> None
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]
    def count_open(self) -> int
    def count_total(self) -> int
```

---

### 1.4 ServiceRegistry
**Path**: `src/app/domain/services/retry/service_registry.py`

Manual service override for maintenance and outages.

```python
class ServiceRegistry:
    """
    Registry for service availability and manual overrides.
    
    Allows operators to:
    - Manually disable services (during outages)
    - Re-enable services (after recovery)
    - Set maintenance windows
    - View service health
    """
    
    def __init__(
        self,
        redis_client: Any,
        telemetry: Optional[RetryTelemetryCollector] = None,
    ): ...
    
    def is_enabled(self, service_name: str) -> bool:
        """Check if service is enabled (not manually disabled)."""
    
    async def disable_service(
        self,
        service_name: str,
        user_id: UUID,
        reason: str,
        duration_minutes: Optional[int] = None,
    ) -> None:
        """Manually disable service with optional auto-expiry."""
    
    async def enable_service(
        self,
        service_name: str,
        user_id: UUID,
        reason: str,
    ) -> None:
        """Manually re-enable service."""
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get service override status with metadata."""
    
    def get_all_service_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get all services with overrides."""
    
    def count_disabled(self) -> int:
        """Count disabled services."""
```

---

### 1.5 RetryTelemetryCollector
**Path**: `src/app/domain/services/retry/telemetry_collector.py`

Comprehensive telemetry tracking for retry system.

```python
class RetryEventType(Enum):
    """Types of retry events."""
    ATTEMPT_START = "attempt_start"
    ATTEMPT_SUCCESS = "attempt_success"
    ATTEMPT_FAILURE = "attempt_failure"
    CIRCUIT_STATE_CHANGE = "circuit_state_change"
    SERVICE_OVERRIDE = "service_override"

class RetryTelemetryCollector:
    """
    Telemetry collector for retry system.
    
    Tracks:
    - Retry attempts and outcomes
    - Circuit breaker state changes
    - Service overrides
    - Performance metrics
    """
    
    def __init__(self, repository: Optional[RetryTelemetryRepository] = None): ...
    
    async def record_attempt_start(
        self, service_name: str, attempt_number: int, context: Optional[Dict] = None
    ) -> None
    
    async def record_success(
        self, service_name: str, attempt_number: int, latency_ms: int, context: Optional[Dict] = None
    ) -> None
    
    async def record_failure(
        self, service_name: str, attempt_number: int, error_type: str, error_message: str, context: Optional[Dict] = None
    ) -> None
    
    async def record_circuit_state_change(
        self, service_name: str, from_state: str, to_state: str, reason: str, failure_count: int = 0, success_count: int = 0
    ) -> None
    
    async def record_service_override(
        self, service_name: str, action: str, user_id: UUID, reason: str, duration_minutes: Optional[int] = None
    ) -> None
    
    async def get_service_metrics(self, service_name: str, days: int = 7) -> Dict[str, Any]
```

---

## 2. Value Objects

### 2.1 RetryConfig
**Path**: `src/app/domain/value_objects/retry_config.py`

Configuration for retry behavior.

```python
@dataclass(frozen=True)
class RetryConfig:
    """Enterprise retry configuration."""
    
    # Retry behavior
    max_retries: int = 3
    initial_backoff_seconds: float = 2.0
    max_backoff_seconds: float = 10.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    # Circuit breaker
    circuit_breaker_enabled: bool = True
    circuit_failure_threshold: int = 5
    circuit_success_threshold: int = 2
    circuit_timeout_seconds: int = 60
    
    # Telemetry
    telemetry_enabled: bool = True
    
    # Manual override
    allow_manual_override: bool = True
    
    def calculate_delay(self, attempt: int) -> int:
        """Calculate delay in milliseconds with exponential backoff."""
    
    @classmethod
    def for_mcp_servers(cls) -> "RetryConfig":
        """Optimized for MCP external API calls."""
    
    @classmethod
    def for_agno_agents(cls) -> "RetryConfig":
        """Optimized for Agno agent tool calls."""
    
    @classmethod
    def for_testing(cls) -> "RetryConfig":
        """Fast retries for test speed."""
```

**Backoff Calculation Example**:
```python
config = RetryConfig(initial_backoff_seconds=2, exponential_base=2)
# attempt 0: 2s * 2^0 = 2s
# attempt 1: 2s * 2^1 = 4s
# attempt 2: 2s * 2^2 = 8s
# attempt 3: min(2s * 2^3, max_backoff) = 10s (capped)
```

---

## 3. Application Layer Interactors

**Path**: `src/app/application/admin/retry/`

### 3.1 GetServiceList
```python
class GetServiceList:
    """List all services with retry status."""
    async def execute(self) -> List[Dict[str, Any]]
```

### 3.2 GetServiceStatus
```python
class GetServiceStatus:
    """Get detailed status for a specific service."""
    async def execute(self, service_name: str) -> Dict[str, Any]
```

### 3.3 DisableService
```python
class DisableService:
    """Manually disable a service."""
    async def execute(self, service_name: str, reason: str, duration_minutes: Optional[int]) -> None
```

### 3.4 EnableService
```python
class EnableService:
    """Manually enable a service."""
    async def execute(self, service_name: str, reason: str) -> None
```

### 3.5 GetCircuitStatus
```python
class GetCircuitStatus:
    """Get circuit breaker status for all services."""
    async def execute(self) -> List[Dict[str, Any]]
```

### 3.6 ResetCircuitBreaker
```python
class ResetCircuitBreaker:
    """Manually reset a circuit breaker."""
    async def execute(self, service_name: str, reason: str) -> None
```

### 3.7 GetServiceMetrics
```python
class GetServiceMetrics:
    """Get aggregated metrics for a service."""
    async def execute(self, service_name: str, days: int = 7) -> Dict[str, Any]
```

---

## 4. Infrastructure Adapters

### 4.1 RetryTelemetryRepository
**Path**: `src/app/infrastructure/persistence_sqla/repositories/retry_telemetry_repository.py`

SQLAlchemy repository for persisting retry telemetry data.

```python
class RetryTelemetryRepository:
    """Repository for retry telemetry data."""
    
    async def create_attempt(
        self, service_name: str, attempt_number: int, **kwargs
    ) -> None
    
    async def create_circuit_event(
        self, service_name: str, from_state: str, to_state: str, reason: str, **kwargs
    ) -> None
    
    async def create_override_event(
        self, service_name: str, action: str, user_id: UUID, reason: str, **kwargs
    ) -> None
    
    async def increment_success(self, service_name: str, latency_ms: int) -> None
    async def increment_failure(self, service_name: str) -> None
    async def increment_circuit_open(self, service_name: str) -> None
    
    async def get_aggregated_metrics(
        self, service_name: str, days: int
    ) -> List[Dict[str, Any]]
```

---

## 5. Integration Points

### 5.1 MCP Server Integration
**Path**: `src/app/infrastructure/mcp/base_retry.py`

Base class for MCP servers with built-in retry.

```python
class RetryableMCPServer:
    """Base class for MCP servers with retry support."""
    
    def __init__(self, retry_engine: EnterpriseRetryEngine): ...
    
    async def execute_with_retry(self, tool_name: str, func: Callable) -> Any:
        """Execute MCP tool with retry logic."""
```

### 5.2 LLM Provider Integration
**Path**: `src/app/infrastructure/adapters/ai/llm/retry_handler.py`

Retry handler for LLM providers.

```python
class LLMRetryHandler:
    """Handles retry logic for LLM provider calls."""
    
    async def execute(self, provider_name: str, func: Callable) -> Any
```

### 5.3 Agno Agent Integration
**Path**: `src/app/infrastructure/agno/base_agent.py`

Retry integration for Agno AI agents.

---

## 6. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Admin Retry Router                                 │  │
│  │  /admin/retry/services • /admin/retry/circuit-breakers • /metrics    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Interactors                                   │  │
│  │  GetServiceList • GetServiceStatus • DisableService • EnableService  │  │
│  │  GetCircuitStatus • ResetCircuitBreaker • GetServiceMetrics          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       Core Services                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │  │
│  │  │ RetryEngine     │  │ CircuitBreaker  │  │  ServiceRegistry    │  │  │
│  │  │                 │  │                 │  │                     │  │  │
│  │  │ • execute_with_ │  │ • is_open       │  │ • is_enabled        │  │  │
│  │  │   retry         │  │ • record_success│  │ • disable_service   │  │  │
│  │  │ • calculate_    │  │ • record_failure│  │ • enable_service    │  │  │
│  │  │   backoff       │  │ • reset         │  │ • get_status        │  │  │
│  │  │ • classify_     │  │ • get_status    │  │                     │  │  │
│  │  │   error         │  │                 │  └─────────────────────┘  │  │
│  │  └─────────────────┘  └─────────────────┘                           │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │                TelemetryCollector                            │   │  │
│  │  │  record_attempt_start • record_success • record_failure      │   │  │
│  │  │  record_circuit_state_change • record_service_override       │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────┐   │  │
│  │  │                  Value Objects                                │   │  │
│  │  │  RetryConfig • CircuitBreakerConfig • RetryEventType         │   │  │
│  │  └──────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Redis State Storage                                │  │
│  │  circuit:{service}:state • circuit:{service}:failures                │  │
│  │  circuit:{service}:opened_at • service:{service}:override            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                  RetryTelemetryRepository                             │  │
│  │  retry_attempts • circuit_breaker_events • service_override_events   │  │
│  │  retry_metrics_aggregate                                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                   Integration Points                                  │  │
│  │  MCP Servers • LLM Providers • Agno Agents • External APIs           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA STORAGE                                        │
│                                                                              │
│  ┌────────────────────────┐  ┌────────────────────────────────────────┐    │
│  │        Redis           │  │           PostgreSQL                   │    │
│  │                        │  │                                        │    │
│  │ • Circuit breaker      │  │ • retry_attempts                       │    │
│  │   state (per service)  │  │ • circuit_breaker_events               │    │
│  │ • Service overrides    │  │ • service_override_events              │    │
│  │ • Failure counters     │  │ • retry_metrics_aggregate              │    │
│  └────────────────────────┘  └────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## References

- **Domain Services**: `src/app/domain/services/retry/`
- **Value Objects**: `src/app/domain/value_objects/retry_config.py`
- **Application Interactors**: `src/app/application/admin/retry/`
- **Infrastructure Repository**: `src/app/infrastructure/persistence_sqla/repositories/retry_telemetry_repository.py`
- **Database Mappings**: `src/app/infrastructure/persistence_sqla/mappings/retry_telemetry.py`
