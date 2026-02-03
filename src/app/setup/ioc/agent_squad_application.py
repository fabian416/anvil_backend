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
from app.domain.chat.ports.message_repository import MessageRepository
from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
from app.domain.services.agent_squad.context_manager import ContextManager
from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator
from app.domain.services.agent_squad.authenticated_supervisor import AuthenticatedSupervisorCoordinator
from app.application.chat.commands.send_message_with_supervisor import SendMessageWithSupervisor
from app.application.chat.services.user_data_service import UserDataService
from app.domain.ports.wallet.wallet_repository import WalletRepository
# NOTE: TransactionRepository import removed - causes session corruption
# from app.domain.transactions.ports.transaction.transaction_repository import TransactionRepository
from app.domain.portfolio.ports.portfolio.portfolio_repository import PortfolioRepository


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
    
    @provide
    def provide_user_data_service(
        self,
        wallet_repository: WalletRepository = None,  # type: ignore
        # NOTE: TransactionRepository is DISABLED - it causes session corruption
        # when queries fail due to schema mismatches or missing data.
        # transaction_repository: TransactionRepository = None,
        portfolio_repository: PortfolioRepository = None,  # type: ignore
    ) -> UserDataService:
        """
        Provide UserDataService for accessing user wallet/portfolio data.
        
        This service aggregates data from multiple repositories for use
        in authenticated chat workflows.
        
        IMPORTANT: TransactionRepository is intentionally NOT injected here.
        When transaction queries fail, they leave the PostgreSQL transaction
        in an "aborted" state, which corrupts the shared session and causes
        all subsequent database operations to fail.
        
        The authenticated supervisor works fine without transaction history -
        it just won't have that context in the LLM prompt.
        """
        return UserDataService(
            wallet_repository=wallet_repository,
            portfolio_repository=portfolio_repository,
            transaction_repository=None,  # Disabled to prevent session corruption
        )
    
    @provide
    def provide_send_message_with_supervisor(
        self,
        authenticated_supervisor: AuthenticatedSupervisorCoordinator,
        orchestrator: AgentOrchestrator,
        user_data_service: UserDataService,
    ) -> SendMessageWithSupervisor:
        """
        Provide SendMessageWithSupervisor command for authenticated users.
        
        This command uses the AuthenticatedSupervisorCoordinator for LLM-based
        multi-agent orchestration with real data access via UserDataService.
        
        Features:
        - Access to user wallet data
        - Access to portfolio snapshots
        - Access to transaction history
        - Real-time balance fetching (via MCP tools)
        """
        # Inject user data service into supervisor
        authenticated_supervisor._user_data_service = user_data_service
        
        return SendMessageWithSupervisor(
            supervisor_coordinator=authenticated_supervisor,
            agent_orchestrator=orchestrator,
        )
