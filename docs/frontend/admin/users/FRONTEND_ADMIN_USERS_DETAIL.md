# FRONTEND_ADMIN_USERS_DETAIL

## Admin User Detail Module

**User Type:** Admin  
**Module:** User Detail  
**Route:** `/admin/users/:id`  
**Access Level:** Read (All) | Write (Admin+)

---

## 📋 Module Overview

### Title
**User Detail** - Complete User Profile

### Description
Comprehensive view of an individual user including profile information, wallet details, transaction history, project access, compliance status, and administrative actions.

### Key Capabilities
- Full user profile view
- Wallet and transaction history
- Project access management
- Compliance and risk information
- Administrative actions
- Activity timeline

---

## 👤 User Stories

### US-ADMIN-USER-001: View User Profile
**As a** platform administrator  
**I want to** see complete user information  
**So that** I understand the user's account

### US-ADMIN-USER-002: View User Wallets
**As a** platform administrator  
**I want to** see user's connected wallets  
**So that** I can verify ownership and activity

### US-ADMIN-USER-003: View Transaction History
**As a** platform administrator  
**I want to** see user's transactions  
**So that** I can investigate activity

### US-ADMIN-USER-004: Manage User Access
**As a** platform administrator  
**I want to** manage user's project access  
**So that** I can control permissions

### US-ADMIN-USER-005: Take Administrative Actions
**As a** platform administrator  
**I want to** suspend, ban, or modify users  
**So that** I can enforce platform policies

---

## 🖼️ Views & Wireframes

### View 1: User Profile Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Users                                                                    │
│  👤 User: alice@defi.co                          [📧 Email] [⏸️ Suspend] [🗑️ Ban]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Wallets]  [Transactions]  [Projects]  [Compliance]  [Activity]        │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  ┌─ Profile ────────────────────────────────────────────────────────────────────┐   │
│  │                                                                               │   │
│  │  ┌──────┐   alice@defi.co                                                    │   │
│  │  │  👤  │   Alice Johnson                                                    │   │
│  │  │  AJ  │                                                                     │   │
│  │  └──────┘   Status: 🟢 Active    Tier: ⭐ Pro    KYC: 🔵 Verified            │   │
│  │             Member since: November 15, 2025 (16 days)                        │   │
│  │                                                                               │   │
│  └───────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ Quick Stats ────────────────────────────────────────────────────────────────┐   │
│  │                                                                               │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐│   │
│  │  │ 💰 Portfolio     │  │ 📊 Transactions │  │ 💬 Conversations│  │ 📂 Projects││   │
│  │  │ $45,230          │  │ 156             │  │ 89              │  │ 3         ││   │
│  │  │ Across 2 wallets │  │ Last 30 days    │  │ Last 30 days    │  │ Active    ││   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └───────────┘│   │
│  │                                                                               │   │
│  └───────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ Connected Wallets ──────────────────────────────────────────────────────────┐   │
│  │                                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │ 🔷 0x7a23...8f4d                                           [Primary]   │ │   │
│  │  │    Ethereum │ Balance: $32,450 │ 45 transactions                       │ │   │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │ 🔷 0x9b12...4c3e                                                       │ │   │
│  │  │    Arbitrum │ Balance: $12,780 │ 111 transactions                      │ │   │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                               │   │
│  └───────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ Risk Assessment ────────────────────────────────────────────────────────────┐   │
│  │                                                                               │   │
│  │  Risk Score: 🟢 Low (12/100)                                                 │   │
│  │                                                                               │   │
│  │  ✅ KYC Verified                    ✅ No sanctions matches                  │   │
│  │  ✅ No suspicious activity          ✅ Wallet age > 6 months                 │   │
│  │  ⚠️ High transaction volume         ✅ No fraud flags                        │   │
│  │                                                                               │   │
│  │  Chainalysis Score: Low Risk │ Last checked: 2 hours ago                     │   │
│  │                                                                               │   │
│  └───────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌─ Recent Activity ────────────────────────────────────────────────────────────┐   │
│  │                                                                               │   │
│  │  Today, 14:32    Swapped 1.5 ETH → 2,890 USDC on Arbitrum                   │   │
│  │  Today, 10:15    Started conversation in Aave project                       │   │
│  │  Yesterday       Supplied 5,000 USDC to Aave on Ethereum                    │   │
│  │  Yesterday       Logged in from San Francisco, US                           │   │
│  │  2 days ago      Upgraded to Pro tier                                        │   │
│  │                                                                               │   │
│  │  [View Full Activity →]                                                      │   │
│  │                                                                               │   │
│  └───────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Transactions Tab

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👤 User: alice@defi.co - Transactions                                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Overview]  [Wallets]  [Transactions]  [Projects]  [Compliance]  [Activity]        │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  ┌─ Transaction Summary ────────────────────────────────────────────────────────┐   │
│  │  📊 156 Transactions    💰 $128,450 Volume    🔄 42 Swaps    📥 28 Deposits   │   │
│  └───────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  Type: [All ▼]    Chain: [All ▼]    Date: [Last 30 Days ▼]    [🔍 Search...]       │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ DATE       │ TYPE    │ DETAILS                    │ AMOUNT     │ STATUS│ HASH  ││
│  ├────────────┼─────────┼────────────────────────────┼────────────┼───────┼───────┤│
│  │ Today      │ 🔄 Swap │ 1.5 ETH → 2,890 USDC       │ $2,890     │ ✅    │ 0x3f..││
│  │ 14:32      │         │ via 1inch on Arbitrum      │            │       │       ││
│  ├────────────┼─────────┼────────────────────────────┼────────────┼───────┼───────┤│
│  │ Yesterday  │ 📥 Supply│ 5,000 USDC to Aave        │ $5,000     │ ✅    │ 0x7a..││
│  │ 16:45      │         │ on Ethereum                │            │       │       ││
│  ├────────────┼─────────┼────────────────────────────┼────────────┼───────┼───────┤│
│  │ Yesterday  │ 📤 Borrow│ 2,500 USDC from Aave      │ $2,500     │ ✅    │ 0x9c..││
│  │ 16:48      │         │ Health Factor: 2.1 → 1.8   │            │       │       ││
│  ├────────────┼─────────┼────────────────────────────┼────────────┼───────┼───────┤│
│  │ 2 days ago │ 🔄 Swap │ 10,000 USDC → 4.2 ETH      │ $10,000    │ ✅    │ 0x2b..││
│  │ 09:12      │         │ via 1inch on Ethereum      │            │       │       ││
│  ├────────────┼─────────┼────────────────────────────┼────────────┼───────┼───────┤│
│  │ 3 days ago │ 🌉 Bridge│ 5 ETH Ethereum → Arbitrum │ $11,250    │ ✅    │ 0x8d..││
│  │ 14:20      │         │ via Across                 │            │       │       ││
│  └────────────┴─────────┴────────────────────────────┴────────────┴───────┴───────┘│
│                                                                                      │
│  Showing 1-50 of 156 transactions                                  [Load More]      │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Administrative Actions Modal

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ⚠️ Suspend User: alice@defi.co                                             [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  SUSPENSION DETAILS                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Reason *                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [Suspicious Activity ▼]                                                 │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Additional Notes                                                            │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Multiple rapid transactions from sanctioned addresses flagged by       │  │  │
│  │  │ Chainalysis. Pending investigation.                                     │  │  │
│  │  │                                                                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Duration                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [●] Indefinite (until manually lifted)                                  │  │  │
│  │  │ [ ] Temporary: [      ] days                                            │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  IMPACT                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  ⚠️ User will be immediately logged out of all sessions                      │  │
│  │  ⚠️ User will not be able to log in                                          │  │
│  │  ⚠️ All pending transactions will be cancelled                               │  │
│  │  ⚠️ User will receive suspension notification email                          │  │
│  │                                                                               │  │
│  │  [✓] Send notification email to user                                         │  │
│  │  [✓] Log this action in audit trail                                          │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Cancel]                                                    [⏸️ Suspend User]      │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get User Detail

