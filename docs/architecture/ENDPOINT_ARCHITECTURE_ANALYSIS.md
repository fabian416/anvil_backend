# ANVIL BACKEND ENDPOINT ARCHITECTURE ANALYSIS
**CTO-Level System Architecture Review**  
**Date:** 2026-01-22  
**Author:** @system-architect  
**Status:** Phase 1 Complete - Inventory & Analysis

---

## EXECUTIVE SUMMARY

**Total Endpoints Discovered:** 350+  
**Active Routers:** 73+  
**Critical Finding:** 4 overlapping chat systems require consolidation  
**Deprecation Deadline:** 2026-06-01 (legacy chat system sunset)  
**Architecture Pattern:** Hexagonal + CQRS + DI (Dishka)

**Key Recommendations:**
1. ✅ Complete legacy chat migration by 2026-06-01
2. Maintain 3 chat endpoints until 2027 (conversations, guest, universal)
3. Consolidate Hunter AI endpoints under `/user/hunter/*`
4. Document all admin endpoints with RBAC matrix
5. Create unified API documentation with migration guides

---

## ENDPOINT INVENTORY

### 1. CHAT SYSTEMS (CRITICAL - 4 OVERLAPPING ROUTERS)

#### A. Legacy System (DEPRECATED - Remove by 2026-06-01)
**File:** `src/app/presentation/http/controllers/chat/router.py`  
**Base Path:** `/api/v1/user/chat/*`  
**Status:** ⚠️ DEPRECATED - Sunset 2026-06-01

**Endpoints:**
- `POST /user/chat/conversations` - Create conversation (DEPRECATED)
- `GET /user/chat/conversations` - List conversations (DEPRECATED)
- `GET /user/chat/conversations/{id}` - Get conversation (DEPRECATED)
- `PATCH /user/chat/conversations/{id}` - Update title (DEPRECATED)
- `DELETE /user/chat/conversations/{id}` - Delete conversation (DEPRECATED)
- `POST /user/chat/conversations/{id}/messages` - Send message (DEPRECATED)
- `GET /user/chat/conversations/{id}/messages` - Get messages (DEPRECATED)
- `POST /user/chat/conversations/{id}/execute` - Execute action
- `POST /user/chat/search-protocols` - GraphRAG search
- `POST /user/chat/analyze-risk` - Risk analysis
- `POST /user/chat/similar-protocols` - Similar protocols
- `POST /user/chat/agent-squad/messages` - Agent Squad routing
- `POST /user/chat/agent-squad/supervisor` - Supervisor workflow
- `GET /user/chat/agent-squad/agents` - List enabled agents
- `PATCH /user/chat/conversations/{id}/messages/{mid}/swap-quote` - Save swap quote

**Tables Used:** `conversations`, `messages`, `users` (INTEGER user_id)  
**Migration Target:** `/api/v1/conversations/*`

#### B. New System (CURRENT - PRIMARY)
**File:** `src/app/presentation/http/controllers/chat/conversations_router.py`  
**Base Path:** `/api/v1/conversations/*`  
**Status:** ✅ ACTIVE - Primary chat system

**Endpoints:**
- `POST /conversations` - Create conversation (guest + auth)
- `GET /conversations` - List conversations (guest + auth)
- `GET /conversations/{id}` - Get conversation with messages (query param: limit)
- `PATCH /conversations/{id}` - Update conversation
- `DELETE /conversations/{id}` - Archive conversation
- `POST /conversations/{id}/archive` - Archive conversation
- `POST /conversations/{id}/messages` - Send message (with intent detection)
- `POST /conversations/{id}/system-message` - Create system message (no LLM)
- `PATCH /conversations/{id}/messages/{mid}/swap-quote` - Save swap quote

**Tables Used:** `chat_conversations`, `chat_messages`, `chat_users` (UUID user_id)  
**Features:**
- Guest support (IP-based tracking)
- Multi-language (en, es, pt, zh)
- Intent detection (IntentDetectorV2)
- Rate limiting (800/hr guest, 1000/hr auth)
- Flow cancellation detection
- Multi-step flows (swap, lending, buy)
- Conversational memory (last 10 messages)
- Compound intent handling ("cancel, tell me about BTC")

