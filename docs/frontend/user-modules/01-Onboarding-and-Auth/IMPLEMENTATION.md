# Auth Module Implementation Files

> **Complete TypeScript/React Implementation for Authentication Modules**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **Authentication & Onboarding** module is the critical entry point for all users. It handles the first impression, security, and user journey from anonymous visitor to authenticated user.

### Key Capabilities
1. **Privy Integration**: Seamless wallet and social login via Privy
2. **Token Management**: Secure JWT token storage and refresh
3. **User Onboarding**: Welcome flow and KYC/profile setup
4. **Session Management**: Persistent authentication across app restarts

### Business Value
- **Security**: Enterprise-grade authentication with multiple providers
- **User Experience**: Frictionless onboarding (< 60 seconds to first use)
- **Compliance**: KYC-ready profile management
- **Retention**: Persistent sessions reduce re-authentication friction

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: Users need secure, fast authentication without friction.

**Root Cause Analysis**:
- **Friction Source**: Multiple steps, unclear flows, authentication failures
- **Solution**: Single-click Privy integration, clear visual feedback, graceful error handling

**Design Decisions**:
1. **Single Entry Point**: Welcome screen → Login → Dashboard (no branching)
2. **Progressive Disclosure**: Show only what's needed at each step
3. **Error Recovery**: Clear, actionable error messages with recovery paths
4. **Visual Feedback**: Loading states, success animations, error toasts

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────┐
│              Welcome Screen              │
│  ┌───────────────────────────────────┐  │
│  │   Onboarding Carousel (3 slides)   │  │
│  │   - AI-Powered DeFi                │  │
│  │   - Multi-Chain Support            │  │
│  │   - Secure Wallet                  │  │
│  └───────────────────────────────────┘  │
│  ┌──────────┐      ┌──────────┐         │
│  │  Create  │      │   Login  │         │
│  │ Account  │      │          │         │
│  └──────────┘      └──────────┘         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│              Login Screen               │
│  ┌───────────────────────────────────┐  │
│  │      Anvil Logo                   │  │
│  │  "Welcome to Anvil"               │  │
│  │  "Connect your wallet or sign in" │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   [Sign In with Privy]            │  │
│  │   (Wallet/Social/Email options)   │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Error Toast (if error)         │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│            KYC/Profile Screen          │
│  ┌───────────────────────────────────┐  │
│  │   Step 1: Personal Information    │  │
│  │   [First Name] [Last Name]        │  │
│  │   [Country] [City]                 │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   Step 2: Profile Picture (opt)   │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   [Continue] [Skip for Now]       │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

#### Color Palette
- **Primary**: `#3B82F6` (Blue) - Trust, security
- **Success**: `#10B981` (Green) - Success states
- **Error**: `#EF4444` (Red) - Errors, warnings
- **Background**: `#FFFFFF` (White) / `#F9FAFB` (Gray-50)
- **Text**: `#111827` (Gray-900) - Primary text
- **Text Secondary**: `#6B7280` (Gray-500) - Secondary text

#### Typography
- **Headings**: Inter, 700 weight, 24-32px
- **Body**: Inter, 400 weight, 16px
- **Labels**: Inter, 500 weight, 14px
- **Helper Text**: Inter, 400 weight, 12px

#### Spacing System
- **Container Padding**: 24px (mobile), 32px (desktop)
- **Component Gap**: 16px (mobile), 24px (desktop)
- **Form Field Gap**: 16px vertical
- **Button Padding**: 12px 24px (medium), 16px 32px (large)

#### Component Specifications

##### Primary Button (Login/Action)
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost'
  size: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  fullWidth?: boolean
  children: React.ReactNode
}
```

**Visual States**:
- **Default**: Blue background (`#3B82F6`), white text, rounded 8px
- **Hover**: Darker blue (`#2563EB`), subtle shadow
- **Active**: Pressed state, slightly darker
- **Loading**: Spinner icon, disabled state, "Signing in..."
- **Disabled**: 50% opacity, gray background, no interaction

