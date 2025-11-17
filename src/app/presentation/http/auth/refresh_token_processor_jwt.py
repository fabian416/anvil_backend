import logging
from typing import Any, TypedDict, cast

import jwt

from app.domain.enums.user_role import UserRole
from app.presentation.http.auth.access_token_processor_jwt import (
    JwtAlgorithm,
    JwtSecret,
)

log = logging.getLogger(__name__)

class RefreshPayload(TypedDict):
    sub: str
    email: str
    role: str
    exp: int


class JwtRefreshTokenProcessor:
    def __init__(self, secret: JwtSecret, algorithm: JwtAlgorithm):
        self._secret = secret
        self._algorithm = algorithm

    def encode(self, *, user_id: int, email: str, role: UserRole, exp_ts: int) -> str:
        payload = RefreshPayload(
            sub=str(user_id),
            email=email,
            role=role.value,
            exp=exp_ts,
        )
        return jwt.encode(cast(dict[str, Any], payload), key=self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> RefreshPayload | None:
        try:
            payload = jwt.decode(token, key=self._secret, algorithms=[self._algorithm])
            return cast(RefreshPayload, payload)
        except jwt.PyJWTError as error:  # includes DecodeError, ExpiredSignatureError, etc.
            log.debug("Refresh token decode failed: %s", error)
            return None


