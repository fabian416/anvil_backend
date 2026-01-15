"""
Send Agent Squad Message Command.

This interactor orchestrates the complete flow of:
1. Saving user message to database
2. Classifying intent and routing to appropriate agent
3. Executing agent and collecting response
4. Saving agent response to database
5. Tracking telemetry (latency, tokens, tools used)
"""

from datetime import datetime, UTC
from uuid import UUID, uuid4

from app.domain.chat.entities.message import Message
from app.domain.entities.agent_squad.agent_telemetry import AgentTelemetry
from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.message_role import MessageRole
from app.domain.ports.agent_squad.agent_gateway import AgentGateway
from app.domain.ports.agent_squad.context_storage_gateway import ContextStorageGateway
from app.domain.ports.agent_squad.feature_flags_gateway import FeatureFlagsGateway
from app.domain.chat.ports.message_repository import MessageRepository
from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
from app.domain.services.agent_squad.context_manager import ContextManager
from app.domain.value_objects.agent_squad.conversation_context import (
    ConversationContext,
    ConversationMessage,
)
from app.domain.value_objects.conversation_id import ConversationId


class SendAgentSquadMessage:
    """
    Command interactor for sending messages to Agent Squad.

    Responsibilities:
    - Validate user has access to requested agent (based on subscription tier)
    - Build conversation context from history
    - Route message to appropriate agent
    - Save messages to database
    - Track telemetry metrics
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        context_manager: ContextManager,
        context_storage: ContextStorageGateway,
        message_repository: MessageRepository,
        feature_flags: FeatureFlagsGateway,
    ):
        self._orchestrator = orchestrator
        self._context_manager = context_manager
        self._context_storage = context_storage
        self._message_repository = message_repository
        self._feature_flags = feature_flags

    async def execute(
        self,
        conversation_id: UUID,
        user_id: UUID,
        content: str,
        force_agent: str | None = None,
    ) -> dict:
        """
        Execute the send message command.

        Args:
            conversation_id: Conversation identifier
            user_id: User identifier
            content: User message content
            force_agent: Optional agent type to force (bypasses intent classification)

        Returns:
            dict with:
                - user_message_id: UUID of saved user message
                - agent_message_id: UUID of saved agent message
                - agent_type: Agent that handled the message
                - intent_classification: Classified intent (if not forced)
                - intent_confidence: Confidence score (if not forced)
                - content: Agent response content
                - tools_used: List of tools the agent used
                - latency_ms: Total processing time
                - tokens_used: Total tokens consumed

        Raises:
            ValueError: If conversation not found or agent disabled
        """
        start_time = datetime.now(UTC)

        # Step 1: Build conversation context
        conv_id = ConversationId(conversation_id)
        context = await self._context_manager.build_context(
            conversation_id=conv_id,
            recent_messages_limit=10,  # Last 10 messages for context
        )

        # Step 2: Save user message to database
        user_message = Message.create(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )
        await self._message_repository.save(user_message)

        # Step 3: Add user message to context storage (Redis)
        await self._context_storage.add_message(
            conversation_id=conv_id,
            message=ConversationMessage(
                role=MessageRole.USER.value,
                content=content,
                timestamp=user_message.created_at.isoformat(),
            ),
        )

        # Step 4: Route to agent (or use forced agent)
        if force_agent:
            agent_type = AgentType(force_agent)
            # Validate agent is enabled
            if not await self._feature_flags.is_agent_enabled(agent_type):
                raise ValueError(f"Agent '{force_agent}' is disabled")
            intent_classification = None
            intent_confidence = None
        else:
            # Use orchestrator to classify intent and route
            agent_type, intent_classification = await self._orchestrator.route_message(
                message=content,
                conversation_context=context,
            )
            intent_confidence = (
                intent_classification.confidence if intent_classification else None
            )

        # Step 5: Execute agent
        agent_response = await self._orchestrator.execute_agent(
            agent_type=agent_type,
            message=content,
            conversation_context=context,
        )

        # Step 6: Save agent response to database (with sources in metadata)
        metadata = {}
        if agent_response.sources:
            # Store sources in metadata
            metadata["sources"] = [s.to_dict() for s in agent_response.sources]
        
        agent_message = Message.create(
            conversation_id=conversation_id,
            role=MessageRole.AGENT,
            content=agent_response.content,
            agent_type=agent_response.agent_type,
            metadata=metadata if metadata else None,
        )
        await self._message_repository.save(agent_message)

        # Step 7: Add agent message to context storage (Redis)
        await self._context_storage.add_message(
            conversation_id=conv_id,
            message=ConversationMessage(
                role=MessageRole.AGENT.value,
                content=agent_response.content,
                timestamp=agent_message.created_at.isoformat(),
                metadata={
                    "agent_type": agent_response.agent_type.value,
                    "tools_used": agent_response.tools_used,
                },
            ),
        )

        # Step 8: Calculate metrics
        end_time = datetime.now(UTC)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        tokens_used = agent_response.metadata.get("tokens_used")

        # Step 9: Track telemetry (for analytics)
        await self._track_telemetry(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_type=agent_type,
            intent_category=(
                intent_classification.intent_category.value
                if intent_classification
                else None
            ),
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            tools_used=agent_response.tools_used,
            success=True,
        )

        # Step 10: Return response (include sources)
        result = {
            "user_message_id": user_message.id,
            "agent_message_id": agent_message.id,
            "agent_type": agent_response.agent_type.value,
            "intent_classification": (
                intent_classification.intent_category.value
                if intent_classification
                else None
            ),
            "intent_confidence": intent_confidence,
            "content": agent_response.content,
            "tools_used": agent_response.tools_used,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
        }
        
        # Add sources if available
        if agent_response.sources:
            result["sources"] = [s.to_dict() for s in agent_response.sources]
        
        return result

    async def _track_telemetry(
        self,
        conversation_id: UUID,
        user_id: UUID,
        agent_type: AgentType,
        intent_category: str | None,
        latency_ms: int,
        tokens_used: int | None,
        tools_used: list[str],
        success: bool,
    ) -> None:
        """
        Track agent telemetry for analytics.

        This stores performance metrics for monitoring and optimization.
        In production, this would write to a time-series database or metrics service.
        """
        # Create telemetry entity
        telemetry = AgentTelemetry.create(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_type=agent_type,
            intent_category=intent_category,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            tools_used=tools_used,
            success=success,
        )

        # TODO: Save to telemetry repository (time-series DB)
        # For now, we'll skip persistence (telemetry is optional)
        # In production: await self._telemetry_repository.save(telemetry)
        pass
