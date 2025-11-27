"""
Conversation Feedback entity.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from app.domain.entities.base import Entity
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.base import ValueObject
from app.domain.entities.ai.llm_conversation import LLMConversationId
from app.domain.enums.ai.feedback_type import FeedbackType
from app.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, repr=False)
class ConversationFeedbackId(ValueObject):
    value: int

@dataclass(eq=False, kw_only=True)
class ConversationFeedback(Entity[ConversationFeedbackId]):
    conversation_id: LLMConversationId
    user_id: UserId
    rating: Optional[int]
    feedback_type: FeedbackType
    feedback_text: Optional[str]
    created_at: CreatedAt
