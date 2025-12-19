# FRONTEND_USER_ACCOUNT_AUTH

## User Account & Authentication Module

**User Type:** Public (Signup/Login) + Authenticated User (Profile, Logout)  
**Module:** Account & Authentication - User Lifecycle Management  
**Route:** `/auth`, `/account`, `/profile`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Account & Authentication** - Complete User Lifecycle from Signup to Profile Management

### Description
Comprehensive authentication and account management system providing user registration, login, profile management, password operations, email verification, and session management with JWT-based authentication.

### Key Capabilities
- ✅ User registration (signup) with validation
- ✅ Email/password login
- ✅ Privy integration (Web3 login)
- ✅ Profile management (view/update)
- ✅ Password management (change, reset)
- ✅ Email verification
- ✅ Session management (logout, refresh token)
- ✅ JWT-based authentication
- ✅ Multi-device session support

---

## 🔌 API Integration

### 1. User Signup

```typescript
// POST /api/v1/account/signup
// Description: Register a new user account
// Authentication: None (Public endpoint)
// Rate Limit: 5 requests per hour per IP
//
// Path Parameters: None
//
// Query Parameters: None
//
// Request Body:
interface SignUpRequest {
  email: string; // Valid email address
  first_name: string; // 1-50 characters
  last_name: string; // 1-50 characters
  password: string; // Min 8 characters, must include uppercase, lowercase, number
  country_id?: number; // Optional country ID
  city_id?: number; // Optional city ID  
  language?: string; // Optional preferred language (en, es, fr, etc.)
}

// Response:
interface SignUpResponse {
  id: number;
  session_id: string;
  user_id: number;
  expires_at: string; // ISO 8601 timestamp
  access_token: string; // JWT access token
  refresh_token: string; // JWT refresh token
  token_type: string; // "Bearer"
  is_active: boolean;
}

// TypeScript Implementation:
const signup = async (data: SignUpRequest): Promise<SignUpResponse> => {
  const response = await api.post('/api/v1/account/signup', data);
  return response.data;
};

// Example Request:
{
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Johnson",
  "password": "SecurePass123!",
  "country_id": 1,
  "city_id": 100,
  "language": "en"
}

// Example Response (201 Created):
{
  "id": 12345,
  "session_id": "sess_550e8400e29b41d4a716446655440000",
  "user_id": 12345,
  "expires_at": "2025-12-02T10:30:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "is_active": true
}

// Example Error Response (409 Conflict - Email exists):
{
  "error": {
    "code": "EMAIL_ALREADY_EXISTS",
    "message": "An account with this email already exists",
    "details": {
      "email": "alice@example.com"
    }
  }
}

// Example Error Response (400 Bad Request - Invalid password):
{
  "error": {
    "code": "INVALID_PASSWORD",
    "message": "Password must be at least 8 characters and include uppercase, lowercase, and number",
    "details": {
      "field": "password",
      "requirements": ["min_length_8", "uppercase", "lowercase", "number"]
    }
  }
}
```

---

### 2. User Login

```typescript
// POST /api/v1/account/login
// Description: Authenticate user with email and password
// Authentication: None (Public endpoint)
// Rate Limit: 10 requests per 15 minutes per IP
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface LogInRequest {
  email: string;
  password: string;
}

// Response:
interface LogInResponse {
  session_id: string;
  user_id: number;
  expires_at: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

const login = async (credentials: LogInRequest): Promise<LogInResponse> => {
  const response = await api.post('/api/v1/account/login', credentials);
  
  // Store tokens
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  
  return response.data;
};

// Example Request:
{
  "email": "alice@example.com",
  "password": "SecurePass123!"
}

// Example Response (200 OK):
{
  "session_id": "sess_660e8400e29b41d4a716446655440000",
  "user_id": 12345,
  "expires_at": "2025-12-02T10:30:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}

// Example Error Response (401 Unauthorized - Invalid credentials):
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "details": {}
  }
}

// Example Error Response (404 Not Found - User not found):
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "No account found with this email",
    "details": {
      "email": "notfound@example.com"
    }
  }
}
```

