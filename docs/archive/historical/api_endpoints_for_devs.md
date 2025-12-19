# 🔌 Anvil API - Endpoints Summary for Development Team

## Technical Specification for Software Factory

**Base URL:** `https://api.anvil.com/v1`  
**API Version:** v1.0  
**Authentication:** JWT Bearer Token  
**Content-Type:** `application/json`

---

## 📊 Overview

| User Type | Endpoints | HTTP Methods | Access Level |
|-----------|-----------|--------------|--------------|
| **CLIENT** | 35 | GET, POST, PATCH, DELETE | Personal data only |
| **ADMIN** | 15 | GET, POST, PATCH, DELETE | Full CRUD access |
| **AUDITOR** | 13 | GET, POST (exports) | Read-only |
| **TOTAL** | **63** | - | - |

---

## 🎯 CLIENT Endpoints (35 total)

### Authentication (3 endpoints)

```http
POST   /api/v1/user/auth/privy        # Login with Privy token
POST   /api/v1/user/auth/refresh      # Refresh access token  
POST   /api/v1/user/auth/logout       # Logout and invalidate token
```

**Key Points:**
- Privy DID authentication
- JWT tokens (1-hour expiry)
- Refresh tokens (30-day expiry)

---

### User Profile (2 endpoints)

```http
GET    /api/v1/user/profile           # Get user profile
PATCH  /api/v1/user/profile           # Update profile
```

**Updatable Fields:**
- firstname, lastname, phone, date_of_birth

---

### Wallet Operations (4 endpoints)

```http
GET    /api/v1/user/wallet            # Get wallet info
GET    /api/v1/user/wallet/balances   # Get token balances (all chains)
GET    /api/v1/user/wallet/addresses  # Get chain addresses
POST   /api/v1/user/wallet/refresh-balances  # Force refresh from blockchain
```

**Query Parameters:**
- `chain`: Filter by chain
- `refresh`: Force blockchain sync (true/false)

**Chains Supported:**
- arbitrum (Chain ID: 42161)
- base (Chain ID: 8453)
- hyperliquid (non-EVM)

---

### Transactions (2 endpoints)

```http
GET    /api/v1/user/transactions      # Get transaction history
GET    /api/v1/user/transactions/:id  # Get transaction details
```

**Query Parameters:**
- `page`, `limit`: Pagination
- `type`: Filter by transaction type (0=SWAP, 1=FUND, 2=EARN, 3=SAVE)
- `status`: Filter by status (0=PENDING, 1=SUCCESS, 2=FAILED)
- `chain`: Filter by blockchain
- `date_from`, `date_to`: Date range
- `asset`: Filter by asset

---

### Trading & Swaps (2 endpoints)

```http
POST   /api/v1/user/trade/quote       # Get swap quote (no execution)
POST   /api/v1/user/trade/swap        # Execute token swap
```

**Quote Request:**
```json
{
  "from_asset": "USDC",
  "from_amount": "50",
  "to_asset": "ETH",
  "chain": "arbitrum",
  "slippage": 0.5
}
```

**Quote Response:**
```json
{
  "quote_id": "quote_abc123",
  "to_amount": "0.0204",
  "to_amount_min": "0.0203",
  "rate": "1 USDC = 0.000408 ETH",
  "estimated_gas_usd": 0.37,
  "dex_aggregator": "1inch",
  "quote_expires_at": "2025-11-16T16:46:00Z"
}
```

**Swap Request:**
```json
{
  "quote_id": "quote_abc123",
  "from_asset": "USDC",
  "from_amount": "50",
  "to_asset": "ETH",
  "to_amount_min": "0.0203",
  "chain": "arbitrum",
  "slippage": 0.5
}
```

**External Dependencies:**
- 1inch API (primary DEX aggregator)
- 0x Protocol API (backup)

---

### Earn - Yield Farming (4 endpoints)

```http
GET    /api/v1/user/earn/opportunities        # List yield opportunities
POST   /api/v1/user/earn/deposit              # Deposit to protocol
GET    /api/v1/user/earn/positions            # Get active positions
POST   /api/v1/user/earn/positions/:id/withdraw  # Withdraw from position
```

**List Opportunities Query:**
- `chain`: arbitrum, base
- `protocol`: aave, compound, curve
- `asset`: Filter by asset
- `min_apy`: Minimum APY filter
- `risk_score`: low, medium, high
- `sort`: Sort by apy, tvl, risk

