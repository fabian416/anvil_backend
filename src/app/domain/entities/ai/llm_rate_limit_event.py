"""
LLM Rate Limit Event entity.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.base import ValueObject
from app.domain.enums.ai.llm_provider import LLMProvider
from app.domain.enums.ai.rate_limit_event_type import RateLimitEventType
from app.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, repr=False)
class RateLimitEventId(ValueObject):
    value: int


@dataclass(eq=False, kw_only=True)
class LLMRateLimitEvent(Entity[RateLimitEventId]):
    provider: LLMProvider
    model_name: str
    event_type: RateLimitEventType
    user_id: Optional[UserId]
    error_code: Optional[str]
    error_message: Optional[str]
    retry_after_seconds: Optional[int]
    fallback_used: bool
    fallback_provider: Optional[str]
    created_at: CreatedAt
