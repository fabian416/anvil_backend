# API Documentation - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅  
**Base URL**: `/api/v1`

---

## Executive Summary

La API de Anvil Backend es una REST API completa construida con FastAPI que proporciona:

- **200+ endpoints** organizados en 30+ módulos
- **REST API** para operaciones CRUD y business logic
- **WebSocket** para comunicación en tiempo real
- **Autenticación JWT** con Bearer tokens
- **Autorización basada en roles** (ADMIN, MODERATOR, USER, GUEST)
- **Multi-idioma** (en, es, pt, zh)
- **Rate limiting** por IP y usuario
- **Error handling** estructurado con `fastapi-error-map`
- **OpenAPI/Swagger** documentation automática

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────┐
                    │   Root Router (/)            │
                    │   → Redirects to /docs       │
                    └──────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────────────────┐
                    │   API v1 Router              │
                    │   /api/v1                    │
                    └──────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Public      │    │   User        │    │   Admin       │
│   Endpoints   │    │   Endpoints   │    │   Endpoints   │
├───────────────┤    ├───────────────┤    ├───────────────┤
│• /guest       │    │• /user/chat   │    │• /admin/users │
│• /account     │    │• /user/wallet │    │• /admin/llm   │
│  (signup/login)│   │• /user/portfolio│   │• /admin/agents│
│• /general     │    │• /user/markets │   │• /admin/stats │
│  (healthcheck)│    │• /user/alerts │   │• /admin/retry │
│               │    │• /user/projects│   │• /admin/...   │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## API Structure

### Base URL

```
Production: https://api.anvil.com/api/v1
Development: http://localhost:8000/api/v1
```

### Versioning

- **Current Version**: `v1`
- **Version Prefix**: `/api/v1`
- **Future Versions**: `/api/v2`, `/api/v3`, etc.

### OpenAPI Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Endpoint Categories

### 1. Public Endpoints (No Authentication)

#### Account Management (`/account`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/account/signup` | User registration | ❌ |
| `POST` | `/account/login` | User login (email/password) | ❌ |
| `POST` | `/account/privy-login` | Privy Web3 login | ❌ |
| `POST` | `/account/password-reset/request` | Request password reset | ❌ |
| `POST` | `/account/password-reset/confirm` | Confirm password reset | ❌ |

#### Guest Chat (`/guest`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/guest/chat` | Send guest message (IP-based) | ❌ |
| `GET` | `/guest/chat/history` | Get guest chat history | ❌ |
| `GET` | `/guest/chat/status` | Get guest status & rate limits | ❌ |

**Features**:
- IP-based tracking
- Rate limiting: 20 msgs/hour, 50 msgs/day
- Multi-language support (en, es, pt, zh)
- Demo mode (view-only actions)

#### General (`/general`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/healthcheck` | Health check | ❌ |
| `GET` | `/chat/shortcuts` | Get chat shortcuts | ❌ |

---

### 2. Authenticated User Endpoints

**Authentication**: Bearer token required (`Authorization: Bearer <token>`)

#### Chat (`/user/chat`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/conversations` | Create conversation |
| `GET` | `/conversations` | List conversations (pagination) |
| `GET` | `/conversations/{id}` | Get conversation |
| `POST` | `/conversations/{id}/messages` | Send message (unified routing) |
| `GET` | `/conversations/{id}/messages` | Get messages |
| `POST` | `/conversations/{id}/execute` | Execute action (swap, deposit, etc.) |
| `POST` | `/search-protocols` | GraphRAG protocol search |
| `POST` | `/analyze-risk` | ML risk analysis |
| `POST` | `/similar-protocols` | Find similar protocols |
| `POST` | `/agent-squad/messages` | Agent Squad message |
| `POST` | `/agent-squad/supervisor` | Multi-agent workflow |
| `GET` | `/agent-squad/agents` | List enabled agents |

**Unified Routing**:
- Automatic intent detection (LLM + keyword fallback)
- Routes to: GraphRAG, Agent Squad, Supervisor, Regular Chat
- Response includes routing metadata

**Execute Actions**:
- `swap`, `deposit`, `withdraw`, `transfer`, `approve`, `bridge`
- Two-step flow: simulate → confirm → execute
- Transaction limits enforced

