"""
LLM Conversation entity.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.base import ValueObject
from app.domain.enums.ai.llm_provider import LLMProvider
from app.domain.enums.ai.llm_status import LLMStatus
from app.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, repr=False)
class LLMConversationId(ValueObject):
    value: int


@dataclass(frozen=True, repr=False)
class ModelId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class LLMConversation(Entity[LLMConversationId]):
    user_id: UserId
    session_id: str
    model_id: Optional[ModelId]
    provider: LLMProvider
    model_name: str
    prompt_text: str
    response_text: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    cost_usd: Optional[Decimal]
    latency_ms: Optional[int]
    status: LLMStatus
    error_message: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: CreatedAt
