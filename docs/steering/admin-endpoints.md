# Admin Endpoints (Operaciones Internas) - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El sistema de endpoints Admin proporciona acceso administrativo completo para operaciones internas:

1. **User Management**: Gestión de usuarios, roles, activación/desactivación
2. **Wallet Management**: Administración de wallets, detalles, actualizaciones
3. **LLM Orchestration**: Configuración y monitoreo del sistema LLM
4. **Agent Management**: Configuración de agentes AI
5. **Security Dashboard**: Monitoreo de seguridad, escaneos OWASP, vulnerabilidades
6. **Retry System**: Control de circuit breakers y servicios
7. **Transactions**: Vista administrativa de transacciones
8. **Projects**: Gestión de proyectos, knowledge base, assignments
9. **Chat Analytics**: Dashboard de métricas de chat
10. **Metrics & Stats**: Estadísticas del sistema
11. **Distillation**: Gestión del sistema de distilling
12. **Policies**: Gestión de políticas Privy
13. **Telemetry**: Control de feature flags y observabilidad

**Todos los endpoints requieren autenticación Bearer token y rol ADMIN.**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           ADMIN API ARCHITECTURE                                        │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────────┐
                    │         Admin Router Aggregator          │
                    │      /api/v1/admin/* (prefix)            │
                    └──────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  User Mgmt      │      │  LLM Mgmt       │      │  Security       │
│  /admin/users   │      │  /admin/llm     │      │  /admin/security│
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│• List users     │      │• Dashboard      │      │• Dashboard      │
│• Grant admin    │      │• Providers      │      │• Scans          │
│• Revoke admin   │      │• Models         │      │• Trends         │
│• Activate       │      │• Rankings       │      │• Posture        │
│• Deactivate     │      │• Telemetry      │      │• Attacks        │
│• Change pwd     │      │• Budgets        │      │• Approvals      │
└─────────────────┘      │• Circuit break  │      │• PII protection │
                          └─────────────────┘      └─────────────────┘
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Wallet Mgmt    │      │  Retry System    │      │  Transactions   │
│  /admin/wallets │      │  /admin/retry    │      │  /admin/tx      │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│• List wallets   │      │• List services   │      │• List by wallet │
│• Get details    │      │• Service status  │      │• List by user   │
│• Update wallet  │      │• Enable/disable  │      │• Filter by chain│
└─────────────────┘      │• Circuit status  │      │• Filter by type │
                          │• Reset breaker   │      │• Filter by status│
                          │• Service metrics │      └─────────────────┘
                          └─────────────────┘
         │                            │
         ▼                            ▼
┌─────────────────┐      ┌─────────────────┐
│  Projects       │      │  Chat Analytics │
│  /admin/projects│      │  /admin/chat    │
├─────────────────┤      ├─────────────────┤
│• CRUD projects  │      │• Dashboard      │
│• Knowledge docs │      │• Agent perf     │
│• Assignment rules│     │• Cache efficiency│
│• User assignments│     │• Cost tracking  │
└─────────────────┘      │• Error monitoring│
                          │• Active users   │
                          │• Conversations  │
                          │• Export data    │
                          └─────────────────┘
```

---

## 1. User Management

**Base Path**: `/api/v1/admin/users`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | List users (pagination, sorting, search) | ✅ Admin |
| `PATCH` | `/{email}/grant-admin` | Grant admin role to user | ✅ Admin |
| `PATCH` | `/{email}/revoke-admin` | Revoke admin role (super admin only) | ✅ Super Admin |
| `PATCH` | `/{email}/activate` | Activate user account | ✅ Admin |
| `PATCH` | `/{email}/deactivate` | Deactivate user account | ✅ Admin |
| `PATCH` | `/{email}/password` | Change user password | ✅ Admin |

### List Users

**Endpoint**: `GET /api/v1/admin/users/`

**Query Parameters**:
- `limit`: Number of results (1-100, default: 20)
- `offset`: Pagination offset (default: 0)
- `sorting_field`: Field to sort by (default: "email")
- `sorting_order`: `ASC` or `DESC` (default: `ASC`)
- `search`: Search term (optional)

**Response**:
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "role": "USER",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

### Grant Admin

**Endpoint**: `PATCH /api/v1/admin/users/{email}/grant-admin`

**Description**: Grants admin role to a user. Super admin cannot be revoked.

**Response**: `204 No Content`

### Revoke Admin

**Endpoint**: `PATCH /api/v1/admin/users/{email}/revoke-admin`

**Description**: Revokes admin role (super admin only). Super admin cannot be revoked.

**Response**: `204 No Content`

### Activate/Deactivate User

**Endpoints**:
- `PATCH /api/v1/admin/users/{email}/activate`
- `PATCH /api/v1/admin/users/{email}/deactivate`

**Response**: `204 No Content`

### Change Password

**Endpoint**: `PATCH /api/v1/admin/users/{email}/password`

**Request Body**:
```json
{
  "new_password": "secure_password_123"
}
```

**Response**: `204 No Content`

---

## 2. Wallet Management

**Base Path**: `/api/v1/admin/wallets`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | List wallets (pagination, sorting, search) | ✅ Admin |
| `GET` | `/{privy_wallet_id}` | Get wallet details | ✅ Admin |
| `PATCH` | `/{privy_wallet_id}` | Update wallet configuration | ✅ Admin |

### List Wallets

**Endpoint**: `GET /api/v1/admin/wallets/`

**Query Parameters**:
- `limit`: Number of results (1-100, default: 50)
- `offset`: Pagination offset (default: 0)
- `sorting_field`: Field to sort by
- `sorting_order`: `ASC` or `DESC`
- `search`: Search by address or user email
- `provider`: Filter by provider (privy, imported, external)
- `chain`: Filter by chain (ethereum, base, etc.)

**Response**:
```json
{
  "wallets": [
    {
      "id": "uuid",
      "privy_wallet_id": "privy_wallet_123",
      "user_id": "uuid",
      "address": "0x...",
      "chain": "ethereum",
      "provider": "privy",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 500,
  "limit": 50,
  "offset": 0
}
```

### Get Wallet Details

**Endpoint**: `GET /api/v1/admin/wallets/{privy_wallet_id}`

**Response**:
```json
{
  "id": "uuid",
  "privy_wallet_id": "privy_wallet_123",
  "user_id": "uuid",
  "address": "0x...",
  "chain": "ethereum",
  "provider": "privy",
  "is_active": true,
  "metadata": {},
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### Update Wallet

**Endpoint**: `PATCH /api/v1/admin/wallets/{privy_wallet_id}`

**Request Body**:
```json
{
  "is_active": false,
  "metadata": {
    "notes": "Flagged for review"
  }
}
```

**Response**: Updated wallet object

---

## 3. LLM Orchestration Management

**Base Path**: `/api/v1/admin/llm`

### Sub-Routers

| Sub-Router | Path | Description |
|------------|------|-------------|
| Dashboard | `/admin/llm/dashboard` | Dashboard overview, WebSocket, export |
| Providers | `/admin/llm/providers` | Provider management |
| Models | `/admin/llm/models` | Model management |
| Rankings | `/admin/llm/rankings` | Model performance rankings |
| Telemetry | `/admin/llm/telemetry` | LLM telemetry metrics |
| Budgets | `/admin/llm/budgets` | Budget tracking and alerts |
| Circuit Breakers | `/admin/llm/circuit-breakers` | Circuit breaker management |

### Dashboard

**Endpoint**: `GET /api/v1/admin/llm/dashboard`

**Query Parameters**:
- `period`: Time period (`1h`, `24h`, `7d`, `30d`)

**Response**:
```json
{
  "system_health": {
    "status": "healthy",
    "providers_healthy": 3,
    "providers_degraded": 0,
    "providers_down": 0
  },
  "providers": [...],
  "top_models": [...],
  "metrics_summary": {...},
  "cost_summary": {...},
  "recent_requests": [...],
  "active_alerts": [...]
}
```

**WebSocket**: `WS /api/v1/admin/llm/dashboard/ws`

Real-time updates for:
- New requests
- Status changes
- Alerts
- Metric updates

**Export**: `POST /api/v1/admin/llm/dashboard/export`

**Request Body**:
```json
{
  "format": "csv",
  "data_type": "requests",
  "period": "30d",
  "filters": {
    "provider": "vertex_ai",
    "agent_type": "swap_agent"
  }
}
```

### Providers

**Endpoints**:
- `GET /api/v1/admin/llm/providers` - List all providers
- `GET /api/v1/admin/llm/providers/{provider_id}` - Get provider details
- `PATCH /api/v1/admin/llm/providers/{provider_id}` - Update provider
- `POST /api/v1/admin/llm/providers/{provider_id}/health-check` - Manual health check

**Provider Response**:
```json
{
  "id": "uuid",
  "name": "vertex_ai",
  "display_name": "Google Vertex AI",
  "priority": 1,
  "is_enabled": true,
  "health_status": "healthy",
  "last_health_check": "2025-01-01T10:00:00Z",
  "model_count": 3,
  "enabled_model_count": 3,
  "circuit_breaker_state": "closed"
}
```

### Models

**Endpoints**:
- `GET /api/v1/admin/llm/models` - List all models
- `GET /api/v1/admin/llm/models/{model_id}` - Get model details
- `PATCH /api/v1/admin/llm/models/{model_id}` - Update model
- `GET /api/v1/admin/llm/models/{model_id}/performance` - Get performance metrics

**Query Parameters** (List):
- `provider_id`: Filter by provider
- `is_enabled`: Filter by enabled status
- `tier`: Filter by tier (premium, standard, economy)

**Model Response**:
```json
{
  "id": "uuid",
  "provider_id": "uuid",
  "provider_name": "vertex_ai",
  "model_id": "gemini-1.5-pro",
  "display_name": "Gemini 1.5 Pro",
  "model_family": "gemini",
  "capabilities": ["chat", "code", "vision", "function_calling"],
  "context_window": 1000000,
  "cost_per_1k_input": "0.00125",
  "cost_per_1k_output": "0.005",
  "carousel_position": 1,
  "tier": "premium",
  "is_enabled": true,
  "circuit_breaker_state": "closed"
}
```

### Rankings

**Endpoint**: `GET /api/v1/admin/llm/rankings`

**Query Parameters**:
- `metric`: Sort by (`success_rate`, `avg_latency`, `cost_per_request`, `total_requests`)
- `period`: Time period (`24h`, `7d`, `30d`)
- `limit`: Number of results (default: 10)

**Response**: Model performance leaderboard

### Telemetry

**Endpoints**:
- `GET /api/v1/admin/llm/telemetry/metrics` - Get LLM telemetry metrics
- `GET /api/v1/admin/llm/telemetry/costs` - Get cost breakdown
- `GET /api/v1/admin/llm/telemetry/models` - Get model usage statistics
- `GET /api/v1/admin/llm/telemetry/alerts` - Get alerts
- `GET /api/v1/admin/llm/telemetry/providers` - Get provider summary
- `POST /api/v1/admin/llm/telemetry/reset` - Reset metrics

### Budgets

**Endpoints**:
- `GET /api/v1/admin/llm/budgets` - Get budget configuration
- `PUT /api/v1/admin/llm/budgets` - Update budget limits
- `GET /api/v1/admin/llm/budgets/alerts` - Get budget alerts

### Circuit Breakers

**Endpoints**:
- `GET /api/v1/admin/llm/circuit-breakers` - List circuit breaker statuses
- `POST /api/v1/admin/llm/circuit-breakers/{service}/reset` - Reset circuit breaker

---

## 4. Agent Management

**Base Path**: `/api/v1/admin/agents`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | List all agents with status | ✅ Admin |

**Response**:
```json
[
  {
    "type": "TRADING",
    "name": "Trading Agent",
    "description": "Analyzes market trends",
    "is_active": true
  }
]
```

---

## 5. Security Dashboard

**Base Path**: `/api/v1/admin/security`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/dashboard` | Get security dashboard summary | ✅ Admin |
| `GET` | `/scans/latest` | Get latest security scan | ✅ Admin |
| `GET` | `/scans/{scan_id}` | Get specific scan details | ✅ Admin |
| `GET` | `/scans` | Get scan history | ✅ Admin |
| `GET` | `/scans/{scan_id}/tools` | Get tool results for scan | ✅ Admin |
| `GET` | `/trends` | Get vulnerability trends | ✅ Admin |
| `GET` | `/health` | Security system health check | ✅ Admin |

### Security Dashboard Summary

**Endpoint**: `GET /api/v1/admin/security/dashboard`

**Response**:
```json
{
  "latest_scan": {
    "scan_id": "20251215_020000",
    "scan_date": "2025-12-15T02:00:00Z",
    "status": "completed",
    "tools_executed": ["helios", "llmexploiter", "nettacker"],
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 10,
      "info": 3,
      "total": 20
    }
  },
  "total_scans": 52,
  "active_tools": ["helios", "llmexploiter", "nettacker", "llm-security-auditor"],
  "overall_status": "warning"
}
```

### Vulnerability Trends

**Endpoint**: `GET /api/v1/admin/security/trends`

**Query Parameters**:
- `days`: Number of days to analyze (1-90, default: 30)

**Response**:
```json
{
  "dates": ["2025-12-01", "2025-12-02", ...],
  "critical": [0, 0, 1, 0, ...],
  "high": [5, 4, 3, 2, ...],
  "medium": [10, 9, 8, 7, ...],
  "low": [15, 14, 13, 12, ...]
}
```

### Security Tools

**5 OWASP Security Tools**:
1. **Helios** - XSS testing (150+ patterns)
2. **LLMExploiter** - LLM security (219 patterns)
3. **Nettacker** - Network scanning
4. **llm-security-auditor** - Multi-agent security
5. **OWASP AI Testing Guide** - Best practices

---

## 6. Retry System Management

**Base Path**: `/api/v1/admin/retry`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/services` | List all services with retry status | ✅ Admin |
| `GET` | `/services/{service_name}` | Get service status | ✅ Admin |
| `POST` | `/services/{service_name}/disable` | Disable service | ✅ Admin |
| `POST` | `/services/{service_name}/enable` | Enable service | ✅ Admin |
| `GET` | `/circuit-breakers` | Get circuit breaker statuses | ✅ Admin |
| `POST` | `/circuit-breakers/{service_name}/reset` | Reset circuit breaker | ✅ Admin |
| `GET` | `/metrics/{service_name}` | Get service metrics | ✅ Admin |

### List Services

**Endpoint**: `GET /api/v1/admin/retry/services`

**Response**:
```json
{
  "services": [
    {
      "service_name": "oneinch_api",
      "is_enabled": true,
      "is_manually_disabled": false,
      "circuit_breaker_state": "closed",
      "failure_count": 0,
      "success_count": 150,
      "last_failure": null,
      "last_success": "2025-01-01T10:00:00Z"
    }
  ]
}
```

### Disable/Enable Service

**Endpoints**:
- `POST /api/v1/admin/retry/services/{service_name}/disable`
- `POST /api/v1/admin/retry/services/{service_name}/enable`

**Request Body**:
```json
{
  "reason": "Maintenance window",
  "duration_minutes": 60
}
```

### Circuit Breaker Status

**Endpoint**: `GET /api/v1/admin/retry/circuit-breakers`

**Response**:
```json
[
  {
    "service_name": "oneinch_api",
    "state": "closed",
    "failure_count": 0,
    "success_count": 150,
    "last_state_change": "2025-01-01T00:00:00Z"
  }
]
```

### Reset Circuit Breaker

**Endpoint**: `POST /api/v1/admin/retry/circuit-breakers/{service_name}/reset`

**Request Body**:
```json
{
  "reason": "Manual reset after maintenance"
}
```

### Service Metrics

**Endpoint**: `GET /api/v1/admin/retry/metrics/{service_name}`

**Query Parameters**:
- `days`: Number of days to retrieve (1-90, default: 7)

**Response**:
```json
{
  "service_name": "oneinch_api",
  "total_attempts": 1000,
  "successful_attempts": 950,
  "failed_attempts": 50,
  "success_rate": 0.95,
  "avg_latency_ms": 250,
  "circuit_breaker_trips": 2,
  "manual_overrides": 0
}
```

---

## 7. Transactions Admin View

**Base Path**: `/api/v1/admin/transactions`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | List transactions (admin view) | ✅ Admin |

### List Transactions

**Endpoint**: `GET /api/v1/admin/transactions`

**Query Parameters**:
- `wallet_address`: Filter by wallet address (recommended)
- `user_id`: Filter by user ID (aggregates across wallets)
- `chain`: Filter by chain (ethereum, base, polygon, etc.)
- `status`: Filter by status (`pending`, `success`, `failed`)
- `tx_type`: Filter by type (`send`, `swap`, `approve`, `fund`, etc.)
- `limit`: Maximum results (1-100, default: 50)
- `offset`: Pagination offset (default: 0)

**Response**:
```json
{
  "wallet_address": "0x...",
  "user_id": 123,
  "transactions": [
    {
      "id": 1,
      "tx_hash": "0x...",
      "type": "SWAP",
      "chain": "ethereum",
      "status": "success",
      "to_address": "0x...",
      "asset_in": "ETH",
      "amount_in": "1.0",
      "asset_out": "USDC",
      "amount_out": "3000.0",
      "fee_usd": "5.50",
      "block_number": 18500000,
      "confirmed_at": "2025-01-01T10:00:00Z",
      "created_at": "2025-01-01T10:00:00Z",
      "explorer_url": "https://etherscan.io/tx/0x...",
      "gas_used": 150000,
      "gas_price": 30000000000,
      "is_incoming": false,
      "from_address": null
    }
  ],
  "total": 500,
  "limit": 50,
  "offset": 0
}
```

---

## 8. Projects Management

**Base Path**: `/api/v1/admin/projects`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/` | Create project | ✅ Admin |
| `GET` | `/` | List projects | ✅ Admin |
| `GET` | `/{project_id}` | Get project | ✅ Admin |
| `PATCH` | `/{project_id}` | Update project | ✅ Admin |
| `DELETE` | `/{project_id}` | Delete project | ✅ Admin |
| `POST` | `/{project_id}/activate` | Activate project | ✅ Admin |
| `POST` | `/{project_id}/knowledge/documents` | Create knowledge document | ✅ Admin |
| `GET` | `/{project_id}/knowledge/documents` | List knowledge documents | ✅ Admin |
| `POST` | `/{project_id}/assignment-rules` | Create assignment rule | ✅ Admin |
| `GET` | `/{project_id}/assignment-rules` | List assignment rules | ✅ Admin |
| `PATCH` | `/{project_id}/assignment-rules/{rule_id}` | Update assignment rule | ✅ Admin |
| `POST` | `/{project_id}/assignments` | Assign user to project | ✅ Admin |
| `GET` | `/{project_id}/assignments` | List project assignments | ✅ Admin |

### Create Project

**Endpoint**: `POST /api/v1/admin/projects`

**Request Body**:
```json
{
  "slug": "defi-yield-optimizer",
  "name": "DeFi Yield Optimizer",
  "description": "Optimize yield farming strategies",
  "system_prompt": "You are a DeFi yield optimizer...",
  "status": "active",
  "visibility": "public",
  "enabled_protocols": ["aave", "morpho", "compound"],
  "enabled_chains": ["ethereum", "base"],
  "enabled_tools": ["swap", "deposit", "withdraw"],
  "risk_config": {
    "max_risk_tolerance": 0.7,
    "max_capital_usd": 100000
  },
  "max_users": 1000,
  "is_featured": true
}
```

### Knowledge Documents

**Create Document**:
```json
{
  "title": "Aave V3 Lending Guide",
  "content": "Aave V3 is a decentralized lending protocol...",
  "doc_type": "guide",
  "source_url": "https://docs.aave.com",
  "source_type": "documentation",
  "tags": ["aave", "lending"],
  "priority": "high"
}
```

---

## 9. Chat Analytics Dashboard

**Base Path**: `/api/v1/admin/chat`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/dashboard` | Get dashboard summary | ✅ Admin |
| `GET` | `/dashboard/agents/performance` | Get agent performance | ✅ Admin |
| `GET` | `/dashboard/cache/efficiency` | Get cache efficiency | ✅ Admin |
| `GET` | `/dashboard/costs` | Get cost tracking | ✅ Admin |
| `GET` | `/dashboard/errors` | Get error monitoring | ✅ Admin |
| `GET` | `/dashboard/users/active` | Get active users | ✅ Admin |
| `GET` | `/dashboard/conversations/metrics` | Get conversation metrics | ✅ Admin |
| `GET` | `/dashboard/export` | Export dashboard data | ✅ Admin |

### Dashboard Summary

**Endpoint**: `GET /api/v1/admin/chat/dashboard`

**Query Parameters**:
- `date_from`: Start date (default: 30 days ago)
- `date_to`: End date (default: now)

**Response**:
```json
{
  "total_conversations": 1500,
  "total_messages": 10000,
  "active_users": 250,
  "agent_usage": {
    "trading": 500,
    "research": 300,
    "portfolio": 200
  },
  "cost_summary": {
    "total_cost_usd": 150.50,
    "cost_by_agent": {...}
  },
  "error_rate": 0.02,
  "cache_hit_rate": 0.85
}
```

### Agent Performance

**Endpoint**: `GET /api/v1/admin/chat/dashboard/agents/performance`

**Query Parameters**:
- `date_from`, `date_to`: Date range
- `agent_type`: Filter by agent
- `sort_by`: `invocations`, `success_rate`, `avg_response_time`, `total_cost`
- `limit`: Number of results (1-50, default: 10)

**Response**: Agent leaderboard with metrics

### Cost Tracking

**Endpoint**: `GET /api/v1/admin/chat/dashboard/costs`

**Query Parameters**:
- `date_from`, `date_to`: Date range
- `group_by`: `agent`, `model`, `day`, `user`

**Response**: Cost breakdown by dimension

### Export Data

**Endpoint**: `GET /api/v1/admin/chat/dashboard/export`

**Query Parameters**:
- `date_from`, `date_to`: Date range
- `format`: `json` or `csv`
- `include_sections`: Array of sections to include

---

## 10. Metrics & Statistics

**Base Path**: `/api/v1/admin/metrics` and `/api/v1/admin/stats`

### Metrics Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/overview` | Get metrics overview | ✅ Admin |
| `GET` | `/transactions/timeseries` | Transaction time series | ✅ Admin |
| `GET` | `/wallets/timeseries` | Wallet creation time series | ✅ Admin |
| `GET` | `/users/activity` | User activity time series | ✅ Admin |
| `GET` | `/wallets/distribution` | Wallet distribution by provider | ✅ Admin |
| `GET` | `/transactions/distribution` | Transaction distribution | ✅ Admin |

### Metrics Overview

**Endpoint**: `GET /api/v1/admin/metrics/overview`

**Response**:
```json
{
  "wallets": {
    "total_wallets": 5000,
    "active_wallets": 3500,
    "privy_wallets": 3000,
    "imported_wallets": 1500,
    "external_wallets": 500
  },
  "transactions": {
    "total_transactions": 50000,
    "pending_transactions": 50,
    "successful_transactions": 48000,
    "failed_transactions": 1950
  },
  "users": {
    "total_users": 2000,
    "total_users_with_transactions": 1500,
    "active_users_today": 250,
    "active_users_7d": 800,
    "active_users_30d": 1500
  },
  "generated_at": "2025-01-01T10:00:00Z"
}
```

### Time Series Data

**Endpoints**:
- `GET /api/v1/admin/metrics/transactions/timeseries`
- `GET /api/v1/admin/metrics/wallets/timeseries`
- `GET /api/v1/admin/metrics/users/activity`

**Query Parameters**:
- `from_date`: Start date (default: 30 days ago)
- `to_date`: End date (default: now)
- `group_by`: `day`, `week`, `month`
- `chain`: Filter by chain (transactions only)
- `tx_type`: Filter by transaction type (transactions only)

**Response**:
```json
{
  "data": [
    {"date": "2025-01-01", "value": 100},
    {"date": "2025-01-02", "value": 120}
  ],
  "from_date": "2025-01-01T00:00:00Z",
  "to_date": "2025-01-31T23:59:59Z",
  "group_by": "day",
  "total_count": 3100
}
```

### Distribution Data

**Endpoints**:
- `GET /api/v1/admin/metrics/wallets/distribution`
- `GET /api/v1/admin/metrics/transactions/distribution`

**Response**:
```json
{
  "by_provider": [
    {"name": "privy", "count": 3000, "percentage": 60.0},
    {"name": "imported", "count": 1500, "percentage": 30.0},
    {"name": "external", "count": 500, "percentage": 10.0}
  ],
  "total": 5000
}
```

### Stats Endpoint

**Endpoint**: `GET /api/v1/admin/stats/`

**Response**:
```json
{
  "active_conversations": 10,
  "total_messages": 150,
  "active_agents": 5,
  "agent_usage": [
    {"agent_type": "trading", "count": 50},
    {"agent_type": "research", "count": 30}
  ]
}
```

---

## 11. Distillation Management

**Base Path**: `/api/v1/admin/distillation`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/static-responses` | Create static response | ✅ Admin |
| `GET` | `/static-responses` | List static responses | ✅ Admin |
| `PATCH` | `/static-responses/{response_id}` | Update static response | ✅ Admin |
| `DELETE` | `/static-responses/{response_id}` | Delete static response | ✅ Admin |
| `GET` | `/config` | Get distillation config | ✅ Admin |
| `PATCH` | `/config` | Update distillation config | ✅ Admin |
| `POST` | `/cache/invalidate` | Invalidate cache | ✅ Admin |
| `GET` | `/cache/stats` | Get cache statistics | ✅ Admin |
| `GET` | `/telemetry/requests` | Get telemetry requests | ✅ Admin |
| `GET` | `/telemetry/summary` | Get telemetry summary | ✅ Admin |

### Static Responses

**Create Static Response**:
```json
{
  "intent": "price_query",
  "variant": "default",
  "response_template": "The price of {token} is ${price}",
  "template_variables": ["token", "price"],
  "data_source": "coingecko",
  "conditions": {"min_confidence": 0.9},
  "priority": 1,
  "is_active": true
}
```

### Configuration

**Get/Update Config**:
```json
{
  "enabled": true,
  "cache_enabled": true,
  "static_responses_enabled": true,
  "semantic_cache_enabled": true,
  "min_confidence_threshold": 0.85,
  "semantic_similarity_threshold": 0.9,
  "max_classification_latency_ms": 100
}
```

### Cache Management

**Invalidate Cache**:
```json
{
  "cache_type": "all",
  "filters": {
    "intent": "price_query"
  }
}
```

**Cache Types**: `exact`, `semantic`, `all`

### Distillation Validation

**Base Path**: `/api/v1/admin/distillation/validation`

**Endpoints**:
- `GET /metrics` - Get distillation metrics
- `GET /providers` - Get provider status
- `GET /config` - Get validation config
- `PATCH /config` - Update validation config
- `GET /health` - Health check

---

## 12. Policies Management

**Base Path**: `/api/v1/admin/policies`

### Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | List policies | ✅ Admin |
| `POST` | `/` | Create policy | ✅ Admin |
| `GET` | `/{policy_id}` | Get policy | ✅ Admin |
| `PATCH` | `/{policy_id}` | Update policy | ✅ Admin |
| `GET` | `/rules` | Get policy rules | ✅ Admin |

**Policies**: Privy authentication policies for wallet access control

---

## 13. Telemetry Feature Flags

**Base Path**: `/api/v1/telemetry/flags`

See [Feature Flags Documentation](./feature-flags.md) for complete details.

**Endpoints**:
- `GET /api/v1/telemetry/flags` - Get current flags
- `PUT /api/v1/telemetry/flags` - Update flags at runtime
- `POST /api/v1/telemetry/flags/disable-api/{api_name}` - Disable API telemetry
- `POST /api/v1/telemetry/flags/enable-api/{api_name}` - Enable API telemetry
- `POST /api/v1/telemetry/flags/save` - Persist to Redis
- `POST /api/v1/telemetry/flags/load` - Load from Redis
- `DELETE /api/v1/telemetry/flags/saved` - Delete from Redis

---

## Authentication & Authorization

### Bearer Token Authentication

**All admin endpoints require**:
```http
Authorization: Bearer <jwt_token>
```

### Role Requirements

| Endpoint Category | Required Role |
|-------------------|---------------|
| Most endpoints | `ADMIN` |
| Revoke admin | `SUPER_ADMIN` (cannot be revoked) |
| Security dashboard | `ADMIN` |
| LLM management | `ADMIN` |

### Error Responses

**401 Unauthorized**:
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden**:
```json
{
  "detail": "Insufficient permissions"
}
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Router Aggregator** | `presentation/http/controllers/admin/router.py` | Main admin router |
| **User Management** | `presentation/http/controllers/admin/user/router.py` | User endpoints |
| **Wallet Management** | `presentation/http/controllers/admin/wallet/router.py` | Wallet endpoints |
| **LLM Management** | `presentation/http/controllers/admin/llm/router.py` | LLM orchestration |
| **Security** | `presentation/http/controllers/admin/security_dashboard_router.py` | Security dashboard |
| **Retry System** | `presentation/http/controllers/admin/retry/router.py` | Retry management |
| **Transactions** | `presentation/http/controllers/admin/transactions_router.py` | Transaction admin view |
| **Projects** | `presentation/http/controllers/admin/projects_router.py` | Project management |
| **Chat Analytics** | `presentation/http/controllers/admin/chat_dashboard.py` | Chat dashboard |
| **Metrics** | `presentation/http/controllers/admin/metrics/router.py` | System metrics |
| **Stats** | `presentation/http/controllers/admin/stats/router.py` | System statistics |
| **Distillation** | `presentation/http/controllers/admin/distillation_router.py` | Distillation management |
| **Policies** | `presentation/http/controllers/admin/policies/router.py` | Policy management |
| **Agent** | `presentation/http/controllers/admin/agent/router.py` | Agent management |

---

## Endpoint Summary

| Category | Endpoint Count | Base Path |
|----------|----------------|-----------|
| **User Management** | 6 | `/api/v1/admin/users` |
| **Wallet Management** | 3 | `/api/v1/admin/wallets` |
| **LLM Orchestration** | 30+ | `/api/v1/admin/llm` |
| **Agent Management** | 1 | `/api/v1/admin/agents` |
| **Security Dashboard** | 7 | `/api/v1/admin/security` |
| **Retry System** | 7 | `/api/v1/admin/retry` |
| **Transactions** | 1 | `/api/v1/admin/transactions` |
| **Projects** | 13+ | `/api/v1/admin/projects` |
| **Chat Analytics** | 8 | `/api/v1/admin/chat` |
| **Metrics** | 6 | `/api/v1/admin/metrics` |
| **Stats** | 1 | `/api/v1/admin/stats` |
| **Distillation** | 10+ | `/api/v1/admin/distillation` |
| **Policies** | 5 | `/api/v1/admin/policies` |
| **Telemetry** | 9 | `/api/v1/telemetry` |
| **TOTAL** | **110+ endpoints** | |

---

## Best Practices

### 1. Use Pagination for Large Datasets

```bash
# Always use limit and offset for list endpoints
GET /api/v1/admin/users?limit=50&offset=0
```

### 2. Filter Results When Possible

```bash
# Use query parameters to filter results
GET /api/v1/admin/transactions?chain=ethereum&status=success&limit=100
```

### 3. Monitor Rate Limits

Admin endpoints may have rate limits. Check response headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### 4. Use WebSocket for Real-Time Updates

```javascript
// LLM Dashboard WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/admin/llm/dashboard/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update UI
};
```

### 5. Export Large Datasets

For large data exports, use the export endpoints:
```bash
POST /api/v1/admin/chat/dashboard/export
{
  "format": "csv",
  "data_type": "requests",
  "period": "30d"
}
```

---

## Security Considerations

1. **All endpoints require admin authentication** via Bearer token
2. **Super admin operations** (revoke admin) require `SUPER_ADMIN` role
3. **Audit logging** - All admin actions are logged (see [audit-logging.md](./audit-logging.md))
4. **Rate limiting** - Admin endpoints may have rate limits
5. **IP whitelisting** - Consider IP whitelisting for production admin access
6. **2FA** - Consider requiring 2FA for sensitive operations

---

**Last Updated**: January 2, 2026
