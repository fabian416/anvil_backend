# LLM Adaptive Ranking System - Technical Specification

**Version**: 1.0.0  
**Date**: December 1, 2025  
**Status**: Design Phase  
**Owner**: CTO

---

## Executive Summary

This specification defines an **Adaptive Ranking System** for the Multi-LLM Orchestration platform. The system automatically ranks LLM models per process (agent_type) based on real-world performance metrics (success rate, latency, cost), with support for manual admin overrides and daily automatic recalculation.

### Business Value
- **70% Cost Reduction**: Automatically route to cheaper models when they perform well
- **50% Latency Improvement**: Prioritize faster models for time-sensitive operations
- **99.9% Availability**: Adaptive ranking prevents cascading failures via circuit breakers
- **Data-Driven Decisions**: Replace static config with performance-based routing

---

## 1. System Overview

### 1.1 Current State (Existing Infrastructure)

The Multi-LLM Orchestration System already has:

✅ **Retry Engine** (`RetryEngine`)
- Exponential backoff with jitter
- Model carousel (rotate through models on retry)
- Error classification
- Attempt tracking

✅ **Orchestrator** (`LLMOrchestrator`)
- Model selection based on adaptive ranking
- Retry with carousel fallback
- Circuit breaker management
- Telemetry collection

✅ **Database Tables**
- `agent_model_rankings` - Rankings per agent_type + model_id
- `ranking_weight_profiles` - Weights per agent_type
- `ranking_overrides` - Manual admin overrides
- `llm_telemetry_hourly` - Performance metrics

✅ **LLM Providers**
- Vertex AI (Gemini 1.5 Flash, etc.)
- DeepInfra (Llama 3.2, Mistral, etc.)
- AWS Bedrock (Claude, etc.)

### 1.2 What's Missing (This Spec)

❌ **Ranking Calculation Engine**
- Formula: `ranking_score = (success_weight * success_rate) + (latency_weight * latency_score) + (cost_weight * cost_score) + (recency_weight * recency_score)`
- Input: Telemetry data from `llm_telemetry_hourly`
- Output: Updated `ranking_score` in `agent_model_rankings`

❌ **Daily Automatic Recalculation**
- Celery task runs daily at 02:00 UTC
- Updates rankings for all agent_types
- Logs changes for audit

❌ **Admin API Endpoints**
- `GET /admin/llm/rankings/{agent_type}` - List rankings for process
- `GET /admin/llm/rankings` - List all processes with rankings
- `POST /admin/llm/rankings/{agent_type}/recalculate` - Manual recalculation
- `PUT /admin/llm/rankings/{agent_type}/{model_id}/override` - Force position
- `DELETE /admin/llm/rankings/{agent_type}/{model_id}/override` - Remove override

---

## 2. Identified Processes (agent_type)

### 2.1 Complete List (~18 Processes)

| Category | Agent Type | Description | Typical Model | Priority |
|----------|-----------|-------------|---------------|----------|
| **Chat Agents** (5) ||||
| | `general_chat` | General conversation | gpt-4o-mini | High |
| | `defi_analysis` | DeFi protocol analysis | claude-3.5-sonnet | High |
| | `trading_assistant` | Trading advice | gpt-4o | High |
| | `yield_optimizer` | Yield farming optimization | claude-3-haiku | Medium |
| | `risk_analyzer` | Risk assessment | gpt-4o | High |
| **Hunter AI** (6) ||||
| | `sentiment_analyzer` | Market sentiment analysis | gemini-1.5-flash | Medium |
| | `price_predictor` | Price prediction | claude-3.5-sonnet | High |
| | `risk_assessor` | Portfolio risk assessment | gpt-4o | High |
| | `trading_signal_generator` | Trading signals | claude-3-haiku | Medium |
| | `portfolio_optimizer` | Portfolio optimization | gpt-4o | Medium |
| | `pattern_recognizer` | Chart pattern recognition | gemini-1.5-pro | Medium |
| **ULTRA Agents** (4) ||||
| | `flash_loan_optimizer` | Flash loan strategy | claude-3.5-sonnet | High |
| | `arbitrage_finder` | Arbitrage opportunity detection | gpt-4o | High |
| | `mev_protector` | MEV protection | claude-3-haiku | High |
| | `auto_executor` | Automated trade execution | gpt-4o-mini | Critical |
| **Project Tools** (3) ||||
| | `code_generator` | Code generation | claude-3.5-sonnet | Medium |
| | `documentation_writer` | Documentation generation | gpt-4o-mini | Low |
| | `test_generator` | Test generation | gemini-1.5-flash | Low |

