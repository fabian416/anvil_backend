# FRONTEND_ADMIN_SYSTEM_AUDIT

## Admin Audit Logs Module

**User Type:** Admin  
**Module:** Audit Logs  
**Route:** `/admin/audit`  
**Access Level:** Read (Admin+) | Export (Super Admin)

---

## 📋 Module Overview

### Title
**Audit Logs** - Security & Compliance Trail

### Description
Comprehensive audit logging system tracking all administrative actions, security events, and system changes. Essential for compliance, incident investigation, and security monitoring.

### Key Capabilities
- Real-time audit event stream
- Advanced filtering and search
- Event categorization
- Actor and target tracking
- Export for compliance
- Retention policy management

---

## 👤 User Stories

### US-ADMIN-AUDIT-001: View Audit Events
**As a** platform administrator  
**I want to** see all audit events  
**So that** I can monitor platform activity

**Acceptance Criteria:**
- Real-time event stream
- Event details on click
- Color-coded by severity
- Timestamp with timezone

### US-ADMIN-AUDIT-002: Filter and Search
**As a** platform administrator  
**I want to** filter and search events  
**So that** I can find specific activities

**Acceptance Criteria:**
- Filter by date range
- Filter by actor (admin user)
- Filter by event type
- Filter by target resource
- Full-text search

### US-ADMIN-AUDIT-003: Investigate Incidents
**As a** platform administrator  
**I want to** investigate security incidents  
**So that** I can understand what happened

**Acceptance Criteria:**
- View related events
- See before/after states
- Track actor's full session
- Timeline visualization

### US-ADMIN-AUDIT-004: Export Audit Data
**As a** super administrator  
**I want to** export audit logs  
**So that** I can meet compliance requirements

**Acceptance Criteria:**
- Export as CSV/JSON
- Date range selection
- Filtered export
- Scheduled exports

---

## 🖼️ Views & Wireframes