```typescript
// GET /admin/users/{id}
interface GetUserDetailResponse {
  success: true;
  data: {
    user: UserDetail;
    wallets: WalletInfo[];
    risk_assessment: RiskAssessment;
    stats: UserStats;
    recent_activity: ActivityEvent[];
  };
}

interface UserDetail {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  status: 'active' | 'inactive' | 'suspended' | 'banned';
  suspension_reason?: string;
  suspended_at?: string;
  suspended_by?: string;
  tier: 'free' | 'pro' | 'elite';
  kyc_status: 'verified' | 'pending' | 'not_started' | 'failed';
  kyc_verified_at?: string;
  two_factor_enabled: boolean;
  last_login_at?: string;
  last_login_ip?: string;
  created_at: string;
  signup_source?: string;
}

interface WalletInfo {
  address: string;
  chain: string;
  is_primary: boolean;
  balance_usd: number;
  transaction_count: number;
  first_seen_at: string;
  risk_score?: number;
}

interface RiskAssessment {
  overall_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  factors: Array<{
    name: string;
    status: 'pass' | 'warning' | 'fail';
    detail: string;
  }>;
  chainalysis_score?: string;
  last_checked_at: string;
}

interface UserStats {
  portfolio_value_usd: number;
  transaction_count_30d: number;
  conversation_count_30d: number;
  project_count: number;
  total_volume_usd: number;
}
```

### Get User Transactions

```typescript
// GET /admin/users/{id}/transactions
interface GetUserTransactionsResponse {
  success: true;
  data: {
    transactions: UserTransaction[];
    summary: {
      total_count: number;
      total_volume_usd: number;
      by_type: Record<string, number>;
    };
    pagination: Pagination;
  };
}

interface UserTransaction {
  id: string;
  type: 'swap' | 'supply' | 'borrow' | 'repay' | 'withdraw' | 'bridge' | 'stake';
  chain: string;
  timestamp: string;
  amount_usd: number;
  details: string;
  status: 'success' | 'failed' | 'pending';
  tx_hash: string;
  gas_usd?: number;
}
```

### Suspend User

```typescript
// POST /admin/users/{id}/suspend
interface SuspendUserRequest {
  reason: string;
  notes?: string;
  duration_days?: number;  // null = indefinite
  send_notification?: boolean;
}
```

### Activate User

```typescript
// POST /admin/users/{id}/activate
interface ActivateUserRequest {
  notes?: string;
}
```

---

## 🎬 Motion Design

```typescript
const userDetailAnimations = {
  tabSwitch: {
    opacity: [0, 1],
    y: [10, 0],
    transition: { duration: 0.2 }
  },
  
  riskIndicator: {
    scale: [0.8, 1],
    transition: { type: 'spring', stiffness: 300 }
  },
  
  actionConfirm: {
    scale: [1, 0.98, 1],
    transition: { duration: 0.15 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: User Detail*
