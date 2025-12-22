# WebSocket Chat Handler Integration Guide

This guide explains how to integrate the new WebSocket chat handler into the FastAPI application.

## Step 1: Update Root Router

Add the WebSocket chat handler to your main router.

**File:** `src/app/presentation/http/controllers/root_router.py`

```python
from fastapi import APIRouter
from app.presentation.http.websocket import chat_handler_router

# Create main router
router = APIRouter()

# Include WebSocket chat handler
router.include_router(
    chat_handler_router,
    prefix="/api/v1",
    tags=["WebSocket Chat"],
)

# ... other routers
```

## Step 2: Configure Dishka Providers

Ensure the required dependencies are registered with Dishka.

**File:** `src/app/setup/ioc/providers.py` (or similar)

```python
from dishka import Provider, Scope, provide
from app.application.chat.services.agent_orchestration_service import (
    AgentOrchestrationService,
)
from app.application.common.ports.identity_provider import IdentityProvider
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.domain.ports.session_store import SessionStore
from app.infrastructure.adapters.session_store_sqla import SqlaSessionStore

class WebSocketProvider(Provider):
    """Provider for WebSocket dependencies."""

    scope = Scope.REQUEST

    # Session store (if not already provided)
    session_store = provide(
        source=SqlaSessionStore,
        provides=SessionStore,
    )

    # Agent orchestration service (if not already provided)
    orchestration_service = provide(
        source=AgentOrchestrationService,
        provides=AgentOrchestrationService,
    )

    # IdentityProvider and UserCommandGateway should already be provided
    # in your existing providers
```

Then add to container:

```python
from dishka import make_async_container
from app.setup.ioc.providers import (
    ApplicationProvider,
    InfrastructureProvider,
    WebSocketProvider,  # Add this
)

container = make_async_container(
    ApplicationProvider(),
    InfrastructureProvider(),
    WebSocketProvider(),  # Add this
)
```

## Step 3: Update Application Setup

Integrate Dishka with FastAPI WebSocket support.

**File:** `src/app/presentation/http/app.py` (or main app file)

```python
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

app = FastAPI(title="Anvil AI Backend")

# Setup Dishka integration
setup_dishka(container, app)

# Include routers
from app.presentation.http.controllers.root_router import router
app.include_router(router)
```

## Step 4: Update CORS Configuration (if needed)

Allow WebSocket connections in CORS configuration.

**File:** `src/app/presentation/http/app.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # WebSocket support
    expose_headers=["*"],
)
```

## Step 5: Test the Endpoint

### Using Python Client

```python
import asyncio
import json
from websockets import connect

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/chat/00000000-0000-0000-0000-000000000000"
    params = "?token=YOUR_JWT_TOKEN"

    async with connect(uri + params) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Welcome: {welcome}")

        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "content": "Hello, AI!"
        }))

        # Receive responses
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {data['type']}")

                if data['type'] == 'message_complete':
                    print(f"Complete: {data['content']}")
                    break

            except Exception as e:
                print(f"Error: {e}")
                break

asyncio.run(test_websocket())
```

### Using wscat

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

### Using Browser JavaScript

```javascript
class ChatWebSocket {
    constructor(conversationId, token) {
        this.ws = new WebSocket(
            `ws://localhost:8000/api/v1/ws/chat/${conversationId}?token=${token}`
        );
        this.setupHandlers();
    }

    setupHandlers() {
        this.ws.onopen = () => {
            console.log('Connected');
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = (event) => {
            console.log('Disconnected:', event.code, event.reason);
        };
    }

    handleMessage(message) {
        switch (message.type) {
            case 'system':
                console.log('System:', message.message);
                break;

            case 'stream':
                // Append token to UI
                this.appendToken(message.content);
                break;

            case 'typing':
                // Show/hide typing indicator
                this.updateTypingIndicator(message.action === 'started');
                break;

            case 'voting_update':
                // Update voting progress
                this.updateVotingProgress(
                    message.votes_received,
                    message.total_agents
                );
                break;

            case 'debate_phase':
                // Show debate phase
                this.showDebatePhase(message.phase, message.description);
                break;

            case 'message_complete':
                // Finalize message
                this.finalizeMessage(message.content);
                break;

            case 'error':
                // Show error
                this.showError(message.error, message.code);
                break;

            case 'pong':
                // Heartbeat response
                console.log('Pong received');
                break;
        }
    }

    sendMessage(content) {
        this.ws.send(JSON.stringify({
            type: 'message',
            content: content
        }));
    }

    sendPing() {
        this.ws.send(JSON.stringify({ type: 'ping' }));
    }

    // UI update methods (implement based on your UI framework)
    appendToken(token) { /* ... */ }
    updateTypingIndicator(isTyping) { /* ... */ }
    updateVotingProgress(received, total) { /* ... */ }
    showDebatePhase(phase, description) { /* ... */ }
    finalizeMessage(content) { /* ... */ }
    showError(error, code) { /* ... */ }
}