**Deposit Request:**
```json
{
  "opportunity_id": "aave-usdc-arbitrum",
  "protocol": "aave",
  "asset": "USDC",
  "amount": "50",
  "chain": "arbitrum"
}
```

**Position Response:**
```json
{
  "id": 101,
  "protocol": "aave",
  "asset": "USDC",
  "amount_deposited": "50.0",
  "current_value": "50.06",
  "rewards_earned": "0.06",
  "apy": 4.2,
  "current_apy": 4.3,
  "status": "active"
}
```

**Protocols Supported:**
- Aave V3 (Arbitrum, Base)
- Compound V3 (Arbitrum, Base)
- Curve (future)

---

### Save Schedules (4 endpoints)

```http
GET    /api/v1/user/save/schedules           # Get save schedules
POST   /api/v1/user/save/schedule            # Create schedule
PATCH  /api/v1/user/save/schedules/:id       # Update schedule
DELETE /api/v1/user/save/schedules/:id       # Delete schedule
```

**Create Schedule Request:**
```json
{
  "asset": "USDC",
  "amount": "20",
  "frequency": "weekly",
  "day_of_week": 1,
  "destination_protocol": "aave",
  "chain": "arbitrum",
  "max_executions": null
}
```

**Frequency Options:**
- daily
- weekly (requires day_of_week: 0-6)
- biweekly (requires day_of_week: 0-6)
- monthly (requires day_of_month: 1-31)

**Execution:**
- Cron job runs every hour
- Executes at specified time (UTC)
- Auto-deposit to protocol if specified

---

### Perpetuals (3 endpoints)

```http
POST   /api/v1/user/perpetuals/open                 # Open position
GET    /api/v1/user/perpetuals/positions            # Get positions
POST   /api/v1/user/perpetuals/positions/:id/close  # Close position
```

**Open Position Request:**
```json
{
  "symbol": "ETH-USD",
  "side": "long",
  "leverage": 5.0,
  "margin": "50",
  "size": "0.102"
}
```

**Position Response:**
```json
{
  "id": 301,
  "symbol": "ETH-USD",
  "side": "long",
  "leverage": 5.0,
  "size": "0.102",
  "entry_price": 2450.50,
  "mark_price": 2450.50,
  "liquidation_price": 1960.40,
  "margin": "50.0",
  "unrealized_pnl": "0.00",
  "funding_rate": 0.01,
  "status": "open"
}
```

**Trading Pairs:**
- ETH-USD
- BTC-USD
- SOL-USD
- (All Hyperliquid supported pairs)

**Leverage:**
- Min: 1x
- Max: 20x
- Liquidation calculated server-side

**External Dependency:**
- Hyperliquid API

---

### AI Chat (2 endpoints)

```http
POST   /api/v1/user/chat/message      # Send message to AI
GET    /api/v1/user/chat/history      # Get chat history
```

**Message Request:**
```json
{
  "message": "What's my portfolio performance?",
  "session_id": "session_abc123",
  "context": {
    "include_portfolio": true,
    "include_market_data": false
  }
}
```

**AI Response:**
```json
{
  "message_id": 5678,
  "session_id": "session_abc123",
  "ai_response": "Your portfolio is performing well! Here's a summary:\n\n📊 Total Value: $120.35 (+1.27% today)...",
  "ai_metadata": {
    "model": "gemini-1.5-flash",
    "tokens_total": 820,
    "cost_usd": 0.00005,
    "latency_ms": 1240
  },
  "recommendations": [
    {
      "action": "close_position",
      "title": "Take Profit on ETH Position",
      "executable": true
    }
  ]
}
```

**Rate Limits:**
- Free tier: 10 conversations per day
- Pro tier: 20 requests per minute

**External Dependencies:**
- Google Vertex AI (Gemini 1.5 Flash)
- AWS Bedrock (Claude Sonnet 4 - fallback)

---

### Subscriptions (3 endpoints)

```http
GET    /api/v1/user/subscription               # Get subscription status
POST   /api/v1/user/subscription/create-checkout  # Create checkout
POST   /api/v1/user/subscription/cancel         # Cancel subscription
```

**Plans:**
- **Free**: 10 AI conversations/day
- **Pro**: $9.99/month, unlimited AI, 7-day trial

**Create Checkout Request:**
```json
{
  "plan": "pro",
  "trial_enabled": true
}
```

