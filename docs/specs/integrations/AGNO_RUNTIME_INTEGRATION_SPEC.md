# Agno Runtime Integration - Enterprise Specification

**Document**: Agno-001  
**Version**: 1.0.0  
**Date**: December 1, 2025  
**Status**: 🔴 **Priority 0** - Ready for Implementation  
**Owner**: CTO

---

## 🎯 Executive Summary

**Agno** is a high-performance agent runtime that provides **microsecond (µs) agent instantiation**, built-in MCP tool integration, and memory efficiency. This specification defines the enterprise-grade integration of Agno into Anvil's AI platform.

### Business Value

- **10x Scalability**: 1k → 50k concurrent users
- **10,000x Faster**: µs instantiation vs ms
- **Memory Efficient**: 10k agents vs 1k (current)
- **Performance**: 400ms average response (vs 1,500ms)
- **Cost**: Same infrastructure, 50x capacity

### Timeline & Investment

- **Timeline**: 3 weeks (120 hours)
- **Complexity**: ⚠️ Medium
- **Investment**: $18,000
- **ROI**: 90 days (infrastructure cost savings)

---

## 1. Feature Control & Configuration

### 1.1 Environment Variables

**Required Configuration** (`.env` / `config.toml`):

```toml
# ========================================
# Agno Runtime Configuration
# ========================================

[agno]
# Feature toggle - Master switch for Agno runtime
enabled = true  # Set to false to disable and use legacy agent system

# Agent pool configuration
pool_size = 10000                    # Maximum concurrent agents
pool_warmup_count = 100              # Pre-warmed agents at startup
pool_eviction_timeout_seconds = 300  # Evict idle agents after 5 minutes

# MCP tools configuration
mcp_defi_url = "http://localhost:8080/mcp/defi"        # DeFi tools MCP server
mcp_internal_url = "http://localhost:8080/mcp/internal" # Internal tools MCP server
mcp_timeout_seconds = 30                                # MCP call timeout

# Performance settings
max_concurrent_executions = 5000  # Max parallel agent executions
execution_timeout_seconds = 60    # Individual agent execution timeout
streaming_enabled = true          # Enable streaming responses

# Telemetry
telemetry_enabled = true
telemetry_sample_rate = 1.0  # 1.0 = 100% of requests

# Fallback behavior
fallback_to_legacy = true  # If Agno fails, fallback to legacy system
fallback_threshold_errors = 3  # Switch to legacy after N consecutive errors
```

**Environment Variable Overrides**:

```bash
# Feature toggle
AGNO_ENABLED=true

# Pool configuration
AGNO_POOL_SIZE=10000
AGNO_POOL_WARMUP_COUNT=100
AGNO_POOL_EVICTION_TIMEOUT_SECONDS=300

# MCP endpoints
AGNO_MCP_DEFI_URL=http://localhost:8080/mcp/defi
AGNO_MCP_INTERNAL_URL=http://localhost:8080/mcp/internal
AGNO_MCP_TIMEOUT_SECONDS=30

# Performance
AGNO_MAX_CONCURRENT_EXECUTIONS=5000
AGNO_EXECUTION_TIMEOUT_SECONDS=60
AGNO_STREAMING_ENABLED=true

# Telemetry
AGNO_TELEMETRY_ENABLED=true
AGNO_TELEMETRY_SAMPLE_RATE=1.0

# Fallback
AGNO_FALLBACK_TO_LEGACY=true
AGNO_FALLBACK_THRESHOLD_ERRORS=3
```

### 1.2 Feature Flag Implementation

