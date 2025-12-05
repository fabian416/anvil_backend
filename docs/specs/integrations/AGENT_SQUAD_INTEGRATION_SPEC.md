# Agent Squad Integration - Enterprise Specification

**Document**: AgentSquad-001  
**Version**: 1.0.0  
**Date**: December 1, 2025  
**Status**: 🔴 **Priority 0** - Ready for Implementation  
**Owner**: CTO

---

## 🎯 Executive Summary

**Agent Squad** is a multi-agent orchestration framework that provides intelligent intent classification, context preservation across multi-turn conversations, and supervisor-based coordination for complex workflows. This specification defines the enterprise-grade integration of Agent Squad into Anvil's AI platform.

### Business Value

- **20% Quality Improvement**: Correct specialist selection
- **30% Engagement Increase**: Better routing, context preservation
- **40% Complex Task Success**: Multi-agent coordination
- **10+ Turn Conversations**: Maintained context, no degradation

### Timeline & Investment

- **Timeline**: 4 weeks (160 hours)
- **Complexity**: ⚠️⚠️ High
- **Investment**: $24,000
- **ROI**: 120 days (engagement & retention)

---

## 1. Feature Control & Configuration

### 1.1 Environment Variables

**Required Configuration** (`.env` / `config.toml`):

```toml
# ========================================
# Agent Squad Configuration
# ========================================

[agent_squad]
# Feature toggle
enabled = true  # Set to false to use single-agent system

# Orchestrator settings
intent_classification_model = "gpt-4o-mini"  # Fast model for routing
intent_confidence_threshold = 0.85           # Min confidence for routing
fallback_agent = "chat"                      # Default if intent unclear

# Agent types
available_agents = [
    "chat",           # General conversation
    "hunter_ai",      # Market analysis
    "research",       # Deep protocol analysis
    "trading",        # Execute swaps
    "risk_analyzer"   # Risk assessment
]

# Supervisor settings
enable_supervisor = true
supervisor_model = "gpt-4o"
supervisor_max_agents = 5
supervisor_timeout_seconds = 120

# Context preservation
conversation_history_limit = 20  # Messages to keep in context
context_window_tokens = 8000     # Max tokens for context

# Performance
max_concurrent_agents = 3        # Parallel agent execution
routing_timeout_seconds = 5      # Intent classification timeout
execution_timeout_seconds = 60   # Individual agent timeout

# Storage
storage_backend = "postgresql"   # "postgresql" or "redis"
storage_ttl_seconds = 86400      # 24 hours

# Telemetry
telemetry_enabled = true
telemetry_sample_rate = 1.0
```

**Environment Variable Overrides**:

```bash
# Feature toggle
AGENT_SQUAD_ENABLED=true

# Orchestrator
AGENT_SQUAD_INTENT_CLASSIFICATION_MODEL=gpt-4o-mini
AGENT_SQUAD_INTENT_CONFIDENCE_THRESHOLD=0.85
AGENT_SQUAD_FALLBACK_AGENT=chat

# Supervisor
AGENT_SQUAD_ENABLE_SUPERVISOR=true
AGENT_SQUAD_SUPERVISOR_MODEL=gpt-4o
AGENT_SQUAD_SUPERVISOR_MAX_AGENTS=5
AGENT_SQUAD_SUPERVISOR_TIMEOUT_SECONDS=120

# Context
AGENT_SQUAD_CONVERSATION_HISTORY_LIMIT=20
AGENT_SQUAD_CONTEXT_WINDOW_TOKENS=8000

# Performance
AGENT_SQUAD_MAX_CONCURRENT_AGENTS=3
AGENT_SQUAD_ROUTING_TIMEOUT_SECONDS=5
AGENT_SQUAD_EXECUTION_TIMEOUT_SECONDS=60

# Storage
AGENT_SQUAD_STORAGE_BACKEND=postgresql
AGENT_SQUAD_STORAGE_TTL_SECONDS=86400

# Telemetry
AGENT_SQUAD_TELEMETRY_ENABLED=true
AGENT_SQUAD_TELEMETRY_SAMPLE_RATE=1.0
```

### 1.2 Feature Flag Implementation

