# Module: AI Agent Chat

**Route**: `/chat`
**Auth Required**: Yes
**Package**: `user/chat`

## 1. Overview
Interface for Hunter AI.

## 2. API Contract

### List Conversations
**Endpoint**: `GET /api/v1/user/chat/conversations`
**Query**: `limit`, `offset`.
**Response**: `ConversationListResponse` (`conversations`: Array, `total`: int).

### Send Message
**Endpoint**: `POST /api/v1/user/chat/conversations/{conversation_id}/messages`
**Body (`SendMessageRequest`)**:
```json
{
  "content": "Buy 0.1 ETH on Base"
}
```
**Response (`SendMessageResponse`)**:
```json
{
  "user_message": { "id": "...", "content": "Buy..." },
  "agent_message": { "id": "...", "content": "Processing...", "agent_type": "hunter" }
}
```
*Note: Response is technically standard JSON here, but frontend might use a different Stream endpoint if implemented, or poll. Current Router is standard JSON.*

### Create Conversation
**Endpoint**: `POST /api/v1/user/chat/conversations`
**Body**: `{"title": "optional"}`

## 3. Implementation Flow
1.  **Mount**: List conversations. If empty, create one.
2.  **Chat**:
    - User sends message.
    - Optimistic Update.
    - **POST** to backend.
    - Receive full `agent_message` (Synchronous wait for LLM).
    - *Future Upgrade*: Server-Sent Events (SSE) for streaming. Current contract is Request/Response.
