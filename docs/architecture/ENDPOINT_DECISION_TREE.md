# ENDPOINT DECISION TREE
**Quick Reference Guide for Anvil Backend API**

---

## CHAT ENDPOINTS - Which One Should I Use?

```
START: I want to implement chat functionality
│
├─► Are you building a NEW integration? (After 2026-01-22)
│   │
│   ├─► YES → Use UNIVERSAL ENDPOINT
│   │         📍 POST /api/v1/chat
│   │         ✅ Auto-detects guest vs authenticated
│   │         ✅ Single endpoint for all use cases
│   │         ✅ Best developer experience
│   │
│   └─► NO → Continue to existing system...
│
├─► Do you need to support GUEST users (no login)?
│   │
│   ├─► YES → Use GUEST ENDPOINT
│   │         📍 POST /api/v1/guest/chat
│   │         ✅ IP-based tracking
│   │         ✅ Demo mode for restricted features
│   │         ⚠️  Rate limit: 20 msg/hr
│   │
│   └─► NO → Continue...
│
├─► Is the user AUTHENTICATED? (Has JWT token)
│   │
│   ├─► YES → Use CONVERSATIONS ENDPOINT
│   │         📍 POST /api/v1/conversations/{id}/messages
│   │         ✅ Full feature access
│   │         ✅ Persistent conversation history
│   │         ✅ Multi-language support
│   │         ⚠️  Rate limit: 1000 msg/hr
│   │
│   └─► NO → Go back to "GUEST" option above
│
└─► Are you maintaining a LEGACY integration? (Before 2026-01-22)
    │
    ├─► YES → MIGRATE IMMEDIATELY! ⚠️ 
    │         📍 OLD: POST /api/v1/user/chat/conversations/{id}/messages
    │         📍 NEW: POST /api/v1/conversations/{id}/messages
    │         ⏰ Sunset: 2026-06-01
    │         📚 Migration Guide: /docs/DEPRECATION_PLAN.md
    │
    └─► NO → You're all set! Use the recommended endpoints above.
```

---

## FEATURE ENDPOINTS - Quick Reference

### HUNTER AI (Market Intelligence)
**Do you need market data?**
```
Sentiment Analysis    → GET /api/v1/user/hunter/sentiment/{token}
Price Predictions     → GET /api/v1/user/hunter/predictions/{token}
Trading Signals       → GET /api/v1/user/hunter/signals/{token}
Risk Analysis         → GET /api/v1/user/hunter/risk/{token}
Portfolio Optimizer   → POST /api/v1/user/hunter/portfolio/optimize
Pattern Recognition   → GET /api/v1/user/hunter/patterns/{token}
```
**Authentication:** Required (JWT)

### ULTRA (DeFi Automation)
**Do you need DeFi automation?**
```
Arbitrage Discovery   → POST /api/v1/user/ultra/arbitrage/discover
Flash Loan Rates      → GET /api/v1/user/ultra/flash-loans/rates
MEV Protection        → POST /api/v1/user/ultra/mev/analyze
Auto-Executor         → POST /api/v1/user/ultra/auto-executor/create
```
**Authentication:** Required (JWT)

### GraphRAG (Protocol Intelligence)
**Do you need protocol search/analysis?**
```
Hybrid Search         → POST /api/v1/user/graph/search
Protocol Analytics    → GET /api/v1/user/graph/analytics/protocols
System Health         → GET /api/v1/user/graph/monitoring/health
Graph Visualization   → GET /api/v1/user/graph/visualization/protocols/{id}
```
**Authentication:** Required (JWT)

### DeFi Protocols
**Do you need to interact with DeFi protocols?**
```
Aave V3     → /api/v1/user/defi/aave/*
Morpho      → /api/v1/user/defi/morpho/*
Curve       → /api/v1/user/defi/curve/*
Hyperliquid → /api/v1/user/defi/hyperliquid/*
LayerZero   → /api/v1/user/defi/layerzero/*
Axelar      → /api/v1/user/defi/axelar/*
```
**Authentication:** Required (JWT)

---

## AUTHENTICATION - Flow Decision