##### Input Fields
```typescript
interface InputProps {
  label: string
  type: 'text' | 'email' | 'password' | 'tel'
  placeholder?: string
  error?: string
  helpText?: string
  required?: boolean
  disabled?: boolean
}
```

**Visual States**:
- **Default**: White background, gray border (`#D1D5DB`), rounded 8px
- **Focus**: Blue border (`#3B82F6`), ring effect (2px)
- **Error**: Red border (`#EF4444`), error icon, error message below
- **Disabled**: Gray background (`#F3F4F6`), reduced opacity

##### Error Toast
```typescript
interface ErrorToastProps {
  message: string
  onClose: () => void
  action?: {
    label: string
    onClick: () => void
  }
}
```

**Visual Design**:
- Red background (`#FEE2E2`), red border, red icon
- Position: Top-center (mobile), top-right (desktop)
- Auto-dismiss: 5 seconds
- Dismissible: X button

### Responsive Breakpoints

**Mobile** (< 640px):
- Single column layout
- Full-width buttons
- Stacked form fields
- Bottom sheet for Privy modal

**Tablet** (640px - 1024px):
- Centered card (max-width: 480px)
- Two-column form (if applicable)
- Side-by-side buttons

**Desktop** (> 1024px):
- Centered card (max-width: 520px)
- Optimal spacing
- Hover states enabled

### Accessibility Requirements (WCAG 2.1 AA)

1. **Keyboard Navigation**:
   - Tab order: Logo → Heading → Button → Links
   - Enter/Space activates buttons
   - Escape closes modals/toasts

2. **Screen Readers**:
   - All buttons have `aria-label`
   - Form fields have `aria-describedby` for help text
   - Error messages have `role="alert"`
   - Loading states announced

3. **Color Contrast**:
   - Text: 4.5:1 minimum
   - Buttons: 3:1 minimum
   - Error states: 4.5:1

4. **Focus Indicators**:
   - Visible focus rings (2px blue)
   - Focus trap in modals
   - Focus restoration on modal close

### Loading States

**Privy Connection**:
- Button shows spinner
- Text: "Connecting..."
- Disabled state

**Backend Authentication**:
- Button shows spinner
- Text: "Signing in..."
- Disabled state
- Optional: Progress indicator

**Token Storage**:
- Silent (happens in background)
- No UI feedback needed

### Empty States

**No Session**:
- Welcome screen displayed
- Clear CTAs
- No error shown

### Error States

**Privy Connection Failed**:
- Error toast: "Failed to connect. Please try again."
- Retry button in toast
- Button re-enabled

**Authentication Failed**:
- Error toast with specific message
- Action: "Try Again" or "Contact Support"
- Button re-enabled

**Network Error**:
- Error toast: "Connection error. Check your internet."
- Retry button
- Offline indicator (if applicable)

---

## 🔌 API Endpoints

### 1. Privy Login

**Method**: `POST`  
**Endpoint**: `/api/v1/account/privy-login`  
**Auth Required**: No (Public)  
**Content-Type**: `application/json`

#### Request

##### Headers
```http
Content-Type: application/json
```

