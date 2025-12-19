# Enterprise Retry System with Telemetry & Circuit Breaker

## Executive Summary

**Specification Date:** December 1, 2025  
**Scope:** MCP Servers, Agno Agents, Complete Observability  
**Version:** 2.0 (Extended with Telemetry & Intervention)

**Goal:** Implement enterprise-grade retry system with comprehensive telemetry, circuit breakers, and manual intervention capabilities for service unavailability.

---

## 🎯 Vision

Build a **self-healing, observable, and controllable** retry system that:
1. **Automatically retries** transient failures
2. **Monitors and logs** all retry attempts and outcomes
3. **Detects and prevents** cascading failures (circuit breaker)
4. **Allows manual intervention** when services are unavailable
5. **Provides real-time dashboards** for operations teams
6. **Tracks costs and performance** across all integrations

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│  (Chat, Projects, Agents orchestrate operations)                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 RETRY ORCHESTRATOR                              │
│  • Retry Engine (exponential backoff + jitter)                 │
│  • Circuit Breaker (CLOSED → OPEN → HALF_OPEN)                 │
│  • Telemetry Collector (metrics, events, logs)                 │
│  • Manual Override Manager (disable/enable services)           │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │  MCP   │  │  Agno  │  │External│
    │Servers │  │ Agents │  │  APIs  │
    │  (6)   │  │  (4)   │  │        │
    └────────┘  └────────┘  └────────┘
         │           │           │
         └───────────┴───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TELEMETRY STORAGE                              │
│  • PostgreSQL (structured metrics)                             │
│  • TimeSeries DB (time-series metrics - optional)              │
│  • Redis (circuit breaker state, rate limits)                  │
└─────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│               OBSERVABILITY LAYER                               │
│  • Admin Dashboard (real-time metrics)                          │
│  • Grafana (historical trends)                                  │
│  • Alerts (PagerDuty, Slack)                                    │
│  • Manual Intervention API (enable/disable services)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. Retry Engine (Enhanced)

**Location:** `src/app/domain/services/retry/retry_engine.py`

**Features:**
- ✅ Exponential backoff with jitter (existing in LLM)
- ✅ Model carousel (existing in LLM)
- 🆕 Circuit breaker integration
- 🆕 Telemetry integration
- 🆕 Manual override support
- 🆕 Service health tracking

**New Capabilities:**
```python
class EnterpriseRetryEngine:
    """
    Enterprise retry engine with circuit breaker and telemetry.
    
    Features:
    - Exponential backoff with jitter
    - Circuit breaker pattern
    - Comprehensive telemetry
    - Manual service override
    - Cost tracking
    - Performance monitoring
    """
    
    def __init__(
        self,
        config: RetryConfig,
        circuit_breaker: CircuitBreaker,
        telemetry: TelemetryCollector,
        service_registry: ServiceRegistry,
    ):
        self.config = config
        self.circuit_breaker = circuit_breaker
        self.telemetry = telemetry
        self.service_registry = service_registry
    
    async def execute_with_retry(
        self,
        service_name: str,
        func: Callable,
        context: Dict[str, Any],
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
        # 1. Manual override check
        if not self.service_registry.is_enabled(service_name):
            raise ServiceDisabledError(
                f"Service '{service_name}' is manually disabled"
            )
        
        # 2. Circuit breaker check
        if self.circuit_breaker.is_open(service_name):
            raise CircuitBreakerOpenError(
                f"Circuit breaker open for '{service_name}'"
            )
        
        # 3. Execute with retry + telemetry
        start_time = time.time()
        attempt = 0
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Record attempt start
                await self.telemetry.record_attempt_start(
                    service_name, attempt, context
                )
                
                # Execute
                result = await func()
                
                # Record success
                latency_ms = (time.time() - start_time) * 1000
                await self.telemetry.record_success(
                    service_name, attempt, latency_ms, context
                )
                
                # Reset circuit breaker on success
                self.circuit_breaker.record_success(service_name)
                
                return result
                
            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)
                
                # Record failure
                await self.telemetry.record_failure(
                    service_name, attempt, error_type, str(e), context
                )
                
                # Update circuit breaker
                self.circuit_breaker.record_failure(service_name)
                
                # Check if should retry
                if not self.should_retry(e, attempt):
                    break
                
                # Apply backoff
                if attempt < self.config.max_retries - 1:
                    backoff = self.calculate_backoff(attempt)
                    await asyncio.sleep(backoff)
        
        # All retries exhausted
        raise AllRetriesExhaustedError(
            f"All {attempt + 1} retries failed for {service_name}: {last_error}"
        )
```

