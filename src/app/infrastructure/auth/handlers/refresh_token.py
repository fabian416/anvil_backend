import logging
from dataclasses import dataclass
from datetime import datetime

from app.application.common.ports.session_store import SessionStore
from app.domain.value_objects.user_id import UserId
from app.infrastructure.auth.session.service import AuthSessionService
from app.presentation.http.auth.refresh_token_processor_jwt import (
    JwtRefreshTokenProcessor,
)
from app.infrastructure.auth.exceptions import AuthenticationError

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshTokenRequest:
    refresh_token: str
    ip_address: str | None = None
    user_agent: str | None = None


class RefreshTokenHandler:
    def __init__(
        self,
        session_store: SessionStore,
        auth_session_service: AuthSessionService,
        refresh_token_processor: JwtRefreshTokenProcessor,
    ):
        self._session_store = session_store
        self._auth_session_service = auth_session_service
        self._refresh_token_processor = refresh_token_processor

    async def execute(self, request_data: RefreshTokenRequest) -> dict:
        # Look up existing session by opaque refresh token instead of decoding JWT
        row = await self._session_store.read_by_refresh_token(request_data.refresh_token)
        if row is None:
            raise AuthenticationError("Invalid or expired refresh token")
        user_id = UserId(int(row["user_id"]))  # type: ignore[index]

        # If an access token is provided (cookie), validate it's a logged-in user and matches payload
        try:
            current_user_id = await self._auth_session_service.get_authenticated_user_id()
            if current_user_id.value != user_id.value:
                # Optional: we could invalidate the old session here
                log.debug(
                    "Refresh token sub does not match current access token user. Sub: %s, Current: %s",
                    user_id.value,
                    current_user_id.value,
                )
        except AuthenticationError:
            # No valid access token available; proceed with refresh-token only flow
            pass
        auth_session, access_token = await self._auth_session_service.create_session(user_id)  # type: ignore[arg-type]

        # Prefer updating existing row; if not found, add a new one
        await self._session_store.update_tokens(
            refresh_token=request_data.refresh_token,
            new_access_token=access_token,
            new_refresh_token=auth_session.refresh_token or "",
            ip_address=request_data.ip_address,
            user_agent=request_data.user_agent,
            last_activity=datetime.utcnow(),
        )

        return {
            "message": "Token refreshed successfully",
            "status": "success",
            "tokens": {
                "access_token": access_token,
                "refresh_token": auth_session.refresh_token,
                "token_type": "bearer",
                "expires_in": 900,
            },
        }