---

### 3. Get Current User Profile

```typescript
// GET /api/v1/account/me
// Description: Get current authenticated user's profile information
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface MeResponse {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_admin: boolean;
  is_super_admin: boolean;
  email_verified: boolean;
  country_id: number | null;
  city_id: number | null;
  language: string;
  created_at: string;
  updated_at: string;
}

const getCurrentUser = async (): Promise<MeResponse> => {
  const response = await api.get('/api/v1/account/me', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "id": 12345,
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Johnson",
  "is_active": true,
  "is_admin": false,
  "is_super_admin": false,
  "email_verified": true,
  "country_id": 1,
  "city_id": 100,
  "language": "en",
  "created_at": "2025-11-01T08:00:00Z",
  "updated_at": "2025-12-01T10:30:00Z"
}

// Example Error Response (401 Unauthorized):
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Valid authentication token required",
    "details": {}
  }
}
```

---

### 4. Update User Profile

```typescript
// PUT /api/v1/account/me
// Description: Update current user's profile information
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface UpdateMeRequest {
  first_name?: string; // 1-50 characters
  last_name?: string; // 1-50 characters
  country_id?: number;
  city_id?: number;
  language?: string;
}

// Response:
interface MeResponse {
  // Same as GET /api/v1/account/me
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  // ... other fields
}

const updateProfile = async (updates: UpdateMeRequest): Promise<MeResponse> => {
  const response = await api.put('/api/v1/account/me', updates, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "first_name": "Alicia",
  "language": "es"
}

// Example Response (200 OK):
{
  "id": 12345,
  "email": "alice@example.com",
  "first_name": "Alicia",
  "last_name": "Johnson",
  "language": "es",
  "updated_at": "2025-12-01T11:00:00Z"
}
```

---

### 5. Logout

```typescript
// DELETE /api/v1/account/logout
// Description: Terminate current user session and invalidate tokens
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface LogoutResponse {
  success: boolean;
  message: string;
}

const logout = async (): Promise<void> => {
  await api.delete('/api/v1/account/logout', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  
  // Clear local tokens
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// Example Response (200 OK):
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### 6. Refresh Access Token

```typescript
// POST /api/v1/account/refresh-token
// Description: Refresh expired access token using refresh token
// Authentication: Required (Refresh token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface RefreshTokenRequest {
  refresh_token: string;
}

// Response:
interface RefreshTokenResponse {
  access_token: string;
  expires_at: string;
  token_type: string;
}

const refreshAccessToken = async (): Promise<RefreshTokenResponse> => {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await api.post('/api/v1/account/refresh-token', {
    refresh_token: refreshToken
  });
  
  // Update stored access token
  localStorage.setItem('access_token', response.data.access_token);
  
  return response.data;
};

// Example Request:
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

// Example Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-12-02T12:00:00Z",
  "token_type": "Bearer"
}

// Example Error Response (401 Unauthorized - Invalid refresh token):
{
  "error": {
    "code": "INVALID_REFRESH_TOKEN",
    "message": "Refresh token is invalid or expired",
    "details": {}
  }
}
```

---

### 7. Change Password

```typescript
// PUT /api/v1/account/password
// Description: Change current user's password
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface ChangePasswordRequest {
  current_password: string;
  new_password: string; // Min 8 chars, uppercase, lowercase, number
}

// Response:
interface ChangePasswordResponse {
  success: boolean;
  message: string;
}

