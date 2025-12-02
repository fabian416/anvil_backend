# FRONTEND_ADMIN_USERS_BANS

## Admin User Bans & Appeals Module

**User Type:** Admin  
**Module:** User Bans  
**Route:** `/admin/users/bans`  
**Access Level:** Read (All) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**User Bans & Appeals** - Account Enforcement Management

### Description
Management interface for suspended and banned user accounts, including appeal processing, reinstatement workflows, and enforcement history tracking.

### Key Capabilities
- View all suspended/banned users
- Process ban appeals
- Reinstate accounts
- Track enforcement history
- Bulk enforcement actions
- Appeal workflow management

---

## 👤 User Stories

### US-ADMIN-BANS-001: View Banned Users
**As a** platform administrator  
**I want to** see all banned/suspended users  
**So that** I can manage account enforcement

**Acceptance Criteria:**
- List all suspended and banned users
- Filter by status, reason, date
- Search by email or wallet
- Sort by any column

### US-ADMIN-BANS-002: Process Appeals
**As a** platform administrator  
**I want to** review and process ban appeals  
**So that** legitimate users can be reinstated

**Acceptance Criteria:**
- View pending appeals queue
- See appeal details and user history
- Approve or deny with notes
- Auto-notify user of decision

### US-ADMIN-BANS-003: Reinstate Users
**As a** platform administrator  
**I want to** reinstate suspended users  
**So that** cleared users can access the platform

**Acceptance Criteria:**
- One-click reinstatement
- Require reason/notes
- Option for conditional reinstatement
- Audit trail of action

### US-ADMIN-BANS-004: Track Enforcement History
**As a** platform administrator  
**I want to** see enforcement history per user  
**So that** I can make informed decisions

**Acceptance Criteria:**
- View all past suspensions/bans
- See reasons and durations
- View who took action
- Track appeal history

---

## 🖼️ Views & Wireframes

### View 1: Bans Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🚫 User Bans & Appeals                                          [📊 Export]        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  🔴 1,441 Suspended    ⛔ 234 Banned    📨 47 Appeals Pending    ✅ 12 Today   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  [All]  [Suspended]  [Banned]  [Appeals]  [Reinstated]                              │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  Status: [All ▼]  Reason: [All ▼]  Date: [All Time ▼]  [🔍 Search...]              │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │   │ USER                   │ STATUS    │ REASON          │ DATE     │ APPEAL   ││
│  ├───┼────────────────────────┼───────────┼─────────────────┼──────────┼──────────┤│
│  │ 🔴│ dave@blockchain.net    │ Suspended │ Fraud           │ Nov 28   │ 📨 Pending││
│  │   │ 0x1d89...4e5f          │           │                 │          │          ││
│  ├───┼────────────────────────┼───────────┼─────────────────┼──────────┼──────────┤│
│  │ ⛔│ scammer@evil.com       │ Banned    │ Sanctions Match │ Nov 25   │ ❌ Denied ││
│  │   │ 0x8f2a...4c3d          │           │                 │          │          ││
│  ├───┼────────────────────────┼───────────┼─────────────────┼──────────┼──────────┤│
│  │ 🔴│ john@example.com       │ Suspended │ TOS Violation   │ Nov 22   │ 📨 Pending││
│  │   │ 0x3c67...9a2b          │ Temp (7d) │                 │          │          ││
│  ├───┼────────────────────────┼───────────┼─────────────────┼──────────┼──────────┤│
│  │ ✅│ alice@crypto.io        │ Reinstated│ False Positive  │ Nov 20   │ ✅ Approved│
│  │   │ 0x7a23...8f4d          │           │                 │          │          ││
│  └───┴────────────────────────┴───────────┴─────────────────┴──────────┴──────────┘│
│                                                                                      │
│  Showing 1-50 of 1,675 records                                     [1] [2] ... [34] │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Appeals Queue

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📨 Pending Appeals (47)                                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Sort: [Oldest First ▼]    Priority: [All ▼]                                        │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  📨 APPEAL #1247 - High Priority                              Submitted: 3d ago ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  User: dave@blockchain.net                                                │  ││
│  │  │  Status: 🔴 Suspended │ Reason: Suspected Fraud                           │  ││
│  │  │  Suspended: Nov 28, 2025 by admin@anvil.app                               │  ││
│  │  │                                                                           │  ││
│  │  │  Appeal Message:                                                          │  ││
│  │  │  "I believe this suspension was made in error. The transactions flagged   │  ││
│  │  │  were legitimate DeFi arbitrage trades. I can provide proof of funds..."  │  ││
│  │  │                                                                           │  ││
│  │  │  Prior History: 0 suspensions │ Account Age: 8 months │ Volume: $125K     │  ││
│  │  │                                                                           │  ││
│  │  │  [View Full Details]        [✅ Approve Appeal]    [❌ Deny Appeal]       │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  📨 APPEAL #1245 - Normal Priority                            Submitted: 5d ago ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  User: john@example.com                                                   │  ││
│  │  │  Status: 🔴 Suspended (7d) │ Reason: TOS Violation - Spam                 │  ││
│  │  │  Suspended: Nov 22, 2025 by sarah@anvil.app                               │  ││
│  │  │                                                                           │  ││
│  │  │  Appeal Message:                                                          │  ││
│  │  │  "My account was hacked and someone else sent those messages. I've       │  ││
│  │  │  since enabled 2FA and changed my password..."                            │  ││
│  │  │                                                                           │  ││
│  │  │  Prior History: 1 warning │ Account Age: 3 months │ Volume: $12K          │  ││
│  │  │                                                                           │  ││
│  │  │  [View Full Details]        [✅ Approve Appeal]    [❌ Deny Appeal]       │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Appeal Decision Modal

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ✅ Approve Appeal #1247                                                    [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  USER SUMMARY                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  dave@blockchain.net │ Suspended Nov 28 │ Reason: Suspected Fraud            │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  DECISION                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Reinstatement Type                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [●] Full Reinstatement - Restore all access                             │  │  │
│  │  │ [ ] Conditional - With restrictions                                     │  │  │
│  │  │ [ ] Probationary - Monitoring period                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Decision Notes *                                                            │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ After review of transaction history and user-provided documentation,   │  │  │
│  │  │ the flagged transactions appear to be legitimate arbitrage activity.   │  │  │
│  │  │ No evidence of fraud found. Approving full reinstatement.              │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  [✓] Send notification email to user                                         │  │
│  │  [✓] Include decision notes in email                                         │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Cancel]                                              [✅ Approve & Reinstate]     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### List Bans

