"""
Chat-related request/response schemas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    
    title: Optional[str] = Field(None, max_length=200)


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    
    content: str = Field(..., min_length=1, max_length=10000)


# Response schemas
class ConversationResponse(BaseModel):
    """Conversation response."""
    
    id: UUID
    user_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Message response."""
    
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    agent_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SendMessageResponse(BaseModel):
    """Response for send message containing both user and agent messages."""
    
    user_message: MessageResponse
    agent_message: MessageResponse


class ConversationListResponse(BaseModel):
    """List of conversations response."""
    
    conversations: List[ConversationResponse]
    total: int


class MessageListResponse(BaseModel):
    """List of messages response."""
    
    messages: List[MessageResponse]
    total: int
