# Module: Welcome & Onboarding

**Route**: `/welcome`
**Auth Required**: No
**Package**: `user/onboarding`

## 1. Overview
The entry point for new users. Displays the value proposition of the Anvil app and provides options to create a new account (seedless wallet) or log in to an existing one.

### Key Features
- **Dynamic Onboarding Carousel**: value props (AI, DeFi, Yields).
- **Navigation Branching**: "Create Account" vs "Log In".

## 2. UI/UX Specification

### Components
- `OnboardingCarousel`: Handles slides and auto-play logic.
- `PrimaryButton`: "Create New Wallet".
- `SecondaryButton`: "I already have an account".

### Interactions
- **Mount**: Check `localStorage` for existing session.
- **Tap "Create"**: Directs to `/signup` (wraps Privy Login).
- **Tap "Login"**: Directs to `/login` (wraps Privy Login).

## 3. Technical Implementation

### Auth State Check
The Welcome screen must strictly check for existing valid session tokens before rendering.

```typescript
// Logic Flow
const hasToken = storage.getItem('access_token');
const privyAuthenticated = privy.authenticated;

if (hasToken && privyAuthenticated) {
  router.replace('/home');
} else {
  // Clear any stale state
  storage.clear(); 
}
```

### API Integration
*No direct backend calls from this screen.*
However, acts as the gatekeeper for:
- `privy_user_id` context initialization.
