"""
Storage adapter for Agent Squad to use unified chat repository.

Updated to use the unified chat system (ChatMessageRepositorySqla)
instead of the deprecated ConversationRepository.
"""

from typing import Any, List, Dict, Optional
from uuid import UUID
from datetime import datetime, UTC

from app.domain.chat.entities.chat_message import ChatMessage, MessageRole


class ChatMessageRepositoryProtocol:
    """Protocol for chat message repository used by squad storage."""
    
    async def save(self, message: ChatMessage) -> ChatMessage: ...
    async def list_for_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatMessage]: ...


class AnvilSquadStorage:
    """
    Storage adapter that bridges Agent Squad's storage interface with unified chat repository.
    
    This adapter allows Agent Squad to persist and retrieve conversation history
    using the unified chat repository infrastructure (chat_messages table).
    """
    
    def __init__(self, message_repo: ChatMessageRepositoryProtocol):
        """
        Initialize storage adapter.
        
        Args:
            message_repo: Unified chat message repository
        """
        self._message_repo = message_repo
    
    async def save_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a message to the conversation history.
        
        Args:
            session_id: Conversation ID (UUID as string)
            role: Message role ("user", "agent", "system")
            content: Message content
            agent_type: Optional agent type that generated the message
            metadata: Optional metadata dictionary
        
        Returns:
            Message ID as string
        """
        try:
            conversation_id = UUID(session_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        # Map role string to MessageRole enum
        role_map = {
            "user": MessageRole.USER,
            "assistant": MessageRole.ASSISTANT,
            "agent": MessageRole.ASSISTANT,
            "system": MessageRole.SYSTEM,
        }
        message_role = role_map.get(role.lower(), MessageRole.USER)
        
        # Create message entity using unified chat system
        message = ChatMessage(
            conversation_id=conversation_id,
            role=message_role,
            content=content,
            metadata=metadata or {},
        )
        
        # Add agent_type to metadata if provided
        if agent_type:
            message.metadata["agent_type"] = agent_type

        # Save to repository
        saved_message = await self._message_repo.save(message)

        return str(saved_message.id)
    
    async def get_chat_history(
        self, 
        session_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chat history for a conversation.
        
        Args:
            session_id: Conversation ID (UUID as string)
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of message dictionaries in Agent Squad format
        """
        try:
            conversation_id = UUID(session_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        # Get messages from unified chat repository
        messages = await self._message_repo.list_for_conversation(
            conversation_id=conversation_id,
            limit=limit
        )
        
        # Convert to Agent Squad format
        history = []
        for msg in messages:
            # Map role enum to string
            role_str = "user" if msg.role == MessageRole.USER else "assistant"
            if msg.role == MessageRole.SYSTEM:
                role_str = "system"

            history.append({
                "id": str(msg.id),
                "role": role_str,
                "content": msg.content,
                "agent_type": msg.metadata.get("agent_type") if msg.metadata else None,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            })

        return history
    
    async def get_conversation_context(
        self, 
        session_id: str, 
        max_messages: int = 10
    ) -> str:
        """
        Get formatted conversation context for agent processing.
        
        Args:
            session_id: Conversation ID
            max_messages: Maximum messages to include in context
        
        Returns:
            Formatted conversation context as string
        """
        history = await self.get_chat_history(session_id, limit=max_messages)
        
        # Format as conversation context
        context_lines = []
        for msg in history:
            role = msg["role"].capitalize()
            content = msg["content"]
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    async def clear_conversation(self, session_id: str) -> None:
        """
        Clear all messages from a conversation (use with caution).
        
        Args:
            session_id: Conversation ID
        """
        # Not implemented - soft delete preferred over hard delete
        pass
