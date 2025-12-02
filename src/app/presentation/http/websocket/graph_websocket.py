"""
GraphRAG WebSocket Handler

Real-time updates for graph changes, protocol updates, and risk alerts.
Enhanced with GraphEventBroadcaster for centralized event management.
"""

from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.websockets import WebSocketState
import json
import logging
import asyncio
import redis.asyncio as aioredis

from app.infrastructure.websocket.event_broadcaster import GraphEventBroadcaster

logger = logging.getLogger(__name__)

router = APIRouter()


class GraphWebSocketManager:
    """
    Manages WebSocket connections for graph updates.
    
    Features:
    - Subscribe to protocol updates
    - Subscribe to risk alerts  
    - Subscribe to graph changes
    - Connection pooling
    - Automatic reconnection
    """
    
    def __init__(self):
        """Initialize WebSocket manager"""
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: dict[WebSocket, Set[str]] = {}
        self._redis: aioredis.Redis | None = None
        self._pubsub_task: asyncio.Task | None = None
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Accept and track new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User identifier
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = set()
        
        logger.info(f"WebSocket connected: user={user_id}, total={len(self.active_connections)}")
        
        # Start Redis pub/sub listener if not running
        if self._pubsub_task is None or self._pubsub_task.done():
            self._pubsub_task = asyncio.create_task(self._listen_redis())
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        self.active_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)
        
        logger.info(f"WebSocket disconnected, remaining={len(self.active_connections)}")
    
    async def subscribe(
        self,
        websocket: WebSocket,
        channel: str,
    ) -> None:
        """
        Subscribe connection to a channel.
        
        Channels:
        - protocol:{protocol_id} - Specific protocol updates
        - risk:alerts - Risk alerts
        - graph:changes - Graph structure changes
        - all - All updates
        
        Args:
            websocket: WebSocket connection
            channel: Channel name
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(channel)
            
            await self.send_personal_message(
                {"type": "subscribed", "channel": channel},
                websocket,
            )
            
            logger.debug(f"Subscribed to channel: {channel}")
    
    async def unsubscribe(
        self,
        websocket: WebSocket,
        channel: str,
    ) -> None:
        """Unsubscribe from a channel"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(channel)
            
            await self.send_personal_message(
                {"type": "unsubscribed", "channel": channel},
                websocket,
            )
    
    async def send_personal_message(
        self,
        message: dict,
        websocket: WebSocket,
    ) -> None:
        """Send message to specific connection"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(
        self,
        message: dict,
        channel: str = "all",
    ) -> None:
        """
        Broadcast message to all subscribed connections.
        
        Args:
            message: Message to broadcast
            channel: Target channel (default: all)
        """
        disconnected = []
        sent = 0
        
        for connection in self.active_connections:
            # Check if connection is subscribed to channel
            subscriptions = self.subscriptions.get(connection, set())
            if channel in subscriptions or "all" in subscriptions:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(message)
                        sent += 1
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)
        
        logger.debug(f"Broadcast to {sent} connections on channel '{channel}'")
    
    async def _listen_redis(self) -> None:
        """Listen to Redis pub/sub for graph events"""
        try:
            # Connect to Redis
            redis_url = "redis://localhost:6379/0"  # TODO: Get from config
            self._redis = await aioredis.from_url(redis_url)
            
            # Subscribe to channels
            pubsub = self._redis.pubsub()
            await pubsub.subscribe(
                "graph:protocol_update",
                "graph:risk_alert",
                "graph:structure_change",
            )
            
            logger.info("Redis pub/sub listener started")
            
            # Listen for messages
            async for message in pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                    data = message["data"].decode() if isinstance(message["data"], bytes) else message["data"]
                    
                    try:
                        event = json.loads(data)
                        await self._handle_redis_event(channel, event)
                    except Exception as e:
                        logger.error(f"Error parsing Redis message: {e}")
        
        except Exception as e:
            logger.error(f"Redis pub/sub error: {e}")
        finally:
            if self._redis:
                await self._redis.close()
    
    async def _handle_redis_event(self, channel: str, event: dict) -> None:
        """Handle Redis pub/sub event and broadcast to WebSocket clients"""
        
        # Map Redis channels to WebSocket channels
        channel_map = {
            "graph:protocol_update": "protocol:update",
            "graph:risk_alert": "risk:alerts",
            "graph:structure_change": "graph:changes",
        }
        
        ws_channel = channel_map.get(channel, "all")
        
        # Add metadata
        event["timestamp"] = event.get("timestamp", asyncio.get_event_loop().time())
        event["source"] = "graph"
        
        # Broadcast to subscribed connections
        await self.broadcast(event, ws_channel)


# Global manager instance
graph_ws_manager = GraphWebSocketManager()


@router.websocket("/ws/graph")
async def graph_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
):
    """
    WebSocket endpoint for real-time graph updates.
    
    Usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/graph?token=YOUR_TOKEN');
    
    ws.onopen = () => {
        // Subscribe to protocol updates
        ws.send(JSON.stringify({
            action: 'subscribe',
            channel: 'protocol:aave-id'
        }));
        
        // Subscribe to risk alerts
        ws.send(JSON.stringify({
            action: 'subscribe',
            channel: 'risk:alerts'
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Update:', data);
    };
    ```
    
    Message Types:
    - protocol:update - Protocol data changed
    - risk:alert - New risk detected
    - graph:change - Graph structure changed
    - subscribed - Subscription confirmed
    - error - Error message
    """
    
    # TODO: Validate token and get user_id
    user_id = "user-from-token"
    
    await graph_ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            action = data.get("action")
            channel = data.get("channel")
            
            if action == "subscribe" and channel:
                await graph_ws_manager.subscribe(websocket, channel)
            
            elif action == "unsubscribe" and channel:
                await graph_ws_manager.unsubscribe(websocket, channel)
            
            elif action == "ping":
                await graph_ws_manager.send_personal_message(
                    {"type": "pong"},
                    websocket,
                )
            
            else:
                await graph_ws_manager.send_personal_message(
                    {"type": "error", "message": "Unknown action"},
                    websocket,
                )
    
    except WebSocketDisconnect:
        graph_ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        graph_ws_manager.disconnect(websocket)


# Helper function to publish events (call from background tasks)
async def publish_graph_event(channel: str, event: dict) -> None:
    """
    Publish graph event to Redis pub/sub.
    
    Args:
        channel: Channel name (e.g., 'graph:protocol_update')
        event: Event data
    
    Example:
        await publish_graph_event('graph:protocol_update', {
            'protocol_id': 'aave-id',
            'protocol_name': 'Aave',
            'field': 'tvl',
            'old_value': 5000000000,
            'new_value': 5500000000,
        })
    """
    try:
        redis_url = "redis://localhost:6379/0"  # TODO: Get from config
        redis = await aioredis.from_url(redis_url)
        
        await redis.publish(channel, json.dumps(event))
        await redis.close()
        
        logger.debug(f"Published event to {channel}")
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
