# WebSocket Chat Handler Documentation

This document describes the WebSocket chat handler implementation for real-time chat features with multi-agent orchestration.

## Overview

The WebSocket chat handler provides real-time bidirectional communication between clients and the server, enabling:

- Real-time message streaming (token-by-token)
- Agent typing indicators
- Multi-agent voting progress updates
- Debate phase notifications
- Connection lifecycle management (connect, disconnect, heartbeat)
- Authentication and authorization

## Architecture

The implementation follows **Hexagonal Architecture** principles:

### Layer Separation

```
Presentation (WebSocket Handler)
    ↓
Application (Agent Orchestration Service)
    ↓
Domain (Entities, Value Objects, Ports)
    ↓
Infrastructure (Adapters, Session Store)
```

### Key Components

#### 1. **chat_handler.py** - Main WebSocket Endpoint
- Endpoint: `/ws/chat/{conversation_id}`
- Authentication via JWT token (query parameter)
- Connection lifecycle management
- Message routing and streaming
- Error handling with domain exceptions

#### 2. **schemas.py** - Message Type Definitions
Pydantic schemas for all WebSocket message types:

**Client → Server:**
- `ChatMessageRequest` - User sends message
- `PingMessage` - Heartbeat ping

**Server → Client:**
- `StreamTokenMessage` - Streaming response tokens
- `TypingIndicatorMessage` - Agent typing status
- `VotingUpdateMessage` - Multi-agent vote progress
- `DebatePhaseMessage` - Debate phase transitions
- `MessageCompleteMessage` - Response completion
- `ProgressMessage` - General progress updates
- `ErrorMessage` - Error notifications
- `PongMessage` - Heartbeat response
- `SystemMessage` - System notifications

#### 3. **auth_helper.py** - Authentication
- JWT token validation
- User authentication via `IdentityProvider`
- Conversation access control
- Proper error handling for auth failures

#### 4. **error_handler.py** - Error Management
- Exception to ErrorMessage conversion
- Domain exception mapping to error codes
- Centralized error handling utilities

#### 5. **connection_manager.py** - Connection Tracking
- Active connection registry
- User/session mapping
- Broadcast capabilities
- Connection statistics

## Usage

### Client Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/chat/${conversationId}?token=${jwtToken}`
);

// Handle connection open
ws.onopen = () => {
  console.log('Connected to chat');
};

// Handle incoming messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'stream':
      // Append streaming token to UI
      appendToken(message.content);
      break;

    case 'typing':
      // Show/hide typing indicator
      updateTypingIndicator(message.action);
      break;

    case 'voting_update':
      // Update voting progress UI
      updateVotingProgress(message.votes_received, message.total_agents);
      break;

    case 'debate_phase':
      // Show debate phase transition
      showDebatePhase(message.phase, message.description);
      break;

    case 'message_complete':
      // Finalize message display
      finalizeMessage(message.message_id, message.content);
      break;

    case 'error':
      // Display error to user
      showError(message.error, message.code);
      break;

    case 'system':
      // Handle system message
      console.log('System:', message.message);
      break;
  }
};

// Send message
function sendMessage(content) {
  ws.send(JSON.stringify({
    type: 'message',
    content: content,
    conversation_id: conversationId
  }));
}

// Send heartbeat ping
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000); // Every 30 seconds
```

### Server-Side Handler Flow

```
1. Client connects with JWT token
   ↓
2. Authenticate user via IdentityProvider
   ↓
3. Check conversation access
   ↓
4. Register connection with ConnectionManager
   ↓
5. Send welcome SystemMessage
   ↓
6. Enter message loop:
   - Receive client message
   - Validate message schema
   - Send TypingIndicatorMessage (started)
   - Route to AgentOrchestrationService
   - Stream response with progress updates
   - Send MessageCompleteMessage
   - Send TypingIndicatorMessage (stopped)
   ↓
7. On disconnect: Clean up connection
```

## Message Flow Examples

### 1. Simple Message Exchange

```
Client → Server:
{
  "type": "message",
  "content": "What's the weather like?",
  "conversation_id": "uuid-here"
}

