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
            classification_model="meta-llama/Meta-Llama-3.1-8B-Instruct",  # DeepInfra-compatible model
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
        agent_orchestrator: AgentOrchestrator,
    ) -> SupervisorCoordinator:
        """Provide supervisor coordinator domain service."""
        from app.infrastructure.adapters.agent_squad.agent_executor_adapter import (
            AgentExecutorAdapter,
        )
        
        # Create real agent executor using orchestrator
        agent_executor = AgentExecutorAdapter(orchestrator=agent_orchestrator)

        return SupervisorCoordinator(
            llm_client=llm_client,
            agent_executor=agent_executor,
        )