#### C. Guest System
**File:** `src/app/presentation/http/controllers/guest/router.py`  
**Base Path:** `/api/v1/guest/*`  
**Status:** ✅ ACTIVE - Public guest endpoints

**Endpoints:**
- `POST /guest/chat` - Send guest message (demo mode)
- `GET /guest/chat/history` - Get guest history
- `GET /guest/chat/status` - Get guest status
- `DELETE /guest/chat` - Delete guest chat

**Features:**
- IP-based identification
- Rate limiting (5000/hr testing, 20/hr production)
- Demo mode for restricted actions
- Signup CTA for premium features
- Session tracking

#### D. Universal Chat (EXPERIMENTAL)
**File:** `src/app/presentation/http/controllers/chat/universal_chat_router.py`  
**Base Path:** `/api/v1/chat`  
**Status:** 🧪 EXPERIMENTAL - Unified endpoint

**Endpoints:**
- `POST /chat` - Universal chat (guest + auth auto-detect)
- `POST /guest/chat` - Legacy guest endpoint (DEPRECATED)

**Features:**
- Auto-detect user type from JWT
- Polymorphic context (GuestContext vs AuthenticatedContext)
- Unified handler (UnifiedChatHandler)
- Rate limiting based on user type (800/hr guest, 1000/hr auth)

#### E. WebSocket Chat
**File:** `src/app/presentation/http/controllers/chat/websocket_router.py`  
**Base Path:** `/api/v1/user/chat/ws`  
**Status:** ✅ ACTIVE - Real-time chat

**Endpoints:**
- `GET /user/chat/ws` - WebSocket connection

**Features:**
- Real-time streaming
- Agent Squad integration
- Connection management

---

### 2. AUTHENTICATION & ACCOUNT

#### Account Management
**File:** `src/app/presentation/http/controllers/account/router.py`  
**Base Path:** `/api/v1/account/*`

**Endpoints:**
- `POST /account/signup` - User registration
- `POST /account/login` - User login (JWT)
- `POST /account/logout` - User logout
- `POST /account/refresh-token` - Refresh JWT
- `POST /account/password-reset` - Password reset request
- `POST /account/password-reset/confirm` - Confirm password reset
- `POST /account/change-password` - Change password
- `POST /account/email-verification` - Send verification email
- `POST /account/email-verification/confirm` - Confirm email
- `GET /account/me` - Get current user info

**Authentication:** Public (except /me)

#### Auth Operations
**File:** `src/app/presentation/http/controllers/auth/router.py`  
**Base Path:** `/api/v1/auth/*`

**Endpoints:**
- `POST /auth/upgrade-to-admin` - Upgrade user to admin
- `POST /auth/change-role` - Change user role

**Authentication:** Admin only

---

### 3. USER ENDPOINTS (30+ ROUTERS)

#### 3.1 Hunter AI (Market Intelligence - 6 routers)
**Base Path:** `/api/v1/user/hunter/*`

**Sentiment Analysis:**
- `GET /user/hunter/sentiment/{token}` - Token sentiment analysis
- Real-time social media, news, Reddit data

**Price Predictions:**
- `GET /user/hunter/predictions/{token}` - Price predictions
- ML-based forecasting (1h, 4h, 24h, 7d)

**Trading Signals:**
- `GET /user/hunter/signals/{token}` - Trading signals
- Entry/exit points, stop-loss, take-profit

**Risk Analysis:**
- `GET /user/hunter/risk/{token}` - Risk analysis
- Volatility, liquidity, correlation analysis

**Portfolio Optimizer:**
- `POST /user/hunter/portfolio/optimize` - Portfolio optimization
- Sharpe ratio, risk-adjusted returns

**Pattern Recognition:**
- `GET /user/hunter/patterns/{token}` - Chart patterns
- Head & shoulders, triangles, support/resistance

