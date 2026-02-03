# Complete Database Architecture & Table Mission Specification

> **Framework:** MIT Systems Thinking + Stanford Design Thinking + First Principles Analysis  
> **Agents:** @database-architect + @backend-engineer + @agent-evolution-system  
> **Status:** Phase 2 - Complete Database Analysis (87 Tables Mapped)  
> **Date:** 2026-01-25

---

## Executive Summary

**Mission:** Analyze the complete database structure of the Anvil DeFi Backend to understand the purpose, relationships, and architectural patterns of each table within the hexagonal architecture framework.

**Scope:** **105 tables mapped** (92 currently in database + 10 money market tables) across **17 functional domains** supporting a multi-agent DeFi platform with guest/authenticated chat, blockchain operations, AI telemetry, LLM orchestration, portfolio management, lending/borrowing operations, and money market rate optimization.

**Key Findings:**
- ✅ **Comprehensive hexagonal architecture** with proper domain isolation across 105 tables
- ✅ **Enterprise LLM Orchestration** with 15 tables managing multi-provider AI operations
- ✅ **Triple chat architecture** (unified + authenticated + guest) all fully operational
- ✅ **Legacy system fully removed** on 2026-01-25 (1,200+ lines of deprecated code eliminated)
- ✅ **Lending & borrowing system** (8 tables + 2 views) with health factor monitoring and leverage loops
- ✅ **Money market optimization** (7 tables + 3 views) with 60s TTL caching and rate comparison *(NEW 2026-01-28)*
- ✅ **Advanced distillation system** (6 tables) for LLM cost optimization
- ✅ **Project-based knowledge bases** (12 tables) for RAG and context management
- ✅ **Comprehensive AI telemetry** tracking 18 specialized agents across 13 tables
- ✅ **Multi-chain wallet support** with Privy integration
- ✅ **Retry/resilience infrastructure** (3 tables) for fault tolerance
- ✅ **Bridge adapters** maintain backward compatibility for existing commands

**Database Technology:** PostgreSQL 16 with UUID, JSONB, pgvector (embeddings), and enum support

---

## 🏗️ Complete Table Inventory (95 Tables)

### Domain Summary

| Domain | Tables | Purpose |
|--------|--------|---------|
| **1. Authentication & User Management** | 6 | User lifecycle, auth sessions, password mgmt, email verification |
| **2. Chat System - Unified** | 4 | Modern chat for guest + authenticated users with multi-language |
| **3. Chat System - Guest** | 4 | Guest-specific chat tracking with IP-based identification |
| **4. Chat System - Context & Analytics** | 3 | Conversation intelligence, user preferences, feedback |
| **5. Subscriptions & Payments** | 5 | Stripe integration, MoonPay, notifications |
| **6. Wallets & Transactions** | 3 | Multi-chain wallets, blockchain transactions |
| **7. DeFi Operations** | 6 | Hyperliquid positions, yield farming, automated savings |
| **8. LLM Orchestration System** | 15 | Enterprise multi-provider LLM management |
| **9. AI Telemetry** | 13 | Agent execution tracking, cost monitoring, performance metrics |
| **10. Distillation System** | 6 | LLM response caching and cost optimization |
| **11. Projects & Knowledge Bases** | 12 | Multi-project RAG, document embeddings, knowledge management |
| **12. Retry & Resilience** | 3 | Circuit breakers, retry logic, service overrides |
| **13. Security & Compliance** | 3 | Privy policy caching, audit logs, access control |
| **14. Location & System Config** | 3 | Countries, cities, system-wide configuration |
| **15. Agent Sessions** | 1 | Stateful agent conversation management |
| **16. Lending & DeFi Borrowing** | 10 | Lending positions, health monitoring, leverage loops, alerts (8 tables + 2 views) |
| **17. Money Market Optimization** | 10 | Rate comparison, protocol optimization, alerts (7 tables + 3 views) |

**Total:** 105 tables mapped (87 tables + 8 lending tables + 7 money market tables + 5 views)

---

## 📋 Domain 1: Authentication & User Management (6 Tables)

### 1.1 users

**Mission:** Central user registry supporting email, Privy (Web3), and multi-wallet authentication.

**Schema Highlights:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NULL,  -- Nullable for Privy-only users
    privy_user_id VARCHAR(255) UNIQUE NULL,
    primary_wallet_address VARCHAR(255) NULL,
    auth_provider VARCHAR(50) DEFAULT 'email',  -- 'email' | 'privy'
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_ip VARCHAR(45),
    registration_ip VARCHAR(45),
    language VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Business Rules:**
- Privy users have `privy_user_id` but may lack email/password
- Email users must verify via `email_verifications` table
- `primary_wallet_address` links to Privy embedded wallet
- `auth_provider` determines authentication flow

**Usage Patterns:**
- `UserRepository` for domain operations
- `AuthenticationService` for login/logout
- Indexed by: id, email, privy_user_id, primary_wallet_address

### 1.2 auth_sessions

**Mission:** JWT session tracking with expiration management.

**Schema:**
```sql
CREATE TABLE auth_sessions (
    id VARCHAR(255) PRIMARY KEY,  -- JWT token ID
    user_id INTEGER REFERENCES users(id) NOT NULL,
    expiration TIMESTAMP WITH TIME ZONE NOT NULL
);
```

**Business Rules:**
- Session ID is the JWT token identifier
- Automatic cleanup of expired sessions via background job
- Single session per user (new login invalidates old session)

### 1.3 email_verifications

**Mission:** Email verification code storage with expiration.

**Key Fields:**
- `user_id`: Links to users table
- `verification_code`: 6-digit code
- `expires_at`: Timestamp for code expiration
- `verified_at`: Null until verification complete

### 1.4 password_resets

**Mission:** Password reset token management with security.

**Key Fields:**
- `user_id`: Links to users table
- `reset_token`: Secure random token
- `expires_at`: Token expiration (typically 1 hour)
- `used_at`: Tracks token usage to prevent reuse

### 1.5 user_events

**Mission:** Track user lifecycle events for analytics and debugging.

**Key Fields:**
- `user_id`: Links to users table
- `event_type`: 'login', 'logout', 'password_change', 'wallet_connected', etc.
- `event_data`: JSONB with contextual information
- `ip_address`: User's IP at event time
- `user_agent`: Browser/client information
- `created_at`: Event timestamp

### 1.6 user_context_aware

**Mission:** Store user-specific context for personalized agent responses.

**Key Fields:**
- `user_id`: UUID (links to chat_users or users)
- `context_data`: JSONB with user preferences, history, patterns
- `last_updated_at`: Context freshness timestamp

---

## 📋 Domain 2: Chat System - Unified (4 Tables)

**Purpose:** Primary UUID-based chat system supporting both guest and authenticated users.

**Status:** ✅ ACTIVE - Primary chat system (replaced legacy INTEGER-based system on 2026-01-25)

### 2.1 chat_users

**Mission:** Unified user identity for chat (replaces legacy `users` INTEGER id).

