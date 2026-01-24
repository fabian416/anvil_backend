"""Chat domain entities."""

from app.domain.chat.entities.conversation import Conversation
from app.domain.chat.entities.message import Message
from app.domain.chat.entities.conversation_context import ConversationContext
from app.domain.chat.entities.authenticated_chat import (
    AuthChatUser,
    AuthChatConversation,
    AuthChatMessage,
)
from app.domain.chat.entities.user_context_aware import UserContextAware

# Export legacy names for backward compatibility
ChatUser = AuthChatUser
ChatConversation = AuthChatConversation
ChatMessage = AuthChatMessage

__all__ = [
    "Conversation",
    "Message",
    "ConversationContext",
    "AuthChatUser",
    "AuthChatConversation",
    "AuthChatMessage",
    "ChatUser",  # Alias for authenticated chat
    "ChatConversation",  # Alias for authenticated chat
    "ChatMessage",  # Alias for authenticated chat
    "UserContextAware",  # Context-aware agent responses
]

