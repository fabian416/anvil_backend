# Frontend API Complete Reference

**Version:** 3.1  
**Last Updated:** December 9, 2025  
**Total Endpoints:** 290+  
**API Structure:** `/api/v1/user/*`, `/api/v1/admin/*`

---

## API Base URL

```
Production: https://api.anvil.defi/api/v1
Staging:    https://staging-api.anvil.defi/api/v1
Local:      http://localhost:8000/api/v1
```

---

## API Structure Overview

| Category | Base Path | Routes | Description |
|----------|-----------|--------|-------------|
| **User** | `/api/v1/user/` | 116 | All user-facing features |
| **Admin** | `/api/v1/admin/` | 119 | Admin & system management |
| **Public** | `/api/v1/` | 28 | Auth, account, payments |

---

## Authentication

All authenticated endpoints require the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

---

## Error Response Format

All errors follow the standardized format. See [ERROR_CODES_REFERENCE.md](./ERROR_CODES_REFERENCE.md) for complete codes.

```typescript
interface APIError {
  error: {
    code: string;           // e.g., "AUTH_001"
    message: string;        // English message
    i18n_key: string;       // Translation key
    details?: object;       // Additional context
    http_status: number;    // HTTP status code
  };
}
```

---

# 📱 USER ENDPOINTS (`/api/v1/user/`)

## 1. Chat & Conversations (`/api/v1/user/chat/`)

### Conversations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/user/chat/conversations` | Create conversation | ✅ |
| GET | `/user/chat/conversations` | List conversations | ✅ |
| GET | `/user/chat/conversations/{id}` | Get conversation | ✅ |
| DELETE | `/user/chat/conversations/{id}` | Delete conversation | ✅ |
| GET | `/user/chat/conversations/{id}/messages` | Get messages | ✅ |
| POST | `/user/chat/conversations/{id}/messages` | Send message | ✅ |

### Agent Squad

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/user/chat/agent-squad/messages` | Send to agent squad | ✅ |
| POST | `/user/chat/agent-squad/supervisor` | Multi-agent workflow | ✅ |
| GET | `/user/chat/agent-squad/agents` | List enabled agents | ✅ |

### GraphRAG Chat

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/user/chat/protocol-search` | Search protocols | ✅ |
| POST | `/user/chat/analyze-risk` | Analyze protocol risk | ✅ |
| POST | `/user/chat/similar-protocols` | Find similar protocols | ✅ |

---

## 2. DeFi Protocols (`/api/v1/user/defi/`)

### Aave V3 Lending (`/api/v1/user/defi/aave/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/defi/aave/markets` | Get all Aave V3 markets | ✅ |
| GET | `/user/defi/aave/markets/{asset}` | Get market details for asset | ✅ |
| GET | `/user/defi/aave/positions/{address}` | Get user lending position | ✅ |
| GET | `/user/defi/aave/positions/{address}/health` | Get health factor | ✅ |
| GET | `/user/defi/aave/positions/{address}/borrow-capacity/{asset}` | Get borrow capacity | ✅ |
| GET | `/user/defi/aave/stats` | Get protocol statistics | ✅ |
| GET | `/user/defi/aave/rates/{asset}` | Get supply/borrow rates | ✅ |
| POST | `/user/defi/aave/calculate/health-factor` | Calculate health factor | ✅ |

### Morpho Vaults (`/api/v1/user/defi/morpho/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/defi/morpho/vaults` | Get MetaMorpho vaults | ✅ |
| GET | `/user/defi/morpho/vaults/{address}` | Get vault details | ✅ |
| GET | `/user/defi/morpho/vaults/{address}/apy` | Get vault APY breakdown | ✅ |
| GET | `/user/defi/morpho/markets` | Get Morpho Blue markets | ✅ |
| GET | `/user/defi/morpho/positions/{address}` | Get user positions | ✅ |
| GET | `/user/defi/morpho/compare` | Compare yields | ✅ |

