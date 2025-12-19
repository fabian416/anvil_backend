# FRONTEND_ADMIN_COMPLIANCE_SANCTIONS

## Admin Sanctions Screening Module

**User Type:** Admin  
**Module:** Sanctions Screening  
**Route:** `/admin/compliance/sanctions`  
**Access Level:** Read (Compliance+) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Sanctions Screening** - OFAC & Watchlist Monitoring

### Description
Real-time sanctions screening integration with Chainalysis and other providers to ensure compliance with OFAC, EU, and other international sanctions lists.

### Key Capabilities
- Real-time wallet screening
- OFAC SDN list monitoring
- EU/UK sanctions lists
- PEP screening
- Match resolution workflow
- Continuous monitoring

---

## 🖼️ Views & Wireframes

### View 1: Sanctions Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🛡️ Sanctions Screening                                     [⚙️ Config] [📊 Report] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Screening Status ──────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 🟢 124,567      │  │ 🔴 4 Matches    │  │ 🟡 12 Pending   │  │ ✅ 99.99%   │ ││
│  │  │    Screened     │  │    Confirmed    │  │    Review       │  │    Clear    │ ││
│  │  │    This Month   │  │                 │  │                 │  │    Rate     │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ACTIVE MATCHES REQUIRING REVIEW                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🔴 OFAC SDN MATCH - 95% Confidence                               [Review Now] ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  Wallet: 0x8f2a...4c3d                                                   │  ││
│  │  │  Matched List: OFAC SDN │ Entity: IRAN'S IRGC                            │  ││
│  │  │  Match Type: Direct wallet interaction │ Detected: 15 min ago            │  ││
│  │  │  User Status: ⛔ Auto-blocked                                             │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟠 EU SANCTIONS MATCH - 78% Confidence                           [Review Now] ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  User: bob@example.com                                                   │  ││
│  │  │  Matched List: EU Consolidated List │ Possible name match               │  ││
│  │  │  Match Type: Name similarity │ Detected: 2 hours ago                     │  ││
│  │  │  User Status: ⏳ Pending review                                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  LISTS MONITORED                              SCREENING COVERAGE                    │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  ✅ OFAC SDN List      Updated: 1d │      │  Wallets Screened                  │ │
│  │  ✅ OFAC Consolidated  Updated: 1d │      │  [████████████████████] 100%       │ │
│  │  ✅ EU Consolidated    Updated: 2d │      │  24,567 / 24,567                   │ │
│  │  ✅ UK Sanctions       Updated: 2d │      │                                    │ │
│  │  ✅ UN Sanctions       Updated: 3d │      │  Users Screened (KYC)              │ │
│  │  ✅ PEP Database       Updated: 1d │      │  [████████████████████] 100%       │ │
│  │                                    │      │  10,245 / 10,245                   │ │
│  │  Last Full Scan: 4 hours ago       │      │                                    │ │
│  │  [Run Full Scan Now]               │      │  Last Batch: 4 hours ago           │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/compliance/sanctions
interface GetSanctionsDashboardResponse {
  success: true;
  data: {
    summary: {
      screened_this_month: number;
      confirmed_matches: number;
      pending_review: number;
      clear_rate: number;
    };
    active_matches: SanctionsMatch[];
    lists_status: Array<{
      name: string;
      updated_at: string;
      enabled: boolean;
    }>;
    coverage: {
      wallets: { screened: number; total: number };
      users: { screened: number; total: number };
      last_batch: string;
    };
  };
}

interface SanctionsMatch {
  id: string;
  type: 'wallet' | 'user';
  wallet_address?: string;
  user_id?: string;
  email?: string;
  matched_list: string;
  matched_entity: string;
  match_type: string;
  confidence: number;
  status: 'pending' | 'confirmed' | 'false_positive';
  user_action: 'blocked' | 'pending' | 'none';
  detected_at: string;
}

// POST /admin/compliance/sanctions/{id}/resolve
interface ResolveSanctionsMatchRequest {
  resolution: 'confirmed_match' | 'false_positive';
  notes: string;
  report_to_fincen?: boolean;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Sanctions Screening*
