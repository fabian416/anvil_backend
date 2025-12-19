# FRONTEND_USER_ONBOARDING_WELCOME

## User Welcome & Onboarding Module

**User Type:** New User  
**Module:** Welcome & Onboarding  
**Route:** `/welcome`, `/onboarding`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**Welcome & Onboarding** - First-Time User Experience

### Description
Engaging onboarding flow introducing new users to Anvil's DeFi capabilities through a conversational AI-first approach, guiding them through wallet setup and initial configuration.

### Key Capabilities
- Welcome carousel/slides
- Value proposition presentation
- Seamless Privy authentication
- Wallet creation/connection
- Personalization preferences
- Skip option for experienced users

---

## 👤 User Stories

### US-USER-ONBOARD-001: View Welcome Screens
**As a** new user  
**I want to** understand what Anvil offers  
**So that** I can decide if it's right for me

**Acceptance Criteria:**
- See 3-4 value proposition slides
- Smooth swipe/navigation between slides
- Skip option always visible
- Progress indicator shown

### US-USER-ONBOARD-002: Create Account
**As a** new user  
**I want to** create an account easily  
**So that** I can start using the app

**Acceptance Criteria:**
- Multiple auth options (email, Google, Apple)
- No seed phrase management required
- Clear privacy policy/terms links
- Loading states during account creation

### US-USER-ONBOARD-003: Set Up Wallet
**As a** new user  
**I want to** have a wallet ready to use  
**So that** I can start DeFi operations

**Acceptance Criteria:**
- Auto-create MPC wallet via Privy
- Option to connect existing wallet
- Clear explanation of wallet security
- Confirmation of wallet creation

### US-USER-ONBOARD-004: Personalize Experience
**As a** new user  
**I want to** set my preferences  
**So that** the app is tailored to me

**Acceptance Criteria:**
- Select experience level (beginner/intermediate/advanced)
- Choose primary interests (trading, lending, staking)
- Set notification preferences
- Optional - can be skipped

---

## 🖼️ Views & Wireframes

### View 1: Welcome Carousel (Mobile)

```
┌─────────────────────────────────────┐
│                              [Skip] │
│                                     │
│                                     │
│         ┌─────────────────┐         │
│         │                 │         │
│         │    🤖 + 💰      │         │
│         │                 │         │
│         │  [Illustration] │         │
│         │                 │         │
│         └─────────────────┘         │
│                                     │
│                                     │
│      Your AI-Powered DeFi          │
│           Assistant                 │
│                                     │
│   Chat naturally to swap, stake,   │
│   lend, and manage your crypto     │
│   across multiple chains.          │
│                                     │
│                                     │
│            ● ○ ○ ○                  │
│                                     │
│   ┌─────────────────────────────┐   │
│   │        Get Started          │   │
│   └─────────────────────────────┘   │
│                                     │
│      Already have an account?       │
│            [Sign In]                │
│                                     │
└─────────────────────────────────────┘
```

### View 2: Welcome Slide 2

```
┌─────────────────────────────────────┐
│                              [Skip] │
│                                     │
│         ┌─────────────────┐         │
│         │                 │         │
│         │   ⛓️ ↔️ ⛓️      │         │
│         │                 │         │
│         │  [Illustration] │         │
│         │                 │         │
│         └─────────────────┘         │
│                                     │
│                                     │
│       Multi-Chain Made Easy        │
│                                     │
│   Seamlessly operate across        │
│   Ethereum, Arbitrum, Polygon,     │
│   and Base - all in one place.     │
│                                     │
│                                     │
│            ○ ● ○ ○                  │
│                                     │
│   ┌─────────────────────────────┐   │
│   │           Next              │   │
│   └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### View 3: Welcome Slide 3

```
┌─────────────────────────────────────┐
│                              [Skip] │
│                                     │
│         ┌─────────────────┐         │
│         │                 │         │
│         │    🔐 ✨        │         │
│         │                 │         │
│         │  [Illustration] │         │
│         │                 │         │
│         └─────────────────┘         │
│                                     │
│                                     │
│      No Seed Phrases Needed        │
│                                     │
│   Our secure MPC wallet means      │
│   you never have to worry about    │
│   losing access to your funds.     │
│                                     │
│                                     │
│            ○ ○ ● ○                  │
│                                     │
│   ┌─────────────────────────────┐   │
│   │           Next              │   │
│   └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### View 4: Sign Up Options

```
┌─────────────────────────────────────┐
│  [←]                                │
│                                     │
│                                     │
│            Create Your              │
│             Account                 │
│                                     │
│    Get started in under a minute   │
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
│   │  🔗  Connect Existing Wallet│   │
│   └─────────────────────────────┘   │
│                                     │
│                                     │
│   By continuing, you agree to our   │
│   Terms of Service and Privacy      │
│   Policy.                           │
│                                     │
└─────────────────────────────────────┘
```

### View 5: Email Sign Up

