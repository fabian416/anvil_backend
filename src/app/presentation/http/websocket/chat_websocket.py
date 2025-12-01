"""
WebSocket handler for real-time chat updates.
"""

import json
import logging
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for chat.
    
    Maintains active connections per conversation and broadcasts
    messages to all connected clients.
    """
    
    def __init__(self):
        """Initialize connection manager."""
        # Map conversation_id -> Set of WebSocket connections
        self._active_connections: Dict[str, Set[WebSocket]] = {}
        # Map WebSocket -> conversation_id for cleanup
        self._connection_to_conversation: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: UUID) -> None:
        """
        Accept a new WebSocket connection for a conversation.
        
        Args:
            websocket: WebSocket connection
            conversation_id: Conversation identifier
        """
        await websocket.accept()
        
        conversation_key = str(conversation_id)
        
        # Add to conversation's connection set
        if conversation_key not in self._active_connections:
            self._active_connections[conversation_key] = set()
        
        self._active_connections[conversation_key].add(websocket)
        self._connection_to_conversation[websocket] = conversation_key
        
        logger.info(
            f"WebSocket connected for conversation {conversation_id}. "
            f"Total connections: {len(self._active_connections[conversation_key])}"
        )
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket not in self._connection_to_conversation:
            return
        
        conversation_key = self._connection_to_conversation[websocket]
        
        # Remove from conversation set
        if conversation_key in self._active_connections:
            self._active_connections[conversation_key].discard(websocket)
            
            # Clean up empty conversation sets
            if not self._active_connections[conversation_key]:
                del self._active_connections[conversation_key]
        
        # Remove from tracking
        del self._connection_to_conversation[websocket]
        
        logger.info(f"WebSocket disconnected for conversation {conversation_key}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket.
        
        Args:
            message: Message data to send
            websocket: Target WebSocket connection
        """
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_conversation(
        self,
        conversation_id: UUID,
        message: dict,
    ) -> None:
        """
        Broadcast a message to all connections for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            message: Message data to broadcast
        """
        conversation_key = str(conversation_id)
        
        if conversation_key not in self._active_connections:
            return
        
        # Get copy of connections to avoid modification during iteration
        connections = list(self._active_connections[conversation_key])
        
        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
            except Exception as e:
                logger.error(
                    f"Error broadcasting to WebSocket in conversation {conversation_id}: {e}"
                )
                # Remove failed connection
                self.disconnect(websocket)
    
    def get_connection_count(self, conversation_id: UUID) -> int:
        """
        Get number of active connections for a conversation.
        
        Args:
            conversation_id: Conversation identifier
        
        Returns:
            Number of active connections
        """
        conversation_key = str(conversation_id)
        return len(self._active_connections.get(conversation_key, set()))


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: UUID,
) -> None:
    """
    WebSocket endpoint for real-time chat updates.
    
    Args:
        websocket: WebSocket connection
        conversation_id: Conversation identifier
    """
    await manager.connect(websocket, conversation_id)
    
    try:
        while True:
            # Receive messages from client (heartbeat/ping)
            data = await websocket.receive_text()
            
            # Echo back for heartbeat
            if data == "ping":
                await manager.send_personal_message(
                    {"type": "pong"},
                    websocket
                )
            else:
                # Log other messages but don't process
                logger.debug(f"Received WebSocket message: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client disconnected from conversation {conversation_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for conversation {conversation_id}: {e}")
        manager.disconnect(websocket)