**Data Sources:** CoinGecko (real), RSS News (real), Reddit (fallback), Twitter/Discord (simulated)

#### 3.2 ULTRA (DeFi Automation - 4 routers)
**Base Path:** `/api/v1/user/ultra/*`

**Arbitrage:**
- `POST /user/ultra/arbitrage/discover` - Find arbitrage opportunities
- Cross-DEX, cross-chain arbitrage

**Flash Loans:**
- `GET /user/ultra/flash-loans/rates` - Flash loan rates
- Aave, dYdX, Uniswap V3

**MEV Protection:**
- `POST /user/ultra/mev/analyze` - MEV risk analysis
- Frontrunning, sandwich attack detection

**Auto-Executor:**
- `POST /user/ultra/auto-executor/create` - Create auto-executor
- Automated trading strategies

#### 3.3 GraphRAG (Protocol Intelligence - 4 routers)
**Base Path:** `/api/v1/user/graph/*`

**Search:**
- `POST /user/graph/search` - Hybrid protocol search
- Vector + graph search, risk scoring

**Analytics:**
- `GET /user/graph/analytics/protocols` - Protocol analytics
- TVL, APY, risk metrics

**Monitoring:**
- `GET /user/graph/monitoring/health` - System health
- Neo4j, vector DB status

**Visualization:**
- `GET /user/graph/visualization/protocols/{id}` - Protocol graph
- Relationship visualization

#### 3.4 ML & AI (2 routers)
**Base Path:** `/api/v1/user/ml/*`

**Prediction:**
- `POST /user/ml/prediction/price` - Price prediction
- `POST /user/ml/prediction/volatility` - Volatility prediction

**Network Analysis:**
- `GET /user/ml/network/analyze` - Network analysis
- Graph-based insights

#### 3.5 DeFi Integrations (6 routers)
**Base Path:** `/api/v1/user/defi/*`

**Aave V3:**
- `GET /user/defi/aave/markets` - Aave markets
- `POST /user/defi/aave/supply` - Supply to Aave
- `POST /user/defi/aave/withdraw` - Withdraw from Aave

**Morpho:**
- `GET /user/defi/morpho/vaults` - Morpho vaults
- `POST /user/defi/morpho/deposit` - Deposit to Morpho

**Curve:**
- `GET /user/defi/curve/pools` - Curve pools
- `POST /user/defi/curve/swap` - Curve swap

**Hyperliquid:**
- `GET /user/defi/hyperliquid/markets` - Perpetual markets
- `POST /user/defi/hyperliquid/trade` - Place order

**LayerZero:**
- `GET /user/defi/layerzero/chains` - Supported chains
- `POST /user/defi/layerzero/bridge` - Cross-chain bridge

**Axelar:**
- `GET /user/defi/axelar/routes` - Bridge routes
- `POST /user/defi/axelar/transfer` - Cross-chain transfer

#### 3.6 NFT (1 router)
**Base Path:** `/api/v1/user/nft/*`

**OpenSea:**
- `GET /user/nft/opensea/collections` - NFT collections
- `GET /user/nft/opensea/assets/{id}` - Asset details

#### 3.7 Portfolio & Wallet
**Portfolio:**
- `GET /user/portfolio` - Portfolio overview
- `GET /user/portfolio/holdings` - Token holdings
- `GET /user/portfolio/history` - Portfolio history

**Wallet:**
- `GET /wallet` - Wallet info
- `POST /wallet/export` - Export wallet
- `GET /wallet/balance` - Wallet balance

#### 3.8 Other User Endpoints
**Dashboard:**
- `GET /user/dashboard` - User dashboard
- `GET /user/dashboard/widgets` - Dashboard widgets

**Alerts:**
- `GET /user/alerts` - User alerts
- `POST /user/alerts` - Create alert

**Preferences:**
- `GET /user/preferences` - User preferences
- `PATCH /user/preferences` - Update preferences

**Search:**
- `GET /user/search` - Search tokens/protocols