### Curve Finance (`/api/v1/user/defi/curve/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/defi/curve/pools` | Get liquidity pools | ✅ |
| GET | `/user/defi/curve/pools/{address}` | Get pool details | ✅ |
| GET | `/user/defi/curve/pools/{address}/price` | Get pool prices | ✅ |
| GET | `/user/defi/curve/gauges` | Get gauge data | ✅ |
| GET | `/user/defi/curve/positions/{address}` | Get user positions | ✅ |

### Hyperliquid Perpetuals (`/api/v1/user/defi/hyperliquid/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/defi/hyperliquid/markets` | Get perpetual markets | ✅ |
| GET | `/user/defi/hyperliquid/markets/{symbol}` | Get market details | ✅ |
| GET | `/user/defi/hyperliquid/positions/{address}` | Get user positions | ✅ |
| GET | `/user/defi/hyperliquid/funding/{symbol}` | Get funding rates | ✅ |
| GET | `/user/defi/hyperliquid/orderbook/{symbol}` | Get orderbook | ✅ |

### LayerZero Cross-Chain (`/api/v1/user/defi/layerzero/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/defi/layerzero/messages/{hash}` | Track message status | ✅ |
| GET | `/user/defi/layerzero/history/{address}` | Get message history | ✅ |
| GET | `/user/defi/layerzero/estimate-fees` | Estimate transfer fees | ✅ |
| GET | `/user/defi/layerzero/chains` | Get supported chains | ✅ |
| GET | `/user/defi/layerzero/stats` | Get protocol stats | ✅ |

### Axelar Bridge (`/api/v1/user/defi/axelar/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/defi/axelar/transfers/{hash}` | Track transfer status | ✅ |
| GET | `/user/defi/axelar/history/{address}` | Get transfer history | ✅ |
| GET | `/user/defi/axelar/estimate-fees` | Estimate bridge fees | ✅ |
| GET | `/user/defi/axelar/chains` | Get supported chains | ✅ |
| GET | `/user/defi/axelar/tokens` | Get supported tokens | ✅ |
| GET | `/user/defi/axelar/stats` | Get protocol stats | ✅ |

---

## 3. NFT Marketplaces (`/api/v1/user/nft/`)

### OpenSea (`/api/v1/user/nft/opensea/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/nft/opensea/collections` | Get collections | ✅ |
| GET | `/user/nft/opensea/collections/{slug}` | Get collection details | ✅ |
| GET | `/user/nft/opensea/collections/{slug}/floor` | Get floor price | ✅ |
| GET | `/user/nft/opensea/assets/{address}/{token_id}` | Get NFT details | ✅ |
| GET | `/user/nft/opensea/portfolio/{address}` | Get user NFTs | ✅ |
| GET | `/user/nft/opensea/trending` | Get trending collections | ✅ |

---

## 4. Wallet (`/api/v1/user/wallet/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/wallet/balance` | Get wallet balance | ✅ |
| GET | `/user/wallet/tokens` | List wallet tokens | ✅ |
| GET | `/user/wallet/transactions` | Transaction history | ✅ |
| POST | `/user/wallet/connect` | Connect wallet | ✅ |

---

## 5. Portfolio (`/api/v1/user/portfolio/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/portfolio` | Get portfolio overview | ✅ |
| GET | `/user/portfolio/risk` | Get risk metrics | ✅ |
| POST | `/user/portfolio/risk/simulate-cascade` | Simulate cascade | ✅ |
| GET | `/user/portfolio/performance` | Performance history | ✅ |

---

## 6. Markets (`/api/v1/user/markets/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/markets/protocols` | List protocols | ❌ |
| GET | `/user/markets/protocols/{id}` | Protocol details | ❌ |
| GET | `/user/markets/tokens` | List tokens | ❌ |
| GET | `/user/markets/yields` | Yield opportunities | ❌ |

---

