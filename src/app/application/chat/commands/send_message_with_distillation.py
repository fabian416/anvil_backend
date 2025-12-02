"""
Send message command with distillation support.
"""

from uuid import UUID
from typing import Optional
import asyncio

from app.domain.entities.message import Message
from app.domain.entities.conversation import Conversation
from app.domain.ports.conversation_repository import ConversationRepository
from app.domain.ports.ai.agent_gateway import AgentGateway
from app.domain.services.distillation.engine import DistillationEngine
from app.domain.value_objects.distillation import RouteType


class SendMessageWithDistillation:
    """
    Send a message with intelligent distillation pass.
    
    This orchestrates:
    1. Run distillation pass on user message
    2. Handle REJECT route (off-topic/harmful)
    3. Handle CACHE route (return cached response)
    4. Handle STATIC route (return templated response)
    5. Handle LIGHT_LLM route (use economy model)
    6. Handle FULL_LLM route (use premium model)
    7. Save all messages
    8. Update conversation timestamp
    9. Log telemetry
    """
    
    def __init__(
        self,
        repository: ConversationRepository,
        agent_gateway: AgentGateway,
        distillation_engine: DistillationEngine,
    ):
        """
        Initialize interactor.
        
        Args:
            repository: Conversation repository
            agent_gateway: Agent gateway for processing messages
            distillation_engine: Distillation engine for pre-processing
        """
        self._repository = repository
        self._agent_gateway = agent_gateway
        self._distillation_engine = distillation_engine
    
    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
        content: str,
    ) -> tuple[Message, Message]:
        """
        Execute the command with distillation.
        
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
        
        # Run distillation pass
        distillation_result = await self._distillation_engine.distill(
            query=content,
            user_id=user_id,
            user_context={
                "conversation_id": str(conversation_id),
            },
        )
        
        # Handle routing
        agent_response = None
        
        if distillation_result.route_type == RouteType.REJECT:
            # Rejected query (off-topic, harmful)
            agent_response = self._get_rejection_message(distillation_result.rejection_reason)
        
        elif distillation_result.route_type == RouteType.CACHE:
            # Cached response
            agent_response = distillation_result.cached_response
        
        elif distillation_result.route_type == RouteType.STATIC:
            # Static response
            agent_response = distillation_result.static_response
        
        elif distillation_result.route_type in [RouteType.LIGHT_LLM, RouteType.FULL_LLM]:
            # Process with agent gateway
            agent_response = await self._agent_gateway.process_message(
                user_id=user_id,
                session_id=str(conversation_id),
                message=content,
                suggested_model=distillation_result.suggested_model_tier,
                suggested_agent=distillation_result.suggested_agent,
            )
            
            # Cache the response for future use
            await self._distillation_engine.cache_response(
                query=content,
                intent=distillation_result.intent.value,
                entities=distillation_result.entities.__dict__ if hasattr(distillation_result.entities, "__dict__") else {},
                response_content=agent_response,
                source_model=distillation_result.suggested_model_tier,
            )
        
        # Create and save agent message
        agent_message = Message.create_agent_message(
            conversation_id=conversation_id,
            content=agent_response,
            metadata={
                "distillation": {
                    "route_type": distillation_result.route_type.value,
                    "intent": distillation_result.intent.value,
                    "complexity": distillation_result.complexity.value,
                    "cache_hit": distillation_result.cache_hit,
                    "cache_level": distillation_result.cache_level.value,
                    "classification_latency_ms": distillation_result.classification_latency_ms,
                    "estimated_cost_saved_usd": str(distillation_result.estimated_cost_saved_usd),
                }
            },
        )
        await self._repository.add_message(agent_message)
        
        # Update conversation timestamp
        conversation.touch()
        await self._repository.add_conversation(conversation)  # Update
        
        # Broadcast agent message via WebSocket (fire and forget)
        asyncio.create_task(self._broadcast_message(conversation_id, agent_message))
        
        return user_message, agent_message
    
    def _get_rejection_message(self, reason: Optional[str]) -> str:
        """
        Get rejection message based on reason.
        
        Args:
            reason: Rejection reason from distillation
            
        Returns:
            User-friendly rejection message
        """
        if not reason:
            reason = "off-topic"
        
        reason_lower = reason.lower()
        
        if "harmful" in reason_lower or "illegal" in reason_lower:
            return (
                "I can't help with that request as it appears to involve harmful or illegal content. "
                "I'm here to assist with DeFi, cryptocurrency, and blockchain-related questions. "
                "How can I help you with those topics?"
            )
        
        if "off-topic" in reason_lower or "unclear" in reason_lower:
            return (
                "I'm specialized in DeFi, cryptocurrency, and blockchain topics. "
                "Your question seems to be outside my area of expertise. "
                "Could you rephrase it to focus on DeFi-related topics, or ask me something about:\n"
                "• Token prices and market data\n"
                "• DeFi protocols (lending, borrowing, trading)\n"
                "• Blockchain networks and gas fees\n"
                "• Yield farming and staking strategies\n"
                "• Portfolio analysis and risk assessment"
            )
        
        # Default rejection
        return (
            "I'm unable to process that request. "
            "I'm here to help with DeFi and cryptocurrency topics. "
            "How can I assist you with those?"
        )
    
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
                        "metadata": message.metadata if hasattr(message, "metadata") else {},
                    }
                }
            )
        except Exception as e:
            # Don't fail the request if WebSocket broadcast fails
            import logging
            logging.error(f"Failed to broadcast message via WebSocket: {e}")
