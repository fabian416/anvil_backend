# 🚀 Anvil Database Quick Reference

## Schema Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ANVIL DATABASE SCHEMA                        │
│                         27 Tables - MySQL 8.0+                       │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  1. USER MANAGEMENT  │  ──────────────────────┐
└──────────────────────┘                         │
                                                 │
    users (1)                                    │
    └── id, uid, privy_user_id                  │
    └── email, role, status, kyc_status         │
                                                 │
                                                 │
┌──────────────────────┐                         │
│  2. WALLET & CHAIN   │  ──────────────────────┤
└──────────────────────┘                         │
                                                 │
    users (1) ←→ (1) wallets                    │
                     └── id, address             │
                     └── privy_wallet_id         │
                     │                           │
                     └→ (many) chain_addresses   │
                         └── chain, address      │
                         └── balance_usd         │
                                                 │
┌──────────────────────┐                         │
│  3. TRANSACTIONS     │  ──────────────────────┤
└──────────────────────┘                         │
                                                 │
    transactions                                 │
    └── type: SWAP, FUND, EARN, SAVE            │
    └── status: PENDING, SUCCESS, FAILED        │
    └── asset_in, asset_out, amounts            │
    └── tx_hash, fee, dex_aggregator            │
                                                 │
┌──────────────────────┐                         │
│  4. DEFI OPERATIONS  │  ──────────────────────┤
└──────────────────────┘                         │
                                                 │
    hyperliquid_positions                        │
    └── symbol, side, leverage                   │
    └── entry_price, liquidation_price          │
    └── unrealized_pnl, status                  │
                                                 │
    earn_positions                              │
    └── protocol, asset, amount_deposited       │
    └── current_value, apy, rewards_earned      │
                                                 │
    save_schedules                              │
    └── frequency, amount, next_execution_at    │
    └── destination_protocol, status            │
                                                 │
┌─────────────────────────┐                      │
│  5. PAYMENTS & SUBS     │  ───────────────────┤
└─────────────────────────┘                      │
                                                 │
    funding_transactions                         │
    └── stripe_payment_intent_id                │
    └── amount_fiat, amount_crypto              │
    └── status, transaction_hash                │
                                                 │
    subscriptions                               │
    └── stripe_subscription_id                  │
    └── plan, status, trial_end                 │
                                                 │
    subscription_payments                       │
    └── stripe_invoice_id, amount               │
    └── status, billing_reason                  │
                                                 │
┌─────────────────────────┐                      │
│  6. AI & AGENTS         │  ───────────────────┤
└─────────────────────────┘                      │
                                                 │
    llm_conversations                            │
    └── model_id, provider, model_name          │
    └── prompt_text, response_text              │
    └── input_tokens, output_tokens, cost_usd   │
                                                 │
    agent_executions                            │
    └── agent_type, workflow_type               │
    └── total_tasks, completed_tasks            │
    └── total_cost_usd, status                  │
    │                                            │
    ├→ (many) agent_tasks                       │
    │   └── task_name, task_type, status        │
    │                                            │
    └→ (many) agent_tools_usage                 │
        └── tool_name, execution_time_ms        │
                                                 │
    llm_rate_limit_events                       │
    llm_cost_alerts                             │
    conversation_feedback                       │
    vertex_api_metrics                          │
    bedrock_api_metrics                         │
                                                 │
┌─────────────────────────┐                      │
│  7. SYSTEM CONFIG       │  ───────────────────┤
└─────────────────────────┘                      │
                                                 │
    models                                      │
    └── provider, model_name, label             │
    └── is_default, is_available                │
    └── cost_per_1k_input/output_tokens         │
                                                 │
    settings                                    │
    └── key, value, scope, is_sensitive         │
    └── description, updated_by                 │
                                                 │
    audit_logs                                  │
    └── actor_user_id, action, entity           │
    └── entity_id, payload_json                 │
                                                 │
┌─────────────────────────┐                      │
│  8. NOTIFICATIONS       │  ───────────────────┘
└─────────────────────────┘
    
    notifications
    └── type, channel, title, message
    └── status, priority, sent_at, read_at
