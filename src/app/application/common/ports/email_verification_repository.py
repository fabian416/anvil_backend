from abc import abstractmethod
from datetime import datetime
from typing import Protocol


class EmailVerificationRow(Protocol):
    id: int
    user_id: int
    token: str
    expires_at: datetime
    is_used: bool
    created_at: datetime
    updated_at: datetime


class EmailVerificationRepository(Protocol):
    @abstractmethod
    async def add(self, *, user_id: int, token: str, expires_at: datetime) -> None: ...

    @abstractmethod
    async def read_by_user_and_token(self, *, user_id: int, token: str) -> dict | None: ...

    @abstractmethod
    async def mark_used(self, *, id_: int) -> None: ...

    @abstractmethod
    async def delete_by_id(self, *, id_: int) -> None: ...


