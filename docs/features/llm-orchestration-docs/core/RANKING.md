# Adaptive Ranking System

## Overview

The ranking system dynamically scores models based on real-world performance, optimizing model selection for each agent type.

---

## Ranking Formula

```
Ranking Score = (w1 × Success Rate) + (w2 × Latency Score) + (w3 × Cost Score) + (w4 × Recency Bonus)
```

### Component Scores

| Component | Calculation | Range |
|-----------|-------------|-------|
| **Success Rate** | `successful / total` | 0.0 - 1.0 |
| **Latency Score** | `1 - (avg_latency / max_latency)` | 0.0 - 1.0 |
| **Cost Score** | `1 - (avg_cost / max_cost)` | 0.0 - 1.0 |
| **Recency Bonus** | `0.5 if used in last N hours, else 0` | 0.0 - 0.5 |

---

## Agent-Specific Weight Profiles

| Agent Type | Success | Latency | Cost | Recency | Rationale |
|------------|---------|---------|------|---------|-----------|
| **swap_agent** | 0.60 | 0.25 | 0.10 | 0.05 | Accuracy critical for DeFi |
| **trading_agent** | 0.55 | 0.30 | 0.10 | 0.05 | Speed matters for trading |
| **portfolio_agent** | 0.45 | 0.20 | 0.25 | 0.10 | Cost-sensitive analysis |
| **researcher** | 0.40 | 0.15 | 0.30 | 0.15 | Bulk queries, cost focus |
| **risk_analyzer** | 0.65 | 0.20 | 0.10 | 0.05 | Highest accuracy needs |

---

## Implementation

