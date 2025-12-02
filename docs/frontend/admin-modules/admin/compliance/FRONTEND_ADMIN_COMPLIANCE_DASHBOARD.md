# FRONTEND_ADMIN_COMPLIANCE_DASHBOARD

## Admin Compliance Dashboard Module

**User Type:** Admin  
**Module:** Compliance Dashboard  
**Route:** `/admin/compliance`  
**Access Level:** Read (Compliance+) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Compliance Dashboard** - Risk & Regulatory Monitoring

### Description
Central compliance hub integrating Chainalysis and other compliance tools to monitor user risk, sanctions screening, and regulatory requirements. Essential for DeFi platform compliance.

### Key Capabilities
- Real-time risk monitoring
- Sanctions screening integration
- User risk scoring
- Alert management
- Compliance reporting
- Regulatory dashboard

---

## 👤 User Stories

### US-ADMIN-COMP-001: View Compliance Overview
**As a** compliance officer  
**I want to** see compliance status at a glance  
**So that** I can identify issues quickly

### US-ADMIN-COMP-002: Monitor High-Risk Users
**As a** compliance officer  
**I want to** see users flagged for risk  
**So that** I can investigate and take action

### US-ADMIN-COMP-003: Review Sanctions Alerts
**As a** compliance officer  
**I want to** review sanctions screening results  
**So that** I can ensure OFAC compliance

### US-ADMIN-COMP-004: Generate Compliance Reports
**As a** compliance officer  
**I want to** generate compliance reports  
**So that** I can meet regulatory requirements

---

## 🖼️ Views & Wireframes

