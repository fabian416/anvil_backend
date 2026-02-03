"""
Legacy Session Recorder - No-Op Implementation.

The legacy 'sessions' table has been deprecated in favor of 'auth_sessions'.
This no-op implementation maintains API compatibility while the SessionRecorder
protocol is still referenced in auth handlers.

TODO: Remove SessionRecorder protocol and this adapter once all auth handlers
are updated to use only auth_sessions.
"""

from datetime import datetime

from app.application.common.ports.session_recorder import SessionRecorder


class SqlaSessionRecorder(SessionRecorder):
    """
    No-op session recorder.

    The legacy sessions table has been removed. Authentication is now
    handled entirely by auth_sessions via AuthSessionService.
    This adapter exists only for API compatibility during migration.
    """

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
        # Authentication handled by auth_sessions via AuthSessionService
        pass
