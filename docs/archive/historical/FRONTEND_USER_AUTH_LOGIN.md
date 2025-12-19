# FRONTEND_USER_AUTH_LOGIN

## User Login Module

**User Type:** Unauthenticated User  
**Module:** Login  
**Route:** `/login`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Login** - User Authentication

### Description
Authentication screen for returning users to sign in via Privy (email, social, or wallet).

---

## 🖼️ Views & Wireframes

### View 1: Login Screen

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│         ┌───────────────┐           │
│         │     ANVIL     │           │
│         │    ◆ ◆ ◆      │           │
│         └───────────────┘           │
│                                     │
│          Welcome Back               │
│                                     │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  📧  Continue with Email    │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  G   Continue with Google   │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  🍎  Continue with Apple    │   │
│   └─────────────────────────────┘   │
│                                     │
│            ─── or ───               │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  🔗  Connect Wallet         │   │
│   └─────────────────────────────┘   │
│                                     │
│                                     │
│      Don't have an account?         │
│           [Sign Up]                 │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### View 2: Email Login

```
┌─────────────────────────────────────┐
│  [←]                                │
│                                     │
│                                     │
│         Sign In with Email          │
│                                     │
│                                     │
│   Email                             │
│   ┌─────────────────────────────┐   │
│   │ alice@example.com           │   │
│   └─────────────────────────────┘   │
│                                     │
│                                     │
│   ┌─────────────────────────────┐   │
│   │      Send Login Code        │   │
│   └─────────────────────────────┘   │
│                                     │
│                                     │
│   We'll email you a secure code     │
│   to sign in. No password needed.   │
│                                     │
│                                     │
│                                     │
│                                     │
│                                     │
│                                     │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### View 3: Biometric Login (Mobile)

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│                                     │
│         ┌───────────────┐           │
│         │     ANVIL     │           │
│         │    ◆ ◆ ◆      │           │
│         └───────────────┘           │
│                                     │
│                                     │
│                                     │
│         ┌───────────────┐           │
│         │               │           │
│         │     👤        │           │
│         │    ────       │           │
│         │   Face ID     │           │
│         │               │           │
│         └───────────────┘           │
│                                     │
│     Sign in with Face ID            │
│                                     │
│                                     │
│      [Use Other Method]             │
│                                     │
│                                     │
│                                     │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// Privy SDK handles authentication
// POST /auth/login via Privy

interface LoginResult {
  success: boolean;
  user?: {
    id: string;
    email?: string;
    wallet_address?: string;
  };
  access_token?: string;
  error?: string;
}
```

---

## 🎬 Motion Design

```typescript
const loginAnimations = {
  logoEntrance: {
    y: [-20, 0],
    opacity: [0, 1],
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  buttonStagger: {
    y: [20, 0],
    opacity: [0, 1],
    transition: { duration: 0.3, delay: 'index * 0.1' }
  },
  
  biometricPulse: {
    scale: [1, 1.1, 1],
    opacity: [0.8, 1, 0.8],
    transition: { duration: 2, repeat: Infinity }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Login*
