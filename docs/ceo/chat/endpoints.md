# Chat System Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Anvil Chat System provides three distinct endpoint categories:
1. **Guest Endpoints** - Public, unauthenticated access with rate limiting
2. **User Endpoints** - Authenticated user chat with full features
3. **Admin Endpoints** - Administrative dashboard and analytics

---

## 1. Guest Endpoints

**Base Path**: `/api/v1/guest`  
**Authentication**: None (IP-based tracking)  
**Rate Limits**: 5000/hour, 10000/day (testing mode)

### POST /guest/chat

Send a message as a guest user.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Message content (max 500 chars) |
| `language` | string | No | Language code: en, es, pt, zh (default: en) |

**Response Schema**:
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "user_message": {
    "id": "uuid",
    "role": "user",
    "content": "string",
    "created_at": "datetime"
  },
  "agent_message": {
    "id": "uuid",
    "role": "assistant",
    "content": "string",
    "created_at": "datetime",
    "sources": [...]
  },
  "routing": {
    "intent": "string",
    "confidence": 0.0-1.0,
    "handler": "string",
    "language": "string",
    "is_demo_mode": true
  },
  "enrichment": {...},
  "registration_required": null | {...},
  "guest_info": {...},
  "rate_limit_status": {...}
}
```

**Demo Mode Features**:
- ✅ Protocol search and discovery
- ✅ Risk assessment information
- ✅ Lending/money market rates (view only)
- ✅ Swap quotes (view only)
- ✅ General DeFi questions
- ✅ Price checks via Hunter AI

**Restricted Actions (require registration)**:
- ❌ View portfolio, balance, activity
- ❌ Execute swaps, deposits, withdrawals
- ❌ Get wallet receive address

**Source File**: `src/app/presentation/http/controllers/guest/router.py`

---

### GET /guest/history

Get conversation history for current guest session.

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Max messages (default: 50, max: 100) |

**Response**: List of messages with metadata

**Source File**: `src/app/presentation/http/controllers/guest/router.py`

---

### DELETE /guest/chat

Clear guest chat history (starts new conversation).

**Response**:
```json
{
  "success": true,
  "message": "Chat history cleared",
  "new_conversation_id": "uuid"
}
```

**Source File**: `src/app/presentation/http/controllers/guest/router.py`

---

### GET /guest/status

Get guest session status and rate limit info.

**Response**:
```json
{
  "session_active": true,
  "messages_remaining_hour": 4950,
  "messages_remaining_day": 9950,
  "conversation_id": "uuid",
  "language": "en"
}
```

**Source File**: `src/app/presentation/http/controllers/guest/router.py`

---

## 2. User Endpoints (Authenticated)

**Base Path**: `/api/v1/conversations`  
**Authentication**: Bearer JWT Token  
**Rate Limits**: Based on subscription tier

### POST /conversations

Create a new conversation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Conversation title (max 255 chars) |
| `language` | string | No | Language code (default: en) |

**Response**:
```json
{
  "id": "uuid",
  "title": "string",
  "status": "active",
  "created_at": "datetime",
  "updated_at": "datetime",
  "last_message_at": null,
  "message_count": 0,
  "language": "en"
}
```

**Source File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

---

### GET /conversations

List user's conversations.

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | No | Filter: active, archived, deleted |
| `limit` | int | No | Max results (default: 20, max: 100) |
| `offset` | int | No | Pagination offset |

**Response**: Paginated list of conversations

**Source File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

---

### GET /conversations/{id}

Get conversation with messages.

**Path Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Conversation ID |

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `include_messages` | bool | No | Include messages (default: true) |
| `message_limit` | int | No | Max messages (default: 50) |

**Source File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

---

### POST /conversations/{id}/messages

Send a message to a conversation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Message content (max 2000 chars) |
| `language` | string | No | Language code (default: en) |

**Response Schema**:
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "user_message": {...},
  "agent_message": {...},
  "routing": {
    "intent": "SUPERVISOR_WORKFLOW",
    "confidence": 1.0,
    "handler": "authenticated_supervisor",
    "language": "en",
    "user_type": "authenticated",
    "agents_used": ["hunter_ai", "swap_workflow", ...]
  },
  "enrichment": {
    "agent_squad": true,
    "workflow_type": "authenticated_supervisor",
    "task_count": 1,
    "agents_used": [...],
    "agent_timings": {...},
    "sources": [...],
    "total_time_ms": 1234
  },
  "execute": null | {...},
  "rate_limit_status": {...}
}
```

