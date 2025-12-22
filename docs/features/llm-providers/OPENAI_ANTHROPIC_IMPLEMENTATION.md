# OpenAI and Anthropic LLM Provider Implementation

This document describes the implementation of OpenAI and Anthropic LLM provider adapters with automatic failover capabilities.

## Overview

The implementation provides:

1. **Unified Chat Interface**: Common interface for both OpenAI and Anthropic APIs
2. **Streaming Support**: Full support for streaming completions
3. **Token Tracking**: Accurate token usage and cost estimation
4. **Error Handling**: Comprehensive error classification and retry logic
5. **Automatic Failover**: Circuit breaker pattern with cost-optimized fallback
6. **Health Monitoring**: Provider health checks and status tracking

## Architecture

### Layer Structure

Following hexagonal architecture principles:

```
Domain Layer
├── ports/chat_llm_provider.py          # Interface definition
└── value_objects/llm/                  # Request/Response value objects

Infrastructure Layer
├── adapters/ai/
│   ├── openai_chat_adapter.py          # OpenAI implementation
│   ├── anthropic_chat_adapter.py       # Anthropic implementation
│   └── llm_provider_failover.py        # Failover orchestrator
└── config/llm_orchestration.py         # Configuration

Tests
└── integration/infrastructure/adapters/ai/
    ├── test_openai_chat_adapter.py
    ├── test_anthropic_chat_adapter.py
    └── test_llm_provider_failover.py
```

### Components

#### 1. ChatLLMProvider Port (`domain/ports/chat_llm_provider.py`)

Defines the contract for chat-focused LLM providers:

```python
class ChatLLMProvider(Protocol):
    async def complete(self, request: LLMRequest) -> LLMResponse
    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]
    async def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> Decimal
    async def health_check(self) -> Dict[str, Any]
```

Exception hierarchy:
- `ChatProviderError` - Base exception
- `RateLimitError` - Rate limiting (retryable)
- `TimeoutError` - Timeouts (retryable)
- `AuthenticationError` - Auth failures (non-retryable)
- `InvalidRequestError` - Bad requests (non-retryable)
- `ModelNotFoundError` - Model not available
- `ContentFilterError` - Policy violations
- `ProviderUnavailableError` - Service unavailable

#### 2. OpenAI Adapter (`openai_chat_adapter.py`)

Features:
- **Models**: GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5-turbo
- **Streaming**: Server-Sent Events (SSE) parsing
- **Pricing**: Accurate cost calculation per model
- **Retry Logic**: Exponential backoff with max 3 retries
- **Tool Support**: Function calling support
- **Connection Pooling**: Persistent HTTP connections

Pricing (per 1M tokens):
```python
PRICING = {
    "gpt-4-turbo": {"input": $10.00, "output": $30.00},
    "gpt-4o": {"input": $5.00, "output": $15.00},
    "gpt-4o-mini": {"input": $0.15, "output": $0.60},
    "gpt-3.5-turbo": {"input": $0.50, "output": $1.50},
}
```

#### 3. Anthropic Adapter (`anthropic_chat_adapter.py`)

Features:
- **Models**: Claude 3 Opus, Sonnet, Haiku, Claude 4.5
- **Streaming**: SSE with Anthropic's event format
- **System Messages**: Proper handling of system prompts
- **Pricing**: Accurate cost calculation per model
- **Tool Support**: Anthropic's tool use format
- **Multi-turn**: Full conversation support

Pricing (per 1M tokens):
```python
PRICING = {
    "claude-opus-4-5": {"input": $15.00, "output": $75.00},
    "claude-sonnet-4-5": {"input": $3.00, "output": $15.00},
    "claude-3-haiku-20240307": {"input": $0.25, "output": $1.25},
}
```

#### 4. Failover Orchestrator (`llm_provider_failover.py`)

Implements:

**Circuit Breaker Pattern**:
- States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
- Configurable thresholds for opening/closing
- Per-provider circuit tracking
- Automatic recovery testing

**Failover Logic**:
1. Try providers in priority order
2. Skip providers with open circuits
3. Apply cost optimization on fallback
4. Exponential backoff on retries
5. Track all attempts and errors