### View 1: Compliance Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🛡️ Compliance Dashboard                                        [📊 Reports]       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Compliance Status ─────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 🟢 Overall      │  │ 🔴 12 Alerts    │  │ 🟡 45 Reviews   │  │ ✅ 98.2%    │ ││
│  │  │    HEALTHY      │  │    Need Action  │  │    Pending      │  │    KYC Rate │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  RISK DISTRIBUTION                            ALERTS BY TYPE                        │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  Risk Score Distribution           │      │  🔴 Sanctions Match        4       │ │
│  │                                    │      │  🟠 High Risk Score        5       │ │
│  │  🟢 Low (0-30)     ████████████ 82%│      │  🟡 Unusual Activity       3       │ │
│  │                    20,142 users    │      │  🟡 KYC Expired            8       │ │
│  │                                    │      │  🔵 Large Transaction      12      │ │
│  │  🟡 Medium (31-60) ████       12%  │      │                                    │ │
│  │                    2,948 users     │      │  Total: 32 active alerts           │ │
│  │                                    │      │                                    │ │
│  │  🟠 High (61-80)   ██          5%  │      │  [View All Alerts →]               │ │
│  │                    1,228 users     │      │                                    │ │
│  │                                    │      │                                    │ │
│  │  🔴 Critical (81+) █           1%  │      │                                    │ │
│  │                    249 users       │      │                                    │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
│  CRITICAL ALERTS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🔴 SANCTIONS MATCH - Immediate Action Required                                 ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  User: 0x8f2a...4c3d │ Match: OFAC SDN List                              │  ││
│  │  │  Detected: 15 min ago │ Confidence: 95%                                   │  ││
│  │  │  Status: ⏳ Pending Review                                                │  ││
│  │  │  [Review Now] [View Details]                                              │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🔴 SANCTIONS MATCH - Immediate Action Required                                 ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  User: bob@example.com │ Match: EU Sanctions List                        │  ││
│  │  │  Detected: 2 hours ago │ Confidence: 87%                                  │  ││
│  │  │  Status: 🔍 Under Investigation                                           │  ││
│  │  │  [Review Now] [View Details]                                              │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  CHAINALYSIS INTEGRATION                      RECENT SCREENINGS                     │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  Status: 🟢 Connected              │      │  Last 24 hours: 1,245 screenings  │ │
│  │  Last Sync: 2 minutes ago          │      │                                    │ │
│  │                                    │      │  • 🟢 1,238 Clear                  │ │
│  │  API Usage: 45,230 / 100,000       │      │  • 🟡 4 Review Required            │ │
│  │  [████████████░░░░░░] 45%          │      │  • 🔴 3 Blocked                    │ │
│  │                                    │      │                                    │ │
│  │  [⚙️ Configure] [🔄 Force Sync]   │      │  Avg Response: 124ms               │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Alert Review

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔴 Review Alert: Sanctions Match                                           [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ALERT DETAILS                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Alert Type: Sanctions Match (OFAC SDN)                                      │  │
│  │  Severity: 🔴 Critical                                                       │  │
│  │  Detected: December 1, 2025 at 14:15:32 UTC                                  │  │
│  │  Source: Chainalysis KYT                                                     │  │
│  │  Confidence Score: 95%                                                        │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  USER INFORMATION                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Wallet: 0x8f2a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d                   │  │
│  │  Email: john.doe@email.com (if KYC'd)                                        │  │
│  │  Account Created: November 15, 2025                                          │  │
│  │  Total Transactions: 23                                                       │  │
│  │  Total Volume: $45,230                                                        │  │
│  │                                                                               │  │
│  │  [View Full Profile →]                                                       │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  MATCH DETAILS                                                                      │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Matched Entity: "IRAN'S ISLAMIC REVOLUTIONARY GUARD CORPS"                  │  │
│  │  List: OFAC SDN (Specially Designated Nationals)                             │  │
│  │  Match Type: Wallet Address                                                   │  │
│  │                                                                               │  │
│  │  Interaction Details:                                                        │  │
│  │  • Received 2.5 ETH from sanctioned address on Nov 28                        │  │
│  │  • Sent 1.0 ETH to sanctioned address on Nov 30                              │  │
│  │                                                                               │  │
│  │  [View Chainalysis Report →]                                                 │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RESOLUTION                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Action *                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [●] Block User & Report to FinCEN                                       │  │  │
│  │  │ [ ] Suspend Pending Investigation                                       │  │  │
│  │  │ [ ] False Positive - Clear Alert                                        │  │  │
│  │  │ [ ] Escalate to Legal                                                   │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Notes *                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Confirmed sanctions match. User wallet has direct interaction with     │  │  │
│  │  │ OFAC-listed address. Blocking account and filing SAR.                   │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Cancel]                                                    [Submit Resolution]    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Compliance Dashboard

```typescript
// GET /admin/compliance/dashboard
interface GetComplianceDashboardResponse {
  success: true;
  data: {
    status: 'healthy' | 'warning' | 'critical';
    alerts: {
      total: number;
      critical: number;
      pending_review: number;
    };
    kyc_rate: number;
    risk_distribution: {
      low: number;
      medium: number;
      high: number;
      critical: number;
    };
    alerts_by_type: Record<string, number>;
    recent_screenings: {
      total: number;
      clear: number;
      review_required: number;
      blocked: number;
      avg_response_ms: number;
    };
    chainalysis_status: {
      connected: boolean;
      last_sync: string;
      api_usage: number;
      api_limit: number;
    };
    critical_alerts: ComplianceAlert[];
  };
}

interface ComplianceAlert {
  id: string;
  type: 'sanctions_match' | 'high_risk' | 'unusual_activity' | 'kyc_expired' | 'large_transaction';
  severity: 'low' | 'medium' | 'high' | 'critical';
  user_id?: string;
  wallet_address?: string;
  description: string;
  confidence_score?: number;
  source: string;
  status: 'pending' | 'investigating' | 'resolved' | 'escalated';
  created_at: string;
  resolved_at?: string;
  resolved_by?: string;
  resolution_action?: string;
  resolution_notes?: string;
}
```

### Resolve Alert

```typescript
// POST /admin/compliance/alerts/{id}/resolve
interface ResolveAlertRequest {
  action: 'block' | 'suspend' | 'clear' | 'escalate';
  notes: string;
  report_to_fincen?: boolean;
}
```

### Get Risk Report

```typescript
// GET /admin/compliance/reports/risk?period=30d
interface GetRiskReportResponse {
  success: true;
  data: {
    period: string;
    summary: {
      total_users_screened: number;
      high_risk_identified: number;
      sanctions_matches: number;
      sars_filed: number;
    };
    trends: {
      risk_scores: TimeSeriesPoint[];
      alerts: TimeSeriesPoint[];
    };
    top_risks: Array<{
      category: string;
      count: number;
      change_pct: number;
    }>;
  };
}
```

---

## 🎬 Motion Design

```typescript
const complianceAnimations = {
  alertPulse: {
    boxShadow: ['0 0 0 0 rgba(239, 68, 68, 0.4)', '0 0 0 10px rgba(239, 68, 68, 0)'],
    transition: { duration: 1.5, repeat: Infinity }
  },
  
  riskBar: {
    width: '100%',
    transition: { duration: 0.8, ease: 'easeOut' }
  },
  
  statusIndicator: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.5 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Compliance Dashboard*
