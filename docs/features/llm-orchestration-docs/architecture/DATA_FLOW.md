# Data Flow Documentation

## Request Lifecycle

This document details the complete lifecycle of an LLM request through the orchestration system.

---

## Status Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REQUEST LIFECYCLE STATES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌──────────┐                                                              │
│    │ PENDING  │◀─────────────────────────────────────────────────┐          │
│    └────┬─────┘                                                   │          │
│         │ Request received                                        │          │
│         ▼                                                         │          │
│    ┌──────────┐     Rate Limited?     ┌──────────┐               │          │
│    │  QUEUED  │──────────Yes─────────▶│  QUEUED  │ (with delay)  │          │
│    └────┬─────┘                       └────┬─────┘               │          │
│         │ Ready to process                 │                      │          │
│         │◀─────────────────────────────────┘                      │          │
│         ▼                                                         │          │
│    ┌──────────────┐                                               │          │
│    │  SELECTING   │  Query ranking engine                         │          │
│    │    MODEL     │  Check circuit breakers                       │          │
│    └──────┬───────┘  Filter by capabilities                       │          │
│           │                                                       │          │
│           ▼                                                       │          │
│    ┌──────────────┐     Error?     ┌──────────────┐              │          │
│    │  EXECUTING   │───────Yes─────▶│   RETRYING   │──────────────┘          │
│    └──────┬───────┘                └──────────────┘   (carousel)            │
│           │                              │                                   │
│           │ Streaming?                   │ Max Retries Exceeded?             │
│           ▼                              ▼                                   │
│    ┌──────────────┐              ┌──────────────┐                           │
│    │  STREAMING   │              │    FAILED    │ ◀── Terminal State        │
│    └──────┬───────┘              └──────────────┘                           │
│           │                                                                  │
│           ▼                                                                  │
│    ┌──────────────┐              ┌──────────────┐                           │
│    │  COMPLETED   │              │   TIMEOUT    │ ◀── Terminal State        │
│    └──────────────┘              └──────────────┘                           │
│           ▲                                                                  │
│           │                                                                  │
│    ┌──────────────┐                                                         │
│    │  CANCELLED   │ ◀── User/Admin initiated (Terminal State)               │
│    └──────────────┘                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Status Definitions

| Status | Description | Duration | Next States |
|--------|-------------|----------|-------------|
| `pending` | Request received, not yet processed | < 100ms | `queued` |
| `queued` | Waiting in queue (rate limit/backpressure) | 0 - 60s | `selecting_model` |
| `selecting_model` | Determining best model via ranking | < 50ms | `executing`, `failed` |
| `executing` | API call in progress | 100ms - 30s | `streaming`, `completed`, `retrying`, `timeout` |
| `streaming` | SSE response in progress | 1s - 60s | `completed`, `failed` |
| `retrying` | Attempt failed, trying next model | < 5s | `executing`, `failed` |
| `completed` | Successfully finished | - | (terminal) |
| `failed` | All retries exhausted | - | (terminal) |
| `timeout` | Request exceeded time limit | - | (terminal) |
| `cancelled` | Manually stopped | - | (terminal) |

---

## Detailed Flow

### Phase 1: Request Ingestion

```python
# 1. Request arrives from agent
async def handle_request(request: LLMRequest, agent_type: str):
    # Create tracking record
    tracking = await create_tracking_record(
        request_id=generate_uuid(),
        agent_type=agent_type,
        status="pending",
        created_at=now()
    )
    
    # Emit status event
    await emit_status_change(tracking, "pending", "Request received")
    
    return tracking
```

### Phase 2: Queue Management

```python
# 2. Check rate limits and queue if needed
async def check_and_queue(tracking: RequestTracking):
    rate_limit_result = await check_rate_limit(
        user_id=tracking.user_id,
        agent_type=tracking.agent_type
    )
    
    if rate_limit_result.exceeded:
        await update_status(tracking, "queued", 
            f"Rate limited, retry after {rate_limit_result.retry_after}s")
        await schedule_retry(tracking, rate_limit_result.retry_after)
        return
    
    await update_status(tracking, "selecting_model")
```

### Phase 3: Model Selection