// Usage
const chat = new ChatWebSocket(conversationId, jwtToken);

// Send message
chat.sendMessage('Hello, AI!');

// Heartbeat
setInterval(() => chat.sendPing(), 30000);
```

## Step 6: Environment Configuration

Add WebSocket-specific configuration if needed.

**File:** `config/local/config.toml`

```toml
[websocket]
# Maximum connections per user
max_connections_per_user = 5

# Connection timeout (seconds)
connection_timeout = 300

# Ping interval (seconds)
ping_interval = 30

# Message size limits
max_message_size = 10000

# Rate limiting
rate_limit_messages_per_minute = 60
```

## Step 7: Add Health Check Endpoint

Add a health check for WebSocket connections.

**File:** `src/app/presentation/http/controllers/general/healthcheck.py`

```python
from fastapi import APIRouter
from app.presentation.http.websocket.connection_manager import connection_manager

router = APIRouter()

@router.get("/health/websocket")
async def websocket_health():
    """Check WebSocket connection health."""
    stats = connection_manager.get_statistics()

    return {
        "status": "healthy",
        "websocket": {
            "active_connections": stats["active_connections"],
            "active_users": stats["active_users"],
            "total_connections": stats["total_connections"],
            "total_messages_sent": stats["total_messages_sent"],
        }
    }
```

## Step 8: Add Monitoring (Optional)

Integrate with telemetry service for monitoring.

**File:** `src/app/presentation/http/websocket/chat_handler.py`

```python
from app.infrastructure.telemetry import telemetry_service

# In chat_websocket_handler function, after authentication:
await telemetry_service.track_event(
    "websocket_connection",
    user_id=str(user.id),
    conversation_id=str(conversation_id),
)

# In _handle_chat_message function, after message received:
await telemetry_service.track_event(
    "websocket_message_received",
    user_id=str(user.id),
    conversation_id=str(conversation_id),
    message_length=len(message_content),
)
```

## Troubleshooting

### Connection Refused

**Problem:** WebSocket connection fails with "Connection refused"

**Solution:**
1. Check if server is running: `curl http://localhost:8000/health`
2. Verify CORS configuration allows WebSocket
3. Check firewall rules

### Authentication Errors

**Problem:** Getting "Authentication failed" errors

**Solution:**
1. Verify JWT token is valid: `jwt.io` or decode manually
2. Check token is passed in query parameter: `?token=YOUR_TOKEN`
3. Verify `IdentityProvider` is properly configured
4. Check token expiration time

### Dependency Injection Errors

**Problem:** Getting "Dependency not found" errors

**Solution:**
1. Verify all dependencies are registered in Dishka providers
2. Check provider scope (REQUEST vs APP vs SESSION)
3. Ensure `setup_dishka(container, app)` is called before including routers
4. Check import paths are correct

### Message Not Being Received

**Problem:** Client sends message but no response

**Solution:**
1. Check server logs for errors
2. Verify message schema matches `ChatMessageRequest`
3. Check `AgentOrchestrationService` is available
4. Verify conversation exists and user has access

### Streaming Not Working

**Problem:** Not receiving streaming tokens

**Solution:**
1. Check `AgentOrchestrationService` returns streaming response
2. Verify WebSocket send is awaited properly
3. Check network for buffering issues
4. Verify client is handling `stream` message type

## Production Deployment Checklist

- [ ] Configure proper CORS origins (not `*`)
- [ ] Set up rate limiting per user
- [ ] Implement proper JWT validation (not placeholder)
- [ ] Integrate authorization service for conversation access
- [ ] Add Redis for multi-server deployment
- [ ] Set up monitoring and alerting
- [ ] Configure graceful shutdown
- [ ] Add connection limits per user
- [ ] Implement message persistence
- [ ] Set up load balancer with WebSocket support
- [ ] Configure SSL/TLS for WSS
- [ ] Add logging and error tracking
- [ ] Implement reconnection logic on client
- [ ] Add session restoration on reconnect

## Next Steps

After integration:

1. **Implement Agent Orchestration Integration**
   - Connect to real agent orchestration service
   - Replace placeholder voting/debate logic
   - Implement actual streaming from agents

2. **Add Message Persistence**
   - Save messages to database via domain commands
   - Implement message history retrieval
   - Add read receipts

3. **Enhance Authentication**
   - Replace JWT validation placeholder
   - Add token refresh logic
   - Implement session management

4. **Add Advanced Features**
   - File upload support
   - Message reactions
   - Presence indicators
   - Voice/video capabilities

## Support

For issues or questions:
- Review implementation files in `src/app/presentation/http/websocket/`
- Check README.md in websocket directory
- Consult IMPLEMENTATION_SUMMARY.md for architecture details
- Review domain exceptions in `src/app/domain/exceptions/chat.py`