```

## Key Relationships

### Core Relationships
```
users (1) ─── (1) wallets ─── (many) chain_addresses
  │
  ├─── (many) transactions
  ├─── (many) hyperliquid_positions
  ├─── (many) earn_positions
  ├─── (many) save_schedules
  ├─── (many) funding_transactions
  ├─── (1) subscriptions ─── (many) subscription_payments
  ├─── (many) llm_conversations
  ├─── (many) agent_executions ─── (many) agent_tasks
  │                           └─── (many) agent_tools_usage
  ├─── (many) notifications
  └─── (many) audit_logs
```

## Common Queries

### 1. Get User Dashboard Data

```sql
-- User profile with wallet
SELECT 
    u.id, u.uid, u.email, u.firstname, u.lastname,
    u.role, u.status, u.kyc_status,
    w.address AS wallet_address,
    w.default_chain
FROM users u
LEFT JOIN wallets w ON u.id = w.user_id
WHERE u.id = ? AND u.status = 1;

-- Wallet balances across chains
SELECT 
    ca.chain,
    ca.address,
    ca.balance_usd,
    ca.last_balance_update
FROM chain_addresses ca
INNER JOIN wallets w ON ca.wallet_id = w.id
WHERE w.user_id = ? AND ca.is_active = TRUE;

-- Recent transactions
SELECT 
    id, type, chain, asset_in, amount_in, 
    asset_out, amount_out, tx_hash, status, created_at
FROM transactions
WHERE user_id = ?
ORDER BY created_at DESC
LIMIT 20;
```

### 2. Monitor Active Positions

```sql
-- Open perpetual positions
SELECT 
    id, symbol, side, leverage, size,
    entry_price, mark_price, liquidation_price,
    unrealized_pnl, margin,
    CASE 
        WHEN side = 'long' THEN 
            ROUND(((liquidation_price - mark_price) / mark_price) * 100, 2)
        ELSE 
            ROUND(((mark_price - liquidation_price) / mark_price) * 100, 2)
    END AS distance_to_liquidation_pct
FROM hyperliquid_positions
WHERE user_id = ? AND status = 'open'
ORDER BY distance_to_liquidation_pct ASC;

-- Active earn positions
SELECT 
    id, protocol, chain, asset,
    amount_deposited, current_value,
    rewards_earned, rewards_earned_usd,
    apy, current_apy,
    DATEDIFF(NOW(), deposited_at) as days_active
FROM earn_positions
WHERE user_id = ? AND status = 'active'
ORDER BY current_value DESC;
```

### 3. AI Cost Analytics

```sql
-- Daily AI spending by user
SELECT 
    DATE(created_at) as date,
    provider,
    model_name,
    COUNT(*) as conversation_count,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(cost_usd) as total_cost_usd
FROM llm_conversations
WHERE user_id = ?
  AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(created_at), provider, model_name
ORDER BY date DESC, total_cost_usd DESC;

-- Most expensive conversations
SELECT 
    id, session_id, model_name,
    input_tokens, output_tokens, cost_usd,
    latency_ms, created_at
FROM llm_conversations
WHERE user_id = ?
ORDER BY cost_usd DESC
LIMIT 10;

-- Total AI spending
SELECT 
    COUNT(*) as total_conversations,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(cost_usd) as total_cost_usd,
    AVG(cost_usd) as avg_cost_per_conversation,
    AVG(latency_ms) as avg_latency_ms
FROM llm_conversations
WHERE user_id = ?
  AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### 4. Agent Execution Monitoring

```sql
-- Recent agent workflows
SELECT 
    ae.id,
    ae.agent_type,
    ae.workflow_type,
    ae.status,
    ae.total_tasks,
    ae.completed_tasks,
    ae.failed_tasks,
    ae.total_cost_usd,
    ae.execution_time_ms,
    ae.created_at,
    lc.prompt_text as user_request
FROM agent_executions ae
LEFT JOIN llm_conversations lc ON ae.conversation_id = lc.id
WHERE ae.user_id = ?
ORDER BY ae.created_at DESC
LIMIT 20;

-- Failed agent executions
SELECT 
    id, agent_type, workflow_type,
    error_message, created_at
FROM agent_executions
WHERE user_id = ?
  AND status = 'failed'
  AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY created_at DESC;

-- Agent performance metrics
SELECT 
    agent_type,
    workflow_type,
    COUNT(*) as total_executions,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    ROUND(AVG(execution_time_ms), 0) as avg_time_ms,
    ROUND(SUM(total_cost_usd), 4) as total_cost
FROM agent_executions
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY agent_type, workflow_type
ORDER BY total_executions DESC;
```