const changePassword = async (
  passwords: ChangePasswordRequest
): Promise<ChangePasswordResponse> => {
  const response = await api.put('/api/v1/account/password', passwords, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}

// Example Response (200 OK):
{
  "success": true,
  "message": "Password changed successfully"
}

// Example Error Response (401 Unauthorized - Wrong current password):
{
  "error": {
    "code": "INVALID_CURRENT_PASSWORD",
    "message": "Current password is incorrect",
    "details": {}
  }
}
```

---

### 8. Request Password Reset

```typescript
// POST /api/v1/account/password-reset/request
// Description: Request password reset email with reset token
// Authentication: None (Public endpoint)
// Rate Limit: 3 requests per hour per email
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface PasswordResetRequest {
  email: string;
}

// Response:
interface PasswordResetResponse {
  success: boolean;
  message: string;
  email_sent: boolean;
}

const requestPasswordReset = async (
  email: string
): Promise<PasswordResetResponse> => {
  const response = await api.post('/api/v1/account/password-reset/request', {
    email
  });
  return response.data;
};

// Example Request:
{
  "email": "alice@example.com"
}

// Example Response (200 OK):
{
  "success": true,
  "message": "If an account with this email exists, a password reset link has been sent",
  "email_sent": true
}

// Note: Always returns success to prevent email enumeration attacks
```

---

### 9. Confirm Password Reset

```typescript
// POST /api/v1/account/password-reset/confirm
// Description: Reset password using token from email
// Authentication: None (Token-based)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface PasswordResetConfirmRequest {
  token: string; // Reset token from email
  new_password: string; // Min 8 chars, uppercase, lowercase, number
}

// Response:
interface PasswordResetConfirmResponse {
  success: boolean;
  message: string;
}

const confirmPasswordReset = async (
  token: string,
  newPassword: string
): Promise<PasswordResetConfirmResponse> => {
  const response = await api.post('/api/v1/account/password-reset/confirm', {
    token,
    new_password: newPassword
  });
  return response.data;
};

// Example Request:
{
  "token": "reset_tok_550e8400e29b41d4a716446655440000",
  "new_password": "NewSecurePass456!"
}

// Example Response (200 OK):
{
  "success": true,
  "message": "Password reset successfully"
}

// Example Error Response (400 Bad Request - Expired token):
{
  "error": {
    "code": "RESET_TOKEN_EXPIRED",
    "message": "Password reset token has expired. Please request a new one.",
    "details": {
      "token_expires_at": "2025-12-01T10:00:00Z"
    }
  }
}
```

---

### 10. Send Email Verification

```typescript
// POST /api/v1/account/email-verification/send
// Description: Send email verification link to user's email
// Authentication: Required (Bearer token)
// Rate Limit: 3 requests per hour
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface EmailVerificationSendResponse {
  success: boolean;
  message: string;
  email: string;
  expires_at: string;
}

const sendEmailVerification = async (): Promise<EmailVerificationSendResponse> => {
  const response = await api.post('/api/v1/account/email-verification/send', {}, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "success": true,
  "message": "Verification email sent successfully",
  "email": "alice@example.com",
  "expires_at": "2025-12-01T11:30:00Z"
}
```

---

### 11. Verify Email

```typescript
// PUT /api/v1/account/email-verification
// Description: Verify user's email using token from email link
// Authentication: Required (Bearer token) OR Token parameter
//
// Path Parameters: None
//
// Query Parameters:
//   - token: string - Verification token from email link
//
// Request Body: None (token in query param)

// Response:
interface EmailVerificationResponse {
  success: boolean;
  message: string;
  email_verified: boolean;
}

const verifyEmail = async (token: string): Promise<EmailVerificationResponse> => {
  const response = await api.put(`/api/v1/account/email-verification?token=${token}`);
  return response.data;
};

// Example Request:
// GET /api/v1/account/email-verification?token=verify_tok_550e8400e29b41d4a716

// Example Response (200 OK):
{
  "success": true,
  "message": "Email verified successfully",
  "email_verified": true
}

// Example Error Response (400 Bad Request - Invalid token):
{
  "error": {
    "code": "INVALID_VERIFICATION_TOKEN",
    "message": "Email verification token is invalid or expired",
    "details": {}
  }
}
```

---

### 12. Privy Login (Web3)

```typescript
// POST /api/v1/account/privy-login
// Description: Authenticate user via Privy (Web3 wallet, social, etc.)
// Authentication: None (Privy token-based)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface PrivyLoginRequest {
  privy_token: string; // Token from Privy SDK
  wallet_address?: string; // Optional wallet address
}

