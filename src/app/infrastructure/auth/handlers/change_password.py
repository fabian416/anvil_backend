import logging
from dataclasses import dataclass
from datetime import datetime

from app.application.common.ports.session_recorder import SessionRecorder
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.services.current_user import CurrentUserService
from app.domain.services.user import UserService
from app.domain.value_objects.raw_password.raw_password import RawPassword
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.auth.session.service import AuthSessionService


log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeOwnPasswordRequest:
    current_password: str
    new_password: str
    confirm_password: str
    ip_address: str | None = None
    user_agent: str | None = None


class ChangeOwnPasswordHandler:
    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_service: UserService,
        user_command_gateway: UserCommandGateway,
        transaction_manager: TransactionManager,
        auth_session_service: AuthSessionService,
        session_recorder: SessionRecorder,
    ) -> None:
        self._current_user_service = current_user_service
        self._user_service = user_service
        self._user_gateway = user_command_gateway
        self._tx = transaction_manager
        self._auth_session_service = auth_session_service
        self._session_recorder = session_recorder

    async def execute(self, request: ChangeOwnPasswordRequest) -> dict:
        if request.new_password != request.confirm_password:
            raise ValueError("New password and confirmation do not match")

        user = await self._current_user_service.get_current_user()

        # Validate current password
        if not self._user_service.is_password_valid(user, RawPassword(request.current_password)):
            raise AuthenticationError("Invalid current password")

        # Apply new password
        self._user_service.change_password(user, RawPassword(request.new_password))
        await self._user_gateway.update(user)
        await self._tx.commit()

        # Invalidate all sessions and create a fresh one
        await self._auth_session_service.invalidate_all_sessions_for_user(user.id_)
        auth_session, access_token = await self._auth_session_service.create_session(user.id_)

        # Record session row
        await self._session_recorder.add(
            user_id=user.id_.value,
            access_token=access_token,
            refresh_token=auth_session.refresh_token or "",
            token_type="bearer",
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            created_at=datetime.utcnow(),
            expires_at=auth_session.expiration,
            last_activity=datetime.utcnow(),
            is_active=True,
        )
        await self._tx.commit()

        return {
            "message": "Password changed successfully",
            "tokens": {
                "access_token": access_token,
                "refresh_token": auth_session.refresh_token,
                "token_type": "bearer",
                "expires_in": 900,
            },
        }