**Intent Routing (Authenticated Users)**:
- All requests → Agent Squad Supervisor
- Supervisor routes to appropriate agents:
  - `hunter_ai` - Price checks, market data
  - `swap_workflow` - Token swaps (Hyperliquid/1inch/LiFi)
  - `lending_workflow` - Deposit/yield operations
  - `portfolio` - Portfolio analysis
  - `risk_analyzer` - Risk assessment
  - `knowledge` - DeFi education

**Source File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

---

### PUT /conversations/{id}

Update conversation (title, status).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | New title |

**Source File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

---

### DELETE /conversations/{id}

Archive/delete a conversation.

**Source File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

---

### POST /conversations/{id}/execute

Execute a pending action (swap, deposit, etc.).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_id` | string | Yes | Action ID from execute_data |
| `confirm` | bool | Yes | User confirmation |

**Response**:
```json
{
  "success": true,
  "transaction_hash": "0x...",
  "action_type": "swap",
  "details": {...}
}
```

**Source File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

---

## 3. Admin Endpoints

**Base Path**: `/api/v1/admin/chat`  
**Authentication**: Bearer JWT Token + Admin Role  
**Access**: Admin users only

### GET /admin/chat/dashboard

Get comprehensive dashboard summary.

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date_from` | datetime | No | Start date (default: 30 days ago) |
| `date_to` | datetime | No | End date (default: now) |

**Response**: Dashboard summary with all key metrics

**Source File**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`

---

### GET /admin/chat/dashboard/agents/performance

Get agent performance leaderboard.

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sort_by` | string | No | invocations, success_rate, avg_response_time, total_cost |
| `limit` | int | No | Max agents (default: 10, max: 50) |
| `agent_type` | string | No | Filter by specific agent |

**Source File**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`

---

### GET /admin/chat/dashboard/cache/efficiency

Monitor cache performance metrics.

**Response**:
```json
{
  "overall_hit_rate": 0.85,
  "miss_rate": 0.15,
  "memory_usage_mb": 256,
  "cache_size": 10000,
  "eviction_count": 500,
  "hit_rate_by_type": {...}
}
```

**Source File**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`

---

### GET /admin/chat/dashboard/costs

Monitor LLM API costs.

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `group_by` | string | No | agent, model, day, user |

**Response**:
```json
{
  "total_spend": 150.50,
  "cost_by_agent": {...},
  "cost_by_model": {...},
  "daily_trend": [...],
  "avg_cost_per_conversation": 0.05,
  "token_usage": {...}
}
```

**Source File**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`

---

### GET /admin/chat/dashboard/errors

Monitor error rates and types.

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `severity` | string | No | critical, high, medium, low |

**Source File**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`

---

### GET /admin/chat/dashboard/users/active

Get active users metrics (DAU, WAU, MAU).

**Source File**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`

---

### GET /admin/chat/dashboard/conversations/metrics

Get conversation statistics and patterns.

**Source File**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`

---

### GET /admin/chat/dashboard/export

Export analytics data.

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `format` | string | No | json, csv |
| `include_sections` | list | No | agents, costs, errors, users, conversations |

**Source File**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`

---

## 4. WebSocket Endpoints

**Path**: `/ws/chat/{conversation_id}`  
**Authentication**: Query param or header token

Real-time message streaming for authenticated users.

**Events**:
- `message` - New message received
- `typing` - Agent typing indicator
- `status` - Connection status updates
- `error` - Error notifications

**Source File**: `src/app/presentation/http/controllers/chat/websocket_router.py`

---

## 5. Intent Detection Endpoints

**Base Path**: `/api/v1/chat/intent`

### POST /chat/intent/detect

Detect intent from message (testing/debug).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | Message to analyze |
| `language` | string | No | Language code |

**Response**:
```json
{
  "intent": "SWAP",
  "confidence": 0.95,
  "entities": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0"
  },
  "metadata": {...}
}
```

**Source File**: `src/app/presentation/http/controllers/chat/intent_detection_router.py`

---

## Error Responses

All endpoints return standardized error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {...}
  }
}
```

**Common Error Codes**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `UNAUTHORIZED` | 401 | Invalid or missing token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid input |
| `INTERNAL_ERROR` | 500 | Server error |

---

## References

- **Guest Router**: `src/app/presentation/http/controllers/guest/router.py`
- **Conversations Router**: `src/app/presentation/http/controllers/chat/conversations_router.py`
- **Admin Dashboard**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`
- **WebSocket Router**: `src/app/presentation/http/controllers/chat/websocket_router.py`
- **Intent Detection**: `src/app/presentation/http/controllers/chat/intent_detection_router.py`
