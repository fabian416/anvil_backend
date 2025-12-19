# 🎯 Anvil User Flows - ADMIN Users (Admin Console)

## User Type: ADMIN (role=0)
**Platform:** Web Admin Console  
**Access Level:** Full CRUD access to all resources  
**Primary Use Cases:** User management, system configuration, monitoring, support

---

## Table of Contents

1. [Admin Login & Dashboard](#1-admin-login--dashboard)
2. [User Management & KYC Approval](#2-user-management--kyc-approval)
3. [Transaction Monitoring & Support](#3-transaction-monitoring--support)
4. [System Configuration Management](#4-system-configuration-management)
5. [AI Model Configuration](#5-ai-model-configuration)
6. [Cost Monitoring & Alerts](#6-cost-monitoring--alerts)
7. [Emergency Position Management](#7-emergency-position-management)
8. [Subscription Management](#8-subscription-management)
9. [Audit Log Review](#9-audit-log-review)
10. [Analytics & Reporting](#10-analytics--reporting)

---

## 1. Admin Login & Dashboard

### Flow: Admin Authentication and Dashboard Access

**Goal:** Securely log in to admin console and view system overview

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Navigate to Admin Console                               │
└─────────────────────────────────────────────────────────────────┘

Admin User: Opens https://admin.anvil.com

UI Display: Admin Login Page
  - Anvil Admin Console logo
  - Email input field
  - Password input field
  - "Sign In" button
  - "Forgot Password?" link
  - Security notice: "Admin access is logged and monitored"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Admin Authentication                                    │
└─────────────────────────────────────────────────────────────────┘

Admin Input:
  - Email: "admin@anvil.com"
  - Password: [secure password]

Admin Action: Clicks "Sign In"

Frontend Action:
  → POST /api/v1/admin/auth/login

Request:
{
  "email": "admin@anvil.com",
  "password": "***********"
}

Backend Process:
  1. Validate credentials
     
     SELECT id, uid, email, role, status, password_hash
     FROM users
     WHERE email = 'admin@anvil.com'
     AND role = 0 (ADMIN)
     AND status = 1 (ACTIVE)
  
  2. Verify password (bcrypt)
     
     bcrypt.compare(input_password, stored_hash)
     → Match ✅
  
  3. Check 2FA status (if enabled)
     → Require TOTP code
     → Validate with authenticator
  
  4. Generate admin JWT token
     
     JWT payload:
     {
       user_id: 1,
       uid: "usr_admin001",
       email: "admin@anvil.com",
       role: 0,
       permissions: ["*"], // Full access
       exp: NOW() + 8 hours
     }
  
  5. Log admin login
     
     DB INSERT: audit_logs
     {
       actor_user_id: 1,
       action: "admin_login",
       entity: "auth",
       entity_id: 1,
       payload_json: {
         "login_time": "2025-11-16T15:00:00Z",
         "success": true
       },
       ip_address: "192.168.1.100",
       user_agent: "Mozilla/5.0...",
       created_at: NOW()
     }
  
  6. Update last login
     
     DB UPDATE: users
     SET last_login_at = NOW(),
         last_active_at = NOW()
     WHERE id = 1

Response: 200 OK
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "expires_in": 28800,
    "admin": {
      "id": 1,
      "email": "admin@anvil.com",
      "role": 0,
      "permissions": ["*"]
    }
  }
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Load Admin Dashboard                                    │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → GET /api/v1/admin/dashboard/stats
  → Authorization: Bearer [admin_access_token]

Backend Process:
  Execute analytics query:
  
  Platform Statistics:
  {
    users: {
      total: 1,234,
      active_24h: 234,
      new_today: 12,
      growth_rate_7d: 5.2%
    },
    transactions: {
      total_24h: 567,
      success_rate: 98.2%,
      total_volume_usd_24h: 45,678.90,
      avg_transaction_usd: 80.56
    },
    llm: {
      total_calls_24h: 5,678,
      total_cost_24h: $11.23,
      avg_cost_per_call: $0.002,
      success_rate: 99.1%,
      vertex_calls: 5,346,
      bedrock_calls: 332
    },
    agents: {
      total_executions_24h: 234,
      success_rate: 96.5%,
      avg_execution_time_ms: 4,567,
      avg_cost: $0.003
    },
    revenue: {
      total_funding_24h: $12,345.67,
      subscriptions_mrr: $2,106.66,
      total_fees_collected_24h: $567.89
    }
  }

Response: 200 OK with complete stats

UI Display: Admin Dashboard

╔════════════════════════════════════════════════════════════════╗
║ ANVIL ADMIN CONSOLE                                            ║
╠════════════════════════════════════════════════════════════════╣
║ Dashboard    Users    Transactions    System    Analytics      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                 ║
║ System Health: 🟢 All systems operational                     ║
║                                                                 ║
║ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              ║
║ │ Total Users │ │ Active Now  │ │ New Today   │              ║
║ │   1,234     │ │     234     │ │     12      │              ║
║ │  +5.2% ⬆️   │ │  +15 vs avg │ │  Normal     │              ║
║ └─────────────┘ └─────────────┘ └─────────────┘              ║
║                                                                 ║
║ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              ║
║ │ AI Cost 24h │ │ Txs Today   │ │ Revenue 24h │              ║
║ │   $11.23    │ │     567     │ │  $12,913.56 │              ║
║ │  -8% vs avg │ │  98.2% ✅   │ │  +12% ⬆️    │              ║
║ └─────────────┘ └─────────────┘ └─────────────┘              ║
║                                                                 ║
║ Recent Alerts:                                                  ║
║ • ⚠️ User #1245 approaching liquidation (ETH-USD)             ║
║ • ℹ️ Model gemini-1.5-pro quota at 75%                       ║
║ • ✅ All backups completed successfully                        ║
║                                                                 ║
║ Pending Actions:                                                ║
║ • 5 KYC approvals pending review                               ║
║ • 2 failed transactions need investigation                     ║
║ • 1 subscription payment failed                                ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝

Sidebar Navigation:
  📊 Dashboard (active)
  👥 Users
  💳 Transactions
  🤖 AI & Agents
  💰 Payments & Subs
  ⚙️ System Settings
  🔐 Security & Audit
  📈 Analytics

✅ SUCCESS CRITERIA:
  - Admin logged in securely
  - Login audit logged
  - Dashboard shows real-time stats
  - Alerts and pending items visible
```

**Total Time:** ~30 seconds  
**Database Tables Used:** `users`, `audit_logs`  
**Security:** 2FA, IP logging, session expiry

---

## 2. User Management & KYC Approval

### Flow: Approve User KYC Application

**Goal:** Review and approve user's KYC submission

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Navigate to KYC Queue                                   │
└─────────────────────────────────────────────────────────────────┘

Admin Action: Clicks "Users" → "KYC Pending" tab

Frontend Action:
  → GET /api/v1/admin/users?kyc_status=pending&page=1&limit=50
  → Authorization: Bearer [admin_token]

Backend Process:
  SELECT u.id, u.uid, u.email, u.firstname, u.lastname,
         u.kyc_status, u.created_at,
         w.address as wallet_address,
         COUNT(DISTINCT t.id) as transaction_count,
         SUM(CASE WHEN t.status = 1 THEN t.amount_in ELSE 0 END) as total_volume
  FROM users u
  LEFT JOIN wallets w ON u.id = w.user_id
  LEFT JOIN transactions t ON u.id = t.user_id
  WHERE u.kyc_status = 'pending'
  GROUP BY u.id
  ORDER BY u.created_at ASC

Response: 200 OK
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 12345,
        "uid": "usr_xyz123",
        "email": "john.doe@example.com",
        "name": "John Doe",
        "kyc_status": "pending",
        "submitted_at": "2025-11-15T10:00:00Z",
        "wallet": "0x1234...5678",
        "transaction_count": 8,
        "total_volume_usd": 450.00,
        "account_age_days": 7
      },
      // ... more pending KYCs
    ],
    "pagination": {
      "page": 1,
      "total": 5
    }
  }
}

UI Display: KYC Pending Queue

╔════════════════════════════════════════════════════════════════╗
║ KYC APPROVALS PENDING (5)                                      ║
╠════════════════════════════════════════════════════════════════╣
║ [Search] [Filter by Date] [Export CSV]                         ║
║                                                                 ║
║ User ID    | Name          | Submitted  | Volume   | Actions   ║
║━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━║
║ usr_xyz123 | John Doe      | 1 day ago  | $450     | [Review]  ║
║ usr_abc456 | Jane Smith    | 2 days ago | $1,200   | [Review]  ║
║ usr_def789 | Bob Johnson   | 3 days ago | $75      | [Review]  ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Review KYC Application                                  │
└─────────────────────────────────────────────────────────────────┘

Admin Action: Clicks "Review" for John Doe

Frontend Action:
  → GET /api/v1/admin/users/12345
  → GET /api/v1/admin/users/12345/kyc-documents

Backend Process:
  1. Get user details
  2. Get KYC documents
  3. Get transaction history
  4. Get activity logs

Response: Complete user profile with KYC data

UI Display: KYC Review Screen

╔════════════════════════════════════════════════════════════════╗
║ KYC REVIEW - John Doe (usr_xyz123)                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                 ║
║ 📋 Personal Information                                         ║
║ ─────────────────────────────────────────────────────────────  ║
║ Name:           John Doe                                        ║
║ Email:          john.doe@example.com (verified ✅)             ║
║ Phone:          +1-234-567-8900 (verified ✅)                  ║
║ Date of Birth:  1990-05-15                                     ║
║ Address:        123 Main St, New York, NY 10001               ║
║ Country:        United States                                   ║
║                                                                 ║
║ 📷 Identity Documents                                           ║
║ ─────────────────────────────────────────────────────────────  ║
║ [Document: Driver's License - Front] [View Full Size]          ║
║  ┌──────────────┐                                              ║
║  │ [Thumbnail]  │  Expiry: 2028-05-15                          ║
║  └──────────────┘  State: New York                             ║
║                    DOB matches: ✅                              ║
║                    Name matches: ✅                             ║
║                                                                 ║
║ [Document: Driver's License - Back] [View Full Size]           ║
║  ┌──────────────┐                                              ║
║  │ [Thumbnail]  │  Barcode scan: ✅                            ║
║  └──────────────┘  Not expired: ✅                             ║
║                                                                 ║
║ [Selfie with ID] [View Full Size]                              ║
║  ┌──────────────┐                                              ║
║  │ [Thumbnail]  │  Face match: ✅ 98% confidence               ║
║  └──────────────┘  Liveness check: ✅                          ║
║                                                                 ║
║ 📊 Account Activity                                             ║
║ ─────────────────────────────────────────────────────────────  ║
║ Account Age:        7 days                                      ║
║ Total Transactions: 8                                           ║
║ Total Volume:       $450.00                                     ║
║ Funding Source:     Card ending in 4242                        ║
║ Last Active:        2 hours ago                                 ║
║                                                                 ║
║ Risk Factors: None detected ✅                                  ║
║                                                                 ║
║ ⚠️ Admin Notes                                                  ║
║ [Text area for notes]                                           ║
║                                                                 ║
║ Decision:                                                        ║
║ ( ) Approve KYC                                                 ║
║ ( ) Reject KYC - Reason: [dropdown]                            ║
║ ( ) Request More Information                                    ║
║                                                                 ║
║ [Cancel]              [Reject]         [Approve ✅]            ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Approve KYC                                             │
└─────────────────────────────────────────────────────────────────┘

Admin Review:
  - Documents look authentic ✅
  - Face match successful ✅
  - No red flags in activity ✅
  - Reasonable transaction volume ✅

Admin Action:
  - Selects "Approve KYC" radio button
  - Adds note: "All documents verified. Normal usage pattern."
  - Clicks "Approve ✅" button

Confirmation Modal:
  "Are you sure you want to approve KYC for John Doe?"
  [Cancel] [Confirm Approval]

Admin Action: Clicks "Confirm Approval"

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Execute KYC Approval                                    │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → PATCH /api/v1/admin/users/12345/kyc
  → Authorization: Bearer [admin_token]

Request:
{
  "action": "approve",
  "notes": "All documents verified. Normal usage pattern."
}

Backend Process:
  1. Start transaction
  
  2. Update user KYC status
     
     DB UPDATE: users
     SET kyc_status = 'approved',
         kyc_completed_at = NOW(),
         updated_at = NOW()
     WHERE id = 12345
  
  3. Create audit log
     
     DB INSERT: audit_logs
     {
       actor_user_id: 1, // Admin ID
       action: "kyc_approved",
       entity: "user",
       entity_id: "12345",
       payload_json: {
         "user_email": "john.doe@example.com",
         "admin_email": "admin@anvil.com",
         "notes": "All documents verified. Normal usage pattern.",
         "before": {"kyc_status": "pending"},
         "after": {"kyc_status": "approved"},
         "approval_time": "2025-11-16T15:30:00Z"
       },
       ip_address: "192.168.1.100",
       created_at: NOW()
     }
  
  4. Send notification to user
     
     DB INSERT: notifications
     {
       user_id: 12345,
       type: "kyc_approved",
       channel: "email",
       title: "KYC Approved! 🎉",
       message: "Your identity verification has been approved. You now have full access to Anvil.",
       data_json: {
         "approved_at": "2025-11-16T15:30:00Z",
         "approved_by": "Anvil Team"
       },
       priority: "medium",
       status: "pending"
     }
  
  5. Commit transaction

Response: 200 OK
{
  "success": true,
  "data": {
    "user_id": 12345,
    "kyc_status": "approved",
    "approved_at": "2025-11-16T15:30:00Z",
    "approved_by": "admin@anvil.com"
  },
  "audit_log_id": 10025
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Confirmation & User Notification                        │
└─────────────────────────────────────────────────────────────────┘

UI Display: Success Toast
  "✅ KYC approved for John Doe. User has been notified."

User's Perspective (John Doe):
  1. Receives email: "KYC Approved!"
  2. Receives push notification
  3. Sees green checkmark in profile: "Verified ✅"
  4. Can now make transactions >$1,000

Admin Dashboard Updates:
  - KYC queue count: 5 → 4
  - John Doe removed from pending list
  - Added to audit log

✅ SUCCESS CRITERIA:
  - User KYC status updated to 'approved'
  - Admin action logged in audit_logs
  - User notified via email and push
  - User can now access all features
```

**Total Time:** ~3-5 minutes per KYC review  
**Database Tables Used:** `users`, `audit_logs`, `notifications`  
**Compliance:** All actions tracked for regulatory audit

---

## 3. Transaction Monitoring & Support

### Flow: Investigate and Retry Failed Transaction

**Goal:** Help user whose transaction failed and retry it

#### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Monitor Failed Transactions                             │
└─────────────────────────────────────────────────────────────────┘

Admin Navigation: Dashboard → "2 failed transactions need investigation"

Frontend Action:
  → GET /api/v1/admin/transactions?status=2&limit=50
  → Authorization: Bearer [admin_token]

Backend Process:
  SELECT t.*,
         u.email, u.firstname, u.lastname,
         w.address as wallet_address
  FROM transactions t
  INNER JOIN users u ON t.user_id = u.id
  INNER JOIN wallets w ON t.wallet_id = w.id
  WHERE t.status = 2 (FAILED)
  AND t.created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
  ORDER BY t.created_at DESC

Response: List of failed transactions

UI Display: Failed Transactions Screen

╔════════════════════════════════════════════════════════════════╗
║ FAILED TRANSACTIONS (Last 24h)                                 ║
╠════════════════════════════════════════════════════════════════╣
║                                                                 ║
║ TX ID  | User          | Type  | Amount   | Error      | Time  ║
║━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━║
║ #458   | john.doe@...  | SWAP  | 50 USDC  | Gas too   | 2h ago║
║        |               |       | → ETH    | low       |       ║
║        | [View Details]         [Investigate]         [Retry]  ║
║━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━║
║ #459   | jane.smith@.. | FUND  | $100     | Stripe    | 1h ago║
║        |               |       |          | declined  |       ║
║        | [View Details]         [Investigate]    [Contact User]║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Investigate Transaction #458                            │
└─────────────────────────────────────────────────────────────────┘

Admin Action: Clicks "View Details" for TX #458

Frontend Action:
  → GET /api/v1/admin/transactions/458
  → Authorization: Bearer [admin_token]

Backend Process:
  SELECT t.*,
         u.id as user_id, u.email, u.firstname, u.lastname,
         w.address, w.default_chain,
         ca.balance_usd
  FROM transactions t
  INNER JOIN users u ON t.user_id = u.id
  INNER JOIN wallets w ON t.wallet_id = w.id
  INNER JOIN chain_addresses ca ON w.id = ca.wallet_id AND ca.chain = t.chain
  WHERE t.id = 458

Response: Complete transaction details

UI Display: Transaction Detail Modal

╔════════════════════════════════════════════════════════════════╗
║ TRANSACTION DETAILS - #458                                      ║
╠════════════════════════════════════════════════════════════════╣
║                                                                 ║
║ User: John Doe (john.doe@example.com)                          ║
║ User ID: 12345                                                  ║
║ Wallet: 0x1234...5678                                          ║
║                                                                 ║
║ Transaction Info:                                               ║
║ ─────────────────────────────────────────────────────────────  ║
║ Type:           SWAP                                            ║
║ From:           50 USDC                                         ║
║ To:             ETH (expected: ~0.0204)                        ║
║ Chain:          Arbitrum                                        ║
║ Status:         FAILED ❌                                       ║
║ Created:        2 hours ago (2025-11-16T13:30:00Z)            ║
║                                                                 ║
║ Error Details:                                                  ║
║ ─────────────────────────────────────────────────────────────  ║
║ Error Code:     INSUFFICIENT_GAS                                ║
║ Error Message:  "Gas price too low. Transaction would fail."    ║
║ Blockchain:     Not submitted                                   ║
║                                                                 ║
║ Technical Details:                                              ║
║ ─────────────────────────────────────────────────────────────  ║
║ DEX Aggregator: 1inch                                           ║
║ Route:          Uniswap V3                                      ║
║ Slippage:       0.5%                                            ║
║ Gas Estimate:   150,000                                         ║
║ Gas Price Used: 0.1 gwei (TOO LOW)                             ║
║ Current Gas:    1.2 gwei (network congestion)                   ║
║                                                                 ║
║ Current Balance:                                                ║
║ ─────────────────────────────────────────────────────────────  ║
║ USDC: 50.00 (sufficient ✅)                                    ║
║ ETH:  0.0204 (for gas ✅)                                      ║
║                                                                 ║
║ Root Cause:                                                     ║
║ Network gas prices spiked during transaction submission.        ║
║ System used cached gas price that was too low.                  ║
║                                                                 ║
║ Recommended Action:                                             ║
║ Retry transaction with current gas price (1.2 gwei)            ║
║                                                                 ║
║ [Close]                          [Retry Transaction]            ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Retry Failed Transaction                                │
└─────────────────────────────────────────────────────────────────┘

Admin Decision: Transaction can be safely retried with higher gas

Admin Action: Clicks "Retry Transaction"

Confirmation Modal:
  "Retry transaction #458?"
  - User: John Doe
  - Type: Swap 50 USDC → ETH
  - Will use current gas price: 1.2 gwei
  - Estimated gas fee: $0.18
  
  [Cancel] [Confirm Retry]

Admin Action: Clicks "Confirm Retry"

Frontend Action:
  → POST /api/v1/admin/transactions/458/retry
  → Authorization: Bearer [admin_token]

Request:
{
  "override_gas_price": 1.2,
  "reason": "Network congestion caused initial failure. Retrying with current gas price."
}

Backend Process:
  1. Validate user still has balance
     
     Check: User has 50 USDC ✅
  
  2. Get fresh DEX quote with current gas
     
     1inch API Call (with gas=1.2 gwei)
     New quote received ✅
  
  3. Execute transaction
     
     Privy signing + blockchain submission
     tx_hash: "0xretry789..."
  
  4. Update original transaction
     
     DB UPDATE: transactions
     SET error_message = "Retried by admin with higher gas price",
         updated_at = NOW()
     WHERE id = 458
  
  5. Create new transaction record
     
     DB INSERT: transactions
     {
       user_id: 12345,
       wallet_id: 67890,
       type: 0 (SWAP),
       chain: "arbitrum",
       asset_in: "USDC",
       amount_in: 50.0,
       asset_out: "ETH",
       amount_out: 0.0204,
       tx_hash: "0xretry789...",
       status: 0 (PENDING),
       fee: 0.00015, // Higher gas
       fee_usd: 0.18,
       created_at: NOW()
     }
     
     New TX ID: 460
  
  6. Create audit log
     
     DB INSERT: audit_logs
     {
       actor_user_id: 1,
       action: "admin_transaction_retry",
       entity: "transaction",
       entity_id: "458",
       payload_json: {
         "original_tx_id": 458,
         "new_tx_id": 460,
         "reason": "Network congestion...",
         "old_gas_price": 0.1,
         "new_gas_price": 1.2,
         "admin_email": "admin@anvil.com"
       },
       ip_address: "192.168.1.100",
       created_at: NOW()
     }
  
  7. Notify user
     
     DB INSERT: notifications
     {
       user_id: 12345,
       type: "transaction_retried",
       channel: "push",
       title: "Transaction Retry in Progress",
       message: "We're retrying your swap. You'll be notified once complete.",
       priority: "medium",
       status: "pending"
     }

Response: 200 OK
{
  "success": true,
  "data": {
    "original_tx_id": 458,
    "new_tx_id": 460,
    "tx_hash": "0xretry789...",
    "status": "pending"
  },
  "audit_log_id": 10026
}

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Monitor Retry                                           │
└─────────────────────────────────────────────────────────────────┘

Background Job monitors TX #460:
  - Checks every 30 seconds
  - After 45 seconds: Confirmed! ✅
  
  DB UPDATE: transactions
  SET status = 1 (SUCCESS),
      block_number = 12345690,
      confirmed_at = NOW()
  WHERE id = 460

User notification sent:
  "Swap Complete! You received 0.0204 ETH"

Admin sees in dashboard:
  "✅ Transaction #460 confirmed. User John Doe's swap successful."

✅ SUCCESS CRITERIA:
  - Failed transaction identified
  - Root cause diagnosed
  - Transaction retried successfully
  - Admin action logged
  - User notified of resolution
```

**Total Time:** ~5-10 minutes investigation + retry  
**Database Tables Used:** `transactions`, `audit_logs`, `notifications`  
**User Impact:** Transaction completed successfully

---

## 4. System Configuration Management

### Flow: Update Trading Limit Setting

**Goal:** Increase max daily trade limit from $5,000 to $10,000

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Navigate to Settings                                    │
└─────────────────────────────────────────────────────────────────┘

Admin Navigation: System → Settings

Frontend Action:
  → GET /api/v1/admin/settings
  → Authorization: Bearer [admin_token]

Backend Process:
  SELECT id, `key`, `value`, scope, is_sensitive, description,
         updated_at, updated_by,
         u.email as updated_by_email
  FROM settings s
  LEFT JOIN users u ON s.updated_by = u.id
  ORDER BY scope, `key`

Response: All system settings

UI Display: System Settings

╔════════════════════════════════════════════════════════════════╗
║ SYSTEM SETTINGS                                                 ║
╠════════════════════════════════════════════════════════════════╣
║ [Search Settings] [Filter by Scope]                             ║
║                                                                 ║
║ 🌍 GLOBAL SETTINGS                                              ║
║ ─────────────────────────────────────────────────────────────  ║
║ max_daily_trade_limit                                           ║
║   Current: $5,000                                               ║
║   Description: Maximum daily trading limit per user (USD)       ║
║   Last updated: 2025-10-01 by admin@anvil.com                  ║
║   [Edit]                                                         ║
║                                                                 ║
║ max_position_size                                               ║
║   Current: $10,000                                              ║
║   Description: Maximum position size per trade (USD)            ║
║   Last updated: 2025-10-01 by admin@anvil.com                  ║
║   [Edit]                                                         ║
║                                                                 ║
║ 🔐 SECURITY SETTINGS                                            ║
║ ─────────────────────────────────────────────────────────────  ║
║ jwt_secret                                                      ║
║   Current: ********** (encrypted)                               ║
║   [Edit] [Rotate]                                               ║
║                                                                 ║
║ 💳 PAYMENT SETTINGS                                             ║
║ ─────────────────────────────────────────────────────────────  ║
║ stripe_api_key                                                  ║
║   Current: sk_live_••••••••                                     ║
║   [Edit] [Test Connection]                                      ║
║                                                                 ║
║ 🤖 AI SETTINGS                                                  ║
║ ─────────────────────────────────────────────────────────────  ║
║ daily_cost_alert_threshold                                      ║
║   Current: $50                                                  ║
║   [Edit]                                                         ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Edit Trade Limit                                        │
└─────────────────────────────────────────────────────────────────┘

Admin Action: Clicks [Edit] for max_daily_trade_limit

Modal Display: Edit Setting

╔════════════════════════════════════════════════════════════════╗
║ EDIT SETTING: max_daily_trade_limit                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                 ║
║ Key: max_daily_trade_limit                                      ║
║                                                                 ║
║ Description:                                                     ║
║ Maximum daily trading limit per user (USD)                      ║
║                                                                 ║
║ Current Value: $5,000                                           ║
║                                                                 ║
║ New Value:                                                       ║
║ [10000          ]                                               ║
║                                                                 ║
║ Reason for Change:                                              ║
║ [Textarea]                                                       ║
║ "Increasing limit to accommodate growth in user base and        ║
║  average transaction sizes. Risk management team approved."     ║
║                                                                 ║
║ ⚠️ Warning: This will affect all users immediately.            ║
║                                                                 ║
║ [Cancel]                          [Save Changes]                ║
║                                                                 ║
╚════════════════════════════════════════════════════════════════╝

Admin Input:
  - New value: 10000
  - Reason: "Increasing limit to accommodate growth..."

Admin Action: Clicks [Save Changes]

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Update Setting                                          │
└─────────────────────────────────────────────────────────────────┘

Frontend Action:
  → PATCH /api/v1/admin/settings/1
  → Authorization: Bearer [admin_token]

Request:
{
  "value": "10000",
  "reason": "Increasing limit to accommodate growth in user base..."
}

Backend Process:
  1. Get current setting value
     
     SELECT `key`, `value` FROM settings WHERE id = 1
     Current: 5000
  
  2. Update setting
     
     DB UPDATE: settings
     SET `value` = "10000",
         updated_at = NOW(),
         updated_by = 1 (admin user ID)
     WHERE id = 1
  
  3. Create audit log
     
     DB INSERT: audit_logs
     {
       actor_user_id: 1,
       action: "setting_updated",
       entity: "setting",
       entity_id: "1",
       payload_json: {
         "key": "max_daily_trade_limit",
         "before": {"value": "5000"},
         "after": {"value": "10000"},
         "reason": "Increasing limit to accommodate growth...",
         "admin_email": "admin@anvil.com",
         "timestamp": "2025-11-16T16:00:00Z"
       },
       ip_address: "192.168.1.100",
       created_at: NOW()
     }
  
  4. Clear application cache for settings
     
     Redis: DEL settings:cache
  
  5. Send alert to admin team
     
     Slack webhook: "Setting changed: max_daily_trade_limit 5000→10000"

Response: 200 OK
{
  "success": true,
  "data": {
    "setting_id": 1,
    "key": "max_daily_trade_limit",
    "value": "10000",
    "previous_value": "5000",
    "updated_by": "admin@anvil.com",
    "updated_at": "2025-11-16T16:00:00Z"
  },
  "audit_log_id": 10027
}

UI Display: Success notification
  "✅ Setting updated successfully. New limit: $10,000"

Settings page refreshes with new value displayed.

✅ SUCCESS CRITERIA:
  - Setting updated in database
  - Audit log created
  - Cache cleared
  - Admin team notified
  - Change takes effect immediately
```

**Total Time:** ~2 minutes  
**Database Tables Used:** `settings`, `audit_logs`  
**Impact:** All users can now trade up to $10,000/day

---

*Continuing with remaining admin flows in separate sections due to length...*

## Summary: ADMIN User Flows Completed

**Flows Documented:**
1. ✅ Admin Login & Dashboard
2. ✅ User Management & KYC Approval
3. ✅ Transaction Monitoring & Support
4. ✅ System Configuration Management

**Remaining Flows (5-10):**
5. AI Model Configuration
6. Cost Monitoring & Alerts
7. Emergency Position Management
8. Subscription Management
9. Audit Log Review
10. Analytics & Reporting

**Total Time per Flow:** 2-10 minutes  
**All Actions Audited:** 100% compliance  
**Security:** Role-based access, IP logging, 2FA

---

**Note:** Due to length, flows 5-10 will be in a separate document. Would you like me to continue with those flows?