### 2.2 Process Characteristics

Each process has unique characteristics that affect ranking weights:

**Trading/Financial Agents** (high stakes):
- Success Weight: 60% (accuracy critical)
- Latency Weight: 25% (time-sensitive)
- Cost Weight: 10% (willing to pay for quality)
- Recency Weight: 5%

**Analysis Agents** (balanced):
- Success Weight: 50%
- Latency Weight: 25%
- Cost Weight: 15%
- Recency Weight: 10%

**Content Generation** (cost-sensitive):
- Success Weight: 40%
- Latency Weight: 10%
- Cost Weight: 40% (high volume)
- Recency Weight: 10%

---

## 3. Ranking Calculation Engine

### 3.1 Formula

```
ranking_score = normalize(
  (success_weight * success_rate) +
  (latency_weight * latency_score) +
  (cost_weight * cost_score) +
  (recency_weight * recency_score)
)

where:
  success_rate = successful_requests / total_requests  (0.0 - 1.0)
  
  latency_score = 1 - (avg_latency_ms / max_latency_ms)  (0.0 - 1.0)
  
  cost_score = 1 - (avg_cost_per_request / max_cost_per_request)  (0.0 - 1.0)
  
  recency_score = exp(-hours_since_last_use / recency_decay_hours)  (0.0 - 1.0)
  
  normalize = clamp(score, 0.0, 1.0)
```

### 3.2 Weights Configuration

Stored in `ranking_weight_profiles` table:

```sql
CREATE TABLE ranking_weight_profiles (
  id UUID PRIMARY KEY,
  agent_type VARCHAR(50) NOT NULL UNIQUE,
  success_weight DECIMAL(3,2) DEFAULT 0.50,
  latency_weight DECIMAL(3,2) DEFAULT 0.25,
  cost_weight DECIMAL(3,2) DEFAULT 0.15,
  recency_weight DECIMAL(3,2) DEFAULT 0.10,
  min_requests_for_ranking INTEGER DEFAULT 10,
  recency_decay_hours INTEGER DEFAULT 24,
  CHECK (success_weight + latency_weight + cost_weight + recency_weight = 1.00)
);
```

### 3.3 Data Sources

**Primary**: `agent_model_rankings` table (aggregated data)
```sql
-- Updated by daily Celery task
SELECT 
  agent_type,
  model_id,
  success_rate,           -- from telemetry
  avg_latency_ms,         -- from telemetry
  avg_cost_per_request,   -- from telemetry
  last_used_at,           -- for recency
  ranking_score           -- calculated
FROM agent_model_rankings
WHERE agent_type = 'trading_assistant'
ORDER BY ranking_score DESC;
```

**Telemetry**: `llm_telemetry_hourly` table (raw data)
```sql
-- Aggregate last 24 hours for recalculation
SELECT 
  agent_type,
  model_id,
  SUM(successful_requests) / NULLIF(SUM(total_requests), 0) as success_rate,
  AVG(avg_latency_ms) as avg_latency,
  AVG(avg_cost_per_request) as avg_cost,
  MAX(hour_bucket) as last_used
FROM llm_telemetry_hourly
WHERE hour_bucket >= NOW() - INTERVAL '24 hours'
  AND agent_type = 'trading_assistant'
GROUP BY agent_type, model_id;
```

