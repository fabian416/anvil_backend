"""
Chat Message Entity.

Unified message entity with enhanced metadata support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class MessageRole(str, Enum):
    """Message role."""
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """
    Unified message entity.
    
    Supports rich metadata for intent tracking, handler info,
    and conversational context.
    """
    
    id: UUID = field(default_factory=uuid4)
    conversation_id: UUID = field(default_factory=uuid4)
    role: MessageRole = MessageRole.USER
    content: str = ""
    intent: str | None = None
    intent_confidence: float | None = None
    handler: str | None = None
    is_restricted_action: bool = False
    language: str = "en"
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create_user_message(
        cls,
        conversation_id: UUID,
        content: str,
        language: str = "en",
        metadata: dict[str, Any] | None = None,
    ) -> "ChatMessage":
        """Create a user message."""
        return cls(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            language=language,
            metadata=metadata or {},
        )
    
    @classmethod
    def create_assistant_message(
        cls,
        conversation_id: UUID,
        content: str,
        intent: str | None = None,
        intent_confidence: float | None = None,
        handler: str | None = None,
        is_restricted_action: bool = False,
        language: str = "en",
        metadata: dict[str, Any] | None = None,
    ) -> "ChatMessage":
        """Create an assistant message."""
        return cls(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            intent=intent,
            intent_confidence=intent_confidence,
            handler=handler,
            is_restricted_action=is_restricted_action,
            language=language,
            metadata=metadata or {},
        )
    
    @classmethod
    def create_system_message(
        cls,
        conversation_id: UUID,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> "ChatMessage":
        """Create a system message."""
        return cls(
            conversation_id=conversation_id,
            role=MessageRole.SYSTEM,
            content=content,
            metadata=metadata or {},
        )
    
    def set_pending_action(self, action: str) -> None:
        """Set a pending action in metadata."""
        self.metadata["pending_action"] = action
    
    def get_pending_action(self) -> str | None:
        """Get pending action from metadata."""
        return self.metadata.get("pending_action")
    
    def set_swap_info(self, swap_info: dict[str, Any]) -> None:
        """Store swap info for multi-turn swap flow."""
        self.metadata["swap_info"] = swap_info
    
    def get_swap_info(self) -> dict[str, Any] | None:
        """Get swap info from metadata."""
        return self.metadata.get("swap_info")
    
    def set_extracted_entities(self, entities: dict[str, Any]) -> None:
        """Store extracted entities (tokens, amounts, etc.)."""
        self.metadata["entities"] = entities
    
    def get_extracted_entities(self) -> dict[str, Any]:
        """Get extracted entities."""
        return self.metadata.get("entities", {})
    
    @property
    def is_user_message(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER
    
    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant."""
        return self.role == MessageRole.ASSISTANT