```typescript
// GET /admin/users/bans
interface GetBansRequest {
  page?: number;
  page_size?: number;
  status?: 'suspended' | 'banned' | 'reinstated';
  reason?: string;
  has_appeal?: boolean;
  appeal_status?: 'pending' | 'approved' | 'denied';
  search?: string;
}

interface GetBansResponse {
  success: true;
  data: {
    bans: UserBan[];
    summary: {
      suspended: number;
      banned: number;
      appeals_pending: number;
      reinstated_today: number;
    };
    pagination: Pagination;
  };
}

interface UserBan {
  id: string;
  user_id: string;
  email: string;
  wallet_address?: string;
  status: 'suspended' | 'banned' | 'reinstated';
  reason: string;
  reason_category: string;
  notes?: string;
  duration_days?: number;
  expires_at?: string;
  created_at: string;
  created_by: string;
  reinstated_at?: string;
  reinstated_by?: string;
  appeal?: BanAppeal;
}

interface BanAppeal {
  id: string;
  status: 'pending' | 'approved' | 'denied';
  message: string;
  submitted_at: string;
  decided_at?: string;
  decided_by?: string;
  decision_notes?: string;
}
```

### Get Appeals

```typescript
// GET /admin/users/bans/appeals
interface GetAppealsResponse {
  success: true;
  data: {
    appeals: AppealWithContext[];
    total_pending: number;
    pagination: Pagination;
  };
}

interface AppealWithContext {
  appeal: BanAppeal;
  ban: UserBan;
  user: {
    id: string;
    email: string;
    account_age_days: number;
    total_volume_usd: number;
    prior_suspensions: number;
    prior_warnings: number;
  };
}
```

### Process Appeal

```typescript
// POST /admin/users/bans/appeals/{id}/decide
interface DecideAppealRequest {
  decision: 'approve' | 'deny';
  reinstatement_type?: 'full' | 'conditional' | 'probationary';
  conditions?: string[];
  probation_days?: number;
  notes: string;
  send_notification?: boolean;
}
```

### Reinstate User

```typescript
// POST /admin/users/bans/{id}/reinstate
interface ReinstateRequest {
  notes: string;
  reinstatement_type: 'full' | 'conditional' | 'probationary';
  conditions?: string[];
}
```

---

## 🎬 Motion Design

```typescript
const bansAnimations = {
  appealCard: {
    y: [10, 0],
    opacity: [0, 1],
    transition: { duration: 0.3 }
  },
  
  statusChange: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.3 }
  },
  
  approveButton: {
    backgroundColor: ['#10B981', '#059669'],
    transition: { duration: 0.2 }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const bansShortcuts = {
  'a': 'View appeals',
  'r': 'Reinstate selected',
  '/': 'Focus search',
  'j/k': 'Navigate list',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: User Bans & Appeals*