---

### 2. Circuit Breaker

**Location:** `src/app/domain/services/retry/circuit_breaker.py`

**Pattern:** Based on `libs/python-patterns/patterns/behavioral/circuit_breaker.py`

**States:**
- **CLOSED**: Normal operation, requests flow through
- **OPEN**: Too many failures, requests blocked
- **HALF_OPEN**: Testing if service recovered

**Implementation:**
```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Optional
import redis

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open to close
    timeout_seconds: int = 60  # Time before trying half-open
    half_open_max_calls: int = 3  # Max calls in half-open state

class CircuitBreaker:
    """
    Circuit breaker with Redis-backed state.
    
    Prevents cascading failures by:
    - Tracking failure rates per service
    - Opening circuit when threshold exceeded
    - Automatically testing recovery
    - Recording state changes in telemetry
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        config: CircuitBreakerConfig,
        telemetry: TelemetryCollector,
    ):
        self.redis = redis_client
        self.config = config
        self.telemetry = telemetry
    
    def is_open(self, service_name: str) -> bool:
        """Check if circuit is open for service."""
        state = self._get_state(service_name)
        
        if state == CircuitState.OPEN:
            # Check if timeout expired (transition to half-open)
            if self._should_attempt_reset(service_name):
                self._transition_to_half_open(service_name)
                return False
            return True
        
        return False
    
    def record_success(self, service_name: str):
        """Record successful call."""
        state = self._get_state(service_name)
        
        if state == CircuitState.HALF_OPEN:
            # Increment success counter
            successes = self._increment_counter(
                f"circuit:{service_name}:half_open_successes"
            )
            
            # Close circuit if threshold met
            if successes >= self.config.success_threshold:
                self._transition_to_closed(service_name)
        
        elif state == CircuitState.CLOSED:
            # Reset failure counter on success
            self._reset_counter(f"circuit:{service_name}:failures")
    
    def record_failure(self, service_name: str):
        """Record failed call."""
        state = self._get_state(service_name)
        
        if state == CircuitState.HALF_OPEN:
            # Failure in half-open immediately opens circuit
            self._transition_to_open(service_name)
        
        elif state == CircuitState.CLOSED:
            # Increment failure counter
            failures = self._increment_counter(
                f"circuit:{service_name}:failures"
            )
            
            # Open circuit if threshold exceeded
            if failures >= self.config.failure_threshold:
                self._transition_to_open(service_name)
    
    def _transition_to_open(self, service_name: str):
        """Transition circuit to OPEN state."""
        self._set_state(service_name, CircuitState.OPEN)
        self._set_open_timestamp(service_name)
        
        # Record telemetry
        self.telemetry.record_circuit_breaker_event(
            service_name,
            "opened",
            {"reason": "failure_threshold_exceeded"}
        )
    
    def _transition_to_half_open(self, service_name: str):
        """Transition circuit to HALF_OPEN state."""
        self._set_state(service_name, CircuitState.HALF_OPEN)
        self._reset_counter(f"circuit:{service_name}:half_open_successes")
        
        # Record telemetry
        self.telemetry.record_circuit_breaker_event(
            service_name,
            "half_opened",
            {"reason": "timeout_expired"}
        )
    
    def _transition_to_closed(self, service_name: str):
        """Transition circuit to CLOSED state."""
        self._set_state(service_name, CircuitState.CLOSED)
        self._reset_counter(f"circuit:{service_name}:failures")
        
        # Record telemetry
        self.telemetry.record_circuit_breaker_event(
            service_name,
            "closed",
            {"reason": "success_threshold_met"}
        )
    
    # Redis helpers
    def _get_state(self, service_name: str) -> CircuitState:
        """Get circuit state from Redis."""
        state = self.redis.get(f"circuit:{service_name}:state")
        if state is None:
            return CircuitState.CLOSED
        return CircuitState(state.decode())
    
    def _set_state(self, service_name: str, state: CircuitState):
        """Set circuit state in Redis."""
        self.redis.set(f"circuit:{service_name}:state", state.value)
```