**External Dependency:**
- Stripe API

---

### Notifications (3 endpoints)

```http
GET    /api/v1/user/notifications                # Get notifications
POST   /api/v1/user/notifications/:id/read      # Mark as read
POST   /api/v1/user/notifications/read-all      # Mark all as read
```

**Query Parameters:**
- `unread_only`: true/false
- `type`: Filter by notification type
- `limit`: Max results (max: 100)

**Notification Types:**
- transaction_confirmed
- transaction_failed
- kyc_approved
- save_executed
- perp_liquidation_warning
- subscription_renewed
- price_alert

**Channels:**
- push (Firebase Cloud Messaging)
- email (SendGrid)
- sms (Twilio)
- in_app

---

### Funding (2 endpoints)

```http
POST   /api/v1/user/funding/create    # Create funding transaction
GET    /api/v1/user/funding/history   # Get funding history
```

**Create Funding Request:**
```json
{
  "amount_fiat": 103.70,
  "asset": "USDC",
  "chain": "arbitrum",
  "payment_method": "card"
}
```

**Fees:**
- Stripe: 2.9% + $0.30
- Network: Variable (0.5%)
- Total: ~3.7%

**External Dependency:**
- Stripe API

---

## 🔧 ADMIN Endpoints (15 total)

### Authentication (1 endpoint)

```http
POST   /api/v1/admin/auth/login       # Admin login (email + password + 2FA)
```

**Request:**
```json
{
  "email": "admin@anvil.com",
  "password": "securepassword123",
  "totp_code": "123456"
}
```

**Security:**
- 2FA/TOTP required
- 8-hour token expiry
- All actions logged to audit_logs

---

### Dashboard (1 endpoint)

```http
GET    /api/v1/admin/dashboard/stats  # Get platform statistics
```

**Query Parameters:**
- `period`: 24h, 7d, 30d, 90d

**Response Includes:**
- User stats (total, active, new, KYC)
- Transaction stats (volume, success rate)
- LLM stats (calls, costs)
- Revenue stats (funding, subscriptions, fees)
- System health status

---

### User Management (4 endpoints)

```http
GET    /api/v1/admin/users             # List all users
GET    /api/v1/admin/users/:id         # Get user details
PATCH  /api/v1/admin/users/:id/kyc     # Approve/reject KYC
PATCH  /api/v1/admin/users/:id/status  # Update user status
```

**List Users Query:**
- `page`, `limit`: Pagination
- `search`: Search by email, name, UID
- `role`: Filter by role
- `status`: Filter by status
- `kyc_status`: Filter by KYC status
- `created_from`, `created_to`: Date range

**KYC Approval:**
```json
{
  "action": "approve",
  "notes": "All documents verified"
}
```

**Status Update:**
```json
{
  "status": 2,
  "reason": "ToS violation",
  "notes": "Suspicious activity confirmed"
}
```

**User Status Values:**
- 0: INACTIVE
- 1: ACTIVE
- 2: DELETED (suspended)

---

### Transaction Management (2 endpoints)

```http
GET    /api/v1/admin/transactions              # List all transactions
POST   /api/v1/admin/transactions/:id/retry    # Retry failed transaction
```

**Retry Transaction:**
```json
{
  "override_gas_price": 1.2,
  "reason": "Network congestion caused initial failure"
}
```

---

### Settings Management (2 endpoints)

```http
GET    /api/v1/admin/settings          # Get all settings
PATCH  /api/v1/admin/settings/:id      # Update setting
```

**Settings Categories:**
- global: Platform-wide settings
- security: Security parameters
- payment: Payment configuration
- ai: AI model settings
- blockchain: RPC endpoints, gas limits

**Update Setting:**
```json
{
  "value": "10000",
  "reason": "Increasing daily trade limit"
}
```

---

### AI Model Configuration (2 endpoints)

```http
GET    /api/v1/admin/ai/models         # Get AI models
PATCH  /api/v1/admin/ai/models/:id     # Update model config
```

**Model Configuration:**
```json
{
  "status": "enabled",
  "quota_limit_daily": 10000,
  "cost_per_1k_input": 0.00001,
  "cost_per_1k_output": 0.00003
}
```

---

### Subscription Management (2 endpoints)

```http
GET    /api/v1/admin/subscriptions               # List subscriptions
POST   /api/v1/admin/subscriptions/:id/refund    # Process refund
```

