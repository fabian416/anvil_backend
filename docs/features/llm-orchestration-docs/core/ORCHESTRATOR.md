# Orchestrator Core

## Overview

The LLM Orchestrator is the central component that coordinates request routing, model selection, retry logic, and telemetry collection.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLMOrchestrator                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                    │
│  │ ProviderManager │     │  RankingEngine  │                    │
│  │                 │     │                 │                    │
│  │ - vertex_ai     │     │ - get_ranked()  │                    │
│  │ - deepinfra     │     │ - record()      │                    │
│  │ - bedrock       │     │ - recalculate() │                    │
│  └────────┬────────┘     └────────┬────────┘                    │
│           │                       │                              │
│           └───────────┬───────────┘                              │
│                       │                                          │
│                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   RetryEngine                            │    │
│  │                                                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │    │
│  │  │  Carousel   │  │  Backoff    │  │ CircuitBreaker  │  │    │
│  │  │   Logic     │  │  Calculator │  │    Manager      │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                       │                                          │
│                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 TelemetryCollector                       │    │
│  │  - request metrics    - cost tracking    - error stats   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Class Definition

```python
# src/llm/orchestration/orchestrator.py

from typing import Optional, List, AsyncIterator
import asyncio
from datetime import datetime
from dataclasses import dataclass

from ..providers.base import BaseLLMProvider, LLMRequest, LLMResponse
from ..ranking.engine import RankingEngine, RankedModel
from .retry import RetryEngine, RetryConfig
from .circuit_breaker import CircuitBreakerManager
from ..telemetry.collector import TelemetryCollector


@dataclass
class OrchestratorConfig:
    """Configuration for the LLM Orchestrator."""
    
    # Retry settings
    max_retries_per_provider: int = 2
    max_total_retries: int = 6
    initial_delay_ms: int = 100
    max_delay_ms: int = 5000
    backoff_multiplier: float = 2.0
    jitter: bool = True
    
    # Timeout settings
    timeout_per_attempt_ms: int = 30000
    total_timeout_ms: int = 120000
    streaming_idle_timeout_ms: int = 10000
    
    # Feature flags
    enable_caching: bool = True
    enable_streaming: bool = True
    enable_cost_tracking: bool = True
    enable_ranking: bool = True


class LLMOrchestrator:
    """
    Main orchestration engine for multi-LLM routing.
    
    Responsibilities:
    - Model selection based on adaptive ranking
    - Retry with carousel fallback
    - Circuit breaker management
    - Telemetry collection
    - Cost tracking
    """
    
    def __init__(
        self,
        providers: dict[str, BaseLLMProvider],
        ranking_engine: RankingEngine,
        circuit_breaker_manager: CircuitBreakerManager,
        telemetry_collector: TelemetryCollector,
        config: OrchestratorConfig = None
    ):
        self.providers = providers
        self.ranking = ranking_engine
        self.circuit_breakers = circuit_breaker_manager
        self.telemetry = telemetry_collector
        self.config = config or OrchestratorConfig()
        
        # Initialize retry engine
        self.retry_engine = RetryEngine(
            config=RetryConfig(
                max_retries_per_provider=self.config.max_retries_per_provider,
                max_total_retries=self.config.max_total_retries,
                initial_delay_ms=self.config.initial_delay_ms,
                max_delay_ms=self.config.max_delay_ms,
                backoff_multiplier=self.config.backoff_multiplier,
                jitter=self.config.jitter
            )
        )
    
    async def execute(
        self,
        request: LLMRequest,
        agent_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> LLMResponse:
        """
        Execute an LLM request with full orchestration.
        
        Flow:
        1. Create tracking record
        2. Select best model based on ranking
        3. Execute with retry/fallback logic
        4. Record telemetry
        5. Update rankings
        
        Args:
            request: The LLM request to execute
            agent_type: Type of agent making the request
            user_id: Optional user ID for tracking
            session_id: Optional session ID for context
            
        Returns:
            LLMResponse from the successful model
            
        Raises:
            AllProvidersExhaustedException: All retries failed
            TimeoutError: Total timeout exceeded
        """
        request_id = self._generate_request_id()
        start_time = datetime.utcnow()
        
        # Create tracking record
        tracking = await self._create_tracking(
            request_id=request_id,
            request=request,
            agent_type=agent_type,
            user_id=user_id,
            session_id=session_id
        )
        
        try:
            # Get required capabilities
            capabilities = self._extract_capabilities(request)
            
            # Get ranked models for this agent
            ranked_models = await self.ranking.get_ranked_models(
                agent_type=agent_type,
                capabilities=capabilities
            )
            
            # Filter out models with open circuit breakers
            available_models = [
                m for m in ranked_models
                if not self.circuit_breakers.is_open(m.model_id)
            ]
            
            if not available_models:
                raise NoAvailableModelsError(
                    f"No available models for agent {agent_type}"
                )
            
            # Update tracking with model selection
            await self._update_tracking(tracking,
                status="selecting_model",
                selected_model_id=available_models[0].model_id
            )
            
            # Execute with retries
            response = await self._execute_with_retries(
                request=request,
                ranked_models=available_models,
                tracking=tracking
            )
            
            # Calculate total latency
            total_latency_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            # Update tracking as completed
            await self._complete_tracking(
                tracking=tracking,
                response=response,
                total_latency_ms=total_latency_ms
            )
            
            # Record telemetry (async, don't block response)
            asyncio.create_task(
                self.telemetry.record_success(
                    tracking=tracking,
                    response=response
                )
            )
            
            # Update rankings (async)
            asyncio.create_task(
                self.ranking.record_outcome(
                    agent_type=agent_type,
                    model_id=str(tracking.selected_model_id),
                    success=True,
                    latency_ms=response.latency_ms,
                    cost=self._calculate_cost(response)
                )
            )
            
            return response
            
        except Exception as e:
            # Record failure
            await self._fail_tracking(tracking, e)
            
            asyncio.create_task(
                self.telemetry.record_failure(
                    tracking=tracking,
                    error=e
                )
            )
            
            raise
    
    async def execute_stream(
        self,
        request: LLMRequest,
        agent_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Execute a streaming LLM request.
        
        Similar to execute() but yields chunks as they arrive.
        """
        request.stream = True
        request_id = self._generate_request_id()
        
        tracking = await self._create_tracking(
            request_id=request_id,
            request=request,
            agent_type=agent_type,
            user_id=user_id,
            session_id=session_id
        )
        
        try:
            ranked_models = await self.ranking.get_ranked_models(
                agent_type=agent_type,
                capabilities=self._extract_capabilities(request)
            )
            
            available_models = [
                m for m in ranked_models
                if not self.circuit_breakers.is_open(m.model_id)
            ]
            
            if not available_models:
                raise NoAvailableModelsError(
                    f"No available models for agent {agent_type}"
                )
            
            # For streaming, try each model until one works
            last_error = None
            
            for model in available_models:
                try:
                    await self._update_tracking(tracking,
                        status="streaming",
                        selected_model_id=model.model_id
                    )
                    
                    provider = self.providers[model.provider_name]
                    request.model_id = model.model_id
                    
                    first_token_time = None
                    total_tokens = 0
                    start_time = datetime.utcnow()
                    
                    async for chunk in provider.complete_stream(request):
                        if first_token_time is None:
                            first_token_time = datetime.utcnow()
                            ttft_ms = int(
                                (first_token_time - start_time).total_seconds() * 1000
                            )
                            await self._update_tracking(tracking,
                                time_to_first_token_ms=ttft_ms
                            )
                        
                        total_tokens += self._count_tokens(chunk)
                        yield chunk
                    
                    # Stream completed successfully
                    latency_ms = int(
                        (datetime.utcnow() - start_time).total_seconds() * 1000
                    )
                    
                    await self._complete_tracking(tracking,
                        response=LLMResponse(
                            content="[streaming]",
                            input_tokens=request.input_tokens or 0,
                            output_tokens=total_tokens,
                            model_id=model.model_id,
                            provider=model.provider_name,
                            latency_ms=latency_ms,
                            finish_reason="stop"
                        ),
                        total_latency_ms=latency_ms
                    )
                    
                    self.circuit_breakers.record_success(model.model_id)
                    return
                    
                except RetryableError as e:
                    last_error = e
                    self.circuit_breakers.record_failure(model.model_id)
                    continue
            
            raise AllProvidersExhaustedException(
                f"All streaming attempts failed. Last error: {last_error}"
            )
            
        except Exception as e:
            await self._fail_tracking(tracking, e)
            raise
    
    async def _execute_with_retries(
        self,
        request: LLMRequest,
        ranked_models: List[RankedModel],
        tracking: 'RequestTracking'
    ) -> LLMResponse:
        """Execute request with carousel retry logic."""
        
        attempt = 0
        last_error = None
        
        for model in ranked_models:
            provider = self.providers[model.provider_name]
            
            # Try each provider's models up to max_retries_per_provider
            for provider_attempt in range(self.config.max_retries_per_provider):
                attempt += 1
                
                if attempt > self.config.max_total_retries:
                    break
                
                try:
                    # Update tracking
                    await self._update_tracking(tracking,
                        status="executing",
                        attempt_count=attempt
                    )
                    
                    # Record attempt start
                    attempt_record = await self._record_attempt_start(
                        tracking=tracking,
                        attempt_number=attempt,
                        model=model
                    )
                    
                    # Execute with timeout
                    request.model_id = model.model_id
                    start_time = datetime.utcnow()
                    
                    response = await asyncio.wait_for(
                        provider.complete(request),
                        timeout=self.config.timeout_per_attempt_ms / 1000
                    )
                    
                    latency_ms = int(
                        (datetime.utcnow() - start_time).total_seconds() * 1000
                    )
                    response.latency_ms = latency_ms
                    
                    # Record successful attempt
                    await self._record_attempt_complete(
                        attempt_record=attempt_record,
                        status="completed",
                        latency_ms=latency_ms,
                        output_tokens=response.output_tokens
                    )
                    
                    # Update circuit breaker
                    self.circuit_breakers.record_success(model.model_id)
                    
                    return response
                    
                except asyncio.TimeoutError:
                    last_error = TimeoutError(
                        f"Attempt {attempt} timed out after "
                        f"{self.config.timeout_per_attempt_ms}ms"
                    )
                    
                    await self._record_attempt_complete(
                        attempt_record=attempt_record,
                        status="timeout",
                        error_type="timeout",
                        error_message=str(last_error)
                    )
                    
                    self.circuit_breakers.record_failure(model.model_id)
                    
                except RetryableError as e:
                    last_error = e
                    
                    await self._record_attempt_complete(
                        attempt_record=attempt_record,
                        status="failed",
                        error_type=self._classify_error(e),
                        error_message=str(e)
                    )
                    
                    self.circuit_breakers.record_failure(model.model_id)
                    
                    # Update tracking to retrying status
                    await self._update_tracking(tracking,
                        status="retrying"
                    )
                    
                    # Apply backoff
                    backoff = self.retry_engine.calculate_backoff(attempt)
                    await asyncio.sleep(backoff)
                    
                except NonRetryableError as e:
                    # Don't retry, record and move to next model
                    await self._record_attempt_complete(
                        attempt_record=attempt_record,
                        status="failed",
                        error_type="non_retryable",
                        error_message=str(e)
                    )
                    break
        
        # All retries exhausted
        raise AllProvidersExhaustedException(
            f"All {attempt} attempts failed across "
            f"{len(ranked_models)} models. Last error: {last_error}"
        )
    
    # Helper methods
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return f"req_{uuid.uuid4().hex[:16]}"
    
    def _extract_capabilities(self, request: LLMRequest) -> List[str]:
        """Extract required capabilities from request."""
        capabilities = ["chat"]
        
        if request.tools:
            capabilities.append("function_calling")
        
        # Check for vision in messages
        for msg in request.messages:
            if hasattr(msg, 'images') and msg.images:
                capabilities.append("vision")
                break
        
        return capabilities
    
    def _calculate_cost(self, response: LLMResponse) -> float:
        """Calculate cost for a response."""
        # Get model pricing
        model = self._get_model_by_id(response.model_id)
        if not model:
            return 0.0
        
        input_cost = (response.input_tokens / 1000) * model.cost_per_1k_input
        output_cost = (response.output_tokens / 1000) * model.cost_per_1k_output
        
        return input_cost + output_cost
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for tracking."""
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "429" in error_str:
            return "rate_limit"
        elif "timeout" in error_str:
            return "timeout"
        elif "503" in error_str or "unavailable" in error_str:
            return "service_unavailable"
        elif "overloaded" in error_str:
            return "model_overloaded"
        elif "authentication" in error_str or "401" in error_str:
            return "authentication_error"
        elif "invalid" in error_str or "400" in error_str:
            return "invalid_request"
        else:
            return "internal_error"
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (simplified)."""
        # Rough estimate: 4 chars per token
        return len(text) // 4
    
    async def _create_tracking(self, **kwargs) -> 'RequestTracking':
        """Create request tracking record in database."""
        # Implementation would create DB record
        pass
    
    async def _update_tracking(self, tracking, **kwargs):
        """Update tracking record."""
        pass
    
    async def _complete_tracking(self, tracking, response, total_latency_ms):
        """Mark tracking as completed."""
        pass
    
    async def _fail_tracking(self, tracking, error):
        """Mark tracking as failed."""
        pass
    
    async def _record_attempt_start(self, tracking, attempt_number, model):
        """Record attempt start in database."""
        pass
    
    async def _record_attempt_complete(self, attempt_record, **kwargs):
        """Record attempt completion."""
        pass
    
    def _get_model_by_id(self, model_id: str):
        """Get model configuration by ID."""
        pass


# Custom exceptions
class NoAvailableModelsError(Exception):
    """Raised when no models are available for a request."""
    pass


class AllProvidersExhaustedException(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class RetryableError(Exception):
    """Base class for errors that should trigger retry."""
    pass


class NonRetryableError(Exception):
    """Base class for errors that should not trigger retry."""
    pass
```

