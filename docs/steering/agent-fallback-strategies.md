# Agent Fallback Strategies - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El sistema de Fallback de Agentes proporciona resiliencia multi-capa:

1. **LLM Provider Failover**: OpenAI ↔ Anthropic ↔ DeepInfra ↔ Vertex AI
2. **Circuit Breaker**: Redis-backed state con auto-recovery
3. **Agent Fallback Chains**: Priority-based agent routing
4. **Retry Engine**: Exponential backoff con jitter
5. **Cost Optimization**: Cheaper models on fallback
6. **Telemetry**: Comprehensive failure tracking
7. **Manual Override**: Admin control per service

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           FALLBACK STRATEGIES ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │    Request      │
                                    └────────┬────────┘
                                             │
                                             ▼
                              ┌──────────────────────────┐
                              │    Service Registry      │
                              │   (Manual Override?)     │
                              └──────────┬───────────────┘
                                         │
                        ┌────────────────┼────────────────┐
                  Service Enabled              Service Disabled
                        │                              │
                        ▼                              ▼
           ┌──────────────────────┐           ┌──────────────┐
           │   Circuit Breaker    │           │ ServiceError │
           │    (Redis State)     │           └──────────────┘
           └──────────┬───────────┘
                      │
      ┌───────────────┼───────────────┐
   CLOSED          OPEN           HALF_OPEN
      │              │                │
      ▼              ▼                ▼
  ┌────────┐   ┌────────────┐   ┌──────────┐
  │ Execute│   │ Skip + Try │   │ Limited  │
  │ Request│   │ Next Agent │   │ Testing  │
  └───┬────┘   └────────────┘   └────┬─────┘
      │                              │
      ▼                              ▼
┌───────────────────────────────────────────────┐
│              Retry Engine                      │
│  (Exponential Backoff + Jitter + Telemetry)   │
└───────────────────────┬───────────────────────┘
                        │
     ┌──────────────────┼──────────────────┐
  Success            Retry             All Failed
     │                 │                    │
     ▼                 ▼                    ▼
┌─────────┐    ┌─────────────┐     ┌──────────────────┐
│ Record  │    │ Backoff &   │     │ Try Fallback     │
│ Success │    │ Retry       │     │ Provider/Agent   │
└─────────┘    └─────────────┘     └──────────────────┘
```

---

## 1. LLM Provider Failover

### LLMProviderFailover

**Location**: `src/app/infrastructure/adapters/ai/llm_provider_failover.py`

Orchestrates automatic failover between LLM providers.

```python
class LLMProviderFailover:
    """
    Failover orchestrator for multiple LLM providers.
    
    Features:
    - Circuit breaker for each provider
    - Priority-based routing
    - Cost optimization (cheaper models on fallback)
    - Automatic retry with exponential backoff
    """
    
    def __init__(
        self,
        providers: List[ProviderConfig],
        failure_threshold: int = 5,
        success_threshold: int = 2,
        circuit_timeout: int = 60,
        max_retries: int = 3,
        enable_cost_fallback: bool = True,
    ): ...
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Execute completion with automatic failover."""
        ...
    
    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Execute streaming completion with failover."""
        ...
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers and circuit breakers."""
        ...
```

### Cost-Based Model Fallback

```python
# Model mapping for cost optimization on fallback
_fallback_models = {
    # OpenAI fallbacks (premium → cheap)
    "gpt-4-turbo": "gpt-4o-mini",
    "gpt-4": "gpt-4o-mini",
    "gpt-4o": "gpt-4o-mini",
    
    # Anthropic fallbacks
    "claude-opus-4-5": "claude-3-haiku-20240307",
    "claude-sonnet-4-5": "claude-3-haiku-20240307",
    "claude-3-5-sonnet-20241022": "claude-3-haiku-20240307",
}
```

### Factory Function

```python
def create_openai_anthropic_failover(
    openai_api_key: str,
    anthropic_api_key: str,
    primary: str = "openai",
    enable_cost_fallback: bool = True,
) -> LLMProviderFailover:
    """
    Create failover with OpenAI and Anthropic providers.
    
    Args:
        primary: Primary provider ("openai" or "anthropic")
        enable_cost_fallback: Use cheaper models on fallback
    """
    ...
```

---

## 2. LLM Client With Fallback

### Agent Squad Fallback

**Location**: `src/app/infrastructure/adapters/agent_squad/llm_client_with_fallback.py`

Simple primary/fallback wrapper for agent operations.

```python
class LLMClientWithFallback:
    """
    LLM Client wrapper with automatic fallback support.
    
    Tries primary provider first, falls back to secondary on failure.
    """
    
    def __init__(
        self,
        primary_client: LLMClientGateway,
        fallback_client: Optional[LLMClientGateway] = None,
        enable_fallback: bool = True,
    ): ...
    
    async def classify_intent(self, prompt: str, model: str) -> dict:
        """Classify intent with fallback support."""
        try:
            return await self._primary.classify_intent(prompt, model)
        except Exception as e:
            if self._enable_fallback:
                logger.warning(f"Primary failed: {e}. Falling back.")
                return await self._fallback.classify_intent(prompt, model)
            raise
    
    async def recommend_agents(self, prompt: str, model: str) -> dict: ...
    async def plan_workflow(self, prompt: str, max_agents: int) -> dict: ...
    async def chat(self, messages, model, temperature, max_tokens) -> dict: ...
    async def generate(self, model, messages, temperature, max_tokens) -> str: ...
```

---

## 3. Circuit Breaker

### Redis-Backed Circuit Breaker

**Location**: `src/app/domain/services/retry/circuit_breaker.py`

Prevents cascade failures with state-machine pattern.

```
State Flow:
    CLOSED ──(failures >= threshold)──▶ OPEN
       ▲                                   │
       │                                   │
       │                        (timeout expired)
       │                                   │
       │                                   ▼
    (successes >= threshold)◀─────── HALF_OPEN ──(failure)──▶ OPEN
```

```python
class CircuitBreaker:
    """
    Circuit breaker with Redis-backed state.
    
    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Failures exceeded threshold, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(
        self,
        redis_client: Any,
        config: CircuitBreakerConfig,
        telemetry: Optional[Any] = None,
    ): ...
    
    def is_open(self, service_name: str) -> bool:
        """Check if circuit is open for service."""
        ...
    
    def record_success(self, service_name: str):
        """Record successful call (may close circuit)."""
        ...
    
    def record_failure(self, service_name: str):
        """Record failed call (may open circuit)."""
        ...
    
    def reset(self, service_name: str):
        """Manually reset circuit breaker to closed."""
        ...
    
    def get_status(self, service_name: str) -> Dict[str, Any]:
        """Get circuit breaker status."""
        ...
