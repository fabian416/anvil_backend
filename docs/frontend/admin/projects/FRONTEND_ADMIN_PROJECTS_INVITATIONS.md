# FRONTEND_ADMIN_PROJECTS_INVITATIONS

## Admin Project Invitations Module

**User Type:** Admin  
**Module:** Project Invitations  
**Route:** `/admin/projects/:id/invitations`  
**Access Level:** Full CRUD (Admin)

---

## 📋 Module Overview

### Title
**Project Invitations** - Access Control & Invites

### Description
Management interface for project invitations, enabling administrators to invite users to private or invite-only projects, manage pending invitations, configure invitation settings, and track invitation conversions.

### Key Capabilities
- Send individual invitations via email
- Generate shareable invite links
- Bulk invitation upload
- Track invitation status
- Set invitation expiration
- Configure access permissions
- View conversion analytics

---

## 👤 User Stories

### US-ADMIN-INVITE-001: Send Email Invitations
**As a** platform administrator  
**I want to** invite users via email  
**So that** specific people can access the project

### US-ADMIN-INVITE-002: Generate Invite Links
**As a** platform administrator  
**I want to** create shareable invite links  
**So that** I can distribute access easily

### US-ADMIN-INVITE-003: Manage Pending Invitations
**As a** platform administrator  
**I want to** see and manage pending invites  
**So that** I can track invitation status

### US-ADMIN-INVITE-004: Bulk Import Invitations
**As a** platform administrator  
**I want to** upload a CSV of emails  
**So that** I can invite many users at once

### US-ADMIN-INVITE-005: Track Conversion
**As a** platform administrator  
**I want to** see invitation acceptance rates  
**So that** I can optimize outreach

---

## 🖼️ Views & Wireframes