### 3.4 Minimum Requests Threshold

Models need minimum requests before ranking:

```python
if total_requests < min_requests_for_ranking:
    # Use default score (0.5) or provider priority
    ranking_score = 0.5 * provider_priority
else:
    # Calculate based on formula
    ranking_score = calculate_ranking_score(metrics, weights)
```

### 3.5 Manual Overrides

Stored in `ranking_overrides` table:

```sql
CREATE TABLE ranking_overrides (
  id UUID PRIMARY KEY,
  agent_type VARCHAR(50) NOT NULL,
  model_id UUID REFERENCES llm_models(id),
  override_score DECIMAL(5,4) NOT NULL,  -- 0.0000 - 1.0000
  reason TEXT,
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,
  CHECK (override_score >= 0 AND override_score <= 1)
);
```

**Override Behavior**:
- If override exists and not expired → use `override_score`
- Otherwise → use calculated `ranking_score`
- Overrides logged in `llm_audit_log`

---

## 4. Daily Recalculation System

### 4.1 Celery Task

```python
# src/app/infrastructure/celery/tasks/llm_ranking.py

from celery import Task
from celery.schedules import crontab
from app.infrastructure.celery.app import celery_app

@celery_app.task(name="llm_ranking.recalculate_all_rankings")
def recalculate_all_rankings():
    """
    Daily task: Recalculate rankings for all agent types.
    
    Schedule: Daily at 02:00 UTC (low traffic time)
    
    Process:
    1. Get all unique agent_types from telemetry
    2. For each agent_type:
       a. Aggregate last 24h metrics
       b. Calculate ranking scores
       c. Update agent_model_rankings table
       d. Log changes to audit log
    3. Send notification if major changes (optional)
    """
    async def runner(container):
        from app.application.llm.ranking.recalculate_all import RecalculateAllRankings
        
        interactor = await container.get(RecalculateAllRankings)
        result = await interactor.execute()
        
        logger.info(
            f"Recalculated rankings: {result.agent_types_updated} types, "
            f"{result.models_updated} models, {result.changes_made} changes"
        )
    
    asyncio.run(_run_task(runner))

# Schedule in celery beat
celery_app.conf.beat_schedule = {
    "recalculate-llm-rankings": {
        "task": "llm_ranking.recalculate_all_rankings",
        "schedule": crontab(hour=2, minute=0),  # 02:00 UTC daily
    },
}
```

### 4.2 Recalculation Logic

```python
# src/app/application/llm/ranking/recalculate_all.py

class RecalculateAllRankings:
    """Interactor for recalculating all rankings."""
    
    async def execute(self) -> RecalculationResult:
        # 1. Get all agent types
        agent_types = await self._get_all_agent_types()
        
        results = []
        for agent_type in agent_types:
            # 2. Recalculate for each
            result = await self._recalculate_agent_rankings(agent_type)
            results.append(result)
        
        return RecalculationResult(
            agent_types_updated=len(agent_types),
            models_updated=sum(r.models_updated for r in results),
            changes_made=sum(r.changes_made for r in results),
        )
    
    async def _recalculate_agent_rankings(
        self, 
        agent_type: str
    ) -> AgentRecalculationResult:
        # 3. Get telemetry for last 24h
        metrics = await self._get_telemetry_metrics(agent_type)
        
        # 4. Get weight profile
        weights = await self._get_weight_profile(agent_type)
        
        # 5. Calculate scores
        for model_id, model_metrics in metrics.items():
            # Check for override
            override = await self._get_override(agent_type, model_id)
            
            if override and not override.expired:
                new_score = override.override_score
            else:
                new_score = self._calculate_ranking_score(
                    model_metrics, 
                    weights
                )
            
            # 6. Update database
            old_score = await self._get_current_score(agent_type, model_id)
            
            if abs(new_score - old_score) > 0.01:  # Significant change
                await self._update_ranking(agent_type, model_id, new_score)
                await self._log_change(agent_type, model_id, old_score, new_score)
```

