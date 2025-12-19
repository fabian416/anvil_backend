# FRONTEND_USER_SETTINGS_PROFILE

## User Profile Module

**User Type:** Authenticated User  
**Module:** Profile  
**Route:** `/settings/profile`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Profile** - User Account Details

### Description
User profile management including personal information, account status, and subscription details.

---

## 🖼️ Views & Wireframes

### View 1: Profile Screen

```
┌─────────────────────────────────────┐
│  [←]       Profile                 │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         ┌───────┐               ││
│  │         │  👤   │               ││
│  │         │       │  [Edit]       ││
│  │         └───────┘               ││
│  │                                 ││
│  │      Alice Johnson              ││
│  │    alice@example.com            ││
│  │                                 ││
│  │  ┌───────────┐ ┌───────────┐   ││
│  │  │ ✅ KYC    │ │ 💎 Elite  │   ││
│  │  │ Verified  │ │   Plan    │   ││
│  │  └───────────┘ └───────────┘   ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Account Details                    │
│  ┌─────────────────────────────────┐│
│  │ Display Name                    ││
│  │ Alice Johnson            [Edit] ││
│  ├─────────────────────────────────┤│
│  │ Email                           ││
│  │ alice@example.com               ││
│  ├─────────────────────────────────┤│
│  │ Phone                           ││
│  │ +1 (555) 123-4567        [Edit] ││
│  ├─────────────────────────────────┤│
│  │ Member Since                    ││
│  │ November 15, 2025               ││
│  └─────────────────────────────────┘│
│                                     │
│  Subscription                       │
│  ┌─────────────────────────────────┐│
│  │ 💎 Elite Plan                   ││
│  │                                 ││
│  │ $79/month                       ││
│  │ Next billing: Dec 15, 2025      ││
│  │                                 ││
│  │ [Manage Subscription]           ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │   ⚠️ Delete Account         [>] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/users/me
interface GetProfileResponse {
  success: true;
  data: {
    id: string;
    email: string;
    name?: string;
    phone?: string;
    avatar_url?: string;
    kyc_status: 'not_started' | 'pending' | 'verified' | 'rejected';
    subscription: {
      plan: string;
      status: string;
      price: number;
      next_billing_date?: string;
    };
    created_at: string;
  };
}

// PUT /api/users/me
interface UpdateProfileRequest {
  name?: string;
  phone?: string;
  avatar_url?: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Profile*
