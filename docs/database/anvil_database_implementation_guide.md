# 🗄️ Anvil Complete Database Schema - Implementation Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Database Architecture](#database-architecture)
3. [Section 1: User Management](#section-1-user-management)
4. [Section 2: Wallet & Multi-Chain](#section-2-wallet--multi-chain)
5. [Section 3: Transactions](#section-3-transactions)
6. [Section 4: DeFi Operations](#section-4-defi-operations)
7. [Section 5: Payments & Subscriptions](#section-5-payments--subscriptions)
8. [Section 6: AI & Agents - Telemetry](#section-6-ai--agents---telemetry)
9. [Section 7: System Configuration](#section-7-system-configuration)
10. [Section 8: Notifications](#section-8-notifications)
11. [Database Relationships](#database-relationships)
12. [Indexes & Performance](#indexes--performance)
13. [Security & Compliance](#security--compliance)
14. [Background Jobs](#background-jobs)
15. [Implementation Checklist](#implementation-checklist)

---

## Overview

**Database Name:** `anvil_production`  
**Engine:** MySQL 8.0+  
**Character Set:** utf8mb4  
**Collation:** utf8mb4_unicode_ci  
**Total Tables:** 27  
**Last Updated:** November 16, 2025

### Database Summary by Category

| Category | Tables | Purpose |
|----------|--------|---------|
| User Management | 1 | Authentication, KYC, roles |
| Wallet & Multi-Chain | 2 | Privy wallets, cross-chain addresses |
| Transactions | 1 | All on-chain activity |
| DeFi Operations | 3 | Perpetuals, yield farming, auto-save |
| Payments & Subscriptions | 3 | Stripe integration, subscriptions |
| AI & Agents Telemetry | 9 | LLM tracking, agent monitoring, costs |
| System Configuration | 3 | Settings, models, audit logs |
| Notifications | 1 | Multi-channel notifications |

### Estimated Database Size

- **1,000 users, 1 year:** ~500 MB
- **Growth rate:** ~40-50 MB/month
- **Critical tables:** `llm_conversations`, `agent_executions`, `transactions`, `hyperliquid_positions`

---

## Database Architecture

### Technology Stack

- **Primary Database:** MySQL 8.0+ (InnoDB engine)
- **Wallet Provider:** Privy (MPC embedded wallets)
- **Payment Processor:** Stripe
- **AI Providers:** Google Cloud Vertex AI, AWS Bedrock
- **Notification Services:** FCM (push), SendGrid (email), Twilio (SMS)

### Key Design Principles

1. **Multi-Chain Support:** Separate chain addresses table for cross-chain operations
2. **Audit Trail:** Immutable audit logs for compliance
3. **Cost Tracking:** Comprehensive AI/LLM cost monitoring
4. **Soft Deletes:** User data preserved with `deleted_at` timestamp
5. **Encryption:** Sensitive settings encrypted at rest with AES-256
6. **Foreign Keys:** Full referential integrity with cascading deletes

---

## Section 1: User Management

### Table: `users`

**Purpose:** Core user accounts with authentication, roles, and KYC management.

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT | Primary key (auto-increment) |
| `uid` | VARCHAR(36) | UUID for external systems (unique) |
| `privy_user_id` | VARCHAR(255) | Privy DID identifier (unique) |
| `email` | VARCHAR(255) | User email (unique, required) |
| `role` | TINYINT | 0=ADMIN, 1=AUDITOR, 2=CLIENT |
| `status` | TINYINT | 0=INACTIVE, 1=ACTIVE, 2=DELETED |
| `kyc_status` | ENUM | 'none', 'pending', 'approved', 'rejected' |

#### Business Rules

- **One user per email:** Email must be unique across system
- **Privy Integration:** `privy_user_id` links to Privy's authentication service
- **Role Hierarchy:**
  - `ADMIN (0)`: Full CRUD access to all resources
  - `AUDITOR (1)`: Read-only access to admin console
  - `CLIENT (2)`: Standard mobile app user
- **Status Workflow:**
  - `INACTIVE (0)`: Newly created, pending email verification
  - `ACTIVE (1)`: Can use all app features
  - `DELETED (2)`: Soft-deleted, data retained for compliance
- **KYC Workflow:**
  - New users start with `kyc_status='none'`
  - Required before high-value transactions (>$1000)
  - Admin approval required for KYC completion

#### Indexes

```sql
INDEX idx_email (email)
INDEX idx_uid (uid)
INDEX idx_privy_user_id (privy_user_id)
INDEX idx_role_status (role, status)
INDEX idx_created_at (created_at)
```

---

## Section 2: Wallet & Multi-Chain

### Table: `wallets`

**Purpose:** Primary wallet records linked to Privy embedded wallets with MPC key management.

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT | Primary key |
| `user_id` | BIGINT | Foreign key to users |
| `privy_wallet_id` | VARCHAR(255) | Privy's internal wallet ID |
| `address` | VARCHAR(42) | Primary wallet address (0x...) |
| `provider` | VARCHAR(20) | Always 'privy' in MVP |
| `default_chain` | ENUM | 'arbitrum', 'base', 'hyperliquid' |

#### Business Rules

- **One wallet per user:** Each user has exactly one primary wallet
- **Privy MPC:** Private keys never exist on device or backend
- **Wallet Creation:** Automatically created on user signup via Privy SDK
- **Address Format:** Ethereum-compatible (0x...) for EVM chains

### Table: `chain_addresses`

**Purpose:** Multi-chain address mapping for cross-chain wallet operations.

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT | Primary key |
| `wallet_id` | BIGINT | Foreign key to wallets |
| `chain` | ENUM | 'arbitrum', 'base', 'hyperliquid' |
| `address` | VARCHAR(255) | Chain-specific address |
| `balance_usd` | DECIMAL(20,2) | Cached balance in USD |
| `last_balance_update` | TIMESTAMP | Last RPC fetch time |

#### Business Rules

- **One address per chain:** Unique constraint on `(wallet_id, chain)`
- **Address Formats:**
  - Arbitrum/Base: Same EVM address (0x...)
  - Hyperliquid: Custom format (hype...)
- **Balance Caching:** Updated every 5 minutes by background job
- **Active Status:** Can disable chains temporarily per user

#### Relationships

```
users (1) ←→ (1) wallets (1) ←→ (many) chain_addresses
```

---

## Section 3: Transactions

### Table: `transactions`

**Purpose:** Complete audit trail of all blockchain transactions across all chains and types.

#### Transaction Types

| Type | Value | Description |
|------|-------|-------------|
| SWAP | 0 | DEX token swaps |
| FUND | 1 | Fiat-to-crypto deposits |
| EARN | 2 | Yield farming deposits |
| SAVE | 3 | Auto-save recurring deposits |
| SUBSCRIPTION | 4 | Pro subscription payments |

#### Status Workflow

| Status | Value | Description | Next Actions |
|--------|-------|-------------|--------------|
| PENDING | 0 | Transaction submitted | Monitor for confirmation |
| SUCCESS | 1 | Confirmed on-chain | Display in activity feed |
| FAILED | 2 | Transaction failed | Show error, allow retry |

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `asset_in` | VARCHAR(20) | Input token (e.g., "USDC") |
| `amount_in` | DECIMAL(30,18) | Input amount |
| `asset_out` | VARCHAR(20) | Output token (e.g., "ETH") |
| `amount_out` | DECIMAL(30,18) | Output amount |
| `tx_hash` | VARCHAR(66) | Blockchain transaction hash |
| `dex_aggregator` | VARCHAR(50) | '1inch', '0x', 'hyperliquid' |
| `dex_route` | JSON | Pool routing details |

#### Business Rules

- **Immutable Records:** SUCCESS transactions cannot be modified
- **Monitoring:** Background job checks PENDING transactions every 30 seconds
- **Retry Logic:** FAILED transactions can be retried with adjusted parameters
- **Activity Feed:** All SUCCESS transactions visible in user's Activity tab
- **DEX Routing:** Store complete routing path for debugging/optimization

#### Example JSON for `dex_route`

```json
{
  "protocol": "1inch",
  "route": [
    {
      "pool": "Uniswap V3",
      "tokenIn": "USDC",
      "tokenOut": "ETH",
      "percentage": 100
    }
  ],
  "estimatedGas": "150000",
  "priceImpact": "0.12"
}
```

---

## Section 4: DeFi Operations

### Table: `hyperliquid_positions`

**Purpose:** Track perpetual trading positions on Hyperliquid L1 with real-time PnL monitoring.

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | VARCHAR(20) | 'ETH-USD', 'BTC-USD', 'SOL-USD' |
| `side` | ENUM | 'long' (bullish), 'short' (bearish) |
| `leverage` | DECIMAL(5,2) | 1.0 to 20.0 (e.g., 5.0 = 5x) |
| `entry_price` | DECIMAL(20,8) | Average entry price USD |
| `liquidation_price` | DECIMAL(20,8) | Auto-close price threshold |
| `unrealized_pnl` | DECIMAL(20,8) | Current profit/loss |
| `status` | ENUM | 'open', 'closed', 'liquidated' |

#### Critical Monitoring

**Liquidation Alerts:**
- Background job checks every 30 seconds
- Alert sent if price within 5% of liquidation price
- Urgent priority notification (push + email)

#### PnL Calculation

```
unrealized_pnl = (mark_price - entry_price) × size × side_multiplier
where side_multiplier = 1 for long, -1 for short
```

### Table: `earn_positions`

**Purpose:** Track yield farming positions across DeFi protocols (Aave, Compound, Curve).

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `protocol` | VARCHAR(50) | 'aave', 'compound', 'curve', 'uniswap-v3' |
| `amount_deposited` | DECIMAL(30,18) | Initial deposit |
| `current_value` | DECIMAL(30,18) | Current value with rewards |
| `apy` | DECIMAL(8,4) | APY at deposit time |
| `current_apy` | DECIMAL(8,4) | Current APY (updated hourly) |
| `rewards_earned` | DECIMAL(30,18) | Total rewards earned |

#### Background Jobs

- **Update Position Value:** Every hour
  - Fetch current balance from protocol
  - Calculate rewards earned
  - Update `current_value` and `rewards_earned`
  
- **Update APY:** Every hour
  - Fetch current APY from protocol
  - Update `current_apy`
  
- **Emergency Withdrawal:** On-demand
  - Admin can force withdraw if protocol compromised
  - Sets status to `emergency_exit`

### Table: `save_schedules`

**Purpose:** Automated recurring savings with configurable frequency.

#### Frequency Options

| Frequency | Description | Execution Logic |
|-----------|-------------|-----------------|
| daily | Every day at same time | `next_execution_at` += 1 day |
| weekly | Specific day of week | `next_execution_at` += 7 days |
| biweekly | Every 2 weeks | `next_execution_at` += 14 days |
| monthly | Specific day of month | `next_execution_at` += 1 month |

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `frequency` | ENUM | Execution frequency |
| `day_of_week` | TINYINT | 0=Sun, 1=Mon, ..., 6=Sat |
| `day_of_month` | TINYINT | 1-31 (for monthly) |
| `next_execution_at` | TIMESTAMP | When to run next |
| `execution_count` | INT | Times executed so far |
| `max_executions` | INT | Max runs (null = infinite) |

#### Execution Flow

```
1. Cron job runs every hour
2. Query: WHERE status='active' AND next_execution_at <= NOW()
3. For each schedule:
   a. Execute save transaction
   b. Update execution_count++
   c. Update total_saved += amount
   d. Calculate next_execution_at based on frequency
   e. If execution_count >= max_executions, set status='completed'
   f. On error, set status='failed', log error_message
```

---

## Section 5: Payments & Subscriptions

### Table: `funding_transactions`

**Purpose:** Fiat-to-crypto purchases via Stripe (credit card, ACH, bank transfer).

#### Payment Flow

```
1. User initiates funding request → Frontend
2. Create Stripe PaymentIntent → Backend calls Stripe API
3. Record in funding_transactions (status='pending')
4. User completes payment → Stripe hosted page
5. Stripe webhook → Backend updates status='processing'
6. Execute on-chain purchase → DEX aggregator
7. Transaction confirmed → Update status='completed', set transaction_hash
8. Notify user → Push notification
```

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `stripe_payment_intent_id` | VARCHAR(255) | Stripe PaymentIntent ID |
| `amount_fiat` | DECIMAL(10,2) | USD amount paid |
| `amount_crypto` | DECIMAL(30,18) | Crypto received |
| `asset` | VARCHAR(20) | 'USDC', 'ETH', 'USDT' |
| `payment_method` | VARCHAR(50) | 'card', 'bank_transfer', 'ach' |
| `fee_stripe` | DECIMAL(10,2) | Stripe's processing fee |
| `fee_network` | DECIMAL(10,2) | Gas fee for on-chain |

#### Status Workflow

| Status | Description | Next Action |
|--------|-------------|-------------|
| pending | Payment initiated | Wait for Stripe confirmation |
| processing | Payment confirmed, executing on-chain | Monitor blockchain |
| completed | Crypto delivered to wallet | Send notification |
| failed | Payment or on-chain tx failed | Refund via Stripe |
| refunded | Refund processed | Close ticket |

### Table: `subscriptions`

**Purpose:** Pro subscription management with Stripe recurring billing.

#### Subscription Plans

| Plan | Price | Features |
|------|-------|----------|
| free | $0/mo | Basic features, 10 conversations/day |
| pro | $9.99/mo | Unlimited conversations, priority support |

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `stripe_subscription_id` | VARCHAR(255) | Stripe Subscription ID |
| `plan` | ENUM | 'free', 'pro' |
| `status` | ENUM | 'active', 'past_due', 'canceled', 'trialing' |
| `trial_end` | TIMESTAMP | Trial expiration date |
| `cancel_at_period_end` | BOOLEAN | Cancel at next billing cycle |

#### Subscription Lifecycle

```
1. User subscribes → Create Stripe Subscription
2. Record in subscriptions (status='trialing' if trial enabled)
3. Stripe webhook 'invoice.paid' → Update status='active'
4. Recurring billing → subscription_payments record created
5. User cancels → Set cancel_at_period_end=TRUE
6. Period ends → Stripe webhook → Update status='canceled'
```

### Table: `subscription_payments`

**Purpose:** Individual subscription payment history for accounting.

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `stripe_invoice_id` | VARCHAR(255) | Stripe Invoice ID |
| `amount` | DECIMAL(10,2) | Payment amount |
| `billing_reason` | VARCHAR(50) | 'subscription_create', 'subscription_cycle' |
| `status` | ENUM | 'paid', 'pending', 'failed', 'refunded' |

---

## Section 6: AI & Agents - Telemetry

### Overview

This section tracks all AI-related activity including:
- LLM conversations (Vertex AI, Bedrock)
- Agent workflow executions
- Tool usage by agents
- Cost tracking and alerts
- Rate limiting events
- User feedback

### Table: `llm_conversations`

**Purpose:** Complete chat history with cost tracking for every AI request.

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | VARCHAR(100) | Frontend session ID |
| `model_id` | BIGINT | FK to models table |
| `provider` | VARCHAR(20) | 'vertex', 'bedrock' |
| `model_name` | VARCHAR(100) | Exact model name |
| `prompt_text` | TEXT | User's input |
| `response_text` | TEXT | AI's output |
| `input_tokens` | INT | Prompt token count |
| `output_tokens` | INT | Response token count |
| `cost_usd` | DECIMAL(10,6) | Request cost |
| `latency_ms` | INT | Response time |

#### Cost Calculation

```
cost_usd = (input_tokens / 1000 × input_price) + 
           (output_tokens / 1000 × output_price)
           
where prices from models table:
  - cost_per_1k_input_tokens
  - cost_per_1k_output_tokens
```

#### Status Values

| Status | Description |
|--------|-------------|
| success | Request completed successfully |
| failed | Request failed (error in prompt or service) |
| rate_limited | Provider rate limit hit |
| fallback | Failed on primary, succeeded on fallback |

### Table: `agent_executions`

**Purpose:** Track multi-step AI agent workflow executions.

#### Agent Types

| Agent Type | Purpose |
|------------|---------|
| research | Market research, price analysis |
| risk | Risk assessment, position sizing |
| execution | Trade execution, transaction submission |
| analysis | Portfolio analysis, performance reports |

#### Workflow Types

| Workflow | Description |
|----------|-------------|
| swap | Token swap execution |
| buy | Buy crypto with fiat |
| sell | Sell crypto to fiat |
| earn | Deposit to yield protocol |
| save | Execute recurring save |
| analysis | Generate portfolio report |

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `agent_type` | VARCHAR(50) | Agent category |
| `workflow_type` | VARCHAR(50) | Workflow category |
| `total_tasks` | INT | Number of tasks in workflow |
| `completed_tasks` | INT | Successfully completed |
| `failed_tasks` | INT | Failed tasks |
| `total_cost_usd` | DECIMAL(10,6) | Total AI cost |
| `execution_time_ms` | INT | Total time |

#### Example Execution Flow

```
1. User: "Swap 100 USDC for ETH"
2. Create agent_execution (workflow_type='swap', status='pending')
3. Tasks created:
   - Task 1: Price research (agent_type='research')
   - Task 2: Risk check (agent_type='risk')
   - Task 3: Execute swap (agent_type='execution')
4. Each task:
   - Create agent_tasks record
   - Execute task (may use multiple tools)
   - Record tool usage in agent_tools_usage
   - Update task status
5. All tasks complete → Update execution status='completed'
```

### Table: `agent_tasks`

**Purpose:** Individual tasks within an agent workflow.

#### Task Types

- **research:** Fetch prices, analyze trends, compare options
- **validation:** Check balances, verify limits, assess risk
- **execution:** Submit transactions, monitor confirmations
- **notification:** Send alerts, update user

### Table: `agent_tools_usage`

**Purpose:** Track which tools agents use and their performance.

#### Common Tool Names

- `price_feed` - Fetch current token prices
- `swap_quote` - Get DEX swap quote
- `balance_check` - Check wallet balance
- `gas_estimator` - Estimate transaction gas
- `risk_calculator` - Calculate position risk
- `position_monitor` - Check position status

### Cost Monitoring Tables

#### Table: `llm_rate_limit_events`

Tracks rate limiting from AI providers to optimize usage and implement failover.

#### Table: `llm_cost_alerts`

Automated alerts when costs exceed thresholds:
- Daily threshold: $50 (configurable)
- Weekly threshold: $300
- Monthly threshold: $1000
- User spike: 10x normal usage

#### Table: `vertex_api_metrics` & `bedrock_api_metrics`

Hourly aggregated metrics for monitoring:
- Request counts
- Token consumption
- Costs
- Error rates
- Latency percentiles (avg, p95, p99)
- Failover counts

---

## Section 7: System Configuration

### Table: `models`

**Purpose:** AI model configuration and availability management.

#### Default Models (Seeded)

**Vertex AI:**
- `gemini-1.5-flash` (default) - Fast & cheap
- `gemini-1.5-pro` - Balanced performance
- `gemini-2.0-flash-exp` - Experimental

**AWS Bedrock:**
- `claude-3-5-sonnet-v2` (default) - High quality
- `claude-3-5-haiku` - Fast responses
- `llama3-1-70b` - Open source option

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `is_default` | BOOLEAN | Default for provider |
| `is_available` | BOOLEAN | Currently available |
| `cost_per_1k_input_tokens` | DECIMAL(10,8) | Input pricing |
| `cost_per_1k_output_tokens` | DECIMAL(10,8) | Output pricing |
| `max_tokens` | INT | Token limit |
| `request_count` | BIGINT | Total requests |
| `total_cost_usd` | DECIMAL(12,2) | Cumulative cost |

### Table: `settings`

**Purpose:** System-wide configuration key-value store.

#### Setting Scopes

| Scope | Value | Purpose |
|-------|-------|---------|
| GLOBAL | 0 | General system settings |
| SECURITY | 1 | Auth, encryption, API keys |
| PAYMENTS | 2 | Stripe, payment processing |
| AI | 3 | LLM, model configuration |

#### Security Best Practices

- **Sensitive Settings:** Set `is_sensitive=TRUE` for:
  - API keys
  - Secrets
  - Encryption keys
  - Database credentials
  
- **Encryption:** Sensitive values encrypted at rest with AES-256
- **Access Control:** Only ADMIN role can update settings
- **Audit Trail:** All changes logged in `audit_logs`

#### Important Settings (Pre-configured)

```sql
-- Global
max_daily_trade_limit = 5000
max_position_size = 10000
min_balance_threshold = 10

-- Security (REPLACE WITH ACTUAL VALUES)
jwt_secret = 'REPLACE_WITH_SECURE_SECRET'
privy_app_id = 'REPLACE_WITH_PRIVY_APP_ID'
privy_app_secret = 'REPLACE_WITH_PRIVY_SECRET'

-- Payments
stripe_api_key = 'REPLACE_WITH_STRIPE_KEY'
funding_fee_percentage = 1.5

-- AI
daily_cost_alert_threshold = 50
max_tokens_per_request = 4000
```

### Table: `audit_logs`

**Purpose:** Immutable audit trail for compliance and security.

#### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `actor_user_id` | BIGINT | Admin who performed action |
| `action` | VARCHAR(100) | 'create', 'update', 'delete', 'approve', 'reject' |
| `entity` | VARCHAR(100) | 'user', 'transaction', 'setting', 'model' |
| `entity_id` | VARCHAR(100) | ID of affected record |
| `payload_json` | JSON | Complete before/after values |

#### Business Rules

- **Immutable:** Never delete or modify audit logs
- **Required for:**
  - All admin actions
  - Payment processing
  - Agent executions with transactions
  - Settings changes
- **Retention:** 7 years for compliance
- **PII Handling:** IP addresses stored, treat as PII under GDPR

#### Example Payload

```json
{
  "request_body": {"status": 1},
  "request_params": {"id": "12345"},
  "before": {"status": 0, "role": 2},
  "after": {"status": 1, "role": 2},
  "response_status": 200,
  "reason": "Manual KYC approval"
}
```

---

## Section 8: Notifications

### Table: `notifications`

**Purpose:** Multi-channel notification queue with delivery tracking.

#### Notification Types

| Type | Priority | Channels | Description |
|------|----------|----------|-------------|
| transaction_confirmed | medium | push, in_app | TX successful |
| transaction_failed | medium | push, in_app | TX failed |
| liquidation_warning | urgent | push, email, sms | Position near liquidation |
| deposit_completed | medium | push, in_app | Funding complete |
| subscription_renewed | low | email | Subscription charged |
| kyc_approved | medium | email, in_app | KYC approved |
| system_alert | high | push, email | System maintenance |

#### Channels

| Channel | Provider | Use Case |
|---------|----------|----------|
| push | Firebase FCM | Immediate alerts |
| email | SendGrid | Detailed notifications |
| in_app | Direct DB | Dashboard alerts |
| sms | Twilio | Critical urgent alerts |

#### Status Workflow

```
1. Create notification (status='pending')
2. Background worker picks up (every minute)
3. Send via appropriate channel
4. Update status='sent', set sent_at
5. If in_app, track when user opens (read_at)
6. On error, status='failed', log error_message
```

#### Priority Handling

- **urgent:** Send immediately (within 30 seconds)
- **high:** Send within 5 minutes
- **medium:** Send within 15 minutes
- **low:** Send within 1 hour

---

## Database Relationships

### Entity Relationship Diagram

```
users (1) ←→ (1) wallets
  │             │
  │             └─→ (many) chain_addresses
  │
  ├─→ (many) transactions
  ├─→ (many) hyperliquid_positions
  ├─→ (many) earn_positions
  ├─→ (many) save_schedules
  ├─→ (many) funding_transactions
  ├─→ (1) subscriptions ─→ (many) subscription_payments
  ├─→ (many) llm_conversations
  ├─→ (many) agent_executions
  │       │
  │       ├─→ (many) agent_tasks
  │       └─→ (many) agent_tools_usage
  │
  ├─→ (many) notifications
  └─→ (many) audit_logs (as actor)

models (1) ←─ (many) llm_conversations
         └─ (many) vertex_api_metrics
         └─ (many) bedrock_api_metrics
```

### Foreign Key Constraints

#### Cascading Deletes (ON DELETE CASCADE)

When parent deleted, children automatically deleted:
- `users` → `wallets`, `transactions`, `llm_conversations`, `agent_executions`, `notifications`
- `wallets` → `chain_addresses`, `transactions`, `earn_positions`, `save_schedules`
- `agent_executions` → `agent_tasks`, `agent_tools_usage`
- `subscriptions` → `subscription_payments`

#### Set NULL (ON DELETE SET NULL)

When parent deleted, foreign key set to NULL:
- `llm_conversations` → `agent_executions.conversation_id`
- `agent_tasks` → `agent_tools_usage.task_id`
- `users` → `settings.updated_by`
- `users` → `llm_rate_limit_events.user_id`

---

## Indexes & Performance

### Critical Indexes

#### Foreign Key Indexes
All foreign key columns automatically indexed by InnoDB.

#### Composite Indexes for Common Queries

```sql
-- User transactions query
INDEX idx_user_created (user_id, created_at) ON transactions

-- Active positions lookup
INDEX idx_user_status (user_id, status) ON hyperliquid_positions

-- Scheduled saves execution
INDEX idx_status_next_execution (status, next_execution_at) ON save_schedules

-- Cost tracking by user
INDEX idx_user_created (user_id, created_at) ON llm_conversations

-- Audit log searches
INDEX idx_actor_created (actor_user_id, created_at) ON audit_logs
```

#### Time-based Indexes

All tables with `created_at` have index for time-range queries:
```sql
INDEX idx_created_at (created_at)
```

### Query Optimization Tips

1. **Use covering indexes** - Include commonly selected columns in index
2. **Avoid SELECT *** - Specify needed columns only
3. **Partition large tables** - Consider partitioning by date for `llm_conversations`, `transactions`
4. **Use EXPLAIN** - Analyze query plans before deploying
5. **Cache frequently accessed data** - Use Redis for hot data

### Maintenance Schedule

```sql
-- Weekly
ANALYZE TABLE users, wallets, transactions, llm_conversations;

-- Monthly
OPTIMIZE TABLE users, wallets, transactions;

-- Quarterly
-- Review slow query log
-- Add indexes for common slow queries
-- Archive old audit logs (>1 year)
```

---

## Security & Compliance

### Encryption

#### At Rest
- **Database Level:** Enable MySQL encryption at rest
- **Column Level:** 
  - `users.password_hash` - Bcrypt
  - `settings.value` (when `is_sensitive=TRUE`) - AES-256

#### In Transit
- **SSL/TLS:** All database connections must use TLS 1.2+
- **Certificate Pinning:** Pin database server certificate

### PII Data (GDPR Compliance)

#### Tables Containing PII

| Table | PII Fields | Retention |
|-------|-----------|-----------|
| users | email, firstname, lastname, phone | Active + 7 years after deletion |
| llm_conversations | prompt_text, response_text, ip_address | 1 year |
| audit_logs | ip_address, user_agent | 7 years |
| notifications | title, message | 90 days |

#### User Data Export (GDPR Article 15)

Provide complete data export including:
- User profile
- Wallet addresses
- Transaction history
- AI conversation history
- Subscription history
- Notification preferences

#### Right to be Forgotten (GDPR Article 17)

1. Set `users.status = 2` (soft delete)
2. Set `users.deleted_at = NOW()`
3. Anonymize PII fields:
   - Set email to `deleted_user_{id}@anvil.deleted`
   - Clear firstname, lastname, phone
4. Keep transaction records (regulatory requirement)
5. Purge AI conversations after 30 days
6. Keep audit logs (compliance requirement)

### Access Control

#### Database Users

```sql
-- Application user (read/write)
CREATE USER 'anvil_app'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON anvil_production.* TO 'anvil_app'@'%';

-- Read-only analytics user
CREATE USER 'anvil_analytics'@'%' IDENTIFIED BY 'secure_password';
GRANT SELECT ON anvil_production.* TO 'anvil_analytics'@'%';

-- Admin user (DDL operations)
CREATE USER 'anvil_admin'@'%' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON anvil_production.* TO 'anvil_admin'@'%';
```

### Audit Requirements

#### Mandatory Audit Events

All these actions must create `audit_logs` entry:
- User status changes
- KYC approvals/rejections
- Settings updates
- Model configuration changes
- Emergency withdrawals
- Payment refunds
- Subscription cancellations

---

## Background Jobs

### Scheduled Tasks

#### Every 30 Seconds
- Monitor pending transactions for confirmations
- Check liquidation prices for open positions
- Update mark prices for perpetuals

#### Every 5 Minutes
- Refresh chain balances via RPC
- Check failed transactions for retry

#### Every Hour
- Execute scheduled saves (`save_schedules`)
- Update earn position values and APY
- Aggregate AI metrics (vertex_api_metrics, bedrock_api_metrics)
- Process notification queue

#### Daily
- Generate cost alert reports
- Archive old notifications (>90 days)
- Update user activity stats
- Calculate daily AI spending by user

#### Weekly
- Analyze slow queries
- Optimize frequently accessed tables
- Review and alert on anomalous user behavior

### Job Implementation

Use a job queue system like:
- **Celery** (Python)
- **Bull** (Node.js)
- **Sidekiq** (Ruby)

Example job configuration:
```python
# Celery Beat Schedule
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'monitor-liquidations': {
        'task': 'jobs.monitor_liquidations',
        'schedule': 30.0,  # Every 30 seconds
    },
    'refresh-balances': {
        'task': 'jobs.refresh_balances',
        'schedule': 300.0,  # Every 5 minutes
    },
    'execute-scheduled-saves': {
        'task': 'jobs.execute_scheduled_saves',
        'schedule': crontab(minute='0'),  # Every hour
    },
}
```

---

## Implementation Checklist

### Phase 1: Database Setup

- [ ] Install MySQL 8.0+ on server
- [ ] Execute `anvil_complete_database_implementation.sql`
- [ ] Verify all 27 tables created successfully
- [ ] Check foreign key relationships: `SELECT * FROM information_schema.table_constraints`
- [ ] Verify indexes: `SHOW INDEX FROM <table_name>`

### Phase 2: Security Configuration

- [ ] Replace all `REPLACE_WITH_*` values in `settings` table with actual credentials
- [ ] Configure database users with appropriate privileges
- [ ] Enable MySQL SSL/TLS encryption
- [ ] Set up AES-256 encryption for sensitive settings
- [ ] Configure database firewall rules (allow only application servers)
- [ ] Enable binary logging for point-in-time recovery

### Phase 3: Initial Data

- [ ] Verify default models inserted (6 models)
- [ ] Verify default settings inserted (15 settings)
- [ ] Create first admin user manually
- [ ] Test user authentication flow

### Phase 4: Integration Testing

- [ ] Test Privy wallet creation flow
- [ ] Test multi-chain address generation
- [ ] Test transaction recording (all types)
- [ ] Test notification delivery
- [ ] Test AI conversation logging
- [ ] Test agent execution workflow

### Phase 5: Monitoring & Backup

- [ ] Set up automated backups (daily full, hourly incremental)
- [ ] Configure database monitoring (CPU, memory, connections)
- [ ] Set up slow query logging
- [ ] Configure cost alerts
- [ ] Test backup restore procedure

### Phase 6: Performance Tuning

- [ ] Configure MySQL parameters (see `my.cnf` recommendations in SQL file)
- [ ] Set `innodb_buffer_pool_size` = 70% of RAM
- [ ] Test query performance with EXPLAIN
- [ ] Add additional indexes based on slow query log
- [ ] Configure connection pooling (20-50 connections)

### Phase 7: Production Readiness

- [ ] Load test with simulated traffic
- [ ] Verify all background jobs running correctly
- [ ] Test failover procedures (database replication)
- [ ] Document operational runbooks
- [ ] Train team on database administration
- [ ] Set up 24/7 monitoring and alerting

---

## Performance Tuning

### MySQL Configuration (`my.cnf`)

```ini
[mysqld]
# Memory
innodb_buffer_pool_size = 4G           # 70% of available RAM
innodb_log_file_size = 512M
tmp_table_size = 256M
max_heap_table_size = 256M

# Connections
max_connections = 200
max_connect_errors = 100

# Performance
innodb_flush_log_at_trx_commit = 2    # Better performance
innodb_flush_method = O_DIRECT
innodb_file_per_table = 1

# Replication (if using)
server_id = 1
log_bin = /var/log/mysql/mysql-bin.log
binlog_format = ROW
expire_logs_days = 7

# Monitoring
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow-query.log
long_query_time = 2                    # Log queries > 2 seconds
```

### Connection Pool Settings

**Recommended:**
- Min connections: 10
- Max connections: 50
- Connection timeout: 30 seconds
- Idle timeout: 600 seconds

---

## Troubleshooting

### Common Issues

#### 1. Slow Queries on `transactions` Table

**Solution:** Ensure composite index exists:
```sql
CREATE INDEX idx_user_created ON transactions(user_id, created_at);
```

#### 2. High AI Costs

**Check:**
```sql
-- Daily costs by model
SELECT 
    provider,
    model_name,
    COUNT(*) as requests,
    SUM(cost_usd) as total_cost
FROM llm_conversations
WHERE DATE(created_at) = CURDATE()
GROUP BY provider, model_name
ORDER BY total_cost DESC;
```

#### 3. Failed Transactions Not Retrying

**Check:**
```sql
SELECT * FROM transactions 
WHERE status = 2 
AND created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)
ORDER BY created_at DESC;
```

#### 4. Notification Queue Backlog

**Check:**
```sql
SELECT 
    channel,
    priority,
    COUNT(*) as pending_count,
    MIN(created_at) as oldest
FROM notifications
WHERE status = 'pending'
GROUP BY channel, priority;
```

---

## Support & Resources

### Documentation
- MySQL 8.0: https://dev.mysql.com/doc/refman/8.0/en/
- Privy: https://docs.privy.io/
- Stripe: https://stripe.com/docs/api
- Vertex AI: https://cloud.google.com/vertex-ai/docs
- AWS Bedrock: https://docs.aws.amazon.com/bedrock/

### Monitoring Tools
- **Database:** MySQL Enterprise Monitor, Percona Monitoring
- **Performance:** New Relic, DataDog
- **Logs:** ELK Stack, CloudWatch Logs

### Contact
For database-related questions or issues, contact:
- **Database Team:** db-team@anvil.com
- **DevOps:** devops@anvil.com
- **Security:** security@anvil.com

---

**Last Updated:** November 16, 2025  
**Version:** 2.0  
**Document Status:** Production Ready
