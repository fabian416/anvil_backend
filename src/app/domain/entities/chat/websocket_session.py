"""
WebSocket session entity.

Domain entity representing an active WebSocket connection session
for real-time chat communication.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from app.domain.enums.connection_state import ConnectionState


@dataclass(slots=True)
class WebSocketSession:
    """
    WebSocket session entity.

    Represents an active or historical WebSocket connection with
    session state, timing information, and metadata.

    Business Rules:
    - Sessions become IDLE after 5 minutes of inactivity
    - Sessions expire after 24 hours of disconnection
    - Each user can have multiple concurrent sessions (multi-device)
    - Session metadata stores client info and permissions
    """

    id: UUID
    session_id: str
    user_id: UUID
    conversation_id: Optional[UUID]
    connection_state: ConnectionState
    connected_at: datetime
    last_activity: datetime
    disconnected_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Business rule constants
    IDLE_THRESHOLD_SECONDS = 300  # 5 minutes
    EXPIRATION_HOURS = 24  # 24 hours after disconnect

    @classmethod
    def create(
        cls,
        session_id: str,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "WebSocketSession":
        """
        Create new WebSocket session.

        Args:
            session_id: Unique session identifier
            user_id: User owning the session
            conversation_id: Associated conversation (if any)
            metadata: Client information and permissions

        Returns:
            WebSocketSession instance with CONNECTED state
        """
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            connection_state=ConnectionState.CONNECTED,
            connected_at=now,
            last_activity=now,
            metadata=metadata or {},
        )

    def update_activity(self) -> None:
        """
        Update last activity timestamp.

        If session was IDLE, transitions back to CONNECTED.
        """
        self.last_activity = datetime.now(UTC)
        if self.connection_state == ConnectionState.IDLE:
            self.connection_state = ConnectionState.CONNECTED

    def disconnect(self) -> None:
        """
        Mark session as disconnected.

        Sets disconnection timestamp and transitions to DISCONNECTED state.
        """
        self.connection_state = ConnectionState.DISCONNECTED
        self.disconnected_at = datetime.now(UTC)

    def mark_idle(self) -> None:
        """
        Mark session as idle due to inactivity.

        Should be called when session exceeds IDLE_THRESHOLD_SECONDS.
        """
        if self.connection_state == ConnectionState.CONNECTED:
            self.connection_state = ConnectionState.IDLE

    def mark_reconnecting(self) -> None:
        """Mark session as attempting to reconnect."""
        self.connection_state = ConnectionState.RECONNECTING

    def is_idle(self) -> bool:
        """
        Check if session should be marked as idle.

        Returns:
            True if last activity exceeds idle threshold
        """
        if self.connection_state != ConnectionState.CONNECTED:
            return False

        time_since_activity = datetime.now(UTC) - self.last_activity
        return time_since_activity.total_seconds() > self.IDLE_THRESHOLD_SECONDS

    def is_expired(self) -> bool:
        """
        Check if session should be cleaned up.

        Sessions expire after EXPIRATION_HOURS of being disconnected.

        Returns:
            True if session should be removed
        """
        if self.connection_state != ConnectionState.DISCONNECTED:
            return False

        if not self.disconnected_at:
            return False

        time_since_disconnect = datetime.now(UTC) - self.disconnected_at
        return time_since_disconnect > timedelta(hours=self.EXPIRATION_HOURS)

    def get_duration(self) -> timedelta:
        """
        Get session connection duration.

        Returns:
            Time connected (or total duration if disconnected)
        """
        end_time = self.disconnected_at or datetime.now(UTC)
        return end_time - self.connected_at

    def get_idle_time(self) -> timedelta:
        """
        Get time since last activity.

        Returns:
            Time since last activity
        """
        return datetime.now(UTC) - self.last_activity

    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """
        Update session metadata.

        Args:
            updates: Metadata fields to update
        """
        self.metadata.update(updates)

    def get_client_info(self) -> Dict[str, Any]:
        """
        Get client information from metadata.

        Returns:
            Client info dict (user_agent, ip_address, platform, etc.)
        """
        return self.metadata.get("client_info", {})

    def get_permissions(self) -> Dict[str, bool]:
        """
        Get session permissions from metadata.

        Returns:
            Permission flags dict
        """
        return self.metadata.get("permissions", {})

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of session
        """
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "user_id": str(self.user_id),
            "conversation_id": str(self.conversation_id)
            if self.conversation_id
            else None,
            "connection_state": self.connection_state.value,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "disconnected_at": self.disconnected_at.isoformat()
            if self.disconnected_at
            else None,
            "metadata": self.metadata,
            "duration_seconds": self.get_duration().total_seconds(),
            "idle_seconds": self.get_idle_time().total_seconds(),
            "is_expired": self.is_expired(),
        }
