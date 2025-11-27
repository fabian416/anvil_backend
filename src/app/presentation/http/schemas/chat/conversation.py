from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationRead(BaseModel):
    id: UUID
    user_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