```python
# src/app/setup/config/agno.py

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class AgnoPoolSettings(BaseModel):
    """Agent pool configuration."""
    size: int = Field(default=10000, ge=1, le=100000)
    warmup_count: int = Field(default=100, ge=0)
    eviction_timeout_seconds: int = Field(default=300, ge=60)

class AgnoMCPSettings(BaseModel):
    """MCP tools configuration."""
    defi_url: str = "http://localhost:8080/mcp/defi"
    internal_url: str = "http://localhost:8080/mcp/internal"
    timeout_seconds: int = Field(default=30, ge=5, le=300)

class AgnoPerformanceSettings(BaseModel):
    """Performance settings."""
    max_concurrent_executions: int = Field(default=5000, ge=100)
    execution_timeout_seconds: int = Field(default=60, ge=10)
    streaming_enabled: bool = True

class AgnoTelemetrySettings(BaseModel):
    """Telemetry settings."""
    enabled: bool = True
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)

class AgnoFallbackSettings(BaseModel):
    """Fallback behavior settings."""
    to_legacy: bool = True
    threshold_errors: int = Field(default=3, ge=1)

class AgnoSettings(BaseSettings):
    """Complete Agno runtime configuration."""
    enabled: bool = Field(default=True, description="Master feature toggle")
    pool: AgnoPoolSettings = Field(default_factory=AgnoPoolSettings)
    mcp: AgnoMCPSettings = Field(default_factory=AgnoMCPSettings)
    performance: AgnoPerformanceSettings = Field(default_factory=AgnoPerformanceSettings)
    telemetry: AgnoTelemetrySettings = Field(default_factory=AgnoTelemetrySettings)
    fallback: AgnoFallbackSettings = Field(default_factory=AgnoFallbackSettings)

    class Config:
        env_prefix = "AGNO_"
        case_sensitive = False
```

---

## 2. Use Cases

### 2.1 High-Frequency Trading Users

**Scenario**: 10,000 concurrent users analyzing market conditions during volatility spike.

**Current System**: 
- Crashes at ~1,000 concurrent users
- 1,500ms average response time
- High memory consumption (80% at 1k users)

**With Agno**:
- Handles 10,000+ concurrent users
- 400ms average response time
- Low memory footprint (30% at 10k users)

**Implementation**:
```python
# Fast agent spawning for market analysis
agent = await agno_runtime.get_or_create_agent(
    agent_type="hunter_ai",
    model_id="gpt-4-turbo"
)

response = await agent.execute(
    message="Analyze ETH price action in the last 5 minutes",
    user_id=user_id,
    tools=["1inch_price", "defillama_tvl"]
)
```

### 2.2 Real-Time Flash Crash Analysis

**Scenario**: Market flash crash detected, need to spawn 5,000 risk analysis agents instantly.

**Current System**:
- Sequential agent creation (5,000 × 100ms = 500 seconds)
- Memory exhaustion after ~1,000 agents

**With Agno**:
- Parallel agent creation (5,000 × 1µs = 5ms)
- Pre-warmed pool instantly available

**Implementation**:
```python
# Instant mass spawning
tasks = []
for user_id in affected_users:
    agent = await agno_runtime.get_or_create_agent(
        agent_type="risk_analyzer",
        model_id="claude-3-opus"
    )
    tasks.append(agent.execute(
        message="Assess portfolio risk given ETH -40% crash",
        user_id=user_id
    ))

results = await asyncio.gather(*tasks)  # All execute in parallel
```

### 2.3 Multi-Turn Conversation with Tool Use

**Scenario**: User requests complex multi-step analysis with DeFi protocol data.

**Current System**:
- Each turn creates new agent instance (slow)
- Tool calls require custom integration
- No state preservation

**With Agno**:
- Agent instance reused (µs retrieval)
- MCP tools built-in
- Conversation state maintained

**Implementation**:
```python
# Turn 1: Initial query
agent = await agno_runtime.get_or_create_agent(
    agent_type="research",
    model_id="gpt-4"
)

response1 = await agent.execute(
    message="What's the APY on Aave USDC?",
    user_id=user_id,
    conversation_id=conv_id,
    tools=["aave_pool_apy"]
)

# Turn 2: Follow-up (same agent, instant retrieval)
response2 = await agent.execute(
    message="Compare that to Compound",
    user_id=user_id,
    conversation_id=conv_id,
    tools=["compound_pool_apy"]
)
```

### 2.4 Streaming Response for Long Analysis

**Scenario**: User requests deep protocol analysis, wants real-time progress.

**Current System**:
- No streaming support
- User waits for full response (30+ seconds)

**With Agno**:
- Built-in streaming
- Real-time token delivery
- Better UX

**Implementation**:
```python
agent = await agno_runtime.get_or_create_agent(
    agent_type="research",
    model_id="gpt-4"
)

async for chunk in agent.stream(
    message="Deep dive into Aave v3 risk parameters",
    user_id=user_id
):
    await websocket.send_json({
        "type": "chunk",
        "content": chunk.content
    })
```

---

## 3. API Endpoints

### 3.1 User Endpoints

#### **POST /api/v1/chat/message** (Enhanced)

Execute agent request using Agno runtime.

**Request**:
```json
{
  "conversation_id": "uuid",
  "message": "What's the best yield farming strategy?",
  "agent_type": "yield_optimizer",
  "streaming": true
}
```

**Response** (Non-streaming):
```json
{
  "message_id": "uuid",
  "content": "Based on current market conditions...",
  "agent_type": "yield_optimizer",
  "model_used": "gpt-4-turbo",
  "tools_used": ["defillama_pool_apy", "aave_rates"],
  "latency_ms": 420,
  "runtime": "agno",
  "created_at": "2025-12-01T10:30:00Z"
}
```

**Response** (Streaming):
```
event: message_start
data: {"message_id": "uuid", "agent_type": "yield_optimizer"}

event: content_chunk
data: {"content": "Based on"}

event: content_chunk
data: {"content": " current market"}

event: tool_call
data: {"tool": "defillama_pool_apy", "args": {"protocol": "aave"}}

event: tool_result
data: {"tool": "defillama_pool_apy", "result": {"apy": 5.67}}

event: content_chunk
data: {"content": " conditions..."}

event: message_end
data: {"latency_ms": 420, "tokens_used": 350}
```

#### **GET /api/v1/chat/agent-status**

Check Agno runtime health and agent pool status.

**Response**:
```json
{
  "runtime": "agno",
  "enabled": true,
  "status": "healthy",
  "pool": {
    "total_capacity": 10000,
    "active_agents": 3452,
    "available_agents": 6548,
    "warmup_agents": 100
  },
  "performance": {
    "avg_instantiation_us": 0.8,
    "avg_execution_ms": 420,
    "p95_execution_ms": 850,
    "p99_execution_ms": 1200
  },
  "mcp_tools": {
    "defi": {
      "status": "healthy",
      "url": "http://localhost:8080/mcp/defi",
      "tools_available": 15
    },
    "internal": {
      "status": "healthy",
      "url": "http://localhost:8080/mcp/internal",
      "tools_available": 8
    }
  }
}
```

---

### 3.2 Admin Endpoints

#### **GET /api/v1/admin/agno/status**

Comprehensive Agno runtime status.

**Authentication**: Admin only

**Response**:
```json
{
  "enabled": true,
  "status": "healthy",
  "uptime_seconds": 86400,
  "pool": {
    "total_capacity": 10000,
    "active_agents": 3452,
    "available_agents": 6548,
    "warmup_agents": 100,
    "evicted_last_hour": 42,
    "created_last_hour": 158
  },
  "performance": {
    "avg_instantiation_us": 0.8,
    "avg_execution_ms": 420,
    "concurrent_executions": 234,
    "max_concurrent_executions": 5000,
    "executions_last_hour": 12450
  },
  "mcp_tools": {
    "defi": {
      "status": "healthy",
      "url": "http://localhost:8080/mcp/defi",
      "tools_available": 15,
      "calls_last_hour": 5678,
      "avg_latency_ms": 45,
      "error_rate": 0.002
    },
    "internal": {
      "status": "healthy",
      "url": "http://localhost:8080/mcp/internal",
      "tools_available": 8,
      "calls_last_hour": 3421,
      "avg_latency_ms": 23,
      "error_rate": 0.001
    }
  },
  "telemetry": {
    "enabled": true,
    "sample_rate": 1.0,
    "records_last_hour": 12450
  },
  "fallback": {
    "to_legacy": true,
    "threshold_errors": 3,
    "consecutive_errors": 0,
    "fallback_active": false,
    "fallback_activations_last_24h": 0
  }
}
```

#### **POST /api/v1/admin/agno/enable**

Enable Agno runtime.

**Authentication**: Admin only

**Request**:
```json
{
  "warmup_pool": true
}
```

**Response**:
```json
{
  "enabled": true,
  "pool_warmup_started": true,
  "estimated_warmup_time_seconds": 5
}
```

#### **POST /api/v1/admin/agno/disable**

Disable Agno runtime (fallback to legacy).

**Authentication**: Admin only