**Refund Request:**
```json
{
  "amount": 9.99,
  "reason": "Customer complaint - service issues",
  "notes": "Approved by support manager"
}
```

---

### Audit Logs (1 endpoint)

```http
GET    /api/v1/admin/audit-logs        # Get audit trail
```

**Query Parameters:**
- `page`, `limit`: Pagination (max: 100)
- `actor_user_id`: Filter by admin
- `action`: Filter by action type
- `entity`: Filter by entity type
- `date_from`, `date_to`: Date range

---

## 🔍 AUDITOR Endpoints (13 total)

### Authentication (1 endpoint)

```http
POST   /api/v1/admin/auth/login        # Auditor login (same as admin)
```

**Note:** Auditors use same login endpoint but have role=1 and read-only permissions.

---

### Dashboard (1 endpoint)

```http
GET    /api/v1/admin/dashboard/stats   # Compliance-focused stats
```

---

### Audit Logs (2 endpoints)

```http
GET    /api/v1/admin/audit-logs        # View audit trail (read-only)
GET    /api/v1/admin/audit-logs/:id    # Get log details
```

---

### User Data Access (3 endpoints)

```http
GET    /api/v1/admin/users               # List users (read-only)
GET    /api/v1/admin/users/:id           # Get user details (read-only)
GET    /api/v1/admin/users/:id/activity  # Get user activity history
```

---

### Transaction Review (2 endpoints)

```http
GET    /api/v1/admin/transactions                  # View transactions (read-only)
GET    /api/v1/admin/transactions/:id/compliance   # Get compliance analysis
```

**Compliance Analysis Includes:**
- CTR requirements (>$10k threshold)
- OFAC screening results
- Wallet screening status
- Risk assessment
- Recommendations

---

### Financial Reporting (1 endpoint)

```http
POST   /api/v1/admin/reports/financial  # Generate financial report
```

**Request:**
```json
{
  "report_type": "monthly",
  "period": "2025-11",
  "include": ["revenue", "volume", "users", "fees", "subscriptions", "costs"],
  "format": "json"
}
```

**Format Options:**
- json
- csv
- xlsx

---

### Export Operations (3 endpoints)

```http
POST   /api/v1/admin/export/audit-logs    # Export audit logs
POST   /api/v1/admin/export/transactions  # Export transactions
POST   /api/v1/admin/export/users         # Export user data
```

**Export Request:**
```json
{
  "date_from": "2025-11-01T00:00:00Z",
  "date_to": "2025-11-30T23:59:59Z",
  "format": "csv",
  "filters": {}
}
```

**Response:**
```json
{
  "export_id": "export_abc123",
  "format": "csv",
  "file_url": "https://exports.anvil.com/audit-logs-nov2025.csv",
  "file_size_bytes": 245678,
  "record_count": 45,
  "expires_at": "2025-11-17T20:35:00Z"
}
```

**Note:** Export URLs expire after 24 hours.

---

## 📋 Standard Response Formats

### Success Response

```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error context
    },
    "timestamp": "2025-11-16T20:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

### Pagination Format

```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

## 🚦 Rate Limits

### CLIENT Endpoints

| Endpoint Type | Rate Limit |
|---------------|------------|
| Authentication | 5/min per IP |
| General GET | 60/min |
| Profile updates (PATCH) | 20/min |
| Trading operations | 10/min |
| Wallet refresh | 5/min |
| AI chat (Free) | 10/day |
| AI chat (Pro) | 20/min |

### ADMIN Endpoints

| Endpoint Type | Rate Limit |
|---------------|------------|
| Authentication | 5/min per IP |
| Read operations (GET) | 60/min |
| Write operations | 20/min |
| Critical operations | 10/min |

### AUDITOR Endpoints

| Endpoint Type | Rate Limit |
|---------------|------------|
| Authentication | 5/min per IP |
| Read operations | 60/min |
| Export operations | 5/min |
| Report generation | 10/min |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700000000
```

---

## 🔐 Authentication

### JWT Token Structure

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "12345",
  "user_id": 12345,
  "uid": "usr_abc123",
  "email": "user@email.com",
  "role": 2,
  "privy_user_id": "did:privy:clk1abc123",
  "iat": 1699876543,
  "exp": 1699880143
}
```

