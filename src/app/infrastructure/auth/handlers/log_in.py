import logging
from dataclasses import dataclass

from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.user import User
from app.domain.exceptions.user import UserNotFoundByEmailError
from app.domain.services.user import UserService
from app.domain.value_objects.raw_password.raw_password import RawPassword
from app.domain.value_objects.email import Email
from app.infrastructure.auth.exceptions import (
    AlreadyAuthenticatedError,
    AuthenticationError,
)
from app.infrastructure.auth.handlers.constants import (
    AUTH_ACCOUNT_INACTIVE,
    AUTH_ALREADY_AUTHENTICATED,
    AUTH_ACCOUNT_BLOCKED,
)
from app.infrastructure.auth.session.constants import AUTH_INVALID_PASSWORD
from app.infrastructure.auth.session.service import AuthSessionService
from app.application.common.ports.session_recorder import SessionRecorder
from app.domain.value_objects.ip_address import IpAddress
from app.application.chat.services.user_context_service import UserContextService
from app.domain.ports.chat_repository import ChatUserRepository
from datetime import datetime, UTC

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class LogInRequest:
    email: str
    password: str
    ip_address: str | None = None
    user_agent: str | None = None


class LogInHandler:
    """
    - Open to everyone.
    - Authenticates registered user,
    sets a JWT access token with a session ID in cookies,
    and creates a session.
    - A logged-in user cannot log in again
    until the session expires or is terminated.
    - Authentication renews automatically
    when accessing protected routes before expiration.
    - If the JWT is invalid, expired, or the session is terminated,
    the user loses authentication.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_command_gateway: UserCommandGateway,
        user_service: UserService,
        auth_session_service: AuthSessionService,
        transaction_manager: TransactionManager,
        session_recorder: SessionRecorder,
        # Context-aware agents dependencies (optional for backwards compat)
        user_context_service: UserContextService | None = None,
        chat_user_repository: ChatUserRepository | None = None,
    ):
        self._current_user_service = current_user_service
        self._user_command_gateway = user_command_gateway
        self._user_service = user_service
        self._auth_session_service = auth_session_service
        self._transaction_manager = transaction_manager
        self._session_recorder = session_recorder
        # Context-aware agents
        self._user_context_service = user_context_service
        self._chat_user_repository = chat_user_repository

    async def execute(self, request_data: LogInRequest) -> None | dict:
        """
        :raises AlreadyAuthenticatedError:
        :raises AuthorizationError:
        :raises DataMapperError:
        :raises DomainFieldError:
        :raises UserNotFoundByEmailError:
        """
        log.info("Log in: started. Email: '%s'.", request_data.email)

        try:
            await self._current_user_service.get_current_user()
            raise AlreadyAuthenticatedError(AUTH_ALREADY_AUTHENTICATED)
        except AuthenticationError:
            pass

        email = Email(request_data.email)
        password = RawPassword(request_data.password)

        user: User | None = await self._user_command_gateway.read_by_email(
            email,
            for_update=True,
        )
        if user is None:
            raise UserNotFoundByEmailError(email)

        # Check if user has a valid password hash (Privy users don't have passwords)
        # A valid bcrypt hash starts with "$2" and has length >= 50
        has_valid_password = (
            user.password
            and user.password.value
            and len(user.password.value) >= 50
            and user.password.value.decode("utf-8", errors="ignore").startswith("$2")
        )
        if not has_valid_password:
            # User was created via Privy (wallet/social login) - no password
            raise AuthenticationError(
                "This account was created via wallet or social login. "
                "Please use the same method to sign in."
            )

        if not self._user_service.is_password_valid(user, password):
            self._user_service.increment_login_retry_count(user)
            await self._transaction_manager.commit()
            raise AuthenticationError(AUTH_INVALID_PASSWORD)

        if not user.is_active.value:
            raise AuthenticationError(AUTH_ACCOUNT_INACTIVE)

        if user.is_blocked.value:
            raise AuthenticationError(AUTH_ACCOUNT_BLOCKED)

        self._user_service.record_successful_login(user)

        # Update last_ip on login
        if request_data.ip_address:
            user.last_ip = IpAddress.from_optional(request_data.ip_address)

        # Persist last_login/updated_at/last_ip to DB
        await self._user_command_gateway.update(user)
        await self._transaction_manager.commit()

        auth_session, access_token = await self._auth_session_service.create_session(
            user.id_
        )
        # Persist session row similar to baseapi
        await self._session_recorder.add(
            user_id=user.id_.value,
            access_token=access_token,
            refresh_token=auth_session.refresh_token or "",
            token_type="bearer",
            ip_address=request_data.ip_address,
            user_agent=request_data.user_agent,
            created_at=datetime.now(UTC),
            expires_at=auth_session.expiration,
            last_activity=datetime.now(UTC),
            is_active=True,
        )
        await self._transaction_manager.commit()

        # Ensure user context exists for context-aware agents
        if self._user_context_service and self._chat_user_repository:
            await self._ensure_user_context(user)

        log.info(
            "Log in: done. User, ID: '%s', email '%s', role '%s'.",
            user.id_.value,
            user.email.value,
            user.role.value,
        )
        return {
            "session_id": auth_session.id_,
            "user_id": user.id_.value,
            "expires_at": auth_session.expiration.isoformat(),
            "refresh_token": auth_session.refresh_token,
            "token_type": "bearer",
            "is_active": True,
            "access_token": access_token,
        }

    async def _ensure_user_context(self, user: User) -> None:
        """
        Ensure user context entry exists for context-aware agents.

        This is called on login to create the context if it doesn't exist.
        For existing users, the Celery task will update their context.
        """
        try:
            # Get or create chat user (UUID-based)
            chat_user = await self._chat_user_repository.get_by_user_id(user.id_.value)

            if not chat_user:
                # Create chat user entry
                from app.domain.chat.entities import ChatUser
                from uuid import uuid4

                chat_user = ChatUser(
                    id_=uuid4(),
                    user_id=user.id_.value,
                    email=user.email.value,
                    subscription_tier="free",
                    total_messages=0,
                    language="en",
                    chat_preferences={},
                    first_seen_at=datetime.now(UTC),
                    last_seen_at=datetime.now(UTC),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                chat_user = await self._chat_user_repository.create(chat_user)

            # Check if context already exists
            existing = await self._user_context_service.exists(chat_user.id_)
            if existing:
                log.debug(
                    "User context already exists for user %s (chat_user_id=%s)",
                    user.id_.value,
                    chat_user.id_,
                )
                return

            # Create user context with defaults
            await self._user_context_service.create_for_new_user(
                chat_user_id=chat_user.id_,
                legacy_user_id=user.id_.value,
                wallet_address=str(user.primary_wallet_address.value)
                if user.primary_wallet_address
                else None,
                wallet_provider="email",  # Regular login is email-based
                language="en",
            )

            log.info(
                "Created user context for user %s (chat_user_id=%s)",
                user.id_.value,
                chat_user.id_,
            )

        except Exception as e:
            # Log but don't fail login if context creation fails
            log.warning(
                "Failed to ensure user context for user %s: %s",
                user.id_.value,
                e,
            )