## 7. Alerts (`/api/v1/user/alerts/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/alerts/risk` | Get risk alerts | ✅ |
| POST | `/user/alerts/risk` | Create risk alert | ✅ |
| PUT | `/user/alerts/risk/{id}` | Update alert | ✅ |
| DELETE | `/user/alerts/risk/{id}` | Delete alert | ✅ |
| POST | `/user/alerts/risk/{id}/acknowledge` | Acknowledge alert | ✅ |
| GET | `/user/alerts/subscription` | Get subscriptions | ✅ |
| POST | `/user/alerts/subscription` | Create subscription | ✅ |

---

## 6. Preferences (`/api/v1/user/preferences/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/preferences` | Get all preferences | ✅ |
| PUT | `/user/preferences/risk-tolerance` | Update risk tolerance | ✅ |
| PUT | `/user/preferences/chains` | Update chain preferences | ✅ |
| PUT | `/user/preferences/notifications` | Notification settings | ✅ |
| GET | `/user/preferences/saved-searches` | Get saved searches | ✅ |
| POST | `/user/preferences/saved-searches` | Save search | ✅ |
| DELETE | `/user/preferences/saved-searches/{id}` | Delete saved search | ✅ |

---

## 7. Dashboard (`/api/v1/user/dashboard/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/dashboard` | Get dashboard data | ✅ |
| GET | `/user/dashboard/insights` | AI-powered insights | ✅ |

---

## 8. Search (`/api/v1/user/search/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/user/search/semantic` | Semantic search | ✅ |
| POST | `/user/search/hybrid` | Hybrid search | ✅ |
| GET | `/user/search/history` | Search history | ✅ |
| GET | `/user/search/suggestions` | Search suggestions | ✅ |
| POST | `/user/search/contextual` | Contextual search | ✅ |
| POST | `/user/search/similar` | Find similar | ✅ |

---

## 9. Comparison (`/api/v1/user/comparison/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/user/comparison` | Compare protocols | ✅ |

---

## 10. Notifications (`/api/v1/user/notifications/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/notifications` | Get notifications | ✅ |
| PUT | `/user/notifications/{id}/read` | Mark as read | ✅ |
| DELETE | `/user/notifications/{id}` | Delete notification | ✅ |

---

## 11. Projects (`/api/v1/user/projects/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/projects` | List user projects | ✅ |
| GET | `/user/projects/{id}` | Get project details | ✅ |
| POST | `/user/projects/{id}/select` | Select project | ✅ |
| GET | `/user/projects/{id}/knowledge` | Get knowledge base | ✅ |
| POST | `/user/projects/{id}/knowledge` | Add to knowledge | ✅ |

---

## 12. Graph (`/api/v1/user/graph/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/graph/protocols` | Get protocol graph | ✅ |
| GET | `/user/graph/protocols/{id}` | Protocol graph details | ✅ |
| GET | `/user/graph/protocols/{id}/relationships` | Get relationships | ✅ |
| POST | `/user/graph/search/hybrid` | Hybrid graph search | ✅ |
| POST | `/user/graph/search/contextual` | Contextual search | ✅ |
| POST | `/user/graph/search/similar` | Find similar | ✅ |
| GET | `/user/graph/analytics/overview` | Graph overview | ✅ |
| POST | `/user/graph/analytics/embeddings/generate` | Generate embeddings | ✅ |
| POST | `/user/graph/analytics/validate` | Validate graph | ✅ |
| GET | `/user/graph/monitoring/cache-stats` | Cache statistics | ✅ |
| POST | `/user/graph/monitoring/cache/clear` | Clear cache | ✅ |

---

## 13. ML Predictions (`/api/v1/user/ml/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/ml/prediction/{protocol_id}` | Get prediction | ✅ |
| POST | `/user/ml/prediction/batch` | Batch predictions | ✅ |
| GET | `/user/ml/prediction/{protocol_id}/forecast` | Risk forecast | ✅ |
| GET | `/user/ml/prediction/{protocol_id}/anomalies` | Detect anomalies | ✅ |
| GET | `/user/ml/network/pagerank` | PageRank scores | ✅ |
| GET | `/user/ml/network/communities` | Detect communities | ✅ |
| GET | `/user/ml/network/centrality` | Centrality metrics | ✅ |
| POST | `/user/ml/network/contagion/{protocol_id}` | Simulate contagion | ✅ |

