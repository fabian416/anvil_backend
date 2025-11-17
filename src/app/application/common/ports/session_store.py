from abc import abstractmethod
from datetime import datetime
from typing import Protocol, TypedDict


class SessionRow(TypedDict, total=False):
    user_id: int
    access_token: str
    refresh_token: str
    token_type: str
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_active: bool


class SessionStore(Protocol):
    @abstractmethod
    async def read_by_refresh_token(self, refresh_token: str) -> SessionRow | None: ...

    @abstractmethod
    async def update_tokens(
        self,
        *,
        refresh_token: str,
        new_access_token: str,
        new_refresh_token: str,
        ip_address: str | None,
        user_agent: str | None,
        last_activity: datetime,
    ) -> None: ...

    @abstractmethod
    async def add(
        self,
        *,
        user_id: int,
        access_token: str,
        refresh_token: str,
        token_type: str,
        ip_address: str | None,
        user_agent: str | None,
        created_at: datetime,
        expires_at: datetime,
        last_activity: datetime,
        is_active: bool,
    ) -> None: ...


