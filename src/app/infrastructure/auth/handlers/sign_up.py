import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypedDict

from app.application.common.ports.flusher import Flusher
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.services.current_user import CurrentUserService
from app.domain.exceptions.user import EmailAlreadyExistsError
from app.domain.exceptions.location import CountryNotFoundError, CityNotFoundInCountryError
from app.domain.services.user import UserService
from app.domain.value_objects.raw_password.raw_password import RawPassword
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.language import Language
from app.domain.value_objects.country_id import CountryId
from app.domain.value_objects.city_id import CityId
from app.infrastructure.auth.exceptions import (
    AlreadyAuthenticatedError,
    AuthenticationError,
)
from app.infrastructure.auth.handlers.constants import (
    AUTH_ALREADY_AUTHENTICATED,
)
from app.infrastructure.auth.session.service import AuthSessionService
from app.application.common.ports.session_recorder import SessionRecorder
from app.application.common.ports.country_query_gateway import CountryQueryGateway
from app.application.common.ports.city_query_gateway import CityQueryGateway
from app.application.common.ports.email_verification_repository import EmailVerificationRepository
from app.infrastructure.celery.app import celery_app

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class SignUpRequest:
    email: str
    first_name: str
    last_name: str
    password: str
    country_id: int | None = None
    city_id: int | None = None
    language: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class SignUpResponse(TypedDict):
    id: int
    session_id: str
    user_id: int
    expires_at: str
    access_token: str
    refresh_token: str
    token_type: str
    is_active: bool


class SignUpHandler:
    """
    - Open to everyone.
    - Registers a new user with validation and uniqueness checks.
    - Passwords are peppered, salted, and stored as hashes.
    - A logged-in user cannot sign up until the session expires or is terminated.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_service: UserService,
        user_command_gateway: UserCommandGateway,
        flusher: Flusher,
        transaction_manager: TransactionManager,
        auth_session_service: AuthSessionService,
        session_recorder: SessionRecorder,
        country_query_gateway: CountryQueryGateway,
        city_query_gateway: CityQueryGateway,
        email_verification_repo: EmailVerificationRepository):
        self._current_user_service = current_user_service
        self._user_service = user_service
        self._user_command_gateway = user_command_gateway
        self._flusher = flusher
        self._transaction_manager = transaction_manager
        self._auth_session_service = auth_session_service
        self._session_recorder = session_recorder
        self._country_query_gateway = country_query_gateway
        self._city_query_gateway = city_query_gateway
        self._email_verification_repo = email_verification_repo

    async def execute(self, request_data: SignUpRequest) -> SignUpResponse:
        """
        :raises AlreadyAuthenticatedError:
        :raises AuthorizationError:
        :raises DataMapperError:
        :raises DomainFieldError:
        :raises RoleAssignmentNotPermittedError:
        :raises EmailAlreadyExistsError:
        """
        log.info("Sign up: started. Email: '%s'.", request_data.email)

        try:
            await self._current_user_service.get_current_user()
            raise AlreadyAuthenticatedError(AUTH_ALREADY_AUTHENTICATED)
        except AuthenticationError:
            pass

        email = Email(request_data.email)
        first_name = FirstName(request_data.first_name)
        last_name = LastName(request_data.last_name)
        password = RawPassword(request_data.password)
        language = Language(request_data.language) if request_data.language else Language("en")

        # Optional fields validation and mapping
        country_id = None
        city_id = None
        if request_data.country_id is not None:
            c_id = request_data.country_id
            if not await self._country_query_gateway.exists(c_id):
                raise CountryNotFoundError(request_data.country_id)
            country_id = c_id
        if request_data.city_id is not None and country_id is not None:
            if not await self._city_query_gateway.exists_in_country(request_data.city_id, country_id):
                raise CityNotFoundInCountryError(request_data.city_id, country_id)
            # Translate external city_id to internal PK for FK storage
            city_pk = await self._city_query_gateway.get_pk_in_country(request_data.city_id, country_id)
            city_id = city_pk

        user = self._user_service.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            language=language,
            country_id=CountryId(country_id) if country_id is not None else None,
            city_id=CityId(city_id) if city_id is not None else None,
        )

        await self._user_command_gateway.add(user)

        try:
            await self._flusher.flush()
        except EmailAlreadyExistsError:
            raise

        await self._transaction_manager.commit()

        # Auto-login: create auth session and persist session row
        auth_session, access_token = await self._auth_session_service.create_session(user.id_)
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
 
        log.info("Sign up: done. Email: '%s'.", user.email.value)
        # Create email verification token and send email
        from secrets import token_urlsafe
        token = token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        await self._email_verification_repo.add(user_id=user.id_.value, token=token, expires_at=expires_at)
        try:
            celery_app.send_task(
                "tasks.email_tasks.send_verification_email",
                kwargs={
                    "to_email": user.email.value,
                    "verification_url": token,
                },
            )
        except Exception as e:  # noqa: BLE001
            log.warning("Failed to enqueue verification email: %s", e)
        return SignUpResponse(
            id=user.id_.value,
            session_id=auth_session.id_,
            user_id=user.id_.value,
            expires_at=auth_session.expiration.isoformat(),
            access_token=access_token,
            refresh_token=auth_session.refresh_token or "",
            token_type="bearer",
            is_active=True,
        )