**Cost Optimization**:
When failing over to secondary provider, automatically uses cheaper models:
```python
FALLBACK_MODELS = {
    "gpt-4-turbo": "gpt-4o-mini",
    "claude-opus-4-5": "claude-3-haiku-20240307",
}
```

## Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
OPENAI_ORGANIZATION=org-...                 # Optional
OPENAI_TIMEOUT=60                           # Optional
OPENAI_MAX_RETRIES=3                        # Optional

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1  # Optional
ANTHROPIC_VERSION=2023-06-01                      # Optional
ANTHROPIC_TIMEOUT=60                              # Optional
ANTHROPIC_MAX_RETRIES=3                           # Optional

# Failover Configuration
LLM_PRIMARY_CHAT_PROVIDER=openai           # or "anthropic"
LLM_ENABLE_COST_FALLBACK=true
LLM_MAX_RETRIES_PER_PROVIDER=2
LLM_MAX_TOTAL_RETRIES=6

# Circuit Breaker Settings
LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
LLM_CIRCUIT_BREAKER_SUCCESS_THRESHOLD=3
LLM_CIRCUIT_BREAKER_TIMEOUT_SECONDS=60
```

### Configuration Loading

```python
from app.setup.config.llm_orchestration import load_llm_orchestration_config

config = load_llm_orchestration_config()

# Access OpenAI config
if config.openai:
    print(config.openai.api_key)

# Access Anthropic config
if config.anthropic:
    print(config.anthropic.api_key)

# Access orchestrator settings
print(config.orchestrator.primary_chat_provider)
```

## Usage Examples

### Basic Completion

```python
from app.infrastructure.adapters.ai.openai_chat_adapter import OpenAIChatAdapter
from app.domain.value_objects.llm import LLMRequest, LLMMessage
from decimal import Decimal

# Create adapter
adapter = OpenAIChatAdapter(api_key="sk-...")

# Build request
request = LLMRequest(
    messages=[
        LLMMessage(role="system", content="You are a helpful assistant."),
        LLMMessage(role="user", content="What is Python?"),
    ],
    model_id="gpt-3.5-turbo",
    max_tokens=500,
    temperature=Decimal("0.7"),
)

# Get completion
response = await adapter.complete(request)

print(f"Response: {response.content}")
print(f"Tokens: {response.total_tokens}")
print(f"Cost: ${response.cost_usd}")
```

### Streaming Completion

```python
request = LLMRequest(
    messages=[LLMMessage(role="user", content="Write a short story.")],
    model_id="gpt-4o-mini",
    max_tokens=1000,
    stream=True,
)

async for chunk in adapter.complete_stream(request):
    print(chunk, end="", flush=True)
```

### Failover with Multiple Providers

```python
from app.infrastructure.adapters.ai.llm_provider_failover import (
    create_openai_anthropic_failover,
)

# Create failover orchestrator
failover = create_openai_anthropic_failover(
    openai_api_key="sk-...",
    anthropic_api_key="sk-ant-...",
    primary="openai",
    enable_cost_fallback=True,
)

# Use normally - automatically fails over if needed
response = await failover.complete(request)

# Check provider status
status = await failover.get_provider_status()
for provider, info in status.items():
    print(f"{provider}: {info['circuit_state']} - {info['health']['status']}")
```

### Cost Estimation

```python
# Estimate cost before making request
cost = await adapter.estimate_cost(
    input_tokens=1000,
    output_tokens=500,
    model="gpt-4-turbo",
)

print(f"Estimated cost: ${cost}")

# Actual usage
response = await adapter.complete(request)
print(f"Actual cost: ${response.cost_usd}")
```

### Health Checks

```python
# Check provider health
health = await adapter.health_check()

print(f"Status: {health['status']}")
print(f"Latency: {health['latency_ms']}ms")

if health['status'] == 'healthy':
    print(f"Available models: {health['available_models']}")
```

## Testing

### Running Integration Tests

```bash
# Set API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Run OpenAI tests
pytest tests/integration/infrastructure/adapters/ai/test_openai_chat_adapter.py -v

# Run Anthropic tests
pytest tests/integration/infrastructure/adapters/ai/test_anthropic_chat_adapter.py -v

