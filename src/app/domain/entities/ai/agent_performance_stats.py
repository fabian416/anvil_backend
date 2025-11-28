"""
Agent Performance Stats Entity.
"""
from dataclasses import dataclass
from typing import NewType
from decimal import Decimal
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt

AgentPerformanceStatsId = NewType("AgentPerformanceStatsId", int)

@dataclass(eq=False, kw_only=True)
class AgentPerformanceStats(Entity[AgentPerformanceStatsId]):
    agent_type: str
    time_window: str  # "1h", "24h", "all_time"
    
    total_requests: int
    successful_requests: int
    failed_requests: int
    canceled_requests: int
    
    avg_latency_ms: int
    avg_cost_usd: Decimal
    total_cost_usd: Decimal
    
    last_updated_at: datetime
    created_at: CreatedAt
    updated_at: UpdatedAt
