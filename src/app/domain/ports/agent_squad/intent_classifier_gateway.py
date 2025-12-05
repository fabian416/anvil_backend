"""
Intent Classifier Gateway port.
"""

from typing import Protocol

from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.enums.agent_type import AgentType


class IntentClassification:
    """Intent classification result (imported from domain services)."""
    pass  # Will use the one from agent_orchestrator


class IntentClassifierGateway(Protocol):
    """
    Intent Classifier Gateway port.
    
    Implementing adapter: IntentClassifierOpenAI
    """
    
    async def classify(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> "IntentClassification":
        """
        Classify user intent from message.
        
        Args:
            message: User message
            conversation_context: Conversation history
            
        Returns:
            IntentClassification with intent, confidence, agent, reasoning
        """
        ...
    
    async def recommend_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int,
    ) -> list[AgentType]:
        """
        Recommend multiple agents for complex task.
        
        Args:
            message: User message
            conversation_context: Conversation history
            max_agents: Maximum agents to recommend
            
        Returns:
            List of agent types
        """
        ...