```python
# src/app/setup/config/agent_squad.py

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import List, Literal

class AgentSquadOrchestratorSettings(BaseModel):
    """Intent classification and routing settings."""
    intent_classification_model: str = "gpt-4o-mini"
    intent_confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    fallback_agent: str = "chat"

class AgentSquadSupervisorSettings(BaseModel):
    """Supervisor coordination settings."""
    enable_supervisor: bool = True
    supervisor_model: str = "gpt-4o"
    supervisor_max_agents: int = Field(default=5, ge=1, le=10)
    supervisor_timeout_seconds: int = Field(default=120, ge=30)

class AgentSquadContextSettings(BaseModel):
    """Context preservation settings."""
    conversation_history_limit: int = Field(default=20, ge=5, le=100)
    context_window_tokens: int = Field(default=8000, ge=1000)

class AgentSquadPerformanceSettings(BaseModel):
    """Performance settings."""
    max_concurrent_agents: int = Field(default=3, ge=1, le=10)
    routing_timeout_seconds: int = Field(default=5, ge=1, le=30)
    execution_timeout_seconds: int = Field(default=60, ge=10)

class AgentSquadStorageSettings(BaseModel):
    """Storage backend settings."""
    backend: Literal["postgresql", "redis"] = "postgresql"
    ttl_seconds: int = Field(default=86400, ge=3600)

class AgentSquadTelemetrySettings(BaseModel):
    """Telemetry settings."""
    enabled: bool = True
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)

class AgentSquadSettings(BaseSettings):
    """Complete Agent Squad configuration."""
    enabled: bool = Field(default=True, description="Master feature toggle")
    available_agents: List[str] = Field(
        default=["chat", "hunter_ai", "research", "trading", "risk_analyzer"]
    )
    orchestrator: AgentSquadOrchestratorSettings = Field(default_factory=AgentSquadOrchestratorSettings)
    supervisor: AgentSquadSupervisorSettings = Field(default_factory=AgentSquadSupervisorSettings)
    context: AgentSquadContextSettings = Field(default_factory=AgentSquadContextSettings)
    performance: AgentSquadPerformanceSettings = Field(default_factory=AgentSquadPerformanceSettings)
    storage: AgentSquadStorageSettings = Field(default_factory=AgentSquadStorageSettings)
    telemetry: AgentSquadTelemetrySettings = Field(default_factory=AgentSquadTelemetrySettings)

    class Config:
        env_prefix = "AGENT_SQUAD_"
        case_sensitive = False
```

---

## 2. Use Cases

### 2.1 Simple Intent Routing

**Scenario**: User asks a question, system routes to correct specialist.

**Examples**:
```
User: "What's the APY on Aave USDC?"
→ Routes to: research agent
→ Tools: aave_pool_apy
→ Response time: 800ms

User: "Buy 100 ETH"
→ Routes to: trading agent
→ Tools: 1inch_swap
→ Response time: 1,200ms

User: "How are you today?"
→ Routes to: chat agent
→ Tools: none
→ Response time: 300ms
```

**Implementation**:
```python
# Intent classification happens automatically
response = await agent_squad.execute(
    user_id=user_id,
    conversation_id=conv_id,
    message="What's the APY on Aave USDC?"
)

# Agent Squad:
# 1. Classifies intent → "protocol_query"
# 2. Routes to research agent
# 3. Research agent uses aave_pool_apy tool
# 4. Returns response
```

### 2.2 Multi-Turn Conversation with Context

**Scenario**: User has extended conversation, system maintains context.

**Example**:
```
Turn 1:
User: "What's the APY on Aave USDC?"
Agent (research): "Aave USDC currently offers 5.67% APY."

Turn 2:
User: "How does that compare to Compound?"
Agent (research): "Compound USDC offers 4.23% APY, so Aave is 1.44% higher."
[Context: Previous question was about Aave USDC]

Turn 3:
User: "Should I move my funds?"
Agent (risk_analyzer): "Considering your risk tolerance, I recommend..."
[Context: Previous discussion about Aave vs Compound USDC]
```

