"""
Send message command.
"""

from uuid import UUID
from typing import Optional
import asyncio

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
        
        # Broadcast agent message via WebSocket (fire and forget)
        asyncio.create_task(self._broadcast_message(conversation_id, agent_message))
        
        return user_message, agent_message
    
    async def _broadcast_message(self, conversation_id: UUID, message: Message) -> None:
        """
        Broadcast message to WebSocket connections.
        
        Args:
            conversation_id: Conversation identifier
            message: Message to broadcast
        """
        try:
            from app.presentation.http.websocket.chat_websocket import manager
            
            await manager.broadcast_to_conversation(
                conversation_id=conversation_id,
                message={
                    "type": "message",
                    "message": {
                        "id": str(message.id),
                        "role": message.role.value,
                        "content": message.content,
                        "agent_type": message.agent_type,
                        "created_at": message.created_at.isoformat(),
                    }
                }
            )
        except Exception as e:
            # Don't fail the request if WebSocket broadcast fails
            import logging
            logging.error(f"Failed to broadcast message via WebSocket: {e}")