**Schema:**
```sql
CREATE TABLE chat_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type VARCHAR(20) NOT NULL,  -- 'guest' | 'authenticated' | 'premium'
    identifier VARCHAR(255) NOT NULL,  -- IP for guest, privy_id for authenticated
    privy_id VARCHAR(255) NULL,
    display_name VARCHAR(100),
    language VARCHAR(5) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Business Rules:**
- `user_type='guest'`: identifier is IP address
- `user_type='authenticated'`: identifier is privy_user_id
- `user_type='premium'`: Has active subscription
- Automatically upgraded from guest → authenticated when user signs up

### 2.2 chat_conversations

**Mission:** Conversation container for message threading.

**Key Fields:**
- `id`: UUID conversation identifier
- `chat_user_id`: Links to chat_users
- `title`: Auto-generated or user-specified
- `status`: 'active' | 'archived' | 'deleted'
- `language`: Conversation language (inherited from user)
- `message_count`: Denormalized for performance
- `metadata`: JSONB for extensibility

### 2.3 chat_messages

**Mission:** Individual messages within conversations.

**Schema:**
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    intent VARCHAR(50),  -- Detected intent: 'swap', 'portfolio', 'help', etc.
    handler VARCHAR(50),  -- Handler used: 'swap_handler_v2', 'portfolio_handler', etc.
    confidence FLOAT,  -- Intent confidence score (0.0-1.0)
    language VARCHAR(5) DEFAULT 'en',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Intent Classification:**
- swap, buy, sell, transfer, portfolio, price, news, help, greeting, farewell

### 2.4 chat_rate_limits

**Mission:** Rate limiting for guest users to prevent abuse.

**Key Fields:**
- `chat_user_id`: Links to chat_users
- `time_window_start`: Rolling window start time
- `message_count`: Messages sent in current window
- `limit_type`: 'hourly' | 'daily'
- `max_messages`: Limit threshold (20/hour for guests)

**Business Rules:**
- Guests: 20 messages/hour
- Authenticated users: 100 messages/hour
- Premium users: 1000 messages/hour

---

## 📋 Domain 3: Chat System - Guest (4 Tables)

**Purpose:** Specialized IP-based guest chat tracking system.

**Status:** ✅ ACTIVE - Standalone guest system for anonymous users (not deprecated)

### 3.1 guest_users
**Mission:** Track guest users by IP address with fingerprinting.

### 3.2 guest_conversations
**Mission:** Guest-specific conversations linked to IP-based users.

### 3.3 guest_messages
**Mission:** Messages in guest conversations with intent tracking.

### 3.4 guest_telemetry
**Mission:** Analytics for guest interactions (conversion tracking, engagement metrics).

**Key Metrics:**
- `event_type`: 'message_sent', 'conversion', 'signup', 'wallet_connected'
- `event_data`: JSONB with contextual information
- Used for guest-to-user conversion funnel analysis

---

## 📋 Domain 4: Chat System - Context & Analytics (3 Tables)

### 4.1 conversation_contexts

**Mission:** Store conversation context for context-aware agent responses.

**Key Fields:**
```sql
CREATE TABLE conversation_contexts (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,
    current_topic VARCHAR(255),
    recent_intents JSON,  -- Array of recent intent strings
    mentioned_tokens JSON,  -- ['ETH', 'USDC', 'ARB']
    mentioned_protocols JSON,  -- ['Uniswap', 'Aave', 'Curve']
    active_positions JSON,  -- Current open positions
    preferred_slippage FLOAT,
    preferred_leverage INTEGER,
    risk_tolerance VARCHAR(20),  -- 'conservative' | 'moderate' | 'aggressive'
    preferred_chains JSON,
    frequent_operations JSON,  -- {'swap': 50, 'portfolio': 30}
    typical_trade_sizes JSON,
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**Usage:**
- Loaded at conversation start for personalization
- Updated after each user interaction
- Used by Hunter AI to provide contextual recommendations

### 4.2 conversation_analytics

**Mission:** Aggregate conversation metrics for insights.

**Key Metrics:**
- Message counts per conversation
- Average response time
- Intent distribution
- User satisfaction scores
- Conversion events

### 4.3 conversation_feedback

**Mission:** User feedback on AI responses for quality improvement.

**Schema:**
```sql
CREATE TABLE conversation_feedback (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES llm_conversations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER,  -- 1-5 stars
    feedback_type VARCHAR(50),  -- 'helpful' | 'not_helpful' | 'inappropriate' | 'incorrect'
    feedback_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📋 Domain 5: Subscriptions & Payments (5 Tables)

### 5.1 subscriptions

**Mission:** Manage user subscription tiers (Free, Premium, Enterprise).

**Key Fields:**
- `user_id`: References users(id)
- `stripe_subscription_id`: Stripe subscription identifier
- `plan`: 'free' | 'premium' | 'enterprise'
- `status`: 'active' | 'canceled' | 'past_due' | 'trialing'
- `current_period_start`, `current_period_end`: Billing period
- `cancel_at_period_end`: Boolean for pending cancellations

### 5.2 subscription_users

**Mission:** Many-to-many relationship for shared subscriptions (Enterprise plans).

### 5.3 payments

**Mission:** Payment transaction history with Stripe integration.

**Key Fields:**
- `user_id`, `subscription_id`: References
- `stripe_payment_intent_id`: Stripe PI identifier
- `amount`, `currency`: Payment details
- `status`: 'succeeded' | 'failed' | 'pending'
- `payment_method`: 'card' | 'crypto' | 'wire'

### 5.4 notifications

**Mission:** In-app and email notification queue.

**Types:**
- payment_success, payment_failed
- subscription_renewed, subscription_expiring
- wallet_connected, transaction_confirmed
- price_alert, portfolio_milestone

### 5.5 moonpay_customer_tokens

**Mission:** Store MoonPay customer tokens for fiat on-ramp.

**Key Fields:**
- `user_id`: Links to users
- `moonpay_customer_id`: MoonPay identifier
- `encrypted_token`: Encrypted customer token
- `created_at`, `expires_at`: Token lifecycle

---

## 📋 Domain 6: Wallets & Transactions (3 Tables)

### 6.1 wallets

**Mission:** Multi-chain wallet management with Privy integration.

**Schema:**
```sql
CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    privy_wallet_id VARCHAR(255) UNIQUE,
    wallet_type VARCHAR(20),  -- 'privy' | 'external' | 'imported'
    is_primary BOOLEAN DEFAULT FALSE,
    nickname VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 chain_addresses

**Mission:** Multi-chain address mapping for each wallet.

**Schema:**
```sql
CREATE TABLE chain_addresses (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER REFERENCES wallets(id) ON DELETE CASCADE,
    chain VARCHAR(20),  -- 'arbitrum' | 'base' | 'optimism' | 'ethereum' | 'polygon'
    address VARCHAR(42) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_balance_check TIMESTAMP WITH TIME ZONE,
    cached_balance NUMERIC(30, 18),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(wallet_id, chain)
);
```

**Supported Chains:**
- Arbitrum, Base, Optimism, Ethereum Mainnet
- Polygon, Avalanche, BSC, zkSync, Linea, Scroll

### 6.3 transactions

**Mission:** Blockchain transaction history with dual-user tracking.

**Schema:**
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER REFERENCES wallets(id) ON DELETE CASCADE,
    tx_hash VARCHAR(66) NULL,  -- NOT globally unique (multi-chain)
    type INTEGER NOT NULL,  -- 0=SWAP, 1=FUND, 2=LP_ADD, 3=LP_REMOVE, 4=EARN, 5=SEND, 6=RECEIVE
    chain VARCHAR(20) NOT NULL,
    asset_in VARCHAR(20), amount_in NUMERIC(30, 18),
    asset_out VARCHAR(20), amount_out NUMERIC(30, 18),
    gas_used BIGINT, gas_price BIGINT,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'confirmed' | 'failed'
    block_number BIGINT,
    tx_metadata JSONB NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITH TIME ZONE
);
```

**Critical Note:** `tx_hash` is NOT globally unique due to multi-chain support. Use `(chain, tx_hash)` as composite unique key.

---

## 📋 Domain 7: DeFi Operations (6 Tables)

### 7.1 hyperliquid_positions

**Mission:** Track perpetual futures positions on Hyperliquid DEX.

**Key Fields:**
```sql
- id, user_id, wallet_id
- symbol VARCHAR(20)  -- 'BTC-PERP', 'ETH-PERP'
- side VARCHAR(10)  -- 'LONG' | 'SHORT'
- leverage NUMERIC(5, 2)  -- e.g., 10.00 for 10x
- size NUMERIC(30, 18)  -- Position size
- entry_price, mark_price, liquidation_price NUMERIC(20, 8)
- unrealized_pnl, realized_pnl NUMERIC(20, 8)
- margin NUMERIC(20, 8)  -- Collateral
- funding_rate NUMERIC(10, 6)  -- Current funding rate
- status VARCHAR(20)  -- 'OPEN' | 'CLOSED' | 'LIQUIDATED'
- opened_at, closed_at TIMESTAMP WITH TIME ZONE
```

### 7.2 earn_positions

**Mission:** Yield farming and lending positions across protocols.

**Supported Protocols:**
- Aave (lending/borrowing)
- Compound (lending)
- Curve (LP rewards)
- Yearn (vault deposits)
- Convex (boosted Curve rewards)

**Key Fields:**
```sql
- chain VARCHAR(20)  -- 'arbitrum' | 'optimism' | etc.
- protocol VARCHAR(50)  -- 'aave' | 'compound' | 'curve'
- asset VARCHAR(20)  -- Deposited asset
- amount_deposited NUMERIC(30, 18)
- current_value NUMERIC(30, 18)  -- Current value with rewards
- apy NUMERIC(8, 4)  -- Annual percentage yield (e.g., 5.25%)
- rewards_earned NUMERIC(30, 18)  -- Total rewards earned
- status VARCHAR(20)  -- 'ACTIVE' | 'WITHDRAWN'
```

### 7.3 save_schedules

**Mission:** Automated recurring deposits (DCA - Dollar Cost Averaging).

**Example Use Case:**
"Save $100 of USDC to Aave every Friday at 2 PM UTC"

**Key Fields:**
```sql
- frequency VARCHAR(20)  -- 'daily' | 'weekly' | 'monthly'
- day_of_week INTEGER  -- 0-6 (Monday=0)
- day_of_month INTEGER  -- 1-31
- amount NUMERIC(30, 18)  -- Amount to save
- destination_protocol VARCHAR(50)  -- Where to deposit
- next_execution_at TIMESTAMP WITH TIME ZONE
- status VARCHAR(20)  -- 'ACTIVE' | 'PAUSED' | 'COMPLETED'
- total_saved NUMERIC(30, 18)  -- Cumulative amount saved
- execution_count INTEGER
- max_executions INTEGER  -- Optional limit
```

### 7.4 token_holdings

**Mission:** Current token balances across all chains.

**Updated via:**
- Real-time: On transaction confirmation
- Scheduled: Hourly balance refresh job
- On-demand: When user views portfolio

### 7.5 portfolio_snapshots

**Mission:** Daily portfolio value snapshots for historical charting.

**Key Fields:**
- `user_id`, `snapshot_date`
- `total_value_usd`: Total portfolio value
- `holdings_snapshot`: JSONB with all token balances
- `pnl_24h`, `pnl_7d`, `pnl_30d`: Performance metrics

### 7.6 settings

**Mission:** User-specific DeFi settings and preferences.

**Stored Settings:**
- Default slippage tolerance
- Default gas settings (slow/normal/fast)
- Favorite tokens
- Watchlist
- Alert preferences

---

## 📋 Domain 8: LLM Orchestration System (15 Tables)

**Purpose:** Enterprise-grade multi-provider LLM management with circuit breakers, cost tracking, and adaptive model ranking.

### 8.1 llm_providers

**Mission:** Manage LLM provider configurations (Vertex AI, DeepInfra, OpenAI, Bedrock).

**Schema:**
```sql
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 'vertex_ai' | 'deepinfra' | 'openai' | 'bedrock'
    display_name VARCHAR(100),
    priority INTEGER DEFAULT 1,  -- 1=highest priority
    is_enabled BOOLEAN DEFAULT TRUE,
    health_status VARCHAR(20) DEFAULT 'healthy',  -- 'healthy' | 'degraded' | 'down'
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_check_interval_seconds INTEGER DEFAULT 60,
    config JSONB,  -- API keys, endpoints, etc.
    rate_limits JSONB,  -- {'requests_per_minute': 60}
    created_at, updated_at TIMESTAMP WITH TIME ZONE
);
```

### 8.2 llm_models

**Mission:** Catalog of available LLM models across providers.

**Schema:**
```sql
CREATE TABLE llm_models (
    id UUID PRIMARY KEY,
    provider_id UUID REFERENCES llm_providers(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,  -- 'claude-3-5-sonnet-20241022'
    display_name VARCHAR(100),
    model_family VARCHAR(50),  -- 'claude' | 'gpt' | 'gemini'
    capabilities JSONB,  -- ['vision', 'tools', 'streaming']
    context_window INTEGER,  -- e.g., 200000
    max_output_tokens INTEGER,  -- e.g., 4096
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_tools BOOLEAN DEFAULT TRUE,
    cost_per_1k_input_tokens NUMERIC(10, 6),  -- e.g., 0.003
    cost_per_1k_output_tokens NUMERIC(10, 6),  -- e.g., 0.015
    avg_latency_ms INTEGER,
    is_enabled BOOLEAN DEFAULT TRUE,
    carousel_position INTEGER DEFAULT 1,  -- Display order in UI
    tier VARCHAR(20) DEFAULT 'standard',  -- 'premium' | 'standard' | 'economy' | 'experimental'
    created_at, updated_at TIMESTAMP WITH TIME ZONE
);
```

### 8.3 agent_model_rankings

**Mission:** Adaptive model ranking per agent type based on performance.

**How It Works:**
1. Each agent type (Hunter AI, Research, Execution, etc.) tracks performance per model
2. Ranking score calculated from: success_rate (50%) + latency_score (25%) + cost_score (15%) + recency (10%)
3. Scores updated after each request
4. Model selection uses weighted random sampling based on ranking scores

**Schema:**
```sql
CREATE TABLE agent_model_rankings (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(50) NOT NULL,  -- 'hunter_ai' | 'research' | 'execution'
    model_id UUID REFERENCES llm_models(id) ON DELETE CASCADE,
    ranking_score NUMERIC(5, 4),  -- 0.0000 to 1.0000
    success_rate NUMERIC(5, 4),
    latency_score NUMERIC(5, 4),
    cost_score NUMERIC(5, 4),
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    timeout_requests INTEGER DEFAULT 0,
    avg_latency_ms INTEGER,
    p95_latency_ms INTEGER,
    avg_cost_per_request NUMERIC(10, 6),
    total_tokens_used INTEGER,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_recalculated_at TIMESTAMP WITH TIME ZONE
);
```

### 8.4 ranking_weight_profiles

**Mission:** Define ranking calculation weights per agent type.

**Example:**
```json
{
  "agent_type": "hunter_ai",
  "success_weight": 0.50,
  "latency_weight": 0.25,
  "cost_weight": 0.15,
  "recency_weight": 0.10,
  "min_requests_for_ranking": 10,
  "recency_decay_hours": 24
}
```

### 8.5 ranking_overrides

**Mission:** Manual ranking overrides for specific agent-model combinations.

**Use Cases:**
- Force premium model for critical agents
- Disable underperforming model temporarily
- A/B testing new models

### 8.6 llm_requests

**Mission:** Track complete request lifecycle from creation to completion.

**Request States:**
1. `pending` → Request created
2. `selecting_model` → Choosing optimal model
3. `executing` → Sending to provider
4. `streaming` (optional) → Receiving streamed response
5. `completed` | `failed` | `timeout` → Final states

**Key Fields:**
```sql
CREATE TABLE llm_requests (
    id UUID PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE NOT NULL,
    user_id UUID,
    agent_type VARCHAR(50) NOT NULL,
    session_id UUID,
    prompt_hash VARCHAR(64),  -- For cache lookups
    input_tokens INTEGER,
    max_output_tokens INTEGER,
    temperature NUMERIC(3, 2),
    has_tools BOOLEAN DEFAULT FALSE,
    is_streaming BOOLEAN DEFAULT FALSE,
    status VARCHAR(30) DEFAULT 'pending',
    status_history JSONB,  -- Array of {state, timestamp}
    selected_provider_id UUID REFERENCES llm_providers(id),
    selected_model_id UUID REFERENCES llm_models(id),
    selection_reason VARCHAR(100),  -- 'highest_ranking' | 'fallback' | 'override'
    attempt_count INTEGER DEFAULT 0,
    total_latency_ms INTEGER,
    time_to_first_token_ms INTEGER,  -- For streaming
    output_tokens INTEGER,
    estimated_cost_usd NUMERIC(10, 6),
    actual_cost_usd NUMERIC(10, 6),
    error_code VARCHAR(50),
    error_message TEXT,
    created_at, started_at, completed_at TIMESTAMP WITH TIME ZONE
);
```

### 8.7 llm_request_attempts

**Mission:** Track individual retry attempts for failed requests.

**Example Retry Flow:**
1. Attempt 1: Vertex AI → Rate limited
2. Attempt 2: DeepInfra (fallback) → Timeout
3. Attempt 3: Vertex AI → Success

**Schema:**
```sql
CREATE TABLE llm_request_attempts (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES llm_requests(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    provider_id UUID REFERENCES llm_providers(id),
    model_id UUID REFERENCES llm_models(id),
    status VARCHAR(30),  -- 'started' | 'completed' | 'failed' | 'timeout' | 'rate_limited'
    latency_ms INTEGER,
    input_tokens, output_tokens INTEGER,
    cost_usd NUMERIC(10, 6),
    error_type VARCHAR(50),  -- 'rate_limit' | 'timeout' | 'server_error' | 'invalid_request'
    error_code VARCHAR(50),
    error_message TEXT,
    started_at, completed_at TIMESTAMP WITH TIME ZONE
);
```

### 8.8 circuit_breakers

**Mission:** Circuit breaker state management per provider/model.

**States:**
1. `closed` → Normal operation
2. `open` → Too many failures, blocking requests
3. `half_open` → Testing if service recovered

**Configuration:**
```json
{
  "failure_threshold": 5,  // Open after 5 consecutive failures
  "success_threshold": 3,  // Close after 3 consecutive successes in half_open
  "timeout_seconds": 60,  // Stay open for 60s before half_open
  "half_open_max_requests": 3  // Max concurrent requests in half_open
}
```

**Schema:**
```sql
CREATE TABLE circuit_breakers (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(20),  -- 'provider' | 'model'
    entity_id UUID NOT NULL,
    entity_name VARCHAR(100),
    state VARCHAR(20) DEFAULT 'closed',
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    consecutive_failures INTEGER DEFAULT 0,
    last_failure_at, last_success_at TIMESTAMP WITH TIME ZONE,
    opened_at, half_open_at TIMESTAMP WITH TIME ZONE,
    config JSONB,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### 8.9 llm_telemetry_hourly

**Mission:** Hourly aggregated metrics per provider/model/agent.

**Metrics Tracked:**
- Request counts (total, successful, failed, timeout, retried, cached)
- Latency percentiles (p50, p95, p99, avg, min, max)
- Token usage (total input, total output, averages)
- Cost metrics (total cost, avg per request)
- Cache performance (hit rate, retry rate)

### 8.10 llm_cost_daily

**Mission:** Daily cost rollup per provider.

**Use Cases:**
- Budget monitoring
- Provider cost comparison
- Billing reconciliation
- Cost attribution by tier (premium/standard/economy)

### 8.11 llm_business_config

**Mission:** Runtime configuration key-value store.

**Stored Configs:**
- Feature flags: `distillation_enabled`, `semantic_cache_enabled`
- Thresholds: `max_cost_per_day_usd`, `circuit_breaker_failure_threshold`
- Routing rules: `agent_type_to_tier_mapping`

### 8.12 llm_cost_budgets

**Mission:** Cost budget management with alerting.

**Budget Types:**
- `daily`: Daily spending limit
- `weekly`: Rolling 7-day limit
- `monthly`: Calendar month limit

**Alerting:**
- Warning at 80% of budget
- Critical at 95% of budget
- Hard stop at 100% (if `is_hard_limit=true`)

### 8.13 llm_budget_alerts

**Mission:** Alert history for budget thresholds.

### 8.14 llm_audit_log

**Mission:** Audit trail for configuration changes.

**Tracked Actions:**
- Provider enable/disable
- Model configuration changes
- Circuit breaker manual overrides
- Budget updates
- Ranking weight profile changes

### 8.15 llm_response_cache

**Mission:** Optional LLM response caching for identical prompts.

**Cache Key Components:**
```
hash(agent_type + prompt_hash + model_id + temperature)
```

**Cache Policy:**
- Max age: 7 days
- Max hit count: 1000
- Eviction: LRU + TTL

---

## 📋 Domain 9: AI Telemetry (13 Tables)

**Purpose:** Comprehensive tracking of AI agent operations, costs, and performance.

### 9.1 models

**Mission:** AI model registry for cost calculation.

**Schema:**
```sql
CREATE TABLE models (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,  -- Enum: VERTEX_AI | DEEPINFRA | OPENAI
    model_name VARCHAR(100) NOT NULL,
    label VARCHAR(255),  -- User-friendly name
    is_default BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    cost_per_1k_input_tokens NUMERIC(10, 8),
    cost_per_1k_output_tokens NUMERIC(10, 8),
    max_tokens INTEGER,
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE | DEPRECATED | DISABLED
    request_count BIGINT DEFAULT 0,
    total_cost_usd NUMERIC(12, 2) DEFAULT 0,
    created_at, updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(provider, model_name)
);
```

### 9.2 llm_conversations

**Mission:** Track individual LLM API calls (different from chat_messages).

**Use Case:** Every time an agent calls an LLM, log the request details.

**Key Fields:**
```sql
- session_id VARCHAR(100)  -- Groups related calls
- model_id BIGINT REFERENCES models(id)
- provider, model_name VARCHAR  -- Denormalized for performance
- prompt_text TEXT  -- Input prompt
- response_text TEXT  -- LLM output
- input_tokens, output_tokens, total_tokens INTEGER
- cost_usd NUMERIC(10, 6)  -- Calculated cost
- latency_ms INTEGER
- status VARCHAR(20)  -- SUCCESS | RATE_LIMITED | TIMEOUT | ERROR
- error_message TEXT
- ip_address VARCHAR(45)
- user_agent TEXT
```

### 9.3 agent_model_configs

**Mission:** Agent-specific model preferences and overrides.

**Example:**
```json
{
  "agent_type": "hunter_ai",
  "provider": "VERTEX_AI",
  "model_name": "gemini-1.5-flash-001",
  "priority": 1,  // Use this model first
  "weight": 100,  // Weighted random selection
  "is_active": true,
  "cost_per_1k_input_override": 0.0001  // Override default pricing
}
```

### 9.4 agent_performance_stats

**Mission:** Rolling performance metrics per agent type.

**Time Windows:**
- `1h`: Last hour stats
- `24h`: Last 24 hours
- `all_time`: Lifetime stats

**Metrics:**
```sql
- total_requests, successful_requests, failed_requests, canceled_requests
- avg_latency_ms, avg_cost_usd, total_cost_usd
- last_updated_at
```

### 9.5 agent_executions

**Mission:** Track high-level agent workflow executions.

**Example Flow:**
1. User: "Swap 100 USDC to ETH"
2. Intent Detector → `agent_type='hunter_ai'`
3. Hunter AI execution created → `workflow_type='swap'`
4. Multiple subtasks created (price check, route optimization, execution)
5. Each subtask logged in `agent_tasks`
6. Final execution status: `COMPLETED` or `FAILED`

**Schema:**
```sql
CREATE TABLE agent_executions (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    conversation_id BIGINT REFERENCES llm_conversations(id) ON DELETE SET NULL,
    agent_type VARCHAR(50),  -- 'hunter_ai' | 'research' | 'execution' | etc.
    workflow_type VARCHAR(50),  -- 'swap' | 'portfolio_analysis' | 'earn_deposit'
    status VARCHAR(20),  -- PENDING | RUNNING | COMPLETED | FAILED | CANCELED
    input_params JSON,  -- Workflow input parameters
    output_result JSON,  -- Workflow output/results
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(10, 6),  -- Sum of all LLM costs
    execution_time_ms INTEGER,
    error_message TEXT,
    started_at, completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### 9.6 agent_tasks

**Mission:** Individual subtasks within agent executions.

**Example Subtasks for Swap Workflow:**
1. `task_type='price_check'` → Get current ETH/USDC price
2. `task_type='route_optimization'` → Find best DEX route
3. `task_type='gas_estimation'` → Estimate gas costs
4. `task_type='transaction_build'` → Build transaction
5. `task_type='transaction_execute'` → Execute on-chain

**Schema:**
```sql
CREATE TABLE agent_tasks (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT REFERENCES agent_executions(id) ON DELETE CASCADE,
    task_name VARCHAR(100),
    task_type VARCHAR(50),
    status VARCHAR(20),  -- PENDING | RUNNING | COMPLETED | FAILED | SKIPPED
    input_data JSON,
    output_data JSON,
    error_message TEXT,
    execution_time_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    started_at, completed_at, created_at TIMESTAMP WITH TIME ZONE
);
```

### 9.7 agent_tools_usage

**Mission:** Track usage of external tools/APIs by agents.

**Tools:**
- CoinGecko API (price data)
- 1inch API (swap routing)
- DeFiLlama API (protocol TVL)
- TheGraph API (subgraph queries)
- Aave API (lending rates)
- Hyperliquid API (perpetuals)

**Schema:**
```sql
CREATE TABLE agent_tools_usage (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT REFERENCES agent_executions(id) ON DELETE CASCADE,
    task_id BIGINT REFERENCES agent_tasks(id) ON DELETE SET NULL,
    tool_name VARCHAR(100),  -- 'coingecko_api' | '1inch_api' | etc.
    input_params JSON,
    output_result JSON,
    status VARCHAR(20),  -- SUCCESS | FAILED | TIMEOUT | RATE_LIMITED
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### 9.8 llm_rate_limit_events

**Mission:** Track rate limit hits for proactive capacity planning.

### 9.9 llm_cost_alerts

**Mission:** Cost threshold alerts (hourly/daily spending limits).

### 9.10 vertex_api_metrics

**Mission:** Vertex AI-specific metrics with regional tracking.

**Additional Fields:**
- `region`: 'us-central1' | 'us-east4' | etc.
- `quota_exceeded_count`: Quota limit hits
- `failover_to_bedrock_count`: Fallback events

### 9.11 deepinfra_api_metrics

**Mission:** DeepInfra-specific metrics.

### 9.12 bedrock_api_metrics

**Mission:** AWS Bedrock-specific metrics.

**Additional Fields:**
- `throttle_count`: Throttling events
- `model_not_ready_count`: Model unavailable events
- `failover_from_vertex_count`: Times used as fallback

---

## 📋 Domain 10: Distillation System (6 Tables)

**Purpose:** LLM cost optimization through response caching and static responses.

**Problem Solved:** Reduce LLM costs by 80-95% for repetitive queries using 3-tier routing:
1. **Static Responses** → Pre-defined templates (FREE)
2. **Exact Cache** → Hash-based cache for identical queries (FREE)
3. **Semantic Cache** → Vector similarity for similar queries (FREE)
4. **Light LLM** → Small/cheap model for simple queries (LOW COST)
5. **Full LLM** → Premium model for complex queries (NORMAL COST)

### 10.1 distillation_config

**Mission:** System-wide distillation configuration.

**Stored Configs:**
```json
{
  "exact_cache_ttl_hours": 168,  // 7 days
  "semantic_cache_ttl_hours": 24,
  "semantic_similarity_threshold": 0.85,
  "light_llm_complexity_threshold": 0.5,
  "enable_static_responses": true,
  "enable_exact_cache": true,
  "enable_semantic_cache": true
}
```

### 10.2 distillation_static_responses

**Mission:** Template-based responses for common queries.

**Example:**
```json
{
  "intent": "greeting",
  "variant": "morning",
  "response_template": "Good morning! How can I help you with DeFi today?",
  "template_variables": [],
  "conditions": {"time_of_day": "morning"},
  "priority": 1,
  "is_active": true
}
```

**Common Static Responses:**
- Greetings/farewells
- "What is X?" for common terms (DeFi, APY, TVL, etc.)
- Platform features overview
- Supported chains/protocols list

### 10.3 distillation_cache_exact

**Mission:** Exact match response cache.

**Cache Key:** `SHA256(normalized_query)`

**Normalization:**
- Lowercase
- Remove extra whitespace
- Strip punctuation
- Remove stop words (optional)

**Schema:**
```sql
CREATE TABLE distillation_cache_exact (
    id UUID PRIMARY KEY,
    cache_key VARCHAR(64) UNIQUE NOT NULL,
    normalized_query TEXT NOT NULL,
    intent VARCHAR(50),
    entities JSONB,  -- Extracted entities
    response_content TEXT NOT NULL,
    response_metadata JSONB,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    last_hit_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    source_model VARCHAR(100),  -- Original LLM used
    source_request_id UUID
);
```

### 10.4 distillation_cache_semantic

**Mission:** Semantic similarity-based cache using vector embeddings.

**How It Works:**
1. User query: "What's the current price of Bitcoin?"
2. Generate embedding: `embedding_model(query)` → 1536-dim vector
3. Find similar cached responses: `SELECT * WHERE cosine_similarity(query_embedding, ?) > 0.85`
4. If found: Return cached response (FREE)
5. If not found: Call LLM, cache response with embedding

**Schema:**
```sql
CREATE TABLE distillation_cache_semantic (
    id UUID PRIMARY KEY,
    query_embedding VECTOR(1536),  -- pgvector extension
    original_query TEXT NOT NULL,
    intent VARCHAR(50),
    entities JSONB,
    response_content TEXT NOT NULL,
    response_metadata JSONB,
    hit_count INTEGER DEFAULT 0,
    created_at, last_hit_at, expires_at TIMESTAMP WITH TIME ZONE,
    source_model VARCHAR(100),
    source_request_id UUID
);

-- Vector similarity index
CREATE INDEX ON distillation_cache_semantic 
USING ivfflat (query_embedding vector_cosine_ops) 
WITH (lists = 100);
```

### 10.5 distillation_requests

**Mission:** Log all distillation routing decisions.

**Routing Decision Flow:**
```
1. Classify query → {intent, complexity, entities}
2. Check static responses → Match? Return static
3. Check exact cache → Match? Return cached
4. Check semantic cache → Similarity > 0.85? Return cached
5. Route by complexity:
   - complexity < 0.5 → Light LLM (Gemini Flash)
   - complexity >= 0.5 → Full LLM (Claude Sonnet)
```

**Schema:**
```sql
CREATE TABLE distillation_requests (
    id UUID PRIMARY KEY,
    request_id VARCHAR(100) NOT NULL,
    user_id UUID,
    original_query TEXT NOT NULL,
    normalized_query TEXT,
    intent VARCHAR(50),
    intent_confidence NUMERIC(4, 3),  -- 0.000 to 1.000
    complexity VARCHAR(20),  -- 'simple' | 'moderate' | 'complex'
    entities JSONB,
    route_type VARCHAR(20) NOT NULL,  -- 'rejected' | 'static' | 'exact_cache' | 'semantic_cache' | 'light_llm' | 'full_llm'
    routing_reason TEXT,
    suggested_model_tier VARCHAR(20),  -- 'economy' | 'standard' | 'premium'
    suggested_agent VARCHAR(50),
    cache_key VARCHAR(64),
    cache_hit BOOLEAN DEFAULT FALSE,
    cache_level VARCHAR(20),  -- 'exact' | 'semantic'
    classification_latency_ms INTEGER,
    total_latency_ms INTEGER,
    was_processed BOOLEAN,
    llm_request_id UUID,  -- Links to llm_requests if LLM was used
    created_at TIMESTAMP WITH TIME ZONE
);
```

### 10.6 distillation_telemetry_hourly

**Mission:** Hourly aggregated distillation metrics.

**Cost Savings Calculation:**
```
estimated_cost_saved_usd = 
  (static_response_count + cache_hit_count) * avg_llm_cost_per_request
```

**Example Metrics:**
```json
{
  "hour_bucket": "2026-01-25T14:00:00Z",
  "total_requests": 1000,
  "rejected_count": 50,  // Invalid/spam
  "static_response_count": 200,  // 20% saved
  "exact_cache_hits": 300,  // 30% saved
  "semantic_cache_hits": 150,  // 15% saved
  "light_llm_count": 200,  // 20% low cost
  "full_llm_count": 100,  // 10% normal cost
  "cache_hit_rate": 0.45,  // 45% cache hit rate
  "avg_classification_latency_ms": 15,
  "avg_confidence": 0.87,
  "estimated_cost_saved_usd": 12.50
}
```

---

## 📋 Domain 11: Projects & Knowledge Bases (12 Tables)

**Purpose:** Multi-project platform with RAG (Retrieval Augmented Generation) capabilities.

**Use Case:** Allow organizations to create custom AI agents with project-specific knowledge bases.

### 11.1 projects

**Mission:** Project/workspace container.

**Schema:**
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,  -- 'acme-defi' | 'crypto-dao'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),  -- Emoji or icon identifier
    color VARCHAR(7),  -- Hex color code
    banner_url TEXT,
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft' | 'active' | 'archived'
    visibility VARCHAR(20) DEFAULT 'public',  -- 'public' | 'private' | 'internal'
    system_prompt TEXT NOT NULL,  -- Custom system prompt for project agent
    welcome_message TEXT,
    enabled_protocols ARRAY<TEXT>,  -- ['aave', 'curve', 'uniswap']
    enabled_chains ARRAY<TEXT>,  -- ['arbitrum', 'optimism']
    enabled_tools ARRAY<TEXT>,  -- ['swap', 'earn', 'portfolio']
    risk_config JSONB,  -- Custom risk parameters
    max_users INTEGER,  -- User limit for private projects
    display_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    created_by UUID NOT NULL,
    created_at, updated_at TIMESTAMP WITH TIME ZONE
);
```

### 11.2 project_knowledge_bases

**Mission:** Knowledge base configuration per project.

**Schema:**
```sql
- project_id UUID
- name VARCHAR(100)  -- 'Protocol Documentation' | 'Trading Strategies'
- description TEXT
- embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small'
- chunk_size INTEGER DEFAULT 500  -- Characters per chunk
- chunk_overlap INTEGER DEFAULT 50  -- Overlap for context preservation
- total_documents, total_chunks INTEGER
- status VARCHAR(20) DEFAULT 'active'
- last_indexed_at TIMESTAMP WITH TIME ZONE
```

### 11.3 project_knowledge_documents

**Mission:** Source documents for knowledge base.

**Document Types:**
- `manual`: Manually uploaded documents
- `web`: Scraped from URL
- `api`: Fetched from API
- `integration`: Synced from external system (Notion, Google Docs, etc.)

**Schema:**
```sql
- knowledge_base_id UUID
- title VARCHAR(255)
- content TEXT  -- Full document text
- doc_type VARCHAR(50)  -- 'guide' | 'faq' | 'protocol_docs' | 'strategy'
- source_url TEXT
- source_type VARCHAR(50)
- tags ARRAY<TEXT>  -- ['beginner', 'advanced', 'liquidity-pools']
- priority INTEGER DEFAULT 1  -- Retrieval priority
- is_processed BOOLEAN DEFAULT FALSE
- chunk_count INTEGER
- processing_error TEXT
```

### 11.4 project_knowledge_chunks

**Mission:** Vector embeddings for RAG retrieval.

**Chunking Strategy:**
1. Split document into 500-character chunks with 50-character overlap
2. Generate embedding for each chunk: `text-embedding-3-small` → 1536-dim vector
3. Store with metadata for retrieval

**Schema:**
```sql
CREATE TABLE project_knowledge_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    knowledge_base_id UUID NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,  -- Position in document
    embedding VECTOR(1536),  -- pgvector
    metadata JSONB,  -- {title, section, page, etc.}
    created_at TIMESTAMP WITH TIME ZONE
);

-- Vector similarity search index
CREATE INDEX ON project_knowledge_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

**RAG Query Flow:**
1. User question: "How do I provide liquidity on Curve?"
2. Generate question embedding
3. Search similar chunks: `SELECT * ORDER BY embedding <=> $1 LIMIT 5`
4. Construct prompt: `system_prompt + retrieved_chunks + user_question`
5. Send to LLM for answer

### 11.5 project_tool_configs

**Mission:** Per-project tool permissions and limits.

**Example:**
```json
{
  "project_id": "abc123",
  "tool_id": "swap",
  "is_enabled": true,
  "max_calls_per_session": 10,
  "max_amount_per_call": 1000.00,  // USDC
  "requires_confirmation": true,
  "default_params": {
    "slippage": 0.5,
    "deadline": 300
  },
  "locked_params": {
    "recipient": "0x..."  // Force recipient address
  }
}
```

### 11.6 project_chat_sessions

**Mission:** Chat sessions within projects (separate from main chat).

### 11.7 project_invitations

**Mission:** Invite users to private projects.

**Workflow:**
1. Project owner creates invitation → `status='pending'`
2. Email sent with invitation link
3. User accepts → `status='accepted'`, user added to `user_project_assignments`
4. Auto-expire after 7 days

### 11.8 project_analytics_daily

**Mission:** Daily analytics per project.

**Metrics:**
- Active users
- Message count
- Tool usage breakdown
- Avg response time
- Cost attribution

### 11.9 project_auto_assign_rules

**Mission:** Auto-assign new users to projects based on rules.

**Example Rules:**
```json
{
  "rule_type": "domain_match",
  "condition": "email.endsWith('@acme.com')",
  "target_project_id": "acme-project",
  "role": "member"
}
```

### 11.10 user_active_projects

**Mission:** Track user's currently active project.

### 11.11 user_project_assignments

**Mission:** Many-to-many relationship between users and projects.

**Roles:**
- `owner`: Full control
- `admin`: Manage users, configure project
- `member`: Use project, no admin access
- `viewer`: Read-only access

### 11.12 distillation_telemetry

**Mission:** Additional distillation metrics (different from hourly table).

---

## 📋 Domain 12: Retry & Resilience (3 Tables)

**Purpose:** Circuit breakers and retry logic for external service calls.

### 12.1 retry_attempts

**Mission:** Log individual retry attempts for failed operations.

**Schema:**
```sql
CREATE TABLE retry_attempts (
    id UUID PRIMARY KEY,
    operation_type VARCHAR(50),  -- 'blockchain_tx' | 'api_call' | 'llm_request'
    operation_id VARCHAR(255),  -- Original operation identifier
    attempt_number INTEGER,
    error_type VARCHAR(50),  -- 'timeout' | 'rate_limit' | 'server_error'
    error_message TEXT,
    retry_strategy VARCHAR(50),  -- 'exponential_backoff' | 'linear' | 'fibonacci'
    delay_ms INTEGER,  -- Delay before this attempt
    status VARCHAR(20),  -- 'retrying' | 'success' | 'failed'
    created_at TIMESTAMP WITH TIME ZONE
);
```

**Retry Strategies:**
1. **Exponential Backoff:** 100ms, 200ms, 400ms, 800ms, 1600ms
2. **Linear:** 1s, 2s, 3s, 4s, 5s
3. **Fibonacci:** 100ms, 100ms, 200ms, 300ms, 500ms, 800ms

### 12.2 retry_metrics_aggregate

**Mission:** Aggregate retry statistics per operation type.

**Metrics:**
- Total retry attempts
- Success rate after retries
- Average retry count to success
- Most common error types
- Peak retry hours

### 12.3 service_override_events

**Mission:** Manual service overrides during incidents.

**Use Case:**
"During Vertex AI outage, manually override to use DeepInfra for all agents"

**Schema:**
```sql
CREATE TABLE service_override_events (
    id UUID PRIMARY KEY,
    service_name VARCHAR(50),  -- 'vertex_ai' | '1inch_api' | 'coingecko_api'
    override_type VARCHAR(20),  -- 'disable' | 'fallback' | 'rate_limit'
    override_config JSONB,  -- Override parameters
    reason TEXT,
    created_by UUID,
    activated_at TIMESTAMP WITH TIME ZONE,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);
```

---

## 📋 Domain 13: Security & Compliance (3 Tables)

### 13.1 policies

**Mission:** Cache Privy user policies for offline validation.

**Schema:**
```sql
CREATE TABLE policies (
    id UUID PRIMARY KEY,
    privy_user_id VARCHAR(255) NOT NULL,
    policy_type VARCHAR(50),  -- 'wallet_ownership' | 'session_validity' | 'mfa_required'
    policy_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    synced_from_privy_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

**Why Cache Policies?**
- Reduce Privy API calls
- Offline policy validation
- Audit trail

### 13.2 policy_audit_events

**Mission:** Audit log for policy enforcement events.

**Events:**
- `policy_granted`: User granted new permission
- `policy_revoked`: Permission removed
- `policy_violation`: Attempted unauthorized action
- `mfa_challenge`: MFA challenge issued
- `mfa_success` / `mfa_failed`: MFA verification results

### 13.3 audit_logs

**Mission:** General audit trail for sensitive operations.

**Logged Operations:**
- User login/logout
- Wallet connections
- Large transactions (>$1000 USD)
- Admin actions
- Configuration changes

**Schema:**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID,
    action_type VARCHAR(50),
    resource_type VARCHAR(50),  -- 'user' | 'wallet' | 'transaction' | 'config'
    resource_id VARCHAR(255),
    before_value JSONB,
    after_value JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE
);
```

---

## 📋 Domain 14: Location & System Config (3 Tables)

### 14.1 countries

**Mission:** Country reference data for user location tracking.

### 14.2 cities

**Mission:** City reference data linked to countries.

### 14.3 analytics_snapshots

**Mission:** System-wide daily analytics snapshots.

**Schema:**
```sql
CREATE TABLE analytics_snapshots (
    id UUID PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    snapshot_type VARCHAR(50) NOT NULL,  -- 'daily' | 'weekly' | 'monthly'
    
    -- Portfolio state counts
    portfolio_empty_count INTEGER,
    portfolio_starter_count INTEGER,  -- $0-$100
    portfolio_active_count INTEGER,  -- $100-$10k
    portfolio_whale_count INTEGER,  -- $10k+
    
    -- Activity level counts
    activity_new_count INTEGER,  -- Signed up today
    activity_very_active_count INTEGER,  -- >10 actions/day
    activity_active_count INTEGER,  -- 1-10 actions/day
    activity_weekly_active_count INTEGER,
    activity_monthly_active_count INTEGER,
    activity_inactive_count INTEGER,  -- No actions in 30 days
    activity_reactivated_count INTEGER,  -- Returned after 30+ days
    
    -- User type counts
    type_new_user_count INTEGER,
    type_casual_count INTEGER,  -- <5 swaps total
    type_trader_count INTEGER,  -- 5-50 swaps
    type_yield_farmer_count INTEGER,  -- >50% in earn positions
    type_power_user_count INTEGER,  -- >50 swaps + earn + portfolio
    
    -- Totals
    total_users INTEGER,
    total_executions INTEGER,
    total_balance_usd NUMERIC(20, 2),
    
    -- Execution counts
    exec_swap_count INTEGER,
    exec_buy_count INTEGER,
    exec_lending_count INTEGER,
    exec_transfer_count INTEGER,
    exec_cashout_count INTEGER,
    
    -- Additional metrics
    additional_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(snapshot_date, snapshot_type)
);
```

---

## 📋 Domain 15: Agent Sessions (1 Table)

### 15.1 agent_sessions

**Mission:** Track stateful agent conversation sessions.

**Schema:**
```sql
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    session_state JSONB,  -- Current conversation state
    context_data JSONB,  -- Agent-specific context
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP WITH TIME ZONE,
    last_interaction_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE
);
```

**Use Case:**
- Hunter AI maintains state across multiple queries
- Research agent tracks fact-checking progress
- Execution agent manages multi-step transaction flows

---

## 📋 Domain 16: Lending & DeFi Borrowing (10 Components)

**Purpose:** Comprehensive lending and borrowing system supporting Aave and Morpho protocols with multi-step leverage loops, health factor monitoring, risk management, and automated alerts.

**Status:** ✅ ACTIVE - Implemented 2026-01-27 (Week 4 of lending implementation)

**Key Features:**
- Multi-protocol support (Aave, Morpho)
- Health factor monitoring with 5 risk levels
- Leverage loop execution tracking (3+ signatures per loop)
- User-specific risk preferences and safety thresholds
- Historical health check tracking for analytics
- Real-time liquidation risk alerts
- Analytical views for portfolio summaries and protocol comparisons

### 16.1 lending_positions

**Mission:** Track all active and historical lending positions across Aave and Morpho protocols with real-time health factor monitoring.

**Schema Highlights:**
```sql
CREATE TABLE lending_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES chat_users(id) ON DELETE CASCADE,
    protocol VARCHAR(20) NOT NULL,  -- 'aave' | 'morpho'
    chain VARCHAR(20) NOT NULL,  -- 'ethereum' | 'base' | 'arbitrum' | 'polygon'
    position_type VARCHAR(10) NOT NULL,  -- 'supply' | 'borrow'
    asset_address VARCHAR(66) NOT NULL,  -- Token contract address
    asset_symbol VARCHAR(20) NOT NULL,  -- USDC, ETH, WBTC, etc.
    amount NUMERIC(78, 18) NOT NULL,  -- Token amount (18 decimals precision)
    amount_usd NUMERIC(20, 2),  -- USD value at position open
    health_factor NUMERIC(10, 2),  -- Liquidation safety metric (NULL for supply-only)
    apy NUMERIC(10, 4),  -- Annual percentage yield/rate
    status VARCHAR(20) DEFAULT 'active',  -- 'active' | 'closed' | 'liquidated'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Composite indexes for fast lookups
    INDEX idx_lending_positions_user_status (user_id, status),
    INDEX idx_lending_positions_protocol_chain (protocol, chain),
    INDEX idx_lending_positions_health_factor (health_factor) WHERE health_factor IS NOT NULL
);
```

**Business Rules:**
- Health factor only applies to borrow positions (NULL for supply-only)
- Health factor < 1.0 indicates liquidation risk
- Health factor < 1.2 blocks new borrow operations (safety threshold)
- Position status transitions: `active` → `closed` (user action) or `liquidated` (protocol action)
- Amount uses NUMERIC(78,18) to handle large token amounts with 18 decimal precision

**Usage Patterns:**
- `LendingPositionRepository` for CRUD operations
- `HealthFactorMonitoringService` checks health factors every 5 minutes
- Dashboard queries aggregate positions by protocol/chain
- Liquidation detection triggers alerts when health_factor < 1.2

**Relationships:**
- Parent of: `lending_supplies`, `lending_borrows` (via position_id FK)
- Related to: `lending_health_checks` (health factor history)
- Triggers: `lending_alerts` on status changes or low health factor

### 16.2 lending_supplies

**Mission:** Track individual supply (deposit) transactions to lending protocols with APY tracking.

**Schema Highlights:**
```sql
CREATE TABLE lending_supplies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL REFERENCES lending_positions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES chat_users(id) ON DELETE CASCADE,
    protocol VARCHAR(20) NOT NULL,
    chain VARCHAR(20) NOT NULL,
    asset_address VARCHAR(66) NOT NULL,
    asset_symbol VARCHAR(20) NOT NULL,
    amount NUMERIC(78, 18) NOT NULL,  -- Supply amount
    apy NUMERIC(10, 4),  -- Supply APY at deposit time
    transaction_hash VARCHAR(66) NOT NULL,  -- Blockchain tx hash
    block_number BIGINT,  -- Block number for verification
    gas_used NUMERIC(20, 0),  -- Gas consumed (in wei)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_lending_supplies_position (position_id, created_at DESC),
    INDEX idx_lending_supplies_user (user_id, created_at DESC),
    INDEX idx_lending_supplies_tx_hash (transaction_hash)
);
```

**Business Rules:**
- Each supply creates/updates a `lending_position` with type='supply'
- APY is recorded at deposit time for historical tracking
- Transaction hash enables blockchain verification
- Gas costs tracked for user cost analytics

**Usage Patterns:**
- Created by `SupplyCommandHandler` after successful deposit
- Queried for supply history and APY performance tracking
- Aggregated for protocol yield comparison analytics

### 16.3 lending_borrows

**Mission:** Track individual borrow transactions with health factor at borrow time and interest rate tracking.

**Schema Highlights:**
```sql
CREATE TABLE lending_borrows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL REFERENCES lending_positions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES chat_users(id) ON DELETE CASCADE,
    protocol VARCHAR(20) NOT NULL,
    chain VARCHAR(20) NOT NULL,
    asset_address VARCHAR(66) NOT NULL,
    asset_symbol VARCHAR(20) NOT NULL,
    amount NUMERIC(78, 18) NOT NULL,  -- Borrow amount
    interest_rate NUMERIC(10, 4),  -- Interest rate at borrow time
    variable_rate BOOLEAN DEFAULT TRUE,  -- TRUE = variable, FALSE = stable
    health_factor_at_borrow NUMERIC(10, 2),  -- Health factor when borrow executed
    transaction_hash VARCHAR(66) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_lending_borrows_position (position_id, created_at DESC),
    INDEX idx_lending_borrows_user (user_id, created_at DESC),
    INDEX idx_lending_borrows_health_factor (health_factor_at_borrow)
);
```

**Business Rules:**
- Borrow operation BLOCKED if health_factor would drop below 1.2
- Health factor recorded at borrow time for safety auditing
- Variable vs stable rate affects interest calculation
- Must have active supply position with sufficient collateral

**Safety Features:**
- Pre-execution validation: Projected health factor must be ≥ 1.2
- Post-execution: `lending_health_checks` monitors ongoing health
- Alerts triggered if health factor drops below user preferences

### 16.4 lending_transactions

**Mission:** Comprehensive audit trail of all lending operations (supply, borrow, repay, withdraw, liquidate) with health factor change tracking.

**Schema Highlights:**
```sql
CREATE TABLE lending_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES chat_users(id) ON DELETE CASCADE,
    protocol VARCHAR(20) NOT NULL,
    chain VARCHAR(20) NOT NULL,
    action_type VARCHAR(20) NOT NULL,  -- 'supply' | 'borrow' | 'repay' | 'withdraw' | 'liquidate'
    asset_address VARCHAR(66) NOT NULL,
    asset_symbol VARCHAR(20) NOT NULL,
    amount NUMERIC(78, 18) NOT NULL,
    transaction_hash VARCHAR(66),
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'confirmed' | 'failed'
    health_factor_before NUMERIC(10, 2),  -- Health factor before operation
    health_factor_after NUMERIC(10, 2),  -- Health factor after operation
    metadata JSONB,  -- Additional context (gas price, slippage, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_lending_transactions_user_date (user_id, created_at DESC),
    INDEX idx_lending_transactions_protocol (protocol, chain, action_type),
    INDEX idx_lending_transactions_status (status) WHERE status = 'pending',
    INDEX idx_lending_transactions_tx_hash (transaction_hash)
);
```

**Business Rules:**
- All lending operations logged regardless of success/failure
- Health factor changes tracked for repay/withdraw/borrow operations
- Status lifecycle: `pending` → `confirmed` or `failed`
- Metadata stores additional context (gas estimation, user preferences)

**Usage Patterns:**
- Transaction monitoring: Celery workers update status on confirmation
- Audit trail: Complete history of user lending activity
- Analytics: Health factor change analysis, operation success rates
- Debugging: Failed transaction analysis via metadata

### 16.5 user_lending_preferences

**Mission:** User-specific risk tolerance settings and notification preferences for lending operations.

**Schema Highlights:**
```sql
CREATE TABLE user_lending_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES chat_users(id) ON DELETE CASCADE,
    risk_tolerance VARCHAR(20) DEFAULT 'moderate',  -- 'conservative' | 'moderate' | 'aggressive'
    min_health_factor NUMERIC(10, 2) DEFAULT 1.5,  -- Minimum allowed health factor
    max_leverage NUMERIC(10, 2) DEFAULT 3.0,  -- Maximum leverage for loop strategies
    preferred_protocol VARCHAR(20),  -- 'aave' | 'morpho' | NULL (no preference)
    auto_rebalance BOOLEAN DEFAULT FALSE,  -- Enable automatic position rebalancing
    notification_health_threshold NUMERIC(10, 2) DEFAULT 1.3,  -- Alert threshold
    notification_email VARCHAR(255),  -- Email for critical alerts
    notification_enabled BOOLEAN DEFAULT TRUE,  -- Enable/disable all alerts
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_user_lending_preferences_user (user_id)
);
```

**Business Rules:**
- **Conservative:** min_health_factor = 1.8, max_leverage = 2.0
- **Moderate:** min_health_factor = 1.5, max_leverage = 3.0 (default)
- **Aggressive:** min_health_factor = 1.3, max_leverage = 5.0
- Notification threshold must be ≥ min_health_factor
- Auto-rebalance triggers when health factor < notification_threshold

**Safety Integration:**
- `BorrowCommandHandler` checks min_health_factor before execution
- `LeverageLoopService` validates max_leverage before starting loops
- `HealthFactorMonitoringService` triggers alerts at notification_threshold

### 16.6 lending_health_checks

**Mission:** Historical time-series tracking of health factors and collateralization ratios for monitoring and analytics.

**Schema Highlights:**
```sql
CREATE TABLE lending_health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES chat_users(id) ON DELETE CASCADE,
    protocol VARCHAR(20) NOT NULL,
    chain VARCHAR(20) NOT NULL,
    health_factor NUMERIC(10, 2) NOT NULL,
    health_factor_level VARCHAR(20) NOT NULL,  -- Risk classification
    total_collateral_usd NUMERIC(20, 2),  -- Total collateral value
    total_debt_usd NUMERIC(20, 2),  -- Total borrowed value
    available_to_borrow_usd NUMERIC(20, 2),  -- Remaining borrowing capacity
    liquidation_price NUMERIC(20, 2),  -- Price at which liquidation occurs
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_lending_health_checks_user_date (user_id, checked_at DESC),
    INDEX idx_lending_health_checks_protocol (protocol, chain),
    INDEX idx_lending_health_checks_level (health_factor_level) WHERE health_factor_level IN ('danger', 'critical', 'liquidatable')
);
```

**Health Factor Classification:**
- **safe:** health_factor ≥ 2.0 (green)
- **caution:** 1.5 ≤ health_factor < 2.0 (yellow)
- **danger:** 1.2 ≤ health_factor < 1.5 (orange)
- **critical:** 1.0 ≤ health_factor < 1.2 (red)
- **liquidatable:** health_factor < 1.0 (critical red)

**Usage Patterns:**
- Celery scheduled task checks every 5 minutes
- Time-series data enables health factor trend analysis
- Liquidation price calculation for proactive alerts
- Historical data for user lending behavior analytics

### 16.7 leverage_loop_executions

**Mission:** Track multi-step leverage loop workflows requiring 3+ separate user signatures with detailed step tracking.

**Schema Highlights:**
```sql
CREATE TABLE leverage_loop_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES chat_users(id) ON DELETE CASCADE,
    protocol VARCHAR(20) NOT NULL,
    chain VARCHAR(20) NOT NULL,
    asset_address VARCHAR(66) NOT NULL,
    asset_symbol VARCHAR(20) NOT NULL,
    initial_amount NUMERIC(78, 18) NOT NULL,  -- Starting deposit
    target_leverage NUMERIC(10, 2) NOT NULL,  -- Desired leverage (e.g., 3.0x)
    actual_leverage NUMERIC(10, 2),  -- Achieved leverage after completion
    total_steps INTEGER NOT NULL,  -- Number of supply/borrow iterations
    current_step INTEGER DEFAULT 0,  -- Current step in execution
    steps_completed TEXT[],  -- Array of completed step descriptions
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled'
    final_health_factor NUMERIC(10, 2),  -- Health factor after loop completes
    final_collateral_usd NUMERIC(20, 2),  -- Total collateral after loop
    final_debt_usd NUMERIC(20, 2),  -- Total debt after loop
    total_gas_used NUMERIC(20, 0),  -- Cumulative gas cost
    total_cost_usd NUMERIC(10, 2),  -- Total USD cost including gas
    error_message TEXT,  -- Error details if failed
    metadata JSONB,  -- Additional context per step
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_leverage_loop_user_date (user_id, created_at DESC),
    INDEX idx_leverage_loop_status (status) WHERE status IN ('pending', 'in_progress')
);
```

**Leverage Loop Workflow:**
1. **Step 1:** User supplies initial collateral → 1 signature
2. **Step 2:** Borrow against collateral → 1 signature
3. **Step 3:** Supply borrowed assets as collateral → 1 signature
4. **Step N:** Repeat borrow/supply iterations until target leverage reached
5. Each step requires separate wallet signature (3+ signatures total)

**Business Rules:**
- Target leverage cannot exceed `user_lending_preferences.max_leverage`
- Each step validates health_factor ≥ user's min_health_factor
- Execution can be cancelled by user at any step
- Failed step halts execution and triggers alert
- Metadata tracks gas estimation vs actual per step

**Safety Features:**
- Multi-signature requirement prevents accidental large leverage
- Step-by-step health factor validation
- User can review position after each step before proceeding

### 16.8 lending_alerts

**Mission:** Real-time notification system for liquidation risks, position changes, and critical lending events.

**Schema Highlights:**
```sql
CREATE TABLE lending_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES chat_users(id) ON DELETE CASCADE,
    position_id UUID REFERENCES lending_positions(id) ON DELETE CASCADE,  -- Nullable for system alerts
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- 'info' | 'warning' | 'critical'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    health_factor NUMERIC(10, 2),  -- Current health factor if applicable
    threshold_value NUMERIC(20, 2),  -- Threshold that triggered alert
    current_value NUMERIC(20, 2),  -- Current value exceeding threshold
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,  -- When notification was sent (email/push)
    metadata JSONB,  -- Additional context
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_lending_alerts_user_unread (user_id, is_read) WHERE is_read = FALSE,
    INDEX idx_lending_alerts_severity (severity, created_at DESC) WHERE severity = 'critical',
    INDEX idx_lending_alerts_position (position_id, created_at DESC)
);
```

**Alert Types:**
- **health_factor_low** (warning/critical): Health factor below notification threshold
- **liquidation_risk** (critical): Health factor < 1.2, immediate action required
- **position_closed** (info): Supply/borrow position closed by user
- **loop_completed** (info): Leverage loop successfully completed
- **loop_failed** (warning): Leverage loop step failed
- **rate_change** (info): Significant APY/interest rate change (>10%)

**Alert Severity Levels:**
- **info:** Informational updates (position changes, loop completion)
- **warning:** Attention needed (health_factor < 1.5, loop failures)
- **critical:** Immediate action required (health_factor < 1.2, liquidation risk)

**Notification Channels:**
- In-app: All alerts stored and shown in dashboard
- Email: Critical alerts sent to `user_lending_preferences.notification_email`
- Push: (Future) Mobile push notifications for critical alerts

**Usage Patterns:**
- Created by `HealthFactorMonitoringService` when threshold breached
- Created by `LeverageLoopService` on step completion/failure
- Created by `LendingTransactionHandler` on position status changes
- Dashboard queries unread alerts via `is_read = FALSE` index

### 16.9 user_lending_summary (VIEW)

**Mission:** Aggregated analytical view for user lending dashboard with portfolio overview.

**View Definition:**
```sql
CREATE VIEW user_lending_summary AS
SELECT
    lp.user_id,
    COUNT(DISTINCT lp.id) AS total_positions,
    COUNT(DISTINCT lp.id) FILTER (WHERE lp.position_type = 'supply') AS supply_positions,
    COUNT(DISTINCT lp.id) FILTER (WHERE lp.position_type = 'borrow') AS borrow_positions,
    ARRAY_AGG(DISTINCT lp.protocol) AS protocols_used,
    SUM(lp.amount_usd) FILTER (WHERE lp.position_type = 'supply') AS total_supplied_usd,
    SUM(lp.amount_usd) FILTER (WHERE lp.position_type = 'borrow') AS total_borrowed_usd,
    MIN(lp.health_factor) FILTER (WHERE lp.health_factor IS NOT NULL) AS min_health_factor,
    AVG(lp.apy) FILTER (WHERE lp.position_type = 'supply') AS avg_supply_apy,
    AVG(lp.apy) FILTER (WHERE lp.position_type = 'borrow') AS avg_borrow_apy,
    COUNT(DISTINCT la.id) FILTER (WHERE la.severity = 'critical' AND la.is_read = FALSE) AS unread_critical_alerts,
    MAX(lp.updated_at) AS last_activity_at
FROM lending_positions lp
LEFT JOIN lending_alerts la ON la.user_id = lp.user_id
WHERE lp.status = 'active'
GROUP BY lp.user_id;
```

**Usage:**
- Powers user lending dashboard with key metrics
- Single query for portfolio overview
- Real-time calculation (no caching needed)
- Alerts integrated for notification badge count

**Dashboard Metrics:**
- Total positions and breakdown by type
- TVL (Total Value Locked) across protocols
- Average yields (supply APY, borrow interest)
- Health status (minimum health factor)
- Unread critical alerts count

### 16.10 protocol_comparison (VIEW)

**Mission:** Real-time protocol analytics for rate comparison and market intelligence.

**View Definition:**
```sql
CREATE VIEW protocol_comparison AS
SELECT
    lp.protocol,
    lp.chain,
    lp.asset_symbol,
    lp.position_type,
    COUNT(DISTINCT lp.user_id) AS unique_users,
    COUNT(lp.id) AS total_positions,
    SUM(lp.amount_usd) AS total_tvl_usd,
    AVG(lp.apy) AS avg_apy,
    MIN(lp.apy) AS min_apy,
    MAX(lp.apy) AS max_apy,
    AVG(lp.health_factor) FILTER (WHERE lp.health_factor IS NOT NULL) AS avg_health_factor,
    COUNT(lp.id) FILTER (WHERE lp.status = 'active') AS active_positions,
    COUNT(lp.id) FILTER (WHERE lp.status = 'liquidated') AS liquidated_positions,
    MAX(lp.updated_at) AS last_updated
FROM lending_positions lp
WHERE lp.status IN ('active', 'liquidated')
GROUP BY lp.protocol, lp.chain, lp.asset_symbol, lp.position_type;
```

**Usage:**
- Market Scanner Agent queries for best rates
- Protocol comparison in chat responses
- Risk analysis (liquidation rates per protocol)
- TVL tracking for protocol health

**Analytics Enabled:**
- **Best Supply APY:** `ORDER BY avg_apy DESC WHERE position_type = 'supply'`
- **Lowest Borrow Rate:** `ORDER BY avg_apy ASC WHERE position_type = 'borrow'`
- **Protocol Risk:** `liquidated_positions / total_positions ratio`
- **User Adoption:** `unique_users per protocol/chain`

---

## 🔄 Data Flow & Integration Patterns

### Pattern 1: Chat Message → Agent Execution

```mermaid
graph LR
    A[User Message] --> B[Unified Chat System]
    B --> C[Intent Detection]
    C --> D{Route Intent}
    D -->|Swap| E[Hunter AI]
    D -->|Portfolio| F[Portfolio Agent]
    D -->|Help| G[Chat Agent]
    E --> H[Agent Execution Record]
    H --> I[Agent Tasks]
    I --> J[LLM Requests]
    J --> K[Response]
    K --> L[chat_messages]

    Note1[Bridge Adapters] -.->|Backward Compat| B
    Note2[Legacy System] -.->|REMOVED 2026-01-25| Note1
```

### Pattern 2: Transaction Lifecycle

```
1. User initiates swap via chat
2. Intent detected → swap_handler_v2
3. SwapHandler creates agent_execution
4. Agent tasks: price_check → route_optimization → gas_estimation
5. Each task may call llm_requests for AI guidance
6. Transaction built and submitted
7. Transaction record created (status='pending')
8. Celery worker monitors confirmation
9. Transaction confirmed → update status='confirmed'
10. Update token_holdings and portfolio_snapshot
11. Notify user via notifications table
```

### Pattern 3: LLM Orchestration Flow

```
1. Agent needs LLM response
2. Check distillation_cache_exact → Hit? Return cached
3. Check distillation_cache_semantic → Hit? Return cached
4. Create llm_requests record (status='pending')
5. Check circuit_breakers → Provider healthy?
6. Query agent_model_rankings for best model
7. Send request to selected provider
8. Log attempt in llm_request_attempts
9. On failure: retry with fallback provider
10. On success: update rankings, cache response
11. Update llm_telemetry_hourly
```

---

## ✅ Legacy System Removal Completed

**Completion Date:** 2026-01-25 (4 months ahead of original 2026-06-01 deadline)

**Successfully Removed Components:**

### Files Deleted (2026-01-25):
1. ✅ **Legacy Router** (`chat/router.py`) - 1,070 lines deleted
   - Old endpoints: `/api/v1/user/chat/*` - Fully removed
2. ✅ **Legacy Mappings** - All deleted:
   - `conversation.py` - INTEGER-based conversations table
   - `message.py` - INTEGER-based messages table
   - `session.py` - Old session model
3. ✅ **Legacy Adapters** - 457 lines deleted:
   - `conversation_repository_sqla.py` (339 lines)
   - `message_repository_sqla.py` (118 lines)

### Replacement Components (Active):
1. ✅ **Unified Chat System** - UUID-based modern architecture
   - Tables: `chat_conversations`, `chat_messages`, `chat_users`, `chat_rate_limits`
   - Endpoints: `/api/v1/conversations/*`
2. ✅ **Bridge Adapters** - Backward compatibility layer
   - `conversation_repository_bridge.py` (191 lines)
   - `message_repository_bridge.py` (129 lines)
   - Maintains compatibility for existing commands without legacy tables
3. ✅ **Auth Sessions** - Modern session management
   - Table: `auth_sessions`
   - Replaced legacy `sessions` table

**Code Reduction:** ~1,200 lines of deprecated code eliminated

**Migration Guide:** Historical reference in `/docs/DEPRECATION_PLAN.md`

---

## 📊 Performance Optimization Strategies

### Indexing Strategy

**High-Priority Indexes:**

```sql
-- Chat performance
CREATE INDEX idx_chat_messages_conversation ON chat_messages(conversation_id, created_at DESC);
CREATE INDEX idx_chat_conversations_user ON chat_conversations(chat_user_id, created_at DESC);

-- Transaction lookups
CREATE INDEX idx_transactions_user_date ON transactions(user_id, created_at DESC);
CREATE INDEX idx_transactions_chain_hash ON transactions(chain, tx_hash);
CREATE INDEX idx_transactions_wallet ON transactions(wallet_id, created_at DESC);

-- Agent telemetry
CREATE INDEX idx_agent_executions_user ON agent_executions(user_id, created_at DESC);
CREATE INDEX idx_agent_tasks_execution ON agent_tasks(execution_id, status);
CREATE INDEX idx_llm_requests_agent ON llm_requests(agent_type, created_at DESC);

-- LLM orchestration
CREATE INDEX idx_llm_requests_status ON llm_requests(status, created_at DESC);
CREATE INDEX idx_circuit_breakers_state ON circuit_breakers(state) WHERE state != 'closed';

-- Portfolio tracking
CREATE INDEX idx_token_holdings_user ON token_holdings(user_id, chain);
CREATE INDEX idx_portfolio_snapshots_user_date ON portfolio_snapshots(user_id, snapshot_date DESC);

-- Vector similarity searches
CREATE INDEX idx_semantic_cache_embedding ON distillation_cache_semantic 
    USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_knowledge_chunks_embedding ON project_knowledge_chunks 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Partitioning Strategy

**Candidate Tables for Partitioning:**

1. **llm_conversations** (by created_at, monthly partitions)
2. **agent_executions** (by created_at, monthly partitions)
3. **transactions** (by created_at, monthly partitions)
4. **llm_requests** (by created_at, weekly partitions)
5. **llm_telemetry_hourly** (by hour_bucket, monthly partitions)
6. **audit_logs** (by created_at, quarterly partitions)

**Example Partitioning:**

```sql
-- Partition llm_conversations by month
CREATE TABLE llm_conversations (
    id BIGSERIAL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

CREATE TABLE llm_conversations_2026_01 
    PARTITION OF llm_conversations 
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE llm_conversations_2026_02 
    PARTITION OF llm_conversations 
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### Denormalization Strategy

**Already Denormalized:**
- ✅ `chat_conversations.message_count` (avoids COUNT query)
- ✅ `llm_requests.estimated_cost_usd` (pre-calculated)
- ✅ `agent_executions.total_cost_usd` (sum of subtask costs)
- ✅ `portfolio_snapshots.total_value_usd` (pre-calculated daily)

**Future Denormalization Opportunities:**
- Add `wallet.total_balance_usd` (sum across all chains)
- Add `user.total_portfolio_value_usd` (current value)
- Add `project.total_message_count` (across all sessions)

---

## 🔒 Security Considerations

### Sensitive Data Protection

**Encrypted Fields:**
- `users.password` → bcrypt hashed
- `moonpay_customer_tokens.encrypted_token` → AES-256 encrypted
- Privy credentials stored externally, not in DB

**PII Data:**
- `users.email` → Masked in logs
- `users.last_ip`, `users.registration_ip` → Retention policy (30 days)
- `guest_users.ip_address` → Hashed for rate limiting

### Access Control

**Row-Level Security (RLS):**

```sql
-- Example: Users can only see their own transactions
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY transactions_user_isolation ON transactions
    FOR ALL
    TO app_user
    USING (user_id = current_setting('app.current_user_id')::INTEGER);
```

### Audit Requirements

**Compliance Logging:**
- All user authentication events → `audit_logs`
- All transactions >$1000 USD → `audit_logs`
- All wallet connections → `user_events`
- All admin actions → `policy_audit_events`

**Retention Policies:**
- `audit_logs`: 7 years (regulatory requirement)
- `llm_conversations`: 1 year
- `agent_executions`: 6 months
- `retry_attempts`: 30 days

---

## 📈 Scaling Projections

### Current Scale (as of 2026-01-25)

- Total tables: 87 (84 in production)
- Total users: ~5,000
- Daily transactions: ~500
- Daily LLM requests: ~10,000
- Database size: ~5 GB

### 6-Month Projection (Q3 2026)

- Total users: ~50,000 (10x growth)
- Daily transactions: ~5,000 (10x growth)
- Daily LLM requests: ~100,000 (10x growth)
- Database size: ~50 GB (10x growth)

**Scaling Actions Required:**
1. ✅ Implement table partitioning (llm_conversations, agent_executions)
2. ✅ Add read replicas for reporting queries
3. ✅ Implement connection pooling (PgBouncer)
4. ⚠️ Consider moving hot data to Redis (distillation cache)
5. ⚠️ Implement archival strategy for old data (>1 year)

### 12-Month Projection (Q1 2027)

- Total users: ~200,000 (40x growth)
- Daily transactions: ~20,000 (40x growth)
- Daily LLM requests: ~500,000 (50x growth)
- Database size: ~200 GB (40x growth)

**Scaling Actions Required:**
1. Implement sharding strategy (shard by user_id)
2. Move LLM telemetry to TimescaleDB or ClickHouse
3. Implement CDC (Change Data Capture) for real-time analytics
4. Consider Aurora PostgreSQL with auto-scaling

---

## 🚀 Future Enhancements

### Planned Tables (Not Yet Implemented)

1. **referral_programs** - User referral tracking
2. **achievement_badges** - Gamification system
3. **trading_competitions** - Leaderboards and contests
4. **social_feeds** - Social trading features
5. **market_alerts** - Price/liquidity alerts
6. **api_keys** - User API key management
7. **webhooks** - Event webhook subscriptions
8. **backup_wallets** - Wallet recovery mechanisms

### Planned Optimizations

1. **Read Replicas** - Separate analytics queries from transactional load
2. **Materialized Views** - Pre-computed dashboards and reports
3. **Event Sourcing** - Track state changes for transactions
4. **CQRS Separation** - Separate write DB from read DB

---

## 📝 Maintenance Procedures

### Daily Operations

1. **Vacuum & Analyze**
```sql
VACUUM ANALYZE llm_conversations;
VACUUM ANALYZE agent_executions;
VACUUM ANALYZE transactions;
```

2. **Index Maintenance**
```sql
REINDEX TABLE CONCURRENTLY llm_requests;
```

3. **Cache Cleanup**
```sql
DELETE FROM distillation_cache_exact WHERE expires_at < NOW();
DELETE FROM distillation_cache_semantic WHERE expires_at < NOW();
DELETE FROM llm_response_cache WHERE expires_at < NOW();
```

### Weekly Operations

1. **Partition Management**
```sql
-- Create next month's partition
CREATE TABLE llm_conversations_2026_03 
    PARTITION OF llm_conversations 
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
```

2. **Statistics Update**
```sql
ANALYZE;
```

### Monthly Operations

1. **Data Archival**
```sql
-- Archive old agent executions to cold storage
INSERT INTO archive.agent_executions 
SELECT * FROM agent_executions 
WHERE created_at < NOW() - INTERVAL '6 months';

DELETE FROM agent_executions 
WHERE created_at < NOW() - INTERVAL '6 months';
```

2. **Compliance Reports**
```sql
-- Generate monthly audit report
SELECT * FROM audit_logs 
WHERE created_at >= date_trunc('month', NOW() - INTERVAL '1 month')
  AND created_at < date_trunc('month', NOW());
```

---

## ✅ Validation & Testing

### Data Integrity Checks

```sql
-- Check for orphaned records
SELECT COUNT(*) FROM chat_messages 
WHERE conversation_id NOT IN (SELECT id FROM chat_conversations);

-- Check for invalid foreign keys
SELECT COUNT(*) FROM transactions 
WHERE wallet_id NOT IN (SELECT id FROM wallets);

-- Check for duplicate cache keys
SELECT cache_key, COUNT(*) 
FROM distillation_cache_exact 
GROUP BY cache_key 
HAVING COUNT(*) > 1;
```

### Performance Benchmarks

**Target Query Times:**
- User portfolio fetch: <50ms
- Conversation history: <100ms
- Agent execution history: <200ms
- LLM request stats: <500ms
- Vector similarity search: <200ms

**Load Testing:**
- Concurrent users: 1,000
- Transactions per second: 100
- LLM requests per second: 500
- Database connections: 200 max

---

## 📚 References

**Internal Documentation:**
- `/docs/DEPRECATION_PLAN.md` - Legacy system migration guide
- `/docs/AGENT_SQUAD_VERTEX_DEEPINFRA.md` - AI agent configuration
- `/docs/HUNTER_AI_DATA_SOURCES.md` - Data source integration
- `/docs/GUEST_CHAT_SYSTEM.md` - Guest chat implementation

**External Resources:**
- PostgreSQL 16 Documentation
- SQLAlchemy 2.0 Documentation
- pgvector Extension Documentation
- TimescaleDB Best Practices

---

## 🎯 Conclusion

This database architecture supports a **comprehensive multi-agent DeFi platform** with:

- ✅ **87 tables** across **15 functional domains**
- ✅ **Hexagonal architecture** with clean separation of concerns
- ✅ **Enterprise LLM orchestration** with 15 tables managing multi-provider AI
- ✅ **Advanced cost optimization** via distillation system (6 tables)
- ✅ **Project-based RAG** for customized knowledge bases (12 tables)
- ✅ **Comprehensive telemetry** tracking 18 specialized agents (13 tables)
- ✅ **Multi-chain support** across 10+ blockchains
- ✅ **Guest-first experience** with IP-based tracking
- ✅ **Scalability** via partitioning, denormalization, and indexing strategies

**Key Architectural Strengths:**
1. **Separation of Concerns**: Clear domain boundaries prevent tight coupling
2. **Future-Proof**: Extensible JSONB fields allow schema evolution
3. **Cost-Aware**: Comprehensive LLM cost tracking and optimization
4. **Performance-Optimized**: Strategic indexing and denormalization
5. **Compliance-Ready**: Audit logs and retention policies

**Next Steps:**
1. Implement missing 3 tables (87 mapped → 87 in DB)
2. Set up table partitioning for high-volume tables
3. Configure read replicas for analytics workloads
4. Implement archival strategy for old data
5. Deploy monitoring and alerting for database health

---

**Document Version:** 2.0  
**Last Updated:** 2026-01-25  
**Status:** Complete - All 87 Tables Documented
