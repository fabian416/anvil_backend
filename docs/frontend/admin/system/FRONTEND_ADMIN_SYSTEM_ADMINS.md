# FRONTEND_ADMIN_SYSTEM_ADMINS

## Admin Users & RBAC Module

**User Type:** Admin (Super Admin only)  
**Module:** Admin Users  
**Route:** `/admin/admins`  
**Access Level:** Full CRUD (Super Admin) | Read-Only (Admin)

---

## 📋 Module Overview

### Title
**Admin Users** - Role-Based Access Control

### Description
Management interface for administrator accounts, roles, and permissions. Implements role-based access control (RBAC) to ensure administrators only have access to features they need.

### Key Capabilities
- Admin user management (CRUD)
- Role definition and assignment
- Granular permission configuration
- Access audit trails
- Session management
- Invitation workflow

---

## 👤 User Stories

### US-ADMIN-ADMINS-001: View Admin Users
**As a** super administrator  
**I want to** see all admin users  
**So that** I know who has platform access

**Acceptance Criteria:**
- List all admins with role, status, last login
- Filter by role, status, department
- Search by name or email
- Sort by any column

### US-ADMIN-ADMINS-002: Create Admin User
**As a** super administrator  
**I want to** invite new admin users  
**So that** team members can access the platform

**Acceptance Criteria:**
- Send invitation via email
- Assign role during invitation
- Set temporary or permanent access
- Auto-expire unaccepted invitations

### US-ADMIN-ADMINS-003: Manage Roles
**As a** super administrator  
**I want to** create and configure roles  
**So that** permissions are properly scoped

**Acceptance Criteria:**
- Create custom roles
- Define granular permissions
- Clone existing roles
- View role usage

### US-ADMIN-ADMINS-004: Audit Admin Activity
**As a** super administrator  
**I want to** see what admins have done  
**So that** I can ensure accountability

**Acceptance Criteria:**
- View login history per admin
- See actions taken
- Filter by date, action type
- Export audit logs

### US-ADMIN-ADMINS-005: Manage Sessions
**As a** super administrator  
**I want to** manage active admin sessions  
**So that** I can revoke access if needed

**Acceptance Criteria:**
- View active sessions
- Force logout specific sessions
- Terminate all sessions for user
- See session details (IP, device)

---

## 🖼️ Views & Wireframes

