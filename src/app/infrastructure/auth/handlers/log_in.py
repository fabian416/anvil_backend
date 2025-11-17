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
from datetime import datetime

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
    ):
        self._current_user_service = current_user_service
        self._user_command_gateway = user_command_gateway
        self._user_service = user_service
        self._auth_session_service = auth_session_service
        self._transaction_manager = transaction_manager
        self._session_recorder = session_recorder

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

        if not self._user_service.is_password_valid(user, password):
            self._user_service.increment_login_retry_count(user)
            await self._transaction_manager.commit()
            raise AuthenticationError(AUTH_INVALID_PASSWORD)

        if not user.is_active.value:
            raise AuthenticationError(AUTH_ACCOUNT_INACTIVE)

        if user.is_blocked.value:
            raise AuthenticationError(AUTH_ACCOUNT_BLOCKED)

        self._user_service.record_successful_login(user)
        # Persist last_login/updated_at to DB
        await self._user_command_gateway.update(user)
        await self._transaction_manager.commit()

        auth_session, access_token = await self._auth_session_service.create_session(user.id_)
        # Persist session row similar to baseapi
        await self._session_recorder.add(
            user_id=user.id_.value,
            access_token=access_token,
            refresh_token=auth_session.refresh_token or "",
            token_type="bearer",
            ip_address=request_data.ip_address,
            user_agent=request_data.user_agent,
            created_at=datetime.utcnow(),
            expires_at=auth_session.expiration,
            last_activity=datetime.utcnow(),
            is_active=True,
        )
        await self._transaction_manager.commit()

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
