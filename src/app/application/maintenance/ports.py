from abc import abstractmethod
from datetime import datetime
from typing import Protocol

from app.domain.value_objects.user_id import UserId


class AuthSessionRepository(Protocol):
    @abstractmethod
    async def delete_expired(self, now: datetime) -> int: ...


class PasswordResetRepository(Protocol):
    @abstractmethod
    async def delete_expired(self, now: datetime) -> int: ...


