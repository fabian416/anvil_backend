# FRONTEND_ADMIN_PROJECTS_USERS

## Admin Project Users Module

**User Type:** Admin  
**Module:** Project User Management  
**Route:** `/admin/projects/:id/users`  
**Access Level:** Full CRUD (Admin) | Read-Only (Operator)

---

## 📋 Module Overview

### Title
**Project Users** - User Access & Management

### Description
Management interface for users assigned to a specific project. Enables viewing user activity, managing access levels, monitoring usage patterns, and handling user-specific configurations.

---

## 👤 User Stories

### US-ADMIN-PROJ-USERS-001: View Project Users
**As a** platform administrator  
**I want to** see all users assigned to a project  
**So that** I understand who has access

### US-ADMIN-PROJ-USERS-002: Manage User Access
**As a** platform administrator  
**I want to** add/remove users from projects  
**So that** I control who can use the project

### US-ADMIN-PROJ-USERS-003: Monitor User Activity
**As a** platform administrator  
**I want to** see user activity metrics  
**So that** I identify active and inactive users

### US-ADMIN-PROJ-USERS-004: Set User Permissions
**As a** platform administrator  
**I want to** configure per-user permissions  
**So that** users have appropriate access levels

---

## 🖼️ Views & Wireframes

### View 1: Project Users List

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👥 Project Users: Aave                                        [+ Invite Users]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  👥 1,245 Users    ✅ 234 Active (24h)    📊 12,450 Conversations    💰 $890   ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ Status: [All ▼]  Role: [All ▼]  Activity: [All ▼]  [🔍 Search...]  [📥 Export]││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ □ │ USER                    │ ROLE    │ JOINED     │ LAST ACTIVE │ CONVOS │ ⋯  ││
│  ├───┼─────────────────────────┼─────────┼────────────┼─────────────┼────────┼────┤│
│  │ □ │ 👤 john@example.com     │ User    │ Nov 15     │ 2 min ago   │ 45     │ ⋯  ││
│  │   │    0x1234...5678        │         │            │ 🟢 Online   │        │    ││
│  ├───┼─────────────────────────┼─────────┼────────────┼─────────────┼────────┼────┤│
│  │ □ │ 👤 alice@company.io     │ User    │ Nov 20     │ 1 hour ago  │ 23     │ ⋯  ││
│  │   │    0xabcd...ef01        │         │            │             │        │    ││
│  ├───┼─────────────────────────┼─────────┼────────────┼─────────────┼────────┼────┤│
│  │ □ │ 👤 bob@defi.xyz         │ Power   │ Oct 5      │ 3 hours ago │ 156    │ ⋯  ││
│  │   │    0x9876...5432        │ User    │            │             │        │    ││
│  ├───┼─────────────────────────┼─────────┼────────────┼─────────────┼────────┼────┤│
│  │ □ │ 👤 carol@trader.com     │ User    │ Nov 28     │ 2 days ago  │ 8      │ ⋯  ││
│  │   │    0xfedc...ba98        │         │            │ ⚠️ Inactive │        │    ││
│  ├───┼─────────────────────────┼─────────┼────────────┼─────────────┼────────┼────┤│
│  │ □ │ 👤 dave@whale.io        │ VIP     │ Sep 12     │ 30 min ago  │ 892    │ ⋯  ││
│  │   │    0x1111...2222        │         │            │             │        │    ││
│  └───┴─────────────────────────┴─────────┴────────────┴─────────────┴────────┴────┘│
│                                                                                      │
│  Showing 1-50 of 1,245 users                              [← Previous] [Next →]     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: User Detail Panel

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👤 User Details: john@example.com                                          [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Profile]  [Activity]  [Permissions]  [Transactions]                               │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  USER PROFILE                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  ┌──────────┐  john@example.com                                              │  │
│  │  │    👤    │  Wallet: 0x1234...5678                                         │  │
│  │  │          │  Privy ID: did:privy:abc123                                    │  │
│  │  └──────────┘                                                                │  │
│  │                                                                               │  │
│  │  Role: [User ▼]                Status: [🟢 Active ▼]                        │  │
│  │                                                                               │  │
│  │  Joined: November 15, 2025                                                   │  │
│  │  Last Active: 2 minutes ago                                                  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  USAGE STATISTICS                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐    │  │
│  │  │ Conversations   │ Messages        │ Transactions    │ LLM Cost        │    │  │
│  │  │ 45              │ 892             │ 12              │ $4.56           │    │  │
│  │  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘    │  │
│  │                                                                               │  │
│  │  ACTIVITY (Last 30 Days)                                                     │  │
│  │  ┌───────────────────────────────────────────────────────────────────────┐    │  │
│  │  │    ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇▆▅▄▃▂▁                                        │    │  │
│  │  │    Nov 1                                                    Dec 1     │    │  │
│  │  └───────────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RECENT CONVERSATIONS                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  • "Help me supply ETH to Aave" - 2 min ago                      [View →]    │  │
│  │  • "What's my current health factor?" - 1 hour ago               [View →]    │  │
│  │  • "Compare borrow rates" - Yesterday                            [View →]    │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [🚫 Suspend User]  [🗑️ Remove from Project]                                [Close] │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Project Users

```typescript
// GET /admin/projects/{id}/users
interface GetProjectUsersResponse {
  success: true;
  data: {
    users: ProjectUser[];
    pagination: Pagination;
    summary: {
      total: number;
      active_24h: number;
      total_conversations: number;
      total_cost_usd: number;
    };
  };
}

interface ProjectUser {
  id: string;
  privy_id: string;
  email?: string;
  wallet_address?: string;
  role: 'user' | 'power_user' | 'vip';
  status: 'active' | 'suspended' | 'pending';
  joined_at: string;
  last_active_at: string;
  stats: {
    conversations: number;
    messages: number;
    transactions: number;
    llm_cost_usd: number;
  };
}
```

### Update User

```typescript
// PUT /admin/projects/{id}/users/{user_id}
interface UpdateProjectUserRequest {
  role?: string;
  status?: string;
  permissions?: UserPermissions;
}
```

### Remove User

```typescript
// DELETE /admin/projects/{id}/users/{user_id}
```

---

## 🎬 Motion Design

```typescript
const usersAnimations = {
  rowHover: {
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
    transition: { duration: 0.15 }
  },
  
  onlineIndicator: {
    scale: [1, 1.2, 1],
    transition: { duration: 1, repeat: Infinity }
  },
  
  activityChart: {
    pathLength: [0, 1],
    transition: { duration: 1 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Project Users*