**Request**:
```json
{
  "drain_existing_agents": true,
  "drain_timeout_seconds": 60
}
```

**Response**:
```json
{
  "enabled": false,
  "drained_agents": 3452,
  "fallback_active": true
}
```

#### **POST /api/v1/admin/agno/pool/resize**

Resize agent pool capacity.

**Authentication**: Admin only

**Request**:
```json
{
  "new_size": 20000,
  "warmup_count": 200
}
```

**Response**:
```json
{
  "old_size": 10000,
  "new_size": 20000,
  "warmup_count": 200,
  "resize_started": true
}
```

#### **POST /api/v1/admin/agno/pool/clear**

Clear all agents from pool (force recreation).

**Authentication**: Admin only

**Response**:
```json
{
  "agents_cleared": 3452,
  "pool_size": 10000,
  "warmup_started": true
}
```

#### **GET /api/v1/admin/agno/metrics**

Detailed performance metrics.

**Authentication**: Admin only

**Query Parameters**:
- `period`: `1h`, `24h`, `7d`, `30d` (default: `24h`)

**Response**:
```json
{
  "period": "24h",
  "total_executions": 298800,
  "successful_executions": 297600,
  "failed_executions": 1200,
  "success_rate": 0.996,
  "performance": {
    "avg_instantiation_us": 0.8,
    "p50_execution_ms": 380,
    "p95_execution_ms": 850,
    "p99_execution_ms": 1200,
    "max_execution_ms": 5400
  },
  "by_agent_type": {
    "chat": {
      "executions": 150000,
      "avg_latency_ms": 300,
      "success_rate": 0.998
    },
    "hunter_ai": {
      "executions": 80000,
      "avg_latency_ms": 650,
      "success_rate": 0.995
    },
    "research": {
      "executions": 40000,
      "avg_latency_ms": 1200,
      "success_rate": 0.993
    }
  },
  "mcp_tools": {
    "total_calls": 450000,
    "avg_latency_ms": 38,
    "by_tool": {
      "1inch_price": {"calls": 120000, "avg_latency_ms": 25},
      "defillama_tvl": {"calls": 80000, "avg_latency_ms": 45},
      "aave_pool_apy": {"calls": 60000, "avg_latency_ms": 52}
    }
  }
}
```

---

## 4. Database Schema

### 4.1 New Tables

#### **agno_agent_pool**

Tracks agent pool state and configuration.

```sql
CREATE TABLE agno_agent_pool (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(50) NOT NULL,
    model_id UUID NOT NULL REFERENCES llm_models(id),
    agent_cache_key VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    execution_count INTEGER NOT NULL DEFAULT 0,
    total_latency_ms INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    -- Index for fast lookups
    INDEX idx_agent_cache_key ON agno_agent_pool(agent_cache_key),
    INDEX idx_agent_type_model ON agno_agent_pool(agent_type, model_id),
    INDEX idx_last_used ON agno_agent_pool(last_used_at)
);

-- Status enum: 'active', 'idle', 'evicted'
```

#### **agno_execution_telemetry**

Detailed telemetry for Agno agent executions.

```sql
CREATE TABLE agno_execution_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    agent_type VARCHAR(50) NOT NULL,
    model_id UUID NOT NULL REFERENCES llm_models(id),
    agent_cache_key VARCHAR(255),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    instantiation_time_us NUMERIC(10, 2),  -- Microseconds
    execution_time_ms INTEGER,
    
    -- Request details
    message_length INTEGER,
    streaming_enabled BOOLEAN,
    
    -- Tool usage
    tools_requested TEXT[],
    tools_executed TEXT[],
    tool_calls_count INTEGER DEFAULT 0,
    total_tool_latency_ms INTEGER DEFAULT 0,
    
    -- Response details
    response_length INTEGER,
    tokens_used INTEGER,
    cost_usd NUMERIC(10, 6),
    
    -- Status
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'timeout'
    error_type VARCHAR(100),
    error_message TEXT,
    
    -- Indexes
    INDEX idx_user_id ON agno_execution_telemetry(user_id),
    INDEX idx_agent_type ON agno_execution_telemetry(agent_type),
    INDEX idx_started_at ON agno_execution_telemetry(started_at),
    INDEX idx_status ON agno_execution_telemetry(status)
);
```