##### Request Body
```typescript
interface PrivyLoginRequest {
  privy_user_id: string;        // Required: DID from Privy (e.g., "did:privy:abc123xyz")
  email?: string;                // Optional: User email if available
  wallet_address?: string;       // Optional: Primary wallet address (0x...)
  auth_provider?: string;        // Optional: "privy" | "google" | "apple" | "discord" | "wallet" (default: "privy")
  first_name?: string;           // Optional: User first name
  last_name?: string;            // Optional: User last name
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `privy_user_id` | `string` | **Yes** | Privy DID identifier | Must start with "did:privy:" |
| `email` | `string` | No | User email address | Valid email format |
| `wallet_address` | `string` | No | Ethereum wallet address | Valid 0x address format |
| `auth_provider` | `string` | No | Authentication provider | One of: privy, google, apple, discord, wallet |
| `first_name` | `string` | No | User first name | Max 100 chars |
| `last_name` | `string` | No | User last name | Max 100 chars |

**JSON Example**:
```json
{
  "privy_user_id": "did:privy:abc123xyz",
  "email": "alice@example.com",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "auth_provider": "google",
  "first_name": "Alice",
  "last_name": "Smith"
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface PrivyLoginResponse {
  access_token: string;      // JWT Bearer Token (expires in 24h)
  refresh_token: string;     // JWT Refresh Token (expires in 30d)
  token_type: string;        // Always "bearer"
  user_id: number;          // Anvil Internal User ID
  email: string;            // Confirmed email address
  is_new_user: boolean;     // Critical: true = redirect to /onboarding/kyc
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| `access_token` | `string` | JWT token for API authentication (24h expiry) |
| `refresh_token` | `string` | JWT token for refreshing access token (30d expiry) |
| `token_type` | `string` | Always "bearer" |
| `user_id` | `number` | Internal user identifier |
| `email` | `string` | User's email address |
| `is_new_user` | `boolean` | **Critical**: If `true`, user must complete KYC/profile setup |

**JSON Example**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 42,
  "email": "alice@example.com",
  "is_new_user": true
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `DomainFieldError` | Missing or invalid `privy_user_id` | Show error toast: "Invalid request. Please try again." |
| `401` | `AuthenticationError` | Invalid Privy signature or user | Show error toast: "Authentication failed. Please sign in again." → Force Privy re-login |
| `409` | `EmailAlreadyExistsError` | Email already registered with different provider | Show error toast: "Email already used. Try logging in with Google?" → Show provider options |
| `500` | `InternalServerError` | Server error | Show error toast: "Something went wrong. Please try again." → Retry button |
| `503` | `DataMapperError` | Database unavailable | Show error toast: "Service temporarily unavailable. Please try again later." → Retry after delay |

**Error Response Format**:
```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid Privy signature",
    "details": {
      "field": "privy_user_id"
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### 2. Get Current User Profile

**Method**: `GET`  
**Endpoint**: `/api/v1/account/me`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

#### Response

##### Success Response (200 OK)
```typescript
interface MeResponse {
  id: number;
  email: string;
  is_verified: boolean;        // KYC verification status
  country_id?: number;         // ISO country ID
  country_name?: string;       // e.g., "United States"
  city_id?: number;            // City ID
  city_name?: string;          // City name
  profile_picture?: string;    // URL to profile picture
  first_name?: string;
  last_name?: string;
  created_at: string;          // ISO 8601 timestamp
  updated_at: string;          // ISO 8601 timestamp
}
```

**JSON Example**:
```json
{
  "id": 42,
  "email": "alice@example.com",
  "is_verified": false,
  "country_id": 840,
  "country_name": "United States",
  "city_id": 1205,
  "city_name": "New York",
  "profile_picture": "https://cdn.anvil.com/profiles/42.jpg",
  "first_name": "Alice",
  "last_name": "Smith",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `503` | `DataMapperError` | Database unavailable | Show error: "Unable to load profile" |

### 3. Update User Profile (KYC)

**Method**: `PUT`  
**Endpoint**: `/api/v1/account/me`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface UpdateMeRequest {
  first_name?: string;         // Optional: User first name
  last_name?: string;          // Optional: User last name
  country_id?: number;         // Optional: ISO country ID (must match countries table)
  city_id?: number;            // Optional: City ID (must belong to country)
  profile_picture?: string;     // Optional: S3/CDN URL
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `first_name` | `string` | No | User first name | Max 100 chars, alphanumeric + spaces |
| `last_name` | `string` | No | User last name | Max 100 chars, alphanumeric + spaces |
| `country_id` | `number` | No | ISO country ID | Must exist in countries table |
| `city_id` | `number` | No | City ID | Must belong to specified country |
| `profile_picture` | `string` | No | Profile picture URL | Valid URL format |

**JSON Example**:
```json
{
  "first_name": "Alice",
  "last_name": "Smith",
  "country_id": 840,
  "city_id": 1205
}
```

#### Response

##### Success Response (200 OK)
Returns updated `MeResponse` (same as GET /me)

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `DomainFieldError` | Invalid country_id or city_id | Show inline error: "Invalid region. Please select a valid country and city." |
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `503` | `DataMapperError` | Database unavailable | Show error toast: "Profile update failed. Please try again." |

### 4. Refresh Token

**Method**: `POST`  
**Endpoint**: `/api/v1/account/refresh-token`  
**Auth Required**: No (Uses refresh token)

#### Request

##### Request Body
```typescript
interface RefreshTokenRequest {
  refresh_token: string;
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
```

### 5. Logout

**Method**: `DELETE`  
**Endpoint**: `/api/v1/account/logout`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (204 No Content)
No response body. Clears server-side session.

---

## 🔄 User Flows & Use Cases

### Use Case 1: New User Onboarding (Happy Path)

**Actor**: New User  
**Goal**: Create account and complete profile setup  
**Preconditions**: User is on welcome screen, no existing session

#### Flow Steps

1. **Entry Point**: User navigates to `/welcome` or app opens
2. **Initial State**: 
   - Welcome screen displays onboarding carousel
   - Two CTAs: "Create Account" and "I already have an account"
3. **User Action**: User taps "Create Account"
4. **System Response**: 
   - Navigate to `/login`
   - Display login screen with Privy button
5. **User Action**: User taps "Sign In with Privy"
6. **System Response**:
   - Privy modal opens (wallet/social/email options)
   - User selects authentication method
   - Privy authenticates user
7. **User Action**: Privy authentication succeeds
8. **System Response**:
   - Extract Privy user data
   - Call `POST /api/v1/account/privy-login`
   - Store tokens in secure storage
   - Check `is_new_user` flag
9. **Success Path**:
   - If `is_new_user === true`:
     - Navigate to `/onboarding/kyc`
     - Display KYC/profile form
   - User completes profile:
     - Call `PUT /api/v1/account/me`
     - Navigate to `/home`
10. **Error Path**:
    - If authentication fails:
      - Show error toast
      - Re-enable login button
      - Allow retry

#### Flow Diagram
```
[User] → [Welcome Screen]
         ↓
    [Create Account]
         ↓
    [Login Screen]
         ↓
    [Privy Modal]
         ↓
    ┌────────────┐
    │ Success?   │
    └────────────┘
         ↓
    ┌────────────┐
    │ New User?  │ → Yes → [KYC Screen] → [Home]
    └────────────┘
         ↓ No
    [Home Dashboard]
```

#### Success Criteria
- [ ] User completes onboarding in < 60 seconds
- [ ] All authentication steps are clear
- [ ] Error recovery is intuitive
- [ ] Tokens are securely stored
- [ ] User is redirected correctly based on `is_new_user`

### Use Case 2: Returning User Login

**Actor**: Returning User  
**Goal**: Sign in to existing account  
**Preconditions**: User has existing account

#### Flow Steps

1. **Entry Point**: User navigates to `/login` or app opens
2. **Initial State**: 
   - Check for existing valid token
   - If token exists and valid → Navigate to `/home`
   - If no token → Show login screen
3. **User Action**: User taps "Sign In with Privy"
4. **System Response**: 
   - Privy modal opens
   - User authenticates
5. **User Action**: Privy authentication succeeds
6. **System Response**:
   - Call `POST /api/v1/account/privy-login`
   - Store tokens
   - Check `is_new_user` flag (should be `false`)
7. **Success Path**:
   - Navigate directly to `/home`
   - Load user profile via `GET /api/v1/account/me`

#### Success Criteria
- [ ] Returning users can login in < 10 seconds
- [ ] Session persists across app restarts
- [ ] No unnecessary redirects

### Use Case 3: Profile/KYC Completion

**Actor**: New User (after login)  
**Goal**: Complete profile setup for KYC  
**Preconditions**: User is authenticated, `is_new_user === true`

#### Flow Steps

1. **Entry Point**: User redirected to `/onboarding/kyc` after login
2. **Initial State**: 
   - Load current profile via `GET /api/v1/account/me`
   - Display form with current values (if any)
3. **User Action**: User fills form (name, country, city)
4. **System Response**:
   - Real-time validation
   - Show field errors if invalid
5. **User Action**: User taps "Continue"
6. **System Response**:
   - Show loading state
   - Call `PUT /api/v1/account/me`
7. **Success Path**:
   - Profile updated successfully
   - Show success message
   - Navigate to `/home`
8. **Error Path**:
   - If validation fails:
     - Show inline field errors
     - Prevent submission
   - If API error:
     - Show error toast
     - Allow retry

#### Success Criteria
- [ ] Form validation is clear and immediate
- [ ] Country/city selection is intuitive
- [ ] Profile updates successfully
- [ ] User can skip optional fields

---

## 📁 File Structure

```
src/modules/auth/
├── login/
│   ├── Login.tsx                    # Main login component
│   ├── Login.types.ts               # TypeScript types
│   ├── Login.hooks.ts               # Custom hooks
│   ├── Login.service.ts             # API service
│   ├── components/
│   │   ├── LoginForm.tsx
│   │   ├── PrivyAuthButton.tsx
│   │   └── AuthErrorToast.tsx
│   └── __tests__/
│       ├── Login.test.tsx
│       └── Login.service.test.ts
├── welcome/
│   ├── Welcome.tsx
│   ├── Welcome.types.ts
│   ├── Welcome.hooks.ts
│   ├── components/
│   │   ├── OnboardingCarousel.tsx
│   │   └── WelcomeActions.tsx
│   └── __tests__/
├── kyc/
│   ├── KYC.tsx
│   ├── KYC.types.ts
│   ├── KYC.hooks.ts
│   ├── KYC.service.ts
│   ├── components/
│   │   ├── KYCForm.tsx
│   │   └── KYCSteps.tsx
│   └── __tests__/
└── shared/
    ├── authStore.ts                 # Auth state management
    ├── tokenStorage.ts              # Secure token storage
    └── authUtils.ts                 # Auth utilities
```

## 🔑 Key Implementation Files

### 1. Login Module

#### `Login.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type { PrivyLoginRequest, PrivyLoginResponse } from './Login.types';

export const loginService = {
  async privyLogin(request: PrivyLoginRequest): Promise<PrivyLoginResponse> {
    const response = await apiClient.post<PrivyLoginResponse>(
      '/api/v1/account/privy-login',
      request
    );
    return response.data;
  },
};
```

#### `Login.types.ts`
```typescript
export interface PrivyLoginRequest {
  privy_user_id: string;
  email?: string;
  wallet_address?: string;
  auth_provider?: string;
  first_name?: string;
  last_name?: string;
}

export interface PrivyLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
  email: string;
  is_new_user: boolean;
}

export interface LoginError {
  code: string;
  message: string;
  status: number;
}
```

#### `Login.hooks.ts`
```typescript
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { loginService } from './Login.service';
import { useAuthStore } from '../shared/authStore';
import type { PrivyLoginRequest, PrivyLoginResponse } from './Login.types';

export function useLogin() {
  const router = useRouter();
  const { setTokens, setUser } = useAuthStore();

  return useMutation({
    mutationFn: (request: PrivyLoginRequest) => loginService.privyLogin(request),
    onSuccess: (response: PrivyLoginResponse) => {
      // Store tokens
      setTokens({
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      });
      
      // Store user info
      setUser({
        id: response.user_id,
        email: response.email,
      });

      // Route based on new user flag
      if (response.is_new_user) {
        router.push('/onboarding/kyc');
      } else {
        router.push('/home');
      }
    },
    onError: (error) => {
      // Error handling
      console.error('Login failed:', error);
    },
  });
}
```

#### `Login.tsx`
```typescript
'use client';

import React, { useEffect } from 'react';
import { usePrivy } from '@privy-io/react-auth';
import { useLogin } from './Login.hooks';
import { LoginForm } from './components/LoginForm';
import { AuthErrorToast } from './components/AuthErrorToast';
import { Button } from '@/design-system/components/Button';
import { Card } from '@/design-system/components/Card';

export const Login: React.FC = () => {
  const { ready, authenticated, login, user } = usePrivy();
  const loginMutation = useLogin();
  const [error, setError] = React.useState<string | null>(null);

  useEffect(() => {
    // Check if already authenticated
    if (ready && authenticated && user) {
      handlePrivySuccess(user);
    }
  }, [ready, authenticated, user]);

  const handlePrivyLogin = async () => {
    try {
      setError(null);
      await login();
    } catch (err) {
      setError('Failed to connect with Privy');
    }
  };

  const handlePrivySuccess = async (privyUser: any) => {
    try {
      // Extract Privy user data
      const loginRequest = {
        privy_user_id: privyUser.id,
        email: privyUser.email?.address,
        wallet_address: privyUser.wallet?.address,
        auth_provider: determineAuthProvider(privyUser),
        first_name: privyUser.google?.name?.split(' ')[0],
        last_name: privyUser.google?.name?.split(' ').slice(1).join(' '),
      };

      // Call backend login
      await loginMutation.mutateAsync(loginRequest);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed');
    }
  };

  const determineAuthProvider = (user: any): string => {
    if (user.google) return 'google';
    if (user.apple) return 'apple';
    if (user.discord) return 'discord';
    if (user.wallet) return 'wallet';
    return 'privy';
  };

  if (!ready) {
    return <div>Loading...</div>;
  }

  return (
    <div className="login-container">
      <Card>
        <h1>Welcome to Anvil</h1>
        <p>Connect your wallet or sign in to continue</p>
        
        <Button
          onClick={handlePrivyLogin}
          loading={loginMutation.isPending}
          disabled={loginMutation.isPending}
          fullWidth
        >
          Sign In with Privy
        </Button>

        {error && <AuthErrorToast message={error} onClose={() => setError(null)} />}
      </Card>
    </div>
  );
};
```

### 2. Welcome Module

#### `Welcome.tsx`
```typescript
'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../shared/authStore';
import { OnboardingCarousel } from './components/OnboardingCarousel';
import { WelcomeActions } from './components/WelcomeActions';
import { Button } from '@/design-system/components/Button';

export const Welcome: React.FC = () => {
  const router = useRouter();
  const { hasValidToken } = useAuthStore();

  useEffect(() => {
    // Check for existing session
    if (hasValidToken()) {
      router.replace('/home');
    }
  }, [hasValidToken, router]);

  const handleCreateAccount = () => {
    router.push('/login');
  };

  const handleLogin = () => {
    router.push('/login');
  };

  return (
    <div className="welcome-container">
      <OnboardingCarousel />
      <WelcomeActions
        onCreateAccount={handleCreateAccount}
        onLogin={handleLogin}
      />
    </div>
  );
};
```

### 3. KYC Module

#### `KYC.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type { KYCRequest, KYCResponse } from './KYC.types';

export const kycService = {
  async submitKYC(request: KYCRequest): Promise<KYCResponse> {
    const response = await apiClient.post<KYCResponse>(
      '/api/v1/user/kyc',
      request
    );
    return response.data;
  },
};
```

## 📝 Complete File List

### Login Module
- [x] `Login.tsx` - Main component
- [x] `Login.types.ts` - TypeScript types
- [x] `Login.hooks.ts` - React hooks
- [x] `Login.service.ts` - API service
- [ ] `components/LoginForm.tsx` - Form component
- [ ] `components/PrivyAuthButton.tsx` - Privy button
- [ ] `components/AuthErrorToast.tsx` - Error display
- [ ] `__tests__/Login.test.tsx` - Component tests
- [ ] `__tests__/Login.service.test.ts` - Service tests

### Welcome Module
- [x] `Welcome.tsx` - Main component
- [ ] `Welcome.types.ts` - Types
- [ ] `Welcome.hooks.ts` - Hooks
- [ ] `components/OnboardingCarousel.tsx` - Carousel
- [ ] `components/WelcomeActions.tsx` - Action buttons
- [ ] `__tests__/Welcome.test.tsx` - Tests

### KYC Module
- [x] `KYC.service.ts` - Service structure
- [ ] `KYC.tsx` - Main component
- [ ] `KYC.types.ts` - Types
- [ ] `KYC.hooks.ts` - Hooks
- [ ] `components/KYCForm.tsx` - Form
- [ ] `components/KYCSteps.tsx` - Step indicator
- [ ] `__tests__/KYC.test.tsx` - Tests

### Shared Auth
- [ ] `authStore.ts` - Zustand/Redux store
- [ ] `tokenStorage.ts` - Secure storage
- [ ] `authUtils.ts` - Utilities

---

## 🧪 Testing Requirements

### Unit Tests

**Login Component** (`Login.test.tsx`):
- [ ] Renders login form correctly
- [ ] Handles Privy login button click
- [ ] Displays error toast on failure
- [ ] Shows loading state during authentication
- [ ] Routes correctly on success (new user vs returning)

**Login Service** (`Login.service.test.ts`):
- [ ] Calls correct API endpoint
- [ ] Formats request correctly
- [ ] Handles success response
- [ ] Handles error responses (400, 401, 409, 503)
- [ ] Validates request data

**KYC Form** (`KYC.test.tsx`):
- [ ] Renders form fields
- [ ] Validates required fields
- [ ] Validates country/city relationship
- [ ] Submits form data correctly
- [ ] Handles API errors

### Integration Tests

**Authentication Flow**:
- [ ] Complete login flow (Privy → Backend → Token storage)
- [ ] Token refresh flow
- [ ] Logout flow
- [ ] Session persistence

**Profile Update Flow**:
- [ ] Load profile data
- [ ] Update profile
- [ ] Handle validation errors
- [ ] Handle API errors

### E2E Tests

**New User Journey**:
- [ ] Welcome → Login → KYC → Dashboard
- [ ] All steps complete successfully
- [ ] Error recovery at each step

**Returning User Journey**:
- [ ] Login → Dashboard (no KYC)
- [ ] Session persists across app restarts

### Performance Tests

- [ ] Login completes in < 2 seconds
- [ ] Profile load in < 1 second
- [ ] Form validation is instant (< 100ms)

### Accessibility Tests

- [ ] Keyboard navigation works
- [ ] Screen reader announces all states
- [ ] Color contrast meets WCAG 2.1 AA
- [ ] Focus indicators visible
- [ ] Error messages are accessible

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **Privy SDK Changes**
   - **Risk**: Privy SDK updates may break integration
   - **Mitigation**: Version pinning, comprehensive testing
   - **Validation**: Test with latest Privy SDK versions

2. **Token Storage Security**
   - **Risk**: Tokens may be compromised on device
   - **Mitigation**: Use secure storage (Keychain/Keystore)
   - **Validation**: Security audit of token storage

3. **Network Edge Cases**
   - **Risk**: Offline scenarios, slow networks
   - **Mitigation**: Offline detection, retry logic
   - **Validation**: Test on slow 3G, offline mode

4. **Multi-Device Scenarios**
   - **Risk**: User logs in on multiple devices
   - **Mitigation**: Session management, device tracking
   - **Validation**: Test concurrent sessions

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **Hardcoded Error Messages**
   - **Debt**: Error messages not localized
   - **Cost**: Poor UX for international users
   - **Prevention**: Use i18n from start

2. **Missing Token Refresh**
   - **Debt**: Manual re-login required
   - **Cost**: Poor user experience
   - **Prevention**: Implement automatic token refresh

3. **No Offline Support**
   - **Debt**: App unusable offline
   - **Cost**: Poor user experience
   - **Prevention**: Cache tokens, detect offline state

### Validation & Testing Strategy

**Success Criteria**:
- ✅ Login success rate > 99%
- ✅ Average login time < 2 seconds
- ✅ Error recovery rate > 95%
- ✅ Accessibility score 100/100

**Failure Detection**:
- Monitor login failure rates
- Track error types
- Alert on high failure rates
- Log all authentication attempts

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/account/privy_login.py`
- **Backend Controller**: `src/app/presentation/http/controllers/account/me.py`
- **Domain Entity**: `src/app/domain/user/entities/user.py`
- **Application Interactor**: `src/app/application/commands/auth/privy_login.py`
- **Related Modules**: 
  - Dashboard (next step after auth)
  - Settings (profile management)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.