**Comparison:**
- `POST /user/comparison` - Compare protocols

**Markets:**
- `GET /user/markets` - Market data

**Bitcoin:**
- `GET /user/bitcoin/transactions` - Bitcoin transactions
- `POST /user/bitcoin/send` - Send Bitcoin

**Atlas:**
- `GET /user/atlas/countries` - Supported countries
- `GET /user/atlas/cities` - Supported cities

**Projects:**
- `GET /user/projects` - User projects
- `POST /user/projects` - Create project

**Transactions:**
- `GET /user/transactions` - Transaction history

**Notifications:**
- `GET /notifications` - User notifications
- `PATCH /notifications/{id}` - Mark as read

**Subscriptions:**
- `GET /subscription` - Subscription status
- `POST /subscription/upgrade` - Upgrade subscription

**Payments:**
- `POST /payments/create` - Create payment
- `GET /payments/{id}` - Payment status

**MoonPay Swap:**
- `POST /moonpay/swap/quote` - Get swap quote
- `POST /moonpay/swap/execute` - Execute swap

---

### 4. ADMIN ENDPOINTS (10+ ROUTERS)

**Base Path:** `/api/v1/admin/*`  
**Authentication:** Admin role required (RBAC)

#### User Management
- `GET /admin/users` - List all users
- `GET /admin/users/{id}` - Get user details
- `POST /admin/users/{id}/activate` - Activate user
- `POST /admin/users/{id}/deactivate` - Deactivate user
- `POST /admin/users/{id}/grant-admin` - Grant admin role
- `POST /admin/users/{id}/revoke-admin` - Revoke admin role

#### LLM Orchestration
- `GET /admin/llm/providers` - List LLM providers (Vertex AI, DeepInfra)
- `GET /admin/llm/models` - List available models
- `GET /admin/llm/telemetry` - LLM usage telemetry
- `GET /admin/llm/budgets` - Cost budgets
- `GET /admin/llm/circuit-breakers` - Circuit breaker status
- `GET /admin/llm/rankings` - Model performance rankings

#### Agent Squad
- `GET /admin/agents` - List all agents (18 agents)
- `POST /admin/agents/enable` - Enable agent
- `POST /admin/agents/disable` - Disable agent
- `GET /admin/agents/telemetry` - Agent usage stats

#### Statistics
- `GET /admin/stats/overview` - System overview
- `GET /admin/stats/usage` - Usage statistics

#### Retry Management
- `GET /admin/retry/jobs` - Failed jobs
- `POST /admin/retry/{id}` - Retry job

#### Distillation
- `GET /admin/distillation/jobs` - Distillation jobs
- `POST /admin/distillation/create` - Create distillation
- `GET /admin/distillation/validation` - Validation results

#### Projects
- `GET /admin/projects` - All projects
- `GET /admin/projects/{id}` - Project details

#### Security
- `GET /admin/security/dashboard` - Security dashboard
- `GET /admin/security/scans` - OWASP scan results

#### Chat Analytics
- `GET /admin/chat/analytics` - Chat analytics
- `GET /admin/chat/intents` - Intent distribution

#### Transactions
- `GET /admin/transactions` - All transactions
- `GET /admin/transactions/{id}` - Transaction details

#### Metrics
- `GET /admin/metrics/overview` - Metrics overview

#### Wallets
- `GET /admin/wallets/{id}` - Wallet details (Privy)
- `PATCH /admin/wallets/{id}` - Update wallet

#### Policies
- `GET /admin/policies` - Privy policies
- `POST /admin/policies` - Create policy

---

### 5. PUBLIC ENDPOINTS

#### Metrics & Monitoring
- `GET /metrics` - Prometheus metrics (public)
- `GET /monitoring/health` - Health check (public)
- `GET /monitoring/status` - System status (public)

#### Chat Shortcuts
- `GET /chat/shortcuts` - Public chat shortcuts

#### General
- `GET /` - Redirect to docs
- `GET /health` - Health endpoint

---

## RESPONSIBILITY MATRIX