```python
# src/llm/ranking/engine.py

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class RankedModel:
    model_id: str
    provider_name: str
    display_name: str
    ranking_score: float
    success_rate: float
    avg_latency_ms: int
    avg_cost_per_request: float
    total_requests: int

@dataclass
class WeightProfile:
    success_weight: float
    latency_weight: float
    cost_weight: float
    recency_weight: float

class RankingEngine:
    """Adaptive model ranking based on performance."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.min_requests = 10  # Minimum samples for ranking
        self.recency_hours = 24
    
    async def get_ranked_models(
        self,
        agent_type: str,
        capabilities: List[str] = None
    ) -> List[RankedModel]:
        """Get models ranked for specific agent."""
        
        # Get weight profile for agent
        weights = await self._get_weights(agent_type)
        
        # Query rankings with capability filter
        query = """
            SELECT 
                r.model_id,
                m.model_id as model_name,
                p.name as provider_name,
                m.display_name,
                r.ranking_score,
                r.success_rate,
                r.avg_latency_ms,
                r.avg_cost_per_request,
                r.total_requests,
                o.override_score,
                o.expires_at
            FROM agent_model_rankings r
            JOIN llm_models m ON m.id = r.model_id
            JOIN llm_providers p ON p.id = m.provider_id
            LEFT JOIN ranking_overrides o ON 
                o.agent_type = r.agent_type AND 
                o.model_id = r.model_id AND
                (o.expires_at IS NULL OR o.expires_at > NOW())
            WHERE r.agent_type = :agent_type
                AND m.is_enabled = true
                AND p.is_enabled = true
            ORDER BY COALESCE(o.override_score, r.ranking_score) DESC
        """
        
        results = await self.db.fetch_all(query, {"agent_type": agent_type})
        
        # Filter by capabilities if specified
        if capabilities:
            results = [r for r in results if self._has_capabilities(r, capabilities)]
        
        return [RankedModel(**r) for r in results]
    
    async def record_outcome(
        self,
        agent_type: str,
        model_id: str,
        success: bool,
        latency_ms: int,
        cost: float
    ):
        """Record request outcome for ranking updates."""
        
        await self.db.execute("""
            UPDATE agent_model_rankings
            SET 
                total_requests = total_requests + 1,
                successful_requests = successful_requests + CASE WHEN :success THEN 1 ELSE 0 END,
                failed_requests = failed_requests + CASE WHEN :success THEN 0 ELSE 1 END,
                avg_latency_ms = (avg_latency_ms * total_requests + :latency) / (total_requests + 1),
                avg_cost_per_request = (avg_cost_per_request * total_requests + :cost) / (total_requests + 1),
                last_used_at = NOW(),
                updated_at = NOW()
            WHERE agent_type = :agent_type AND model_id = :model_id
        """, {
            "agent_type": agent_type,
            "model_id": model_id,
            "success": success,
            "latency": latency_ms,
            "cost": cost
        })
    
    async def recalculate_rankings(self, agent_type: str = None):
        """Recalculate ranking scores."""
        
        # Get all agent types to recalculate
        if agent_type:
            agent_types = [agent_type]
        else:
            agent_types = await self._get_all_agent_types()
        
        for at in agent_types:
            weights = await self._get_weights(at)
            
            # Get max values for normalization
            stats = await self.db.fetch_one("""
                SELECT 
                    MAX(avg_latency_ms) as max_latency,
                    MAX(avg_cost_per_request) as max_cost
                FROM agent_model_rankings
                WHERE agent_type = :agent_type
                    AND total_requests >= :min_requests
            """, {"agent_type": at, "min_requests": self.min_requests})
            
            max_latency = stats["max_latency"] or 1
            max_cost = stats["max_cost"] or 0.01
            
            # Update scores
            await self.db.execute("""
                UPDATE agent_model_rankings
                SET 
                    success_rate = CASE 
                        WHEN total_requests > 0 
                        THEN successful_requests::float / total_requests 
                        ELSE 0 
                    END,
                    latency_score = CASE 
                        WHEN total_requests >= :min_requests 
                        THEN 1 - LEAST(avg_latency_ms::float / :max_latency, 1)
                        ELSE 0.5 
                    END,
                    cost_score = CASE 
                        WHEN total_requests >= :min_requests 
                        THEN 1 - LEAST(avg_cost_per_request / :max_cost, 1)
                        ELSE 0.5 
                    END,
                    ranking_score = CASE 
                        WHEN total_requests >= :min_requests THEN
                            :w_success * (successful_requests::float / total_requests) +
                            :w_latency * (1 - LEAST(avg_latency_ms::float / :max_latency, 1)) +
                            :w_cost * (1 - LEAST(avg_cost_per_request / :max_cost, 1)) +
                            :w_recency * CASE 
                                WHEN last_used_at > NOW() - INTERVAL ':recency hours' 
                                THEN 0.5 ELSE 0 
                            END
                        ELSE 0.5
                    END,
                    last_recalculated_at = NOW()
                WHERE agent_type = :agent_type
            """, {
                "agent_type": at,
                "min_requests": self.min_requests,
                "max_latency": max_latency,
                "max_cost": max_cost,
                "w_success": weights.success_weight,
                "w_latency": weights.latency_weight,
                "w_cost": weights.cost_weight,
                "w_recency": weights.recency_weight,
                "recency": self.recency_hours
            })
```

---

## Ranking Visualization

```
Agent: swap_agent
┌────┬─────────────────────┬───────────┬─────────┬─────────┬──────────┬──────────┐
│Rank│ Model               │ Score     │ Success │ Latency │ Cost     │ Requests │
├────┼─────────────────────┼───────────┼─────────┼─────────┼──────────┼──────────┤
│ 1  │ gemini-1.5-pro      │ 0.8945    │ 98.5%   │ 1,100ms │ $0.0072  │ 8,000    │
│ 2  │ claude-3-5-sonnet   │ 0.8721    │ 97.8%   │ 1,350ms │ $0.0095  │ 5,000    │
│ 3  │ llama-3.1-405b      │ 0.8543    │ 96.2%   │ 1,450ms │ $0.0081  │ 3,500    │
│ 4  │ gemini-1.5-flash    │ 0.8234    │ 95.1%   │ 890ms   │ $0.0023  │ 6,200    │
│ 5  │ mixtral-8x22b       │ 0.7912    │ 93.5%   │ 1,890ms │ $0.0042  │ 2,100    │
└────┴─────────────────────┴───────────┴─────────┴─────────┴──────────┴──────────┘
```

---

## Recalculation Schedule

Rankings are recalculated:
- **Hourly**: Automatic background job
- **On-demand**: Via admin API
- **After significant events**: Circuit breaker trips, config changes