```

### Circuit Breaker Configuration

```python
@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5    # Failures before opening
    success_threshold: int = 2    # Successes in half-open to close
    timeout_seconds: int = 60     # Time before trying half-open
    half_open_max_calls: int = 3  # Max calls in half-open state
```

### Circuit Breaker Manager

```python
class CircuitBreakerManager:
    """Manages circuit breakers for all services."""
    
    def get_or_create(self, service_name: str) -> CircuitBreaker: ...
    def is_open(self, service_name: str) -> bool: ...
    def record_success(self, service_name: str): ...
    def record_failure(self, service_name: str): ...
    def reset(self, service_name: str): ...
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]: ...
    def count_open(self) -> int: ...
    def count_total(self) -> int: ...
```

---

## 4. Enterprise Retry Engine

### Retry Engine

**Location**: `src/app/domain/services/retry/retry_engine.py`

Intelligent retry with circuit breaker and telemetry integration.

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
    """
    
    def __init__(
        self,
        config: RetryConfig,
        circuit_breaker: Optional[CircuitBreakerManager] = None,
        telemetry: Optional[TelemetryCollector] = None,
        service_registry: Optional[ServiceRegistry] = None,
    ): ...
    
    async def execute_with_retry(
        self,
        service_name: str,
        func: Callable,
        context: Optional[Dict] = None,
    ) -> Any:
        """
        Execute function with retry, circuit breaker, and telemetry.
        
        Flow:
        1. Check manual override (service disabled?)
        2. Check circuit breaker (too many failures?)
        3. Execute with retry
        4. Record telemetry
        5. Update circuit breaker state
        """
        ...
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if error should trigger retry."""
        ...
    
    def classify_error(self, error: Exception) -> str:
        """Classify error type for tracking."""
        ...
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff delay with exponential backoff."""
        ...
```

### Error Classification

```python
def classify_error(self, error: Exception) -> str:
    """Classify error type for tracking."""
    
    # Retryable errors
    "rate_limit"           # 429, "rate limit" in message
    "timeout"              # Timeout errors
    "service_unavailable"  # 503, "unavailable"
    "model_overloaded"     # "overloaded" in message
    "internal_error"       # Unknown/default
    
    # Non-retryable errors (don't retry)
    "authentication_error" # 401, 403, "authentication"
    "invalid_request"      # 400, "invalid"
    "content_policy"       # "content" + "policy"
```

