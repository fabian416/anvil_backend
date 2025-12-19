# FRONTEND_USER_PAYMENT_SUBSCRIPTION

## User Payment & Subscription Module

**User Type:** Authenticated User  
**Module:** Payment & Subscription - Stripe Integration  
**Route:** `/payment`, `/subscription`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Payment & Subscription** - Stripe-Powered Subscription Management

### Description
Complete payment and subscription system integrated with Stripe for handling user subscription lifecycle, payment processing, and billing management.

### Key Capabilities
- ✅ View available subscription plans (PRO, CORPORATE)
- ✅ Subscribe to plans with Stripe Checkout
- ✅ Cancel subscriptions
- ✅ View payment history
- ✅ Manage payment methods
- ✅ Subscription success/failure handling
- ✅ Automatic billing renewal
- ✅ Webhook integration for payment events

---

## 🔌 API Integration

### 1. Get Available Subscriptions

```typescript
// GET /api/v1/subscription/
// Description: Get all available subscription plans
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface Subscription {
  id: number;
  name: string; // "PRO" | "CORPORATE"
  price_monthly: number; // USD
  price_yearly: number; // USD
  features: string[];
  stripe_price_id_monthly: string;
  stripe_price_id_yearly: string;
  is_active: boolean;
}

const getSubscriptions = async (): Promise<Subscription[]> => {
  const response = await api.get('/api/v1/subscription/', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
[
  {
    "id": 1,
    "name": "PRO",
    "price_monthly": 29.99,
    "price_yearly": 299.99,
    "features": [
      "Advanced AI Chat",
      "Portfolio Analytics",
      "Risk Alerts",
      "GraphRAG Search",
      "Priority Support"
    ],
    "stripe_price_id_monthly": "price_1234567890",
    "stripe_price_id_yearly": "price_0987654321",
    "is_active": true
  },
  {
    "id": 2,
    "name": "CORPORATE",
    "price_monthly": 99.99,
    "price_yearly": 999.99,
    "features": [
      "Everything in PRO",
      "Team Management (up to 10 users)",
      "API Access",
      "Custom Projects",
      "Dedicated Support"
    ],
    "stripe_price_id_monthly": "price_1111111111",
    "stripe_price_id_yearly": "price_2222222222",
    "is_active": true
  }
]
```

---

### 2. Create Subscription (Subscribe to Plan)

```typescript
// POST /api/v1/subscription/{subscription_id}/subscribe
// Description: Create a new subscription for current user via Stripe Checkout
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - subscription_id: number - ID of the subscription plan (1=PRO, 2=CORPORATE)
//
// Query Parameters: None
//
// Request Body: None (subscription_id in path)

// Response:
interface CreateSubscriptionResponse {
  checkout_url: string; // Stripe Checkout URL to redirect user
  subscription_id: number;
  plan_name: string;
}

const createSubscription = async (
  subscriptionId: number
): Promise<CreateSubscriptionResponse> => {
  const response = await api.post(
    `/api/v1/subscription/${subscriptionId}/subscribe`,
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Usage:
const handleSubscribe = async (planId: number) => {
  const result = await createSubscription(planId);
  // Redirect to Stripe Checkout
  window.location.href = result.checkout_url;
};

// Example Response (200 OK):
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_abc123...",
  "subscription_id": 1,
  "plan_name": "PRO"
}

// Example Error Response (404 Not Found - Invalid plan):
{
  "error": {
    "code": "SUBSCRIPTION_NOT_FOUND",
    "message": "Subscription plan with ID 99 not found",
    "details": {
      "subscription_id": 99
    }
  }
}
```

---

### 3. Cancel Subscription

```typescript
// POST /api/v1/subscription/cancel
// Description: Cancel current user's active subscription
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface CancelSubscriptionRequest {
  reason?: string; // Optional cancellation reason
  feedback?: string; // Optional user feedback
}

// Response:
interface CancelSubscriptionResponse {
  success: boolean;
  message: string;
  cancelled_at: string;
  active_until: string; // End of current billing period
}

const cancelSubscription = async (
  reason?: string
): Promise<CancelSubscriptionResponse> => {
  const response = await api.post('/api/v1/subscription/cancel', {
    reason,
  }, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "reason": "switching_to_competitor",
  "feedback": "Need more features for team management"
}

// Example Response (200 OK):
{
  "success": true,
  "message": "Subscription cancelled successfully",
  "cancelled_at": "2025-12-01T11:00:00Z",
  "active_until": "2025-12-31T23:59:59Z"
}

// Example Error Response (400 Bad Request - No active subscription):
{
  "error": {
    "code": "NO_ACTIVE_SUBSCRIPTION",
    "message": "You don't have an active subscription to cancel",
    "details": {}
  }
}
```

