# FRONTEND_USER_SETTINGS_MAIN

## User Settings Module

**User Type:** Authenticated User  
**Module:** Settings  
**Route:** `/settings`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Settings** - App Configuration

### Description
Central settings hub for app preferences, security settings, notifications, and account management.

### Key Capabilities
- Profile management
- Security settings (2FA, biometrics)
- Notification preferences
- Display preferences
- Network settings
- Account management (export, delete)

---

## 🖼️ Views & Wireframes

### View 1: Settings Main

```
┌─────────────────────────────────────┐
│  [←]       Settings                │
│                                     │
│  Account                            │
│  ┌─────────────────────────────────┐│
│  │ 👤 Profile                  [>] ││
│  │    alice@example.com            ││
│  ├─────────────────────────────────┤│
│  │ 🪪 KYC Verification         [>] ││
│  │    ✅ Verified                  ││
│  ├─────────────────────────────────┤│
│  │ 💳 Subscription             [>] ││
│  │    Elite Plan                   ││
│  └─────────────────────────────────┘│
│                                     │
│  Security                           │
│  ┌─────────────────────────────────┐│
│  │ 🔐 Security Settings        [>] ││
│  │    2FA enabled                  ││
│  ├─────────────────────────────────┤│
│  │ 👛 Connected Wallets        [>] ││
│  │    2 wallets                    ││
│  └─────────────────────────────────┘│
│                                     │
│  Preferences                        │
│  ┌─────────────────────────────────┐│
│  │ 🔔 Notifications            [>] ││
│  ├─────────────────────────────────┤│
│  │ 🌙 Appearance               [>] ││
│  │    Dark mode                    ││
│  ├─────────────────────────────────┤│
│  │ 🌐 Network                  [>] ││
│  │    Default: Ethereum            ││
│  ├─────────────────────────────────┤│
│  │ 💱 Currency                 [>] ││
│  │    USD                          ││
│  └─────────────────────────────────┘│
│                                     │
│  Support                            │
│  ┌─────────────────────────────────┐│
│  │ ❓ Help Center              [>] ││
│  ├─────────────────────────────────┤│
│  │ 💬 Contact Support          [>] ││
│  ├─────────────────────────────────┤│
│  │ 📜 Terms & Privacy          [>] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │        Sign Out                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Version 1.0.0 (Build 123)         │
│                                     │
└─────────────────────────────────────┘
```

### View 2: Security Settings

```
┌─────────────────────────────────────┐
│  [←]       Security                │
│                                     │
│  Authentication                     │
│  ┌─────────────────────────────────┐│
│  │ 🔐 Two-Factor Authentication    ││
│  │    Add extra security          ││
│  │                         [On ●] ││
│  ├─────────────────────────────────┤│
│  │ 🔏 Biometric Login              ││
│  │    Use Face ID / Fingerprint   ││
│  │                         [On ●] ││
│  ├─────────────────────────────────┤│
│  │ ⏱️ Auto-Lock                    ││
│  │    Lock app after inactivity   ││
│  │                       5 minutes││
│  └─────────────────────────────────┘│
│                                     │
│  Transaction Security               │
│  ┌─────────────────────────────────┐│
│  │ 🔒 Require Confirmation         ││
│  │    For transactions over        ││
│  │                          $100  ││
│  ├─────────────────────────────────┤│
│  │ 📧 Transaction Alerts           ││
│  │    Email for all transactions  ││
│  │                         [On ●] ││
│  └─────────────────────────────────┘│
│                                     │
│  Session                            │
│  ┌─────────────────────────────────┐│
│  │ 📱 Active Sessions          [>] ││
│  │    2 devices                    ││
│  ├─────────────────────────────────┤│
│  │ 🔄 Sign Out All Devices     [>] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 3: Notification Settings

```
┌─────────────────────────────────────┐
│  [←]    Notifications              │
│                                     │
│  Push Notifications                 │
│  ┌─────────────────────────────────┐│
│  │ All Push Notifications  [On ●] ││
│  └─────────────────────────────────┘│
│                                     │
│  Transaction Alerts                 │
│  ┌─────────────────────────────────┐│
│  │ Transaction Completed   [On ●] ││
│  ├─────────────────────────────────┤│
│  │ Transaction Failed      [On ●] ││
│  ├─────────────────────────────────┤│
│  │ Large Transactions      [On ●] ││
│  │ Threshold: $1,000               ││
│  └─────────────────────────────────┘│
│                                     │
│  DeFi Alerts                        │
│  ┌─────────────────────────────────┐│
│  │ Position Alerts         [On ●] ││
│  │ Health factor warnings          ││
│  ├─────────────────────────────────┤│
│  │ Price Alerts            [On ●] ││
│  │ Custom price targets            ││
│  ├─────────────────────────────────┤│
│  │ Yield Changes          [Off ○] ││
│  └─────────────────────────────────┘│
│                                     │
│  Marketing                          │
│  ┌─────────────────────────────────┐│
│  │ Product Updates        [Off ○] ││
│  ├─────────────────────────────────┤│
│  │ Tips & Tutorials       [Off ○] ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/users/me/settings
interface GetUserSettingsResponse {
  success: true;
  data: {
    profile: {
      email: string;
      name?: string;
      kyc_status: string;
      subscription_plan: string;
    };
    security: {
      two_factor_enabled: boolean;
      biometric_enabled: boolean;
      auto_lock_minutes: number;
      transaction_confirm_threshold: number;
    };
    notifications: {
      push_enabled: boolean;
      transaction_completed: boolean;
      transaction_failed: boolean;
      large_transactions: boolean;
      position_alerts: boolean;
      price_alerts: boolean;
      marketing: boolean;
    };
    preferences: {
      theme: 'light' | 'dark' | 'system';
      default_chain: string;
      currency: string;
    };
  };
}

// PUT /api/users/me/settings
interface UpdateSettingsRequest {
  security?: Partial<SecuritySettings>;
  notifications?: Partial<NotificationSettings>;
  preferences?: Partial<PreferenceSettings>;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Settings*