### View 1: Audit Log Stream

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📋 Audit Logs                                            [📥 Export] [⚙️ Settings] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Filters ───────────────────────────────────────────────────────────────────────┐│
│  │ Date: [Last 24h ▼]  Actor: [All ▼]  Type: [All ▼]  Severity: [All ▼]          ││
│  │ Resource: [All ▼]  [🔍 Search events...]                        [Clear Filters] ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  📊 2,456 Events    🔴 12 Critical    🟠 45 Warning    🔵 2,399 Info           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🔴 14:32:15  SECURITY_ALERT                                                    ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Failed login attempt (5th attempt)                                       │  ││
│  │  │  Actor: unknown@email.com │ IP: 185.220.101.45 │ Location: Unknown        │  ││
│  │  │  Target: Authentication system                                            │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟠 14:31:42  PERMISSION_CHANGE                                                 ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Admin role permissions updated                                           │  ││
│  │  │  Actor: john@anvil.app │ IP: 192.168.1.100 │ Location: San Francisco     │  ││
│  │  │  Target: Role "Operator" │ Changes: +2 permissions, -1 permission        │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🔵 14:30:55  USER_ACTION                                                       ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  User suspended                                                           │  ││
│  │  │  Actor: sarah@anvil.app │ IP: 10.0.0.50 │ Location: New York             │  ││
│  │  │  Target: User #12345 (bob@example.com) │ Reason: Suspicious activity      │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🔵 14:29:30  CONFIG_CHANGE                                                     ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Feature flag toggled                                                     │  ││
│  │  │  Actor: john@anvil.app │ IP: 192.168.1.100 │ Location: San Francisco     │  ││
│  │  │  Target: ENABLE_FLASH_LOANS │ Change: false → true                        │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🔵 14:28:15  LOGIN_SUCCESS                                                     ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Admin login successful                                                   │  ││
│  │  │  Actor: mike@anvil.app │ IP: 172.16.0.25 │ Location: London              │  ││
│  │  │  Device: Chrome 119 on MacOS │ 2FA: Verified                              │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ● Live updating                                             [Load More Events]    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Event Detail

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📋 Event Detail: evt_8a7b3c2d                                              [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  EVENT SUMMARY                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  🟠 PERMISSION_CHANGE                                                        │  │
│  │  Admin role permissions updated                                               │  │
│  │                                                                               │  │
│  │  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐   │  │
│  │  │ Event ID        │ Timestamp       │ Severity        │ Category        │   │  │
│  │  │ evt_8a7b3c2d    │ Dec 1, 14:31:42 │ 🟠 Warning      │ Access Control  │   │  │
│  │  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘   │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ACTOR                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  👤 John Smith (john@anvil.app)                                              │  │
│  │  Role: Super Admin                                                            │  │
│  │  IP Address: 192.168.1.100                                                    │  │
│  │  Location: San Francisco, CA, United States                                   │  │
│  │  Device: Chrome 119 on MacOS 14.1                                            │  │
│  │  Session: sess_xyz789 (started 2 hours ago)                                  │  │
│  │                                                                               │  │
│  │  [View Actor's Full Session →]                                               │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  TARGET                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Resource Type: Role                                                          │  │
│  │  Resource ID: role_operator                                                   │  │
│  │  Resource Name: Operator                                                      │  │
│  │                                                                               │  │
│  │  [View Resource →]                                                           │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CHANGES                                                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  BEFORE                              AFTER                                   │  │
│  │  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐  │  │
│  │  │ permissions: [              │    │ permissions: [                      │  │  │
│  │  │   "view_dashboard",         │    │   "view_dashboard",                 │  │  │
│  │  │   "view_users",             │    │   "view_users",                     │  │  │
│  │  │ - "edit_users",             │    │   "view_projects",                  │  │  │
│  │  │   "view_projects"           │    │ + "edit_projects",                  │  │  │
│  │  │ ]                           │    │ + "manage_knowledge"                │  │  │
│  │  │                             │    │ ]                                   │  │  │
│  │  └─────────────────────────────┘    └─────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Summary: Added 2 permissions, removed 1 permission                          │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RELATED EVENTS                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  • 14:31:40 - Role "Operator" opened for editing                             │  │
│  │  • 14:31:45 - Permission change notification sent to 4 admins                │  │
│  │  [View All Related →]                                                        │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Export Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📥 Export Audit Logs                                                       [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  DATE RANGE                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  From                                   To                                   │  │
│  │  ┌─────────────────────────────┐       ┌─────────────────────────────┐       │  │
│  │  │ [November 1, 2025 📅]       │       │ [December 1, 2025 📅]       │       │  │
│  │  └─────────────────────────────┘       └─────────────────────────────┘       │  │
│  │                                                                               │  │
│  │  Quick Select: [24h] [7d] [30d] [90d] [Custom]                               │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  FILTERS (Optional)                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Event Types                                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [✓] Authentication    [✓] Permission Changes    [✓] Config Changes     │  │  │
│  │  │ [✓] User Actions      [✓] Security Alerts       [✓] System Events      │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Severity Levels                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [✓] Critical    [✓] Warning    [✓] Info                                │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Actors (leave empty for all)                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [                                                                      ]│  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  EXPORT FORMAT                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Format                                 Include                              │  │
│  │  ┌─────────────────────────────┐       ┌─────────────────────────────┐       │  │
│  │  │ [●] CSV   [ ] JSON          │       │ [✓] Actor details           │       │  │
│  │  │ [ ] PDF   [ ] SIEM Format   │       │ [✓] IP addresses            │       │  │
│  │  └─────────────────────────────┘       │ [✓] Change diffs            │       │  │
│  │                                        │ [ ] Raw request data        │       │  │
│  │                                        └─────────────────────────────┘       │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  PREVIEW                                                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Estimated events: 45,230                                                    │  │
│  │  Estimated file size: 12.5 MB                                                │  │
│  │  Estimated time: ~30 seconds                                                 │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Schedule Recurring Export]                               [Cancel]    [Export Now] │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Audit Events

```typescript
// GET /admin/audit
interface GetAuditEventsRequest {
  page?: number;
  page_size?: number;
  start_date?: string;
  end_date?: string;
  event_types?: string[];
  severity?: string[];
  actor_id?: string;
  resource_type?: string;
  resource_id?: string;
  search?: string;
}

interface GetAuditEventsResponse {
  success: true;
  data: {
    events: AuditEvent[];
    summary: {
      total: number;
      critical: number;
      warning: number;
      info: number;
    };
    pagination: Pagination;
  };
}

interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: string;
  event_category: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  actor: {
    id?: string;
    email?: string;
    name?: string;
    role?: string;
    ip_address: string;
    user_agent?: string;
    location?: {
      city: string;
      country: string;
    };
    session_id?: string;
  };
  target?: {
    type: string;
    id: string;
    name?: string;
  };
  changes?: {
    before: Record<string, any>;
    after: Record<string, any>;
  };
  metadata?: Record<string, any>;
}
```

### Get Event Detail

```typescript
// GET /admin/audit/{event_id}
interface GetAuditEventResponse {
  success: true;
  data: {
    event: AuditEvent;
    related_events: AuditEvent[];
    actor_session_events?: AuditEvent[];
  };
}
```

### Export Audit Logs

```typescript
// POST /admin/audit/export
interface ExportAuditRequest {
  start_date: string;
  end_date: string;
  event_types?: string[];
  severity?: string[];
  actor_ids?: string[];
  format: 'csv' | 'json' | 'pdf' | 'siem';
  include_actor_details?: boolean;
  include_ip_addresses?: boolean;
  include_change_diffs?: boolean;
  include_raw_data?: boolean;
}

interface ExportAuditResponse {
  success: true;
  data: {
    export_id: string;
    estimated_events: number;
    estimated_size_mb: number;
    status: 'processing' | 'ready';
    download_url?: string;
  };
}
```

---

## 🎬 Motion Design

```typescript
const auditAnimations = {
  eventAppear: {
    opacity: [0, 1],
    x: [-20, 0],
    transition: { duration: 0.2 }
  },
  
  severityPulse: {
    boxShadow: ['0 0 0 0 var(--severity-color)', '0 0 0 4px transparent'],
    transition: { duration: 0.5 }
  },
  
  expandDetail: {
    height: 'auto',
    opacity: 1,
    transition: { duration: 0.3 }
  },
  
  liveIndicator: {
    opacity: [1, 0.5, 1],
    transition: { duration: 1.5, repeat: Infinity }
  }
};
```

---

## ⌨️ Keyboard Shortcuts

```typescript
const auditShortcuts = {
  'mod+e': 'Export logs',
  'mod+f': 'Focus search',
  'j/k': 'Navigate events',
  'enter': 'View event detail',
  'escape': 'Close detail',
  'r': 'Refresh events',
};
```

---

## ⚠️ Error Handling

```typescript
const auditErrorCodes = {
  AUDIT_LOAD_001: 'Failed to load audit events',
  AUDIT_EXPORT_001: 'Export failed',
  AUDIT_EXPORT_002: 'Date range too large for export',
  AUDIT_DETAIL_001: 'Event not found',
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Audit Logs*