#### Wallet (`/wallet`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/me` | Get all wallets for user |
| `POST` | `/sync` | Sync wallets from frontend |
| `POST` | `/export` | Export wallet private key (HPKE encrypted) |

#### Portfolio (`/user/portfolio`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/snapshots` | Get portfolio snapshots |
| `GET` | `/positions` | Get DeFi positions (Aave, Morpho, Hyperliquid) |
| `GET` | `/balances` | Get token balances |

#### Markets (`/user/markets`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tokens` | Get token prices |
| `GET` | `/protocols` | Get protocol data |
| `GET` | `/yields` | Get yield opportunities |

#### Alerts (`/user/alerts`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create price alert |
| `GET` | `/` | List alerts |
| `DELETE` | `/{id}` | Delete alert |

#### Projects (`/user/projects`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List user projects |
| `GET` | `/{id}` | Get project details |
| `POST` | `/{id}/assign` | Assign to project |

#### Transactions (`/user/transactions`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List transactions |
| `GET` | `/{id}` | Get transaction details |
| `POST` | `/log` | Log transaction |

#### Bitcoin (`/user/bitcoin`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/wallet` | Get Bitcoin wallet |
| `POST` | `/transaction` | Create Bitcoin transaction |

#### DeFi Protocols (`/user/defi`)

**Aave** (`/aave`):
- `GET /markets` - List markets
- `GET /positions` - User positions
- `POST /deposit` - Deposit
- `POST /withdraw` - Withdraw

**Morpho** (`/morpho`):
- `GET /vaults` - List vaults
- `GET /positions` - User positions
- `POST /deposit` - Deposit
- `POST /withdraw` - Withdraw

**Hyperliquid** (`/hyperliquid`):
- `GET /positions` - Perpetual positions
- `POST /trade` - Place order

**Curve** (`/curve`):
- `GET /pools` - List pools
- `GET /gauges` - List gauges

**Axelar** (`/axelar`):
- `GET /chains` - Supported chains
- `POST /bridge` - Cross-chain bridge

**LayerZero** (`/layerzero`):
- `GET /chains` - Supported chains
- `POST /bridge` - Cross-chain bridge

#### Hunter AI (`/user/hunter`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/sentiment` | Sentiment analysis |
| `POST` | `/price-prediction` | Price prediction |
| `POST` | `/risk-analysis` | Risk analysis |
| `POST` | `/trading-signals` | Trading signals |
| `POST` | `/portfolio-optimization` | Portfolio optimization |
| `POST` | `/pattern-recognition` | Pattern recognition |

#### ULTRA Arbitrage (`/user/ultra`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/flash-loans` | Flash loan opportunities |
| `POST` | `/arbitrage` | Arbitrage discovery |
| `POST` | `/mev-protection` | MEV protection |
| `POST` | `/auto-executor` | Auto-executor |

#### GraphRAG (`/user/graph`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/search` | Hybrid search (semantic + graph) |
| `GET` | `/analytics` | Graph analytics |
| `GET` | `/monitoring` | Graph monitoring |
| `GET` | `/visualization` | Graph visualization |

#### ML (`/user/ml`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/prediction` | ML predictions |
| `POST` | `/network` | Network analysis |

#### Preferences (`/user/preferences`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Get preferences |
| `PUT` | `/` | Update preferences |

#### Dashboard (`/user/dashboard`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard summary |
| `GET` | `/metrics` | Dashboard metrics |

#### Search (`/user/search`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Search (protocols, tokens, etc.) |

#### Comparison (`/user/comparison`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Compare assets/protocols |

#### Notifications (`/user/notifications`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List notifications |
| `PUT` | `/{id}/read` | Mark as read |

#### Metrics (`/metrics`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Get metrics |
| `POST` | `/track` | Track event |

---

### 3. Admin Endpoints

**Authentication**: Bearer token + ADMIN role required

#### User Management (`/admin/users`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List users (pagination, search) |
| `PATCH` | `/{email}/grant-admin` | Grant admin (super admin only) |
| `PATCH` | `/{email}/revoke-admin` | Revoke admin (super admin only) |
| `PATCH` | `/{email}/activate` | Activate user |
| `PATCH` | `/{email}/deactivate` | Deactivate user |
| `PATCH` | `/{email}/password` | Change user password |