Server → Client (sequence):
1. { "type": "typing", "action": "started", "agent_name": "AI Assistant" }
2. { "type": "progress", "status": "thinking", "message": "Processing..." }
3. { "type": "stream", "content": "The ", "message_id": "uuid" }
4. { "type": "stream", "content": "weather ", "message_id": "uuid" }
5. { "type": "stream", "content": "is...", "message_id": "uuid" }
6. { "type": "message_complete", "message_id": "uuid", "content": "The weather is..." }
7. { "type": "typing", "action": "stopped", "agent_name": "AI Assistant" }
```

### 2. Multi-Agent Voting Flow

```
Server → Client (sequence):
1. { "type": "debate_phase", "phase": "initial_analysis", ... }
2. { "type": "debate_phase", "phase": "voting", ... }
3. { "type": "voting_update", "total_agents": 3, "votes_received": 1, ... }
4. { "type": "voting_update", "total_agents": 3, "votes_received": 2, ... }
5. { "type": "voting_update", "total_agents": 3, "votes_received": 3, ... }
6. { "type": "debate_phase", "phase": "consensus", ... }
7. { "type": "debate_phase", "phase": "final_response", ... }
8. [Stream tokens...]
9. { "type": "message_complete", ... }
```

### 3. Error Handling

```
Client → Server:
{ "type": "message", "content": "" }

Server → Client:
{
  "type": "error",
  "error": "Message content cannot be empty",
  "code": "CHAT_004",
  "details": { "field": "content" },
  "timestamp": "2025-12-16T05:00:00Z"
}
```

## Error Codes

| Code | Description | Exception Type |
|------|-------------|----------------|
| `CHAT_001` | Conversation not found | `ConversationNotFoundError` |
| `CHAT_002` | Access denied | `ConversationAccessDeniedError` |
| `CHAT_003` | Conversation closed | `ConversationClosedError` |
| `CHAT_004` | Empty message | `MessageEmptyError` |
| `CHAT_005` | Message too long | `MessageTooLongError` |
| `CHAT_006` | Agent unavailable | `AgentUnavailableError` |
| `CHAT_007` | Rate limit exceeded | `ChatRateLimitError` |
| `CHAT_008` | Agent error | `AgentProcessingError` |
| `CHAT_009` | Invalid agent type | `InvalidAgentTypeError` |
| `voting_failed` | Voting failed | `VotingFailedError` |
| `debate_timeout` | Debate timeout | `DebateTimeoutError` |
| `no_consensus` | No consensus | `NoConsensusError` |
| `agent_timeout` | Agent timeout | `AgentTimeoutError` |

## Authentication

### JWT Token Validation

The handler uses the hexagonal architecture's `IdentityProvider` pattern:

```python
# Infrastructure Layer
identity_provider: IdentityProvider  # Injected via Dishka

# Presentation Layer
auth_helper = WebSocketAuthHelper(identity_provider, user_gateway)
user = await auth_helper.authenticate_websocket(websocket, token)

if not user:
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return
```

### Authorization

Conversation access is checked before accepting the connection:

```python
has_access = await auth_helper.check_conversation_access(user, conversation_id)
if not has_access:
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return
```

## Dependency Injection

The handler uses **Dishka** for dependency injection (following the project's convention):

```python
@router.websocket("/ws/chat/{conversation_id}")
@inject
async def chat_websocket_handler(
    websocket: WebSocket,
    conversation_id: UUID,
    identity_provider: FromDishka[IdentityProvider] = None,
    user_gateway: FromDishka[UserCommandGateway] = None,
    session_store: FromDishka[SessionStore] = None,
    orchestration_service: FromDishka[AgentOrchestrationService] = None,
):
    ...
```

## Integration with Agent Orchestration

The handler delegates to `AgentOrchestrationService` for:

1. **Agent routing** - Selecting appropriate agent(s)
2. **Multi-agent voting** - Coordinating multiple agents
3. **Debate orchestration** - Managing agent debates
4. **Response generation** - Streaming final responses

```python
await _process_with_orchestration(
    websocket=websocket,
    user=user,
    conversation_id=conversation_id,
    message_content=message_content,
    orchestration_service=orchestration_service,
)
```

## Session Management

### Connection Tracking

```python
# Register connection
await connection_manager.connect(
    websocket,
    user_id=str(user.id),
    session_id=session_id,
    metadata={
        "conversation_id": str(conversation_id),
        "email": user.email,
        "connected_at": datetime.utcnow().isoformat(),
    },
)

# Cleanup on disconnect
await connection_manager.disconnect(websocket, str(user.id), session_id)
```

### Heartbeat/Ping-Pong

Clients should send periodic pings to maintain connection:

```javascript
// Client-side
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

