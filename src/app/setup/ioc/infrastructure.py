from dishka import Provider, Scope, provide, provide_all

from app.infrastructure.adapters.main_transaction_manager_sqla import (
    SqlaMainTransactionManager,
)
from app.infrastructure.adapters.user_data_mapper_sqla import (
    SqlaUserDataMapper,
)
from app.infrastructure.adapters.user_reader_sqla import SqlaUserReader
from app.infrastructure.adapters.country_reader_sqla import SqlaCountryReader
from app.infrastructure.adapters.city_reader_sqla import SqlaCityReader
from app.infrastructure.adapters.session_recorder_sqla import SqlaSessionRecorder
from app.infrastructure.auth.adapters.data_mapper_sqla import (
    SqlaAuthSessionDataMapper,
)
from app.infrastructure.atlas.readers_sqla import (
    SqlaCityReader as AtlasSqlaCityReader,
    SqlaCountryReader as AtlasSqlaCountryReader,
)
from app.infrastructure.auth.adapters.identity_provider import (
    AuthSessionIdentityProvider,
)
from app.infrastructure.auth.adapters.transaction_manager_sqla import (
    SqlaAuthSessionTransactionManager,
)
from app.infrastructure.auth.handlers.log_in import LogInHandler
from app.infrastructure.auth.handlers.log_out import LogOutHandler
from app.infrastructure.auth.handlers.sign_up import SignUpHandler
from app.infrastructure.auth.handlers.refresh_token import RefreshTokenHandler
from app.infrastructure.auth.handlers.verify_email import VerifyEmailHandler
from app.infrastructure.auth.handlers.send_email_verification import SendEmailVerificationHandler
from app.infrastructure.auth.handlers.password_reset import ForgotPasswordHandler, ResetPasswordHandler
from app.infrastructure.auth.handlers.change_password import ChangeOwnPasswordHandler
from app.infrastructure.subscription.handlers.init_subscriptions import InitSubscriptionsHandler
from app.infrastructure.subscription.handlers.get_subscriptions import GetSubscriptionsHandler
from app.infrastructure.subscription.handlers.customer_subscription import CreateSubscriptionHandler
from app.infrastructure.auth.handlers.account_me import GetMeHandler, UpdateMeHandler
from app.domain.ports.auth_gateway import AuthGateway
from app.infrastructure.auth.adapters.auth_gateway_sqla import AuthGatewaySqla
from app.infrastructure.auth.handlers.jwt_handler import JwtHandler
from app.infrastructure.auth.session.id_generator_str import (
    StrAuthSessionIdGenerator,
)
from app.infrastructure.auth.refresh_token.generator import RefreshTokenGenerator
from app.infrastructure.auth.session.ports.gateway import AuthSessionGateway
from app.infrastructure.auth.session.ports.transaction_manager import (
    AuthSessionTransactionManager,
)
from app.infrastructure.auth.session.ports.transport import AuthSessionTransport
from app.infrastructure.auth.session.service import AuthSessionService
from app.infrastructure.auth.session.timer_utc import UtcAuthSessionTimer
from app.application.common.ports.session_recorder import SessionRecorder
from app.application.atlas.ports import CityReader as AtlasCityReader, CountryReader as AtlasCountryReader
from app.application.common.ports.session_store import SessionStore
from app.application.common.ports.country_query_gateway import CountryQueryGateway
from app.application.common.ports.city_query_gateway import CityQueryGateway
from app.infrastructure.persistence_sqla.provider import (
    get_async_engine,
    get_async_session_factory,
    get_auth_async_session,
    get_main_async_session,
)
from app.presentation.http.auth.adapters.session_transport_jwt_header import (
    JwtHeaderAuthSessionTransport,
)
from app.infrastructure.atlas.handlers.init_cities import InitCitiesHandler
from app.infrastructure.atlas.handlers.init_countries import InitCountriesHandler
from app.infrastructure.adapters.session_store_sqla import SqlaSessionStore
from app.infrastructure.maintenance.repositories_sqla import (
    SqlaAuthSessionRepository,
    SqlaPasswordResetRepository,
)
from app.application.maintenance.ports import (
    AuthSessionRepository,
    PasswordResetRepository,
)
from app.application.common.ports.password_reset_repository import (
    PasswordResetRepository as CommonPasswordResetRepository,
)
from app.application.common.ports.email_verification_repository import EmailVerificationRepository
from app.infrastructure.adapters.email_verification_repository_sqla import (
    SqlaEmailVerificationRepository,
)
from app.infrastructure.adapters.password_reset_repository_sqla import (
    SqlaPasswordResetRepository as SqlaCommonPasswordResetRepository,
)
from app.application.subscription.ports import SubscriptionRepository
from app.infrastructure.adapters.subscription_repository_sqla import (
    SqlaSubscriptionRepository,
)
from app.application.subscription.ports import SubscriptionUserRepository, PaymentRepository
from app.infrastructure.adapters.subscription_user_repository_sqla import (
    SqlaSubscriptionUserRepository,
)
from app.infrastructure.adapters.payment_repository_sqla import (
    SqlaPaymentRepository,
)
from app.application.notification.ports import NotificationRepository
from app.infrastructure.adapters.notification_repository_sqla import (
    SqlaNotificationRepository,
)


