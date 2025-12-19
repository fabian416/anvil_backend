# FRONTEND_ADMIN_ANNOUNCEMENTS

## Admin Announcements Module

**User Type:** Admin  
**Module:** Announcements  
**Route:** `/admin/announcements`  
**Access Level:** Read (All) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Announcements** - Platform-wide Announcements

### Description
Create and manage platform-wide announcements, banners, and system messages displayed to users across the application.

### Key Capabilities
- Banner announcements
- In-app messages
- Scheduled announcements
- Targeting by user segment
- Analytics tracking
- Multi-language support

---

## 🖼️ Views & Wireframes

### View 1: Announcements Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📢 Announcements                                             [+ New Announcement]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  [Active]  [Scheduled]  [Expired]  [Drafts]                                         │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  ACTIVE ANNOUNCEMENTS                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🔵 BANNER - Top of App                                        Ends: Dec 15    ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  🎉 Cross-Chain Swaps Now Live!                                          │  ││
│  │  │  Swap tokens across Ethereum, Arbitrum, Polygon, and Base in one tx.     │  ││
│  │  │                                                                           │  ││
│  │  │  Audience: All users │ Views: 45,230 │ Clicks: 3,456 (7.6%)              │  ││
│  │  │  Started: Nov 25 │ [Edit] [End Now] [View Stats]                         │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟡 WARNING - System Status                                    Ends: Manual    ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │                                                                           │  ││
│  │  │  ⚠️ Polygon network experiencing high congestion.                        │  ││
│  │  │  Transactions may be delayed.                                            │  ││
│  │  │                                                                           │  ││
│  │  │  Audience: Users with Polygon activity │ Views: 2,456 │ Dismissals: 1,234│  ││
│  │  │  Started: 2 hours ago │ [Edit] [End Now] [View Stats]                    │  ││
│  │  │                                                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  SCHEDULED                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  📅 Dec 5, 10:00 AM - Year-End Promo                                            ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  🎁 Holiday Special: 50% off Elite plan for 3 months!                    │  ││
│  │  │  Audience: Free tier users │ Duration: Dec 5 - Dec 25                    │  ││
│  │  │  [Edit] [Cancel] [Preview]                                               │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  📅 Dec 10, 9:00 AM - Maintenance Notice                                        ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  🔧 Scheduled maintenance on Dec 12, 2-4 AM UTC                          │  ││
│  │  │  Audience: All users │ Duration: Dec 10 - Dec 12                         │  ││
│  │  │  [Edit] [Cancel] [Preview]                                               │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Create Announcement

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📢 Create Announcement                                                     [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  TYPE & STYLE                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Announcement Type                                                           │  │
│  │  [●] Banner (top of app)    [ ] Modal    [ ] Toast    [ ] In-feed           │  │
│  │                                                                               │  │
│  │  Style                                                                       │  │
│  │  [🔵 Info]  [🟢 Success]  [🟡 Warning]  [🔴 Error]  [🟣 Promo]               │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CONTENT                                                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Title                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ 🎉 Cross-Chain Swaps Now Live!                                          │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Message                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Swap tokens across Ethereum, Arbitrum, Polygon, and Base in a single   │  │  │
│  │  │ transaction. Try it now!                                                │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Button (optional)                                                           │  │
│  │  ┌────────────────────────┐  ┌──────────────────────────────────────────────┐│  │
│  │  │ Try Cross-Chain        │  │ https://app.anvil.app/swap?cross=true      ││  │
│  │  └────────────────────────┘  └──────────────────────────────────────────────┘│  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  TARGETING                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Audience                                                                    │  │
│  │  [●] All users    [ ] Segment    [ ] Specific users                         │  │
│  │                                                                               │  │
│  │  [✓] Allow users to dismiss                                                  │  │
│  │  [ ] Show only once per user                                                 │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  SCHEDULE                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Start: [●] Now  [ ] Scheduled: [Dec 5, 2025 📅] [10:00 AM ⏰]               │  │
│  │  End:   [ ] Manual  [●] Scheduled: [Dec 15, 2025 📅] [11:59 PM ⏰]           │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Save as Draft]              [Preview]                          [📢 Publish Now]  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/announcements
interface GetAnnouncementsResponse {
  success: true;
  data: {
    active: Announcement[];
    scheduled: Announcement[];
    expired: Announcement[];
    drafts: Announcement[];
  };
}

interface Announcement {
  id: string;
  type: 'banner' | 'modal' | 'toast' | 'in_feed';
  style: 'info' | 'success' | 'warning' | 'error' | 'promo';
  title: string;
  message: string;
  button_text?: string;
  button_url?: string;
  audience: {
    type: 'all' | 'segment' | 'specific';
    segment_id?: string;
    user_ids?: string[];
  };
  dismissible: boolean;
  show_once: boolean;
  status: 'draft' | 'active' | 'scheduled' | 'expired';
  start_at: string;
  end_at?: string;
  stats?: {
    views: number;
    clicks: number;
    dismissals: number;
  };
  created_at: string;
  created_by: string;
}

// POST /admin/announcements
interface CreateAnnouncementRequest {
  type: 'banner' | 'modal' | 'toast' | 'in_feed';
  style: 'info' | 'success' | 'warning' | 'error' | 'promo';
  title: string;
  message: string;
  button_text?: string;
  button_url?: string;
  audience: {
    type: 'all' | 'segment' | 'specific';
    segment_id?: string;
    user_ids?: string[];
  };
  dismissible?: boolean;
  show_once?: boolean;
  start_at?: string;
  end_at?: string;
  publish_now?: boolean;
}

// POST /admin/announcements/{id}/end
interface EndAnnouncementRequest {
  notes?: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Announcements*