```
START: User needs to authenticate
│
├─► NEW USER?
│   │
│   ├─► YES → POST /api/v1/account/signup
│   │         Returns: JWT access token + refresh token
│   │
│   └─► NO → Continue...
│
├─► EXISTING USER?
│   │
│   ├─► YES → POST /api/v1/account/login
│   │         Returns: JWT access token + refresh token
│   │
│   └─► NO → Continue...
│
├─► TOKEN EXPIRED?
│   │
│   ├─► YES → POST /api/v1/account/refresh-token
│   │         Body: { "refresh_token": "..." }
│   │         Returns: New access token
│   │
│   └─► NO → Continue...
│
└─► NEED USER INFO?
    │
    └─► YES → GET /api/v1/account/me
              Headers: Authorization: Bearer {access_token}
              Returns: User profile
```

---

## ADMIN ENDPOINTS - Access Control

```
START: Need admin functionality
│
├─► Are you an ADMIN? (role = "admin")
│   │
│   ├─► YES → Proceed to admin endpoints
│   │         📍 Base: /api/v1/admin/*
│   │
│   └─► NO → ⛔ 403 Forbidden
│              Request admin role upgrade via support
│
└─► Admin Categories:
    │
    ├─► User Management      → /api/v1/admin/users/*
    ├─► LLM Orchestration    → /api/v1/admin/llm/*
    ├─► Agent Squad          → /api/v1/admin/agents/*
    ├─► System Stats         → /api/v1/admin/stats/*
    ├─► Security Dashboard   → /api/v1/admin/security/*
    ├─► Chat Analytics       → /api/v1/admin/chat/*
    ├─► Transactions         → /api/v1/admin/transactions/*
    └─► More...              → See full list in main docs
```

---

## RATE LIMITING - What to Expect

| User Type | Endpoint | Rate Limit | Notes |
|-----------|----------|------------|-------|
| **Guest** | `/api/v1/guest/chat` | 20 msg/hr | IP-based tracking |
| **Guest** | `/api/v1/chat` | 800 msg/hr | Universal endpoint |
| **Authenticated** | `/api/v1/conversations/*` | 1000 msg/hr | JWT required |
| **Authenticated** | `/api/v1/chat` | 1000 msg/hr | Universal endpoint |
| **Premium** | All endpoints | 10,000 msg/hr | Subscription tier |
| **Admin** | `/api/v1/admin/*` | Unlimited | RBAC enforced |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1737504000
Retry-After: 3600  # seconds
```

---

## COMMON USE CASES

### Use Case 1: Guest Chat Demo
**Goal:** Let users try chat without signup

```bash
# Step 1: Send message (no auth)
POST /api/v1/chat
{
  "content": "What is Bitcoin?",
  "language": "en"
}

# Response includes:
# - message_id
# - content (answer)
# - intent ("GENERAL_CONVERSATION")
# - requires_registration (false)
```

### Use Case 2: Authenticated User Chat
**Goal:** Full-featured chat with history

```bash
# Step 1: Login
POST /api/v1/account/login
{
  "email": "user@example.com",
  "password": "***"
}
# Returns: { "access_token": "eyJ...", "refresh_token": "..." }

# Step 2: Create conversation
POST /api/v1/conversations
Authorization: Bearer eyJ...
{
  "title": "My Crypto Chat",
  "language": "en"
}
# Returns: { "id": "123e4567-e89b-12d3-a456-426614174000", ... }

# Step 3: Send messages
POST /api/v1/conversations/123e4567-e89b-12d3-a456-426614174000/messages
Authorization: Bearer eyJ...
{
  "content": "Show me ETH trading signals",
  "language": "en"
}
# Returns: { "user_message": {...}, "agent_message": {...}, "routing": {...} }
```

### Use Case 3: Hunter AI Market Analysis
**Goal:** Get real-time sentiment for a token

```bash
# Requires authentication
GET /api/v1/user/hunter/sentiment/BTC
Authorization: Bearer eyJ...

# Returns:
{
  "token": "BTC",
  "sentiment_score": 0.75,
  "sentiment_label": "bullish",
  "price": 45000.0,
  "sources": {
    "twitter": 0.72,
    "reddit": 0.68,
    "news": 0.85
  }
}
```

### Use Case 4: Execute DeFi Action (Swap)
**Goal:** Swap tokens via chat

```bash
# Step 1: Send swap request
POST /api/v1/conversations/123.../messages
Authorization: Bearer eyJ...
{
  "content": "Swap 100 USDC to ETH on Base",
  "language": "en"
}

