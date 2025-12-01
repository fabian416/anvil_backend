# DeFi Chat Platform API Documentation

Complete API reference for the DeFi Multi-Agents Chat Platform.

## Base URL

- **Production:** `https://api.defi-chat.example.com`
- **Staging:** `https://staging-api.defi-chat.example.com`
- **Local:** `http://localhost:8000`

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

### Getting a Token

**Sign Up:**
```bash
curl -X POST https://api.defi-chat.example.com/api/v1/account/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "username": "johndoe"
  }'
```

**Login:**
```bash
curl -X POST https://api.defi-chat.example.com/api/v1/account/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Rate Limits

- **Authenticated Users:** 100 requests/minute
- **Unauthenticated:** 20 requests/minute
- **WebSocket Connections:** 10 per user

Headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701432000
```

## Endpoints

### Chat

#### Create Conversation
```http
POST /api/v1/chat/conversations
Authorization: Bearer TOKEN
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-12-01T12:00:00Z",
  "messages": []
}
```

#### Send Message
```http
POST /api/v1/chat/conversations/{conversation_id}/messages
Authorization: Bearer TOKEN
Content-Type: application/json

{
  "content": "Swap 100 USDC to ETH"
}
```

Response:
```json
{
  "user_message": {
    "id": "...",
    "role": "user",
    "content": "Swap 100 USDC to ETH",
    "created_at": "2024-12-01T12:00:00Z"
  },
  "agent_message": {
    "id": "...",
    "role": "assistant",
    "content": "I'll help you swap 100 USDC to ETH...",
    "created_at": "2024-12-01T12:00:01Z"
  }
}
```

#### Get Conversation
```http
GET /api/v1/chat/conversations/{conversation_id}
Authorization: Bearer TOKEN
```

#### List Conversations
```http
GET /api/v1/chat/conversations?limit=20&offset=0
Authorization: Bearer TOKEN
```

### WebSocket

Connect to WebSocket for real-time chat:

```javascript
const ws = new WebSocket('wss://api.defi-chat.example.com/api/v1/chat/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'YOUR_JWT_TOKEN'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Send message
ws.send(JSON.stringify({
  type: 'message',
  conversation_id: '550e8400-e29b-41d4-a716-446655440000',
  content: 'What is BTC price?'
}));
```

### Health & Monitoring

#### Basic Health
```http
GET /health
```

#### Liveness Probe
```http
GET /health/live
```

#### Readiness Probe
```http
GET /health/ready
```

#### Metrics
```http
GET /metrics
```

## OpenAPI/Swagger

Interactive API documentation available at:

- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI JSON:** `/openapi.json`

## Examples

### Complete Swap Flow

```python
import requests

API_BASE = "https://api.defi-chat.example.com"

# 1. Login
response = requests.post(f"{API_BASE}/api/v1/account/login", json={
    "email": "user@example.com",
    "password": "password123"
})
token = response.json()["access_token"]

# 2. Create conversation
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(f"{API_BASE}/api/v1/chat/conversations", headers=headers)
conversation_id = response.json()["id"]

# 3. Ask about swap
response = requests.post(
    f"{API_BASE}/api/v1/chat/conversations/{conversation_id}/messages",
    headers=headers,
    json={"content": "Swap 100 USDC to ETH"}
)

print(response.json()["agent_message"]["content"])
```

### Trading Flow

```javascript
const axios = require('axios');

const API_BASE = 'https://api.defi-chat.example.com';
let token, conversationId;

// 1. Login
const login = async () => {
  const response = await axios.post(`${API_BASE}/api/v1/account/login`, {
    email: 'user@example.com',
    password: 'password123'
  });
  token = response.data.access_token;
};

// 2. Create conversation
const createConversation = async () => {
  const response = await axios.post(
    `${API_BASE}/api/v1/chat/conversations`,
    {},
    { headers: { Authorization: `Bearer ${token}` } }
  );
  conversationId = response.data.id;
};

// 3. Open trading position
const openPosition = async () => {
  const response = await axios.post(
    `${API_BASE}/api/v1/chat/conversations/${conversationId}/messages`,
    { content: 'Open 10x long BTC with $1000' },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  
  console.log(response.data.agent_message.content);
};

// Execute
(async () => {
  await login();
  await createConversation();
  await openPosition();
})();
```

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-12-01T12:00:00Z"
}
```

### Common Error Codes

- `401 UNAUTHORIZED` - Invalid or missing token
- `403 FORBIDDEN` - Insufficient permissions
- `404 NOT_FOUND` - Resource not found
- `422 UNPROCESSABLE_ENTITY` - Validation error
- `429 TOO_MANY_REQUESTS` - Rate limit exceeded
- `500 INTERNAL_SERVER_ERROR` - Server error
- `503 SERVICE_UNAVAILABLE` - Service temporarily unavailable

## SDKs

### Python SDK

```python
from defi_chat import DeFiChatClient

client = DeFiChatClient(
    api_key="YOUR_API_KEY",
    base_url="https://api.defi-chat.example.com"
)

# Create conversation
conversation = client.conversations.create()

# Send message
response = client.messages.send(
    conversation_id=conversation.id,
    content="Swap 100 USDC to ETH"
)

print(response.content)
```

### JavaScript SDK

```javascript
import { DeFiChatClient } from '@defi-chat/sdk';

const client = new DeFiChatClient({
  apiKey: 'YOUR_API_KEY',
  baseUrl: 'https://api.defi-chat.example.com'
});

// Create conversation
const conversation = await client.conversations.create();

// Send message
const response = await client.messages.send(conversation.id, {
  content: 'Swap 100 USDC to ETH'
});

console.log(response.content);
```

## Support

- **Documentation:** https://docs.defi-chat.example.com
- **API Status:** https://status.defi-chat.example.com
- **Discord:** https://discord.gg/defi-chat
- **Email:** support@defi-chat.example.com
