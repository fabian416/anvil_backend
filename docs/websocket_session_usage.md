# WebSocket Session Management

This document provides usage examples for the Redis-based WebSocket session management system.

## Architecture Overview

The WebSocket session management system follows hexagonal architecture principles:

- **Domain Layer**: `WebSocketSession` entity and `SessionStore` port
- **Infrastructure Layer**: `RedisSessionStoreAdapter` implementation
- **Dependency Injection**: `WebSocketSessionProvider` for IOC

## Components

### 1. Domain Entity: WebSocketSession

```python
from app.domain.entities.chat.websocket_session import WebSocketSession
from uuid import UUID, uuid4

# Create a new session
session = WebSocketSession.create(
    session_id="ws_abc123",
    user_id=UUID("12345678-1234-5678-1234-567812345678"),
    conversation_id=UUID("87654321-4321-8765-4321-876543218765"),
    metadata={
        "client_info": {
            "user_agent": "Mozilla/5.0...",
            "ip_address": "192.168.1.1",
            "platform": "web"
        },
        "permissions": {
            "can_send_messages": True,
            "can_receive_notifications": True
        }
    }
)

# Update activity
session.update_activity()

# Check if session is idle
if session.is_idle():
    session.mark_idle()

# Disconnect session
session.disconnect()

# Check if expired
if session.is_expired():
    # Session should be cleaned up
    pass
```

### 2. Connection States

```python
from app.domain.enums.connection_state import ConnectionState

# Available states:
# - CONNECTED: Active connection established
# - DISCONNECTED: Connection closed or terminated
# - IDLE: Connection active but no recent activity (>5 minutes)
# - RECONNECTING: Attempting to restore connection
```

### 3. Session Store Port

```python
from app.domain.ports.session_store import SessionStore
from dishka import FromDishka

# In your interactor or handler
class WebSocketMessageHandler:
    def __init__(self, session_store: FromDishka[SessionStore]):
        self._session_store = session_store

    async def handle_connection(self, session_id: str, user_id: UUID):
        # Create new session
        session = WebSocketSession.create(
            session_id=session_id,
            user_id=user_id
        )

        await self._session_store.create_session(session)

    async def handle_message(self, session_id: str):
        # Update activity on message
        await self._session_store.update_activity(session_id)

    async def handle_disconnect(self, session_id: str):
        # Mark session as disconnected
        await self._session_store.disconnect_session(session_id)
```

### 4. Redis Implementation

The `RedisSessionStoreAdapter` provides:

- **Connection pooling** with 20 connections for optimal performance
- **Atomic operations** using Redis pipelines for consistency
- **Efficient indexing** using Redis Sets and Sorted Sets
- **Automatic TTL management** (7-day retention)
- **Multi-device support** (users can have multiple concurrent sessions)

Redis data structure:
```
ws:session:{session_id}              - Hash: Session data
ws:user:{user_id}:sessions           - Set: User's session IDs
ws:conversation:{conv_id}:sessions   - Set: Conversation session IDs
ws:state:{state}:sessions            - Set: Sessions by state
ws:activity                          - ZSet: Sessions by last activity
ws:disconnected                      - ZSet: Disconnected sessions by time
```

## Common Operations

### Creating a Session

```python
from app.domain.entities.chat.websocket_session import WebSocketSession
from app.domain.ports.session_store import SessionStore
from dishka import FromDishka

async def create_session(
    session_store: FromDishka[SessionStore],
    session_id: str,
    user_id: UUID,
    conversation_id: UUID | None = None
) -> bool:
    session = WebSocketSession.create(
        session_id=session_id,
        user_id=user_id,
        conversation_id=conversation_id,
        metadata={
            "client_info": {
                "platform": "web"
            }
        }
    )

    return await session_store.create_session(session)
```

### Getting User Sessions

```python
from app.domain.enums.connection_state import ConnectionState

async def get_active_sessions(
    session_store: FromDishka[SessionStore],
    user_id: UUID
):
    # Get all active sessions
    sessions = await session_store.get_user_sessions(
        user_id=user_id,
        state_filter=ConnectionState.CONNECTED
    )

    return sessions
```

### Broadcasting to Conversation

```python
async def broadcast_to_conversation(
    session_store: FromDishka[SessionStore],
    conversation_id: UUID,
    message: str
):
    # Get all active sessions in conversation
    sessions = await session_store.get_conversation_sessions(conversation_id)

    # Broadcast to each session
    for session in sessions:
        # Send message to WebSocket connection
        # (Implementation depends on your WebSocket manager)
        await send_to_websocket(session.session_id, message)
```

