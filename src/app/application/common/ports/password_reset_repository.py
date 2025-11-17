from abc import abstractmethod
from datetime import datetime
from typing import Protocol


class PasswordResetRepository(Protocol):
    @abstractmethod
    async def add(self, *, user_id: int, token: str, expires_at: datetime) -> None: ...

    @abstractmethod
    async def invalidate_all_for_user(self, *, user_id: int) -> None: ...

    @abstractmethod
    async def read_by_token(self, *, token: str) -> dict | None: ...

    @abstractmethod
    async def mark_used(self, *, id_: int) -> None: ...

    @abstractmethod
    async def delete_by_id(self, *, id_: int) -> None: ...


