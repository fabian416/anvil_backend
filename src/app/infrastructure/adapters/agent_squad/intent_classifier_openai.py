"""
Intent Classifier OpenAI adapter.
"""

from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import (
    ConversationContext,
)
from app.domain.enums.agent_type import AgentType
from app.domain.services.agent_squad.intent_classifier import IntentClassifier
from app.domain.ports.agent_squad.intent_classifier_gateway import (
    IntentClassifierGateway,
)
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class IntentClassifierOpenAI:
    """
    Intent Classifier OpenAI adapter.

    Implements: IntentClassifierGateway

    Uses IntentClassifier domain service with OpenAI LLM client.
    """

    def __init__(
        self,
        llm_client: LLMClientGateway,
        classification_model: str = "gpt-4o-mini",
    ):
        """
        Initialize intent classifier.

        Args:
            llm_client: OpenAI LLM client
            classification_model: Model for classification (default: gpt-4o-mini)
        """
        # Create domain service with LLM client
        self._intent_classifier = IntentClassifier(
            llm_client=llm_client,
            classification_model=classification_model,
        )

    async def classify(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> "IntentClassification":
        """Classify user intent from message."""
        return await self._intent_classifier.classify(
            message=message,
            conversation_context=conversation_context,
        )

    async def recommend_agents_for_complex_task(
        self,
        message: MessageContent,
        conversation_context: ConversationContext,
        max_agents: int,
    ) -> list[AgentType]:
        """Recommend multiple agents for complex task."""
        return await self._intent_classifier.recommend_agents_for_complex_task(
            message=message,
            conversation_context=conversation_context,
            max_agents=max_agents,
        )
