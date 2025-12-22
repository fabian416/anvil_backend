# WebSocket Session Management Implementation

## Overview

This document describes the Redis-based WebSocket session management system implemented following hexagonal architecture patterns.

## Implementation Summary

### Components Created

1. **Domain Layer**
   - `src/app/domain/enums/connection_state.py` - Connection state enumeration
   - `src/app/domain/entities/chat/websocket_session.py` - WebSocket session entity
   - `src/app/domain/ports/session_store.py` - Session store port interface

2. **Infrastructure Layer**
   - `src/app/infrastructure/adapters/chat/redis_session_store_adapter.py` - Redis adapter implementation

3. **Dependency Injection**
   - `src/app/setup/ioc/websocket_session.py` - IOC provider
   - Updated `src/app/setup/ioc/provider_registry.py` - Registered provider

4. **Documentation**
   - `docs/websocket_session_usage.md` - Usage examples and patterns

## Architecture

### Hexagonal Architecture Compliance

```
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  ┌─────────────────┐      ┌─────────────────┐              │
│  │ WebSocketSession│      │  SessionStore   │              │
│  │    (Entity)     │      │     (Port)      │              │
│  └─────────────────┘      └─────────────────┘              │
│           ▲                        ▲                         │
└───────────┼────────────────────────┼─────────────────────────┘
            │                        │
┌───────────┼────────────────────────┼─────────────────────────┐
│           │   Infrastructure Layer │                         │
│  ┌────────┴────────────────────────┴────────┐               │
│  │   RedisSessionStoreAdapter              │               │
│  │   (Implements SessionStore)             │               │
│  │                                          │               │
│  │  - Connection pooling (20 connections)  │               │
│  │  - Atomic operations via pipelines      │               │
│  │  - Efficient indexing with Sets/ZSets   │               │
│  │  - Automatic TTL management             │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Redis Data Architecture

```
Key Structure:
┌────────────────────────────────────────────────────────┐
│ ws:session:{session_id}                 (Hash)        │
│   - id, session_id, user_id, conversation_id          │
│   - connection_state, connected_at, last_activity     │
│   - disconnected_at, metadata                         │
│   TTL: 7 days                                          │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ ws:user:{user_id}:sessions             (Set)          │
│   - Set of session_ids for user                       │
│   - Enables multi-device support                      │
│   TTL: 7 days                                          │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ ws:conversation:{conv_id}:sessions     (Set)          │
│   - Set of session_ids in conversation                │
│   - For broadcasting to conversation participants      │
│   TTL: 7 days                                          │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ ws:state:{state}:sessions              (Set)          │
│   - Sessions grouped by ConnectionState                │
│   - States: connected, disconnected, idle, reconnecting│
│   - Enables efficient state-based queries              │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ ws:activity                            (Sorted Set)   │
│   - Sessions ordered by last_activity timestamp        │
│   - Score: timestamp of last activity                  │
│   - Used for idle detection                            │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ ws:disconnected                        (Sorted Set)   │
│   - Disconnected sessions by disconnect time           │
│   - Score: disconnection timestamp                     │
│   - Used for cleanup of expired sessions               │
└────────────────────────────────────────────────────────┘
```

## Business Rules

### Session Lifecycle

1. **CONNECTED**: Active WebSocket connection
   - Initial state when session is created
   - Updated on every message/activity

2. **IDLE**: No activity for 5 minutes
   - Automatically marked by `mark_idle_sessions()`
   - Transitions back to CONNECTED on activity

3. **DISCONNECTED**: Connection closed
   - Manual disconnect or connection loss
   - Starts expiration timer

4. **RECONNECTING**: Attempting to reconnect
   - Optional state for reconnection logic

### Expiration Rules

- **Idle Threshold**: 5 minutes (300 seconds)
- **Expiration**: 24 hours after disconnection
- **TTL**: 7 days for all Redis keys
- **Cleanup**: Periodic background task recommended

## Key Features

### 1. Connection Pooling

```python
# Dedicated connection pool with 20 connections
pool = ConnectionPool.from_url(
    redis_url,
    max_connections=20,
    decode_responses=False
)
```

### 2. Atomic Operations

All state changes use Redis pipelines for atomicity:

```python
async with self._redis.pipeline(transaction=True) as pipe:
    pipe.hset(session_key, "connection_state", state.value)
    pipe.srem(old_state_key, session_id)
    pipe.sadd(new_state_key, session_id)
    await pipe.execute()