### View 1: Admin Users List

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👥 Admin Users                                                   [+ Invite Admin]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Users]  [Roles]  [Permissions]  [Audit Log]                                       │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  👥 12 Admins    🟢 10 Active    🟡 1 Pending    🔴 1 Suspended                 ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Role: [All ▼]    Status: [All ▼]    [🔍 Search by name or email...]              │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │   │ ADMIN                      │ ROLE          │ STATUS    │ LAST LOGIN │       ││
│  ├───┼─────────────────────────────┼───────────────┼───────────┼────────────┼───────┤│
│  │ 👤│ John Smith                 │ 🔴 Super Admin│ 🟢 Active │ 2 min ago  │ [•••] ││
│  │   │ john@anvil.app             │               │           │            │       ││
│  ├───┼─────────────────────────────┼───────────────┼───────────┼────────────┼───────┤│
│  │ 👤│ Sarah Connor               │ 🟠 Admin      │ 🟢 Active │ 1 hour ago │ [•••] ││
│  │   │ sarah@anvil.app            │               │           │            │       ││
│  ├───┼─────────────────────────────┼───────────────┼───────────┼────────────┼───────┤│
│  │ 👤│ Mike Johnson               │ 🔵 Operator   │ 🟢 Active │ 3 hours ago│ [•••] ││
│  │   │ mike@anvil.app             │               │           │            │       ││
│  ├───┼─────────────────────────────┼───────────────┼───────────┼────────────┼───────┤│
│  │ 👤│ Emily Davis                │ 🟢 Viewer     │ 🟢 Active │ 1 day ago  │ [•••] ││
│  │   │ emily@anvil.app            │               │           │            │       ││
│  ├───┼─────────────────────────────┼───────────────┼───────────┼────────────┼───────┤│
│  │ 👤│ Alex Chen                  │ 🟠 Admin      │ 🟡 Pending│ Never      │ [•••] ││
│  │   │ alex@anvil.app             │               │ Invited 2d│            │       ││
│  ├───┼─────────────────────────────┼───────────────┼───────────┼────────────┼───────┤│
│  │ 👤│ Bob Wilson                 │ 🔵 Operator   │ 🔴 Suspend│ 5 days ago │ [•••] ││
│  │   │ bob@anvil.app              │               │           │            │       ││
│  └───┴─────────────────────────────┴───────────────┴───────────┴────────────┴───────┘│
│                                                                                      │
│  Showing 6 of 12 admins                                          [1] [2] [→]        │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Admin Detail / Edit

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👤 Admin: Sarah Connor                                                     [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Profile]  [Permissions]  [Sessions]  [Activity]                                   │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  PROFILE                                                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  ┌──────┐   Name                                                             │  │
│  │  │  👤  │   ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  SC  │   │ Sarah Connor                                                │  │  │
│  │  └──────┘   └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │             Email                                                            │  │
│  │             ┌─────────────────────────────────────────────────────────────┐  │  │
│  │             │ sarah@anvil.app                                   🔒 Verified│  │  │
│  │             └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │             Department                      Phone                            │  │
│  │             ┌─────────────────────────┐    ┌─────────────────────────┐       │  │
│  │             │ [Engineering ▼]         │    │ +1 (555) 123-4567       │       │  │
│  │             └─────────────────────────┘    └─────────────────────────┘       │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ROLE & STATUS                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Role                                   Status                               │  │
│  │  ┌─────────────────────────────┐       ┌─────────────────────────────┐       │  │
│  │  │ [🟠 Admin ▼]                │       │ [🟢 Active ▼]               │       │  │
│  │  └─────────────────────────────┘       └─────────────────────────────┘       │  │
│  │                                                                               │  │
│  │  Access Expiration                                                           │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [●] Never expires    [ ] Expires on: [                        📅]      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  SECURITY                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  2FA Status: 🟢 Enabled (Authenticator App)                                  │  │
│  │  Password: Last changed 15 days ago                                          │  │
│  │  Last Login: 1 hour ago from 192.168.1.100 (San Francisco, US)              │  │
│  │                                                                               │  │
│  │  [🔑 Reset Password]    [📱 Reset 2FA]    [🚪 Force Logout All Sessions]    │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [🗑️ Delete Admin]                                   [Cancel]      [Save Changes]   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Roles Management

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  👥 Admin Users - Roles                                              [+ New Role]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Users]  [Roles]  [Permissions]  [Audit Log]                                       │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🔴 SUPER ADMIN                                                      [System]  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Full platform access including settings and admin management            │  ││
│  │  │  Users: 2 │ Permissions: All (48/48)                                     │  ││
│  │  │  ⚠️ Cannot be modified or deleted                                        │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟠 ADMIN                                                            [System]  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Full operational access, no settings or admin management                │  ││
│  │  │  Users: 3 │ Permissions: 42/48                                           │  ││
│  │  │  [View] [Clone]                                                          │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🔵 OPERATOR                                                         [System]  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Day-to-day operations, monitoring, user support                         │  ││
│  │  │  Users: 4 │ Permissions: 28/48                                           │  ││
│  │  │  [View] [Clone]                                                          │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟢 VIEWER                                                           [System]  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Read-only access to dashboards and reports                              │  ││
│  │  │  Users: 2 │ Permissions: 12/48                                           │  ││
│  │  │  [View] [Clone]                                                          │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟣 COMPLIANCE OFFICER                                               [Custom]  ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Access to compliance tools, user data, audit logs                       │  ││
│  │  │  Users: 1 │ Permissions: 18/48                                           │  ││
│  │  │  [View] [Edit] [Clone] [Delete]                                          │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 4: Role Permission Editor

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ✏️ Edit Role: Compliance Officer                                           [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ROLE INFO                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Name: [Compliance Officer        ]    Color: [🟣 Purple ▼]                  │  │
│  │  Description: [Access to compliance tools, user data, audit logs         ]   │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  PERMISSIONS                                           Selected: 18/48              │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  📊 LLM ORCHESTRATION                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [✓] View dashboard    [ ] Manage providers    [ ] Manage models        │  │  │
│  │  │ [✓] View requests     [ ] Manage budgets      [ ] Manage rankings      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  👥 USER MANAGEMENT                                                          │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [✓] View users        [✓] View user details   [ ] Edit users           │  │  │
│  │  │ [✓] View transactions [ ] Suspend users       [ ] Delete users         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  🛡️ COMPLIANCE & SECURITY                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [✓] View compliance   [✓] Manage alerts       [✓] View audit logs      │  │  │
│  │  │ [✓] Export reports    [✓] View security       [ ] Manage sanctions     │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  📂 PROJECTS                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [✓] View projects     [ ] Create projects     [ ] Edit projects        │  │  │
│  │  │ [✓] View analytics    [ ] Manage users        [ ] Delete projects      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  ⚙️ SYSTEM                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [ ] View settings     [ ] Edit settings       [ ] Manage admins        │  │  │
│  │  │ [✓] View audit logs   [ ] Feature flags       [ ] Maintenance mode     │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Delete Role]                                       [Cancel]        [Save Role]    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### List Admins