#### **agno_mcp_tool_calls**

MCP tool call tracking for debugging and optimization.

```sql
CREATE TABLE agno_mcp_tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES agno_execution_telemetry(execution_id),
    tool_name VARCHAR(100) NOT NULL,
    tool_args JSONB,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    latency_ms INTEGER,
    
    -- Result
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'timeout'
    result JSONB,
    error_message TEXT,
    
    -- MCP server info
    mcp_server_url VARCHAR(255),
    
    -- Indexes
    INDEX idx_execution_id ON agno_mcp_tool_calls(execution_id),
    INDEX idx_tool_name ON agno_mcp_tool_calls(tool_name),
    INDEX idx_started_at ON agno_mcp_tool_calls(started_at)
);
```

### 4.2 Materialized Views

#### **agno_hourly_metrics**

Aggregated hourly performance metrics.

```sql
CREATE MATERIALIZED VIEW agno_hourly_metrics AS
SELECT
    DATE_TRUNC('hour', started_at) AS hour,
    agent_type,
    COUNT(*) AS total_executions,
    COUNT(*) FILTER (WHERE status = 'success') AS successful_executions,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_executions,
    AVG(instantiation_time_us) AS avg_instantiation_us,
    AVG(execution_time_ms) AS avg_execution_ms,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY execution_time_ms) AS p50_execution_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) AS p95_execution_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY execution_time_ms) AS p99_execution_ms,
    MAX(execution_time_ms) AS max_execution_ms,
    SUM(tool_calls_count) AS total_tool_calls,
    AVG(total_tool_latency_ms) AS avg_tool_latency_ms,
    SUM(tokens_used) AS total_tokens_used,
    SUM(cost_usd) AS total_cost_usd
FROM agno_execution_telemetry
WHERE started_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('hour', started_at), agent_type;

-- Refresh every 5 minutes
CREATE UNIQUE INDEX ON agno_hourly_metrics (hour, agent_type);
```

---

## 5. Celery Background Tasks

### 5.1 Pool Maintenance Tasks

#### **Task: agno_pool_eviction**

Evict idle agents from pool to free memory.

**Schedule**: Every 5 minutes

```python
# src/app/infrastructure/celery/tasks/agno_maintenance.py

from celery import Task
from datetime import datetime, timedelta

@celery_app.task(
    name="agno.pool_eviction",
    bind=True
)
def agno_pool_eviction(self: Task):
    """
    Evict idle agents from pool.
    
    Runs every 5 minutes.
    """
    async def runner(container):
        from app.infrastructure.adapters.agno.runtime import AgnoRuntime
        from app.setup.config.agno import AgnoSettings
        
        runtime = await container.get(AgnoRuntime)
        settings = await container.get(AgnoSettings)
        
        if not settings.enabled:
            return {"status": "skipped", "reason": "Agno disabled"}
        
        eviction_threshold = datetime.utcnow() - timedelta(
            seconds=settings.pool.eviction_timeout_seconds
        )
        
        evicted_count = await runtime.evict_idle_agents(
            before=eviction_threshold
        )
        
        logger.info(f"Evicted {evicted_count} idle agents from pool")
        
        return {
            "status": "success",
            "evicted_count": evicted_count,
            "threshold": eviction_threshold.isoformat()
        }
    
    return asyncio.run(_run_task(runner))


# Add to beat schedule
celery_app.conf.beat_schedule = {
    "agno-pool-eviction": {
        "task": "agno.pool_eviction",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    }
}
```

#### **Task: agno_pool_warmup**

Ensure pool has minimum number of warmed-up agents.

**Schedule**: Every 15 minutes

```python
@celery_app.task(
    name="agno.pool_warmup",
    bind=True
)
def agno_pool_warmup(self: Task):
    """
    Ensure pool warmup count is maintained.
    
    Runs every 15 minutes.
    """
    async def runner(container):
        from app.infrastructure.adapters.agno.runtime import AgnoRuntime
        from app.setup.config.agno import AgnoSettings
        
        runtime = await container.get(AgnoRuntime)
        settings = await container.get(AgnoSettings)
        
        if not settings.enabled:
            return {"status": "skipped", "reason": "Agno disabled"}
        
        current_warmup = await runtime.get_warmup_count()
        target_warmup = settings.pool.warmup_count
        
        if current_warmup < target_warmup:
            created = await runtime.warmup_pool(
                count=target_warmup - current_warmup
            )
            logger.info(f"Warmed up {created} agents")
        
        return {
            "status": "success",
            "current_warmup": current_warmup,
            "target_warmup": target_warmup,
            "created": created
        }
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["agno-pool-warmup"] = {
    "task": "agno.pool_warmup",
    "schedule": crontab(minute="*/15"),  # Every 15 minutes
}
```

