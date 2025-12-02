# FRONTEND_ADMIN_COMPLIANCE_FRAUD

## Admin Fraud Detection Module

**User Type:** Admin  
**Module:** Fraud Detection  
**Route:** `/admin/security/fraud`  
**Access Level:** Read (Compliance+) | Manage (Admin+)

---

## 📋 Module Overview

### Title
**Fraud Detection** - Transaction & Behavior Analysis

### Description
Advanced fraud detection dashboard utilizing pattern analysis, behavioral signals, and machine learning to identify suspicious activities and prevent financial losses.

### Key Capabilities
- Real-time fraud scoring
- Pattern detection
- Velocity checks
- Behavioral analysis
- Case management
- Rule configuration

---

## 🖼️ Views & Wireframes

### View 1: Fraud Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔍 Fraud Detection                                          [⚙️ Rules] [📊 Report] │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Fraud Metrics (24h) ───────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ ││
│  │  │ 🚨 23 Flagged   │  │ 🔴 8 Blocked    │  │ 💰 $45,230      │  │ 📊 0.12%    │ ││
│  │  │    Transactions │  │    Transactions │  │    Prevented    │  │    Fraud Rate││
│  │  │    ↓ 15% vs avg │  │                 │  │                 │  │             │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ACTIVE FRAUD CASES                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                  ││
│  │  🔴 HIGH RISK - Case #F-2847                                     [Investigate] ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  User: 0x8f2a...4c3d │ Fraud Score: 92/100                               │  ││
│  │  │  Pattern: Rapid account draining after dormancy                          │  ││
│  │  │  Amount at Risk: $12,450 │ Transactions: 15 in 2 minutes                 │  ││
│  │  │  Status: ⏳ Pending Review │ Auto-blocked: Yes                           │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  │  🟠 MEDIUM RISK - Case #F-2846                                   [Investigate] ││
│  │  ┌───────────────────────────────────────────────────────────────────────────┐  ││
│  │  │  User: bob@example.com │ Fraud Score: 68/100                             │  ││
│  │  │  Pattern: New account with high-value transactions                       │  ││
│  │  │  Amount at Risk: $5,200 │ Account Age: 2 days                            │  ││
│  │  │  Status: ⏳ Pending Review │ Auto-blocked: No                            │  ││
│  │  └───────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  FRAUD PATTERNS (30d)                         DETECTION BY RULE                     │
│  ┌────────────────────────────────────┐      ┌────────────────────────────────────┐ │
│  │                                    │      │                                    │ │
│  │  Account Takeover    ████████ 35%  │      │  Velocity Check    ████████   42% │ │
│  │  New Account Fraud   ██████   28%  │      │  Amount Threshold  █████      28% │ │
│  │  Rapid Draining      █████    22%  │      │  Behavioral ML     ████       18% │ │
│  │  Money Laundering    ███      12%  │      │  Device Fingerprint██          8% │ │
│  │  Other               █         3%  │      │  Manual Flag       █           4% │ │
│  │                                    │      │                                    │ │
│  └────────────────────────────────────┘      └────────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Case Investigation

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🔍 Fraud Case #F-2847                                                      [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  RISK ASSESSMENT                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Fraud Score: [████████████████████░░░░] 92/100 - HIGH RISK                  │  │
│  │                                                                               │  │
│  │  Risk Factors:                                                               │  │
│  │  • 🔴 15 transactions in 2 minutes (velocity: 7.5x normal)                   │  │
│  │  • 🔴 Account dormant for 45 days before activity                            │  │
│  │  • 🔴 New device fingerprint detected                                        │  │
│  │  • 🟠 Transactions to previously unseen addresses                            │  │
│  │  • 🟡 VPN detected (Netherlands)                                             │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  TRANSACTION TIMELINE                                                               │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  14:32:00  🔴 Swap 5.0 ETH → USDC ($11,250)    → 0x9a3b...                   │  │
│  │  14:32:15  🔴 Transfer 8,000 USDC             → 0x7c2d... (new addr)         │  │
│  │  14:32:28  🔴 Swap 2.0 ETH → USDC ($4,500)    → 0x9a3b...                   │  │
│  │  14:32:45  🔴 Transfer 4,000 USDC             → 0x5e1f... (new addr)         │  │
│  │  14:33:02  ⛔ BLOCKED - Velocity limit exceeded                              │  │
│  │  ...                                                                         │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  DECISION                                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  [Confirm Fraud & Ban]  [Suspicious - Suspend]  [False Positive - Clear]     │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /admin/security/fraud
interface GetFraudDashboardResponse {
  success: true;
  data: {
    metrics_24h: {
      flagged: number;
      blocked: number;
      prevented_usd: number;
      fraud_rate: number;
    };
    active_cases: FraudCase[];
    patterns_30d: Record<string, number>;
    detection_by_rule: Record<string, number>;
  };
}

interface FraudCase {
  id: string;
  user_id: string;
  wallet_address?: string;
  email?: string;
  fraud_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  pattern: string;
  amount_at_risk_usd: number;
  transaction_count: number;
  status: 'pending' | 'investigating' | 'confirmed_fraud' | 'false_positive';
  auto_blocked: boolean;
  risk_factors: Array<{ severity: string; description: string }>;
  transactions: FraudTransaction[];
  created_at: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Fraud Detection*
