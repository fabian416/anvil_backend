# FRONTEND_ADMIN_USERS_LIST

## Admin Platform Users Module

**User Type:** Admin  
**Module:** All Users  
**Route:** `/admin/users`  
**Access Level:** Read (All) | Write (Admin+)

---

## 📋 Module Overview

### Title
**All Users** - Platform-Wide User Management

### Description
Centralized view of all platform users across all projects. Enables administrators to search, filter, analyze user base, and take actions on user accounts.

### Key Capabilities
- View all platform users
- Advanced search and filtering
- User segmentation
- Bulk actions
- Export user data
- Quick user actions

---

## 👤 User Stories

### US-ADMIN-USERS-001: View All Users
**As a** platform administrator  
**I want to** see all platform users  
**So that** I can manage the user base

### US-ADMIN-USERS-002: Search and Filter Users
**As a** platform administrator  
**I want to** search and filter users  
**So that** I can find specific users quickly

### US-ADMIN-USERS-003: Analyze User Segments
**As a** platform administrator  
**I want to** see user segmentation  
**So that** I understand user distribution

### US-ADMIN-USERS-004: Take Bulk Actions
**As a** platform administrator  
**I want to** perform bulk actions  
**So that** I can manage users efficiently

---

## 🖼️ Views & Wireframes

### View 1: Users List

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👥 All Users                                              [📥 Export] [+ Add User] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  👥 24,567 Total    🟢 18,234 Active    🟡 4,892 Inactive    🔴 1,441 Suspended ││
│  │     +456 this week      74% of total        20% of total         6% of total    ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ Status: [All ▼]  Tier: [All ▼]  Project: [All ▼]  Chain: [All ▼]  KYC: [All ▼]││
│  │ Joined: [All Time ▼]  [🔍 Search by email, wallet, or name...]  [Clear Filters]││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ □ │ USER                        │ STATUS   │ TIER    │ PROJECTS│ JOINED   │     ││
│  ├───┼─────────────────────────────┼──────────┼─────────┼─────────┼──────────┼─────┤│
│  │ □ │ alice@defi.co               │ 🟢 Active│ ⭐ Pro   │ 3       │ Nov 15   │[•••]││
│  │   │ 0x7a23...8f4d │ 🔵 Verified │          │         │         │          │     ││
│  ├───┼─────────────────────────────┼──────────┼─────────┼─────────┼──────────┼─────┤│
│  │ □ │ bob@crypto.com              │ 🟢 Active│ 💎 Elite│ 5       │ Oct 28   │[•••]││
│  │   │ 0x9b45...2c1e │ 🔵 Verified │          │         │         │          │     ││
│  ├───┼─────────────────────────────┼──────────┼─────────┼─────────┼──────────┼─────┤│
│  │ □ │ carol@web3.io               │ 🟡 Inactive│ 🆓 Free │ 1       │ Dec 1    │[•••]││
│  │   │ 0x3c67...9a2b │ ⚪ Pending  │          │         │         │          │     ││
│  ├───┼─────────────────────────────┼──────────┼─────────┼─────────┼──────────┼─────┤│
│  │ □ │ dave@blockchain.net         │ 🔴 Suspend│ ⭐ Pro   │ 2       │ Sep 10   │[•••]││
│  │   │ 0x1d89...4e5f │ 🔵 Verified │ Fraud    │         │         │          │     ││
│  ├───┼─────────────────────────────┼──────────┼─────────┼─────────┼──────────┼─────┤│
│  │ □ │ eve@eth.org                 │ 🟢 Active│ 🆓 Free │ 1       │ Nov 30   │[•••]││
│  │   │ No wallet connected         │          │         │         │          │     ││
│  └───┴─────────────────────────────┴──────────┴─────────┴─────────┴──────────┴─────┘│
│                                                                                      │
│  ┌─ Selected: 0 ───────────────────────────────────────────────────────────────────┐│
│  │ [Select All]  [📧 Email Selected]  [⏸️ Suspend Selected]  [📥 Export Selected] ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Showing 1-50 of 24,567 users                                    [1] [2] ... [492]  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: User Segmentation

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👥 User Segmentation                                                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  BY TIER                                      BY ACTIVITY (Last 30d)                │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  🆓 Free        ██████████████ 68% │      │  Power (10+ tx)    ████       12% │ │
│  │                 16,706 users       │      │                    2,948 users    │ │
│  │                                    │      │                                    │ │
│  │  ⭐ Pro         ██████       24%   │      │  Active (3-9 tx)   ████████   28% │ │
│  │                 5,896 users        │      │                    6,879 users    │ │
│  │                                    │      │                                    │ │
│  │  💎 Elite       ██            8%   │      │  Casual (1-2 tx)   ██████████ 35% │ │
│  │                 1,965 users        │      │                    8,598 users    │ │
│  │                                    │      │                                    │ │
│  │                                    │      │  Inactive (0 tx)   ██████     25% │ │
│  │                                    │      │                    6,142 users    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
│  BY PRIMARY CHAIN                             BY KYC STATUS                         │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  Ethereum      █████████████  52%  │      │  🔵 Verified      ██████████  42% │ │
│  │  Arbitrum      ██████         28%  │      │  ⚪ Pending       ████        15% │ │
│  │  Polygon       ████           15%  │      │  ⚫ Not Started   ██████████  43% │ │
│  │  Base          █              5%   │      │                                    │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
│  BY SIGNUP SOURCE                             USER GROWTH                           │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  Direct        ████████████   48%  │      │  2K ┤            ╭──╮    ╭──      │ │
│  │  Referral      ██████         26%  │      │     │     ╭─────╯  ╰────╯         │ │
│  │  Social        ████           16%  │      │  1K ┤ ────╯                        │ │
│  │  Partner       ██             10%  │      │     └────────────────────────▶    │ │
│  │                                    │      │      Oct    Nov    Dec            │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### List Users

