"""
Agent Model Configuration Entity.
"""

from dataclasses import dataclass
from typing import NewType
from uuid import UUID
from decimal import Decimal

from app.domain.entities.base import Entity
from app.domain.enums.ai.llm_provider import LLMProvider
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt

AgentModelConfigId = NewType("AgentModelConfigId", int)


@dataclass(eq=False, kw_only=True)
class AgentModelConfig(Entity[AgentModelConfigId]):
    agent_type: str  # e.g., "TRADING", "RESEARCH"
    provider: LLMProvider
    model_name: str
    priority: int  # 1 = Highest
    weight: int  # For load balancing if priorities are equal
    is_active: bool

    # Overrides global model cost if specific to this agent deal
    cost_per_1k_input_override: Decimal | None = None
    cost_per_1k_output_override: Decimal | None = None

    created_at: CreatedAt
    updated_at: UpdatedAt