#### Wallet Management (`/admin/wallets`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List wallets (filters) |
| `GET` | `/{privy_wallet_id}` | Get wallet details |
| `PATCH` | `/{privy_wallet_id}` | Update wallet |

#### LLM Orchestration (`/admin/llm`)

**Dashboard** (`/dashboard`):
- `GET /` - LLM dashboard
- `WS /ws` - Real-time updates
- `POST /export` - Export data

**Providers** (`/providers`):
- `GET /` - List providers
- `GET /{id}` - Get provider
- `PATCH /{id}` - Update provider
- `POST /{id}/health-check` - Health check

**Models** (`/models`):
- `GET /` - List models
- `GET /{id}` - Get model
- `PATCH /{id}` - Update model
- `GET /{id}/performance` - Performance metrics

**Rankings** (`/rankings`):
- `GET /` - Model performance leaderboard

**Telemetry** (`/telemetry`):
- `GET /metrics` - LLM metrics
- `GET /costs` - Cost tracking
- `GET /models` - Model usage
- `GET /alerts` - Alerts
- `GET /providers` - Provider stats
- `POST /reset` - Reset metrics

**Budgets** (`/budgets`):
- `GET /` - List budgets
- `PUT /` - Update budgets
- `GET /alerts` - Budget alerts

**Circuit Breakers** (`/circuit-breakers`):
- `GET /` - List circuit breakers
- `POST /{service}/reset` - Reset circuit breaker

#### Agent Management (`/admin/agents`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all agents |

#### Retry System (`/admin/retry`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/services` | List services with retry status |
| `POST` | `/services/{service}/enable` | Enable service |
| `POST` | `/services/{service}/disable` | Disable service |
| `POST` | `/circuit-breakers/{service}/reset` | Reset circuit breaker |

#### Security Dashboard (`/admin/security`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard` | Security dashboard |
| `GET` | `/scans/latest` | Latest security scan |
| `GET` | `/scans/{id}` | Get scan details |
| `GET` | `/scans` | List scans |
| `GET` | `/trends` | Vulnerability trends |
| `GET` | `/health` | Security system health |

#### Chat Analytics (`/admin/chat`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard` | Chat dashboard |
| `GET` | `/dashboard/agents/performance` | Agent performance |
| `GET` | `/dashboard/cache/efficiency` | Cache efficiency |
| `GET` | `/dashboard/costs` | Cost tracking |
| `GET` | `/dashboard/errors` | Error monitoring |
| `GET` | `/dashboard/export` | Export data |

#### Transactions Admin (`/admin/transactions`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List transactions (filters) |

#### Projects Management (`/admin/projects`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create project |
| `GET` | `/` | List projects |
| `GET` | `/{id}` | Get project |
| `PATCH` | `/{id}` | Update project |
| `DELETE` | `/{id}` | Delete project |
| `POST` | `/{id}/activate` | Activate project |
| `POST` | `/{id}/knowledge/documents` | Add knowledge document |
| `GET` | `/{id}/knowledge/documents` | List documents |
| `POST` | `/{id}/assignment-rules` | Create assignment rule |
| `GET` | `/{id}/assignment-rules` | List assignment rules |
| `PATCH` | `/{id}/assignment-rules/{rule_id}` | Update rule |
| `POST` | `/{id}/assignments` | Create assignment |
| `GET` | `/{id}/assignments` | List assignments |

#### Distillation (`/admin/distillation`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/static-responses` | Create static response |
| `GET` | `/static-responses` | List static responses |
| `PATCH` | `/static-responses/{id}` | Update static response |
| `DELETE` | `/static-responses/{id}` | Delete static response |
| `GET` | `/config` | Get config |
| `PATCH` | `/config` | Update config |
| `POST` | `/cache/invalidate` | Invalidate cache |
| `GET` | `/cache/stats` | Cache statistics |
| `GET` | `/telemetry/requests` | Telemetry requests |
| `GET` | `/telemetry/summary` | Telemetry summary |

#### Policies (`/admin/policies`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List Privy policies |
| `POST` | `/` | Create policy |
| `GET` | `/{id}` | Get policy |
| `PATCH` | `/{id}` | Update policy |
| `POST` | `/{id}/rules` | Manage policy rules |
| `GET` | `/{id}/rules` | List policy rules |

#### Stats (`/admin/stats`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | System statistics |

#### Metrics (`/admin/metrics`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/overview` | Metrics overview |
| `GET` | `/transactions/timeseries` | Transaction time series |
| `GET` | `/wallets/timeseries` | Wallet time series |
| `GET` | `/users/activity` | User activity |
| `GET` | `/wallets/distribution` | Wallet distribution |
| `GET` | `/transactions/distribution` | Transaction distribution |

#### Telemetry Flags (`/admin/telemetry`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/flags` | Get telemetry flags |
| `PUT` | `/flags` | Update telemetry flags |
| `POST` | `/flags/disable-api/{api_name}` | Disable API telemetry |
| `POST` | `/flags/enable-api/{api_name}` | Enable API telemetry |
| `POST` | `/flags/disable-llm/{provider}` | Disable LLM telemetry |
| `POST` | `/flags/enable-llm/{provider}` | Enable LLM telemetry |
| `POST` | `/flags/save` | Save flags to Redis |
| `POST` | `/flags/load` | Load flags from Redis |
| `DELETE` | `/flags/saved` | Delete saved flags |

---

### 4. Subscription & Payment

#### Subscription (`/subscription`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | Get available subscriptions | ✅ |
| `POST` | `/init` | Initialize subscriptions (admin) | ✅ |
| `POST` | `/{id}/subscribe` | Create subscription | ✅ |
| `POST` | `/{id}/cancel` | Cancel subscription | ✅ |
| `GET` | `/success` | Subscription success callback | ❌ |
| `GET` | `/cancel` | Subscription cancel callback | ❌ |

#### Payment (`/payment`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | Get payment information | ✅ |
| `POST` | `/` | Process payment | ✅ |

---

### 5. WebSocket Endpoints

#### Chat WebSocket (`/ws/chat`)

**Connection**: `ws://localhost:8000/api/v1/ws/chat`

**Features**:
- Real-time agent responses
- Streaming support
- Session management
- Multi-language support

#### Graph WebSocket (`/ws/graph`)

**Connection**: `ws://localhost:8000/api/v1/ws/graph`

**Features**:
- Real-time graph updates
- GraphRAG search results
- Analytics updates

#### LLM Dashboard WebSocket (`/admin/llm/dashboard/ws`)

**Connection**: `ws://localhost:8000/api/v1/admin/llm/dashboard/ws`

**Features**:
- Real-time LLM metrics
- Provider status updates
- Model performance updates

---

## Authentication & Authorization

### Authentication Methods

#### 1. Bearer Token (JWT)

**Header**:
```
Authorization: Bearer <access_token>
```

**Token Types**:
- **Access Token**: Short-lived (15 minutes default)
- **Refresh Token**: Long-lived (7 days default)

**Endpoints**:
- `POST /account/login` - Get access + refresh tokens
- `POST /account/refresh-token` - Refresh access token
- `POST /account/logout` - Invalidate tokens

#### 2. Privy Web3 Login

**Endpoint**: `POST /account/privy-login`

**Request**:
```json
{
  "privy_token": "<privy_access_token>",
  "wallet_address": "0x...",
  "chain": "ethereum"
}
```

**Response**:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {...}
}
```

### Authorization

**Role-Based Access Control (RBAC)**:

| Role | Access Level |
|------|--------------|
| **GUEST** | Public endpoints only |
| **USER** | User endpoints |
| **MODERATOR** | User + moderation endpoints |
| **ADMIN** | All endpoints (except super admin) |
| **SUPER_ADMIN** | All endpoints (email-based, immutable) |

**Permission Checks**:
- Endpoints use `Security(bearer_scheme)` for authentication
- Application layer (interactors) check permissions
- See [permissions-scopes.md](./permissions-scopes.md) for details

---

## Request/Response Formats

### Request Headers

**Required**:
```
Authorization: Bearer <token>  # For authenticated endpoints
Content-Type: application/json
```

**Optional**:
```
Accept-Language: en|es|pt|zh  # Language preference
X-Request-ID: <uuid>          # Request tracking
```

### Response Format

**Success** (200 OK):
```json
{
  "data": {...},
  "meta": {
    "timestamp": "2026-01-02T12:00:00Z",
    "request_id": "uuid"
  }
}
```

**Error** (4xx/5xx):
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {...}
  },
  "meta": {
    "timestamp": "2026-01-02T12:00:00Z",
    "request_id": "uuid"
  }
}
```

### Pagination

**Query Parameters**:
- `limit`: Number of items (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)

**Response**:
```json
{
  "items": [...],
  "total": 100,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Sorting

**Query Parameters**:
- `sort_by`: Field to sort by
- `sort_order`: `asc` or `desc` (default: `desc`)

**Example**:
```
GET /api/v1/admin/users?sort_by=created_at&sort_order=desc
```

### Filtering

**Query Parameters**:
- Filter by field: `?field=value`
- Multiple filters: `?field1=value1&field2=value2`
- Search: `?search=query`

**Example**:
```
GET /api/v1/admin/users?role=admin&is_active=true&search=john
```

---

## Error Handling

### Error Codes

**Authentication Errors** (401):
- `AUTHENTICATION_ERROR`: Invalid or missing token
- `TOKEN_EXPIRED`: Access token expired
- `INVALID_CREDENTIALS`: Invalid email/password

**Authorization Errors** (403):
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `ROLE_REQUIRED`: Specific role required

**Validation Errors** (400):
- `VALIDATION_ERROR`: Request validation failed
- `MISSING_FIELD`: Required field missing
- `INVALID_FORMAT`: Invalid data format

**Not Found Errors** (404):
- `NOT_FOUND`: Resource not found
- `USER_NOT_FOUND`: User not found
- `CONVERSATION_NOT_FOUND`: Conversation not found

**Conflict Errors** (409):
- `ALREADY_EXISTS`: Resource already exists
- `DUPLICATE_ENTRY`: Duplicate entry

**Service Errors** (503):
- `SERVICE_UNAVAILABLE`: External service unavailable
- `DATABASE_ERROR`: Database error
- `EXTERNAL_API_ERROR`: External API error

### Error Response Example

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  },
  "meta": {
    "timestamp": "2026-01-02T12:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## Rate Limiting

### Guest Endpoints

- **Per IP**: 20 requests/hour
- **Per IP**: 50 requests/day
- **Message Length**: Max 500 characters

### Authenticated Endpoints

- **Per User**: 1000 requests/hour
- **Per User**: 10000 requests/day
- **Burst**: 100 requests/minute

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1641024000
```

### Rate Limit Exceeded

**Status**: `429 Too Many Requests`

**Response**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Multi-Language Support

### Supported Languages

- `en` - English (default)
- `es` - Spanish
- `pt` - Portuguese
- `zh` - Mandarin Chinese

### Language Detection

**Methods**:
1. **Request Header**: `Accept-Language: es`
2. **Query Parameter**: `?language=es`
3. **Request Body**: `{"language": "es", ...}`

### Language-Specific Endpoints

Most chat and agent endpoints support language parameter:

```json
POST /api/v1/user/chat/conversations/{id}/messages
{
  "content": "Hello",
  "language": "es"
}
```

---

## WebSocket API

### Connection

**URL**: `ws://localhost:8000/api/v1/ws/chat`

**Headers**:
```
Authorization: Bearer <token>
```

### Message Format

**Client → Server**:
```json
{
  "type": "message",
  "conversation_id": "uuid",
  "content": "Hello",
  "language": "en"
}
```

**Server → Client**:
```json
{
  "type": "message",
  "conversation_id": "uuid",
  "message_id": "uuid",
  "content": "Hello! How can I help?",
  "agent_type": "chat",
  "streaming": false
}
```

### Message Types

- `message` - Chat message
- `stream_start` - Start of streaming response
- `stream_chunk` - Streaming chunk
- `stream_end` - End of streaming
- `error` - Error message
- `ping` - Keep-alive ping
- `pong` - Keep-alive pong

---

## API Examples

### Example 1: Create Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/user/chat/conversations" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "DeFi Portfolio Discussion"
  }'
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "title": "DeFi Portfolio Discussion",
  "created_at": "2026-01-02T12:00:00Z",
  "updated_at": "2026-01-02T12:00:00Z"
}
```

### Example 2: Send Message (Unified Routing)

```bash
curl -X POST "http://localhost:8000/api/v1/user/chat/conversations/{id}/messages" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Find low-risk staking on Ethereum",
    "language": "en"
  }'
```

**Response**:
```json
{
  "user_message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "user",
    "content": "Find low-risk staking on Ethereum",
    "created_at": "2026-01-02T12:00:00Z"
  },
  "agent_message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "assistant",
    "content": "Here are some low-risk staking options...",
    "agent_type": "graphrag_search",
    "created_at": "2026-01-02T12:00:01Z"
  },
  "routing": {
    "intent": "PROTOCOL_SEARCH",
    "confidence": 0.95,
    "handler": "graphrag_search",
    "reasoning": "Message contains protocol search keywords",
    "total_latency_ms": 850
  },
  "enrichment": {
    "protocols": [
      {
        "protocol_id": "uuid",
        "protocol_name": "Lido",
        "risk_score": 0.15,
        "apy": 4.2
      }
    ],
    "search_context": "Found 5 protocols matching criteria",
    "recommendations": [...]
  }
}
```

### Example 3: Execute Swap Action

```bash
# Step 1: Get simulation
curl -X POST "http://localhost:8000/api/v1/user/chat/conversations/{id}/execute" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "swap",
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "0.5",
    "chain": "base",
    "confirmed": false
  }'

# Step 2: Confirm execution
curl -X POST "http://localhost:8000/api/v1/user/chat/conversations/{id}/execute" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "swap",
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "0.5",
    "chain": "base",
    "confirmed": true
  }'
```

### Example 4: List Users (Admin)

```bash
curl -X GET "http://localhost:8000/api/v1/admin/users?limit=20&offset=0&sort_by=created_at&sort_order=desc&search=john" \
  -H "Authorization: Bearer <admin_token>"
```

---

## API Versioning Strategy

### Current Version: v1

**Stability**:
- **Stable**: Core endpoints (account, chat, wallet)
- **Beta**: New features (GraphRAG, Agent Squad)
- **Experimental**: Advanced features (ML, ULTRA)

### Future Versions

**v2** (Planned):
- GraphQL support
- Webhook subscriptions
- Batch operations
- Advanced filtering

**Migration**:
- v1 endpoints remain available
- v2 endpoints use `/api/v2` prefix
- Deprecation notices 6 months before removal

---

## OpenAPI/Swagger Documentation

### Access

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Features

- **Interactive Testing**: Test endpoints directly from browser
- **Schema Validation**: Request/response schemas
- **Authentication**: Test with Bearer tokens
- **Examples**: Request/response examples

---

## Best Practices

### 1. Use Proper HTTP Methods

- `GET` - Read operations
- `POST` - Create operations
- `PUT` - Full update
- `PATCH` - Partial update
- `DELETE` - Delete operations

### 2. Handle Errors Gracefully

- Check status codes
- Parse error responses
- Retry with exponential backoff
- Log errors for debugging

### 3. Use Pagination

- Always use `limit` and `offset`
- Check `has_more` for additional pages
- Default limit: 20, max: 100

### 4. Implement Rate Limiting

- Respect `X-RateLimit-*` headers
- Implement exponential backoff
- Cache responses when possible

### 5. Use WebSockets for Real-Time

- Use WebSocket for streaming responses
- Fallback to REST for compatibility
- Handle reconnection logic

### 6. Language Support

- Always include `language` parameter
- Default to `en` if not specified
- Support all 4 languages (en, es, pt, zh)

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/app/run.py` | FastAPI app factory |
| `src/app/presentation/http/controllers/root_router.py` | Root router |
| `src/app/presentation/http/controllers/api_v1_router.py` | API v1 router |
| `src/app/presentation/http/controllers/account/router.py` | Account endpoints |
| `src/app/presentation/http/controllers/chat/router.py` | Chat endpoints |
| `src/app/presentation/http/controllers/admin/router.py` | Admin endpoints |
| `src/app/presentation/http/auth/fastapi_openapi_markers.py` | Auth markers |
| `src/app/presentation/http/schemas/` | Request/response schemas |

---

## API Statistics

| Metric | Value |
|--------|-------|
| **Total Endpoints** | 200+ |
| **Public Endpoints** | ~15 |
| **User Endpoints** | ~100 |
| **Admin Endpoints** | ~110 |
| **WebSocket Endpoints** | 3 |
| **API Modules** | 30+ |
| **Supported Languages** | 4 (en, es, pt, zh) |
| **Rate Limit (User)** | 1000/hour |
| **Rate Limit (Guest)** | 20/hour |

---

**Last Updated**: January 2, 2026
