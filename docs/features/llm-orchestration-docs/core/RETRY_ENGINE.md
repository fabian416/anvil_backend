# Retry Engine

## Overview

The Retry Engine implements carousel-based retry logic with exponential backoff, allowing the system to gracefully handle failures by rotating through multiple models and providers.

---

## Carousel Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CAROUSEL RETRY STRATEGY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Attempt 1: Provider 1 (Vertex AI) → Model with highest ranking             │
│      │                                                                       │
│      ▼ [FAIL: Rate Limit]                                                   │
│      │ Backoff: 100ms + jitter                                              │
│                                                                              │
│  Attempt 2: Provider 1 (Vertex AI) → Next model in carousel                 │
│      │                                                                       │
│      ▼ [FAIL: Provider Down - Circuit Breaker Opens]                        │
│      │ Backoff: 200ms + jitter                                              │
│                                                                              │
│  Attempt 3: Provider 2 (DeepInfra) → Model with highest ranking             │
│      │                                                                       │
│      ▼ [FAIL: Timeout]                                                      │
│      │ Backoff: 400ms + jitter                                              │
│                                                                              │
│  Attempt 4: Provider 2 (DeepInfra) → Next model in carousel                 │
│      │                                                                       │
│      ▼ [FAIL: Model Error]                                                  │
│      │ Backoff: 800ms + jitter                                              │
│                                                                              │
│  Attempt 5: Provider 3 (Bedrock) → Model with highest ranking               │
│      │                                                                       │
│      ▼ [SUCCESS!]                                                           │
│                                                                              │
│  Response returned to caller                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

```python
from dataclasses import dataclass
from typing import List

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    # Retry limits
    max_retries_per_provider: int = 2
    max_total_retries: int = 6
    
    # Backoff settings
    initial_delay_ms: int = 100
    max_delay_ms: int = 5000
    backoff_multiplier: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.25  # ±25% jitter
    
    # Timeout settings
    timeout_per_attempt_ms: int = 30000
    total_timeout_ms: int = 120000
    
    # Error classification
    retry_on_errors: List[str] = None
    no_retry_errors: List[str] = None
    
    def __post_init__(self):
        if self.retry_on_errors is None:
            self.retry_on_errors = [
                "rate_limit",
                "timeout",
                "service_unavailable",
                "model_overloaded",
                "internal_error",
                "connection_error"
            ]
        
        if self.no_retry_errors is None:
            self.no_retry_errors = [
                "invalid_request",
                "authentication_error",
                "content_policy_violation",
                "context_length_exceeded",
                "insufficient_quota"
            ]
```

---

## Implementation

