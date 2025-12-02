# FRONTEND_ADMIN_USERS_KYC

## Admin KYC Management Module

**User Type:** Admin  
**Module:** KYC Management  
**Route:** `/admin/users/kyc`  
**Access Level:** Read (All) | Manage (Compliance+)

---

## 📋 Module Overview

### Title
**KYC Management** - Identity Verification Administration

### Description
Management interface for Know Your Customer (KYC) verification processes, including review queues, verification status tracking, and document management.

### Key Capabilities
- KYC verification queue
- Document review
- Manual verification
- Status tracking
- Expiration management
- Compliance reporting

---

## 👤 User Stories

### US-ADMIN-KYC-001: View KYC Queue
**As a** compliance officer  
**I want to** see pending KYC verifications  
**So that** I can process them efficiently

### US-ADMIN-KYC-002: Review Documents
**As a** compliance officer  
**I want to** review submitted documents  
**So that** I can verify user identity

### US-ADMIN-KYC-003: Manual Verification
**As a** compliance officer  
**I want to** manually approve/reject KYC  
**So that** I can handle edge cases

### US-ADMIN-KYC-004: Track Expirations
**As a** compliance officer  
**I want to** see expiring verifications  
**So that** users can re-verify in time

---

## 🖼️ Views & Wireframes

### View 1: KYC Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🪪 KYC Management                                               [📊 Report]        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  🔵 10,245 Verified    ⏳ 342 Pending    ❌ 89 Failed    ⚠️ 156 Expiring Soon  ││
│  │     42% of users          Avg: 4.2 hrs      This month      Next 30 days        ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  [All]  [Pending Review]  [Auto-Approved]  [Failed]  [Expiring]                     │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  PENDING REVIEW (23 require manual review)                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │ USER             │ LEVEL  │ DOCUMENTS      │ AUTO-CHECK │ SUBMITTED│ ACTION│││
│  │  ├──────────────────┼────────┼────────────────┼────────────┼──────────┼───────┤││
│  │  │ alice@defi.co    │ Tier 2 │ Passport, PoA  │ ⚠️ Review  │ 2h ago   │[Review]│││
│  │  │ john@crypto.com  │ Tier 1 │ Driver License │ ⚠️ Blurry  │ 4h ago   │[Review]│││
│  │  │ bob@web3.io      │ Tier 2 │ ID Card, Bill  │ ⚠️ Mismatch│ 6h ago   │[Review]│││
│  │  │ carol@eth.org    │ Tier 1 │ Passport       │ ⚠️ Expired │ 8h ago   │[Review]│││
│  │  └──────────────────┴────────┴────────────────┴────────────┴──────────┴───────┘││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  VERIFICATION FUNNEL (30d)                    BY TIER                               │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  Started      ████████████████ 2,456│      │  Tier 1 (Basic)    ████████  65%  │ │
│  │  Submitted    ████████████     1,892│      │  6,659 users │ ID only           │ │
│  │  Auto-Passed  ██████████       1,456│      │                                    │ │
│  │  Manual Review████              342 │      │  Tier 2 (Enhanced) ████      28%  │ │
│  │  Approved     █████████        1,678│      │  2,869 users │ ID + PoA           │ │
│  │  Failed       █                  89 │      │                                    │ │
│  │                                    │      │  Tier 3 (Full)     ██          7%  │ │
│  │  Pass Rate: 94.9%                  │      │  717 users │ Full verification     │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: KYC Review

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🪪 KYC Review: alice@defi.co                                               [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  USER INFO                                    VERIFICATION REQUEST                  │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  Email: alice@defi.co              │      │  Level: Tier 2 (Enhanced)          │ │
│  │  Account: Created Nov 15, 2025     │      │  Submitted: 2 hours ago            │ │
│  │  Wallet: 0x7a23...8f4d             │      │  Auto-Check: ⚠️ Needs Review       │ │
│  │  Volume: $45,230                   │      │                                    │ │
│  │                                    │      │  Reason: Name mismatch detected    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
│  SUBMITTED DOCUMENTS                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  DOCUMENT 1: Passport                      DOCUMENT 2: Proof of Address        ││
│  │  ┌─────────────────────────────────┐      ┌─────────────────────────────────┐  ││
│  │  │                                 │      │                                 │  ││
│  │  │  ┌───────────────────────────┐  │      │  ┌───────────────────────────┐  │  ││
│  │  │  │                           │  │      │  │                           │  │  ││
│  │  │  │     🪪 PASSPORT           │  │      │  │     📄 UTILITY BILL       │  │  ││
│  │  │  │                           │  │      │  │                           │  │  ││
│  │  │  │  Name: Alice M. Johnson   │  │      │  │  Name: Alice Johnson      │  │  ││
│  │  │  │  DOB: 1990-05-15          │  │      │  │  Address: 123 Main St     │  │  ││
│  │  │  │  Expires: 2028-03-20      │  │      │  │  Date: Nov 2025           │  │  ││
│  │  │  │                           │  │      │  │                           │  │  ││
│  │  │  └───────────────────────────┘  │      │  └───────────────────────────┘  │  ││
│  │  │                                 │      │                                 │  ││
│  │  │  [🔍 Zoom] [↻ Rotate]           │      │  [🔍 Zoom] [↻ Rotate]           │  ││
│  │  │                                 │      │                                 │  ││
│  │  └─────────────────────────────────┘      └─────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  ⚠️ Auto-Check Flag: Middle initial "M." on passport not present on utility bill ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  DECISION                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Notes                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Name variation is minor (middle initial). Documents otherwise match.   │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Request Re-upload]          [❌ Reject]          [✅ Approve Verification]        │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get KYC Dashboard

```typescript
// GET /admin/users/kyc
interface GetKYCDashboardResponse {
  success: true;
  data: {
    summary: {
      verified: number;
      pending: number;
      failed: number;
      expiring_soon: number;
      verification_rate: number;
    };
    pending_review: KYCSubmission[];
    funnel: {
      started: number;
      submitted: number;
      auto_passed: number;
      manual_review: number;
      approved: number;
      failed: number;
    };
    by_tier: Record<string, { count: number; percentage: number }>;
  };
}

interface KYCSubmission {
  id: string;
  user_id: string;
  email: string;
  tier: 'tier_1' | 'tier_2' | 'tier_3';
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  auto_check_result: 'passed' | 'review' | 'failed';
  auto_check_reason?: string;
  documents: KYCDocument[];
  submitted_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
}

interface KYCDocument {
  id: string;
  type: 'passport' | 'drivers_license' | 'id_card' | 'proof_of_address' | 'selfie';
  url: string;
  extracted_data?: Record<string, string>;
  verification_status: 'pending' | 'verified' | 'rejected';
}
```

### Review KYC

```typescript
// POST /admin/users/kyc/{id}/review
interface ReviewKYCRequest {
  decision: 'approve' | 'reject' | 'request_reupload';
  notes: string;
  rejection_reason?: string;
  documents_to_reupload?: string[];
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: KYC Management*
