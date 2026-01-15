"""
Guest Chat API Schemas.

Request and response models for guest chat endpoints.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GuestChatRequest(BaseModel):
    """Request to send a guest chat message."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Message content (max 500 characters)",
    )
    language: str = Field(
        default="en",
        pattern="^(en|es|pt|zh|fr)$",
        description="Response language: en, es, pt, zh, fr",
    )


class GuestMessageData(BaseModel):
    """Message data in response."""

    id: str
    role: str
    content: str
    created_at: str


class GuestRoutingData(BaseModel):
    """Routing metadata in response."""

    intent: str
    confidence: float = 0.5
    handler: str = "demo_handler"
    language: str = "en"
    is_demo_mode: bool = True


class GuestRegistrationRequired(BaseModel):
    """Registration required response object."""

    required: bool = True
    reason: str
    message: dict[str, str]
    cta: dict[str, str]
    signup_url: str = "/signup"


class GuestInfo(BaseModel):
    """Guest session info."""

    messages_remaining: int = 20
    session_active: bool = True


class GuestChatResponse(BaseModel):
    """Response from guest chat endpoint."""

    conversation_id: UUID
    message_id: UUID
    user_message: dict[str, Any]
    agent_message: dict[str, Any]
    routing: GuestRoutingData
    enrichment: dict[str, Any] | None = None
    registration_required: GuestRegistrationRequired | None = None
    guest_info: GuestInfo | None = None
    rate_limited: bool = False

    model_config = ConfigDict(from_attributes=True)


class GuestHistoryMessage(BaseModel):
    """Message in history response."""

    id: UUID
    role: str
    content: str
    intent: str | None = None
    is_restricted_action: bool = False
    created_at: datetime


class GuestHistoryResponse(BaseModel):
    """Response for guest chat history."""

    conversation_id: UUID | None = None
    messages: list[GuestHistoryMessage] = []
    total_messages: int = 0
    is_active: bool = False
    language: str = "en"


class GuestStatusResponse(BaseModel):
    """Response for guest status check."""

    has_active_session: bool = False
    conversation_id: UUID | None = None
    messages_remaining: int = 20
    messages_this_hour: int = 0
    is_blocked: bool = False
    language: str = "en"


class GuestDeleteChatResponse(BaseModel):
    """Response for deleting guest chat."""

    success: bool = False
    message: str = "No active chat to delete"