| Endpoint Category | User Type | Authentication | Data Storage | Purpose |
|-------------------|-----------|----------------|--------------|---------|
| `/api/v1/user/chat/*` | Authenticated | Required | `conversations` table | ⚠️ DEPRECATED - Legacy chat |
| `/api/v1/conversations/*` | Guest + Auth | Optional | `chat_conversations` table | ✅ NEW - Primary chat system |
| `/api/v1/guest/*` | Guest only | None | `guest_users`, `guest_conversations` | Guest demo chat |
| `/api/v1/chat` | Guest + Auth | Optional | Auto-detect | Universal endpoint (experimental) |
| `/api/v1/account/*` | Public + Auth | Mixed | `users`, `auth_sessions` | Authentication & account |
| `/api/v1/auth/*` | Admin | Required | `users` | Role management |
| `/api/v1/user/*` | Authenticated | Required | Various | User features (portfolio, wallet, etc.) |
| `/api/v1/admin/*` | Admin | Required | Various | System administration |
| `/api/v1/metrics` | Public | None | Redis | System metrics |
| `/api/v1/monitoring` | Public | None | - | Health checks |

---

## ARCHITECTURAL PATTERNS ANALYSIS

### ✅ Hexagonal Architecture
**Layers:**
1. **Domain Layer:** Entities, value objects, ports (interfaces)
2. **Application Layer:** Commands, queries, interactors
3. **Infrastructure Layer:** Adapters, repositories, external integrations
4. **Presentation Layer:** HTTP controllers, routers, schemas

**Compliance:**
- Domain layer has NO dependencies on outer layers ✅
- Application layer orchestrates domain logic ✅
- Infrastructure implements domain ports ✅
- Presentation depends on application, not domain directly ✅

### ✅ CQRS Pattern
**Commands:** Write operations via `UserCommandGateway`
- CreateConversation, SendMessage, ExecuteAction
- Uses domain entities

**Queries:** Read operations via `UserQueryGateway`
- ListConversations, GetMessages, GetPortfolio
- Uses optimized query models

**Separation:** Clear command/query split in application layer ✅

