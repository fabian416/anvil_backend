from dishka import Provider, Scope, provide, provide_all

# Chat interactors
from app.application.chat.commands.create_conversation import CreateConversation
from app.application.chat.commands.delete_conversation import DeleteConversation
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.services.admin_analytics_service import AdminChatAnalyticsService
from app.application.chat.queries.get_conversation import GetConversation
from app.application.chat.queries.list_conversations import ListConversations
from app.application.chat.queries.get_messages import GetMessages

# Domain ports for SendMessage
from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.chat.ports.analytics_repository import AnalyticsRepository
from app.domain.ports.ai.agent_gateway import AgentGateway

from app.application.commands.user.activate_user import ActivateUserInteractor
from app.application.commands.user.change_password import ChangePasswordInteractor
from app.application.commands.user.deactivate_user import DeactivateUserInteractor
from app.application.commands.user.grant_admin import GrantAdminInteractor
from app.application.commands.user.revoke_admin import RevokeAdminInteractor
from app.application.commands.auth.upgrade_to_admin import UpgradeToAdminInteractor
from app.application.commands.auth.change_role import ChangeRoleInteractor
from app.application.commands.auth.privy_login import PrivyLogin
from app.application.commands.wallet.export_wallet import ExportWallet
from app.application.commands.wallet.update_privy_wallet import UpdatePrivyWallet
from app.application.commands.policy.create_privy_policy import CreatePrivyPolicy
from app.application.commands.policy.get_privy_policy import GetPrivyPolicy
from app.application.commands.policy.update_privy_policy import UpdatePrivyPolicy
from app.application.commands.policy.manage_privy_policy_rules import (
    CreatePrivyPolicyRule,
    UpdatePrivyPolicyRule,
    DeletePrivyPolicyRule,
)
from app.application.common.ports.access_revoker import AccessRevoker
from app.application.common.ports.flusher import Flusher
from app.application.common.ports.identity_provider import IdentityProvider
from app.application.common.ports.transaction_manager import (
    TransactionManager,
)
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.ports.user_query_gateway import UserQueryGateway
from app.application.common.services.current_user import CurrentUserService
from app.application.queries.list_users import ListUsersQueryService
from app.application.queries.list_wallets import ListWalletsQueryService
from app.application.queries.wallet.get_privy_wallet_details import GetPrivyWalletDetails
from app.application.queries.policy.list_privy_policies import ListPrivyPolicies
from app.application.atlas.queries import (
    SearchCountriesQueryService,
    SearchCitiesQueryService,
    ListStatesByCountryQueryService,
)
from app.application.metrics.ports import UserMetricsRepository
from app.infrastructure.adapters.main_flusher_sqla import SqlaMainFlusher
from app.infrastructure.adapters.main_transaction_manager_sqla import (
    SqlaMainTransactionManager,
)
from app.infrastructure.adapters.user_data_mapper_sqla import (
    SqlaUserDataMapper,
)
from app.infrastructure.adapters.user_reader_sqla import SqlaUserReader
from app.infrastructure.adapters.user_metrics_repository_sqla import UserMetricsRepositorySqla
from app.infrastructure.auth.adapters.access_revoker import (
    AuthSessionAccessRevoker,
)
from app.infrastructure.auth.adapters.identity_provider import (
    AuthSessionIdentityProvider,
)
from app.infrastructure.privy.client import PrivyClient
from app.domain.services.user import UserService
from app.domain.services.auth import AuthService
from app.domain.ports.password_hasher import PasswordHasher
from app.domain.ports.user_id_generator import UserIdGenerator
from app.domain.ports.auth_gateway import AuthGateway
from app.infrastructure.adapters.password_hasher_bcrypt import BcryptPasswordHasher, PasswordPepper
from app.infrastructure.adapters.user_id_generator_uuid import UuidUserIdGenerator
from app.setup.config.security import PasswordSettings
from app.setup.config.privy import PrivySettings


class ApplicationProvider(Provider):
    scope = Scope.REQUEST

    # Chat interactors
    chat_command_interactors = provide_all(
        CreateConversation,
        DeleteConversation,
        scope=Scope.REQUEST,
    )
    
    @provide(scope=Scope.REQUEST)
    def provide_send_message(
        self,
        repository: ConversationRepository,
        agent_gateway: AgentGateway,
        transaction_manager: TransactionManager,
    ) -> SendMessage:
        """
        Provide SendMessage with only required dependencies.
        Optional dependencies will use their defaults.
        """
        return SendMessage(
            repository=repository,
            agent_gateway=agent_gateway,
            transaction_manager=transaction_manager,
        )
    
    chat_query_interactors = provide_all(
        GetConversation,
        ListConversations,
        GetMessages,
        scope=Scope.REQUEST,
    )

    @provide(scope=Scope.REQUEST)
    def provide_admin_chat_analytics_service(
        self,
        conversation_repository: ConversationRepository,
        analytics_repository: AnalyticsRepository,
    ) -> AdminChatAnalyticsService:
        """Provide admin chat analytics service for admin dashboard endpoints."""
        return AdminChatAnalyticsService(
            conversation_repository=conversation_repository,
            analytics_repository=analytics_repository,
        )

    # Services
    services = provide_all(
        CurrentUserService,
        UserService,
        AuthService,
    )

    # Domain service dependencies
    user_id_generator = provide(source=UuidUserIdGenerator, provides=UserIdGenerator)
    password_hasher = provide(source=BcryptPasswordHasher, provides=PasswordHasher)

    @staticmethod
    def _password_pepper(settings: PasswordSettings) -> PasswordPepper:  # factory
        return PasswordPepper(settings.pepper)

    pepper = provide(source=_password_pepper)

    # Ports Auth
    access_revoker = provide(
        source=AuthSessionAccessRevoker,
        provides=AccessRevoker,
    )
    identity_provider = provide(
        source=AuthSessionIdentityProvider,
        provides=IdentityProvider,
    )

    # Ports Persistence
    tx_manager = provide(
        source=SqlaMainTransactionManager,
        provides=TransactionManager,
    )
    flusher = provide(
        source=SqlaMainFlusher,
        provides=Flusher,
    )
    user_command_gateway = provide(
        source=SqlaUserDataMapper,
        provides=UserCommandGateway,
    )
    user_query_gateway = provide(
        source=SqlaUserReader,
        provides=UserQueryGateway,
    )
    
    # Metrics
    metrics_repository = provide(
        source=UserMetricsRepositorySqla,
        provides=UserMetricsRepository,
    )

    # Privy Client
    @staticmethod
    def _privy_client(settings: PrivySettings) -> PrivyClient:
        return PrivyClient(settings)

    privy_client = provide(source=_privy_client, scope=Scope.REQUEST)

    # Commands
    commands = provide_all(
        ActivateUserInteractor,
        ChangePasswordInteractor,
        DeactivateUserInteractor,
        GrantAdminInteractor,
        RevokeAdminInteractor,
        UpgradeToAdminInteractor,
        ChangeRoleInteractor,
        PrivyLogin,
        ExportWallet,
        UpdatePrivyWallet,
        # Privy policy management (admin)
        CreatePrivyPolicy,
        GetPrivyPolicy,
        UpdatePrivyPolicy,
        CreatePrivyPolicyRule,
        UpdatePrivyPolicyRule,
        DeletePrivyPolicyRule,
    )

    # Queries
    query_services = provide_all(
        ListUsersQueryService,
        ListWalletsQueryService,
        SearchCountriesQueryService,
        SearchCitiesQueryService,
        ListStatesByCountryQueryService,
        GetPrivyWalletDetails,
        ListPrivyPolicies,
    )
