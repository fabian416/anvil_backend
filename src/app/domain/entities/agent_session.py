"""
Agent Session entity.
"""

from dataclasses import dataclass
from typing import Optional, Any
import uuid

from app.domain.entities.base import Entity
from app.domain.value_objects.agent_session_id import AgentSessionId
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class AgentSession(Entity[AgentSessionId]):
    conversation_id: ConversationId
    agent_type: AgentType
    state: dict[str, Any]
    created_at: CreatedAt
    updated_at: UpdatedAt

    @classmethod
    def create(
        cls, 
        conversation_id: ConversationId, 
        agent_type: AgentType,
        state: dict[str, Any]
    ) -> "AgentSession":
        now = CreatedAt.now()
        return cls(
            id_=AgentSessionId(uuid.uuid4()),
            conversation_id=conversation_id,
            agent_type=agent_type,
            state=state,
            created_at=now,
            updated_at=UpdatedAt(now.value),
        )