---

## 14. Metrics (`/api/v1/user/metrics/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/metrics/me` | Get user metrics | ✅ |
| GET | `/user/metrics/me/events` | Get user events | ✅ |
| POST | `/user/metrics/track` | Track event | ✅ |
| GET | `/user/metrics/event-types` | List event types | ✅ |

---

## 15. Hunter AI (`/api/v1/user/hunter/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/user/hunter/sentiment/analyze` | Analyze sentiment | ✅ |
| GET | `/user/hunter/sentiment/trending` | Trending tokens | ✅ |
| POST | `/user/hunter/patterns/detect` | Detect patterns | ✅ |
| POST | `/user/hunter/signals/generate` | Trading signals | ✅ |
| POST | `/user/hunter/price/predict` | Price prediction | ✅ |
| POST | `/user/hunter/risk/analyze` | Risk analysis | ✅ |

---

## 16. ULTRA Arbitrage (`/api/v1/user/ultra/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/user/ultra/arbitrage/opportunities` | Scan opportunities | ✅ |
| GET | `/user/ultra/arbitrage/dex-dex` | DEX-DEX arbitrage | ✅ |
| GET | `/user/ultra/arbitrage/cex-dex` | CEX-DEX arbitrage | ✅ |
| POST | `/user/ultra/arbitrage/simulate` | Simulate arbitrage | ✅ |
| POST | `/user/ultra/flash-loans/simulate` | Simulate flash loan | ✅ |
| GET | `/user/ultra/mev/protection` | MEV protection status | ✅ |
| POST | `/user/ultra/auto-executor/create` | Create executor | ✅ |
| GET | `/user/ultra/auto-executor/status` | Executor status | ✅ |

---

## 17. WebSocket (`/api/v1/user/ws/`)

| Endpoint | Description | Auth |
|----------|-------------|------|
| `ws://*/api/v1/user/ws/chat` | Real-time chat | ✅ |
| `ws://*/api/v1/user/ws/graph` | Graph updates | ✅ |
| `ws://*/api/v1/user/ws/stats` | Live stats | ✅ |

---

# 🔐 ADMIN ENDPOINTS (`/api/v1/admin/`)

## 1. User Management (`/api/v1/admin/users/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/users` | List all users | ✅ Admin |
| GET | `/admin/users/{id}` | Get user details | ✅ Admin |
| PATCH | `/admin/users/{email}/grant-admin` | Grant admin role | ✅ Super Admin |
| PATCH | `/admin/users/{email}/revoke-admin` | Revoke admin role | ✅ Super Admin |
| PATCH | `/admin/users/{email}/activate` | Activate user | ✅ Admin |
| PATCH | `/admin/users/{email}/deactivate` | Deactivate user | ✅ Admin |

---

## 2. LLM Orchestration (`/api/v1/admin/llm/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/llm/dashboard/stats` | LLM statistics | ✅ Admin |
| GET | `/admin/llm/providers` | List providers | ✅ Admin |
| PUT | `/admin/llm/providers/{id}/enable` | Enable provider | ✅ Admin |
| PUT | `/admin/llm/providers/{id}/disable` | Disable provider | ✅ Admin |
| GET | `/admin/llm/models` | List models | ✅ Admin |
| PUT | `/admin/llm/models/{id}/priority` | Set model priority | ✅ Admin |
| GET | `/admin/llm/rankings` | Get rankings | ✅ Admin |
| PUT | `/admin/llm/rankings` | Update rankings | ✅ Admin |
| GET | `/admin/llm/budgets` | Get budgets | ✅ Admin |
| PUT | `/admin/llm/budgets` | Update budgets | ✅ Admin |
| GET | `/admin/llm/circuit-breakers` | Circuit breaker status | ✅ Admin |
| POST | `/admin/llm/circuit-breakers/{id}/reset` | Reset circuit | ✅ Admin |
| GET | `/admin/llm/agent-config` | Agent configurations | ✅ Admin |
| PUT | `/admin/llm/agent-config/{agent}` | Update agent config | ✅ Admin |
| GET | `/admin/llm/telemetry/requests` | Request telemetry | ✅ Admin |

