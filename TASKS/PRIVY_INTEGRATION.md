# Privy Integration Guide for Frontend

## Overview

Anvil uses **Privy** for user authentication, supporting:
- **Wallet connections**: MetaMask, WalletConnect, Coinbase Wallet, etc.
- **Social logins**: Google, Apple, Twitter, Discord
- **Email**: Traditional email authentication via Privy

This guide explains how the frontend should integrate with Privy and the Anvil backend.

---

## Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │     │    Privy    │     │   Backend   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │  1. User clicks   │                   │
       │     "Connect"     │                   │
       │──────────────────>│                   │
       │                   │                   │
       │  2. Privy handles │                   │
       │     auth flow     │                   │
       │<──────────────────│                   │
       │                   │                   │
       │  3. Receive Privy │                   │
       │     user data     │                   │
       │<──────────────────│                   │
       │                   │                   │
       │  4. POST /api/v1/account/privy-login  │
       │──────────────────────────────────────>│
       │                   │                   │
       │  5. Backend creates/finds user,       │
       │     returns JWT tokens                │
       │<──────────────────────────────────────│
       │                   │                   │
       │  6. Store JWT tokens locally          │
       │                   │                   │
       │  7. Use JWT for all API calls         │
       │──────────────────────────────────────>│
```

---

## Frontend Implementation

### 1. Install Privy SDK

```bash
Ya esta listo ✅
```

### 2. Configure Privy Provider

```tsx
// 
import { PrivyProvider } from '@privy-io/react-auth';

function App({ children }) {
  return (
    <PrivyProvider
      appId="YOUR_PRIVY_APP_ID"
      config={{
        loginMethods: ['wallet', 'email', 'google', 'apple', 'twitter', 'discord'],
        appearance: {
          theme: 'dark',
          accentColor: '#your-brand-color',
        },
        embeddedWallets: {
          createOnLogin: 'users-without-wallets',
        },
      }}
    >
      {children}
    </PrivyProvider>
  );
}
```

### 3. Authentication Hook

```tsx
// hooks/useAnvilAuth.ts
import { usePrivy, useWallets } from '@privy-io/react-auth';
import { useState, useCallback } from 'react';

interface AnvilAuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
  email: string;
  is_new_user: boolean;
}

export function useAnvilAuth() {
  const { login, logout, authenticated, user, ready } = usePrivy();
  const { wallets } = useWallets();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authenticateWithBackend = useCallback(async () => {
    if (!user) return null;

    setIsLoading(true);
    setError(null);

    try {
      // Get primary wallet address if available
      const primaryWallet = wallets.find(w => w.walletClientType !== 'privy');
      
      const response = await fetch('/api/v1/account/privy-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          privy_user_id: user.id, // e.g., "did:privy:abc123"
          email: user.email?.address || null,
          wallet_address: primaryWallet?.address || null,
          auth_provider: getAuthProvider(user),
          first_name: user.google?.name?.split(' ')[0] || null,
          last_name: user.google?.name?.split(' ').slice(1).join(' ') || null,
        }),
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data: AnvilAuthResponse = await response.json();
      
      // Store tokens
      localStorage.setItem('anvil_access_token', data.access_token);
      localStorage.setItem('anvil_refresh_token', data.refresh_token);
      
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [user, wallets]);

  const handleLogin = useCallback(async () => {
    await login();
    // After Privy login, authenticate with backend
    // This is typically done in a useEffect watching the `authenticated` state
  }, [login]);

  const handleLogout = useCallback(async () => {
    localStorage.removeItem('anvil_access_token');
    localStorage.removeItem('anvil_refresh_token');
    await logout();
  }, [logout]);

  return {
    login: handleLogin,
    logout: handleLogout,
    authenticateWithBackend,
    isAuthenticated: authenticated,
    isReady: ready,
    isLoading,
    error,
    user,
    wallets,
  };
}

function getAuthProvider(user: any): string {
  if (user.wallet) return 'wallet';
  if (user.google) return 'google';
  if (user.apple) return 'apple';
  if (user.twitter) return 'twitter';
  if (user.discord) return 'discord';
  if (user.email) return 'email';
  return 'privy';
}
```

### 4. Auth Context Provider

```tsx
// contexts/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';
import { usePrivy } from '@privy-io/react-auth';
import { useAnvilAuth } from '../hooks/useAnvilAuth';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: any;
  accessToken: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }) {
  const { authenticated, ready } = usePrivy();
  const { authenticateWithBackend, login, logout, user } = useAnvilAuth();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (ready && authenticated && user) {
      // User just authenticated with Privy, now authenticate with backend
      authenticateWithBackend().then((response) => {
        if (response) {
          setAccessToken(response.access_token);
        }
        setIsLoading(false);
      });
    } else if (ready) {
      // Check for existing token
      const storedToken = localStorage.getItem('anvil_access_token');
      setAccessToken(storedToken);
      setIsLoading(false);
    }
  }, [ready, authenticated, user, authenticateWithBackend]);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!accessToken,
        isLoading,
        user,
        accessToken,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