```

### 3. Multi-Device Support

Users can have multiple concurrent sessions:

```python
# Each device creates its own session
sessions = await session_store.get_user_sessions(user_id)
# Returns all active sessions for the user
```

### 4. Efficient Querying

- **By User**: O(1) lookup via user session set
- **By State**: O(1) lookup via state index
- **By Activity**: O(log N) range query via sorted set
- **By Conversation**: O(1) lookup via conversation set

## Usage Patterns

### Basic Session Management

```python
from app.domain.entities.chat.websocket_session import WebSocketSession
from app.domain.ports.session_store import SessionStore
from dishka import FromDishka

class WebSocketHandler:
    def __init__(self, session_store: FromDishka[SessionStore]):
        self._session_store = session_store

    async def on_connect(self, session_id: str, user_id: UUID):
        session = WebSocketSession.create(
            session_id=session_id,
            user_id=user_id
        )
        await self._session_store.create_session(session)

    async def on_message(self, session_id: str):
        await self._session_store.update_activity(session_id)

    async def on_disconnect(self, session_id: str):
        await self._session_store.disconnect_session(session_id)
```

### Broadcasting

```python
async def broadcast_to_conversation(
    session_store: SessionStore,
    conversation_id: UUID,
    message: dict
):
    sessions = await session_store.get_conversation_sessions(conversation_id)

    for session in sessions:
        # Send to WebSocket connection
        await websocket_manager.send(session.session_id, message)
```

### Cleanup Task

```python
from celery import shared_task

@shared_task
async def cleanup_websocket_sessions():
    # Mark idle sessions (CONNECTED -> IDLE)
    idle_count = await session_store.mark_idle_sessions()

    # Remove expired sessions (DISCONNECTED > 24h)
    cleanup_count = await session_store.cleanup_expired_sessions()

    return {"idle": idle_count, "cleaned": cleanup_count}
```

### User Logout

```python
async def logout_user(user_id: UUID):
    # Disconnect all user sessions across all devices
    count = await session_store.disconnect_user_sessions(user_id)
    return f"Disconnected {count} sessions"
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| create_session | O(1) | Single hash + set operations |
| get_session | O(1) | Hash lookup |
| get_user_sessions | O(N) | N = user's session count |
| update_activity | O(1) | Hash update + sorted set update |
| disconnect_session | O(1) | Atomic pipeline operation |
| mark_idle_sessions | O(M log M) | M = sessions to check |
| cleanup_expired_sessions | O(K) | K = expired sessions |

### Space Complexity

Per session storage:
- Session hash: ~500-1000 bytes
- Index entries: ~100 bytes
- Total per session: ~1KB

For 10,000 concurrent sessions: ~10MB

## Configuration

### Environment Variables

```bash
# Redis URL (database 1 by default to avoid contention)
REDIS_URL=redis://localhost:6379/1

# Or with authentication
REDIS_URL=redis://:password@redis-host:6379/1
```

### Dependency Injection

The provider is automatically registered in `provider_registry.py`:

```python
WebSocketSessionProvider(),  # WebSocket session management with Redis
```

### Connection Pool Settings

Configured in `websocket_session.py`:

```python
max_connections=20  # Adjust based on expected concurrent WebSocket connections
```

## Testing Recommendations

### Unit Tests

Test the domain entity:

```python
def test_session_is_idle():
    session = WebSocketSession.create(...)
    # Manipulate last_activity
    assert session.is_idle() == True

def test_session_expiration():
    session = WebSocketSession.create(...)
    session.disconnect()
    # Manipulate disconnected_at
    assert session.is_expired() == True
```