### 5.2 Metrics Tasks

#### **Task: agno_refresh_metrics**

Refresh materialized view for metrics.

**Schedule**: Every 5 minutes

```python
@celery_app.task(
    name="agno.refresh_metrics",
    bind=True
)
def agno_refresh_metrics(self: Task):
    """
    Refresh agno_hourly_metrics materialized view.
    
    Runs every 5 minutes.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.session import AsyncSession
        
        session = await container.get(AsyncSession)
        
        await session.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY agno_hourly_metrics"
        )
        await session.commit()
        
        logger.info("Refreshed agno_hourly_metrics view")
        
        return {"status": "success"}
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["agno-refresh-metrics"] = {
    "task": "agno.refresh_metrics",
    "schedule": crontab(minute="*/5"),  # Every 5 minutes
}
```

#### **Task: agno_cleanup_old_telemetry**

Archive and delete old telemetry data.

**Schedule**: Daily at 03:00 UTC

```python
@celery_app.task(
    name="agno.cleanup_old_telemetry",
    bind=True
)
def agno_cleanup_old_telemetry(self: Task):
    """
    Archive telemetry older than 90 days.
    
    Runs daily at 03:00 UTC.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.session import AsyncSession
        from datetime import datetime, timedelta
        
        session = await container.get(AsyncSession)
        
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Archive to S3 (implementation detail)
        # ... archive logic ...
        
        # Delete from database
        result = await session.execute(
            """
            DELETE FROM agno_execution_telemetry
            WHERE started_at < :cutoff_date
            """,
            {"cutoff_date": cutoff_date}
        )
        deleted_count = result.rowcount
        await session.commit()
        
        logger.info(f"Archived and deleted {deleted_count} old telemetry records")
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["agno-cleanup-old-telemetry"] = {
    "task": "agno.cleanup_old_telemetry",
    "schedule": crontab(hour=3, minute=0),  # Daily at 03:00 UTC
}
```

---

## 6. Integration with Existing Solution

### 6.1 Integration Points

**1. AgentGateway Port** (Domain Layer)

Agno implements the existing `AgentGateway` interface, ensuring zero changes to application layer.

```python
# src/app/domain/ports/ai/agent_gateway.py (Existing)

from typing import Protocol
from uuid import UUID

class AgentGateway(Protocol):
    """Port for agent execution (existing interface)."""
    
    async def process_message(
        self,
        user_id: UUID,
        session_id: str,
        message: str,
        agent_type: str = "chat"
    ) -> AgentResponse:
        """Process user message via agent."""
        ...
```

**Implementation**:

```python
# src/app/infrastructure/adapters/agno/gateway.py (New)

from app.domain.ports.ai.agent_gateway import AgentGateway, AgentResponse
from app.infrastructure.adapters.agno.runtime import AgnoRuntime
from app.domain.services.llm.orchestrator import LLMOrchestrator

class AgnoRuntimeGateway(AgentGateway):
    """AgentGateway implementation using Agno runtime."""
    
    def __init__(
        self,
        runtime: AgnoRuntime,
        orchestrator: LLMOrchestrator,
        settings: AgnoSettings
    ):
        self._runtime = runtime
        self._orchestrator = orchestrator
        self._settings = settings
    
    async def process_message(
        self,
        user_id: UUID,
        session_id: str,
        message: str,
        agent_type: str = "chat"
    ) -> AgentResponse:
        """
        Process message via Agno runtime.
        
        Flow:
        1. Check if Agno enabled
        2. Select best model via LLMOrchestrator
        3. Get/create agent from Agno pool
        4. Execute with MCP tools
        5. Record telemetry
        6. Fallback to legacy on error
        """
        # Check if Agno enabled
        if not self._settings.enabled:
            return await self._legacy_fallback(user_id, session_id, message, agent_type)
        
        try:
            # Select model via orchestrator (existing adaptive ranking)
            selected_model = await self._orchestrator.select_model(
                agent_type=agent_type,
                user_id=user_id
            )
            
            # Execute via Agno
            response = await self._runtime.execute(
                agent_type=agent_type,
                model_id=selected_model.model_id,
                message=message,
                user_id=user_id,
                session_id=session_id
            )
            
            # Record telemetry to orchestrator
            await self._orchestrator.record_execution(
                model_id=selected_model.model_id,
                agent_type=agent_type,
                success=response.success,
                latency_ms=response.latency_ms,
                cost_usd=response.cost_usd
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Agno execution failed: {e}")
            
            # Fallback to legacy if enabled
            if self._settings.fallback.to_legacy:
                return await self._legacy_fallback(user_id, session_id, message, agent_type)
            else:
                raise
```