**Implementation**:
```python
# Turn 1
response1 = await agent_squad.execute(
    user_id=user_id,
    conversation_id=conv_id,
    message="What's the APY on Aave USDC?"
)
# → Routed to research agent

# Turn 2 (same conversation_id, context preserved)
response2 = await agent_squad.execute(
    user_id=user_id,
    conversation_id=conv_id,  # SAME conversation
    message="How does that compare to Compound?"
)
# → Research agent has context: "Aave USDC"
# → Knows to compare Compound USDC

# Turn 3 (context maintained)
response3 = await agent_squad.execute(
    user_id=user_id,
    conversation_id=conv_id,
    message="Should I move my funds?"
)
# → Routed to risk_analyzer
# → Has full context: Aave 5.67%, Compound 4.23%
```

### 2.3 Supervisor-Coordinated Complex Task

**Scenario**: User requests complex multi-step analysis requiring multiple specialists.

**Example**:
```
User: "Create a balanced DeFi portfolio for me"

Supervisor Agent:
1. Analyzes request → Complex task, needs multiple agents
2. Creates plan:
   - Research Agent: Find top protocols
   - Risk Agent: Assess risk for each
   - Allocation Agent: Suggest allocation
3. Coordinates execution:
   - Research → "Top protocols: Aave, Compound, Lido, Curve"
   - Risk → "Risk scores: Aave 6/10, Compound 5/10, Lido 7/10, Curve 4/10"
   - Allocation → "Suggested: 30% Aave, 30% Compound, 20% Lido, 20% Curve"
4. Aggregates results → Final recommendation
```

**Implementation**:
```python
response = await agent_squad.execute_with_supervisor(
    user_id=user_id,
    conversation_id=conv_id,
    message="Create a balanced DeFi portfolio for me"
)

# Supervisor:
# 1. Creates subtasks
# 2. Delegates to specialists
# 3. Aggregates responses
# 4. Returns unified answer
```

### 2.4 Parallel Agent Execution

**Scenario**: User asks multiple independent questions, execute in parallel.

**Example**:
```
User: "What's the APY on Aave USDC and what's the current ETH price?"

Agent Squad:
1. Identifies 2 independent sub-queries
2. Executes in parallel:
   - Research Agent: "Aave USDC APY" → 600ms
   - Hunter AI: "ETH price" → 400ms
3. Total time: 600ms (not 1,000ms sequential)
```

**Implementation**:
```python
response = await agent_squad.execute(
    user_id=user_id,
    conversation_id=conv_id,
    message="What's the APY on Aave USDC and what's the current ETH price?",
    enable_parallel=True
)

# Agent Squad automatically:
# 1. Detects multiple independent queries
# 2. Routes to different agents
# 3. Executes in parallel
# 4. Aggregates responses
```

---

## 3. API Endpoints

### 3.1 User Endpoints

#### **POST /api/v1/chat/message** (Enhanced with Agent Squad)

Execute message with intelligent agent routing.

**Request**:
```json
{
  "conversation_id": "uuid",
  "message": "What's the best yield farming strategy?",
  "enable_supervisor": false,
  "enable_parallel": true
}
```

**Response**:
```json
{
  "message_id": "uuid",
  "content": "Based on current market conditions...",
  "routed_agent": "research",
  "intent": "protocol_analysis",
  "intent_confidence": 0.95,
  "agents_used": ["research"],
  "tools_used": ["defillama_pool_apy", "aave_rates"],
  "latency_ms": 780,
  "context_preserved": true,
  "conversation_turn": 3,
  "created_at": "2025-12-01T10:30:00Z"
}
```

#### **POST /api/v1/chat/supervisor** (New)

Execute complex task with supervisor coordination.

**Request**:
```json
{
  "conversation_id": "uuid",
  "message": "Create a balanced DeFi portfolio",
  "max_agents": 5,
  "timeout_seconds": 120
}
```

**Response**:
```json
{
  "message_id": "uuid",
  "content": "I've created a balanced portfolio recommendation...",
  "supervisor_plan": [
    {"agent": "research", "task": "Find top protocols", "status": "completed"},
    {"agent": "risk_analyzer", "task": "Assess risks", "status": "completed"},
    {"agent": "allocation", "task": "Suggest allocation", "status": "completed"}
  ],
  "agents_used": ["research", "risk_analyzer", "allocation"],
  "execution_order": "parallel",
  "total_latency_ms": 2400,
  "individual_latencies": {
    "research": 1200,
    "risk_analyzer": 800,
    "allocation": 600
  },
  "created_at": "2025-12-01T10:35:00Z"
}
```

