from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums.message_role import MessageRole
from app.domain.enums.agent_type import AgentType

class MessageCreate(BaseModel):
    content: str
    agent_type: Optional[AgentType] = None

class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    agent_type: Optional[AgentType]
    created_at: datetime

    class Config:
        from_attributes = True
