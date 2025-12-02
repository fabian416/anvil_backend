# Anvil User App Frontend Module Documentation

## 📋 Complete Module Index

**Total Modules:** 24  
**Last Updated:** December 2, 2025  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0 (Complete)

---

## 🎯 Quick Stats

| Metric | Value |
|--------|-------|
| **Total Modules** | 24 |
| **Total Domains** | 9 |
| **Total Files** | 25 |
| **Wireframes** | ~60 |
| **API Endpoints** | ~50 |

---

## 📱 App Information

**Anvil** - Your AI-Powered DeFi Assistant

A mobile-first application that makes DeFi accessible through natural language AI conversations. Users can swap, stake, lend, borrow, and bridge tokens simply by chatting with their AI copilot.

### Supported Chains
- Ethereum Mainnet
- Arbitrum One
- Polygon
- Base

### Key Features
- 🤖 AI-powered DeFi operations via chat
- 🔐 Seedless wallet (Privy MPC)
- 🔄 DEX aggregation (1inch)
- 🏦 Lending/Borrowing (Aave)
- 🥩 Liquid Staking (Lido)
- 🌉 Cross-chain bridging

---

## 📁 Complete Module Directory

### 🚀 Onboarding & Authentication (4 Modules)

| # | Module | Route | File |
|---|--------|-------|------|
| 1 | Welcome & Onboarding | `/welcome` | [FRONTEND_USER_ONBOARDING_WELCOME.md](user/onboarding/FRONTEND_USER_ONBOARDING_WELCOME.md) |
| 2 | Login | `/login` | [FRONTEND_USER_AUTH_LOGIN.md](user/onboarding/FRONTEND_USER_AUTH_LOGIN.md) |
| 3 | KYC Verification | `/kyc` | [FRONTEND_USER_ONBOARDING_KYC.md](user/onboarding/FRONTEND_USER_ONBOARDING_KYC.md) |

### 🏠 Home & Discovery (2 Modules)

| # | Module | Route | File |
|---|--------|-------|------|
| 4 | Home Dashboard | `/home` | [FRONTEND_USER_HOME_DASHBOARD.md](user/home/FRONTEND_USER_HOME_DASHBOARD.md) |
| 5 | Markets | `/markets` | [FRONTEND_USER_HOME_MARKETS.md](user/home/FRONTEND_USER_HOME_MARKETS.md) |

### 💼 Wallet Management (4 Modules)

| # | Module | Route | File |
|---|--------|-------|------|
| 6 | Wallet Overview | `/wallet` | [FRONTEND_USER_WALLET_OVERVIEW.md](user/wallet/FRONTEND_USER_WALLET_OVERVIEW.md) |
| 7 | Token Detail | `/wallet/token/:symbol` | [FRONTEND_USER_WALLET_TOKEN.md](user/wallet/FRONTEND_USER_WALLET_TOKEN.md) |
| 8 | Send | `/wallet/send` | [FRONTEND_USER_WALLET_SEND.md](user/wallet/FRONTEND_USER_WALLET_SEND.md) |
| 9 | Receive | `/wallet/receive` | [FRONTEND_USER_WALLET_RECEIVE.md](user/wallet/FRONTEND_USER_WALLET_RECEIVE.md) |

### 🤖 AI Chat (1 Module)

| # | Module | Route | File |
|---|--------|-------|------|
| 10 | AI Chat (Copilot) | `/chat` | [FRONTEND_USER_CHAT_MAIN.md](user/chat/FRONTEND_USER_CHAT_MAIN.md) |

### 💰 DeFi Operations (6 Modules)

| # | Module | Route | File |
|---|--------|-------|------|
| 11 | Token Swap | `/swap` | [FRONTEND_USER_DEFI_SWAP.md](user/defi/FRONTEND_USER_DEFI_SWAP.md) |
| 12 | Cross-Chain Bridge | `/bridge` | [FRONTEND_USER_DEFI_BRIDGE.md](user/defi/FRONTEND_USER_DEFI_BRIDGE.md) |
| 13 | Earn Overview | `/earn` | [FRONTEND_USER_DEFI_EARN.md](user/defi/FRONTEND_USER_DEFI_EARN.md) |
| 14 | Supply (Lending) | `/earn/supply` | [FRONTEND_USER_DEFI_SUPPLY.md](user/defi/FRONTEND_USER_DEFI_SUPPLY.md) |
| 15 | Borrow | `/earn/borrow` | [FRONTEND_USER_DEFI_BORROW.md](user/defi/FRONTEND_USER_DEFI_BORROW.md) |
| 16 | Stake | `/earn/stake` | [FRONTEND_USER_DEFI_STAKE.md](user/defi/FRONTEND_USER_DEFI_STAKE.md) |