```typescript
// GET /admin/users
interface GetUsersRequest {
  page?: number;
  page_size?: number;
  status?: 'active' | 'inactive' | 'suspended';
  tier?: 'free' | 'pro' | 'elite';
  project_id?: string;
  chain?: string;
  kyc_status?: 'verified' | 'pending' | 'not_started';
  joined_after?: string;
  joined_before?: string;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

interface GetUsersResponse {
  success: true;
  data: {
    users: PlatformUser[];
    summary: {
      total: number;
      active: number;
      inactive: number;
      suspended: number;
      new_this_week: number;
    };
    pagination: Pagination;
  };
}

interface PlatformUser {
  id: string;
  email: string;
  name?: string;
  status: 'active' | 'inactive' | 'suspended';
  suspension_reason?: string;
  tier: 'free' | 'pro' | 'elite';
  kyc_status: 'verified' | 'pending' | 'not_started';
  wallets: Array<{
    address: string;
    chain: string;
    is_primary: boolean;
  }>;
  projects: string[];
  project_count: number;
  transaction_count: number;
  total_volume_usd: number;
  last_active_at?: string;
  created_at: string;
  signup_source?: string;
}
```

### Get User Segments

```typescript
// GET /admin/users/segments
interface GetUserSegmentsResponse {
  success: true;
  data: {
    by_tier: Record<string, number>;
    by_activity: Record<string, number>;
    by_chain: Record<string, number>;
    by_kyc: Record<string, number>;
    by_source: Record<string, number>;
    growth_timeseries: TimeSeriesPoint[];
  };
}
```

### Bulk Actions

```typescript
// POST /admin/users/bulk
interface BulkUserActionRequest {
  user_ids: string[];
  action: 'suspend' | 'activate' | 'send_email' | 'export';
  reason?: string;
  email_template_id?: string;
}
```

---

## 🎬 Motion Design

```typescript
const usersAnimations = {
  rowSelect: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    transition: { duration: 0.15 }
  },
  
  bulkActionBar: {
    y: [20, 0],
    opacity: [0, 1],
    transition: { duration: 0.2 }
  },
  
  segmentHover: {
    scale: 1.02,
    transition: { duration: 0.2 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: All Users*