### 5. Transaction Analysis

```sql
-- Transaction summary by type
SELECT 
    CASE type
        WHEN 0 THEN 'SWAP'
        WHEN 1 THEN 'FUND'
        WHEN 2 THEN 'EARN'
        WHEN 3 THEN 'SAVE'
        WHEN 4 THEN 'SUBSCRIPTION'
    END as transaction_type,
    COUNT(*) as total_count,
    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as failed,
    SUM(fee_usd) as total_fees_paid
FROM transactions
WHERE user_id = ?
GROUP BY type;

-- Pending transactions (need monitoring)
SELECT 
    id, type, chain, asset_in, amount_in,
    tx_hash, created_at,
    TIMESTAMPDIFF(MINUTE, created_at, NOW()) as minutes_pending
FROM transactions
WHERE status = 0
  AND created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
ORDER BY created_at ASC;

-- Failed transactions for retry
SELECT 
    id, type, chain, asset_in, amount_in,
    error_message, created_at
FROM transactions
WHERE status = 2
  AND user_id = ?
  AND created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY created_at DESC;
```

### 6. Subscription & Payment Status

```sql
-- User subscription details
SELECT 
    s.id,
    s.stripe_subscription_id,
    s.plan,
    s.status,
    s.price_monthly,
    s.billing_cycle_start,
    s.billing_cycle_end,
    s.trial_end,
    s.cancel_at_period_end,
    COUNT(sp.id) as payment_count,
    SUM(CASE WHEN sp.status = 'paid' THEN sp.amount ELSE 0 END) as total_paid
FROM subscriptions s
LEFT JOIN subscription_payments sp ON s.id = sp.subscription_id
WHERE s.user_id = ?
GROUP BY s.id;

-- Payment history
SELECT 
    id, stripe_invoice_id, amount,
    status, billing_reason, paid_at, created_at
FROM subscription_payments
WHERE user_id = ?
ORDER BY created_at DESC;

-- Failed payments requiring attention
SELECT 
    sp.id,
    sp.stripe_invoice_id,
    sp.amount,
    sp.created_at,
    u.email,
    u.firstname,
    u.lastname
FROM subscription_payments sp
INNER JOIN users u ON sp.user_id = u.id
WHERE sp.status = 'failed'
  AND sp.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY sp.created_at DESC;
```

### 7. Scheduled Saves Execution

```sql
-- Saves due for execution
SELECT 
    id, user_id, chain, asset, amount,
    frequency, destination_protocol,
    next_execution_at, execution_count
FROM save_schedules
WHERE status = 'active'
  AND next_execution_at <= NOW()
ORDER BY next_execution_at ASC;

-- User's active save schedules
SELECT 
    id, chain, asset, amount, frequency,
    destination_protocol, next_execution_at,
    total_saved, execution_count,
    CASE 
        WHEN max_executions IS NULL THEN 'Unlimited'
        ELSE CONCAT(max_executions - execution_count, ' remaining')
    END as executions_remaining
FROM save_schedules
WHERE user_id = ?
  AND status = 'active'
ORDER BY next_execution_at ASC;
```

### 8. Notifications & Alerts

```sql
-- Unread notifications
SELECT 
    id, type, channel, title, message,
    priority, created_at
FROM notifications
WHERE user_id = ?
  AND status IN ('sent', 'pending')
  AND read_at IS NULL
ORDER BY 
    CASE priority
        WHEN 'urgent' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    created_at DESC;

-- Failed notifications for retry
SELECT 
    id, type, channel, title,
    error_message, created_at
FROM notifications
WHERE status = 'failed'
  AND created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
ORDER BY priority ASC, created_at ASC;
```

### 9. Admin Analytics Queries