```typescript
// GET /admin/admins
interface GetAdminsResponse {
  success: true;
  data: {
    admins: AdminUser[];
    summary: {
      total: number;
      active: number;
      pending: number;
      suspended: number;
    };
    pagination: Pagination;
  };
}

interface AdminUser {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: AdminRole;
  status: 'active' | 'pending' | 'suspended' | 'deactivated';
  department?: string;
  phone?: string;
  two_factor_enabled: boolean;
  last_login_at?: string;
  last_login_ip?: string;
  created_at: string;
  access_expires_at?: string;
  invited_by?: string;
}

interface AdminRole {
  id: string;
  name: string;
  color: string;
  is_system: boolean;
  permissions: string[];
}
```

### Create Admin (Invite)

```typescript
// POST /admin/admins/invite
interface InviteAdminRequest {
  email: string;
  name: string;
  role_id: string;
  department?: string;
  access_expires_at?: string;
  send_email?: boolean;
}

interface InviteAdminResponse {
  success: true;
  data: {
    admin: AdminUser;
    invitation_url?: string;
  };
}
```

### List Roles

```typescript
// GET /admin/admins/roles
interface GetRolesResponse {
  success: true;
  data: {
    roles: AdminRole[];
    permissions: Permission[];
  };
}

interface Permission {
  id: string;
  name: string;
  description: string;
  category: string;
}
```

### Create/Update Role

```typescript
// POST /admin/admins/roles
// PUT /admin/admins/roles/{id}
interface RoleRequest {
  name: string;
  description: string;
  color: string;
  permissions: string[];
}
```

### Get Admin Sessions

```typescript
// GET /admin/admins/{id}/sessions
interface GetAdminSessionsResponse {
  success: true;
  data: {
    sessions: AdminSession[];
  };
}

interface AdminSession {
  id: string;
  ip_address: string;
  user_agent: string;
  device: string;
  location?: {
    city: string;
    country: string;
  };
  created_at: string;
  last_active_at: string;
  is_current: boolean;
}
```

### Terminate Session

```typescript
// DELETE /admin/admins/{id}/sessions/{session_id}
// DELETE /admin/admins/{id}/sessions (terminate all)
```

---

## 🎬 Motion Design

```typescript
const adminsAnimations = {
  roleColor: {
    backgroundColor: 'var(--role-color)',
    transition: { duration: 0.2 }
  },
  
  permissionToggle: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.15 }
  },
  
  sessionTerminate: {
    opacity: [1, 0],
    x: [0, -20],
    transition: { duration: 0.3 }
  },
  
  inviteSend: {
    scale: [1, 0.95, 1],
    transition: { duration: 0.2 }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const adminsShortcuts = {
  'mod+n': 'New admin invitation',
  'mod+r': 'New role',
  '/': 'Focus search',
  'delete': 'Suspend selected admin',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin Users*
