"""
Agent Squad Application Layer Providers.

Provides application layer interactors (use cases).
"""

from dishka import Provider, Scope, provide

from app.application.agent_squad.commands.send_agent_squad_message import (
    SendAgentSquadMessage,
)
from app.application.agent_squad.commands.execute_supervisor_workflow import (
    ExecuteSupervisorWorkflow,
)
from app.application.agent_squad.queries.get_enabled_agents import GetEnabledAgents
from app.application.agent_squad.queries.get_conversation_context import (
    GetConversationContext,
)
from app.domain.ports.agent_squad.context_storage_gateway import ContextStorageGateway
from app.domain.ports.agent_squad.feature_flags_gateway import FeatureFlagsGateway
from app.domain.ports.message_repository import MessageRepository
from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
from app.domain.services.agent_squad.context_manager import ContextManager
from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator


class AgentSquadApplicationProvider(Provider):
    """Provider for Agent Squad application layer dependencies."""

    scope = Scope.REQUEST

    # ========================================
    # Commands (Write Operations)
    # ========================================

    @provide
    def provide_send_agent_squad_message(
        self,
        orchestrator: AgentOrchestrator,
        context_manager: ContextManager,
        context_storage: ContextStorageGateway,
        message_repository: MessageRepository,
        feature_flags: FeatureFlagsGateway,
    ) -> SendAgentSquadMessage:
        """Provide SendAgentSquadMessage command."""
        return SendAgentSquadMessage(
            orchestrator=orchestrator,
            context_manager=context_manager,
            context_storage=context_storage,
            message_repository=message_repository,
            feature_flags=feature_flags,
        )

    @provide
    def provide_execute_supervisor_workflow(
        self,
        supervisor: SupervisorCoordinator,
        context_manager: ContextManager,
        context_storage: ContextStorageGateway,
        message_repository: MessageRepository,
    ) -> ExecuteSupervisorWorkflow:
        """Provide ExecuteSupervisorWorkflow command."""
        return ExecuteSupervisorWorkflow(
            supervisor=supervisor,
            context_manager=context_manager,
            context_storage=context_storage,
            message_repository=message_repository,
        )

    # ========================================
    # Queries (Read Operations)
    # ========================================

    @provide
    def provide_get_enabled_agents(
        self,
        feature_flags: FeatureFlagsGateway,
    ) -> GetEnabledAgents:
        """Provide GetEnabledAgents query."""
        return GetEnabledAgents(feature_flags=feature_flags)

    @provide
    def provide_get_conversation_context(
        self,
        context_manager: ContextManager,
        context_storage: ContextStorageGateway,
    ) -> GetConversationContext:
        """Provide GetConversationContext query."""
        return GetConversationContext(
            context_manager=context_manager,
            context_storage=context_storage,
        )