---

## Usage Examples

### Basic Execution

```python
from llm.orchestration import LLMOrchestrator
from llm.providers import VertexAIProvider, DeepInfraProvider, BedrockProvider

# Initialize providers
providers = {
    "vertex_ai": VertexAIProvider(config=vertex_config),
    "deepinfra": DeepInfraProvider(config=deepinfra_config),
    "bedrock": BedrockProvider(config=bedrock_config)
}

# Initialize orchestrator
orchestrator = LLMOrchestrator(
    providers=providers,
    ranking_engine=ranking_engine,
    circuit_breaker_manager=circuit_breaker_manager,
    telemetry_collector=telemetry_collector
)

# Execute request
request = LLMRequest(
    messages=[
        LLMMessage(role="user", content="What are the best yield farming strategies?")
    ],
    max_tokens=2000,
    temperature=0.7
)

response = await orchestrator.execute(
    request=request,
    agent_type="swap_agent",
    user_id="user_123"
)

print(f"Response: {response.content}")
print(f"Model: {response.model_id}")
print(f"Latency: {response.latency_ms}ms")
print(f"Cost: ${orchestrator._calculate_cost(response):.4f}")
```

### Streaming Execution

```python
# Streaming request
request = LLMRequest(
    messages=[
        LLMMessage(role="user", content="Explain DeFi yield farming in detail")
    ],
    max_tokens=4000,
    temperature=0.7,
    stream=True
)

async for chunk in orchestrator.execute_stream(
    request=request,
    agent_type="researcher"
):
    print(chunk, end="", flush=True)
```