---

### 4. Subscription Success Callback

```typescript
// POST /api/v1/subscription/success
// Description: Handle successful subscription payment from Stripe
// Authentication: Required (Bearer token)
// Note: Typically called by Stripe redirect after successful payment
//
// Path Parameters: None
//
// Query Parameters:
//   - session_id: string - Stripe Checkout session ID
//
// Request Body: None

// Response:
interface SubscriptionSuccessResponse {
  success: boolean;
  subscription_active: boolean;
  plan_name: string;
  next_billing_date: string;
}

const handleSubscriptionSuccess = async (
  sessionId: string
): Promise<SubscriptionSuccessResponse> => {
  const response = await api.post(
    `/api/v1/subscription/success?session_id=${sessionId}`,
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Request:
// POST /api/v1/subscription/success?session_id=cs_test_abc123...

// Example Response (200 OK):
{
  "success": true,
  "subscription_active": true,
  "plan_name": "PRO",
  "next_billing_date": "2026-01-01T00:00:00Z"
}
```

---

### 5. Initialize Subscriptions (Admin Only)

```typescript
// POST /api/v1/subscription/init
// Description: Initialize default subscription plans (PRO, CORPORATE)
// Authentication: Required (Bearer token + Admin role)
// Note: Internal/admin endpoint for setup
//
// Path Parameters: None
// Query Parameters: None
// Request Body: None

// Response:
interface InitSubscriptionsResponse {
  plans_created: number;
  plans: Subscription[];
}

const initializeSubscriptions = async (): Promise<InitSubscriptionsResponse> => {
  const response = await api.post('/api/v1/subscription/init', {}, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "plans_created": 2,
  "plans": [
    {
      "id": 1,
      "name": "PRO",
      "price_monthly": 29.99,
      "price_yearly": 299.99
    },
    {
      "id": 2,
      "name": "CORPORATE",
      "price_monthly": 99.99,
      "price_yearly": 999.99
    }
  ]
}
```

---

### 6. Get User Payment History

```typescript
// GET /api/v1/payments/user?page=1&per_page=10
// Description: Get paginated list of user's payment transactions
// Authentication: Required (Bearer token)
//
// Path Parameters: None
//
// Query Parameters:
//   - page: number - Page number (default: 1, min: 1)
//   - per_page: number - Items per page (default: 10, max: 100)

// Response:
interface PaymentHistoryResponse {
  items: Payment[];
  page: number;
  per_page: number;
  total: number;
}

interface Payment {
  id: number;
  user_id: number;
  subscription_id: number;
  subscription_name: string;
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  stripe_payment_id: string;
  created_at: string;
  paid_at: string | null;
}

const getUserPayments = async (
  page: number = 1,
  perPage: number = 10
): Promise<PaymentHistoryResponse> => {
  const response = await api.get('/api/v1/payments/user', {
    params: { page, per_page: perPage },
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/payments/user?page=1&per_page=5

// Example Response (200 OK):
{
  "items": [
    {
      "id": 501,
      "user_id": 12345,
      "subscription_id": 1,
      "subscription_name": "PRO",
      "amount": 29.99,
      "currency": "USD",
      "status": "completed",
      "stripe_payment_id": "pi_1234567890",
      "created_at": "2025-12-01T10:00:00Z",
      "paid_at": "2025-12-01T10:00:15Z"
    },
    {
      "id": 450,
      "user_id": 12345,
      "subscription_id": 1,
      "subscription_name": "PRO",
      "amount": 29.99,
      "currency": "USD",
      "status": "completed",
      "stripe_payment_id": "pi_0987654321",
      "created_at": "2025-11-01T10:00:00Z",
      "paid_at": "2025-11-01T10:00:12Z"
    }
  ],
  "page": 1,
  "per_page": 5,
  "total": 12
}
```

---

### 7. Create Payment Transaction