---

### 3. Telemetry Collector (Enhanced)

**Location:** `src/app/domain/services/retry/telemetry_collector.py`

**Extends:** Existing `src/app/domain/services/llm/telemetry_collector.py`

**New Metrics:**
```python
class RetryTelemetryCollector:
    """
    Telemetry collector for retry system.
    
    Tracks:
    - Retry attempts (count, success rate)
    - Circuit breaker events (open, close, half-open)
    - Service health (availability, latency)
    - Manual overrides (who, when, why)
    - Cost per service (API calls, tokens)
    - Error distribution (by type, service)
    """
    
    async def record_attempt_start(
        self,
        service_name: str,
        attempt: int,
        context: Dict[str, Any],
    ):
        """Record retry attempt start."""
        await self._store_event({
            "type": "retry_attempt_start",
            "service_name": service_name,
            "attempt": attempt,
            "timestamp": datetime.utcnow(),
            "context": context,
        })
    
    async def record_success(
        self,
        service_name: str,
        attempt: int,
        latency_ms: int,
        context: Dict[str, Any],
    ):
        """Record successful retry."""
        await self._store_event({
            "type": "retry_success",
            "service_name": service_name,
            "attempt": attempt,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow(),
            "context": context,
        })
        
        # Update metrics
        await self._update_service_metrics(
            service_name,
            success=True,
            latency_ms=latency_ms,
        )
    
    async def record_failure(
        self,
        service_name: str,
        attempt: int,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
    ):
        """Record failed retry."""
        await self._store_event({
            "type": "retry_failure",
            "service_name": service_name,
            "attempt": attempt,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow(),
            "context": context,
        })
        
        # Update metrics
        await self._update_service_metrics(
            service_name,
            success=False,
            error_type=error_type,
        )
    
    async def record_circuit_breaker_event(
        self,
        service_name: str,
        event_type: str,  # "opened", "closed", "half_opened"
        metadata: Dict[str, Any],
    ):
        """Record circuit breaker state change."""
        await self._store_event({
            "type": f"circuit_breaker_{event_type}",
            "service_name": service_name,
            "timestamp": datetime.utcnow(),
            "metadata": metadata,
        })
    
    async def record_manual_override(
        self,
        service_name: str,
        action: str,  # "enabled", "disabled"
        user_id: UUID,
        reason: str,
    ):
        """Record manual service override."""
        await self._store_event({
            "type": "manual_override",
            "service_name": service_name,
            "action": action,
            "user_id": str(user_id),
            "reason": reason,
            "timestamp": datetime.utcnow(),
        })
```

---

### 4. Service Registry (Manual Override)

**Location:** `src/app/domain/services/retry/service_registry.py`

**Purpose:** Allow manual intervention when services are unavailable.