### 📋 Transactions (1 Module)

| # | Module | Route | File |
|---|--------|-------|------|
| 17 | Transaction History | `/transactions` | [FRONTEND_USER_TRANSACTIONS_HISTORY.md](user/transactions/FRONTEND_USER_TRANSACTIONS_HISTORY.md) |

### 🔔 Notifications & Alerts (2 Modules)

| # | Module | Route | File |
|---|--------|-------|------|
| 18 | Notifications | `/notifications` | [FRONTEND_USER_NOTIFICATIONS.md](user/notifications/FRONTEND_USER_NOTIFICATIONS.md) |
| 19 | Price Alerts | `/alerts` | [FRONTEND_USER_ALERTS_PRICE.md](user/notifications/FRONTEND_USER_ALERTS_PRICE.md) |

### ⚙️ Settings (4 Modules)

| # | Module | Route | File |
|---|--------|-------|------|
| 20 | Settings Main | `/settings` | [FRONTEND_USER_SETTINGS_MAIN.md](user/settings/FRONTEND_USER_SETTINGS_MAIN.md) |
| 21 | Profile | `/settings/profile` | [FRONTEND_USER_SETTINGS_PROFILE.md](user/settings/FRONTEND_USER_SETTINGS_PROFILE.md) |
| 22 | Subscription | `/settings/subscription` | [FRONTEND_USER_SETTINGS_SUBSCRIPTION.md](user/settings/FRONTEND_USER_SETTINGS_SUBSCRIPTION.md) |
| 23 | Referrals | `/referrals` | [FRONTEND_USER_SETTINGS_REFERRALS.md](user/settings/FRONTEND_USER_SETTINGS_REFERRALS.md) |

### 🆘 Support (1 Module)

| # | Module | Route | File |
|---|--------|-------|------|
| 24 | Help & Support | `/support` | [FRONTEND_USER_SUPPORT_HELP.md](user/support/FRONTEND_USER_SUPPORT_HELP.md) |

---

## 📁 Directory Structure

```
anvil-user-modules/
├── 00_INDEX.md
└── user/
    ├── onboarding/              (3 modules)
    │   ├── FRONTEND_USER_ONBOARDING_WELCOME.md
    │   ├── FRONTEND_USER_AUTH_LOGIN.md
    │   └── FRONTEND_USER_ONBOARDING_KYC.md
    ├── home/                    (2 modules)
    │   ├── FRONTEND_USER_HOME_DASHBOARD.md
    │   └── FRONTEND_USER_HOME_MARKETS.md
    ├── wallet/                  (4 modules)
    │   ├── FRONTEND_USER_WALLET_OVERVIEW.md
    │   ├── FRONTEND_USER_WALLET_TOKEN.md
    │   ├── FRONTEND_USER_WALLET_SEND.md
    │   └── FRONTEND_USER_WALLET_RECEIVE.md
    ├── chat/                    (1 module)
    │   └── FRONTEND_USER_CHAT_MAIN.md
    ├── defi/                    (6 modules)
    │   ├── FRONTEND_USER_DEFI_SWAP.md
    │   ├── FRONTEND_USER_DEFI_BRIDGE.md
    │   ├── FRONTEND_USER_DEFI_EARN.md
    │   ├── FRONTEND_USER_DEFI_SUPPLY.md
    │   ├── FRONTEND_USER_DEFI_BORROW.md
    │   └── FRONTEND_USER_DEFI_STAKE.md
    ├── transactions/            (1 module)
    │   └── FRONTEND_USER_TRANSACTIONS_HISTORY.md
    ├── notifications/           (2 modules)
    │   ├── FRONTEND_USER_NOTIFICATIONS.md
    │   └── FRONTEND_USER_ALERTS_PRICE.md
    ├── settings/                (4 modules)
    │   ├── FRONTEND_USER_SETTINGS_MAIN.md
    │   ├── FRONTEND_USER_SETTINGS_PROFILE.md
    │   ├── FRONTEND_USER_SETTINGS_SUBSCRIPTION.md
    │   └── FRONTEND_USER_SETTINGS_REFERRALS.md
    └── support/                 (1 module)
        └── FRONTEND_USER_SUPPORT_HELP.md
```