**2. Dependency Injection** (IOC Container)

Register Agno components in Dishka provider.

```python
# src/app/setup/ioc/agno.py (New)

from dishka import Provider, Scope, provide
from app.infrastructure.adapters.agno.runtime import AgnoRuntime
from app.infrastructure.adapters.agno.gateway import AgnoRuntimeGateway
from app.setup.config.agno import AgnoSettings
from app.domain.ports.ai.agent_gateway import AgentGateway

class AgnoProvider(Provider):
    """Dishka provider for Agno runtime."""
    
    @provide(scope=Scope.APP)
    def get_agno_settings(self, settings: Settings) -> AgnoSettings:
        """Provide Agno settings from main config."""
        return settings.agno
    
    @provide(scope=Scope.APP)
    async def get_agno_runtime(self, settings: AgnoSettings) -> AgnoRuntime:
        """
        Provide Agno runtime (singleton).
        
        Initializes pool on first access.
        """
        runtime = AgnoRuntime(settings)
        await runtime.initialize()
        return runtime
    
    @provide(scope=Scope.REQUEST)
    def get_agent_gateway(
        self,
        runtime: AgnoRuntime,
        orchestrator: LLMOrchestrator,
        settings: AgnoSettings
    ) -> AgentGateway:
        """
        Provide AgentGateway implementation.
        
        Returns AgnoRuntimeGateway if enabled, else LegacyAgentGateway.
        """
        if settings.enabled:
            return AgnoRuntimeGateway(runtime, orchestrator, settings)
        else:
            return LegacyAgentGateway(orchestrator)
```

Register in provider registry:

```python
# src/app/setup/ioc/provider_registry.py (Modified)

from app.setup.ioc.agno import AgnoProvider

def get_providers() -> tuple[Provider, ...]:
    return (
        ApplicationProvider(),
        infrastructure_provider(),
        PresentationProvider(),
        SettingsProvider(),
        LLMRankingProvider(),
        AgnoProvider(),  # NEW
    )
```

**3. LLM Orchestrator Integration** (Existing System)

Agno uses the existing `LLMOrchestrator` for model selection (adaptive ranking).

```python
# src/app/domain/services/llm/orchestrator.py (Existing - No changes)

class LLMOrchestrator:
    """
    Multi-LLM orchestration with adaptive ranking.
    
    Already implemented, no changes needed.
    """
    
    async def select_model(
        self,
        agent_type: str,
        user_id: UUID
    ) -> SelectedModel:
        """
        Select best model for agent type.
        
        Uses adaptive ranking system (already implemented).
        """
        # ... existing logic ...
        pass
    
    async def record_execution(
        self,
        model_id: UUID,
        agent_type: str,
        success: bool,
        latency_ms: int,
        cost_usd: Decimal
    ) -> None:
        """
        Record execution telemetry.
        
        Feeds into adaptive ranking (already implemented).
        """
        # ... existing logic ...
        pass
```

### 6.2 Migration Strategy

**Phase 1: Shadow Mode** (Week 1)

