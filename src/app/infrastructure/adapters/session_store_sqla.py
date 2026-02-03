"""
Legacy Session Store - No-Op Implementation.

The legacy 'sessions' table has been deprecated in favor of 'auth_sessions'.
This no-op implementation maintains API compatibility while the SessionStore
protocol is still referenced.

TODO: Remove SessionStore protocol and this adapter once all references
are updated to use only auth_sessions.
"""

from datetime import datetime

from app.application.common.ports.session_store import SessionRow, SessionStore


class SqlaSessionStore(SessionStore):
    """
    No-op session store.

    The legacy sessions table has been removed. Authentication is now
    handled entirely by auth_sessions.
    This adapter exists only for API compatibility during migration.
    """

    async def read_by_refresh_token(self, refresh_token: str) -> SessionRow | None:
        # No-op: legacy sessions table removed
        # Return None to indicate no session found
        return None

    async def update_tokens(
        self,
        *,
        refresh_token: str,
        new_access_token: str,
        new_refresh_token: str,
        ip_address: str | None,
        user_agent: str | None,
        last_activity: datetime,
    ) -> None:
        # No-op: legacy sessions table removed
        pass

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
    ) -> None:
        # No-op: legacy sessions table removed
        pass
