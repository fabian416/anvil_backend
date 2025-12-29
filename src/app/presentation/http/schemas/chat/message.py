from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.value_objects.message_role import MessageRole

class MessageCreate(BaseModel):
    content: str
    agent_type: Optional[str] = None

class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    agent_type: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