// Response:
interface PrivyLoginResponse {
  session_id: string;
  user_id: number;
  access_token: string;
  refresh_token: string;
  is_new_user: boolean; // True if user was created during login
}

const loginWithPrivy = async (
  privyToken: string,
  walletAddress?: string
): Promise<PrivyLoginResponse> => {
  const response = await api.post('/api/v1/account/privy-login', {
    privy_token: privyToken,
    wallet_address: walletAddress
  });
  
  // Store tokens
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  
  return response.data;
};

// Example Request:
{
  "privy_token": "privy_tok_abc123def456...",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}

// Example Response (200 OK - Existing user):
{
  "session_id": "sess_770e8400e29b41d4a716446655440000",
  "user_id": 12345,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "is_new_user": false
}

// Example Response (201 Created - New user):
{
  "session_id": "sess_880e8400e29b41d4a716446655440000",
  "user_id": 67890,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "is_new_user": true
}
```

---

## 🔗 React Hooks

### useAuth Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useAuth() {
  const queryClient = useQueryClient();
  
  const { data: user, isLoading } = useQuery({
    queryKey: ['current-user'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return null;
      
      const response = await api.get('/api/v1/account/me');
      return response.data;
    },
    retry: false,
  });
  
  const signup = useMutation({
    mutationFn: async (data: SignUpRequest) => {
      const response = await api.post('/api/v1/account/signup', data);
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      queryClient.setQueryData(['current-user'], data);
      toast.success('Account created successfully!');
    },
  });
  
  const login = useMutation({
    mutationFn: async (credentials: LogInRequest) => {
      const response = await api.post('/api/v1/account/login', credentials);
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast.success('Logged in successfully!');
    },
  });
  
  const logout = useMutation({
    mutationFn: async () => {
      await api.delete('/api/v1/account/logout');
    },
    onSuccess: () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      queryClient.setQueryData(['current-user'], null);
      toast.success('Logged out successfully');
    },
  });
  
  const updateProfile = useMutation({
    mutationFn: async (updates: UpdateMeRequest) => {
      const response = await api.put('/api/v1/account/me', updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast.success('Profile updated successfully');
    },
  });
  
  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    signup: signup.mutate,
    login: login.mutate,
    logout: logout.mutate,
    updateProfile: updateProfile.mutate,
  };
}
```

---

## 🎭 User Flows

### Flow 1: New User Signup

```
1. User opens app/website
   ↓
2. Taps "Sign Up"
   ↓
3. Fills signup form (email, name, password)
   ↓
4. Optionally selects country/city
   ↓
5. Taps "Create Account"
   ↓
6. Validation runs (client + server)
   ↓
7. POST /api/v1/account/signup
   ↓
8. Receives JWT tokens (201 Created)
   ↓
9. Tokens stored in localStorage
   ↓
10. Redirects to onboarding/dashboard
   ↓
11. Email verification sent (background)
```

### Flow 2: User Login

```
1. User opens app
   ↓
2. Taps "Log In"
   ↓
3. Enters email & password
   ↓
4. Taps "Log In"
   ↓
5. POST /api/v1/account/login
   ↓
6. Receives JWT tokens (200 OK)
   ↓
7. Tokens stored
   ↓
8. GET /api/v1/account/me (fetch profile)
   ↓
9. Redirects to dashboard
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Account & Authentication*  
*Backend Status: ✅ 100% Implemented (12 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