---

## 3. Agents (`/api/v1/admin/agents/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/agents` | List all agents | ✅ Admin |
| PUT | `/admin/agents/{id}/enable` | Enable agent | ✅ Admin |
| PUT | `/admin/agents/{id}/disable` | Disable agent | ✅ Admin |

---

## 4. Stats (`/api/v1/admin/stats/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/stats` | System statistics | ✅ Admin |

---

## 5. Retry System (`/api/v1/admin/retry/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/retry/services` | List services | ✅ Admin |
| GET | `/admin/retry/services/{name}` | Service status | ✅ Admin |
| POST | `/admin/retry/services/{name}/disable` | Disable service | ✅ Admin |
| POST | `/admin/retry/services/{name}/enable` | Enable service | ✅ Admin |
| GET | `/admin/retry/circuit-breakers` | Circuit status | ✅ Admin |
| POST | `/admin/retry/circuit-breakers/{name}/reset` | Reset circuit | ✅ Admin |
| GET | `/admin/retry/metrics/{name}` | Service metrics | ✅ Admin |

---

## 6. Distillation (`/api/v1/admin/distillation/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/distillation/config` | Get config | ✅ Admin |
| PUT | `/admin/distillation/config` | Update config | ✅ Admin |
| GET | `/admin/distillation/static-responses` | List responses | ✅ Admin |
| POST | `/admin/distillation/static-responses` | Create response | ✅ Admin |
| PUT | `/admin/distillation/static-responses/{id}` | Update response | ✅ Admin |
| DELETE | `/admin/distillation/static-responses/{id}` | Delete response | ✅ Admin |
| POST | `/admin/distillation/cache/invalidate` | Invalidate cache | ✅ Admin |
| GET | `/admin/distillation/cache/stats` | Cache statistics | ✅ Admin |
| GET | `/admin/distillation/telemetry/summary` | Telemetry summary | ✅ Admin |
| GET | `/admin/distillation/telemetry/requests` | Request telemetry | ✅ Admin |

---

## 7. Projects (`/api/v1/admin/projects/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/projects` | List all projects | ✅ Admin |
| POST | `/admin/projects` | Create project | ✅ Admin |
| GET | `/admin/projects/{id}` | Get project | ✅ Admin |
| PUT | `/admin/projects/{id}` | Update project | ✅ Admin |
| DELETE | `/admin/projects/{id}` | Delete project | ✅ Admin |
| GET | `/admin/projects/{id}/assignments` | Get assignments | ✅ Admin |
| POST | `/admin/projects/{id}/assignments` | Create assignment | ✅ Admin |
| PUT | `/admin/projects/{id}/assignments/{aid}` | Update assignment | ✅ Admin |
| DELETE | `/admin/projects/{id}/assignments/{aid}` | Delete assignment | ✅ Admin |

---

## 8. Telemetry (`/api/v1/admin/telemetry/`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/telemetry/metrics` | API metrics | ✅ Admin |
| GET | `/admin/telemetry/errors` | Error summary | ✅ Admin |
| GET | `/admin/telemetry/slow-calls` | Slow calls | ✅ Admin |
| GET | `/admin/telemetry/health` | Health status | ✅ Admin |
| POST | `/admin/telemetry/reset` | Reset metrics | ✅ Admin |
| GET | `/admin/telemetry/prometheus` | Prometheus format | ✅ Admin |
| GET | `/admin/telemetry/traces` | List traces | ✅ Admin |
| GET | `/admin/telemetry/traces/{id}` | Get trace | ✅ Admin |
| GET | `/admin/telemetry/slow-traces` | Slow traces | ✅ Admin |