#### **GET /api/v1/chat/conversation/{conversation_id}/context**

Retrieve conversation context and agent routing history.

**Response**:
```json
{
  "conversation_id": "uuid",
  "message_count": 15,
  "context_preserved": true,
  "routing_history": [
    {
      "turn": 1,
      "message": "What's the APY on Aave?",
      "routed_agent": "research",
      "intent": "protocol_query",
      "confidence": 0.98
    },
    {
      "turn": 2,
      "message": "Compare to Compound",
      "routed_agent": "research",
      "intent": "protocol_comparison",
      "confidence": 0.92,
      "used_context": true
    }
  ],
  "agents_used_distribution": {
    "research": 8,
    "hunter_ai": 4,
    "chat": 3
  }
}
```

---

### 3.2 Admin Endpoints

#### **GET /api/v1/admin/agent-squad/status**

Overall system status.

**Authentication**: Admin only

**Response**:
```json
{
  "enabled": true,
  "status": "healthy",
  "orchestrator": {
    "intent_model": "gpt-4o-mini",
    "avg_routing_time_ms": 45,
    "routing_success_rate": 0.97
  },
  "agents": {
    "chat": {"status": "healthy", "executions_last_hour": 1200},
    "hunter_ai": {"status": "healthy", "executions_last_hour": 800},
    "research": {"status": "healthy", "executions_last_hour": 600},
    "trading": {"status": "healthy", "executions_last_hour": 400},
    "risk_analyzer": {"status": "healthy", "executions_last_hour": 300}
  },
  "supervisor": {
    "enabled": true,
    "executions_last_hour": 50,
    "avg_coordination_time_ms": 2200,
    "avg_agents_per_task": 3.2
  },
  "context_preservation": {
    "avg_conversation_length": 6.5,
    "max_conversation_length": 45,
    "context_loss_rate": 0.003
  },
  "storage": {
    "backend": "postgresql",
    "active_conversations": 4500,
    "total_messages_stored": 285000
  }
}
```

#### **POST /api/v1/admin/agent-squad/enable**

Enable Agent Squad.

**Authentication**: Admin only

**Response**:
```json
{
  "enabled": true,
  "status": "Agent Squad enabled"
}
```

#### **POST /api/v1/admin/agent-squad/disable**

Disable Agent Squad (fallback to single-agent).

**Authentication**: Admin only

**Response**:
```json
{
  "enabled": false,
  "status": "Fallback to single-agent system"
}
```

#### **GET /api/v1/admin/agent-squad/metrics**

Detailed performance metrics.

**Authentication**: Admin only

**Query Parameters**:
- `period`: `1h`, `24h`, `7d`, `30d` (default: `24h`)

**Response**:
```json
{
  "period": "24h",
  "total_executions": 45000,
  "routing": {
    "total_classifications": 45000,
    "successful_classifications": 43650,
    "classification_success_rate": 0.97,
    "avg_classification_time_ms": 45,
    "by_intent": {
      "protocol_query": {"count": 15000, "confidence_avg": 0.95},
      "market_analysis": {"count": 12000, "confidence_avg": 0.93},
      "trading_request": {"count": 8000, "confidence_avg": 0.98},
      "general_chat": {"count": 10000, "confidence_avg": 0.89}
    }
  },
  "agents": {
    "research": {
      "executions": 15000,
      "avg_latency_ms": 850,
      "success_rate": 0.98
    },
    "hunter_ai": {
      "executions": 12000,
      "avg_latency_ms": 650,
      "success_rate": 0.96
    },
    "trading": {
      "executions": 8000,
      "avg_latency_ms": 1200,
      "success_rate": 0.97
    },
    "chat": {
      "executions": 10000,
      "avg_latency_ms": 300,
      "success_rate": 0.99
    }
  },
  "supervisor": {
    "total_coordinations": 500,
    "avg_agents_per_task": 3.2,
    "avg_coordination_time_ms": 2200,
    "success_rate": 0.94,
    "most_common_patterns": [
      {"agents": ["research", "risk_analyzer"], "count": 150},
      {"agents": ["research", "trading"], "count": 120}
    ]
  },
  "context_preservation": {
    "conversations_with_context": 4200,
    "avg_turns_per_conversation": 6.5,
    "context_usage_rate": 0.75,
    "context_loss_events": 135
  }
}
```

