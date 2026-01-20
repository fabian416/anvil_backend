"""
Agent Executor Adapter for SupervisorCoordinator.

Implements AgentExecutorPort using AgentOrchestrator to execute agents.
"""

import logging
from typing import TYPE_CHECKING

from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent

if TYPE_CHECKING:
    from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
    from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
    from app.domain.enums.agent_type import AgentType

logger = logging.getLogger(__name__)


class AgentExecutorAdapter:
    """
    Adapter that implements AgentExecutorPort using AgentOrchestrator.
    
    This allows SupervisorCoordinator to execute agents through the orchestrator.
    """

    def __init__(self, orchestrator: "AgentOrchestrator"):
        """
        Initialize agent executor adapter.
        
        Args:
            orchestrator: AgentOrchestrator to use for agent execution
        """
        self._orchestrator = orchestrator

    async def execute_agent(
        self,
        conversation_id: ConversationId,
        agent_type: "AgentType",
        message: MessageContent,
        conversation_context: "ConversationContext",
    ) -> "AgentResponse":
        """
        Execute specific agent and return full AgentResponse.
        
        Args:
            conversation_id: Conversation identifier
            agent_type: Agent to execute
            message: Message content for agent
            conversation_context: Conversation context
            
        Returns:
            AgentResponse with content, sources, and metadata
        """
        from app.domain.ports.agent_squad.agent_gateway import AgentResponse
        try:
            # Build conversation context for orchestrator
            # The orchestrator expects a different context format
            from app.domain.value_objects.agent_squad.conversation_context import (
                ConversationContext as OrchestratorContext,
            )
            
            # The orchestrator's execute_agent expects conversation_context with conversation_id
            # We need to add conversation_id to the context
            from app.domain.value_objects.agent_squad.conversation_context import (
                ConversationContext as OrchestratorContext,
            )
            
            # Create context - pass conversation_id via session_metadata as ConversationId object
            # The orchestrator expects ConversationId object in session_metadata
            orchestrator_context = OrchestratorContext(
                conversation_history=conversation_context.conversation_history,
                user_metadata={
                    **conversation_context.user_metadata,
                },
                session_metadata={
                    **conversation_context.session_metadata,
                    "conversation_id": conversation_id,  # Store ConversationId object (orchestrator will convert if needed)
                },
            )
            
            # Note: ConversationContext is frozen, so we can't assign conversation_id directly
            # The orchestrator will extract it from session_metadata and convert to ConversationId if needed
            
            # Use orchestrator to execute agent
            # Note: orchestrator.execute_agent expects message as str, not MessageContent
            response = await self._orchestrator.execute_agent(
                agent_type=agent_type,
                message=message.value,  # Convert MessageContent to str
                conversation_context=orchestrator_context,
            )
            
            # Return full AgentResponse if available, otherwise create one
            if isinstance(response, AgentResponse):
                return response
            elif hasattr(response, "content"):
                # If it has content attribute, assume it's AgentResponse-like
                return response
            elif isinstance(response, str):
                # Fallback: create minimal AgentResponse from string
                from app.domain.enums.agent_type import AgentType
                return AgentResponse(
                    content=response,
                    agent_type=agent_type,
                    tools_used=[],
                    sources=[],
                    metadata={},
                )
            else:
                # Last resort: convert to string
                return AgentResponse(
                    content=str(response),
                    agent_type=agent_type,
                    tools_used=[],
                    sources=[],
                    metadata={},
                )
            
        except Exception as e:
            logger.error(
                f"Failed to execute agent {agent_type.value}",
                extra={
                    "agent_type": agent_type.value,
                    "conversation_id": str(conversation_id.value),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise
