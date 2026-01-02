# API Documentation

**Version**: 1.0.0  
**Base URL**: `http://localhost:8000/api/v1`  
**Documentation**: Interactive docs at `/docs` (Swagger UI)

---

## 📚 Quick Navigation

- **[API Reference](reference/README.md)** - Complete API reference
- **[Endpoints by Category](endpoints/README.md)** - Endpoints organized by feature
- **[Authentication](authentication.md)** - Authentication and authorization
- **[Error Handling](error-handling.md)** - Error responses and codes
- **[Examples](examples/README.md)** - API usage examples

---

## 🎯 API Overview

### Base URL

```
http://localhost:8000/api/v1
```

### API Structure

All endpoints follow the pattern:
```
/api/v1/{user-type}/{feature}/{endpoint}
```

**User Types**:
- `user` - Authenticated user endpoints
- `admin` - Admin-only endpoints
- `guest` - Public endpoints (no authentication)

**Examples**:
- `/api/v1/user/chat/conversations` - User chat endpoints
- `/api/v1/admin/users` - Admin user management
- `/api/v1/guest/health` - Public health check

---

## 🔐 Authentication

### Bearer Token

Most endpoints require authentication via Bearer token:

```http
Authorization: Bearer <jwt_token>
```

### Getting a Token

```http
POST /api/v1/account/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

See **[Authentication Guide](authentication.md)** for details.

---

## 🚀 What's New: Unified Chat Routing (Phase 8)

**Game Changer**: The chat endpoint `/api/v1/user/chat/conversations/{id}/messages` now features **intelligent intent-based routing**!

✨ **One endpoint handles everything**:
- Protocol search queries → GraphRAG Search
- Risk assessment → GraphRAG Risk Analysis
- Finding alternatives → GraphRAG Similar Protocols
- Specialist tasks → Agent Squad (18 AI agents)
- Complex workflows → Supervisor (multi-agent coordination)
- General chat → Traditional conversation agent

**Benefits**:
- 🎯 No need to choose which endpoint to use
- 🤖 AI-powered intent detection (LLM + keyword fallback)
- 💰 Cost optimized (routes to cheapest appropriate handler)
- 📊 Transparent routing metadata in responses
- ↩️ Backward compatible with feature flags

**See**: [Chat Endpoints Explained](../CHAT_ENDPOINTS_EXPLAINED.md#0-unified-routing-system-new) for full documentation.

---

## 📋 Endpoint Categories

### User Endpoints (`/api/v1/user/`)

| Category | Endpoints | Documentation |
|----------|-----------|---------------|
| **Chat** | `/user/chat/*` | [Chat API](endpoints/chat.md) ⭐ **NEW: Unified Routing** |
| **Portfolio** | `/user/portfolio/*` | [Portfolio API](endpoints/portfolio.md) |
| **Transactions** | `/user/transactions/*` | [Transactions API](endpoints/transactions.md) |
| **Graph** | `/user/graph/*` | [Graph API](endpoints/graph.md) |
| **ML** | `/user/ml/*` | [ML API](endpoints/ml.md) |
| **Alerts** | `/user/alerts/*` | [Alerts API](endpoints/alerts.md) |
| **Dashboard** | `/user/dashboard/*` | [Dashboard API](endpoints/dashboard.md) |
| **Markets** | `/user/markets/*` | [Markets API](endpoints/markets.md) |
| **Hunter** | `/user/hunter/*` | [Hunter API](endpoints/hunter.md) |
| **ULTRA** | `/user/ultra/*` | [ULTRA API](endpoints/ultra.md) |
| **Bitcoin** | `/user/bitcoin/*` | [Bitcoin API](endpoints/bitcoin.md) |
| **Projects** | `/user/projects/*` | [Projects API](endpoints/projects.md) |
| **Search** | `/user/search/*` | [Search API](endpoints/search.md) |
| **Preferences** | `/user/preferences/*` | [Preferences API](endpoints/preferences.md) |
| **Atlas** | `/user/atlas/*` | [Atlas API](endpoints/atlas.md) |

### Admin Endpoints (`/api/v1/admin/`)

| Category | Endpoints | Documentation |
|----------|-----------|---------------|
| **Users** | `/admin/users/*` | [Admin Users API](endpoints/admin-users.md) |
| **Metrics** | `/admin/metrics/*` | [Admin Metrics API](endpoints/admin-metrics.md) |
| **System** | `/admin/system/*` | [Admin System API](endpoints/admin-system.md) |

### Public Endpoints (`/api/v1/guest/` and `/api/v1/public/`)

| Endpoint | Documentation |
|----------|---------------|
| `/guest/health` | Health check |
| `/guest/chat` | **Guest Chat** ⭐ NEW - AI chat for unauthenticated users |
| `/public/chat/shortcuts` | **Chat Shortcuts** - Localized command hints |
| `/account/signup` | User registration |
| `/account/login` | User login |

### Guest Chat System ⭐ NEW

The Guest Chat allows unauthenticated users to experience Anvil's AI capabilities:

```http
POST /api/v1/guest/chat
{
  "content": "What is the sentiment for ETH?",
  "language": "en"
}
```

**Features**:
- Real Hunter AI data (sentiment, predictions, signals)
- Real ULTRA data (arbitrage, flash loans, MEV)
- Rate limited: 20 messages/hour
- Multi-language: en, es, pt, zh
- IP-based session tracking

See **[Guest Chat System](../GUEST_CHAT_SYSTEM.md)** for full documentation.

---

## 📖 Complete API Reference

See **[API Reference](reference/README.md)** for complete endpoint documentation including:

- Request/response schemas
- Authentication requirements
- Error responses
- Rate limiting
- Examples

---

## 🔍 Interactive Documentation

### Swagger UI

Visit `http://localhost:8000/docs` for interactive API documentation:

- Browse all endpoints
- Test endpoints directly
- View request/response schemas
- See authentication requirements

### ReDoc

Visit `http://localhost:8000/redoc` for alternative documentation format.

---

## 📝 API Standards

### Request Format

- **Content-Type**: `application/json`
- **Authentication**: Bearer token in `Authorization` header
- **Encoding**: UTF-8

### Response Format

- **Content-Type**: `application/json`
- **Encoding**: UTF-8
- **Status Codes**: Standard HTTP status codes

### Error Format

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "status_code": 400
}
```

See **[Error Handling](error-handling.md)** for details.

---

## 🚀 Quick Start

### 1. Get Authentication Token

```bash
curl -X POST http://localhost:8000/api/v1/account/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### 2. Make Authenticated Request

```bash
curl -X GET http://localhost:8000/api/v1/user/chat/conversations \
  -H "Authorization: Bearer <token>"
```

### 3. Explore Interactive Docs

Visit `http://localhost:8000/docs` for full API exploration.

---

## 📚 Related Documentation

- **[Authentication Guide](authentication.md)** - Authentication details
- **[Error Handling](error-handling.md)** - Error responses
- **[API Examples](examples/README.md)** - Usage examples
- **[Frontend Integration](../frontend/README.md)** - Frontend integration guide

---

---

## 🆕 Recent Updates

### January 2025

- **Guest Chat System**: AI chat for unauthenticated users with real Hunter AI/ULTRA data
- **Chat Execution Endpoint**: Execute swap, deposit, withdraw actions via chat
- **Chat Shortcuts**: Localized command hints in 5 languages
- **Hunter AI Real Data**: CoinGecko prices, RSS news sentiment (free APIs)
- **Multi-Language Support**: en, es, pt, zh for all chat endpoints
- **User IP Tracking**: Track registration and login IPs

---

**Last Updated**: January 2, 2025