```

### 5. API Client with Auth

```tsx
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const accessToken = localStorage.getItem('anvil_access_token');
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      ...options.headers,
    },
  });

  if (response.status === 401) {
    // Token expired, try to refresh
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry the request
      return apiRequest(endpoint, options);
    }
    // Refresh failed, redirect to login
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

async function refreshToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem('anvil_refresh_token');
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/account/refresh-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) return false;

    const data = await response.json();
    localStorage.setItem('anvil_access_token', data.access_token);
    return true;
  } catch {
    return false;
  }
}
```

---

## Backend API Endpoints

### Authentication

#### POST `/api/v1/account/privy-login`

Authenticate a user via Privy. Creates a new user if one doesn't exist.

**Request:**
```json
{
  "privy_user_id": "did:privy:abc123xyz",
  "email": "user@example.com",
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "auth_provider": "wallet",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 123,
  "email": "user@example.com",
  "is_new_user": false
}
```

### Metrics/Analytics

#### POST `/api/v1/metrics/track`

Track a user event for analytics.

**Request:**
```json
{
  "event_type": "swap_completed",
  "event_category": "trading",
  "properties": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.5",
    "chain": "ethereum"
  },
  "device_type": "mobile",
  "platform": "ios",
  "app_version": "1.0.0",
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "event_id": 456,
  "message": "Event tracked successfully"
}
```

#### GET `/api/v1/metrics/event-types`

Get available event types.

**Response:**
```json
{
  "auth": ["login", "logout", "signup", "wallet_connected", "wallet_disconnected"],
  "trading": ["swap_initiated", "swap_completed", "swap_failed"],
  "earn": ["earn_deposit_initiated", "earn_deposit_completed", ...],
  ...
}
```

#### GET `/api/v1/metrics/me`

Get your metrics summary.

**Response:**
```json
{
  "user_id": 123,
  "total_events": 150,
  "first_event_at": "2025-01-01T00:00:00Z",
  "last_event_at": "2025-11-26T12:00:00Z",
  "events_by_category": {
    "trading": 80,
    "auth": 20,
    "navigation": 50
  },
  "events_by_type": {
    "swap_completed": 40,
    "page_view": 50,
    ...
  },
  "devices_used": ["mobile", "desktop"],
  "platforms_used": ["ios", "web"]
}
```

---

## Event Tracking Best Practices

### When to Track Events

```tsx
// Example: Track swap completion
async function executeSwap(params: SwapParams) {
  // Track initiation
  await trackEvent({
    event_type: 'swap_initiated',
    event_category: 'trading',
    properties: {
      from_token: params.fromToken,
      to_token: params.toToken,
      amount: params.amount,
    },
  });

  try {
    const result = await performSwap(params);
    
    // Track success
    await trackEvent({
      event_type: 'swap_completed',
      event_category: 'trading',
      properties: {
        from_token: params.fromToken,
        to_token: params.toToken,
        amount: params.amount,
        tx_hash: result.txHash,
      },
    });
    
    return result;
  } catch (error) {
    // Track failure
    await trackEvent({
      event_type: 'swap_failed',
      event_category: 'trading',
      properties: {
        from_token: params.fromToken,
        to_token: params.toToken,
        amount: params.amount,
        error: error.message,
      },
    });
    throw error;
  }
}
```

### Tracking Hook

```tsx
// hooks/useTracking.ts
import { useCallback } from 'react';
import { apiRequest } from '../lib/api';

