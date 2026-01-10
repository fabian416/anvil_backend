"""
Conversation Service.

Handles conversation CRUD operations.
"""

import logging
from typing import Any, Protocol
from uuid import UUID

from app.domain.chat.entities.chat_conversation import ChatConversation
from app.domain.chat.entities.chat_message import ChatMessage

logger = logging.getLogger(__name__)


class ConversationRepositoryProtocol(Protocol):
    """Protocol for conversation repository."""
    
    async def get_by_id(self, conversation_id: UUID) -> ChatConversation | None:
        ...
    
    async def get_by_id_and_user(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ChatConversation | None:
        ...
    
    async def get_active_for_user(self, user_id: UUID) -> ChatConversation | None:
        ...
    
    async def list_for_user(
        self,
        user_id: UUID,
        status: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> list[ChatConversation]:
        ...
    
    async def count_for_user(self, user_id: UUID, status: str = "active") -> int:
        ...
    
    async def save(self, conversation: ChatConversation) -> ChatConversation:
        ...
    
    async def update(self, conversation: ChatConversation) -> ChatConversation:
        ...
    
    async def delete_for_user(self, conversation_id: UUID, user_id: UUID) -> bool:
        ...


class MessageRepositoryProtocol(Protocol):
    """Protocol for message repository."""
    
    async def list_for_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatMessage]:
        ...
    
    async def count_for_conversation(self, conversation_id: UUID) -> int:
        ...


class ConversationService:
    """
    Service for managing conversations.
    
    Provides CRUD operations for conversations with user authorization.
    """
    
    def __init__(
        self,
        conversation_repository: ConversationRepositoryProtocol,
        message_repository: MessageRepositoryProtocol,
    ):
        self._conv_repo = conversation_repository
        self._msg_repo = message_repository
    
    async def create(
        self,
        user_id: UUID,
        title: str | None = None,
        language: str = "en",
    ) -> ChatConversation:
        """
        Create a new conversation.
        
        Args:
            user_id: User ID
            title: Optional title
            language: Language code
            
        Returns:
            Created conversation
        """
        conversation = ChatConversation.create(
            user_id=user_id,
            title=title,
            language=language,
        )
        return await self._conv_repo.save(conversation)
    
    async def get(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ChatConversation | None:
        """
        Get conversation by ID (with ownership check).
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for authorization
            
        Returns:
            Conversation if found and owned by user, None otherwise
        """
        return await self._conv_repo.get_by_id_and_user(conversation_id, user_id)
    
    async def get_with_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        message_limit: int = 50,
    ) -> dict[str, Any] | None:
        """
        Get conversation with messages.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for authorization
            message_limit: Max messages to return
            
        Returns:
            Dict with conversation and messages, or None
        """
        conversation = await self._conv_repo.get_by_id_and_user(
            conversation_id,
            user_id,
        )
        if not conversation:
            return None
        
        messages = await self._msg_repo.list_for_conversation(
            conversation_id,
            limit=message_limit,
        )
        
        return {
            "conversation": {
                "id": str(conversation.id),
                "title": conversation.title,
                "status": conversation.status.value,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
                "message_count": conversation.message_count,
                "language": conversation.language,
            },
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role.value,
                    "content": msg.content,
                    "intent": msg.intent,
                    "is_restricted_action": msg.is_restricted_action,
                    "created_at": msg.created_at.isoformat(),
                    "metadata": msg.metadata if msg.metadata else None,
                }
                for msg in messages
            ],
        }
    
    async def list(
        self,
        user_id: UUID,
        status: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List conversations for user.
        
        Args:
            user_id: User ID
            status: Filter by status
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of conversation dicts
        """
        conversations = await self._conv_repo.list_for_user(
            user_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        
        return [
            {
                "id": str(conv.id),
                "title": conv.title,
                "status": conv.status.value,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "message_count": conv.message_count,
                "language": conv.language,
            }
            for conv in conversations
        ]
    
    async def delete(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete (soft) a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for authorization
            
        Returns:
            True if deleted, False if not found
        """
        return await self._conv_repo.delete_for_user(conversation_id, user_id)
    
    async def archive(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ChatConversation | None:
        """
        Archive a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for authorization
            
        Returns:
            Updated conversation or None
        """
        conversation = await self._conv_repo.get_by_id_and_user(
            conversation_id,
            user_id,
        )
        if not conversation:
            return None
        
        conversation.archive()
        return await self._conv_repo.update(conversation)
    
    async def get_or_create_active(
        self,
        user_id: UUID,
        language: str = "en",
    ) -> ChatConversation:
        """
        Get active conversation or create new one.
        
        Args:
            user_id: User ID
            language: Language code
            
        Returns:
            Active conversation
        """
        conversation = await self._conv_repo.get_active_for_user(user_id)
        if conversation:
            return conversation
        
        return await self.create(user_id=user_id, language=language)
    
    async def update_title(
        self,
        conversation_id: UUID,
        user_id: UUID,
        title: str,
    ) -> ChatConversation | None:
        """
        Update conversation title.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID for authorization
            title: New title
            
        Returns:
            Updated conversation or None
        """
        conversation = await self._conv_repo.get_by_id_and_user(
            conversation_id,
            user_id,
        )
        if not conversation:
            return None
        
        conversation.set_title(title)
        return await self._conv_repo.update(conversation)

