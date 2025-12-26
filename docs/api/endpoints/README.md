# API Endpoints Reference

**Purpose**: Comprehensive API endpoint documentation
**Audience**: Frontend developers, API consumers, integration partners

---

## 📚 Quick Navigation

- [Main API Documentation](../README.md)
- [Chat Endpoints Guide](../../CHAT_ENDPOINTS_EXPLAINED.md)
- [API Examples](../examples/README.md)
- [Authentication](../authentication.md)

---

## 🚀 Featured: Unified Chat Routing

### `/api/v1/user/chat/conversations/{conversation_id}/messages`

**NEW** (Phase 8): Intelligent intent-based routing system that automatically directs messages to the most appropriate handler.

**Single endpoint for**:
- 🔍 Protocol search & discovery (GraphRAG)
- ⚠️ Risk assessment & analysis (GraphRAG)
- 🔄 Finding similar protocols (GraphRAG)
- 📊 Market sentiment analysis (Hunter AI)
- 📈 Price predictions & forecasts (Hunter AI)
- ⚡ Trading signals & patterns (Hunter AI)
- 💼 Portfolio optimization (Hunter AI)
- 🔎 Arbitrage opportunity discovery (ULTRA)
- ⚡ Flash loan protocol selection (ULTRA)
- 🛡️ MEV-protected execution (ULTRA)
- 🤖 Automated trading bot control (ULTRA)
- 🤖 Specialist AI tasks (Agent Squad - 18 agents)
- 🎯 Complex multi-agent workflows (Supervisor)
- 💬 General conversation (Traditional chat)

**Request**:
```http
POST /api/v1/user/chat/conversations/{conversation_id}/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Show me safe lending protocols on Ethereum"
}
```

**Response**:
```json
{
  "user_message": { ... },
  "agent_message": {
    "content": "I found 5 safe lending protocols...",
    "agent_type": "graphrag_search"
  },
  "routing": {
    "intent": "protocol_search",
    "confidence": 0.91,
    "handler": "graphrag_search",
    "reasoning": "User query matches protocol search pattern with risk and chain filters"
  },
  "enrichment": {
    "protocols": [...],
    "search_context": "Filtered for low-risk lending protocols on Ethereum"
  }
}
```

**Benefits**:
- ✅ No need to choose which endpoint to use
- ✅ AI-powered routing (98% accuracy)
- ✅ Cost optimized (up to 98% savings on graph queries)
- ✅ Transparent routing metadata
- ✅ All messages saved to conversation history

**Full Documentation**: [Chat Endpoints Explained](../../CHAT_ENDPOINTS_EXPLAINED.md#0-unified-routing-system-new)

---

## 📋 Endpoint Categories

### Chat Endpoints (`/api/v1/user/chat/`)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/conversations` | GET | List user conversations | ✅ Active |
| `/conversations` | POST | Create new conversation | ✅ Active |
| `/conversations/{id}` | GET | Get conversation details | ✅ Active |
| `/conversations/{id}` | DELETE | Delete conversation | ✅ Active |
| `/conversations/{id}/messages` | POST | Send message (unified routing) | ⭐ **NEW** |
| `/conversations/{id}/messages` | GET | List conversation messages | ✅ Active |
| `/search-protocols` | POST | Protocol search (direct) | ✅ Active |
| `/analyze-risk` | POST | Risk analysis (direct) | ✅ Active |
| `/similar-protocols` | POST | Find similar protocols (direct) | ✅ Active |
| `/agent-squad/messages` | POST | Agent Squad (direct) | ✅ Active |
| `/agent-squad/supervisor` | POST | Supervisor workflow (direct) | ✅ Active |
| `/agent-squad/agents` | GET | List enabled agents | ✅ Active |
| `/detect-intent` | POST | Test intent detection | ✅ Active |
| `/autocomplete` | POST | Autocomplete suggestions | ✅ Active |
| `/similar-conversations` | POST | Find similar conversations | ✅ Active |

**Note**: Direct endpoints (`/search-protocols`, `/analyze-risk`, etc.) are still available for:
- Programmatic access requiring specific handler
- Testing and debugging
- Legacy integrations

**Recommendation**: Use unified routing endpoint (`/conversations/{id}/messages`) for new integrations.

---

## 📖 Documentation by Category

### User Endpoints

#### Chat & Conversations
- **Full Guide**: [Chat Endpoints Explained](../../CHAT_ENDPOINTS_EXPLAINED.md)
- **Unified Routing**: [Unified Routing System](../../CHAT_ENDPOINTS_EXPLAINED.md#0-unified-routing-system-new)
- **Examples**: [Chat API Examples](../examples/unified-routing.md)

#### Portfolio Management
- **Endpoint**: `/api/v1/user/portfolio/*`
- **Documentation**: Coming soon

#### Transactions
- **Endpoint**: `/api/v1/user/transactions/*`
- **Documentation**: Coming soon

#### Graph & Analytics
- **Endpoint**: `/api/v1/user/graph/*`
- **Documentation**: Coming soon

#### Machine Learning
- **Endpoint**: `/api/v1/user/ml/*`
- **Documentation**: Coming soon

#### Markets & Trading
- **Endpoint**: `/api/v1/user/markets/*`
- **Documentation**: Coming soon

#### Hunter AI
- **Endpoint**: `/api/v1/user/hunter/*`
- **Documentation**: Coming soon

#### ULTRA Tools
- **Endpoint**: `/api/v1/user/ultra/*`
- **Documentation**: Coming soon

---

## 🔐 Authentication

All user endpoints require Bearer token authentication:

```http
Authorization: Bearer <jwt_token>
```

**Get Token**:
```http
POST /api/v1/account/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

**See**: [Authentication Guide](../authentication.md)

---

## 📝 Response Standards

### Success Response
```json
{
  "data": { ... },
  "status": "success"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "status_code": 400
}
```

### Common Status Codes
- `200 OK` - Successful GET request
- `201 Created` - Successful POST (creation)
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid auth token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## 🚀 Rate Limiting

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Chat (unified routing) | 60 req/min | Per user |
| Agent Squad (direct) | 100 req/min | Per user |
| GraphRAG endpoints | 200 req/min | Per user |
| Authentication | 10 req/min | Per IP |
| Admin endpoints | 1000 req/min | Per admin user |

**Headers**:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```

---

## 📚 Related Documentation

- [Main API Documentation](../README.md)
- [Chat Endpoints Explained](../../CHAT_ENDPOINTS_EXPLAINED.md)
- [API Examples](../examples/README.md)
- [Authentication Guide](../authentication.md)
- [Error Handling](../error-handling.md)
- [Frontend Integration](../../frontend/README.md)

---

**Last Updated**: December 26, 2025