### Session Cleanup

```python
async def cleanup_sessions(session_store: FromDishka[SessionStore]):
    # Mark idle sessions
    idle_count = await session_store.mark_idle_sessions()
    print(f"Marked {idle_count} sessions as idle")

    # Cleanup expired sessions
    cleanup_count = await session_store.cleanup_expired_sessions()
    print(f"Cleaned up {cleanup_count} expired sessions")
```

### User Logout

```python
async def logout_user(
    session_store: FromDishka[SessionStore],
    user_id: UUID
):
    # Disconnect all user sessions
    count = await session_store.disconnect_user_sessions(user_id)
    print(f"Disconnected {count} sessions")
```

## Background Task Example

You can create a Celery task for periodic cleanup:

```python
from celery import shared_task
from dishka import make_async_container
from app.setup.ioc.provider_registry import get_providers
from app.domain.ports.session_store import SessionStore

@shared_task
async def cleanup_websocket_sessions():
    """Periodic task to cleanup idle and expired WebSocket sessions."""
    container = make_async_container(*get_providers())

    async with container() as request_container:
        session_store = await request_container.get(SessionStore)

        # Mark idle sessions
        idle_count = await session_store.mark_idle_sessions()

        # Cleanup expired sessions
        cleanup_count = await session_store.cleanup_expired_sessions()

        return {
            "idle_marked": idle_count,
            "expired_cleaned": cleanup_count
        }
```

## Configuration

### Environment Variables

```bash
# Redis URL for WebSocket sessions (uses database 1 by default)
REDIS_URL=redis://localhost:6379/1
```

### Business Rules

- **Idle Threshold**: 5 minutes of inactivity (300 seconds)
- **Expiration**: 24 hours after disconnection
- **TTL**: 7 days for all session data
- **Connection Pool**: 20 connections for session operations

## Performance Considerations

1. **Connection Pooling**: The adapter uses a dedicated connection pool with 20 connections
2. **Atomic Operations**: All state changes use Redis pipelines for atomicity
3. **Efficient Queries**: Uses Redis Sets and Sorted Sets for O(1) lookups
4. **Separate Database**: Uses Redis database 1 to avoid contention with other data
5. **Batch Processing**: Cleanup operations process sessions in batches

## Testing

Example test:

```python
import pytest
from app.domain.entities.chat.websocket_session import WebSocketSession
from app.infrastructure.adapters.chat.redis_session_store_adapter import (
    RedisSessionStoreAdapter
)

@pytest.mark.asyncio
async def test_session_lifecycle(redis_client):
    adapter = RedisSessionStoreAdapter(redis_client)

    # Create session
    session = WebSocketSession.create(
        session_id="test_123",
        user_id=uuid4()
    )

    assert await adapter.create_session(session)

    # Retrieve session
    retrieved = await adapter.get_session("test_123")
    assert retrieved is not None
    assert retrieved.session_id == "test_123"

    # Update activity
    assert await adapter.update_activity("test_123")

    # Disconnect
    assert await adapter.disconnect_session("test_123")

    # Cleanup
    assert await adapter.delete_session("test_123")
```

## Integration with WebSocket Server

```python
from fastapi import WebSocket
from app.domain.ports.session_store import SessionStore

class WebSocketManager:
    def __init__(self, session_store: SessionStore):
        self._session_store = session_store
        self._active_connections: dict[str, WebSocket] = {}

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: UUID,
        conversation_id: UUID | None = None
    ):
        await websocket.accept()

        # Store WebSocket connection
        self._active_connections[session_id] = websocket

        # Create session in store
        session = WebSocketSession.create(
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id
        )
        await self._session_store.create_session(session)

    async def disconnect(self, session_id: str):
        # Remove from active connections
        self._active_connections.pop(session_id, None)

        # Mark as disconnected in store
        await self._session_store.disconnect_session(session_id)

    async def send_message(self, session_id: str, message: str):
        # Update activity
        await self._session_store.update_activity(session_id)

        # Send message
        websocket = self._active_connections.get(session_id)
        if websocket:
            await websocket.send_text(message)
```

## Monitoring and Statistics

```python
async def get_session_stats(session_store: FromDishka[SessionStore]):
    total = await session_store.get_session_count()
    connected = await session_store.get_session_count(
        state=ConnectionState.CONNECTED
    )
    idle = await session_store.get_session_count(
        state=ConnectionState.IDLE
    )
    active_users = await session_store.get_active_user_count()

    return {
        "total_sessions": total,
        "connected_sessions": connected,
        "idle_sessions": idle,
        "active_users": active_users
    }
```
