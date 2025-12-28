"""
Agent Squad Domain Layer Providers.

Provides domain services and entities for dependency injection.
"""

from dishka import Provider, Scope, provide

from app.domain.enums.agent_type import AgentType
from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
from app.domain.services.agent_squad.context_manager import ContextManager
from app.domain.services.agent_squad.intent_classifier import IntentClassifier
from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator
from app.domain.ports.agent_squad.agent_gateway import AgentGateway
from app.domain.ports.agent_squad.intent_classifier_gateway import IntentClassifierGateway
from app.domain.ports.agent_squad.feature_flags_gateway import FeatureFlagsGateway
from app.domain.ports.agent_squad.context_storage_gateway import ContextStorageGateway
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class AgentSquadDomainProvider(Provider):
    """Provider for Agent Squad domain layer dependencies."""

    scope = Scope.REQUEST

    @provide
    def provide_intent_classifier(
        self,
        llm_client: LLMClientGateway,
    ) -> IntentClassifier:
        """Provide intent classifier domain service."""
        return IntentClassifier(
            llm_client=llm_client,
            classification_model="gpt-4o-mini",  # Fast classification
        )

    @provide
    def provide_context_manager(
        self,
        context_storage: ContextStorageGateway,
    ) -> ContextManager:
        """Provide context manager domain service."""
        return ContextManager(storage=context_storage)

    @provide
    def provide_agent_orchestrator(
        self,
        intent_classifier: IntentClassifier,
        feature_flags: FeatureFlagsGateway,
        agent_registry: dict[AgentType, AgentGateway],
    ) -> AgentOrchestrator:
        """Provide agent orchestrator domain service."""
        return AgentOrchestrator(
            intent_classifier=intent_classifier,
            feature_flags=feature_flags,
            agent_registry=agent_registry,
        )

    @provide
    def provide_supervisor_coordinator(
        self,
        llm_client: LLMClientGateway,
    ) -> SupervisorCoordinator:
        """Provide supervisor coordinator domain service."""
        from unittest.mock import MagicMock
        # Mock agent_executor for testing (real implementation pending)
        agent_executor = MagicMock()

        return SupervisorCoordinator(
            llm_client=llm_client,
            agent_executor=agent_executor,
        )