```
┌─────────────────────────────────────┐
│  [←]                                │
│                                     │
│                                     │
│          Enter Your Email           │
│                                     │
│   We'll send you a verification    │
│   code to get started.             │
│                                     │
│                                     │
│   Email                             │
│   ┌─────────────────────────────┐   │
│   │ alice@example.com           │   │
│   └─────────────────────────────┘   │
│                                     │
│                                     │
│   ┌─────────────────────────────┐   │
│   │        Send Code            │   │
│   └─────────────────────────────┘   │
│                                     │
│                                     │
│                                     │
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

### View 6: Verification Code

```
┌─────────────────────────────────────┐
│  [←]                                │
│                                     │
│                                     │
│         Enter the Code              │
│                                     │
│   We sent a 6-digit code to        │
│   alice@example.com                │
│                                     │
│                                     │
│      ┌───┬───┬───┬───┬───┬───┐     │
│      │ 4 │ 2 │ 8 │ 9 │ _ │ _ │     │
│      └───┴───┴───┴───┴───┴───┘     │
│                                     │
│                                     │
│      Didn't receive it?            │
│      [Resend Code] (0:45)          │
│                                     │
│                                     │
│                                     │
│                                     │
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

### View 7: Wallet Creation

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│         ┌─────────────────┐         │
│         │                 │         │
│         │    🎉 ✨        │         │
│         │                 │         │
│         └─────────────────┘         │
│                                     │
│                                     │
│      Your Wallet is Ready!         │
│                                     │
│   We've created a secure wallet    │
│   for you. No seed phrases to      │
│   remember - ever.                 │
│                                     │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  Your Wallet Address        │   │
│   │  0x7a23...8f4d         [📋] │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌───────────────────────────────┐ │
│   │ 🔐 Secured by Privy MPC       │ │
│   │    Your keys are split across │ │
│   │    multiple secure locations  │ │
│   └───────────────────────────────┘ │
│                                     │
│   ┌─────────────────────────────┐   │
│   │        Continue             │   │
│   └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### View 8: Personalization

```
┌─────────────────────────────────────┐
│                              [Skip] │
│                                     │
│       Let's Personalize Your       │
│           Experience                │
│                                     │
│                                     │
│   What's your DeFi experience?     │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  🌱  I'm New to DeFi        │   │
│   │      Guide me step by step  │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  📈  I Have Some Experience │   │
│   │      Show me the basics     │   │
│   └─────────────────────────────┘   │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  🚀  I'm a DeFi Pro         │   │
│   │      Skip the tutorials     │   │
│   └─────────────────────────────┘   │
│                                     │
│                                     │
│                                     │
│                                     │
│                                     │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Create Account (Privy)

```typescript
// Handled by Privy SDK
// POST /auth/login (Privy endpoint)

interface PrivyAuthResult {
  user: {
    id: string;
    email?: string;
    wallet?: {
      address: string;
      chain_id: number;
    };
  };
  access_token: string;
}
```

### Complete Onboarding

```typescript
// POST /api/users/onboarding
interface CompleteOnboardingRequest {
  experience_level: 'beginner' | 'intermediate' | 'advanced';
  interests?: ('trading' | 'lending' | 'staking' | 'yield')[];
  notifications_enabled?: boolean;
}

interface CompleteOnboardingResponse {
  success: true;
  data: {
    user_id: string;
    onboarding_complete: true;
    recommended_actions: string[];
  };
}
```

### Check Onboarding Status

```typescript
// GET /api/users/me/onboarding
interface OnboardingStatusResponse {
  success: true;
  data: {
    onboarding_complete: boolean;
    steps_completed: string[];
    current_step?: string;
  };
}
```

---

## 🎬 Motion Design

```typescript
const onboardingAnimations = {
  slideTransition: {
    x: ['100%', '0%'],
    opacity: [0, 1],
    transition: { duration: 0.3, ease: 'easeOut' }
  },
  
  illustrationEntrance: {
    scale: [0.8, 1],
    opacity: [0, 1],
    transition: { duration: 0.5, ease: 'easeOut' }
  },
  
  buttonPulse: {
    scale: [1, 1.02, 1],
    transition: { duration: 2, repeat: Infinity }
  },
  
  walletCreated: {
    scale: [0.5, 1.1, 1],
    opacity: [0, 1],
    transition: { duration: 0.5, ease: 'backOut' }
  },
  
  codeInput: {
    scale: [1, 1.05, 1],
    transition: { duration: 0.15 }
  }
};
```

---

## 🎨 Component Specifications

```typescript
interface WelcomeSlideProps {
  illustration: React.ReactNode;
  title: string;
  description: string;
  currentIndex: number;
  totalSlides: number;
  onNext: () => void;
  onSkip: () => void;
}

interface AuthButtonProps {
  provider: 'email' | 'google' | 'apple' | 'wallet';
  onPress: () => void;
  loading?: boolean;
}

interface CodeInputProps {
  length: number;
  value: string;
  onChange: (code: string) => void;
  error?: string;
  autoFocus?: boolean;
}

interface ExperienceLevelCardProps {
  level: 'beginner' | 'intermediate' | 'advanced';
  icon: string;
  title: string;
  description: string;
  selected: boolean;
  onSelect: () => void;
}
```

---

## ⚠️ Error Handling

```typescript
const onboardingErrors = {
  AUTH_001: 'Invalid email format',
  AUTH_002: 'Email already registered',
  AUTH_003: 'Invalid verification code',
  AUTH_004: 'Code expired, please request a new one',
  AUTH_005: 'Too many attempts, please try again later',
  WALLET_001: 'Failed to create wallet',
  WALLET_002: 'Wallet connection failed',
  NETWORK_001: 'Network error, please check connection',
};
```

---

## ♿ Accessibility

- VoiceOver/TalkBack support for all elements
- Minimum touch target 44x44pt
- High contrast text on all backgrounds
- Screen reader announcements for step changes
- Keyboard navigation support (web)

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: Welcome & Onboarding*
