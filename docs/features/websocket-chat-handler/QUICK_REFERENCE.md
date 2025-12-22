# WebSocket Chat Handler Quick Reference

## Endpoint

```
ws://localhost:8000/api/v1/ws/chat/{conversation_id}?token={jwt_token}
```

## Message Types Quick Reference

### Client → Server

```javascript
// Send message
{
  "type": "message",
  "content": "Your message here",
  "conversation_id": "uuid-optional"
}

// Ping (heartbeat)
{
  "type": "ping"
}
```

### Server → Client

```javascript
// Stream token
{
  "type": "stream",
  "content": "token",
  "message_id": "uuid",
  "timestamp": "2025-12-16T05:00:00Z"
}

// Typing indicator
{
  "type": "typing",
  "action": "started|stopped",
  "agent_name": "AI Assistant",
  "timestamp": "2025-12-16T05:00:00Z"
}

// Voting update
{
  "type": "voting_update",
  "total_agents": 3,
  "votes_received": 2,
  "vote_summary": {"Option A": 2, "Option B": 1},
  "leading_option": "Option A",
  "timestamp": "2025-12-16T05:00:00Z"
}

// Debate phase
{
  "type": "debate_phase",
  "phase": "initial_analysis|voting|debate|consensus|final_response",
  "description": "Human-readable description",
  "participating_agents": ["Agent1", "Agent2"],
  "round_number": 1,
  "timestamp": "2025-12-16T05:00:00Z"
}

// Message complete
{
  "type": "message_complete",
  "message_id": "uuid",
  "content": "Full message content",
  "metadata": {
    "agent": "analyst",
    "confidence": 0.95
  },
  "timestamp": "2025-12-16T05:00:00Z"
}

// Progress update
{
  "type": "progress",
  "status": "thinking|tool_call|processing",
  "message": "Human-readable message",
  "tool": "tool_name",
  "data": {},
  "timestamp": "2025-12-16T05:00:00Z"
}

// Error
{
  "type": "error",
  "error": "Error message",
  "code": "CHAT_001",
  "details": {},
  "timestamp": "2025-12-16T05:00:00Z"
}

// Pong (heartbeat response)
{
  "type": "pong",
  "timestamp": "2025-12-16T05:00:00Z"
}

// System message
{
  "type": "system",
  "message": "System message",
  "data": {},
  "timestamp": "2025-12-16T05:00:00Z"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `CHAT_001` | Conversation not found |
| `CHAT_002` | Access denied |
| `CHAT_003` | Conversation closed |
| `CHAT_004` | Empty message |
| `CHAT_005` | Message too long |
| `CHAT_006` | Agent unavailable |
| `CHAT_007` | Rate limit exceeded |
| `CHAT_008` | Agent error |
| `CHAT_009` | Invalid agent type |
| `voting_failed` | Multi-agent voting failed |
| `debate_timeout` | Debate timeout |
| `no_consensus` | No consensus reached |
| `agent_timeout` | Agent timeout |

## WebSocket Close Codes

| Code | Reason |
|------|--------|
| 1008 | Policy Violation (auth failure) |
| 1000 | Normal Closure |
| 1001 | Going Away |
| 1011 | Internal Error |

## JavaScript Client Example

```javascript
// Connect
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/ws/chat/${conversationId}?token=${token}`
);

// Handle messages
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg.type, msg);
};

// Send message
ws.send(JSON.stringify({
  type: 'message',
  content: 'Hello!'
}));

// Heartbeat
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

## Python Client Example

```python
import asyncio
import json
from websockets import connect

async def chat():
    uri = f"ws://localhost:8000/api/v1/ws/chat/{conversation_id}?token={token}"

    async with connect(uri) as ws:
        # Receive welcome
        msg = await ws.recv()
        print(json.loads(msg))

        # Send message
        await ws.send(json.dumps({
            'type': 'message',
            'content': 'Hello!'
        }))

        # Receive responses
        async for msg in ws:
            data = json.loads(msg)
            print(data['type'], data)

asyncio.run(chat())
```

## Testing with wscat

```bash
# Install
npm install -g wscat

# Connect
wscat -c "ws://localhost:8000/api/v1/ws/chat/UUID?token=JWT"

# Send
> {"type": "message", "content": "test"}
> {"type": "ping"}
```

## Files

```
src/app/presentation/http/websocket/
├── chat_handler.py       # Main endpoint
├── schemas.py            # Message schemas
├── auth_helper.py        # Authentication
├── error_handler.py      # Error handling
├── connection_manager.py # Connection tracking
└── README.md             # Full documentation
```

## Key Dependencies

```python
# Dishka injection
identity_provider: FromDishka[IdentityProvider]
user_gateway: FromDishka[UserCommandGateway]
session_store: FromDishka[SessionStore]
orchestration_service: FromDishka[AgentOrchestrationService]
```

## Common Patterns

### Send typed message to client

```python
from app.presentation.http.websocket.schemas import StreamTokenMessage

msg = StreamTokenMessage(
    content="token",
    message_id=message_id,
)
await websocket.send_json(msg.model_dump(mode="json"))
```

### Handle domain exception

```python
from app.domain.exceptions.chat import MessageEmptyError
from app.presentation.http.websocket.error_handler import send_error_message

try:
    # ... processing
    raise MessageEmptyError()
except MessageEmptyError as e:
    await send_error_message(websocket, e)
```

### Authenticate connection

```python
from app.presentation.http.websocket.auth_helper import WebSocketAuthHelper

auth_helper = WebSocketAuthHelper(identity_provider, user_gateway)
user = await auth_helper.authenticate_websocket(websocket, token)

if not user:
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return
```

## Typical Message Flow

```
1. Connect → System message (welcome)
2. Client sends message
3. Server: Typing started
4. Server: Progress (thinking)
5. Server: Debate phase (initial_analysis)
6. Server: Debate phase (voting)
7. Server: Voting update (1/3)
8. Server: Voting update (2/3)
9. Server: Voting update (3/3)
10. Server: Debate phase (consensus)
11. Server: Debate phase (final_response)
12. Server: Stream tokens (multiple)
13. Server: Message complete
14. Server: Typing stopped
```

## Environment Variables

```bash
# JWT configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# WebSocket configuration
WS_MAX_CONNECTIONS_PER_USER=5
WS_CONNECTION_TIMEOUT=300
WS_PING_INTERVAL=30
WS_MAX_MESSAGE_SIZE=10000
WS_RATE_LIMIT_PER_MINUTE=60
```

## Health Check

```bash
# Check WebSocket health
curl http://localhost:8000/health/websocket

# Response
{
  "status": "healthy",
  "websocket": {
    "active_connections": 5,
    "active_users": 3,
    "total_connections": 100,
    "total_messages_sent": 1500
  }
}
```

## Useful Commands

```bash
# Run server
make start

# Format code
make code.format

# Lint code
make code.lint

# Run tests
make code.test
```

## Documentation Links

- Full Documentation: `src/app/presentation/http/websocket/README.md`
- Implementation Summary: `docs/features/websocket-chat-handler/IMPLEMENTATION_SUMMARY.md`
- Integration Guide: `docs/features/websocket-chat-handler/INTEGRATION_GUIDE.md`
- Domain Exceptions: `src/app/domain/exceptions/chat.py`
