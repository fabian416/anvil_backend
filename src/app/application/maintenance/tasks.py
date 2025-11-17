from datetime import datetime, timezone

from app.application.maintenance.ports import (
    AuthSessionRepository,
    PasswordResetRepository,
)


class CleanupExpiredSessionsTask:
    def __init__(self, repo: AuthSessionRepository):
        self._repo = repo

    async def run(self) -> int:
        now = datetime.now(tz=timezone.utc)
        return await self._repo.delete_expired(now)


class CleanupExpiredPasswordResetsTask:
    def __init__(self, repo: PasswordResetRepository):
        self._repo = repo

    async def run(self) -> int:
        now = datetime.now(tz=timezone.utc)
        return await self._repo.delete_expired(now)


