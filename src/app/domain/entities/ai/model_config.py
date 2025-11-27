"""
Model Config entity.
"""
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.entities.ai.llm_conversation import ModelId
from app.domain.enums.ai.llm_provider import LLMProvider
from app.domain.enums.ai.model_status import ModelStatus
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt

@dataclass(eq=False, kw_only=True)
class ModelConfig(Entity[ModelId]):
    provider: LLMProvider
    model_name: str
    label: str
    is_default: bool
    is_available: bool
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal
    max_tokens: Optional[int]
    status: ModelStatus
    request_count: int
    total_cost_usd: Decimal
    created_at: CreatedAt
    updated_at: UpdatedAt