### With Tool Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_token_price",
            "description": "Get current price of a token",
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Token symbol"}
                },
                "required": ["token"]
            }
        }
    }
]

request = LLMRequest(
    messages=[
        LLMMessage(role="user", content="What's the current ETH price?")
    ],
    tools=tools,
    max_tokens=1000
)

response = await orchestrator.execute(
    request=request,
    agent_type="trading_agent"
)

if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"Tool: {tool_call.function.name}")
        print(f"Args: {tool_call.function.arguments}")
```

---

## Configuration

### Environment Variables

```bash
# Orchestrator settings
LLM_MAX_RETRIES_PER_PROVIDER=2
LLM_MAX_TOTAL_RETRIES=6
LLM_TIMEOUT_PER_ATTEMPT_MS=30000
LLM_TOTAL_TIMEOUT_MS=120000

# Feature flags
LLM_ENABLE_CACHING=true
LLM_ENABLE_STREAMING=true
LLM_ENABLE_RANKING=true
LLM_ENABLE_COST_TRACKING=true
```

### Runtime Configuration

Configuration can be updated at runtime via the business config API:

```python
# Update retry config
await config_manager.update(
    key="retry_config",
    value={
        "max_retries_per_provider": 3,
        "max_total_retries": 8
    },
    reason="Increased retries for improved reliability"
)
```

---

## Error Handling

### Error Classification

| Error Type | Retry? | Action |
|------------|--------|--------|
| `rate_limit` | Yes | Exponential backoff |
| `timeout` | Yes | Try different model |
| `service_unavailable` | Yes | Try different provider |
| `model_overloaded` | Yes | Try different model |
| `internal_error` | Yes | Retry same model |
| `authentication_error` | No | Alert ops, fail |
| `invalid_request` | No | Return error |
| `content_policy` | No | Return error |

### Custom Error Handlers

```python
@orchestrator.on_error("rate_limit")
async def handle_rate_limit(error, context):
    """Custom handler for rate limit errors."""
    logger.warning(f"Rate limited on {context.model_id}")
    await alert_ops(f"Rate limit hit on {context.provider}")

@orchestrator.on_error("all_failed")
async def handle_all_failed(error, context):
    """Handler when all retries exhausted."""
    logger.error(f"All providers failed for request {context.request_id}")
    await notify_on_call(error)
```

---

## Monitoring

### Key Metrics

The orchestrator emits the following metrics:

```python
# Request metrics
llm_requests_total{provider, model, agent, status}
llm_request_duration_seconds{provider, model, agent}
llm_request_attempts_total{provider, model}

# Circuit breaker metrics
llm_circuit_breaker_state{entity_type, entity_id}
llm_circuit_breaker_trips_total{entity_type, entity_id}

# Cost metrics
llm_request_cost_usd{provider, model, agent}
llm_tokens_total{provider, model, direction}
```

### Health Check

```python
async def health_check() -> dict:
    """Check orchestrator health."""
    return {
        "status": "healthy",
        "providers": {
            name: await provider.health_check()
            for name, provider in orchestrator.providers.items()
        },
        "circuit_breakers": {
            "open": orchestrator.circuit_breakers.count_open(),
            "total": orchestrator.circuit_breakers.count_total()
        },
        "queue_depth": orchestrator.queue_depth
    }
```