#### **POST /api/v1/admin/agent-squad/clear-context**

Clear conversation context (for testing or user request).

**Authentication**: Admin only

**Request**:
```json
{
  "conversation_id": "uuid"  // Or "all" for all conversations
}
```

**Response**:
```json
{
  "conversations_cleared": 1,
  "messages_deleted": 15
}
```

---

## 4. Database Schema

### 4.1 New Tables

#### **agent_squad_conversations**

Extended conversation metadata for Agent Squad.

```sql
CREATE TABLE agent_squad_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL UNIQUE REFERENCES conversations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Context tracking
    message_count INTEGER NOT NULL DEFAULT 0,
    context_preserved BOOLEAN NOT NULL DEFAULT TRUE,
    context_window_tokens_used INTEGER NOT NULL DEFAULT 0,
    
    -- Agent usage
    agents_used JSONB NOT NULL DEFAULT '{}',  -- {"research": 5, "hunter_ai": 3}
    primary_agent VARCHAR(50),
    
    -- Supervisor usage
    supervisor_used BOOLEAN NOT NULL DEFAULT FALSE,
    supervisor_coordination_count INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_conversation_id ON agent_squad_conversations(conversation_id),
    INDEX idx_user_id ON agent_squad_conversations(user_id),
    INDEX idx_last_message_at ON agent_squad_conversations(last_message_at)
);
```

#### **agent_squad_routing**

Intent classification and routing history.

```sql
CREATE TABLE agent_squad_routing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_squad_conversations(conversation_id),
    message_id UUID NOT NULL REFERENCES messages(id),
    
    -- Intent classification
    user_message TEXT NOT NULL,
    classified_intent VARCHAR(100) NOT NULL,
    intent_confidence NUMERIC(5, 4) NOT NULL,  -- 0.0000 to 1.0000
    classification_model VARCHAR(50) NOT NULL,
    
    -- Routing decision
    routed_agent VARCHAR(50) NOT NULL,
    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
    routing_latency_ms INTEGER NOT NULL,
    
    -- Context usage
    conversation_turn INTEGER NOT NULL,
    context_used BOOLEAN NOT NULL DEFAULT FALSE,
    context_tokens_used INTEGER,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_conversation_id ON agent_squad_routing(conversation_id),
    INDEX idx_routed_agent ON agent_squad_routing(routed_agent),
    INDEX idx_classified_intent ON agent_squad_routing(classified_intent),
    INDEX idx_created_at ON agent_squad_routing(created_at)
);
```

#### **agent_squad_supervisor_executions**

Supervisor coordination tracking.

```sql
CREATE TABLE agent_squad_supervisor_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_squad_conversations(conversation_id),
    message_id UUID NOT NULL REFERENCES messages(id),
    
    -- Request
    user_message TEXT NOT NULL,
    supervisor_model VARCHAR(50) NOT NULL,
    
    -- Plan
    plan JSONB NOT NULL,  -- [{"agent": "research", "task": "..."}, ...]
    agents_planned VARCHAR(50)[] NOT NULL,
    
    -- Execution
    agents_executed VARCHAR(50)[] NOT NULL,
    execution_order VARCHAR(20) NOT NULL,  -- "sequential" or "parallel"
    
    -- Results
    status VARCHAR(20) NOT NULL,  -- "completed", "partial", "failed"
    aggregated_response TEXT,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    total_latency_ms INTEGER,
    individual_latencies JSONB,  -- {"research": 1200, "risk": 800}
    
    -- Indexes
    INDEX idx_conversation_id ON agent_squad_supervisor_executions(conversation_id),
    INDEX idx_status ON agent_squad_supervisor_executions(status),
    INDEX idx_started_at ON agent_squad_supervisor_executions(started_at)
);
```

### 4.2 Materialized Views

#### **agent_squad_hourly_metrics**

