# FRONTEND_USER_SETTINGS_REFERRALS

## User Referrals Module

**User Type:** Authenticated User  
**Module:** Referrals  
**Route:** `/referrals`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Referrals** - Invite & Earn Program

### Description
Referral program allowing users to invite friends and earn rewards for successful sign-ups.

---

## 🖼️ Views & Wireframes

### View 1: Referrals Dashboard

```
┌─────────────────────────────────────┐
│  [←]      Invite Friends           │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         ┌───────┐               ││
│  │         │  🎁   │               ││
│  │         └───────┘               ││
│  │                                 ││
│  │    Give $20, Get $20            ││
│  │                                 ││
│  │  Invite friends to Anvil.       ││
│  │  When they complete their first ││
│  │  $100+ trade, you both get $20  ││
│  │  in rewards.                    ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Your Referral Code                 │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │     ALICE2024                   ││
│  │                                 ││
│  │  [📋 Copy]     [📤 Share]      ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Your Stats                         │
│  ┌─────────────────────────────────┐│
│  │  Friends Invited         12     ││
│  │  Completed Referrals      8     ││
│  │  Total Earned          $160     ││
│  └─────────────────────────────────┘│
│                                     │
│  Referred Friends                   │
│  ┌─────────────────────────────────┐│
│  │ 👤 bob@***         ✅ Complete  ││
│  │    Joined Nov 28   +$20 earned  ││
│  ├─────────────────────────────────┤│
│  │ 👤 carol@***       ✅ Complete  ││
│  │    Joined Nov 25   +$20 earned  ││
│  ├─────────────────────────────────┤│
│  │ 👤 dave@***        ⏳ Pending   ││
│  │    Joined Nov 30   Awaiting trade│
│  └─────────────────────────────────┘│
│                                     │
│  Terms & Conditions apply           │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/referrals
interface GetReferralsResponse {
  success: true;
  data: {
    referral_code: string;
    referral_link: string;
    reward_amount: number;
    stats: {
      invited_count: number;
      completed_count: number;
      total_earned_usd: number;
    };
    referrals: Array<{
      id: string;
      email_masked: string;
      status: 'pending' | 'complete';
      joined_at: string;
      completed_at?: string;
      reward_earned?: number;
    }>;
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Referrals*