---

## 5. Retry Configuration

### RetryConfig Value Object

**Location**: `src/app/domain/value_objects/retry_config.py`

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
        """
        Calculate delay with exponential backoff + jitter.
        
        Formula: min(initial * (base ^ attempt), max) * jitter_factor
        
        Example:
            Attempt 0: ~2000ms (2s)
            Attempt 1: ~4000ms (4s)
            Attempt 2: ~8000ms (8s)
            Attempt 3: 10000ms (capped at max)
        """
        ...
```

### Pre-Configured Profiles

```python
# For MCP servers (external APIs, rate limits)
RetryConfig.for_mcp_servers()
# max_retries=3, backoff=2-10s, circuit_failure=5

# For Agno agents (lower latency tolerance)
RetryConfig.for_agno_agents()
# max_retries=2, backoff=1-5s, circuit_failure=3

# For testing (fast, deterministic)
RetryConfig.for_testing()
# max_retries=2, backoff=0.1-0.5s, no jitter
```

---

## 6. Agent Fallback Chains

### FallbackChain Value Object

**Location**: `src/app/domain/value_objects/chat/orchestration.py`

Priority-based agent fallback for resilient routing.

```python
class AgentPriority(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    FALLBACK = "fallback"


class FallbackReason(Enum):
    TIMEOUT = "timeout"
    ERROR = "error"
    LOW_CONFIDENCE = "low_confidence"
    UNAVAILABLE = "unavailable"
    OVERLOADED = "overloaded"


@dataclass(frozen=True)
class FallbackAgent:
    """Agent configuration for fallback chain."""
    
    agent_name: str
    priority: AgentPriority
    timeout_seconds: int = 30
    min_confidence_threshold: float = 0.5
    max_retries: int = 2
    is_available: bool = True
    
    def should_fallback(self, confidence: float, error: bool) -> bool:
        """Determine if should fallback to next agent."""
        if error:
            return True
        if confidence < self.min_confidence_threshold:
            return True
        return False


@dataclass
class FallbackChain:
    """Chain of fallback agents for resilient routing."""
    
    chain_id: UUID
    agents: List[FallbackAgent]
    current_agent_index: int = 0
    attempts: List[str] = field(default_factory=list)
    fallback_reasons: List[FallbackReason] = field(default_factory=list)
    final_agent_used: Optional[str] = None
    total_time_ms: int = 0
    
    def get_next_agent(self) -> Optional[FallbackAgent]:
        """Get next available agent in chain."""
        ...
    
    def record_attempt(self, agent_name: str, reason: FallbackReason):
        """Record agent attempt and fallback reason."""
        ...
    
    def has_more_agents(self) -> bool:
        """Check if more fallback agents are available."""
        ...
```

### Execute With Fallback

**Location**: `src/app/application/chat/services/agent_orchestration_service.py`

```python
async def execute_with_fallback(
    self,
    query: str,
    fallback_chain: FallbackChain,
    conversation: Optional[Conversation] = None,
) -> Tuple[str, FallbackChain]:
    """
    Execute query with intelligent fallback routing.
    
    Tries agents in priority order until successful response.
    Falls back on timeout, error, or low confidence.
    
    Example:
        Chain: primary (risk_analyzer) → secondary (yield_optimizer) → tertiary (general)
        
        Attempt 1: risk_analyzer times out → FALLBACK
        Attempt 2: yield_optimizer responds with 40% confidence → FALLBACK
        Attempt 3: general agent responds with 75% confidence → SUCCESS
    """
    while fallback_chain.has_more_agents():
        agent = fallback_chain.get_next_agent()
        
        try:
            response, confidence = await asyncio.wait_for(
                self._get_agent_response(agent.agent_name, query),
                timeout=agent.timeout_seconds,
            )
            
            if agent.should_fallback(confidence, False):
                fallback_chain.record_attempt(agent.agent_name, FallbackReason.LOW_CONFIDENCE)
                continue
            
            # Success!
            fallback_chain.final_agent_used = agent.agent_name
            return response, fallback_chain
            
        except asyncio.TimeoutError:
            fallback_chain.record_attempt(agent.agent_name, FallbackReason.TIMEOUT)
            
        except Exception:
            fallback_chain.record_attempt(agent.agent_name, FallbackReason.ERROR)
    
    return "All agents unavailable", fallback_chain
```

### Default Fallback Chain

```python
def create_default_fallback_chain(self) -> FallbackChain:
    """Create default fallback chain for DeFi queries."""
    return FallbackChain(agents=[
        FallbackAgent(
            agent_name="risk_analyzer",
            priority=AgentPriority.PRIMARY,
            timeout_seconds=30,
            min_confidence_threshold=0.7,
        ),
        FallbackAgent(
            agent_name="yield_optimizer",
            priority=AgentPriority.SECONDARY,
            timeout_seconds=45,
            min_confidence_threshold=0.6,
        ),
        FallbackAgent(
            agent_name="general_advisor",
            priority=AgentPriority.TERTIARY,
            timeout_seconds=60,
            min_confidence_threshold=0.5,
        ),
    ])
```

---

## 7. In-Memory Circuit Breaker

### Provider-Level Circuit Breaker

**Location**: `src/app/infrastructure/adapters/ai/llm_provider_failover.py`

Lightweight in-memory circuit breaker for LLM providers.

```python
@dataclass
class CircuitBreaker:
    """In-memory circuit breaker for individual provider."""
    
    provider_name: str
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 60
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    
    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset on success
    
    def record_failure(self):
        """Record failed request."""
        if self.state == CircuitState.HALF_OPEN:
            self._open_circuit()  # Failure in testing reopens
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._open_circuit()
    
    def can_attempt(self) -> bool:
        """Check if provider can be attempted."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check timeout
            if time.time() - self.last_failure_time >= self.timeout_seconds:
                self._half_open_circuit()
                return True
            return False
        
        return self.state == CircuitState.HALF_OPEN
```

---

## 8. Admin API Endpoints

### Circuit Breaker Admin

**Location**: `src/app/presentation/http/controllers/admin/retry/router.py`

```python
# GET /api/v1/admin/retry/services
# List all services and their circuit breaker status

# GET /api/v1/admin/retry/services/{service_name}/status
# Get specific service status

# POST /api/v1/admin/retry/services/{service_name}/reset
# Reset circuit breaker for service

# POST /api/v1/admin/retry/services/{service_name}/enable
# Enable service (manual override)

# POST /api/v1/admin/retry/services/{service_name}/disable
# Disable service (manual override)

# GET /api/v1/admin/retry/services/{service_name}/metrics
# Get retry metrics for service
```

---

## Fallback Strategy Examples

### Example 1: LLM Provider Failover

```python
# Create failover with OpenAI primary, Anthropic fallback
failover = LLMProviderFailover(
    providers=[
        ProviderConfig(provider=openai, priority=0),
        ProviderConfig(provider=anthropic, priority=1, is_fallback=True),
    ],
    enable_cost_fallback=True,  # Use gpt-4o-mini on fallback
)

# Execute request
response = await failover.complete(request)
# If OpenAI fails → tries Anthropic with cheaper model
```

### Example 2: Agent Fallback Chain

```python
# Create fallback chain
chain = FallbackChain(agents=[
    FallbackAgent("risk_analyzer", AgentPriority.PRIMARY, timeout=30, min_confidence=0.7),
    FallbackAgent("yield_optimizer", AgentPriority.SECONDARY, timeout=45, min_confidence=0.6),
    FallbackAgent("general_advisor", AgentPriority.TERTIARY, timeout=60, min_confidence=0.5),
])

# Execute with fallback
response, updated_chain = await orchestration_service.execute_with_fallback(
    query="Analyze this DeFi position",
    fallback_chain=chain,
)

# Check what happened
print(f"Final agent: {updated_chain.final_agent_used}")
print(f"Attempts: {updated_chain.attempts}")
print(f"Fallback reasons: {updated_chain.fallback_reasons}")
```

### Example 3: Retry Engine with Circuit Breaker

```python
# Configure retry
config = RetryConfig.for_mcp_servers()
engine = EnterpriseRetryEngine(
    config=config,
    circuit_breaker=circuit_breaker_manager,
    telemetry=telemetry_collector,
    service_registry=service_registry,
)

# Execute with retry
try:
    result = await engine.execute_with_retry(
        service_name="defillama_mcp",
        func=lambda: defillama_client.get_protocol_tvl("aave"),
        context={"user_id": user_id},
    )
except CircuitBreakerOpenError:
    # Circuit is open, use cached data
    result = await cache.get("aave_tvl")
except AllRetriesExhaustedError:
    # All retries failed, return error
    raise ServiceUnavailableError("DeFiLlama temporarily unavailable")
```

---

## Configuration Summary

### Default Thresholds

| Parameter | MCP Servers | Agno Agents | LLM Providers |
|-----------|-------------|-------------|---------------|
| Max Retries | 3 | 2 | 3 |
| Initial Backoff | 2s | 1s | 2s |
| Max Backoff | 10s | 5s | 60s |
| Circuit Failure Threshold | 5 | 3 | 5 |
| Circuit Success Threshold | 2 | 2 | 2 |
| Circuit Timeout | 60s | 30s | 60s |

### Error Classification

| Error Type | Retryable | Action |
|------------|-----------|--------|
| `rate_limit` | ✅ | Wait retry-after, then retry |
| `timeout` | ✅ | Exponential backoff retry |
| `service_unavailable` | ✅ | Try fallback provider |
| `model_overloaded` | ✅ | Backoff + retry |
| `authentication_error` | ❌ | Fail immediately |
| `invalid_request` | ❌ | Fail immediately |
| `content_policy` | ❌ | Fail immediately |

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **LLM Failover** | `infrastructure/adapters/ai/llm_provider_failover.py` | Multi-provider failover |
| **Client Fallback** | `infrastructure/adapters/agent_squad/llm_client_with_fallback.py` | Simple primary/fallback |
| **Circuit Breaker** | `domain/services/retry/circuit_breaker.py` | Redis-backed circuit breaker |
| **Retry Engine** | `domain/services/retry/retry_engine.py` | Enterprise retry with telemetry |
| **Retry Config** | `domain/value_objects/retry_config.py` | Retry configuration |
| **Fallback Chain** | `domain/value_objects/chat/orchestration.py` | Agent fallback chains |
| **Orchestration** | `application/chat/services/agent_orchestration_service.py` | Execute with fallback |
| **Admin API** | `presentation/http/controllers/admin/retry/router.py` | Admin endpoints |
| **Telemetry** | `domain/services/retry/telemetry_collector.py` | Retry telemetry |

---

## Telemetry & Monitoring

### Retry Telemetry Events

```python
# Recorded on each attempt
await telemetry.record_attempt_start(service_name, attempt, context)

# Recorded on success
await telemetry.record_success(service_name, attempt, latency_ms, context)

# Recorded on failure
await telemetry.record_failure(service_name, attempt, error_type, error_msg, context)

# Recorded on circuit state change
await telemetry.record_circuit_state_change(
    service_name, from_state, to_state, reason, failure_count
)
```

### Metrics Available

| Metric | Description |
|--------|-------------|
| `retry_attempts_total` | Total retry attempts per service |
| `retry_success_rate` | Success rate by service |
| `retry_latency_ms` | Latency per attempt |
| `circuit_breaker_state` | Current state per service |
| `circuit_breaker_transitions` | State transitions count |
| `fallback_chain_depth` | Average fallback depth used |

---

## Best Practices

### 1. Configure Appropriate Thresholds

```python
# For latency-sensitive operations
config = RetryConfig(
    max_retries=2,
    initial_backoff_seconds=0.5,
    max_backoff_seconds=2.0,
)

# For reliability-critical operations
config = RetryConfig(
    max_retries=5,
    initial_backoff_seconds=2.0,
    max_backoff_seconds=30.0,
)
```

### 2. Use Jitter to Prevent Thundering Herd

```python
config = RetryConfig(
    jitter=True,  # Adds 0.5x-1.5x random factor
)
```

### 3. Monitor Circuit Breaker States

```python
# Check before operations
if circuit_breaker.count_open() > 0:
    logger.warning(f"Open circuits: {circuit_breaker.count_open()}")
```

### 4. Implement Graceful Degradation

```python
try:
    result = await primary_service.execute(request)
except CircuitBreakerOpenError:
    # Use cached/stale data
    result = await cache.get_stale(key)
    logger.info("Using cached data due to circuit breaker")
```

---

## Security Considerations

### 1. Rate Limit Respect

Always honor `retry-after` headers to avoid account issues.

### 2. Cost Control

Use cost fallback to prevent expensive retries on premium models.

### 3. Admin Access

Circuit breaker admin endpoints require admin authentication.

### 4. Telemetry Sanitization

Don't log sensitive data in retry context.

---

**Last Updated**: January 2, 2026