```python
# src/llm/orchestration/retry.py

import asyncio
import random
from datetime import datetime
from typing import Callable, Optional, TypeVar, Any
from enum import Enum

T = TypeVar('T')


class RetryDecision(Enum):
    """Decision for whether to retry."""
    RETRY_SAME_MODEL = "retry_same_model"
    RETRY_NEXT_MODEL = "retry_next_model"
    RETRY_NEXT_PROVIDER = "retry_next_provider"
    NO_RETRY = "no_retry"


class RetryEngine:
    """
    Implements carousel-based retry logic with exponential backoff.
    
    Features:
    - Exponential backoff with jitter
    - Model carousel within providers
    - Provider fallback chain
    - Error classification
    - Attempt tracking
    """
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate backoff delay for a given attempt.
        
        Uses exponential backoff with optional jitter.
        
        Args:
            attempt: Current attempt number (1-indexed)
            
        Returns:
            Delay in seconds
        """
        # Calculate base delay using exponential backoff
        delay_ms = self.config.initial_delay_ms * (
            self.config.backoff_multiplier ** (attempt - 1)
        )
        
        # Cap at max delay
        delay_ms = min(delay_ms, self.config.max_delay_ms)
        
        # Add jitter if enabled
        if self.config.jitter:
            jitter_range = delay_ms * self.config.jitter_factor
            delay_ms += random.uniform(-jitter_range, jitter_range)
        
        # Convert to seconds
        return max(delay_ms / 1000, 0)
    
    def should_retry(self, error: Exception) -> RetryDecision:
        """
        Determine if and how to retry based on error type.
        
        Args:
            error: The exception that occurred
            
        Returns:
            RetryDecision indicating retry strategy
        """
        error_type = self._classify_error(error)
        
        # Check if error is in no-retry list
        if error_type in self.config.no_retry_errors:
            return RetryDecision.NO_RETRY
        
        # Check if error is in retry list
        if error_type not in self.config.retry_on_errors:
            return RetryDecision.NO_RETRY
        
        # Determine retry strategy based on error type
        if error_type in ["rate_limit", "model_overloaded"]:
            return RetryDecision.RETRY_NEXT_MODEL
        
        elif error_type in ["service_unavailable", "connection_error"]:
            return RetryDecision.RETRY_NEXT_PROVIDER
        
        elif error_type in ["timeout", "internal_error"]:
            return RetryDecision.RETRY_SAME_MODEL
        
        return RetryDecision.RETRY_NEXT_MODEL
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error into known categories."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Rate limiting
        if "rate limit" in error_str or "429" in error_str or "too many" in error_str:
            return "rate_limit"
        
        # Timeout
        if "timeout" in error_str or isinstance(error, asyncio.TimeoutError):
            return "timeout"
        
        # Service unavailable
        if "503" in error_str or "unavailable" in error_str:
            return "service_unavailable"
        
        # Model overloaded
        if "overloaded" in error_str or "capacity" in error_str:
            return "model_overloaded"
        
        # Connection errors
        if "connection" in error_str or "network" in error_str:
            return "connection_error"
        
        # Authentication
        if "401" in error_str or "authentication" in error_str or "unauthorized" in error_str:
            return "authentication_error"
        
        # Invalid request
        if "400" in error_str or "invalid" in error_str or "bad request" in error_str:
            return "invalid_request"
        
        # Content policy
        if "policy" in error_str or "content" in error_str:
            return "content_policy_violation"
        
        # Context length
        if "context" in error_str and "length" in error_str:
            return "context_length_exceeded"
        
        # Default to internal error
        return "internal_error"
    
    async def execute_with_retry(
        self,
        func: Callable[..., T],
        models: list,
        max_attempts: Optional[int] = None
    ) -> T:
        """
        Execute a function with carousel retry logic.
        
        Args:
            func: Async function to execute (takes model as first arg)
            models: List of models to try in order
            max_attempts: Override for max total retries
            
        Returns:
            Result of successful function call
            
        Raises:
            AllRetriesExhausted: When all attempts fail
        """
        max_attempts = max_attempts or self.config.max_total_retries
        
        attempt = 0
        model_index = 0
        provider_attempts = {}  # Track attempts per provider
        last_error = None
        
        while attempt < max_attempts and model_index < len(models):
            model = models[model_index]
            provider_id = model.provider_id
            
            # Check if we've exhausted attempts for this provider
            provider_attempts[provider_id] = provider_attempts.get(provider_id, 0) + 1
            
            if provider_attempts[provider_id] > self.config.max_retries_per_provider:
                # Move to next provider's models
                next_provider = self._find_next_provider(models, model_index, provider_id)
                if next_provider is not None:
                    model_index = next_provider
                    continue
                else:
                    break
            
            attempt += 1
            
            try:
                result = await asyncio.wait_for(
                    func(model),
                    timeout=self.config.timeout_per_attempt_ms / 1000
                )
                return result
                
            except Exception as e:
                last_error = e
                decision = self.should_retry(e)
                
                if decision == RetryDecision.NO_RETRY:
                    raise
                
                elif decision == RetryDecision.RETRY_SAME_MODEL:
                    # Stay on same model
                    pass
                
                elif decision == RetryDecision.RETRY_NEXT_MODEL:
                    # Move to next model in carousel
                    model_index += 1
                
                elif decision == RetryDecision.RETRY_NEXT_PROVIDER:
                    # Skip to next provider
                    next_provider = self._find_next_provider(
                        models, model_index, provider_id
                    )
                    if next_provider is not None:
                        model_index = next_provider
                    else:
                        model_index = len(models)  # End loop
                
                # Apply backoff before retry
                if attempt < max_attempts:
                    delay = self.calculate_backoff(attempt)
                    await asyncio.sleep(delay)
        
        raise AllRetriesExhausted(
            f"All {attempt} attempts failed. Last error: {last_error}"
        )
    
    def _find_next_provider(
        self,
        models: list,
        current_index: int,
        current_provider: str
    ) -> Optional[int]:
        """Find index of first model from a different provider."""
        for i, model in enumerate(models[current_index + 1:], current_index + 1):
            if model.provider_id != current_provider:
                return i
        return None


class AllRetriesExhausted(Exception):
    """Raised when all retry attempts are exhausted."""
    pass
```

