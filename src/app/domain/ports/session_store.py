"""
Session store port.

Domain-defined interface for WebSocket session management.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat.websocket_session import WebSocketSession
from app.domain.enums.connection_state import ConnectionState


class SessionStore(ABC):
    """
    Port for WebSocket session storage and management.

    Handles session lifecycle including creation, state updates,
    activity tracking, and cleanup of expired sessions.
    """

    @abstractmethod
    async def create_session(self, session: WebSocketSession) -> bool:
        """
        Store new WebSocket session.

        Args:
            session: Session to store

        Returns:
            True if stored successfully
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[WebSocketSession]:
        """
        Retrieve session by session ID.

        Args:
            session_id: Unique session identifier

        Returns:
            WebSocketSession or None if not found
        """
        pass

    @abstractmethod
    async def get_user_sessions(
        self,
        user_id: UUID,
        state_filter: Optional[ConnectionState] = None,
    ) -> List[WebSocketSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier
            state_filter: Optional filter by connection state

        Returns:
            List of user sessions
        """
        pass

    @abstractmethod
    async def get_conversation_sessions(
        self,
        conversation_id: UUID,
    ) -> List[WebSocketSession]:
        """
        Get all active sessions for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of active sessions in conversation
        """
        pass

    @abstractmethod
    async def update_session_state(
        self,
        session_id: str,
        state: ConnectionState,
    ) -> bool:
        """
        Update session connection state.

        Args:
            session_id: Session identifier
            state: New connection state

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def update_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp.

        Args:
            session_id: Session identifier

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def disconnect_session(self, session_id: str) -> bool:
        """
        Mark session as disconnected.

        Sets disconnection timestamp and updates state.

        Args:
            session_id: Session identifier

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """
        Remove session from store.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def mark_idle_sessions(self) -> int:
        """
        Mark sessions as idle based on inactivity threshold.

        Scans all CONNECTED sessions and marks those exceeding
        idle threshold as IDLE.

        Returns:
            Number of sessions marked as idle
        """
        pass

    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from store.

        Deletes sessions that have been disconnected beyond
        the expiration threshold.

        Returns:
            Number of sessions cleaned up
        """
        pass

    @abstractmethod
    async def get_session_count(
        self,
        user_id: Optional[UUID] = None,
        state: Optional[ConnectionState] = None,
    ) -> int:
        """
        Get count of sessions matching criteria.

        Args:
            user_id: Optional user filter
            state: Optional state filter

        Returns:
            Number of matching sessions
        """
        pass

    @abstractmethod
    async def get_active_user_count(self) -> int:
        """
        Get count of users with active sessions.

        Returns:
            Number of unique users with CONNECTED or IDLE sessions
        """
        pass

    @abstractmethod
    async def disconnect_user_sessions(self, user_id: UUID) -> int:
        """
        Disconnect all sessions for a user.

        Useful for logout operations or security events.

        Args:
            user_id: User identifier

        Returns:
            Number of sessions disconnected
        """
        pass
