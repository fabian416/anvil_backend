"""
Conversation entity.
"""

from dataclasses import dataclass
from typing import Optional
import uuid

from app.domain.entities.base import Entity
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.conversation_title import ConversationTitle
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class Conversation(Entity[ConversationId]):
    user_id: UserId
    title: Optional[ConversationTitle]
    created_at: CreatedAt
    updated_at: UpdatedAt

    @classmethod
    def create(cls, user_id: UserId, title: Optional[ConversationTitle] = None) -> "Conversation":
        now = CreatedAt.now()
        return cls(
            id_=ConversationId(uuid.uuid4()),
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=UpdatedAt(now.value),
        )