### Integration Tests

Test the Redis adapter:

```python
@pytest.mark.asyncio
async def test_session_lifecycle(redis_client):
    adapter = RedisSessionStoreAdapter(redis_client)

    # Create
    session = WebSocketSession.create(...)
    assert await adapter.create_session(session)

    # Read
    retrieved = await adapter.get_session(session.session_id)
    assert retrieved is not None

    # Update
    assert await adapter.update_activity(session.session_id)

    # Delete
    assert await adapter.delete_session(session.session_id)
```

### Load Tests

Test performance under load:

```python
async def test_concurrent_sessions():
    # Create 1000 concurrent sessions
    tasks = [
        adapter.create_session(WebSocketSession.create(...))
        for _ in range(1000)
    ]
    results = await asyncio.gather(*tasks)
    assert all(results)
```

## Monitoring

### Metrics to Track

```python
async def get_metrics(session_store: SessionStore):
    return {
        "total_sessions": await session_store.get_session_count(),
        "connected": await session_store.get_session_count(
            state=ConnectionState.CONNECTED
        ),
        "idle": await session_store.get_session_count(
            state=ConnectionState.IDLE
        ),
        "disconnected": await session_store.get_session_count(
            state=ConnectionState.DISCONNECTED
        ),
        "active_users": await session_store.get_active_user_count()
    }
```

### Recommended Dashboards

1. **Session Count Over Time**
   - Track concurrent connections
   - Identify peak usage times

2. **State Distribution**
   - CONNECTED vs IDLE vs DISCONNECTED
   - Monitor idle rate

3. **Cleanup Metrics**
   - Sessions marked idle per run
   - Expired sessions cleaned per run

4. **User Activity**
   - Active users count
   - Average sessions per user

## Production Considerations

### 1. Redis High Availability

Use Redis Sentinel or Cluster for production:

```bash
REDIS_URL=redis://sentinel-host:26379/1?sentinel=mymaster
```

### 2. Cleanup Scheduling

Run cleanup task every 5-10 minutes:

```python
# Celery beat schedule
schedule = {
    'cleanup-websocket-sessions': {
        'task': 'cleanup_websocket_sessions',
        'schedule': timedelta(minutes=5),
    }
}
```

### 3. Connection Pool Tuning

Adjust pool size based on load:
- Start with 20 connections
- Monitor Redis connection usage
- Increase if needed (max ~100)

### 4. Monitoring Alerts

Set up alerts for:
- High disconnected session count (> 1000)
- Low cleanup success rate
- Redis connection pool exhaustion
- High idle session percentage (> 50%)

## Migration Guide

### From In-Memory Storage

If migrating from in-memory WebSocket storage:

1. Deploy Redis adapter alongside existing system
2. Write to both stores temporarily
3. Verify data consistency
4. Switch reads to Redis
5. Remove old in-memory store

### Database Schema

No database schema changes required - this is a pure Redis implementation.

## Security Considerations

1. **Session Hijacking**: Store session metadata with client fingerprinting
2. **Rate Limiting**: Track message counts in session metadata
3. **Authorization**: Store permissions in session metadata
4. **Audit Trail**: Log all state transitions

## Future Enhancements

Potential improvements:

1. **Compression**: Compress large metadata using gzip
2. **Sharding**: Distribute sessions across Redis instances
3. **Analytics**: Track session duration statistics
4. **Reconnection Logic**: Auto-recovery for disconnected sessions
5. **Message Queuing**: Integrate with offline queue for disconnected users

## Summary

The WebSocket session management system provides:

- Scalable Redis-based storage with connection pooling
- Clean hexagonal architecture following project conventions
- Multi-device support with efficient querying
- Automatic cleanup of idle and expired sessions
- Production-ready with monitoring and testing support

All files follow the established patterns from `RedisOfflineQueueAdapter` and integrate seamlessly with the existing IOC infrastructure.