- Deploy Agno with `enabled=false`
- Run in shadow mode (parallel execution, don't use results)
- Compare Agno vs legacy performance
- Validate telemetry collection

**Phase 2: Alpha** (Week 2)

- Enable Agno for 1% of traffic
- Monitor error rates, latency, success rates
- Ensure fallback to legacy works

**Phase 3: Beta** (Week 3)

- Enable for 10% of traffic
- Monitor pool behavior, eviction, warmup
- Validate MCP tool integration

**Phase 4: Production** (Week 4)

- Enable for 50% of traffic
- Monitor at scale
- Full rollout to 100%

**Rollback Plan**:

```bash
# Emergency disable
export AGNO_ENABLED=false

# Or via admin API
curl -X POST https://api.anvil.com/api/v1/admin/agno/disable \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"drain_existing_agents": true}'
```

---

## 7. Monitoring & Alerting

### 7.1 Key Metrics

**Performance**:
- `agno.instantiation.time.us` (histogram, target: <10µs)
- `agno.execution.time.ms` (histogram, target: <500ms p95)
- `agno.pool.size` (gauge)
- `agno.pool.active` (gauge)
- `agno.concurrent.executions` (gauge)

**Health**:
- `agno.execution.success.rate` (gauge, target: >99%)
- `agno.mcp.tool.success.rate` (gauge, target: >98%)
- `agno.fallback.activations` (counter, target: 0)

**Business**:
- `agno.cost.per.execution` (gauge)
- `agno.executions.per.minute` (counter)

### 7.2 Alerts

```yaml
# Prometheus alerts

groups:
  - name: agno_runtime
    rules:
      - alert: AgnoHighErrorRate
        expr: rate(agno_execution_failures[5m]) > 0.01
        for: 5m
        annotations:
          summary: "Agno error rate above 1%"
          
      - alert: AgnoPoolExhausted
        expr: agno_pool_available < 100
        for: 5m
        annotations:
          summary: "Agno pool near exhaustion (<100 available)"
          
      - alert: AgnoHighLatency
        expr: histogram_quantile(0.95, agno_execution_time_ms) > 1000
        for: 10m
        annotations:
          summary: "Agno p95 latency >1s"
          
      - alert: AgnoFallbackActive
        expr: agno_fallback_active == 1
        for: 1m
        annotations:
          summary: "Agno fallback to legacy activated"
```

---

## 8. Success Criteria

### 8.1 Technical Metrics

- ✅ Agent instantiation: <10µs (p95)
- ✅ Execution latency: <500ms (p95)
- ✅ Success rate: >99%
- ✅ Concurrent users: >10,000
- ✅ Pool capacity: 10,000 agents
- ✅ MCP tool success: >98%

### 8.2 Business Metrics

- ✅ Infrastructure cost: Same as before (50x efficiency)
- ✅ User capacity: 1k → 50k (+4,900%)
- ✅ Response time: 1,500ms → 400ms (-73%)
- ✅ Zero downtime migration
- ✅ Fallback to legacy: <1% of requests

---

## 9. Implementation Checklist

### Week 1: Core Integration

- [ ] Create `src/app/infrastructure/adapters/agno/` directory
- [ ] Implement `AgnoRuntime` class
- [ ] Implement `AgnoRuntimeGateway` class
- [ ] Create Agno settings in `src/app/setup/config/agno.py`
- [ ] Create Agno IOC provider
- [ ] Add database migrations for 3 new tables
- [ ] Unit tests for runtime and gateway

### Week 2: MCP Tools & Admin API

- [ ] Implement MCP tools for DeFi (1inch, DeFiLlama, Aave)
- [ ] Implement MCP tools for internal APIs
- [ ] Create 6 admin API endpoints
- [ ] Integration tests for MCP tools
- [ ] Admin API documentation

### Week 3: Celery Tasks & Monitoring

- [ ] Implement 4 Celery maintenance tasks
- [ ] Add Prometheus metrics
- [ ] Configure alerts
- [ ] Create monitoring dashboards
- [ ] Load testing (10k+ concurrent users)

### Week 4: Migration & Documentation

- [ ] Shadow mode deployment
- [ ] Alpha testing (1% traffic)
- [ ] Beta testing (10% traffic)
- [ ] Production rollout (100% traffic)
- [ ] Final documentation
- [ ] Runbook for operations

---

**Document Status**: ✅ Ready for Implementation  
**Next Step**: Create development tasks and start Week 1  
**Timeline**: 3 weeks (120 hours)  
**Investment**: $18,000  
**Expected ROI**: 90 days