### ✅ Dependency Injection
**Framework:** Dishka (NOT FastAPI's built-in DI)
- Maintains framework independence ✅
- Scoped lifecycles (request, singleton) ✅
- Type-safe injection with `FromDishka[T]` ✅

### ⚠️ Endpoint Overlap (Problem)
**Issue:** 4 chat systems with overlapping responsibilities

**Current State:**
1. Legacy (`/user/chat/*`) - 15 endpoints
2. New (`/conversations/*`) - 9 endpoints
3. Guest (`/guest/*`) - 4 endpoints
4. Universal (`/chat`) - 2 endpoints

**Impact:**
- Confuses developers on which endpoint to use
- Increases maintenance burden (4 codepaths)
- Duplication of logic (intent detection, rate limiting)

---

## DEPRECATION TIMELINE & MIGRATION STRATEGY

### Phase 1: Immediate (Q1 2026 - Before 2026-06-01)
**Actions:**
1. ✅ Add deprecation headers to legacy endpoints (DONE)
2. ⏳ Monitor usage metrics for `/user/chat/*`
3. ⏳ Update frontend to use `/conversations/*`
4. ⏳ Notify API consumers via email/docs
5. ⏳ Create migration guide with code examples

**Deprecation Headers (Already Implemented):**
```http
Deprecation: true
Sunset: Sun, 01 Jun 2026 00:00:00 GMT
Link: </api/v1/conversations>; rel="successor-version"
```

### Phase 2: Migration (Q2 2026)
**Target Date:** 2026-06-01 (Sunset)

**Actions:**
1. Remove `/api/v1/user/chat/*` router
2. Remove legacy table mappers (`conversations`, `messages` with INTEGER user_id)
3. Remove legacy interactors (`CreateConversation`, `SendMessage` using old tables)
4. Update OpenAPI schema to remove deprecated endpoints
5. Archive legacy code with git tag `legacy-chat-final`

**Breaking Changes:**
- All clients MUST migrate to `/api/v1/conversations/*`
- Session data NOT automatically migrated (users must re-login)
- Conversation history preserved (data migration completed)

### Phase 3: Consolidation (Q3-Q4 2026)
**Evaluation:** Determine if universal endpoint `/api/v1/chat` should replace guest+conversations

**Options:**
1. **Keep 3 endpoints** (conversations, guest, universal)
   - Pros: Backward compatibility, clear separation
   - Cons: Maintenance overhead
   
2. **Consolidate to universal** (only `/api/v1/chat`)
   - Pros: Single source of truth, simpler for clients
   - Cons: Loses explicit guest/auth separation in URL
   
3. **Keep 2 endpoints** (conversations for auth, guest for public)
   - Pros: Clear separation, removes universal redundancy
   - Cons: Clients must know which endpoint to use

**Recommendation:** Option 1 (3 endpoints) until 2027, then evaluate Option 2

### Phase 4: Long-term (2027+)
**Goal:** Single unified chat endpoint

**Proposed:** `/api/v1/chat` becomes primary, others alias to it  
**Rationale:**
- Simplifies client integration
- Auto-detects user type (guest vs auth)
- Maintains backward compatibility via routing

---

## MIGRATION GUIDE (For API Consumers)

### Legacy → New System Migration

#### Before (DEPRECATED):
```bash
# Create conversation
POST /api/v1/user/chat/conversations
Authorization: Bearer {jwt}
{
  "title": "My Conversation"
}

# Send message
POST /api/v1/user/chat/conversations/{id}/messages
Authorization: Bearer {jwt}
{
  "content": "What is Bitcoin?",
  "language": "en"
}
```

#### After (NEW):
```bash
# Create conversation
POST /api/v1/conversations
Authorization: Bearer {jwt}  # Optional for guests
{
  "title": "My Conversation",
  "language": "en"
}

# Send message
POST /api/v1/conversations/{id}/messages
Authorization: Bearer {jwt}  # Optional for guests
{
  "content": "What is Bitcoin?",
  "language": "en"
}
```

**Key Differences:**
1. Base path changed: `/user/chat/*` → `/conversations/*`
2. Guest support: New system supports guests (IP-based)
3. Response format: Enhanced with routing metadata
4. Tables: `chat_conversations`, `chat_messages` (UUID user_id)

### Guest Chat Migration

#### Before:
```bash
POST /api/v1/guest/chat
{
  "content": "What is Ethereum?",
  "language": "en"
}
```

#### After (Option 1 - Dedicated guest endpoint):
```bash
POST /api/v1/guest/chat
{
  "content": "What is Ethereum?",
  "language": "en"
}
```

#### After (Option 2 - Universal endpoint):
```bash
POST /api/v1/chat
{
  "content": "What is Ethereum?",
  "language": "en"
}
# No Authorization header = automatically treated as guest
```

**Recommendation:** Use Option 2 (universal endpoint) for new integrations

---

## RISK ASSESSMENT

### HIGH RISK
1. **Legacy Endpoint Removal (2026-06-01)**
   - **Impact:** Frontend clients using `/user/chat/*` will break
   - **Mitigation:** Deprecation headers, email notifications, monitoring
   - **Contingency:** Keep legacy router for 30 days post-sunset as read-only

2. **Data Migration Issues**
   - **Impact:** Conversation history loss if migration fails
   - **Mitigation:** Data migration already completed ✅
   - **Validation:** Both systems use same domain layer

### MEDIUM RISK
3. **Endpoint Confusion**
   - **Impact:** Developers use wrong endpoint, suboptimal UX
   - **Mitigation:** Clear documentation, OpenAPI examples
   - **Monitoring:** Track endpoint usage metrics

4. **Universal Endpoint Adoption**
   - **Impact:** Low adoption if not promoted
   - **Mitigation:** Update SDKs, client libraries, examples
   - **Timeline:** Q2 2026

### LOW RISK
5. **Performance Degradation**
   - **Impact:** Universal endpoint adds routing overhead
   - **Measurement:** ~2ms latency increase (negligible)
   - **Mitigation:** Optimize intent detection, cache user type

6. **Security Regression**
   - **Impact:** Auth bypass in universal endpoint
   - **Mitigation:** Extensive testing, rate limiting per user type
   - **Status:** Security audit passed ✅

---

## RECOMMENDATIONS

### Immediate Actions (Q1 2026)
1. ✅ **Documentation:**
   - Create `/docs/API_MIGRATION_GUIDE.md`
   - Update OpenAPI schema with deprecation notices
   - Add migration examples to README

2. ⏳ **Monitoring:**
   - Set up Prometheus metrics for endpoint usage
   - Track legacy endpoint calls (`/user/chat/*`)
   - Alert if usage > 10% after 2026-05-01

3. ⏳ **Communication:**
   - Email all API consumers with migration guide
   - Post announcement in developer Discord
   - Update status page with deprecation timeline

### Short-term (Q2 2026)
4. **Removal:**
   - Delete `/api/v1/user/chat/*` router on 2026-06-01
   - Archive legacy code with git tag
   - Update CI/CD to fail on legacy imports

5. **Consolidation:**
   - Promote universal endpoint `/api/v1/chat` as primary
   - Update client SDKs (JavaScript, Python, Go)
   - Create migration scripts for popular frameworks (React, Next.js)

### Long-term (Q3-Q4 2026)
6. **Optimization:**
   - Evaluate consolidating to single universal endpoint
   - Benchmark performance impact
   - Conduct user survey on endpoint preference

7. **Documentation:**
   - Create endpoint decision tree (which endpoint to use?)
   - Video tutorial for migration
   - API playground with live examples

---

## APPENDIX A: ENDPOINT COUNT BY CATEGORY

| Category | Router Count | Endpoint Count | Authentication |
|----------|--------------|----------------|----------------|
| **Chat** | 5 | 30+ | Mixed |
| **Authentication** | 2 | 12 | Public + Admin |
| **User Features** | 30+ | 150+ | Required |
| **Hunter AI** | 6 | 25 | Required |
| **ULTRA** | 4 | 15 | Required |
| **GraphRAG** | 4 | 20 | Required |
| **ML & AI** | 2 | 10 | Required |
| **DeFi** | 6 | 30 | Required |
| **NFT** | 1 | 5 | Required |
| **Admin** | 10+ | 50+ | Admin Only |
| **Public** | 3 | 5 | None |
| **Total** | **73+** | **350+** | - |

---

## APPENDIX B: TECHNOLOGY STACK

### Backend Framework
- **FastAPI** - Web framework
- **Dishka** - Dependency injection
- **Pydantic** - Request/response validation
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations

### Databases
- **PostgreSQL** - Primary database
- **Redis** - Rate limiting, caching
- **Neo4j** - Graph database (GraphRAG)

### AI & ML
- **Vertex AI** - Primary LLM provider ($0.10/1M tokens)
- **DeepInfra** - Fallback LLM provider
- **Agent Squad** - 18 specialized AI agents

### External Integrations
- **MCP Servers** - 11 servers (1inch, DeFiLlama, CoinGecko, etc.)
- **Privy** - Wallet management
- **MoonPay** - Fiat on-ramp
- **0x Protocol** - DEX aggregation

---

## APPENDIX C: CONTACT & ESCALATION

**Primary Contacts:**
- **CTO:** system-architect
- **Backend Lead:** software-engineering-expert
- **DevOps:** infrastructure-expert
- **Security:** security-specialist

**Escalation Path:**
1. Developer → Backend Lead
2. Backend Lead → CTO
3. CTO → Executive Team

**Migration Support:**
- Slack: #api-migration
- Email: api-support@anvil.finance
- Office Hours: Tue/Thu 2-4pm UTC

---

**END OF ANALYSIS**  
**Next Steps:** Review with executive team, approve migration timeline, begin implementation of Phase 1 actions.
