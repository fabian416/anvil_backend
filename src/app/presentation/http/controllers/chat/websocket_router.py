"""
WebSocket router for chat real-time updates.
"""

from uuid import UUID

from fastapi import APIRouter, WebSocket, Query
from fastapi.exceptions import WebSocketException

from app.presentation.http.websocket.chat_websocket import (
    chat_websocket as websocket_endpoint,
)


def create_chat_websocket_router() -> APIRouter:
    """
    Create WebSocket router for chat.

    Returns:
        APIRouter with WebSocket endpoint
    """
    router = APIRouter(
        prefix="/user/chat",
        tags=["chat-websocket"],
    )

    @router.websocket("/ws/{conversation_id}")
    async def chat_websocket(
        websocket: WebSocket,
        conversation_id: UUID,
        token: str = Query(..., description="JWT authentication token"),
    ):
        """
        WebSocket endpoint for real-time chat updates.

        Connect to receive real-time messages for a conversation.

        Query Parameters:
        - token: JWT authentication token

        Message Format (received):
        ```json
        {
            "type": "message",
            "message": {
                "id": "uuid",
                "role": "agent",
                "content": "...",
                "created_at": "2025-12-01T12:00:00Z"
            }
        }
        ```

        Heartbeat:
        - Send "ping" to keep connection alive
        - Receive "pong" response
        """
        # TODO: Validate JWT token
        # For now, accept all connections
        # In production, verify token before accepting

        try:
            await websocket_endpoint(websocket, conversation_id)
        except Exception as e:
            raise WebSocketException(code=1011, reason=str(e))

    return router