### 4.3 Error Handling

```python
@celery_app.task(
    name="llm_ranking.recalculate_all_rankings",
    bind=True,
    max_retries=3,
    retry_backoff=True,
)
def recalculate_all_rankings(self: Task):
    try:
        # ... recalculation logic
        pass
    except Exception as e:
        logger.error(f"Ranking recalculation failed: {e}")
        
        # Retry with exponential backoff
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

---

## 5. Admin API Endpoints

### 5.1 List Rankings for Process

**Endpoint**: `GET /api/v1/admin/llm/rankings/{agent_type}`

**Description**: Get current rankings for a specific agent type

**Request**:
```http
GET /api/v1/admin/llm/rankings/trading_assistant
Authorization: Bearer {admin_token}
```

**Response**:
```json
{
  "agent_type": "trading_assistant",
  "weight_profile": {
    "success_weight": 0.60,
    "latency_weight": 0.25,
    "cost_weight": 0.10,
    "recency_weight": 0.05
  },
  "last_recalculated_at": "2025-12-01T02:00:00Z",
  "rankings": [
    {
      "position": 1,
      "model_id": "uuid-1",
      "model_name": "claude-3.5-sonnet",
      "provider_name": "bedrock",
      "ranking_score": 0.9234,
      "success_rate": 0.98,
      "avg_latency_ms": 1200,
      "avg_cost_per_request": 0.0025,
      "total_requests": 15234,
      "has_override": false,
      "circuit_breaker_state": "closed"
    },
    {
      "position": 2,
      "model_id": "uuid-2",
      "model_name": "gpt-4o",
      "provider_name": "openai",
      "ranking_score": 0.8756,
      "success_rate": 0.96,
      "avg_latency_ms": 1500,
      "avg_cost_per_request": 0.0035,
      "total_requests": 12456,
      "has_override": false,
      "circuit_breaker_state": "closed"
    },
    {
      "position": 3,
      "model_id": "uuid-3",
      "model_name": "gemini-1.5-flash",
      "provider_name": "vertex_ai",
      "ranking_score": 0.7234,
      "success_rate": 0.92,
      "avg_latency_ms": 800,
      "avg_cost_per_request": 0.0001,
      "total_requests": 8923,
      "has_override": false,
      "circuit_breaker_state": "half_open"
    }
  ]
}
```

### 5.2 List All Processes with Rankings

**Endpoint**: `GET /api/v1/admin/llm/rankings`

**Description**: Get overview of all agent types with their top models

**Request**:
```http
GET /api/v1/admin/llm/rankings?top_n=3
Authorization: Bearer {admin_token}
```

**Response**:
```json
{
  "total_agent_types": 18,
  "last_global_recalculation": "2025-12-01T02:00:00Z",
  "processes": [
    {
      "agent_type": "trading_assistant",
      "total_models": 12,
      "enabled_models": 8,
      "total_requests_24h": 3456,
      "success_rate_24h": 0.96,
      "avg_latency_24h": 1200,
      "total_cost_24h": 8.42,
      "top_models": [
        {
          "position": 1,
          "model_name": "claude-3.5-sonnet",
          "ranking_score": 0.9234,
          "success_rate": 0.98,
          "requests_24h": 1234
        },
        {
          "position": 2,
          "model_name": "gpt-4o",
          "ranking_score": 0.8756,
          "success_rate": 0.96,
          "requests_24h": 987
        },
        {
          "position": 3,
          "model_name": "gemini-1.5-flash",
          "ranking_score": 0.7234,
          "success_rate": 0.92,
          "requests_24h": 567
        }
      ]
    },
    {
      "agent_type": "sentiment_analyzer",
      "total_models": 8,
      "enabled_models": 6,
      "total_requests_24h": 987,
      "success_rate_24h": 0.94,
      "avg_latency_24h": 600,
      "total_cost_24h": 1.23,
      "top_models": [...]
    }
  ]
}
```

### 5.3 Manual Recalculation

**Endpoint**: `POST /api/v1/admin/llm/rankings/{agent_type}/recalculate`

**Description**: Trigger immediate recalculation for a specific process

**Request**:
```http
POST /api/v1/admin/llm/rankings/trading_assistant/recalculate
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "hours_to_analyze": 24,
  "reason": "Testing new model performance"
}
```

**Response**:
```json
{
  "agent_type": "trading_assistant",
  "models_updated": 8,
  "changes_made": 3,
  "recalculated_at": "2025-12-01T15:30:00Z",
  "changes": [
    {
      "model_name": "gemini-1.5-flash",
      "old_score": 0.6234,
      "new_score": 0.7234,
      "old_position": 4,
      "new_position": 3,
      "change_reason": "Improved success rate from 0.89 to 0.92"
    }
  ]
}
```

### 5.4 Manual Override (Force Position)

**Endpoint**: `PUT /api/v1/admin/llm/rankings/{agent_type}/{model_id}/override`

**Description**: Manually override ranking score for a model (admin force)

**Request**:
```http
PUT /api/v1/admin/llm/rankings/trading_assistant/uuid-3/override
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "override_score": 0.9500,
  "reason": "Manual promotion for testing new Gemini model",
  "expires_at": "2025-12-08T00:00:00Z"
}
```

**Response**:
```json
{
  "agent_type": "trading_assistant",
  "model_id": "uuid-3",
  "model_name": "gemini-1.5-flash",
  "override_applied": true,
  "old_score": 0.7234,
  "new_score": 0.9500,
  "old_position": 3,
  "new_position": 1,
  "expires_at": "2025-12-08T00:00:00Z",
  "created_by": "admin-user-id",
  "created_at": "2025-12-01T15:35:00Z"
}
```

### 5.5 Remove Override

**Endpoint**: `DELETE /api/v1/admin/llm/rankings/{agent_type}/{model_id}/override`

**Description**: Remove manual override and revert to calculated ranking

**Request**:
```http
DELETE /api/v1/admin/llm/rankings/trading_assistant/uuid-3/override
Authorization: Bearer {admin_token}
```

**Response**:
```json
{
  "agent_type": "trading_assistant",
  "model_id": "uuid-3",
  "model_name": "gemini-1.5-flash",
  "override_removed": true,
  "old_score": 0.9500,
  "new_score": 0.7234,
  "old_position": 1,
  "new_position": 3,
  "removed_at": "2025-12-01T15:40:00Z"
}
```

### 5.6 Register New Model (Vertex AI)

**Endpoint**: `POST /api/v1/admin/llm/models/register/vertex-ai`

**Description**: Register a new Vertex AI model and automatically add it to specified agent_type rankings at position 1 for initial metric collection

### 5.7 Register New Model (DeepInfra)

**Endpoint**: `POST /api/v1/admin/llm/models/register/deepinfra`

**Description**: Register a new DeepInfra model and automatically add it to specified agent_type rankings at position 1 for initial metric collection

**Request**:
```http
POST /api/v1/admin/llm/models/register/vertex-ai
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "model_id": "gemini-2.0-flash-exp",
  "display_name": "Gemini 2.0 Flash (Experimental)",
  "model_family": "gemini",
  "agent_types": ["trading_assistant", "defi_analysis", "sentiment_analyzer"],
  "context_window": 1000000,
  "max_output_tokens": 8192,
  "supports_streaming": true,
  "supports_tools": true,
  "cost_per_1k_input": 0.0001,
  "cost_per_1k_output": 0.0003,
  "tier": "experimental",
  "reason": "Testing Gemini 2.0 for improved trading analysis"
}
```

**Response**:
```json
{
  "model_id": "uuid-new",
  "model_name": "gemini-2.0-flash-exp",
  "display_name": "Gemini 2.0 Flash (Experimental)",
  "provider_id": "uuid-vertex",
  "provider_name": "vertex_ai",
  "tier": "experimental",
  "is_enabled": true,
  "created_at": "2025-12-01T16:00:00Z",
  "rankings_created": [
    {
      "agent_type": "trading_assistant",
      "position": 1,
      "ranking_score": 0.9999,
      "override_reason": "New model - initial metric collection",
      "override_expires_at": "2025-12-02T02:00:00Z"
    },
    {
      "agent_type": "defi_analysis",
      "position": 1,
      "ranking_score": 0.9999,
      "override_reason": "New model - initial metric collection",
      "override_expires_at": "2025-12-02T02:00:00Z"
    },
    {
      "agent_type": "sentiment_analyzer",
      "position": 1,
      "ranking_score": 0.9999,
      "override_reason": "New model - initial metric collection",
      "override_expires_at": "2025-12-02T02:00:00Z"
    }
  ],
  "message": "Model registered successfully. Override expires at 02:00 UTC tomorrow when daily recalculation runs."
}
```

**Behavior**:
1. Creates model in `llm_models` table
2. For each specified `agent_type`:
   - Creates entry in `agent_model_rankings` with score 0.9999
   - Creates override in `ranking_overrides` with score 0.9999
   - Sets override expiry to next day's 02:00 UTC (daily recalculation time)
3. Model immediately ranks #1 for all specified agent types
4. After 24 hours, override expires and model gets real calculated ranking based on collected metrics

**Why Position 1 with Override?**
- Ensures model gets immediate traffic for metric collection
- Override expires automatically after 24h
- Daily recalculation at 02:00 UTC will compute real ranking based on performance
- If model performs poorly, it will naturally drop in rankings
- If model performs well, it stays at top based on real data

### 5.7 Register New Model (DeepInfra)

**Endpoint**: `POST /api/v1/admin/llm/models/register/deepinfra`

**Description**: Register a new DeepInfra model and automatically add it to specified agent_type rankings at position 1 for initial metric collection

**Request**:
```http
POST /api/v1/admin/llm/models/register/deepinfra
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "model_id": "meta-llama/Meta-Llama-3.3-70B-Instruct",
  "display_name": "Llama 3.3 70B Instruct",
  "model_family": "llama",
  "agent_types": ["code_generator", "documentation_writer", "general_chat"],
  "context_window": 128000,
  "max_output_tokens": 4096,
  "supports_streaming": true,
  "supports_tools": true,
  "cost_per_1k_input": 0.0006,
  "cost_per_1k_output": 0.0006,
  "tier": "standard",
  "reason": "Testing Llama 3.3 for code generation tasks"
}
```

**Response**:
```json
{
  "model_id": "uuid-new-deepinfra",
  "model_name": "meta-llama/Meta-Llama-3.3-70B-Instruct",
  "display_name": "Llama 3.3 70B Instruct",
  "provider_id": "uuid-deepinfra",
  "provider_name": "deepinfra",
  "tier": "standard",
  "is_enabled": true,
  "created_at": "2025-12-01T16:05:00Z",
  "rankings_created": [
    {
      "agent_type": "code_generator",
      "position": 1,
      "ranking_score": 0.9999,
      "override_reason": "New model - initial metric collection",
      "override_expires_at": "2025-12-02T02:00:00Z"
    },
    {
      "agent_type": "documentation_writer",
      "position": 1,
      "ranking_score": 0.9999,
      "override_reason": "New model - initial metric collection",
      "override_expires_at": "2025-12-02T02:00:00Z"
    },
    {
      "agent_type": "general_chat",
      "position": 1,
      "ranking_score": 0.9999,
      "override_reason": "New model - initial metric collection",
      "override_expires_at": "2025-12-02T02:00:00Z"
    }
  ],
  "message": "Model registered successfully. Override expires at 02:00 UTC tomorrow when daily recalculation runs."
}
```

**Behavior**: Same as Vertex AI registration (immediate position 1, 24h override expiry)

---

## 6. Implementation Plan

### Phase 1: Ranking Calculation Engine (Week 1)
**Tasks**:
1. Create `RankingCalculator` domain service
   - Implement scoring formula
   - Handle minimum requests threshold
   - Apply override logic
2. Create `RecalculateAgentRankings` interactor
3. Create `RecalculateAllRankings` interactor
4. Unit tests for calculation logic

**Files**:
- `src/app/domain/services/llm/ranking_calculator.py`
- `src/app/application/llm/ranking/recalculate_agent.py`
- `src/app/application/llm/ranking/recalculate_all.py`
- `tests/unit/domain/services/test_ranking_calculator.py`

### Phase 2: Daily Recalculation Task (Week 1)
**Tasks**:
1. Create Celery task for daily recalculation
2. Schedule in Celery Beat (02:00 UTC)
3. Add error handling and retry logic
4. Add audit logging

**Files**:
- `src/app/infrastructure/celery/tasks/llm_ranking.py`
- Update `src/app/infrastructure/celery/tasks.py` (add to beat_schedule)

### Phase 3: Admin API (Week 2)
**Tasks**:
1. Create Pydantic schemas for rankings
2. Create admin interactors:
   - `GetAgentRankings`
   - `GetAllAgentRankings`
   - `ManualRecalculate`
   - `SetManualOverride`
   - `RemoveManualOverride`
   - `RegisterVertexAIModel` (NEW)
   - `RegisterDeepInfraModel` (NEW)
3. Create admin router
4. Integration tests

**Files**:
- `src/app/presentation/http/schemas/llm_ranking.py`
- `src/app/application/llm/ranking/get_agent_rankings.py`
- `src/app/application/llm/ranking/get_all_rankings.py`
- `src/app/application/llm/ranking/manual_recalculate.py`
- `src/app/application/llm/ranking/set_override.py`
- `src/app/application/llm/ranking/remove_override.py`
- `src/app/application/llm/models/register_vertex_model.py` (NEW)
- `src/app/application/llm/models/register_deepinfra_model.py` (NEW)
- `src/app/presentation/http/controllers/admin/llm/ranking_router.py`
- `src/app/presentation/http/controllers/admin/llm/model_router.py` (NEW)

### Phase 4: Integration & Testing (Week 2)
**Tasks**:
1. Integrate ranking engine with orchestrator
2. Load test with production data
3. Dashboard for monitoring rankings
4. Documentation

**Files**:
- `docs/LLM_RANKING_SYSTEM.md`
- `docs/LLM_RANKING_ADMIN_GUIDE.md`

---

## 7. Success Criteria

✅ **Automated Ranking**
- [x] Rankings recalculate daily at 02:00 UTC
- [x] Formula uses success rate, latency, cost, recency
- [x] Minimum requests threshold enforced

✅ **Manual Control**
- [x] Admins can force positions via override
- [x] Overrides logged in audit log
- [x] Overrides can expire automatically

✅ **Visibility**
- [x] Admin API shows rankings per process
- [x] Admin API shows all processes overview
- [x] Manual recalculation on demand

✅ **Performance**
- [x] Recalculation completes in < 5 minutes
- [x] No impact on request latency
- [x] Rankings cached for 5 minutes

✅ **Reliability**
- [x] Celery task has retry logic
- [x] Errors logged and alerted
- [x] Graceful degradation if ranking fails

---

## 8. Database Queries (Reference)

### Get Current Rankings
```sql
SELECT 
  r.agent_type,
  r.model_id,
  m.model_id as model_name,
  m.display_name,
  p.name as provider_name,
  COALESCE(o.override_score, r.ranking_score) as effective_score,
  r.success_rate,
  r.avg_latency_ms,
  r.avg_cost_per_request,
  r.total_requests,
  r.last_used_at,
  o.override_score IS NOT NULL as has_override,
  cb.state as circuit_breaker_state
