import logging

from starlette.requests import Request

from app.infrastructure.auth.session.model import AuthSession
from app.infrastructure.auth.session.ports.transport import AuthSessionTransport
from app.presentation.http.auth.access_token_processor_jwt import (
    JwtAccessTokenProcessor,
)

log = logging.getLogger(__name__)


class JwtHeaderAuthSessionTransport(AuthSessionTransport):
    def __init__(
        self,
        request: Request,
        access_token_processor: JwtAccessTokenProcessor,
    ):
        self._request = request
        self._access_token_processor = access_token_processor

    def deliver(self, auth_session: AuthSession) -> str:
        # For header-based transport, just generate and expose the token
        access_token = self._access_token_processor.encode(auth_session)
        # Controllers already include it in the response body; clients set it as Authorization header
        log.debug(
            "%s Session ID: %s",
            "Delivered auth session token via response body",
            auth_session.id_,
        )
        return access_token

    def extract_id(self) -> str | None:
        auth_header = self._request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.removeprefix("Bearer ").strip()
        return self._access_token_processor.decode_auth_session_id(token)

    def remove_current(self) -> None:
        # No-op for header transport
        pass