# Run failover tests
pytest tests/integration/infrastructure/adapters/ai/test_llm_provider_failover.py -v

# Run all integration tests
pytest tests/integration/infrastructure/adapters/ai/ -v -m integration
```

### Running Unit Tests

```bash
# Unit tests don't require API keys
pytest tests/integration/infrastructure/adapters/ai/test_llm_provider_failover.py -v -m unit
```

## Error Handling

### Retryable Errors

These errors trigger automatic retry with exponential backoff:
- `RateLimitError` (429) - Respects retry-after header
- `TimeoutError` - Network timeouts
- `ProviderUnavailableError` (503, 529) - Service unavailable

### Non-Retryable Errors

These errors fail immediately:
- `AuthenticationError` (401) - Invalid API key
- `InvalidRequestError` (400) - Malformed request
- `ModelNotFoundError` (404) - Model doesn't exist
- `ContentFilterError` - Policy violation

### Example Error Handling

```python
from app.domain.ports.chat_llm_provider import (
    RateLimitError,
    AuthenticationError,
)

try:
    response = await adapter.complete(request)
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
    # Update API key
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Optimization

### Connection Pooling

Both adapters use persistent HTTP connections:
```python
self._client = httpx.AsyncClient(
    timeout=httpx.Timeout(timeout=60, connect=10.0),
    limits=httpx.Limits(
        max_keepalive_connections=10,
        max_connections=50,
    ),
)
```

### Token Efficiency

- Use `max_tokens` to control output length
- Set `temperature=0` for deterministic results
- Use cheaper models for simple tasks
- Enable cost fallback for automatic optimization

### Streaming Benefits

- Reduced time-to-first-token
- Lower perceived latency
- Better UX for long responses
- Memory efficient for large outputs

## Monitoring and Observability

### Metrics to Track

1. **Request Metrics**:
   - Total requests per provider
   - Success/failure rates
   - Latency (p50, p95, p99)

2. **Cost Metrics**:
   - Total spend per provider
   - Cost per request
   - Token usage trends

3. **Circuit Breaker Metrics**:
   - Circuit state changes
   - Failure counts
   - Recovery attempts

4. **Provider Health**:
   - Availability percentage
   - Error rates by type
   - Model availability

### Example Monitoring

```python
# Get provider status periodically
status = await failover.get_provider_status()

for provider, info in status.items():
    metrics = {
        "provider": provider,
        "circuit_state": info["circuit_state"],
        "failure_count": info["failure_count"],
        "health_status": info["health"]["status"],
        "latency_ms": info["health"]["latency_ms"],
    }
    # Send to monitoring system
    send_metrics(metrics)
```

## Best Practices

1. **Always use failover in production** - Don't rely on single provider
2. **Set appropriate timeouts** - Balance reliability vs latency
3. **Monitor circuit breaker states** - Alert on persistent failures
4. **Track costs closely** - Set budget alerts
5. **Use streaming for UX** - Better experience for users
6. **Test with both providers** - Ensure compatibility
7. **Handle errors gracefully** - Don't expose raw errors to users
8. **Use context managers** - Properly close HTTP clients

## Troubleshooting

### Issue: High latency

**Solutions**:
- Use faster models (gpt-4o-mini, claude-3-haiku)
- Reduce max_tokens
- Enable streaming
- Check network connectivity

### Issue: Rate limits

**Solutions**:
- Implement request queuing
- Use multiple API keys
- Increase backoff delays
- Contact provider for limit increase

### Issue: Circuit breaker stuck open

**Solutions**:
- Check provider health manually
- Verify API keys are valid
- Review failure threshold settings
- Wait for timeout period

### Issue: Incorrect costs

**Solutions**:
- Verify model names match pricing table
- Check for model version suffixes
- Update pricing if provider changed rates
- Use actual costs from provider dashboard

## Future Enhancements

1. **Model routing** - Route requests to best model based on task
2. **Caching** - Cache responses for identical requests
3. **Batch processing** - Batch multiple requests
4. **Advanced fallback** - Smart model selection based on capabilities
5. **A/B testing** - Compare provider performance
6. **Budget controls** - Hard limits on spending
7. **Prompt optimization** - Automatic prompt compression
8. **Multi-region** - Geographic failover

## References

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