interface TrackEventParams {
  event_type: string;
  event_category?: string;
  properties?: Record<string, any>;
}

export function useTracking() {
  const trackEvent = useCallback(async (params: TrackEventParams) => {
    try {
      await apiRequest('/api/v1/metrics/track', {
        method: 'POST',
        body: JSON.stringify({
          ...params,
          device_type: getDeviceType(),
          platform: getPlatform(),
          app_version: process.env.NEXT_PUBLIC_APP_VERSION,
          session_id: getSessionId(),
        }),
      });
    } catch (error) {
      // Don't throw - tracking should not break the app
      console.error('Failed to track event:', error);
    }
  }, []);

  return { trackEvent };
}

function getDeviceType(): string {
  const ua = navigator.userAgent;
  if (/tablet|ipad/i.test(ua)) return 'tablet';
  if (/mobile|iphone|android/i.test(ua)) return 'mobile';
  return 'desktop';
}

function getPlatform(): string {
  const ua = navigator.userAgent;
  if (/iphone|ipad/i.test(ua)) return 'ios';
  if (/android/i.test(ua)) return 'android';
  return 'web';
}

function getSessionId(): string {
  let sessionId = sessionStorage.getItem('anvil_session_id');
  if (!sessionId) {
    sessionId = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('anvil_session_id', sessionId);
  }
  return sessionId;
}
```

---

## Database Schema

### Users Table (Extended)

| Column | Type | Description |
|--------|------|-------------|
| `privy_user_id` | VARCHAR(255) | Unique Privy user ID (e.g., `did:privy:xxx`) |
| `primary_wallet_address` | VARCHAR(255) | User's primary wallet address |
| `auth_provider` | VARCHAR(50) | How user authenticated: `privy`, `wallet`, `google`, `apple`, etc. |
| `password` | VARCHAR(255) | **Nullable** - Only for email/password users |

### User Events Table (New)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Foreign key to users |
| `event_type` | VARCHAR(100) | Event type (e.g., `swap_completed`) |
| `event_category` | VARCHAR(50) | Category (e.g., `trading`) |
| `properties` | JSONB | Event-specific data |
| `device_type` | VARCHAR(50) | `mobile`, `desktop`, `tablet` |
| `platform` | VARCHAR(50) | `ios`, `android`, `web` |
| `app_version` | VARCHAR(20) | App version |
| `session_id` | VARCHAR(255) | Session identifier |
| `ip_address` | VARCHAR(50) | Client IP |
| `country_code` | VARCHAR(10) | Country code |
| `created_at` | TIMESTAMP | Event timestamp |

---

## Next Steps for Frontend

1. **Install Privy SDK** and configure with your Privy App ID
2. **Implement auth hooks** as shown above
3. **Create auth context** to manage global auth state
4. **Set up API client** with automatic token handling
5. **Implement event tracking** for key user actions
6. **Test the flow**:
   - Connect wallet → Backend creates user → JWT returned
   - Use JWT for all subsequent API calls
   - Track important events

## Support

For questions about:
- **Privy SDK**: https://docs.privy.io
- **Backend API**: Check the OpenAPI docs at `/docs` or `/redoc`

