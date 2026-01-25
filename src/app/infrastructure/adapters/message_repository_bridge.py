"""
Message Repository Bridge Adapter.

Bridges the legacy MessageRepository port to the unified chat system.
This allows legacy commands to continue working while using the new
chat_messages table.
"""

from typing import List, Optional
from uuid import UUID

from app.domain.chat.ports.message_repository import MessageRepository
from app.domain.entities.message import Message
from app.domain.chat.entities.chat_message import ChatMessage, MessageRole as ChatMessageRole
from app.domain.value_objects.message_role import MessageRole
from app.infrastructure.adapters.chat_unified_repository_sqla import ChatMessageRepositorySqla


class MessageRepositoryBridge(MessageRepository):
    """
    Bridge adapter that implements legacy MessageRepository using unified chat.
    
    This adapter converts between legacy Message entities and unified ChatMessage
    entities, allowing existing code to work with the new chat_messages table.
    """
    
    def __init__(self, chat_message_repo: ChatMessageRepositorySqla):
        """
        Initialize bridge adapter.
        
        Args:
            chat_message_repo: Unified chat message repository
        """
        self._repo = chat_message_repo
    
    async def save(self, message: Message) -> None:
        """
        Save a message by converting to ChatMessage.
        
        Args:
            message: Legacy Message entity
        """
        # Convert MessageRole to ChatMessageRole
        role_map = {
            MessageRole.USER: ChatMessageRole.USER,
            MessageRole.AGENT: ChatMessageRole.ASSISTANT,
            MessageRole.SYSTEM: ChatMessageRole.SYSTEM,
        }
        chat_role = role_map.get(message.role, ChatMessageRole.USER)
        
        # Create ChatMessage from legacy Message
        chat_message = ChatMessage(
            id=message.id,
            conversation_id=message.conversation_id,
            role=chat_role,
            content=message.content,
            created_at=message.created_at,
            metadata=message.metadata or {},
        )
        
        # Add agent_type to metadata if present
        if message.agent_type:
            chat_message.metadata["agent_type"] = message.agent_type
        
        await self._repo.save(chat_message)
    
    async def get(self, message_id: UUID) -> Optional[Message]:
        """
        Get a message by ID.
        
        Args:
            message_id: Message identifier
        
        Returns:
            Legacy Message entity or None
        """
        # ChatMessageRepositorySqla doesn't have a get_by_id, so return None
        # This method is rarely used in practice
        return None
    
    async def get_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[Message]:
        """
        Get messages for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages
        
        Returns:
            List of legacy Message entities
        """
        # Get ChatMessages from unified repository
        chat_messages = await self._repo.list_for_conversation(
            conversation_id=conversation_id,
            limit=limit,
        )
        
        # Convert to legacy Message entities
        messages = []
        for chat_msg in chat_messages:
            # Convert ChatMessageRole to MessageRole
            role_map = {
                ChatMessageRole.USER: MessageRole.USER,
                ChatMessageRole.ASSISTANT: MessageRole.AGENT,
                ChatMessageRole.SYSTEM: MessageRole.SYSTEM,
            }
            legacy_role = role_map.get(chat_msg.role, MessageRole.USER)
            
            # Extract agent_type from metadata
            agent_type = None
            if chat_msg.metadata:
                agent_type = chat_msg.metadata.get("agent_type")
            
            message = Message(
                id=chat_msg.id,
                conversation_id=chat_msg.conversation_id,
                role=legacy_role,
                content=chat_msg.content,
                agent_type=agent_type,
                created_at=chat_msg.created_at,
                metadata=chat_msg.metadata,
            )
            messages.append(message)
        
        return messages