**Usage:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## ❌ Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid/expired token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INSUFFICIENT_BALANCE` | 400 | Not enough funds |
| `DAILY_LIMIT_EXCEEDED` | 429 | Daily limit reached |
| `SERVER_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | External service down |

---

## 🔌 External Service Integrations

### Required Services

1. **Privy**
   - Wallet creation and management
   - User authentication
   - Transaction signing

2. **Stripe**
   - Fiat to crypto payments
   - Subscription billing
   - Refund processing

3. **1inch / 0x Protocol**
   - DEX aggregation
   - Best swap rates
   - Route optimization

4. **Aave V3 / Compound V3**
   - Smart contract calls
   - APY data fetching
   - Position management

5. **Hyperliquid**
   - Perpetual trading
   - Position updates
   - Funding rate data

6. **Vertex AI (Google)**
   - Gemini 1.5 Flash model
   - AI conversations
   - Recommendation engine

7. **Chainlink**
   - Price feeds
   - Oracle data

8. **Alchemy**
   - Blockchain RPC endpoints
   - Transaction monitoring

9. **SendGrid**
   - Email notifications
   - Transactional emails

10. **Twilio**
    - SMS notifications
    - 2FA codes

11. **Firebase Cloud Messaging**
    - Push notifications
    - Real-time updates

---

## 📊 Database Operations

Each endpoint performs specific database operations. See separate SQLAlchemy models documentation for:
- Complete table schemas
- Relationships
- Indexes
- Constraints

**Key Tables:**
- users, wallets, chain_addresses
- transactions, funding_transactions
- earn_positions, save_schedules
- hyperliquid_positions
- llm_conversations, agent_executions
- subscriptions, subscription_payments
- notifications, audit_logs

---

## 🔄 Webhook Support

### Stripe Webhooks

```http
POST /api/v1/webhooks/stripe
```

**Events Handled:**
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `customer.subscription.updated`
- `customer.subscription.deleted`

### Blockchain Event Monitoring

Internal webhook system monitors:
- Transaction confirmations
- Failed transactions
- Contract events (Aave/Compound deposits/withdrawals)

---

## 📚 API Documentation Access

### Swagger/OpenAPI
- URL: `https://api.anvil.com/docs`
- Interactive API testing
- Request/response schemas

### Postman Collection
- Available on request
- Pre-configured environments
- Example requests

---

## 🧪 Testing Environments

### Sandbox
- **URL:** `https://api-sandbox.anvil.com/v1`
- **Database:** Isolated test database
- **Blockchain:** Testnet RPCs
- **Payments:** Stripe test mode
- **AI:** Test quotas

### Staging
- **URL:** `https://api-staging.anvil.com/v1`
- **Database:** Staging database
- **Blockchain:** Mainnet RPCs
- **Payments:** Stripe test mode
- **AI:** Production quotas

### Production
- **URL:** `https://api.anvil.com/v1`
- **Database:** Production database
- **Blockchain:** Mainnet RPCs
- **Payments:** Stripe live mode
- **AI:** Production quotas

---

## 📈 Performance Requirements

- **API Response Time:** <500ms (p95)
- **Database Query Time:** <100ms (p95)
- **Blockchain RPC Calls:** <2s (p95)
- **AI Response Time:** <3s (p95)

---

## 🔒 Security Requirements

- **TLS 1.3** for all connections
- **JWT tokens** with 1-hour expiry
- **API rate limiting** on all endpoints
- **Input validation** on all requests
- **SQL injection prevention**
- **XSS protection**
- **CSRF tokens** for web console
- **Audit logging** for all admin/auditor actions

---

## ✅ Implementation Checklist

- [ ] Set up API framework (Express/FastAPI)
- [ ] Implement authentication (JWT + Privy)
- [ ] Configure database (MySQL)
- [ ] Set up Redis cache
- [ ] Integrate Stripe
- [ ] Integrate 1inch/0x
- [ ] Integrate Aave/Compound
- [ ] Integrate Hyperliquid
- [ ] Integrate Vertex AI
- [ ] Set up notification services
- [ ] Implement rate limiting
- [ ] Set up monitoring
- [ ] Write tests
- [ ] Create API documentation
- [ ] Deploy to staging
- [ ] Load testing
- [ ] Deploy to production

---

**Document Status:** Complete for Development ✅  
**Version:** 1.0  
**Last Updated:** November 2025  
**Related Documents:** User Stories, Database Models (SQLAlchemy)

**Next Steps:** Review with development team and begin implementation.