Server responds with pong:

```python
if message_type == WebSocketMessageType.PING:
    await _handle_ping(websocket)  # Sends PongMessage
```

## Testing

### Manual Testing with wscat

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c "ws://localhost:8000/api/v1/ws/chat/00000000-0000-0000-0000-000000000000?token=YOUR_JWT_TOKEN"

# Send message
> {"type": "message", "content": "Hello!"}

# Send ping
> {"type": "ping"}
```

### Integration Testing

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_websocket_authentication():
    with TestClient(app).websocket_connect(
        f"/api/v1/ws/chat/{conversation_id}?token={valid_token}"
    ) as websocket:
        # Should receive welcome message
        data = websocket.receive_json()
        assert data["type"] == "system"
        assert "Connected to conversation" in data["message"]

@pytest.mark.asyncio
async def test_websocket_message_streaming():
    with TestClient(app).websocket_connect(
        f"/api/v1/ws/chat/{conversation_id}?token={valid_token}"
    ) as websocket:
        # Send message
        websocket.send_json({
            "type": "message",
            "content": "Test message"
        })

        # Should receive typing indicator
        data = websocket.receive_json()
        assert data["type"] == "typing"
        assert data["action"] == "started"

        # Should receive stream tokens
        data = websocket.receive_json()
        assert data["type"] == "stream"

        # Should receive message complete
        data = websocket.receive_json()
        assert data["type"] == "message_complete"
```

## Production Considerations

### 1. Scalability

For production deployment with multiple servers:

- Use Redis for shared connection state
- Implement Redis pub/sub for broadcasting
- Consider WebSocket gateway (e.g., Socket.IO with Redis adapter)

### 2. Rate Limiting

Implement rate limiting per user:

```python
from app.domain.exceptions.chat import ChatRateLimitError

# Check rate limit before processing
if await rate_limiter.is_limited(user.id):
    raise ChatRateLimitError(
        retry_after_seconds=60,
        limit=10,
        window_seconds=60,
    )
```

### 3. Monitoring

Add telemetry for:
- Connection count
- Message throughput
- Error rates
- Response latency

```python
from app.infrastructure.telemetry import telemetry_service

await telemetry_service.track_websocket_connection(user.id, conversation_id)
await telemetry_service.track_message_sent(user.id, message_id)
```

### 4. Graceful Shutdown

Handle server shutdown gracefully:

```python
@app.on_event("shutdown")
async def shutdown_websockets():
    # Send system message to all connections
    await connection_manager.broadcast({
        "type": "system",
        "message": "Server is shutting down. Please reconnect in a moment."
    })

    # Close all connections
    # ... cleanup logic
```

## Files Structure

```
src/app/presentation/http/websocket/
├── __init__.py                  # Exports
├── README.md                    # This file
├── chat_handler.py              # Main WebSocket endpoint
├── schemas.py                   # Message type schemas
├── auth_helper.py               # Authentication utilities
├── error_handler.py             # Error handling utilities
├── connection_manager.py        # Connection tracking
├── chat_websocket.py            # Legacy handler (deprecated)
└── graph_websocket.py           # Graph-specific WebSocket
```

## Migration from Legacy Handler

The new `chat_handler.py` replaces `chat_websocket.py` with:

- ✅ Structured message schemas (Pydantic)
- ✅ Proper authentication via IdentityProvider
- ✅ Domain exception handling
- ✅ Multi-agent orchestration support
- ✅ Comprehensive error handling
- ✅ Better separation of concerns

To migrate:

1. Update router imports to use `chat_handler_router`
2. Update client code to use new message schemas
3. Test authentication flow
4. Verify error handling

## Future Enhancements

1. **Redis Integration** - For multi-server deployment
2. **Message Persistence** - Store messages in database via domain commands
3. **Reconnection Logic** - Client-side reconnection with session restoration
4. **File Upload Support** - Binary message handling for attachments
5. **Read Receipts** - Track message read status
6. **Presence Indicators** - Show online/offline status
7. **Typing Indicators Optimization** - Debounce typing events
8. **Message Reactions** - Real-time reaction updates

## Support

For questions or issues:
- Check domain exceptions in `src/app/domain/exceptions/chat.py`
- Review agent orchestration service documentation
- Consult hexagonal architecture guidelines in `/CLAUDE.md`