```python
# 3. Select optimal model based on ranking
async def select_model(tracking: RequestTracking, request: LLMRequest):
    await update_status(tracking, "selecting_model")
    
    # Get required capabilities from request
    capabilities = extract_capabilities(request)
    
    # Query ranking engine
    ranked_models = await ranking_engine.get_ranked_models(
        agent_type=tracking.agent_type,
        capabilities=capabilities,
        exclude_circuit_breaker_open=True
    )
    
    if not ranked_models:
        await update_status(tracking, "failed", 
            "No available models match requirements")
        raise NoAvailableModelsError()
    
    # Store selection in tracking
    await update_tracking(tracking,
        selected_model_id=ranked_models[0].model_id,
        selection_reason="ranking"
    )
    
    return ranked_models
```

### Phase 4: Execution with Retry

```python
# 4. Execute with carousel retry
async def execute_with_retry(
    tracking: RequestTracking,
    request: LLMRequest,
    ranked_models: List[RankedModel]
):
    attempt = 0
    
    for model in ranked_models:
        # Check circuit breaker
        if circuit_breaker.is_open(model.model_id):
            continue
        
        for provider_attempt in range(MAX_RETRIES_PER_PROVIDER):
            attempt += 1
            
            if attempt > MAX_TOTAL_RETRIES:
                break
            
            try:
                # Update status
                await update_status(tracking, "executing",
                    f"Attempt {attempt}: {model.display_name}")
                
                # Record attempt start
                attempt_record = await record_attempt_start(
                    tracking=tracking,
                    attempt_number=attempt,
                    model=model
                )
                
                # Execute request
                start_time = time.time()
                response = await provider_orchestrator.execute(
                    request=request,
                    model=model
                )
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Record success
                await record_attempt_complete(
                    attempt_record=attempt_record,
                    status="completed",
                    latency_ms=latency_ms,
                    output_tokens=response.output_tokens
                )
                
                circuit_breaker.record_success(model.model_id)
                
                return response
                
            except RetryableError as e:
                # Record failure
                await record_attempt_complete(
                    attempt_record=attempt_record,
                    status="failed",
                    error_type=classify_error(e),
                    error_message=str(e)
                )
                
                circuit_breaker.record_failure(model.model_id)
                
                # Update status to retrying
                await update_status(tracking, "retrying",
                    f"Attempt {attempt} failed: {e}, trying next model")
                
                # Apply backoff
                backoff = calculate_backoff(attempt)
                await asyncio.sleep(backoff)
                
            except NonRetryableError as e:
                await record_attempt_complete(
                    attempt_record=attempt_record,
                    status="failed",
                    error_type="non_retryable",
                    error_message=str(e)
                )
                break  # Move to next model
    
    # All retries exhausted
    await update_status(tracking, "failed",
        f"All {attempt} attempts failed")
    raise AllRetriesExhaustedError()
```

### Phase 5: Response Handling

```python
# 5. Handle successful response
async def handle_response(
    tracking: RequestTracking,
    response: LLMResponse
):
    # Update tracking with response data
    await update_tracking(tracking,
        status="completed",
        output_tokens=response.output_tokens,
        total_latency_ms=response.latency_ms,
        actual_cost_usd=calculate_cost(response),
        completed_at=now()
    )
    
    # Emit status event
    await emit_status_change(tracking, "completed", "Request successful")
    
    # Record telemetry (async)
    asyncio.create_task(
        telemetry_engine.record_request(tracking, response)
    )
    
    # Update rankings (async)
    asyncio.create_task(
        ranking_engine.record_success(
            agent_type=tracking.agent_type,
            model_id=tracking.selected_model_id,
            latency_ms=response.latency_ms,
            cost=tracking.actual_cost_usd
        )
    )
    
    return response
```

---

## Streaming Flow

For streaming requests, the flow is modified:

```python
async def execute_streaming(
    tracking: RequestTracking,
    request: LLMRequest,
    model: RankedModel
) -> AsyncIterator[str]:
    await update_status(tracking, "streaming")
    
    first_token_time = None
    total_tokens = 0
    
    try:
        async for chunk in provider_orchestrator.execute_stream(request, model):
            if first_token_time is None:
                first_token_time = time.time()
                await update_tracking(tracking,
                    time_to_first_token_ms=int((first_token_time - start_time) * 1000)
                )
            
            total_tokens += count_tokens(chunk)
            yield chunk
        
        # Stream completed
        await update_status(tracking, "completed")
        await update_tracking(tracking,
            output_tokens=total_tokens,
            completed_at=now()
        )
        
    except Exception as e:
        await update_status(tracking, "failed", str(e))
        raise
```