### LLM Telemetry

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/telemetry/llm/metrics` | LLM metrics | ✅ Admin |
| GET | `/admin/telemetry/llm/costs` | Cost breakdown | ✅ Admin |
| GET | `/admin/telemetry/llm/models` | Model usage | ✅ Admin |
| GET | `/admin/telemetry/llm/alerts` | LLM alerts | ✅ Admin |
| GET | `/admin/telemetry/llm/providers` | Provider stats | ✅ Admin |
| POST | `/admin/telemetry/llm/reset` | Reset LLM metrics | ✅ Admin |

### Database Telemetry

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/telemetry/db/metrics` | DB metrics | ✅ Admin |
| GET | `/admin/telemetry/db/slow-queries` | Slow queries | ✅ Admin |
| GET | `/admin/telemetry/db/patterns` | Query patterns | ✅ Admin |
| GET | `/admin/telemetry/db/pool` | Connection pool | ✅ Admin |
| GET | `/admin/telemetry/db/tables/{table}` | Table metrics | ✅ Admin |
| GET | `/admin/telemetry/db/errors` | DB errors | ✅ Admin |
| GET | `/admin/telemetry/db/summary` | DB summary | ✅ Admin |
| POST | `/admin/telemetry/db/reset` | Reset DB metrics | ✅ Admin |

### Feature Flags

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/telemetry/flags` | Get feature flags | ✅ Admin |
| PUT | `/admin/telemetry/flags` | Update flags | ✅ Admin |
| POST | `/admin/telemetry/flags/save` | Save to Redis | ✅ Admin |
| POST | `/admin/telemetry/flags/load` | Load from Redis | ✅ Admin |
| DELETE | `/admin/telemetry/flags/saved` | Delete saved | ✅ Admin |
| POST | `/admin/telemetry/flags/disable-api/{name}` | Disable API | ✅ Admin |
| POST | `/admin/telemetry/flags/enable-api/{name}` | Enable API | ✅ Admin |
| POST | `/admin/telemetry/flags/disable-llm/{provider}` | Disable LLM | ✅ Admin |
| POST | `/admin/telemetry/flags/enable-llm/{provider}` | Enable LLM | ✅ Admin |

---

# 🌐 PUBLIC ENDPOINTS (`/api/v1/`)

## Account & Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/account/signup` | Register new user | ❌ |
| POST | `/account/login` | User login | ❌ |
| POST | `/account/logout` | User logout | ✅ |
| GET | `/account/me` | Get current user | ✅ |
| PUT | `/account/me` | Update profile | ✅ |
| PUT | `/account/change-password` | Change password | ✅ |
| POST | `/account/forgot-password` | Request reset | ❌ |
| POST | `/account/reset-password` | Confirm reset | ❌ |
| POST | `/account/refresh-token` | Refresh JWT | ✅ |
| PUT | `/account/email/verify` | Verify email | ✅ |
| POST | `/account/email/verify/send` | Send verification | ✅ |
| POST | `/account/privy-login` | Privy Web3 login | ❌ |

## Auth (Admin Role Management)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/upgrade-to-admin` | Upgrade to admin | ✅ Super Admin |
| POST | `/auth/change-role` | Change user role | ✅ Super Admin |

## Subscription & Payments

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/subscription` | List subscriptions | ✅ |
| POST | `/subscription/{id}/subscribe` | Subscribe | ✅ |
| POST | `/subscription/{id}/cancel` | Cancel | ✅ |
| POST | `/subscription/init` | Initialize plans | ✅ Admin |
| POST | `/subscription/success` | Success callback | ✅ |
| POST | `/subscription/cancel` | Cancel callback | ✅ |
| GET | `/payments/user` | Get payments | ✅ |
| POST | `/payments/transaction` | Process payment | ✅ |

## Atlas (Geographic)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/atlas/countries/search` | Search countries | ❌ |
| POST | `/atlas/countries/init` | Initialize countries | ✅ Admin |
| GET | `/atlas/states/{country_id}` | Get states | ❌ |
| GET | `/atlas/cities/search` | Search cities | ❌ |
| POST | `/atlas/cities/init` | Initialize cities | ✅ Admin |