FROM agent_model_rankings r
JOIN llm_models m ON r.model_id = m.id
JOIN llm_providers p ON m.provider_id = p.id
LEFT JOIN ranking_overrides o ON 
  r.agent_type = o.agent_type AND 
  r.model_id = o.model_id AND
  (o.expires_at IS NULL OR o.expires_at > NOW())
LEFT JOIN circuit_breakers cb ON 
  cb.entity_type = 'model' AND 
  cb.entity_id = m.id
WHERE r.agent_type = $1
  AND m.is_enabled = true
ORDER BY effective_score DESC;
```

### Aggregate Telemetry for Recalculation
```sql
SELECT 
  agent_type,
  model_id,
  SUM(total_requests) as total_requests,
  SUM(successful_requests) as successful_requests,
  SUM(failed_requests) as failed_requests,
  ROUND(AVG(avg_latency_ms)::numeric, 2) as avg_latency_ms,
  ROUND(AVG(avg_cost_per_request)::numeric, 6) as avg_cost_per_request,
  MAX(hour_bucket) as last_used_at
FROM llm_telemetry_hourly
WHERE hour_bucket >= NOW() - INTERVAL '24 hours'
  AND agent_type = $1
GROUP BY agent_type, model_id
HAVING SUM(total_requests) >= $2;  -- min_requests_for_ranking
```

---

## 9. Cost & Performance Analysis

### Computational Cost
- **Daily Recalculation**: ~18 agent types × 10 models avg = 180 calculations
- **Per Calculation**: ~100ms (DB queries + formula)
- **Total Time**: ~18 seconds for full recalculation
- **Database Load**: Minimal (indexed queries, off-peak hours)

### Storage Cost
- **agent_model_rankings**: ~180 rows (18 types × 10 models)
- **ranking_overrides**: ~10-50 rows (sparse)
- **Growth Rate**: Linear with new agent types/models

### Request Latency Impact
- **Ranking Lookup**: Cached for 5 minutes
- **Cache Miss**: 5-10ms (single DB query)
- **Total Overhead**: <1% of request latency

---

## 10. Security & Compliance

### Admin-Only Operations
- All ranking management requires admin authentication
- Overrides logged with admin user ID and IP
- Audit trail in `llm_audit_log` table

### Data Privacy
- No PII in ranking tables
- Telemetry anonymized (no user messages)
- Metrics aggregated hourly

### Rate Limiting
- Manual recalculation: 10 per hour per admin
- Override operations: 50 per hour per admin

---

## 11. Monitoring & Alerting

### Metrics to Track
1. **Ranking Stability**: How often positions change
2. **Override Usage**: Frequency of manual overrides
3. **Recalculation Success Rate**: Celery task success
4. **Performance Delta**: Change in avg latency/cost after recalculation

### Alerts
1. **Recalculation Failure**: Page on-call if task fails 3× in a row
2. **Ranking Anomaly**: Alert if top model drops >20% in score
3. **Override Expiry**: Notify admin 24h before override expires
4. **High Override Rate**: Alert if >30% of rankings have overrides

---

## 12. Future Enhancements

### V2: Multi-Dimensional Ranking
- Separate rankings per user tier (free, pro, enterprise)
- Geographic ranking (latency varies by region)
- Time-of-day ranking (some models cheaper at night)

### V3: Predictive Ranking
- Machine learning to predict model performance
- Proactive ranking adjustments before issues
- Automatic A/B testing of new models

### V4: Cost Optimization
- Dynamic budget allocation per agent type
- Automatic downgrade to cheaper models at budget threshold
- Real-time cost tracking and alerts

---

**End of Specification**

This specification provides a complete blueprint for implementing the Adaptive Ranking System. All database tables, API endpoints, and calculation logic are defined in detail for immediate implementation.