```sql
-- Platform-wide statistics
SELECT 
    (SELECT COUNT(*) FROM users WHERE status = 1) as active_users,
    (SELECT COUNT(*) FROM transactions WHERE DATE(created_at) = CURDATE()) as transactions_today,
    (SELECT SUM(cost_usd) FROM llm_conversations WHERE DATE(created_at) = CURDATE()) as ai_cost_today,
    (SELECT COUNT(*) FROM agent_executions WHERE DATE(created_at) = CURDATE()) as agent_runs_today,
    (SELECT SUM(amount_fiat) FROM funding_transactions WHERE status = 'completed' AND DATE(created_at) = CURDATE()) as funding_today,
    (SELECT COUNT(*) FROM subscriptions WHERE status = 'active') as active_subscriptions;

-- Top spenders (AI cost)
SELECT 
    u.id,
    u.email,
    u.firstname,
    u.lastname,
    COUNT(lc.id) as conversation_count,
    SUM(lc.cost_usd) as total_ai_cost
FROM users u
INNER JOIN llm_conversations lc ON u.id = lc.user_id
WHERE lc.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY u.id
ORDER BY total_ai_cost DESC
LIMIT 10;

-- Transaction success rates by chain
SELECT 
    chain,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) as failed,
    ROUND(AVG(CASE WHEN status = 1 THEN 1 ELSE 0 END) * 100, 2) as success_rate_pct
FROM transactions
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY chain;

-- Model usage and costs
SELECT 
    m.provider,
    m.model_name,
    m.label,
    COUNT(lc.id) as request_count,
    SUM(lc.input_tokens) as total_input_tokens,
    SUM(lc.output_tokens) as total_output_tokens,
    SUM(lc.cost_usd) as total_cost,
    AVG(lc.latency_ms) as avg_latency_ms
FROM models m
LEFT JOIN llm_conversations lc ON m.id = lc.model_id
WHERE lc.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY m.id
ORDER BY total_cost DESC;
```

### 10. Audit & Compliance Queries

```sql
-- Recent admin actions
SELECT 
    al.id,
    u.email as admin_email,
    al.action,
    al.entity,
    al.entity_id,
    al.created_at
FROM audit_logs al
INNER JOIN users u ON al.actor_user_id = u.id
WHERE al.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY al.created_at DESC
LIMIT 50;

-- KYC approval audit trail
SELECT 
    al.id,
    u.email as admin_email,
    al.entity_id as user_id,
    al.payload_json->>'$.before.kyc_status' as before_status,
    al.payload_json->>'$.after.kyc_status' as after_status,
    al.created_at
FROM audit_logs al
INNER JOIN users u ON al.actor_user_id = u.id
WHERE al.entity = 'user'
  AND JSON_EXTRACT(al.payload_json, '$.after.kyc_status') IS NOT NULL
ORDER BY al.created_at DESC;

-- Settings change history
SELECT 
    al.id,
    u.email as admin_email,
    al.payload_json->>'$.key' as setting_key,
    al.payload_json->>'$.before.value' as old_value,
    al.payload_json->>'$.after.value' as new_value,
    al.created_at
FROM audit_logs al
INNER JOIN users u ON al.actor_user_id = u.id
WHERE al.entity = 'setting'
ORDER BY al.created_at DESC;
```

## Enum Reference

### User Roles
```
0 = ADMIN    - Full CRUD access
1 = AUDITOR  - Read-only console access
2 = CLIENT   - Standard mobile user
```

### Status Values
```
0 = INACTIVE  - Pending, not active
1 = ACTIVE    - Currently active
2 = DELETED   - Soft deleted
```

### Transaction Types
```
0 = SWAP         - DEX token swap
1 = FUND         - Fiat-to-crypto deposit
2 = EARN         - Yield farming deposit
3 = SAVE         - Auto-save execution
4 = SUBSCRIPTION - Pro subscription payment
```

### Transaction Status
```
0 = PENDING  - Submitted to blockchain
1 = SUCCESS  - Confirmed on-chain
2 = FAILED   - Transaction failed
```

### Chains
```
arbitrum    - Arbitrum One (Layer 2)
base        - Base (Coinbase L2)
hyperliquid - Hyperliquid L1
```

### Position Side
```
long  - Bullish (betting price goes up)
short - Bearish (betting price goes down)
```