---

## Request/Response Examples

### User Chat - Send Message

```typescript
// POST /api/v1/user/chat/agent-squad/messages
// Auth: Bearer Token Required

// Request
interface SendAgentMessageRequest {
  message: string;          // Required: Message content (1-10000 chars)
  conversation_id?: string; // Optional: Existing conversation UUID
  agent_type?: string;      // Optional: "research" | "trading" | "risk" | "yield"
  context?: {               // Optional: Additional context
    protocols?: string[];
    chains?: string[];
    risk_tolerance?: "low" | "medium" | "high";
  };
}

// Response (200 OK)
interface SendAgentMessageResponse {
  user_message_id: string;
  agent_message_id: string;
  conversation_id: string;
  agent_type: string;
  content: string;
  tools_used: string[];
  latency_ms: number;
  tokens_used: number;
  action_suggestions?: {
    context_message: string;
    primary_suggestion: ActionSuggestion;
    suggestions: ActionSuggestion[];
  };
}

// Error Responses
// 400 - CHAT_003: Message cannot be empty
// 401 - AUTH_004: Authentication required
// 404 - CHAT_001: Conversation not found
// 422 - CHAT_005: Agent unavailable
// 429 - CHAT_007: Rate limit exceeded
// 500 - CHAT_008: Agent processing error
```

### Admin Telemetry - Get Metrics

```typescript
// GET /api/v1/admin/telemetry/metrics?api=coingecko
// Auth: Bearer Token Required (Admin)

// Query Parameters
interface TelemetryMetricsQuery {
  api?: string;      // Optional: Filter by API name
  hours?: number;    // Optional: Time range (default: 24)
}

// Response (200 OK)
interface TelemetryMetricsResponse {
  timestamp: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  cache_hits: number;
  cache_misses: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  error_rate: number;
  apis: Record<string, APIMetrics>;
}

// Error Responses
// 401 - AUTH_004: Authentication required
// 403 - ADM_001: Admin access required
// 400 - TEL_002: Invalid time range
// 503 - TEL_003: Telemetry service unavailable
```

---

## Migration Guide (Old → New URLs)

| Old URL | New URL |
|---------|---------|
| `/chat/conversations` | `/user/chat/conversations` |
| `/wallet/balance` | `/user/wallet/balance` |
| `/portfolio/risk` | `/user/portfolio/risk` |
| `/markets/protocols` | `/user/markets/protocols` |
| `/graph/search/hybrid` | `/user/graph/search/hybrid` |
| `/ml/prediction/{id}` | `/user/ml/prediction/{id}` |
| `/metrics/track` | `/user/metrics/track` |
| `/telemetry/metrics` | `/admin/telemetry/metrics` |
| `/admin/users` | `/admin/users` (unchanged) |
| `/admin/llm/*` | `/admin/llm/*` (unchanged) |

---

## Related Documents

- [ERROR_CODES_REFERENCE.md](./ERROR_CODES_REFERENCE.md) - Complete error codes with i18n
- [MASTER_API_INDEX.md](./MASTER_API_INDEX.md) - Documentation index
- [WEBSOCKET_INTEGRATION_GUIDE.md](./WEBSOCKET_INTEGRATION_GUIDE.md) - WebSocket guide
- [user-modules/](./user-modules/) - Detailed user endpoint docs
- [admin-modules/](./admin-modules/) - Detailed admin endpoint docs

---

**Document Version:** 3.0  
**Total Endpoints:** 262  
**Last Updated:** December 6, 2025
