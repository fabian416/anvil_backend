# FRONTEND_ADMIN_NOTIFICATIONS_TEMPLATES

## Admin Email Templates Module

**User Type:** Admin  
**Module:** Email Templates  
**Route:** `/admin/notifications/templates`  
**Access Level:** Read (All) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Email Templates** - Transactional Email Management

### Description
Management of email templates for transactional emails, notifications, and marketing communications with preview and testing capabilities.

### Key Capabilities
- Template editing
- Variable management
- Preview & testing
- Version history
- Localization
- A/B testing setup

---

## 🖼️ Views & Wireframes

### View 1: Templates List

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📧 Email Templates                                               [+ New Template]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Category: [All ▼]  Status: [All ▼]  [🔍 Search templates...]                       │
│                                                                                      │
│  TRANSACTIONAL                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  📧 Welcome Email                                               ✅ Active       ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Trigger: User signup │ Sent (30d): 456 │ Open Rate: 68.2%               │  ││
│  │  │  Last Updated: Nov 28 by admin@anvil.app                                 │  ││
│  │  │  [Edit] [Preview] [Send Test] [View Stats]                               │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  📧 Password Reset                                              ✅ Active       ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Trigger: Password reset request │ Sent (30d): 89 │ Open Rate: 92.1%     │  ││
│  │  │  Last Updated: Nov 15 by admin@anvil.app                                 │  ││
│  │  │  [Edit] [Preview] [Send Test] [View Stats]                               │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  📧 Transaction Confirmation                                    ✅ Active       ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Trigger: Successful transaction │ Sent (30d): 12,456 │ Open Rate: 45.3% │  ││
│  │  │  Last Updated: Nov 20 by admin@anvil.app                                 │  ││
│  │  │  [Edit] [Preview] [Send Test] [View Stats]                               │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  BILLING                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  📧 Invoice Receipt                                             ✅ Active       ││
│  │  📧 Payment Failed                                              ✅ Active       ││
│  │  📧 Subscription Renewal                                        ✅ Active       ││
│  │  📧 Trial Ending                                                ✅ Active       ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  SECURITY                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  📧 New Login Alert                                             ✅ Active       ││
│  │  📧 Account Suspended                                           ✅ Active       ││
│  │  📧 KYC Approved                                                ✅ Active       ││
│  │  📧 KYC Rejected                                                ✅ Active       ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Template Editor

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📧 Edit: Welcome Email                                                     [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Edit]  [Preview]  [Variables]  [History]                                          │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  TEMPLATE SETTINGS                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Subject Line                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Welcome to Anvil, {{user.name}}! 🎉                                     │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  From Name                           From Email                              │  │
│  │  ┌───────────────────────────┐      ┌───────────────────────────────────────┐│  │
│  │  │ Anvil Team                │      │ hello@anvil.app                       ││  │
│  │  └───────────────────────────┘      └───────────────────────────────────────┘│  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  EMAIL BODY                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                                                                         │  │  │
│  │  │  Hi {{user.name}},                                                      │  │  │
│  │  │                                                                         │  │  │
│  │  │  Welcome to Anvil! We're thrilled to have you join our community of    │  │  │
│  │  │  DeFi enthusiasts.                                                      │  │  │
│  │  │                                                                         │  │  │
│  │  │  Here's what you can do next:                                           │  │  │
│  │  │                                                                         │  │  │
│  │  │  • Connect your wallet                                                  │  │  │
│  │  │  • Complete your KYC verification                                       │  │  │
│  │  │  • Make your first swap                                                 │  │  │
│  │  │                                                                         │  │  │
│  │  │  {{#if user.referrer}}                                                  │  │  │
│  │  │  You were referred by {{user.referrer.name}}!                           │  │  │
│  │  │  {{/if}}                                                                │  │  │
│  │  │                                                                         │  │  │
│  │  │  Best,                                                                  │  │  │
│  │  │  The Anvil Team                                                         │  │  │
│  │  │                                                                         │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  [B] [I] [Link] [Image] [Button] [Divider] [Code Block]                      │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Cancel]          [📧 Send Test]           [💾 Save Draft]        [✅ Publish]    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/notifications/templates
interface GetTemplatesResponse {
  success: true;
  data: {
    templates: EmailTemplate[];
    categories: string[];
  };
}

interface EmailTemplate {
  id: string;
  name: string;
  slug: string;
  category: 'transactional' | 'billing' | 'security' | 'marketing';
  trigger: string;
  status: 'active' | 'draft' | 'disabled';
  subject: string;
  from_name: string;
  from_email: string;
  body_html: string;
  body_text?: string;
  variables: Array<{
    name: string;
    description: string;
    example: string;
  }>;
  stats_30d?: {
    sent: number;
    open_rate: number;
    click_rate: number;
  };
  updated_at: string;
  updated_by: string;
}

// PUT /admin/notifications/templates/{id}
interface UpdateTemplateRequest {
  subject?: string;
  from_name?: string;
  from_email?: string;
  body_html?: string;
  body_text?: string;
  status?: 'active' | 'draft' | 'disabled';
}

// POST /admin/notifications/templates/{id}/test
interface SendTestEmailRequest {
  email: string;
  variables?: Record<string, any>;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Email Templates*