Aggregated routing and agent usage metrics.

```sql
CREATE MATERIALIZED VIEW agent_squad_hourly_metrics AS
SELECT
    DATE_TRUNC('hour', created_at) AS hour,
    routed_agent,
    classified_intent,
    COUNT(*) AS total_routings,
    AVG(intent_confidence) AS avg_confidence,
    AVG(routing_latency_ms) AS avg_routing_latency_ms,
    COUNT(*) FILTER (WHERE fallback_used = TRUE) AS fallback_count,
    COUNT(*) FILTER (WHERE context_used = TRUE) AS context_used_count
FROM agent_squad_routing
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('hour', created_at), routed_agent, classified_intent;

CREATE UNIQUE INDEX ON agent_squad_hourly_metrics (hour, routed_agent, classified_intent);
```

---

## 5. Celery Background Tasks

### 5.1 Context Management Tasks

#### **Task: agent_squad_cleanup_old_context**

Clean up old conversation context to save storage.

**Schedule**: Daily at 02:00 UTC

```python
# src/app/infrastructure/celery/tasks/agent_squad_maintenance.py

@celery_app.task(
    name="agent_squad.cleanup_old_context",
    bind=True
)
def agent_squad_cleanup_old_context(self: Task):
    """
    Delete conversation context older than TTL.
    
    Runs daily at 02:00 UTC.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.session import AsyncSession
        from app.setup.config.agent_squad import AgentSquadSettings
        from datetime import datetime, timedelta
        
        session = await container.get(AsyncSession)
        settings = await container.get(AgentSquadSettings)
        
        if not settings.enabled:
            return {"status": "skipped", "reason": "Agent Squad disabled"}
        
        cutoff_date = datetime.utcnow() - timedelta(
            seconds=settings.storage.ttl_seconds
        )
        
        # Delete old conversations
        result = await session.execute(
            """
            DELETE FROM agent_squad_conversations
            WHERE last_message_at < :cutoff_date
            """,
            {"cutoff_date": cutoff_date}
        )
        deleted_count = result.rowcount
        await session.commit()
        
        logger.info(f"Deleted {deleted_count} old Agent Squad conversations")
        
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["agent-squad-cleanup-old-context"] = {
    "task": "agent_squad.cleanup_old_context",
    "schedule": crontab(hour=2, minute=0),  # Daily at 02:00 UTC
}
```

### 5.2 Metrics Tasks

#### **Task: agent_squad_refresh_metrics**

Refresh materialized views.

**Schedule**: Every 5 minutes

```python
@celery_app.task(
    name="agent_squad.refresh_metrics",
    bind=True
)
def agent_squad_refresh_metrics(self: Task):
    """
    Refresh agent_squad_hourly_metrics materialized view.
    
    Runs every 5 minutes.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.session import AsyncSession
        
        session = await container.get(AsyncSession)
        
        await session.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY agent_squad_hourly_metrics"
        )
        await session.commit()
        
        logger.info("Refreshed agent_squad_hourly_metrics view")
        
        return {"status": "success"}
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["agent-squad-refresh-metrics"] = {
    "task": "agent_squad.refresh_metrics",
    "schedule": crontab(minute="*/5"),  # Every 5 minutes
}
```

---

## 6. Integration with Existing Solution

### 6.1 Integration Architecture

```
User Message
    ↓
FastAPI Presentation Layer
    ↓
SendMessage Interactor (Application)
    ↓
AgentGateway (Port) → Existing interface, no changes
    ↓
    ├─→ AgentSquadGateway (New) ← if agent_squad.enabled = true
    │       ↓
    │   Intent Classifier (gpt-4o-mini)
    │       ↓
    │   Route to Specialist
    │       ↓
    │   ├─→ Chat Agent → AgnoRuntime → LLMOrchestrator
    │   ├─→ Hunter AI → AgnoRuntime → LLMOrchestrator
    │   ├─→ Research → AgnoRuntime → LLMOrchestrator
    │   ├─→ Trading → AgnoRuntime → LLMOrchestrator
    │   └─→ Risk Analyzer → AgnoRuntime → LLMOrchestrator
    │       ↓
    │   Context Storage (PostgreSQL)
    │
    └─→ AgnoRuntimeGateway (Existing) ← if agent_squad.enabled = false
            ↓
        Single Agent → AgnoRuntime → LLMOrchestrator
```

