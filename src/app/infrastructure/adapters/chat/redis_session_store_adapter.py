"""
Redis-based session store adapter for WebSocket sessions.

High-performance Redis implementation of SessionStore port with
connection pooling, efficient querying, and automatic cleanup.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, UTC
import json

from redis.asyncio import Redis, ConnectionPool

from app.domain.ports.session_store import SessionStore
from app.domain.entities.chat.websocket_session import WebSocketSession
from app.domain.enums.connection_state import ConnectionState


class RedisSessionStoreAdapter(SessionStore):
    """
    Redis adapter for WebSocket session management.

    Architecture:
    - Hash (ws:session:{session_id}): Session data storage
    - Set (ws:user:{user_id}:sessions): User's session IDs
    - Set (ws:conversation:{conversation_id}:sessions): Conversation session IDs
    - Set (ws:state:{state}:sessions): Sessions by state for efficient queries
    - Sorted Set (ws:activity): Sessions ordered by last activity for idle detection
    - Sorted Set (ws:disconnected): Disconnected sessions for cleanup

    Features:
    - Connection pooling for optimal performance
    - Atomic operations for state consistency
    - Efficient bulk queries using Redis Sets
    - Automatic TTL management
    - Pipeline support for batch operations
    """

    def __init__(
        self,
        redis_client: Redis,
        key_prefix: str = "ws",
        pool_size: int = 10,
    ) -> None:
        """
        Initialize Redis session store adapter.

        Args:
            redis_client: Async Redis client instance
            key_prefix: Redis key prefix for namespacing
            pool_size: Connection pool size (for reference)
        """
        self._redis = redis_client
        self._prefix = key_prefix
        self._pool_size = pool_size

    # ============= Key Generation Methods =============

    def _session_key(self, session_id: str) -> str:
        """Get Redis key for session data hash."""
        return f"{self._prefix}:session:{session_id}"

    def _user_sessions_key(self, user_id: UUID) -> str:
        """Get Redis key for user's session set."""
        return f"{self._prefix}:user:{user_id}:sessions"

    def _conversation_sessions_key(self, conversation_id: UUID) -> str:
        """Get Redis key for conversation's session set."""
        return f"{self._prefix}:conversation:{conversation_id}:sessions"

    def _state_sessions_key(self, state: ConnectionState) -> str:
        """Get Redis key for state-based session set."""
        return f"{self._prefix}:state:{state.value}:sessions"

    def _activity_key(self) -> str:
        """Get Redis key for activity sorted set."""
        return f"{self._prefix}:activity"

    def _disconnected_key(self) -> str:
        """Get Redis key for disconnected sessions sorted set."""
        return f"{self._prefix}:disconnected"

    # ============= Serialization Methods =============

    def _serialize_session(self, session: WebSocketSession) -> Dict[str, str]:
        """
        Serialize session to Redis hash format.

        Args:
            session: Session to serialize

        Returns:
            Dictionary for Redis HSET
        """
        return {
            "id": str(session.id),
            "session_id": session.session_id,
            "user_id": str(session.user_id),
            "conversation_id": str(session.conversation_id)
            if session.conversation_id
            else "",
            "connection_state": session.connection_state.value,
            "connected_at": session.connected_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "disconnected_at": session.disconnected_at.isoformat()
            if session.disconnected_at
            else "",
            "metadata": json.dumps(session.metadata),
        }

    def _deserialize_session(
        self, data: Dict[bytes, bytes]
    ) -> Optional[WebSocketSession]:
        """
        Deserialize session from Redis hash data.

        Args:
            data: Redis hash data

        Returns:
            WebSocketSession or None if data is invalid
        """
        if not data:
            return None

        try:
            conversation_id_str = data.get(b"conversation_id", b"").decode()
            disconnected_at_str = data.get(b"disconnected_at", b"").decode()

            return WebSocketSession(
                id=UUID(data[b"id"].decode()),
                session_id=data[b"session_id"].decode(),
                user_id=UUID(data[b"user_id"].decode()),
                conversation_id=UUID(conversation_id_str)
                if conversation_id_str
                else None,
                connection_state=ConnectionState(data[b"connection_state"].decode()),
                connected_at=datetime.fromisoformat(data[b"connected_at"].decode()),
                last_activity=datetime.fromisoformat(data[b"last_activity"].decode()),
                disconnected_at=datetime.fromisoformat(disconnected_at_str)
                if disconnected_at_str
                else None,
                metadata=json.loads(data[b"metadata"].decode()),
            )
        except (KeyError, ValueError, json.JSONDecodeError):
            return None

    # ============= Core Session Operations =============

    async def create_session(self, session: WebSocketSession) -> bool:
        """
        Store new WebSocket session.

        Creates session hash and updates all index sets atomically.

        Args:
            session: Session to store

        Returns:
            True if stored successfully
        """
        try:
            session_key = self._session_key(session.session_id)
            user_sessions_key = self._user_sessions_key(session.user_id)
            state_sessions_key = self._state_sessions_key(session.connection_state)
            activity_key = self._activity_key()

            # Serialize session data
            session_data = self._serialize_session(session)

            # Use pipeline for atomic operations
            async with self._redis.pipeline(transaction=True) as pipe:
                # Store session data
                pipe.hset(session_key, mapping=session_data)  # type: ignore

                # Set TTL (7 days for all sessions)
                pipe.expire(session_key, 7 * 24 * 3600)

                # Add to user's session set
                pipe.sadd(user_sessions_key, session.session_id)
                pipe.expire(user_sessions_key, 7 * 24 * 3600)

                # Add to conversation set if applicable
                if session.conversation_id:
                    conv_key = self._conversation_sessions_key(session.conversation_id)
                    pipe.sadd(conv_key, session.session_id)
                    pipe.expire(conv_key, 7 * 24 * 3600)

                # Add to state index
                pipe.sadd(state_sessions_key, session.session_id)

                # Add to activity sorted set (score = last_activity timestamp)
                activity_score = session.last_activity.timestamp()
                pipe.zadd(activity_key, {session.session_id: activity_score})

                await pipe.execute()

            return True

        except Exception:
            return False

    async def get_session(self, session_id: str) -> Optional[WebSocketSession]:
        """
        Retrieve session by session ID.

        Args:
            session_id: Unique session identifier

        Returns:
            WebSocketSession or None if not found
        """
        try:
            session_key = self._session_key(session_id)
            session_data = await self._redis.hgetall(session_key)

            return self._deserialize_session(session_data)

        except Exception:
            return None

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
        try:
            user_sessions_key = self._user_sessions_key(user_id)

            # Get session IDs
            session_ids = await self._redis.smembers(user_sessions_key)

            if not session_ids:
                return []

            # Fetch session data
            sessions: List[WebSocketSession] = []
            for session_id_bytes in session_ids:
                session_id = session_id_bytes.decode()
                session = await self.get_session(session_id)

                if session:
                    # Apply state filter if specified
                    if state_filter is None or session.connection_state == state_filter:
                        sessions.append(session)

            return sessions

        except Exception:
            return []

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
        try:
            conv_key = self._conversation_sessions_key(conversation_id)
            session_ids = await self._redis.smembers(conv_key)

            if not session_ids:
                return []

            # Fetch session data
            sessions: List[WebSocketSession] = []
            for session_id_bytes in session_ids:
                session_id = session_id_bytes.decode()
                session = await self.get_session(session_id)

                if session and session.connection_state in (
                    ConnectionState.CONNECTED,
                    ConnectionState.IDLE,
                ):
                    sessions.append(session)

            return sessions

        except Exception:
            return []

    # ============= State Management =============

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
        try:
            # Get current session
            session = await self.get_session(session_id)
            if not session:
                return False

            old_state = session.connection_state
            session_key = self._session_key(session_id)

            # Update state in hash
            await self._redis.hset(session_key, "connection_state", state.value)

            # Update state indices
            old_state_key = self._state_sessions_key(old_state)
            new_state_key = self._state_sessions_key(state)

            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.srem(old_state_key, session_id)
                pipe.sadd(new_state_key, session_id)
                await pipe.execute()

            return True

        except Exception:
            return False

    async def update_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp.

        Args:
            session_id: Session identifier

        Returns:
            True if updated successfully
        """
        try:
            session_key = self._session_key(session_id)
            activity_key = self._activity_key()
            now = datetime.now(UTC)

            # Check if session exists
            exists = await self._redis.exists(session_key)
            if not exists:
                return False

            async with self._redis.pipeline(transaction=True) as pipe:
                # Update last_activity in session hash
                pipe.hset(session_key, "last_activity", now.isoformat())

                # Update activity sorted set score
                pipe.zadd(activity_key, {session_id: now.timestamp()})

                # If session was IDLE, transition to CONNECTED
                session_data = await self._redis.hget(session_key, "connection_state")
                if session_data and session_data.decode() == ConnectionState.IDLE.value:
                    pipe.hset(
                        session_key, "connection_state", ConnectionState.CONNECTED.value
                    )

                    # Update state indices
                    idle_key = self._state_sessions_key(ConnectionState.IDLE)
                    connected_key = self._state_sessions_key(ConnectionState.CONNECTED)
                    pipe.srem(idle_key, session_id)
                    pipe.sadd(connected_key, session_id)

                await pipe.execute()

            return True

        except Exception:
            return False

    async def disconnect_session(self, session_id: str) -> bool:
        """
        Mark session as disconnected.

        Sets disconnection timestamp and updates state.

        Args:
            session_id: Session identifier

        Returns:
            True if updated successfully
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False

            session_key = self._session_key(session_id)
            disconnected_key = self._disconnected_key()
            now = datetime.now(UTC)

            async with self._redis.pipeline(transaction=True) as pipe:
                # Update session hash
                pipe.hset(
                    session_key, "connection_state", ConnectionState.DISCONNECTED.value
                )
                pipe.hset(session_key, "disconnected_at", now.isoformat())

                # Update state indices
                old_state_key = self._state_sessions_key(session.connection_state)
                new_state_key = self._state_sessions_key(ConnectionState.DISCONNECTED)
                pipe.srem(old_state_key, session_id)
                pipe.sadd(new_state_key, session_id)

                # Add to disconnected sorted set for cleanup (score = disconnect time)
                pipe.zadd(disconnected_key, {session_id: now.timestamp()})

                # Remove from activity tracking
                activity_key = self._activity_key()
                pipe.zrem(activity_key, session_id)

                await pipe.execute()

            return True

        except Exception:
            return False

    # ============= Cleanup and Maintenance =============

    async def delete_session(self, session_id: str) -> bool:
        """
        Remove session from store.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted successfully
        """
        try:
            # Get session data to clean up indices
            session = await self.get_session(session_id)
            if not session:
                return False

            session_key = self._session_key(session_id)
            user_sessions_key = self._user_sessions_key(session.user_id)
            state_sessions_key = self._state_sessions_key(session.connection_state)
            activity_key = self._activity_key()
            disconnected_key = self._disconnected_key()

            async with self._redis.pipeline(transaction=True) as pipe:
                # Delete session hash
                pipe.delete(session_key)

                # Remove from user's session set
                pipe.srem(user_sessions_key, session_id)

                # Remove from conversation set if applicable
                if session.conversation_id:
                    conv_key = self._conversation_sessions_key(session.conversation_id)
                    pipe.srem(conv_key, session_id)

                # Remove from state index
                pipe.srem(state_sessions_key, session_id)

                # Remove from activity and disconnected sets
                pipe.zrem(activity_key, session_id)
                pipe.zrem(disconnected_key, session_id)

                await pipe.execute()

            return True

        except Exception:
            return False

    async def mark_idle_sessions(self) -> int:
        """
        Mark sessions as idle based on inactivity threshold.

        Scans all CONNECTED sessions and marks those exceeding
        idle threshold as IDLE.

        Returns:
            Number of sessions marked as idle
        """
        try:
            activity_key = self._activity_key()
            connected_key = self._state_sessions_key(ConnectionState.CONNECTED)
            idle_key = self._state_sessions_key(ConnectionState.IDLE)

            # Calculate idle threshold timestamp
            now = datetime.now(UTC)
            idle_threshold = now.timestamp() - WebSocketSession.IDLE_THRESHOLD_SECONDS

            # Get sessions with activity before threshold
            idle_session_ids = await self._redis.zrangebyscore(
                activity_key,
                "-inf",
                idle_threshold,
            )

            if not idle_session_ids:
                return 0

            marked_count = 0

            # Process each potentially idle session
            for session_id_bytes in idle_session_ids:
                session_id = session_id_bytes.decode()
                session = await self.get_session(session_id)

                if session and session.connection_state == ConnectionState.CONNECTED:
                    session_key = self._session_key(session_id)

                    async with self._redis.pipeline(transaction=True) as pipe:
                        # Update state to IDLE
                        pipe.hset(
                            session_key, "connection_state", ConnectionState.IDLE.value
                        )

                        # Update state indices
                        pipe.srem(connected_key, session_id)
                        pipe.sadd(idle_key, session_id)

                        await pipe.execute()

                    marked_count += 1

            return marked_count

        except Exception:
            return 0

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from store.

        Deletes sessions that have been disconnected beyond
        the expiration threshold.

        Returns:
            Number of sessions cleaned up
        """
        try:
            disconnected_key = self._disconnected_key()

            # Calculate expiration threshold timestamp
            now = datetime.now(UTC)
            expiration_threshold = now.timestamp() - (
                WebSocketSession.EXPIRATION_HOURS * 3600
            )

            # Get expired session IDs
            expired_session_ids = await self._redis.zrangebyscore(
                disconnected_key,
                "-inf",
                expiration_threshold,
            )

            if not expired_session_ids:
                return 0

            # Delete each expired session
            cleanup_count = 0
            for session_id_bytes in expired_session_ids:
                session_id = session_id_bytes.decode()
                if await self.delete_session(session_id):
                    cleanup_count += 1

            return cleanup_count

        except Exception:
            return 0

    # ============= Query and Statistics =============

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
        try:
            if user_id and state:
                # Get user sessions and filter by state
                sessions = await self.get_user_sessions(user_id, state)
                return len(sessions)

            elif user_id:
                # Count user's sessions
                user_sessions_key = self._user_sessions_key(user_id)
                count = await self._redis.scard(user_sessions_key)
                return count or 0

            elif state:
                # Count sessions by state
                state_sessions_key = self._state_sessions_key(state)
                count = await self._redis.scard(state_sessions_key)
                return count or 0

            else:
                # Count all sessions
                activity_key = self._activity_key()
                disconnected_key = self._disconnected_key()
                active_count = await self._redis.zcard(activity_key) or 0
                disconnected_count = await self._redis.zcard(disconnected_key) or 0
                return active_count + disconnected_count

        except Exception:
            return 0

    async def get_active_user_count(self) -> int:
        """
        Get count of users with active sessions.

        Returns:
            Number of unique users with CONNECTED or IDLE sessions
        """
        try:
            # Get all active session IDs
            connected_key = self._state_sessions_key(ConnectionState.CONNECTED)
            idle_key = self._state_sessions_key(ConnectionState.IDLE)

            connected_sessions = await self._redis.smembers(connected_key)
            idle_sessions = await self._redis.smembers(idle_key)

            all_active_sessions = set(connected_sessions) | set(idle_sessions)

            # Collect unique user IDs
            user_ids = set()
            for session_id_bytes in all_active_sessions:
                session_id = session_id_bytes.decode()
                session = await self.get_session(session_id)
                if session:
                    user_ids.add(session.user_id)

            return len(user_ids)

        except Exception:
            return 0

    async def disconnect_user_sessions(self, user_id: UUID) -> int:
        """
        Disconnect all sessions for a user.

        Useful for logout operations or security events.

        Args:
            user_id: User identifier

        Returns:
            Number of sessions disconnected
        """
        try:
            # Get all user sessions
            sessions = await self.get_user_sessions(user_id)

            disconnected_count = 0
            for session in sessions:
                if session.connection_state != ConnectionState.DISCONNECTED:
                    if await self.disconnect_session(session.session_id):
                        disconnected_count += 1

            return disconnected_count

        except Exception:
            return 0
