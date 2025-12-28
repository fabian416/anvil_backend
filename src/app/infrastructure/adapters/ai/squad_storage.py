"""
Storage adapter for Agent Squad to use our conversation repository.
"""

from typing import Any, List, Dict, Optional
from uuid import UUID
from datetime import datetime

from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.chat.entities.message import Message
from app.domain.value_objects.message_role import MessageRole


class AnvilSquadStorage:
    """
    Storage adapter that bridges Agent Squad's storage interface with our domain repository.
    
    This adapter allows Agent Squad to persist and retrieve conversation history
    using our existing conversation repository infrastructure.
    """
    
    def __init__(self, repo: ConversationRepository):
        """
        Initialize storage adapter.
        
        Args:
            repo: Our domain conversation repository
        """
        self._repo = repo
    
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
        
        # Map role string to enum
        role_map = {
            "user": MessageRole.USER,
            "assistant": MessageRole.AGENT,
            "agent": MessageRole.AGENT,
            "system": MessageRole.SYSTEM,
        }
        message_role = role_map.get(role.lower(), MessageRole.USER)
        
        # Create message entity (using plain types, not value objects)
        message = Message.create(
            conversation_id=conversation_id,  # UUID, not ConversationId value object
            role=message_role,  # MessageRole enum
            content=content,  # str, not MessageContent value object
            agent_type=agent_type  # Optional[str], not AgentType enum
        )

        # Save to repository
        await self._repo.add_message(message)

        return str(message.id)  # message.id is UUID, not value object
    
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
        
        # Get messages from repository
        messages = await self._repo.get_messages(
            conversation_id=conversation_id,
            limit=limit
        )
        
        # Convert to Agent Squad format
        history = []
        for msg in messages:
            # Map our role enum to string
            role_str = "user" if msg.role == MessageRole.USER else "assistant"
            if msg.role == MessageRole.SYSTEM:
                role_str = "system"

            history.append({
                "id": str(msg.id),  # msg.id is UUID, not value object
                "role": role_str,
                "content": msg.content,  # msg.content is str, not value object
                "agent_type": msg.agent_type if msg.agent_type else None,  # Optional[str]
                "created_at": msg.created_at.isoformat() if msg.created_at else None,  # datetime
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
        try:
            conversation_id = UUID(session_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        # This would need to be implemented in the repository
        # For now, we'll skip implementation as it's not critical for MVP
        pass