### View 1: Invitations Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ✉️ Invitations: Aave                              [🔗 Invite Link] [+ New Invite]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  📨 156 Sent    ⏳ 42 Pending    ✅ 98 Accepted    ❌ 16 Expired                ││
│  │                                         63% conversion rate                     ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  Status: [All ▼]    [🔍 Search by email...]                                        │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ □ │ EMAIL                       │ STATUS     │ SENT       │ EXPIRES  │ ACTIONS  ││
│  ├───┼─────────────────────────────┼────────────┼────────────┼──────────┼──────────┤│
│  │ □ │ alice@defi.co               │ ⏳ Pending │ 2h ago     │ 5 days   │ [↻] [🗑️]││
│  │ □ │ bob@protocol.xyz            │ ⏳ Pending │ 1d ago     │ 4 days   │ [↻] [🗑️]││
│  │ □ │ carol@web3.io               │ ✅ Accepted│ 3d ago     │ -        │ [👤]     ││
│  │ □ │ dave@crypto.com             │ ✅ Accepted│ 5d ago     │ -        │ [👤]     ││
│  │ □ │ eve@blockchain.net          │ ❌ Expired │ 10d ago    │ Expired  │ [↻]      ││
│  │ □ │ frank@eth.org               │ ⏳ Pending │ 12h ago    │ 6 days   │ [↻] [🗑️]││
│  └───┴─────────────────────────────┴────────────┴────────────┴──────────┴──────────┘│
│                                                                                      │
│  ┌─ Selected: 0 ───────────────────────────────────────────────────────────────────┐│
│  │ [Select All]  [↻ Resend Selected]  [🗑️ Revoke Selected]                        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Invite Links ──────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  Active Link: https://anvil.app/invite/aave/abc123xyz                           ││
│  │  Uses: 45/100    Expires: Dec 15, 2025                                          ││
│  │  [📋 Copy]  [⚙️ Configure]  [🔄 Regenerate]                                     ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: New Invitation Modal

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ✉️ Send Invitation                                                         [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Email]  [Bulk Import]                                                             │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  EMAIL ADDRESS *                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │ [user@example.com                                                            ]│  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  PERSONAL MESSAGE (optional)                                                        │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │ Hi! You're invited to try our Aave assistant. It can help you manage your    │  │
│  │ lending positions and monitor health factors.                                 │  │
│  │                                                                               │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│  Characters: 124/500                                                                │
│                                                                                      │
│  INVITATION SETTINGS                                                                │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Expiration                                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [7 days ▼]                                                              │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Initial Role                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [User ▼]                                                                │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  EMAIL PREVIEW                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                         │  │  │
│  │  │  You're invited to Aave on Anvil                                        │  │  │
│  │  │                                                                         │  │  │
│  │  │  Hi! You're invited to try our Aave assistant. It can help             │  │  │
│  │  │  you manage your lending positions and monitor health factors.          │  │  │
│  │  │                                                                         │  │  │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐    │  │  │
│  │  │  │              Accept Invitation                                  │    │  │  │
│  │  │  └─────────────────────────────────────────────────────────────────┘    │  │  │
│  │  │                                                                         │  │  │
│  │  │  This invitation expires in 7 days.                                     │  │  │
│  │  │                                                                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Cancel]                                                    [Send Invitation]      │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Invite Link Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔗 Configure Invite Link                                                   [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  CURRENT LINK                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  https://anvil.app/invite/aave/abc123xyz                           [📋 Copy] │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  LINK SETTINGS                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Maximum Uses                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [100        ]        (0 = unlimited)                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │  Current uses: 45                                                            │  │
│  │                                                                               │  │
│  │  Expiration Date                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [December 15, 2025 📅]                                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Default Role for New Users                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [User ▼]                                                                │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Restrictions                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [ ] Require email domain: [                                            ]│  │  │
│  │  │ [ ] Require wallet connection                                           │  │  │
│  │  │ [ ] Require minimum wallet balance: [$                                 ]│  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  LINK STATUS                                                                        │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  [●] Active    [ ] Disabled                                                  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [🔄 Regenerate Link]                              [Cancel]        [Save Changes]   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Project Invitations

```typescript
// GET /admin/projects/{id}/invitations
interface GetInvitationsResponse {
  success: true;
  data: {
    invitations: Invitation[];
    invite_link: InviteLink | null;
    summary: {
      sent: number;
      pending: number;
      accepted: number;
      expired: number;
      conversion_rate: number;
    };
    pagination: Pagination;
  };
}

interface Invitation {
  id: string;
  email: string;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  role: string;
  sent_at: string;
  expires_at: string;
  accepted_at?: string;
  user_id?: string;
  message?: string;
}

interface InviteLink {
  id: string;
  code: string;
  url: string;
  max_uses: number;
  current_uses: number;
  expires_at: string;
  is_active: boolean;
  default_role: string;
  restrictions: {
    email_domain?: string;
    require_wallet?: boolean;
    min_wallet_balance_usd?: number;
  };
}
```

### Create Invitation

```typescript
// POST /admin/projects/{id}/invitations
interface CreateInvitationRequest {
  email: string;
  message?: string;
  role?: string;
  expires_in_days?: number;
}
```

### Bulk Create Invitations

```typescript
// POST /admin/projects/{id}/invitations/bulk
interface BulkCreateInvitationsRequest {
  emails: string[];
  message?: string;
  role?: string;
  expires_in_days?: number;
}

interface BulkCreateInvitationsResponse {
  success: true;
  data: {
    created: number;
    skipped: number;
    errors: Array<{ email: string; reason: string }>;
  };
}
```

### Manage Invite Link

```typescript
// PUT /admin/projects/{id}/invitations/link
interface UpdateInviteLinkRequest {
  max_uses?: number;
  expires_at?: string;
  default_role?: string;
  is_active?: boolean;
  restrictions?: {
    email_domain?: string;
    require_wallet?: boolean;
    min_wallet_balance_usd?: number;
  };
}

// POST /admin/projects/{id}/invitations/link/regenerate
interface RegenerateInviteLinkResponse {
  success: true;
  data: {
    invite_link: InviteLink;
  };
}
```

### Resend Invitation

```typescript
// POST /admin/projects/{id}/invitations/{invitation_id}/resend
interface ResendInvitationResponse {
  success: true;
  data: {
    invitation: Invitation;
  };
}
```

### Revoke Invitation

```typescript
// DELETE /admin/projects/{id}/invitations/{invitation_id}
interface RevokeInvitationResponse {
  success: true;
  data: {
    revoked: true;
  };
}
```

---

## 🎬 Motion Design

```typescript
const invitationsAnimations = {
  statusBadge: {
    scale: [0.8, 1],
    opacity: [0, 1],
    transition: { duration: 0.2 }
  },
  
  emailSend: {
    x: [0, 50],
    opacity: [1, 0],
    transition: { duration: 0.3 }
  },
  
  linkCopy: {
    scale: [1, 1.1, 1],
    transition: { duration: 0.2 }
  },
  
  rowSelect: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    transition: { duration: 0.15 }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const invitationsShortcuts = {
  'mod+n': 'New invitation',
  'mod+l': 'Copy invite link',
  'mod+a': 'Select all',
  'delete': 'Revoke selected',
  'r': 'Resend selected',
};
```

---

## ⚠️ Error Handling

```typescript
const invitationsErrorCodes = {
  INV_VAL_001: 'Invalid email format',
  INV_VAL_002: 'Email already invited',
  INV_VAL_003: 'User already has access',
  INV_LIMIT_001: 'Invitation limit reached',
  INV_LINK_001: 'Invite link expired',
  INV_LINK_002: 'Invite link usage exceeded',
  INV_SEND_001: 'Failed to send invitation email',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Project Invitations*
