# FRONTEND_METRICS

## Metrics & Analytics Module

**User Type:** Authenticated User + Admin  
**Module:** Metrics - Event Tracking & Analytics  
**Route:** `/metrics`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Metrics & Analytics** - User Activity Tracking & Analytics

### Description
Comprehensive event tracking system for monitoring user activity, analyzing behavior patterns, and generating insights across the platform.

### Key Capabilities
- ✅ Event tracking (user & system)
- ✅ Activity analytics
- ✅ User metrics summary
- ✅ Platform-wide analytics (admin)
- ✅ Multi-device tracking
- ✅ Session management

---

## 🔌 API Integration

### 1. Track Event

```typescript
// POST /api/v1/metrics/track
// Description: Track a user event for analytics
// Authentication: Required (Bearer token)

interface TrackEventRequest {
  event_type: string;
  event_category?: string;
  properties?: Record<string, any>;
  device_type?: 'mobile' | 'desktop' | 'tablet';
  platform?: 'ios' | 'android' | 'web';
  app_version?: string;
  session_id?: string;
}

interface TrackEventResponse {
  success: boolean;
  event_id: number;
  message: string;
}

const trackEvent = async (event: TrackEventRequest): Promise<TrackEventResponse> => {
  const response = await api.post('/api/v1/metrics/track', event, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Request:
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

// Example Response (201 Created):
{
  "success": true,
  "event_id": 12345,
  "message": "Event tracked successfully"
}
```

### 2. Get Event Types

```typescript
// GET /api/v1/metrics/event-types
// Description: Get list of available event types
// Authentication: None (public)

interface EventTypesResponse {
  auth: string[];
  navigation: string[];
  trading: string[];
  earn: string[];
  save: string[];
  perpetuals: string[];
  ai: string[];
  subscription: string[];
  error: string[];
}

const getEventTypes = async (): Promise<EventTypesResponse> => {
  const response = await api.get('/api/v1/metrics/event-types');
  return response.data;
};

// Example Response (200 OK):
{
  "auth": ["login", "logout", "signup", "wallet_connected", "wallet_disconnected"],
  "navigation": ["page_view", "screen_view"],
  "trading": ["swap_initiated", "swap_completed", "swap_failed"],
  "earn": ["earn_deposit_initiated", "earn_deposit_completed", "earn_withdraw_initiated", "earn_withdraw_completed"],
  "save": ["save_schedule_created", "save_schedule_paused", "save_execution"],
  "perpetuals": ["perp_position_opened", "perp_position_closed", "perp_order_placed"],
  "ai": ["ai_chat_started", "ai_message_sent"],
  "subscription": ["subscription_started", "subscription_cancelled", "subscription_upgraded"],
  "error": ["error_occurred"]
}
```

### 3. Get My Metrics

```typescript
// GET /api/v1/metrics/me
// Description: Get metrics summary for authenticated user
// Authentication: Required (Bearer token)

interface UserMetricsSummaryResponse {
  user_id: number;
  total_events: number;
  first_event_at: string | null;
  last_event_at: string | null;
  events_by_category: Record<string, number>;
  events_by_type: Record<string, number>;
  devices_used: string[];
  platforms_used: string[];
}

const getMyMetrics = async (): Promise<UserMetricsSummaryResponse> => {
  const response = await api.get('/api/v1/metrics/me', {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "user_id": 123,
  "total_events": 1523,
  "first_event_at": "2025-01-01T10:00:00Z",
  "last_event_at": "2025-12-01T15:30:00Z",
  "events_by_category": {
    "auth": 45,
    "trading": 856,
    "earn": 234,
    "ai": 388
  },
  "events_by_type": {
    "swap_completed": 654,
    "ai_message_sent": 388,
    "earn_deposit_completed": 120
  },
  "devices_used": ["mobile", "desktop"],
  "platforms_used": ["ios", "web"]
}
```

### 4. Get My Events

```typescript
// GET /api/v1/metrics/me/events
// Description: Get list of tracked events with filters
// Authentication: Required (Bearer token)

interface GetMyEventsParams {
  event_type?: string;
  event_category?: string;
  limit?: number; // Default: 50, max: 100
  offset?: number; // Default: 0
}

interface EventListResponse {
  events: Array<{
    id: number;
    user_id: number;
    event_type: string;
    event_category: string;
    properties: Record<string, any>;
    device_type: string;
    platform: string;
    created_at: string;
  }>;
  total: number;
  limit: number;
  offset: number;
}

const getMyEvents = async (params: GetMyEventsParams = {}): Promise<EventListResponse> => {
  const response = await api.get('/api/v1/metrics/me/events', {
    params,
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 5. Get Platform Metrics (Admin)

```typescript
// GET /api/v1/metrics/admin/summary
// Description: Get platform-wide metrics (admin only)
// Authentication: Required (Bearer token + Admin role)

interface PlatformMetricsParams {
  days?: number; // Default: 7, min: 1, max: 90
}

interface PlatformMetricsResponse {
  period_days: number;
  total_events: number;
  active_users: number;
  from_date: string;
  to_date: string;
}

const getPlatformMetrics = async (
  params: PlatformMetricsParams = { days: 7 }
): Promise<PlatformMetricsResponse> => {
  const response = await api.get('/api/v1/metrics/admin/summary', {
    params,
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

---

## 🔗 React Hooks

```typescript
export function useTrackEvent() {
  return useMutation({
    mutationFn: trackEvent,
  });
}

export function useEventTypes() {
  return useQuery({
    queryKey: ['metrics', 'event-types'],
    queryFn: getEventTypes,
    staleTime: Infinity, // Event types rarely change
  });
}

export function useMyMetrics() {
  return useQuery({
    queryKey: ['metrics', 'me'],
    queryFn: getMyMetrics,
    staleTime: 60000, // 1 minute
  });
}

export function useMyEvents(params: GetMyEventsParams = {}) {
  return useQuery({
    queryKey: ['metrics', 'me', 'events', params],
    queryFn: () => getMyEvents(params),
  });
}

export function usePlatformMetrics(days: number = 7) {
  return useQuery({
    queryKey: ['metrics', 'admin', 'summary', days],
    queryFn: () => getPlatformMetrics({ days }),
  });
}
```

---

## 🎯 Event Tracking Helper

```typescript
// Create a tracking utility
export class Analytics {
  private trackEvent = useTrackEvent();
  
  // Track page view
  trackPageView(pageName: string, properties?: Record<string, any>) {
    this.trackEvent.mutate({
      event_type: 'page_view',
      event_category: 'navigation',
      properties: { page_name: pageName, ...properties },
    });
  }
  
  // Track swap
  trackSwap(fromToken: string, toToken: string, amount: string, success: boolean) {
    this.trackEvent.mutate({
      event_type: success ? 'swap_completed' : 'swap_failed',
      event_category: 'trading',
      properties: { from_token: fromToken, to_token: toToken, amount },
    });
  }
  
  // Track AI interaction
  trackAIMessage(conversationId: string, messageLength: number) {
    this.trackEvent.mutate({
      event_type: 'ai_message_sent',
      event_category: 'ai',
      properties: { conversation_id: conversationId, message_length: messageLength },
    });
  }
}

// Usage
const analytics = new Analytics();
analytics.trackPageView('/dashboard');
analytics.trackSwap('ETH', 'USDC', '1.5', true);
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Metrics & Analytics*  
*Backend Status: ✅ 100% Implemented (5 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