---

## Backoff Visualization

```
Attempt | Base Delay | With Jitter (±25%)
--------|------------|--------------------
   1    |    100ms   |    75ms - 125ms
   2    |    200ms   |   150ms - 250ms
   3    |    400ms   |   300ms - 500ms
   4    |    800ms   |   600ms - 1000ms
   5    |   1600ms   |  1200ms - 2000ms
   6    |   3200ms   |  2400ms - 4000ms
   7+   |   5000ms   |  3750ms - 5000ms (capped)
```

---

## Error Classification Decision Tree

```
┌─────────────────────────────────────────────┐
│              Error Occurred                  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Is error in no_retry_errors list?          │
│  (invalid_request, auth_error, etc.)        │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
       YES                 NO
        │                   │
        ▼                   ▼
┌───────────────┐  ┌───────────────────────────┐
│   NO RETRY    │  │ Is error in retry_errors? │
│  Return error │  └───────────┬───────────────┘
└───────────────┘              │
                     ┌─────────┴─────────┐
                     │                   │
                    YES                 NO
                     │                   │
                     ▼                   ▼
        ┌────────────────────┐  ┌───────────────┐
        │ Classify error:    │  │   NO RETRY    │
        │ - rate_limit       │  │  Return error │
        │ - timeout          │  └───────────────┘
        │ - unavailable      │
        │ - overloaded       │
        └─────────┬──────────┘
                  │
    ┌─────────────┼─────────────┬─────────────────┐
    │             │             │                 │
    ▼             ▼             ▼                 ▼
┌────────┐  ┌────────┐   ┌──────────┐     ┌──────────┐
│ rate_  │  │timeout │   │service_  │     │internal_ │
│ limit  │  │        │   │unavail   │     │error     │
└───┬────┘  └───┬────┘   └────┬─────┘     └────┬─────┘
    │           │             │                │
    ▼           ▼             ▼                ▼
┌────────┐  ┌────────┐   ┌──────────┐     ┌──────────┐
│ RETRY  │  │ RETRY  │   │  RETRY   │     │  RETRY   │
│ NEXT   │  │ SAME   │   │  NEXT    │     │  SAME    │
│ MODEL  │  │ MODEL  │   │ PROVIDER │     │  MODEL   │
└────────┘  └────────┘   └──────────┘     └──────────┘
```

---

## Usage Examples

### Basic Retry

```python
retry_engine = RetryEngine(config=RetryConfig())

async def call_model(model):
    return await provider.complete(request, model)

result = await retry_engine.execute_with_retry(
    func=call_model,
    models=ranked_models
)
```

### Custom Configuration

```python
config = RetryConfig(
    max_retries_per_provider=3,
    max_total_retries=9,
    initial_delay_ms=200,
    backoff_multiplier=1.5,
    jitter=True,
    jitter_factor=0.3
)

retry_engine = RetryEngine(config=config)
```

### With Callback

```python
async def on_retry(attempt, model, error):
    logger.warning(f"Attempt {attempt} failed on {model.name}: {error}")
    await metrics.increment("llm_retries", {"model": model.name})

result = await retry_engine.execute_with_retry(
    func=call_model,
    models=ranked_models,
    on_retry=on_retry
)
```

---

## Metrics

The retry engine emits these metrics:

```python
# Retry counts
llm_retry_attempts_total{provider, model, error_type}

# Backoff time
llm_retry_backoff_seconds{attempt}

# Final outcomes
llm_retry_final_status{status}  # success, exhausted
```