**Implementation:**
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
        redis_client: redis.Redis,
        telemetry: TelemetryCollector,
    ):
        self.redis = redis_client
        self.telemetry = telemetry
    
    def is_enabled(self, service_name: str) -> bool:
        """Check if service is enabled."""
        # Check manual override
        override = self.redis.get(f"service:{service_name}:override")
        if override is not None:
            return override.decode() == "enabled"
        
        # Default: enabled
        return True
    
    async def disable_service(
        self,
        service_name: str,
        user_id: UUID,
        reason: str,
        duration_minutes: Optional[int] = None,
    ):
        """
        Manually disable service.
        
        Use cases:
        - Known API outage (1inch down)
        - Maintenance window
        - Rate limit exhausted
        - Cost control
        """
        # Set override
        self.redis.set(f"service:{service_name}:override", "disabled")
        
        # Set expiration if duration provided
        if duration_minutes:
            self.redis.expire(
                f"service:{service_name}:override",
                duration_minutes * 60
            )
        
        # Record telemetry
        await self.telemetry.record_manual_override(
            service_name,
            "disabled",
            user_id,
            reason,
        )
    
    async def enable_service(
        self,
        service_name: str,
        user_id: UUID,
        reason: str,
    ):
        """Manually enable service."""
        # Remove override
        self.redis.delete(f"service:{service_name}:override")
        
        # Record telemetry
        await self.telemetry.record_manual_override(
            service_name,
            "enabled",
            user_id,
            reason,
        )
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get current service status."""
        override = self.redis.get(f"service:{service_name}:override")
        
        return {
            "service_name": service_name,
            "enabled": self.is_enabled(service_name),
            "override": override.decode() if override else None,
            "ttl_seconds": self.redis.ttl(f"service:{service_name}:override"),
        }
```

---

## 📋 Database Schema (Telemetry)

### New Tables:

#### `retry_events`
```sql
CREATE TABLE retry_events (
    id BIGSERIAL PRIMARY KEY,
    
    -- Service identification
    service_name VARCHAR(100) NOT NULL,  -- 'defillama_mcp', '1inch_mcp', etc.
    service_type VARCHAR(50) NOT NULL,   -- 'mcp_server', 'agno_agent', 'external_api'
    
    -- Event details
    event_type VARCHAR(50) NOT NULL,     -- 'attempt_start', 'success', 'failure'
    attempt_number INT NOT NULL,
    
    -- Performance metrics
    latency_ms INT,
    
    -- Error details (if failed)
    error_type VARCHAR(100),
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- Context
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    request_id VARCHAR(100),
    
    -- Additional metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_retry_events_service (service_name, created_at),
    INDEX idx_retry_events_type (event_type, created_at),
    INDEX idx_retry_events_user (user_id, created_at)
);
```

#### `circuit_breaker_events`
```sql
CREATE TABLE circuit_breaker_events (
    id BIGSERIAL PRIMARY KEY,
    
    -- Service identification
    service_name VARCHAR(100) NOT NULL,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL,  -- 'opened', 'closed', 'half_opened'
    previous_state VARCHAR(20),
    new_state VARCHAR(20) NOT NULL,
    
    -- Trigger details
    trigger_reason VARCHAR(255),
    failure_count INT,
    success_count INT,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_circuit_breaker_service (service_name, created_at),
    INDEX idx_circuit_breaker_state (new_state, created_at)
);
```

#### `service_overrides`
```sql
CREATE TABLE service_overrides (
    id BIGSERIAL PRIMARY KEY,
    
    -- Service identification
    service_name VARCHAR(100) NOT NULL,
    
    -- Override details
    action VARCHAR(20) NOT NULL,  -- 'enabled', 'disabled'
    reason TEXT NOT NULL,
    
    -- Who did it
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Duration
    duration_minutes INT,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_service_overrides_service (service_name, is_active),
    INDEX idx_service_overrides_user (user_id, created_at)
);
```

#### `service_health_metrics`
```sql
CREATE TABLE service_health_metrics (
    id BIGSERIAL PRIMARY KEY,
    
    -- Service identification
    service_name VARCHAR(100) NOT NULL,
    
    -- Time window
    time_bucket TIMESTAMP WITH TIME ZONE NOT NULL,  -- 1-minute buckets
    
    -- Request metrics
    total_requests INT DEFAULT 0,
    successful_requests INT DEFAULT 0,
    failed_requests INT DEFAULT 0,
    
    -- Performance metrics
    avg_latency_ms INT,
    p50_latency_ms INT,
    p95_latency_ms INT,
    p99_latency_ms INT,
    
    -- Error distribution
    error_types JSONB,  -- {"rate_limit": 5, "timeout": 2, ...}
    
    -- Retry metrics
    total_retries INT DEFAULT 0,
    successful_retries INT DEFAULT 0,
    
    -- Circuit breaker metrics
    circuit_state VARCHAR(20),
    time_in_state_seconds INT,
    
    -- Cost metrics (for paid APIs)
    estimated_cost_usd NUMERIC(10, 6),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_service_health_service_time (service_name, time_bucket),
    
    -- Unique constraint
    UNIQUE(service_name, time_bucket)
);
```

---

## 🎨 Admin Dashboard (Manual Intervention UI)

### Location: `src/app/presentation/http/controllers/admin/retry/`

### Endpoints:

#### 1. Get Service Health
```http
GET /api/v1/admin/retry/services
```

**Response:**
```json
{
  "services": [
    {
      "service_name": "defillama_mcp",
      "service_type": "mcp_server",
      "enabled": true,
      "circuit_state": "closed",
      "health": {
        "success_rate": 0.98,
        "avg_latency_ms": 450,
        "error_rate": 0.02,
        "last_failure": "2025-12-01T10:30:00Z"
      },
      "metrics_24h": {
        "total_requests": 1250,
        "successful_requests": 1225,
        "failed_requests": 25,
        "total_retries": 45,
        "estimated_cost_usd": 0.0
      }
    },
    {
      "service_name": "oneinch_mcp",
      "service_type": "mcp_server",
      "enabled": false,
      "manual_override": {
        "action": "disabled",
        "reason": "1inch API outage - https://status.1inch.io/incidents/123",
        "disabled_by": "admin@anvil.com",
        "disabled_at": "2025-12-01T09:00:00Z",
        "expires_at": "2025-12-01T12:00:00Z"
      },
      "circuit_state": "open",
      "health": {
        "success_rate": 0.15,
        "avg_latency_ms": null,
        "error_rate": 0.85,
        "last_failure": "2025-12-01T09:15:00Z"
      }
    }
  ]
}
```

#### 2. Disable Service (Manual Override)
```http
POST /api/v1/admin/retry/services/{service_name}/disable
```

**Request:**
```json
{
  "reason": "1inch API experiencing outage - https://status.1inch.io/incidents/123",
  "duration_minutes": 180  // Optional: Auto re-enable after 3 hours
}
```

**Response:**
```json
{
  "success": true,
  "service_name": "oneinch_mcp",
  "action": "disabled",
  "disabled_at": "2025-12-01T09:00:00Z",
  "expires_at": "2025-12-01T12:00:00Z",
  "message": "Service manually disabled for 180 minutes"
}
```

#### 3. Enable Service (Manual Override)
```http
POST /api/v1/admin/retry/services/{service_name}/enable
```

**Request:**
```json
{
  "reason": "1inch API back online - verified via status page"
}
```

**Response:**
```json
{
  "success": true,
  "service_name": "oneinch_mcp",
  "action": "enabled",
  "enabled_at": "2025-12-01T12:00:00Z",
  "message": "Service manually enabled"
}
```

#### 4. Get Service Metrics
```http
GET /api/v1/admin/retry/services/{service_name}/metrics?period=24h
```

**Response:**
```json
{
  "service_name": "defillama_mcp",
  "period": "24h",
  "summary": {
    "total_requests": 1250,
    "successful_requests": 1225,
    "failed_requests": 25,
    "success_rate": 0.98,
    "total_retries": 45,
    "retry_success_rate": 0.80,
    "avg_latency_ms": 450,
    "p95_latency_ms": 850,
    "p99_latency_ms": 1200
  },
  "errors": [
    {
      "error_type": "timeout",
      "count": 15,
      "percentage": 0.60
    },
    {
      "error_type": "rate_limit",
      "count": 10,
      "percentage": 0.40
    }
  ],
  "circuit_breaker": {
    "total_opens": 2,
    "total_closes": 2,
    "current_state": "closed",
    "time_in_open_minutes": 15
  },
  "time_series": [
    {
      "timestamp": "2025-12-01T00:00:00Z",
      "requests": 52,
      "success_rate": 0.98,
      "avg_latency_ms": 420
    }
    // ... hourly buckets
  ]
}
```

#### 5. Get Circuit Breaker History
```http
GET /api/v1/admin/retry/circuit-breaker/history?service={service_name}&period=7d
```

**Response:**
```json
{
  "service_name": "oneinch_mcp",
  "period": "7d",
  "events": [
    {
      "id": 123,
      "event_type": "opened",
      "previous_state": "closed",
      "new_state": "open",
      "trigger_reason": "failure_threshold_exceeded",
      "failure_count": 5,
      "created_at": "2025-12-01T09:00:00Z"
    },
    {
      "id": 124,
      "event_type": "half_opened",
      "previous_state": "open",
      "new_state": "half_open",
      "trigger_reason": "timeout_expired",
      "created_at": "2025-12-01T09:01:00Z"
    },
    {
      "id": 125,
      "event_type": "opened",
      "previous_state": "half_open",
      "new_state": "open",
      "trigger_reason": "failure_in_half_open",
      "created_at": "2025-12-01T09:01:05Z"
    }
  ]
}
```

---

## 🔧 Configuration

### MCP Retry Config (Updated)

**Location:** `config/local/config.toml`

```toml
[mcp.retry]
# Retry behavior
enabled = true
max_retries = 3
initial_backoff_seconds = 2
max_backoff_seconds = 10
exponential_base = 2
jitter = true

# Circuit breaker
circuit_breaker_enabled = true
circuit_failure_threshold = 5
circuit_success_threshold = 2
circuit_timeout_seconds = 60
circuit_half_open_max_calls = 3

# Telemetry
telemetry_enabled = true
telemetry_batch_size = 100
telemetry_flush_interval_seconds = 60

# Manual override
allow_manual_override = true
```

### Agno Retry Config (Updated)

```toml
[agno.retry]
# Retry behavior
enabled = true
max_retries = 2
initial_backoff_seconds = 1
max_backoff_seconds = 5
exponential_base = 2
jitter = true

# Circuit breaker
circuit_breaker_enabled = true
circuit_failure_threshold = 3
circuit_success_threshold = 2
circuit_timeout_seconds = 30

# Telemetry
telemetry_enabled = true
```

---

## 📈 Telemetry Metrics

### Real-Time Metrics (Redis):
- Circuit breaker state per service
- Manual override status
- Current failure counts
- Last error timestamps

### Persistent Metrics (PostgreSQL):
- Retry attempts (all attempts logged)
- Success/failure rates (per service, per hour)
- Latency percentiles (P50, P95, P99)
- Error distribution (by type)
- Circuit breaker events (open, close, half-open)
- Manual overrides (who, when, why)
- Cost per service (API calls)

### Dashboard Visualizations:
1. **Service Health Overview**
   - Grid of all services (green = healthy, yellow = degraded, red = down)
   - Circuit breaker states
   - Manual override indicators

2. **Retry Success Rate (24h)**
   - Line chart showing success rate over time
   - Overlaid with circuit breaker events

3. **Error Distribution**
   - Pie chart of error types
   - Bar chart of errors per service

4. **Latency Trends**
   - Line chart of P50/P95/P99 latency
   - Per-service breakdown

5. **Cost Tracking**
   - Bar chart of cost per service
   - Total cost trend over time

6. **Manual Intervention Log**
   - Table of recent overrides
   - Who disabled/enabled services and why

---

## 🚀 Implementation Plan

### Phase 1: Core Retry Infrastructure (3-4 hours)

#### Task 1.1: Add tenacity dependency
- Update `pyproject.toml`
- Install: `uv pip install tenacity`

#### Task 1.2: Create EnterpriseRetryEngine
- File: `src/app/domain/services/retry/retry_engine.py`
- Implement exponential backoff + jitter
- Integrate circuit breaker
- Integrate telemetry
- Add manual override support

#### Task 1.3: Create CircuitBreaker
- File: `src/app/domain/services/retry/circuit_breaker.py`
- Implement state machine (CLOSED → OPEN → HALF_OPEN)
- Redis-backed state storage
- Telemetry integration

#### Task 1.4: Create ServiceRegistry
- File: `src/app/domain/services/retry/service_registry.py`
- Manual enable/disable
- Expiration support
- Telemetry integration

#### Task 1.5: Update Retry Config
- File: `src/app/setup/config/retry.py`
- Create `RetryConfig` Pydantic model
- Add circuit breaker settings
- Add telemetry settings

#### Task 1.6: Integration Tests
- File: `tests/integration/retry/test_retry_engine.py`
- Test exponential backoff
- Test circuit breaker transitions
- Test manual overrides
- Test telemetry recording

**Deliverables:**
- ✅ Enterprise retry engine with circuit breaker
- ✅ Service registry with manual override
- ✅ Configuration models
- ✅ Integration tests

---

### Phase 2: MCP Server Retry (2-3 hours)

#### Task 2.1: Create MCPServerBase with retry
- File: `src/app/infrastructure/mcp/base_retry.py`
- Base class with `@retry` decorators
- Integrate with EnterpriseRetryEngine

#### Task 2.2: Update all 6 MCP servers
- Inherit from MCPServerBase
- Remove manual try/catch
- Let retry engine handle failures

#### Task 2.3: Update MCPSettings
- Add retry configuration fields
- Document new flags

#### Task 2.4: Integration Tests
- File: `tests/integration/mcp/test_mcp_retry.py`
- Test retry behavior per server
- Test circuit breaker opens on failures
- Test manual override blocks requests

**Deliverables:**
- ✅ All 6 MCP servers with enterprise retry
- ✅ Circuit breaker integration
- ✅ Manual override support
- ✅ Integration tests

---

### Phase 3: Agno Agent Retry (2-3 hours)

#### Task 3.1: Update DeFiAgentBase
- File: `src/app/infrastructure/agno/base_agent.py`
- Add retry to `call_mcp_tool()`
- Integrate with EnterpriseRetryEngine

#### Task 3.2: Update AgnoSettings
- Add retry configuration fields

#### Task 3.3: Integration Tests
- File: `tests/integration/agno/test_agent_retry.py`
- Test MCP tool call retry
- Test circuit breaker for agents

**Deliverables:**
- ✅ Agno agents with MCP tool retry
- ✅ Circuit breaker integration
- ✅ Integration tests

---

### Phase 4: Telemetry Infrastructure (3-4 hours)

#### Task 4.1: Create Database Schema
- Migration: `2025_12_01_1500-retry_telemetry_schema.py`
- Create tables: `retry_events`, `circuit_breaker_events`, `service_overrides`, `service_health_metrics`

#### Task 4.2: Create RetryTelemetryCollector
- File: `src/app/domain/services/retry/telemetry_collector.py`
- Implement event recording methods
- PostgreSQL persistence

#### Task 4.3: Create Telemetry Repository
- File: `src/app/infrastructure/persistence_sqla/repositories/retry_telemetry_repository.py`
- CRUD operations for telemetry tables
- Query methods for dashboard

#### Task 4.4: Integrate Telemetry into Retry Engine
- Update `EnterpriseRetryEngine` to record events
- Update `CircuitBreaker` to record events

**Deliverables:**
- ✅ Complete telemetry database schema
- ✅ Telemetry collector with persistence
- ✅ Repository for telemetry queries
- ✅ Integration with retry engine

---

### Phase 5: Admin Dashboard & Manual Intervention (4-5 hours)

#### Task 5.1: Create Admin Retry Controller
- File: `src/app/presentation/http/controllers/admin/retry/router.py`
- Endpoints: GET services, POST disable, POST enable, GET metrics, GET circuit-breaker history

#### Task 5.2: Create Interactors
- File: `src/app/application/admin/retry/get_services_health.py`
- File: `src/app/application/admin/retry/disable_service.py`
- File: `src/app/application/admin/retry/enable_service.py`
- File: `src/app/application/admin/retry/get_service_metrics.py`

#### Task 5.3: Create Response Models
- File: `src/app/presentation/http/schemas/admin/retry.py`
- Models: `ServiceHealthResponse`, `ServiceMetricsResponse`, `CircuitBreakerEventResponse`

#### Task 5.4: Create Frontend Dashboard (Basic)
- File: `docs/frontend/ADMIN_RETRY_DASHBOARD.md`
- Specification for frontend team
- API integration guide
- Component breakdown

#### Task 5.5: Integration Tests
- File: `tests/integration/admin/test_retry_admin.py`
- Test all admin endpoints
- Test authorization (admin-only)

**Deliverables:**
- ✅ Complete admin API for manual intervention
- ✅ Frontend documentation
- ✅ Authorization checks (admin-only)
- ✅ Integration tests

---

### Phase 6: Error Standardization (2-3 hours)

#### Task 6.1: Create MCP Exception Hierarchy
- File: `src/app/infrastructure/mcp/exceptions.py`
- `MCPError`, `MCPRateLimitError`, `MCPServiceUnavailableError`, `MCPAuthenticationError`, etc.

#### Task 6.2: Update all MCP servers to use standard exceptions
- Replace generic `httpx.HTTPError` with specific exceptions

#### Task 6.3: Update error classification in RetryEngine
- Map exceptions to retryable/non-retryable

#### Task 6.4: Integration Tests
- File: `tests/integration/mcp/test_mcp_errors.py`
- Test error classification
- Test retryable vs non-retryable errors

**Deliverables:**
- ✅ Standard exception hierarchy
- ✅ All MCP servers using standard exceptions
- ✅ Improved error classification
- ✅ Integration tests

---

### Phase 7: Documentation & Deployment (2-3 hours)

#### Task 7.1: Update Main Documentation
- File: `docs/RETRY_SYSTEM.md`
- Complete guide for developers
- Configuration examples
- Troubleshooting guide

#### Task 7.2: Update Frontend Documentation
- File: `docs/frontend/ADMIN_RETRY_DASHBOARD.md`
- Admin dashboard specification
- API integration guide
- Component designs

#### Task 7.3: Create Runbook
- File: `docs/ops/RETRY_SYSTEM_RUNBOOK.md`
- How to handle service outages
- When to manually disable services
- How to monitor health

#### Task 7.4: Update Configuration Examples
- Update `config/local/config.toml`
- Update `config/prod/config.toml`

#### Task 7.5: Create Migration Guide
- File: `docs/MIGRATION_RETRY_SYSTEM.md`
- How existing code will be affected
- Breaking changes (none expected)

**Deliverables:**
- ✅ Complete developer documentation
- ✅ Frontend integration docs
- ✅ Operations runbook
- ✅ Configuration examples
- ✅ Migration guide

---

## 📊 Summary

### Total Effort:
- **Phase 1:** Core Retry Infrastructure (3-4 hours)
- **Phase 2:** MCP Server Retry (2-3 hours)
- **Phase 3:** Agno Agent Retry (2-3 hours)
- **Phase 4:** Telemetry Infrastructure (3-4 hours)
- **Phase 5:** Admin Dashboard (4-5 hours)
- **Phase 6:** Error Standardization (2-3 hours)
- **Phase 7:** Documentation (2-3 hours)

**TOTAL: 18-25 hours** (3-4 days for 1 developer)

### Deliverables:
- ✅ Enterprise retry engine with exponential backoff
- ✅ Circuit breaker pattern (CLOSED → OPEN → HALF_OPEN)
- ✅ Comprehensive telemetry (retry events, circuit breaker events, service health)
- ✅ Manual intervention system (disable/enable services)
- ✅ Admin dashboard API (service health, metrics, manual override)
- ✅ Standard exception hierarchy
- ✅ Complete documentation (developer, frontend, ops)
- ✅ Integration tests (60+ tests)

### Expected Impact:
- **Reliability:** 85% → 98% success rate (+13%)
- **User Errors:** 15% → 3% (-80%)
- **Observability:** 0% → 100% (full visibility)
- **Manual Control:** 0% → 100% (intervention capability)
- **Cost Optimization:** Prevent wasted API calls during outages

### Business Value:
- 🚀 **Self-healing system** (automatic retry + circuit breaker)
- 📊 **Complete observability** (all retry attempts tracked)
- 🎛️ **Manual control** (disable services during outages)
- 💰 **Cost savings** (prevent wasted API calls)
- 😊 **Better UX** (fewer user-visible errors)
- 🔧 **Ops-friendly** (clear dashboard, easy intervention)

---

**Document Version:** 2.0  
**Created:** December 1, 2025  
**Status:** READY FOR IMPLEMENTATION 🚀
