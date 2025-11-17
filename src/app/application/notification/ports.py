from abc import abstractmethod
from typing import Protocol


class NotificationRepository(Protocol):
    @abstractmethod
    async def read_by_user_paginated(
        self,
        *,
        user_id: int,
        offset: int,
        limit: int,
    ) -> list[dict]: ...


