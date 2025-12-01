"""
Send message command.
"""

from uuid import UUID
from typing import Optional

from app.domain.entities.message import Message
from app.domain.entities.conversation import Conversation
from app.domain.ports.conversation_repository import ConversationRepository
from app.domain.ports.ai.agent_gateway import AgentGateway


class SendMessage:
    """
    Send a message in a conversation and get agent response.
    
    This orchestrates:
    1. Save user message
    2. Process with agent gateway
    3. Save agent response
    4. Update conversation timestamp
    """
    
    def __init__(
        self,
        repository: ConversationRepository,
        agent_gateway: AgentGateway,
    ):
        """
        Initialize interactor.
        
        Args:
            repository: Conversation repository
            agent_gateway: Agent gateway for processing messages
        """
        self._repository = repository
        self._agent_gateway = agent_gateway
    
    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
        content: str,
    ) -> tuple[Message, Message]:
        """
        Execute the command.
        
        Args:
            user_id: User identifier (for verification)
            conversation_id: Conversation identifier
            content: Message content
        
        Returns:
            Tuple of (user_message, agent_message)
        
        Raises:
            ValueError: If conversation not found or not owned by user
        """
        # Get conversation
        conversation = await self._repository.get_conversation(conversation_id)
        
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if conversation.user_id != user_id:
            raise ValueError("Conversation does not belong to user")
        
        # Create and save user message
        user_message = Message.create_user_message(
            conversation_id=conversation_id,
            content=content,
        )
        await self._repository.add_message(user_message)
        
        # Process with agent gateway
        agent_response = await self._agent_gateway.process_message(
            user_id=user_id,
            session_id=str(conversation_id),
            message=content,
        )
        
        # Create and save agent message
        agent_message = Message.create_agent_message(
            conversation_id=conversation_id,
            content=agent_response,
        )
        await self._repository.add_message(agent_message)
        
        # Update conversation timestamp
        conversation.touch()
        await self._repository.add_conversation(conversation)  # Update
        
        return user_message, agent_message
