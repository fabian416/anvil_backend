"""
Message entity for chat messages.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from app.domain.value_objects.message_role import MessageRole


class Message:
    """
    Message entity representing a single message in a conversation.
    
    Messages can be from users or agents.
    """
    
    def __init__(
        self,
        id: UUID,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        agent_type: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """
        Initialize message.
        
        Args:
            id: Message identifier
            conversation_id: Parent conversation identifier
            role: Message role (user/agent/system)
            content: Message content
            agent_type: Optional agent type if from agent
            created_at: Creation timestamp
        """
        self.id = id
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.agent_type = agent_type
        self.created_at = created_at or datetime.utcnow()
    
    @classmethod
    def create_user_message(
        cls,
        conversation_id: UUID,
        content: str,
    ) -> "Message":
        """
        Create a user message.
        
        Args:
            conversation_id: Parent conversation identifier
            content: Message content
        
        Returns:
            New user message instance
        """
        return cls(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )
    
    @classmethod
    def create_agent_message(
        cls,
        conversation_id: UUID,
        content: str,
        agent_type: Optional[str] = None,
    ) -> "Message":
        """
        Create an agent message.
        
        Args:
            conversation_id: Parent conversation identifier
            content: Message content
            agent_type: Optional agent type
        
        Returns:
            New agent message instance
        """
        return cls(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.AGENT,
            content=content,
            agent_type=agent_type,
        )
    
    @classmethod
    def create_system_message(
        cls,
        conversation_id: UUID,
        content: str,
    ) -> "Message":
        """
        Create a system message.
        
        Args:
            conversation_id: Parent conversation identifier
            content: Message content
        
        Returns:
            New system message instance
        """
        return cls(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.SYSTEM,
            content=content,
        )