```typescript
// POST /api/v1/payments/transaction
// Description: Create a new payment transaction
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface CreatePaymentRequest {
  amount: number; // Payment amount in specified currency
  currency: string; // "USD", "EUR", etc.
  description: string; // Payment description/memo
}

// Response:
interface CreatePaymentResponse {
  status: string;
  payment: {
    id: number;
    amount: number;
    currency: string;
    status: string;
  };
}

const createPayment = async (
  payment: CreatePaymentRequest
): Promise<CreatePaymentResponse> => {
  const response = await api.post('/api/v1/payments/transaction', payment, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "amount": 29.99,
  "currency": "USD",
  "description": "PRO Plan - Monthly subscription"
}

// Example Response (200 OK):
{
  "status": "success",
  "payment": {
    "id": 502,
    "amount": 29.99,
    "currency": "USD",
    "status": "pending"
  }
}
```

---

## 🔗 React Hooks

### useSubscription Hook

```typescript
export function useSubscription() {
  const queryClient = useQueryClient();
  
  const { data: plans, isLoading } = useQuery({
    queryKey: ['subscription-plans'],
    queryFn: async () => {
      const response = await api.get('/api/v1/subscription/');
      return response.data;
    },
  });
  
  const subscribe = useMutation({
    mutationFn: async (planId: number) => {
      const response = await api.post(`/api/v1/subscription/${planId}/subscribe`);
      return response.data;
    },
    onSuccess: (data) => {
      // Redirect to Stripe Checkout
      window.location.href = data.checkout_url;
    },
  });
  
  const cancelSubscription = useMutation({
    mutationFn: async (reason?: string) => {
      const response = await api.post('/api/v1/subscription/cancel', { reason });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast.success('Subscription cancelled successfully');
    },
  });
  
  return {
    plans: plans || [],
    isLoading,
    subscribe: subscribe.mutate,
    cancelSubscription: cancelSubscription.mutate,
  };
}
```

### usePaymentHistory Hook

```typescript
export function usePaymentHistory(page: number = 1, perPage: number = 10) {
  const { data, isLoading } = useQuery({
    queryKey: ['payment-history', page, perPage],
    queryFn: async () => {
      const response = await api.get('/api/v1/payments/user', {
        params: { page, per_page: perPage }
      });
      return response.data;
    },
  });
  
  return {
    payments: data?.items || [],
    page: data?.page || 1,
    perPage: data?.per_page || 10,
    total: data?.total || 0,
    isLoading,
  };
}
```

---

## 🎭 User Flows

### Flow 1: Subscribe to PRO Plan

```
1. User navigates to Subscription/Pricing page
   ↓
2. Views available plans (PRO, CORPORATE)
   ↓
3. Taps "Subscribe to PRO"
   ↓
4. POST /api/v1/subscription/1/subscribe
   ↓
5. Receives Stripe Checkout URL
   ↓
6. Redirects to Stripe Checkout page
   ↓
7. User enters payment details on Stripe
   ↓
8. Stripe processes payment
   ↓
9. Redirects back to app with session_id
   ↓
10. POST /api/v1/subscription/success?session_id={id}
   ↓
11. Subscription activated
   ↓
12. Shows success message & updated features
```

### Flow 2: Cancel Subscription

```
1. User navigates to Settings > Subscription
   ↓
2. Views current subscription details
   ↓
3. Taps "Cancel Subscription"
   ↓
4. Confirmation modal appears
   ↓
5. Selects cancellation reason (optional)
   ↓
6. Confirms cancellation
   ↓
7. POST /api/v1/subscription/cancel
   ↓
8. Subscription marked as cancelled
   ↓
9. Shows: "Active until Dec 31, 2025"
   ↓
10. Features remain active until period end
```

---

## ⚠️ Error Handling

```typescript
const subscriptionErrors = {
  SUB_001: 'Subscription plan not found',
  SUB_002: 'Already subscribed to this plan',
  SUB_003: 'No active subscription to cancel',
  SUB_004: 'Payment processing failed',
  SUB_005: 'Stripe checkout session expired',
};

// Handle subscription error
try {
  await createSubscription(planId);
} catch (error) {
  if (error.code === 'SUB_002') {
    toast.error('You are already subscribed to this plan');
  } else if (error.code === 'SUB_004') {
    toast.error('Payment failed. Please try again or contact support.');
  } else {
    toast.error('Subscription failed. Please try again.');
  }
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Payment & Subscription*  
*Backend Status: ✅ 100% Implemented (8 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
