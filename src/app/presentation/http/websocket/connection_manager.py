"""WebSocket Connection Manager.

Manages active WebSocket connections, broadcasting, and connection lifecycle.

Features:
    - Connection tracking per user/session
    - Broadcast to specific users or all connections
    - Automatic cleanup on disconnect
    - Heartbeat/ping support
    - Connection statistics
"""
from typing import Dict, Set, Optional, Any
from uuid import UUID
import logging
import asyncio
from datetime import datetime, UTC

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.
    
    Tracks connections per user and session, enabling:
    - Targeted messages to specific users/sessions
    - Broadcast messages to all connected clients
    - Connection health monitoring
    - Automatic cleanup
    
    Usage:
        manager = ConnectionManager()
        
        # Connect
        await manager.connect(websocket, user_id, session_id)
        
        # Send to specific user
        await manager.send_to_user(user_id, {"type": "message", "data": "..."})
        
        # Broadcast to all
        await manager.broadcast({"type": "system", "data": "..."})
        
        # Disconnect
        await manager.disconnect(websocket, user_id, session_id)
    """
    
    def __init__(self):
        """Initialize connection manager."""
        # Active connections: {user_id: {session_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        
        # Reverse lookup: {websocket_id: (user_id, session_id)}
        self.connection_lookup: Dict[int, tuple[str, str]] = {}
        
        # Connection metadata: {websocket_id: metadata}
        self.connection_metadata: Dict[int, Dict[str, Any]] = {}
        
        # Statistics
        self.total_connections = 0
        self.total_messages_sent = 0
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket instance
            user_id: User identifier
            session_id: Session identifier (optional)
            metadata: Additional connection metadata
        """
        # Accept connection
        await websocket.accept()
        
        # Use websocket id() as unique identifier
        ws_id = id(websocket)
        
        # Generate session_id if not provided
        if not session_id:
            session_id = f"ws_{ws_id}"
        
        # Store connection
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][session_id] = websocket
        self.connection_lookup[ws_id] = (user_id, session_id)
        
        # Store metadata
        self.connection_metadata[ws_id] = {
            "user_id": user_id,
            "session_id": session_id,
            "connected_at": datetime.now(UTC).isoformat(),
            "messages_sent": 0,
            "messages_received": 0,
            **(metadata or {}),
        }
        
        self.total_connections += 1
        
        logger.info(
            f"WebSocket connected: user={user_id}, session={session_id}, "
            f"total_active={self.get_active_count()}"
        )
    
    async def disconnect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Disconnect and unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket instance
            user_id: User identifier (optional, will lookup if not provided)
            session_id: Session identifier (optional, will lookup if not provided)
        """
        ws_id = id(websocket)
        
        # Lookup user_id and session_id if not provided
        if not user_id or not session_id:
            lookup = self.connection_lookup.get(ws_id)
            if lookup:
                user_id, session_id = lookup
        
        if not user_id or not session_id:
            logger.warning(f"Cannot disconnect unknown WebSocket: {ws_id}")
            return
        
        # Remove connection
        if user_id in self.active_connections:
            if session_id in self.active_connections[user_id]:
                del self.active_connections[user_id][session_id]
            
            # Clean up empty user dict
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove lookup
        if ws_id in self.connection_lookup:
            del self.connection_lookup[ws_id]
        
        # Remove metadata
        if ws_id in self.connection_metadata:
            del self.connection_metadata[ws_id]
        
        logger.info(
            f"WebSocket disconnected: user={user_id}, session={session_id}, "
            f"total_active={self.get_active_count()}"
        )
    
    async def send_to_user(
        self,
        user_id: str,
        message: Dict[str, Any],
        session_id: Optional[str] = None,
    ):
        """
        Send message to specific user (all sessions or specific session).
        
        Args:
            user_id: User identifier
            message: Message to send (will be JSON-encoded)
            session_id: Specific session (None = all user sessions)
        """
        if user_id not in self.active_connections:
            logger.warning(f"User {user_id} has no active connections")
            return
        
        sessions = self.active_connections[user_id]
        
        # Filter to specific session if provided
        if session_id:
            if session_id not in sessions:
                logger.warning(f"Session {session_id} not found for user {user_id}")
                return
            sessions = {session_id: sessions[session_id]}
        
        # Send to all matching sessions (copy items to avoid dict modification during iteration)
        failed_sessions: list[tuple[str, Any]] = []
        for sid, websocket in list(sessions.items()):
            try:
                await websocket.send_json(message)
                self.total_messages_sent += 1
                
                # Update metadata
                ws_id = id(websocket)
                if ws_id in self.connection_metadata:
                    self.connection_metadata[ws_id]["messages_sent"] += 1
                
            except Exception as e:
                logger.error(
                    f"Error sending to user {user_id} session {sid}: {e}",
                    exc_info=True,
                )
                # Mark for disconnection (don't modify dict during iteration)
                failed_sessions.append((sid, websocket))
        
        # Disconnect broken connections after iteration
        for sid, websocket in failed_sessions:
            await self.disconnect(websocket, user_id, sid)
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude_user: Optional[str] = None,
    ):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message to send (will be JSON-encoded)
            exclude_user: User to exclude from broadcast (optional)
        """
        disconnected = []
        
        for user_id, sessions in self.active_connections.items():
            # Skip excluded user
            if exclude_user and user_id == exclude_user:
                continue
            
            for session_id, websocket in sessions.items():
                try:
                    await websocket.send_json(message)
                    self.total_messages_sent += 1
                    
                    # Update metadata
                    ws_id = id(websocket)
                    if ws_id in self.connection_metadata:
                        self.connection_metadata[ws_id]["messages_sent"] += 1
                    
                except Exception as e:
                    logger.error(
                        f"Error broadcasting to user {user_id} session {session_id}: {e}"
                    )
                    disconnected.append((websocket, user_id, session_id))
        
        # Clean up disconnected
        for websocket, user_id, session_id in disconnected:
            await self.disconnect(websocket, user_id, session_id)
    
    async def send_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
    ):
        """
        Send message to specific session (finds across all users).
        
        Args:
            session_id: Session identifier
            message: Message to send
        """
        for user_id, sessions in self.active_connections.items():
            if session_id in sessions:
                websocket = sessions[session_id]
                try:
                    await websocket.send_json(message)
                    self.total_messages_sent += 1
                    
                    # Update metadata
                    ws_id = id(websocket)
                    if ws_id in self.connection_metadata:
                        self.connection_metadata[ws_id]["messages_sent"] += 1
                    
                except Exception as e:
                    logger.error(
                        f"Error sending to session {session_id}: {e}",
                        exc_info=True,
                    )
                    await self.disconnect(websocket, user_id, session_id)
                
                return
        
        logger.warning(f"Session {session_id} not found")
    
    def get_active_count(self) -> int:
        """
        Get count of active connections.
        
        Returns:
            Number of active connections
        """
        return sum(len(sessions) for sessions in self.active_connections.values())
    
    def get_user_sessions(self, user_id: str) -> list[str]:
        """
        Get all active session IDs for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of session IDs
        """
        if user_id not in self.active_connections:
            return []
        return list(self.active_connections[user_id].keys())
    
    def is_user_connected(self, user_id: str) -> bool:
        """
        Check if user has any active connections.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if user is connected
        """
        return user_id in self.active_connections and bool(
            self.active_connections[user_id]
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "active_connections": self.get_active_count(),
            "active_users": len(self.active_connections),
            "total_connections": self.total_connections,
            "total_messages_sent": self.total_messages_sent,
            "connections_per_user": {
                user_id: len(sessions)
                for user_id, sessions in self.active_connections.items()
            },
        }


# Global connection manager instance
connection_manager = ConnectionManager()