class InfrastructureProvider(Provider):
    scope = Scope.REQUEST

    # Auth Services
    auth_session_service = provide(source=AuthSessionService)

    # Auth Ports Persistence
    auth_session_gateway = provide(
        source=SqlaAuthSessionDataMapper,
        provides=AuthSessionGateway,
    )
    # Session Recorder Port
    session_recorder = provide(
        source=SqlaSessionRecorder,
        provides=SessionRecorder,
    )
    # Session Store Port
    session_store = provide(
        source=SqlaSessionStore,
        provides=SessionStore,
    )
    auth_session_tx_manager = provide(
        source=SqlaAuthSessionTransactionManager,
        provides=AuthSessionTransactionManager,
    )

    # Auth Ports
    auth_session_transport = provide(
        source=JwtHeaderAuthSessionTransport,
        provides=AuthSessionTransport,
    )
    country_query_gateway = provide(
        source=SqlaCountryReader,
        provides=CountryQueryGateway,
    )
    city_query_gateway = provide(
        source=SqlaCityReader,
        provides=CityQueryGateway,
    )
    atlas_country_reader = provide(
        source=AtlasSqlaCountryReader,
        provides=AtlasCountryReader,
    )
    atlas_city_reader = provide(
        source=AtlasSqlaCityReader,
        provides=AtlasCityReader,
    )
    # These repositories depend on MainAsyncSession, so they must be REQUEST-scoped
    auth_session_repo = provide(
        source=SqlaAuthSessionRepository,
        provides=AuthSessionRepository,
        scope=Scope.REQUEST,
    )
    password_reset_repo = provide(
        source=SqlaPasswordResetRepository,
        provides=PasswordResetRepository,
        scope=Scope.REQUEST,
    )
    # Common Password Reset Port (create/read/mark used)
    common_password_reset_repo = provide(
        source=SqlaCommonPasswordResetRepository,
        provides=CommonPasswordResetRepository,
    )
    subscription_repo = provide(
        source=SqlaSubscriptionRepository,
        provides=SubscriptionRepository,
    )
    subscription_user_repo = provide(
        source=SqlaSubscriptionUserRepository,
        provides=SubscriptionUserRepository,
    )
    payment_repo = provide(
        source=SqlaPaymentRepository,
        provides=PaymentRepository,
    )
    notification_repo = provide(
        source=SqlaNotificationRepository,
        provides=NotificationRepository,
    )
    email_verification_repo = provide(
        source=SqlaEmailVerificationRepository,
        provides=EmailVerificationRepository,
    )
    
    # Auth Gateway
    auth_gateway = provide(
        source=AuthGatewaySqla,
        provides=AuthGateway,
    )

    # Infrastructure Handlers
    infra_handlers = provide_all(
        SignUpHandler,
        LogInHandler,
        LogOutHandler,
        RefreshTokenHandler,
        VerifyEmailHandler,
        SendEmailVerificationHandler,
        ForgotPasswordHandler,
        ResetPasswordHandler,
        ChangeOwnPasswordHandler,
        InitSubscriptionsHandler,
        GetSubscriptionsHandler,
        CreateSubscriptionHandler,
        GetMeHandler,
        UpdateMeHandler,
    )

    # Concrete Objects
    infra_objects = provide_all(
        StrAuthSessionIdGenerator,
        UtcAuthSessionTimer,
        RefreshTokenGenerator,
        AuthSessionIdentityProvider,
        SqlaAuthSessionDataMapper,
        SqlaAuthSessionTransactionManager,
        SqlaSessionRecorder,
        SqlaSessionStore,
        SqlaUserDataMapper,
        SqlaUserReader,
        SqlaMainTransactionManager,
        InitCountriesHandler,
        InitCitiesHandler,
        JwtHandler,
    )


def infrastructure_provider() -> InfrastructureProvider:
    provider = InfrastructureProvider()

    # SQLA Persistence
    # Engine and session factory are APP-scoped (shared across requests)
    provider.provide(
        source=get_async_engine,
        scope=Scope.APP,
    )
    provider.provide(
        source=get_async_session_factory,
        scope=Scope.APP,
    )
    # Sessions MUST be REQUEST-scoped to avoid concurrent operation errors
    # Each request gets its own session instance from the shared factory
    provider.provide(
        source=get_main_async_session,
        scope=Scope.REQUEST,
    )
    provider.provide(
        source=get_auth_async_session,
        scope=Scope.REQUEST,
    )
    return provider
