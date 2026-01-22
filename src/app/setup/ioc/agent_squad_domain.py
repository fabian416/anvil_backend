"""
Agent Squad Domain Layer Providers.

Provides domain services and entities for dependency injection.

Architecture:
- GuestSupervisorCoordinator: For unauthenticated users (isolated prompts)
- AuthenticatedSupervisorCoordinator: For logged-in users (isolated prompts)
- SupervisorCoordinator: Base class (workflow execution only)

The guest and authenticated supervisors are COMPLETELY ISOLATED to prevent
changes in one from affecting the other.
"""

from dishka import Provider, Scope, provide

from app.domain.enums.agent_type import AgentType
from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
from app.domain.services.agent_squad.context_manager import ContextManager
from app.domain.services.agent_squad.intent_classifier import IntentClassifier
from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator
from app.domain.services.agent_squad.guest_supervisor import GuestSupervisorCoordinator
from app.domain.services.agent_squad.authenticated_supervisor import AuthenticatedSupervisorCoordinator
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
    def provide_guest_supervisor_coordinator(
        self,
        llm_client: LLMClientGateway,
        agent_orchestrator: AgentOrchestrator,
    ) -> GuestSupervisorCoordinator:
        """
        Provide supervisor coordinator domain service for GUEST users.
        
        ISOLATED from AuthenticatedSupervisorCoordinator to:
        - Prevent prompt changes from affecting authenticated users
        - Allow independent optimization
        - Enable different routing strategies
        
        Guest-specific:
        - Lower agent limit (5)
        - Shorter timeout (120s)
        - Redirects wallet/portfolio actions to guest_auth
        - No access to real user data
        """
        from app.infrastructure.adapters.agent_squad.agent_executor_adapter import (
            AgentExecutorAdapter,
        )
        
        # Create real agent executor using orchestrator
        agent_executor = AgentExecutorAdapter(orchestrator=agent_orchestrator)

        return GuestSupervisorCoordinator(
            llm_client=llm_client,
            agent_executor=agent_executor,
            max_agents=5,  # Lower limit for guests
            timeout_seconds=120,  # Shorter timeout for guests
        )

    @provide
    def provide_supervisor_coordinator(
        self,
        llm_client: LLMClientGateway,
        agent_orchestrator: AgentOrchestrator,
    ) -> SupervisorCoordinator:
        """
        Provide base supervisor coordinator.
        
        DEPRECATED for direct use - prefer GuestSupervisorCoordinator or
        AuthenticatedSupervisorCoordinator for proper isolation.
        
        Kept for backward compatibility with existing code.
        """
        from app.infrastructure.adapters.agent_squad.agent_executor_adapter import (
            AgentExecutorAdapter,
        )
        
        # Create real agent executor using orchestrator
        agent_executor = AgentExecutorAdapter(orchestrator=agent_orchestrator)

        return SupervisorCoordinator(
            llm_client=llm_client,
            agent_executor=agent_executor,
        )
    
    @provide
    def provide_authenticated_supervisor_coordinator(
        self,
        llm_client: LLMClientGateway,
        agent_orchestrator: AgentOrchestrator,
    ) -> AuthenticatedSupervisorCoordinator:
        """
        Provide supervisor coordinator domain service for AUTHENTICATED users.
        
        ISOLATED from GuestSupervisorCoordinator to:
        - Prevent prompt changes from affecting guest users
        - Allow independent optimization
        - Enable different routing strategies
        
        Authenticated-specific:
        - Higher agent limit (6)
        - Longer timeout (180s)
        - Real data access via UserDataService
        - Access to wallet, portfolio, transaction history agents
        - No demo mode disclaimers
        """
        from app.infrastructure.adapters.agent_squad.agent_executor_adapter import (
            AgentExecutorAdapter,
        )
        
        # Create real agent executor using orchestrator
        agent_executor = AgentExecutorAdapter(orchestrator=agent_orchestrator)
        
        # UserDataService will be injected separately when needed
        # (repositories are request-scoped, so we can't inject them here)
        # The command layer will set user data via load_user_data()

        return AuthenticatedSupervisorCoordinator(
            llm_client=llm_client,
            agent_executor=agent_executor,
            user_data_service=None,  # Set at request time
            max_agents=6,  # Higher limit for authenticated users
            timeout_seconds=180,  # Longer timeout for complex workflows
        )
