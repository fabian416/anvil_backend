from abc import abstractmethod
from datetime import datetime
from typing import Protocol


class SessionRecorder(Protocol):
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


