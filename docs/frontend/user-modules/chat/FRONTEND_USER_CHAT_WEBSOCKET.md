# FRONTEND_USER_CHAT_WEBSOCKET

> **Enterprise Real-Time Protocol**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/websocket/chat_websocket.py`

## 1. Connection Details

| Attribute | Value |
| :--- | :--- |
| **URL (Dev)** | `ws://localhost:8000/api/v1/ws/chat` |
| **URL (Prod)** | `wss://api.anvil.com/api/v1/ws/chat` |
| **Auth** | Query Parameter: `?token=<jwt_access_token>` |
| **Optional** | Query Parameter: `?session_id=<uuid>` (for resuming sessions) |

### 1.1 Connection Lifecycle
1.  **Connect**: Client initiates WS connection with JWT.
2.  **Validate**: Server validates token (Close Code 1008 if invalid).
3.  **Welcome**: Server sends `type: system` welcome message.
4.  **Loop**: Bidirectional message flow.
5.  **Heartbeat**: Client sends `ping`, Server responds `pong`.

---

## 2. Client-to-Server Messages

### 2.1 Send Chat Message
Send a user message to be processed by the Agent Squad.

```json
{
  "type": "message",
  "content": "Find me the best stablecoin yields on Arbitrum",
  "conversation_id": "uuid"  // Optional: New conversation created if omitted
}
```

### 2.2 Heartbeat (Ping)
Keep connection alive (send every 30s).

```json
{
  "type": "ping"
}
```

---

## 3. Server-to-Client Messages

The server streams responses in a specific sequence of events.

### 3.1 System/Welcome
Sent immediately upon successful connection.

```json
{
  "type": "system",
  "message": "Connected to Anvil AI Chat",
  "user_id": "user_123",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3.2 Progress Updates (The "Thinking" State)
Sent before and during agent execution to show UI feedback.

**Status Types**:
*   `thinking`: Initial processing.
*   `routing`: Agent Squad is routing the request.
*   `tool_call`: Agent is using an external tool (e.g., Price API).
*   `tool_completed`: Tool execution finished.

```json
{
  "type": "progress",
  "status": "routing",
  "message": "Routing to hunter_ai agent (confidence: 98%)",
  "agent": "hunter_ai"
}
```

### 3.3 Streaming Content (Token-by-Token)
The core response text, streamed in small chunks.

```json
{
  "type": "stream",
  "content": "The ",
  "message_id": "msg_123"
}
```

### 3.4 Message Complete
Sent when the agent has finished generation.

```json
{
  "type": "message_complete",
  "message_id": "msg_123",
  "content": "The best stablecoin yield is Aave V3...", // Full aggregated content
  "metadata": {
    "agent": "hunter_ai",
    "confidence": 0.98,
    "latency_ms": 1200
  }
}
```

### 3.5 Error
Sent if processing fails.

```json
{
  "type": "error",
  "error": "Message content is required",
  "code": "empty_message"
}
```

### 3.6 Heartbeat Response (Pong)

```json
{
  "type": "pong"
}
```

---

## 4. Example Event Sequence (Happy Path)

1.  **Client**: Sends `type: message` ("Check ETH price").
2.  **Server**: Sends `type: progress` (status: `thinking`).
3.  **Server**: Sends `type: progress` (status: `routing`, agent: `hunter_ai`).
4.  **Server**: Sends `type: progress` (status: `tool_call`, tool: `get_price`).
5.  **Server**: Sends `type: progress` (status: `tool_completed`).
6.  **Server**: Sends `type: stream` ("ETH").
7.  **Server**: Sends `type: stream` (" is").
8.  **Server**: Sends `type: stream` (" $2500").
9.  **Server**: Sends `type: message_complete` (full text).