**Zero changes to**:
- `AgentGateway` port (domain)
- `SendMessage` interactor (application)
- Controllers (presentation)
- `AgnoRuntime` (infrastructure)
- `LLMOrchestrator` (domain)

### 6.2 Dependency Injection

```python
# src/app/setup/ioc/agent_squad.py (New)

from dishka import Provider, Scope, provide
from app.infrastructure.adapters.agent_squad.orchestrator import AgentSquadOrchestrator
from app.infrastructure.adapters.agent_squad.gateway import AgentSquadGateway
from app.setup.config.agent_squad import AgentSquadSettings
from app.domain.ports.ai.agent_gateway import AgentGateway

class AgentSquadProvider(Provider):
    """Dishka provider for Agent Squad."""
    
    @provide(scope=Scope.APP)
    def get_agent_squad_settings(self, settings: Settings) -> AgentSquadSettings:
        """Provide Agent Squad settings."""
        return settings.agent_squad
    
    @provide(scope=Scope.APP)
    async def get_orchestrator(
        self,
        settings: AgentSquadSettings,
        agno_gateway: AgnoRuntimeGateway
    ) -> AgentSquadOrchestrator:
        """Provide Agent Squad orchestrator (singleton)."""
        orchestrator = AgentSquadOrchestrator(settings, agno_gateway)
        await orchestrator.initialize()
        return orchestrator
    
    @provide(scope=Scope.REQUEST)
    def get_agent_gateway(
        self,
        orchestrator: AgentSquadOrchestrator,
        agno_gateway: AgnoRuntimeGateway,
        settings: AgentSquadSettings
    ) -> AgentGateway:
        """
        Provide AgentGateway implementation.
        
        Returns AgentSquadGateway if enabled, else AgnoRuntimeGateway.
        """
        if settings.enabled:
            return AgentSquadGateway(orchestrator, settings)
        else:
            return agno_gateway
```

Register in provider registry:

```python
# src/app/setup/ioc/provider_registry.py (Modified)

from app.setup.ioc.agent_squad import AgentSquadProvider

def get_providers() -> tuple[Provider, ...]:
    return (
        ApplicationProvider(),
        infrastructure_provider(),
        PresentationProvider(),
        SettingsProvider(),
        LLMRankingProvider(),
        AgnoProvider(),
        AgentSquadProvider(),  # NEW
    )
```

### 6.3 Migration Strategy

**Phase 1: Shadow Mode** (Week 1)
- Deploy with `enabled=false`
- Run intent classification in background (log only)
- Compare Agent Squad routing vs single-agent
- Validate context preservation

**Phase 2: Alpha** (Week 2)
- Enable for 5% of traffic
- Monitor intent classification accuracy
- Verify context preservation
- Test supervisor coordination

**Phase 3: Beta** (Week 3)
- Enable for 25% of traffic
- Monitor multi-turn conversations
- Test parallel agent execution
- Validate storage performance

**Phase 4: Production** (Week 4)
- Enable for 100% of traffic
- Full monitoring dashboards
- Performance optimization

**Rollback Plan**:
```bash
# Emergency disable
export AGENT_SQUAD_ENABLED=false

# Or via admin API
curl -X POST https://api.anvil.com/api/v1/admin/agent-squad/disable \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 7. Success Criteria

### 7.1 Technical Metrics

- ✅ Intent classification accuracy: >95%
- ✅ Routing latency: <50ms (p95)
- ✅ Context preservation: 10+ turns without loss
- ✅ Supervisor coordination: <5s total latency
- ✅ Agent selection accuracy: >90%

### 7.2 Business Metrics

- ✅ Quality improvement: +20%
- ✅ User engagement: +30%
- ✅ Complex task success: +40%
- ✅ Multi-turn conversation rate: +50%
- ✅ User satisfaction: +25%

---

**Document Status**: ✅ Ready for Implementation  
**Next Step**: Create development tasks and start Week 1  
**Timeline**: 4 weeks (160 hours)  
**Investment**: $24,000  
**Expected ROI**: 120 days