### Position Status
```
open       - Active position
closed     - Manually closed by user
liquidated - Auto-closed due to liquidation
```

### Notification Channels
```
push   - Firebase Cloud Messaging (FCM)
email  - SendGrid
in_app - In-app notification center
sms    - Twilio SMS
```

### Notification Priority
```
low    - Send within 1 hour
medium - Send within 15 minutes
high   - Send within 5 minutes
urgent - Send within 30 seconds
```

## Index Strategy

### Critical Indexes (Must Have)

```sql
-- User lookups
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_privy_user_id ON users(privy_user_id);

-- Wallet queries
CREATE INDEX idx_user_id ON wallets(user_id);
CREATE INDEX idx_address ON wallets(address);

-- Transaction history
CREATE INDEX idx_user_created ON transactions(user_id, created_at);
CREATE INDEX idx_tx_hash ON transactions(tx_hash);
CREATE INDEX idx_status ON transactions(status);

-- AI cost tracking
CREATE INDEX idx_user_created ON llm_conversations(user_id, created_at);
CREATE INDEX idx_session_id ON llm_conversations(session_id);

-- Agent monitoring
CREATE INDEX idx_user_id ON agent_executions(user_id);
CREATE INDEX idx_status ON agent_executions(status);

-- Scheduled saves
CREATE INDEX idx_status_next_execution ON save_schedules(status, next_execution_at);

-- Audit trail
CREATE INDEX idx_actor_created ON audit_logs(actor_user_id, created_at);
CREATE INDEX idx_entity ON audit_logs(entity);
```

## Performance Tips

### Query Optimization
1. **Always use indexes** - Ensure WHERE clauses use indexed columns
2. **Limit result sets** - Use LIMIT for pagination
3. **Avoid SELECT *** - Specify only needed columns
4. **Use JOINs wisely** - Inner join when possible, left join when needed
5. **Analyze slow queries** - Review `slow_query_log` weekly

### Database Configuration
```ini
# Recommended for 8GB RAM server
innodb_buffer_pool_size = 4G
innodb_log_file_size = 512M
max_connections = 200
```

### Connection Pooling
- Min: 10 connections
- Max: 50 connections
- Timeout: 30 seconds

## Backup Strategy

### Automated Backups
- **Full Backup:** Daily at 2 AM UTC
- **Incremental:** Every 6 hours
- **Transaction Logs:** Every hour
- **Retention:** 30 days full, 7 days incremental

### Manual Backup
```bash
# Full database backup
mysqldump -u root -p \
  --single-transaction \
  --routines \
  --triggers \
  anvil_production > anvil_backup_$(date +%Y%m%d).sql

# Restore from backup
mysql -u root -p anvil_production < anvil_backup_20251116.sql
```

## Emergency Procedures

### 1. Database Connection Issues
```sql
-- Check active connections
SHOW PROCESSLIST;

-- Kill long-running queries
KILL <process_id>;

-- Check max connections
SHOW VARIABLES LIKE 'max_connections';
```

### 2. Disk Space Full
```bash
# Check disk usage
df -h

# Find large tables
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.TABLES
WHERE table_schema = 'anvil_production'
ORDER BY size_mb DESC;

# Archive old data
-- Move old llm_conversations to archive table
-- Delete notifications older than 90 days
```

### 3. High AI Costs
```sql
-- Disable expensive models temporarily
UPDATE models 
SET is_available = FALSE 
WHERE model_name IN ('gemini-1.5-pro', 'claude-3-5-sonnet-v2');

-- Check cost alerts
SELECT * FROM llm_cost_alerts 
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY actual_cost_usd DESC;
```

### 4. Failed Transactions Spike
```sql
-- Identify failing chain
SELECT chain, COUNT(*) as failed_count
FROM transactions
WHERE status = 2 
  AND created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY chain;

-- Check error messages
SELECT error_message, COUNT(*) as count
FROM transactions
WHERE status = 2
  AND created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY error_message;
```

## Contact & Support

- **Database Issues:** db-team@anvil.com
- **Performance:** devops@anvil.com
- **Security:** security@anvil.com
- **Documentation:** https://docs.anvil.com/database

---

**Version:** 2.0  
**Last Updated:** November 16, 2025  
**Status:** Production Ready