---

## 🧭 Navigation Structure

### Bottom Tab Bar
```
┌─────────────────────────────────────┐
│  🏠     💼     🤖     📊     👤    │
│  Home  Wallet  Chat  Markets Profile│
└─────────────────────────────────────┘
```

### User Flows

**New User Flow:**
```
Welcome → Sign Up → Wallet Created → Personalization → KYC (optional) → Home
```

**Returning User Flow:**
```
Login (Biometric/Email) → Home
```

**DeFi Transaction Flow:**
```
Home → Chat/Swap → Token Selection → Amount → Review → Confirm → Success
```

---

## 🎨 Design System

### Color Tokens (Mobile)

```typescript
const colors = {
  // Primary
  primary: '#3B82F6',
  primaryLight: '#60A5FA',
  primaryDark: '#2563EB',
  
  // Status
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#06B6D4',
  
  // Background (Dark Theme)
  background: '#0F172A',
  surface: '#1E293B',
  surfaceElevated: '#334155',
  
  // Text
  textPrimary: '#F8FAFC',
  textSecondary: '#94A3B8',
  textTertiary: '#64748B',
  
  // Border
  border: '#334155',
  borderLight: '#475569',
};
```

### Typography Scale

```typescript
const typography = {
  // Display
  displayLarge: { size: 32, weight: '700', lineHeight: 40 },
  displayMedium: { size: 28, weight: '700', lineHeight: 36 },
  
  // Headlines
  headlineLarge: { size: 24, weight: '600', lineHeight: 32 },
  headlineMedium: { size: 20, weight: '600', lineHeight: 28 },
  headlineSmall: { size: 18, weight: '600', lineHeight: 24 },
  
  // Body
  bodyLarge: { size: 16, weight: '400', lineHeight: 24 },
  bodyMedium: { size: 14, weight: '400', lineHeight: 20 },
  bodySmall: { size: 12, weight: '400', lineHeight: 16 },
  
  // Labels
  labelLarge: { size: 14, weight: '500', lineHeight: 20 },
  labelMedium: { size: 12, weight: '500', lineHeight: 16 },
  labelSmall: { size: 10, weight: '500', lineHeight: 14 },
};
```

### Spacing Scale

```typescript
const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};
```

### Motion Tokens

```typescript
const motion = {
  duration: {
    instant: 100,
    fast: 150,
    normal: 300,
    slow: 500,
  },
  easing: {
    smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    snappy: 'cubic-bezier(0.2, 0, 0, 1)',
  },
};
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Mobile Framework | React Native |
| Web Framework | React |
| Language | TypeScript |
| Navigation | React Navigation |
| State Management | Zustand + TanStack Query |
| Styling | NativeWind (Tailwind) |
| Animations | Reanimated 3 / Framer Motion |
| Forms | React Hook Form + Zod |
| Auth | Privy SDK |
| Charts | Victory Native / Recharts |

---

## 🔐 Authentication (Privy)

### Supported Methods
- Email (Passwordless OTP)
- Google OAuth
- Apple Sign In
- Wallet Connect (MetaMask, Coinbase, etc.)

### Wallet Types
- **Embedded Wallet (Primary):** Privy MPC wallet - no seed phrase
- **External Wallet:** User's existing wallet (view-only for balance)

---

## 📝 Documentation Standards

Each module includes:
1. Module Overview & Capabilities
2. User Stories with Acceptance Criteria
3. ASCII Wireframes (Mobile-first)
4. Complete TypeScript API Interfaces
5. Framer Motion / Reanimated Animations
6. Error Handling Codes
7. Accessibility Considerations

---

## ✅ Module Checklist

| Domain | Count | Status |
|--------|-------|--------|
| Onboarding & Auth | 3 | ✅ Complete |
| Home & Discovery | 2 | ✅ Complete |
| Wallet Management | 4 | ✅ Complete |
| AI Chat | 1 | ✅ Complete |
| DeFi Operations | 6 | ✅ Complete |
| Transactions | 1 | ✅ Complete |
| Notifications | 2 | ✅ Complete |
| Settings | 4 | ✅ Complete |
| Support | 1 | ✅ Complete |
| **TOTAL** | **24** | **✅ Complete** |

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*All 24 User Modules Complete*
