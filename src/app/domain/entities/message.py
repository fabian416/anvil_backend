"""
Message entity.
"""

from dataclasses import dataclass
from typing import Optional
import uuid

from app.domain.entities.base import Entity
from app.domain.value_objects.message_id import MessageId
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.enums.message_role import MessageRole
from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.created_at import CreatedAt


@dataclass(eq=False, kw_only=True)
class Message(Entity[MessageId]):
    conversation_id: ConversationId
    role: MessageRole
    content: MessageContent
    agent_type: Optional[AgentType]
    created_at: CreatedAt

    @classmethod
    def create(
        cls, 
        conversation_id: ConversationId, 
        role: MessageRole, 
        content: MessageContent,
        agent_type: Optional[AgentType] = None
    ) -> "Message":
        return cls(
            id_=MessageId(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_type=agent_type,
            created_at=CreatedAt.now(),
        )