# Response includes execute data:
{
  "execute": {
    "action_type": "swap",
    "provider": "privy_0x",
    "chain": "base",
    "from_token": "USDC",
    "to_token": "ETH",
    "amount": "100",
    "quote_amount": "0.0222",
    "exchange_rate": "0.000222",
    "expires_at": "2026-01-22T01:05:00Z"
  }
}

# Step 2: Execute the swap (via frontend SDK)
# Frontend calls Privy SDK with execute.data
```

---

## MIGRATION CHECKLIST

### Moving from Legacy Chat to New System
- [ ] Update base URL: `/user/chat/*` → `/conversations/*`
- [ ] Remove `/user` prefix from all chat endpoints
- [ ] Update request/response schemas (new format)
- [ ] Test guest functionality (no JWT)
- [ ] Update error handling (new error codes)
- [ ] Monitor deprecation headers in responses
- [ ] Complete migration before 2026-06-01

### Adding Chat to a New App
- [ ] Start with universal endpoint: `POST /api/v1/chat`
- [ ] Implement JWT authentication (optional for guests)
- [ ] Handle rate limiting (check response headers)
- [ ] Support multi-language (en, es, pt, zh)
- [ ] Implement intent-specific UI (swap, lending, portfolio)
- [ ] Test guest mode (no JWT)
- [ ] Test authenticated mode (with JWT)

---

## TROUBLESHOOTING

### "Which endpoint should I use for chat?"
**Answer:** Use `POST /api/v1/chat` for all new integrations. It auto-detects guest vs authenticated.

### "Why is my rate limit so low?"
**Answer:** Guest users get 20 msg/hr, authenticated get 1000 msg/hr. Sign up for higher limits.

### "My legacy endpoint stopped working!"
**Answer:** Legacy endpoints (`/user/chat/*`) are deprecated and will be removed 2026-06-01. Migrate to `/conversations/*` immediately.

### "How do I execute a swap from chat?"
**Answer:** Send swap request via chat, get `execute` data in response, use Privy SDK to execute on frontend.

### "Can guests execute swaps?"
**Answer:** No. Guests see demo data only. Swaps, deposits, withdrawals require authentication and wallet connection (Privy).

### "What's the difference between /conversations and /chat?"
**Answer:**
- `/chat` - Universal endpoint (auto-detect guest vs auth)
- `/conversations` - Explicit conversation management (supports guests too)
Both work, but `/chat` is simpler for new apps.

---

## QUICK REFERENCE CARD

```
┌─────────────────────────────────────────────────────────┐
│ ANVIL BACKEND API - QUICK REFERENCE                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ CHAT (Guest + Auth):                                    │
│ • POST /api/v1/chat                    [RECOMMENDED]    │
│ • POST /api/v1/conversations/{id}/messages              │
│ • POST /api/v1/guest/chat              [Guest only]     │
│                                                          │
│ AUTHENTICATION:                                         │
│ • POST /api/v1/account/signup          [Register]       │
│ • POST /api/v1/account/login           [Login]          │
│ • POST /api/v1/account/refresh-token   [Refresh JWT]    │
│ • GET  /api/v1/account/me              [Profile]        │
│                                                          │
│ MARKET INTELLIGENCE:                                    │
│ • GET /api/v1/user/hunter/sentiment/{token}             │
│ • GET /api/v1/user/hunter/predictions/{token}           │
│ • GET /api/v1/user/hunter/signals/{token}               │
│                                                          │
│ DEFI AUTOMATION:                                        │
│ • POST /api/v1/user/ultra/arbitrage/discover            │
│ • GET  /api/v1/user/ultra/flash-loans/rates             │
│                                                          │
│ PROTOCOL SEARCH:                                        │
│ • POST /api/v1/user/graph/search                        │
│ • GET  /api/v1/user/graph/analytics/protocols           │
│                                                          │
│ ADMIN:                                                  │
│ • ALL /api/v1/admin/*                  [Admin role]     │
│                                                          │
│ RATE LIMITS:                                            │
│ • Guest: 20 msg/hr (demo), 800 msg/hr (universal)      │
│ • Auth: 1000 msg/hr                                     │
│ • Premium: 10,000 msg/hr                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

**Last Updated:** 2026-01-22  
**Maintained By:** @system-architect  
**Related Docs:** 
- [Full Endpoint Analysis](/docs/architecture/ENDPOINT_ARCHITECTURE_ANALYSIS.md)
- [Deprecation Plan](/docs/DEPRECATION_PLAN.md)
- [API Examples](/docs/api/examples/)