---

## Error Classification

### Retryable Errors

| Error Type | Description | Retry Strategy |
|------------|-------------|----------------|
| `rate_limit` | Provider rate limit hit | Exponential backoff |
| `timeout` | Request timed out | Try different model |
| `service_unavailable` | Provider temporarily down | Try different provider |
| `model_overloaded` | Specific model at capacity | Try different model |
| `internal_error` | Provider internal error | Retry same model |

### Non-Retryable Errors

| Error Type | Description | Action |
|------------|-------------|--------|
| `invalid_request` | Malformed request | Return error to caller |
| `authentication_error` | Invalid API key | Alert ops, fail request |
| `content_policy_violation` | Request blocked by policy | Return error to caller |
| `context_length_exceeded` | Input too long | Return error to caller |
| `insufficient_quota` | Account quota exceeded | Alert ops, try fallback |

---

## Status History Tracking

Each status change is recorded in `status_history`:

```json
{
  "status_history": [
    {
      "status": "pending",
      "timestamp": "2025-12-01T10:00:00.000Z",
      "details": "Request received"
    },
    {
      "status": "selecting_model",
      "timestamp": "2025-12-01T10:00:00.050Z",
      "details": "Querying ranking engine"
    },
    {
      "status": "executing",
      "timestamp": "2025-12-01T10:00:00.100Z",
      "details": "Attempt 1: gemini-1.5-pro"
    },
    {
      "status": "retrying",
      "timestamp": "2025-12-01T10:00:02.500Z",
      "details": "Attempt 1 failed: timeout, trying next model"
    },
    {
      "status": "executing",
      "timestamp": "2025-12-01T10:00:02.600Z",
      "details": "Attempt 2: gemini-1.5-flash"
    },
    {
      "status": "completed",
      "timestamp": "2025-12-01T10:00:04.200Z",
      "details": "Request successful"
    }
  ]
}
```

---

## Timeout Handling

### Per-Attempt Timeout

```python
TIMEOUT_PER_ATTEMPT_MS = 30000  # 30 seconds

async def execute_with_timeout(request, model):
    try:
        return await asyncio.wait_for(
            provider_orchestrator.execute(request, model),
            timeout=TIMEOUT_PER_ATTEMPT_MS / 1000
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"Attempt timed out after {TIMEOUT_PER_ATTEMPT_MS}ms")
```

### Total Request Timeout

```python
TOTAL_TIMEOUT_MS = 120000  # 2 minutes

async def execute_request(request):
    try:
        return await asyncio.wait_for(
            orchestrator.execute(request),
            timeout=TOTAL_TIMEOUT_MS / 1000
        )
    except asyncio.TimeoutError:
        await update_status(tracking, "timeout",
            f"Total request timed out after {TOTAL_TIMEOUT_MS}ms")
        raise
```

---

## Cancellation Flow

```python
async def cancel_request(request_id: str, reason: str):
    tracking = await get_tracking(request_id)
    
    if tracking.status in TERMINAL_STATES:
        raise InvalidOperationError("Cannot cancel completed request")
    
    # Mark as cancelled
    await update_status(tracking, "cancelled", reason)
    
    # Cancel any in-flight operations
    if tracking.execution_task:
        tracking.execution_task.cancel()
    
    # Emit event
    await emit_status_change(tracking, "cancelled", reason)
```

---

## Event Emission

All status changes emit events for real-time monitoring:

```python
async def emit_status_change(
    tracking: RequestTracking,
    status: str,
    details: str
):
    event = {
        "type": "llm.request.status",
        "request_id": tracking.request_id,
        "status": status,
        "details": details,
        "timestamp": now().isoformat(),
        "agent_type": tracking.agent_type,
        "model_id": tracking.selected_model_id
    }
    
    # Emit to WebSocket subscribers
    await websocket_manager.broadcast(
        channel=f"llm:requests:{tracking.user_id}",
        event=event
    )
    
    # Emit to metrics
    metrics.counter("llm_status_changes_total",
        labels={"status": status, "agent_type": tracking.agent_type}
    ).inc()
```
