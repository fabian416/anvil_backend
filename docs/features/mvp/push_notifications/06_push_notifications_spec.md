# Push Notifications — Implementation Specification

**Version**: 1.0  
**Date**: 2026-02-09  
**Status**: Specification  
**Context**: Mobile Push Notifications (FCM/APNs via Expo)  
**Platform**: React Native (Expo) — iOS & Android  
**Related**: Notifications Module (GET /api/v1/notifications/), Alert Subscriptions, Admin Notifications Dashboard, Celery Workers

---

## Overview

Server-initiated push notifications delivered to users' mobile devices via **Firebase Cloud Messaging (FCM)** as the unified transport layer (FCM handles both Android and iOS/APNs). The mobile app (React Native + Expo) registers a push token on startup and sends it to the backend. The backend stores device tokens, manages notification preferences, and uses **Celery** workers to dispatch notifications — both targeted (per-user) and broadcast (general). An **admin panel** controls notification campaigns, per-user send limits, and delivery analytics.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        NOTIFICATION FLOW                             │
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐             │
│  │ Trigger      │───▶│ Celery      │───▶│ FCM / APNs   │            │
│  │ Sources      │    │ Worker      │    │ Gateway      │            │
│  └─────────────┘    └─────────────┘    └──────┬───────┘            │
│       │                    │                    │                    │
│       │                    ▼                    ▼                    │
│       │            ┌─────────────┐    ┌──────────────┐             │
│       │            │ PostgreSQL  │    │ User Device   │             │
│       │            │ (log+track) │    │ (push shown)  │             │
│       │            └─────────────┘    └──────────────┘             │
│       │                                                             │
│  Sources:                                                           │
│  ├── Admin Panel (broadcast / targeted campaigns)                   │
│  ├── System Events (tx confirmed, risk alert, price alert)          │
│  ├── Scheduled (daily portfolio summary, weekly digest)             │
│  └── Chat Agent (waitlist CTA, recommendation follow-up)            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 1. Database Schema

### 1.1 `push_device_tokens` — Device Registration

Stores each device's push token. A user can have multiple devices (phone + tablet). Tokens are refreshed periodically by the OS and must be updated.

```sql
CREATE TABLE push_device_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Device identification
    device_token TEXT NOT NULL,               -- FCM/Expo push token
    device_id VARCHAR(255),                   -- Unique device fingerprint (links to auth_sessions.device_id)
    platform VARCHAR(10) NOT NULL,            -- 'ios' | 'android'
    app_version VARCHAR(20),                  -- e.g., '1.2.3'
    os_version VARCHAR(20),                   -- e.g., 'iOS 18.1' | 'Android 15'
    device_model VARCHAR(100),                -- e.g., 'iPhone 16 Pro' | 'Pixel 9'
    
    -- Token management
    token_type VARCHAR(20) DEFAULT 'fcm',     -- 'fcm' | 'expo' | 'apns'
    is_active BOOLEAN DEFAULT true,           -- Set false on unregister or token failure
    failed_count INTEGER DEFAULT 0,           -- Consecutive delivery failures
    last_failed_at TIMESTAMPTZ,               -- Last delivery failure timestamp
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,                 -- Last successful push sent to this device
    
    -- Constraints
    UNIQUE(user_id, device_token),
    INDEX idx_push_device_user (user_id, is_active),
    INDEX idx_push_device_token (device_token),
    INDEX idx_push_device_platform (platform, is_active)
);

-- Auto-deactivate devices with too many failures
-- (handled by Celery cleanup task, threshold = 5 consecutive failures)
```

### 1.2 `push_notification_preferences` — Per-User Settings

Controls what types of notifications a user receives and rate limits.

```sql
CREATE TABLE push_notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Category toggles (user-controllable)
    transactions_enabled BOOLEAN DEFAULT true,       -- Tx confirmed, failed, received
    risk_alerts_enabled BOOLEAN DEFAULT true,        -- Protocol risk changes
    price_alerts_enabled BOOLEAN DEFAULT false,      -- Token price movements
    portfolio_updates_enabled BOOLEAN DEFAULT true,  -- Daily/weekly portfolio summary
    promotions_enabled BOOLEAN DEFAULT true,         -- Marketing, announcements, features
    system_enabled BOOLEAN DEFAULT true,             -- Maintenance, security, mandatory
    chat_enabled BOOLEAN DEFAULT true,               -- Chat-related (agent recommendations, follow-ups)
    
    -- Rate limiting (admin-overridable per user)
    max_per_hour INTEGER DEFAULT 10,                 -- Max push notifications per hour
    max_per_day INTEGER DEFAULT 50,                  -- Max push notifications per day
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME DEFAULT '23:00',          -- Local time (UTC stored, converted by app)
    quiet_hours_end TIME DEFAULT '08:00',
    timezone VARCHAR(50) DEFAULT 'UTC',              -- IANA timezone for quiet hours
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id)
);
```

### 1.3 `push_notifications` — Notification Log & Delivery Tracking

Every notification sent is logged here. Used for history, analytics, and deduplication.

```sql
CREATE TABLE push_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Targeting
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- NULL for broadcast
    campaign_id UUID REFERENCES push_campaigns(id) ON DELETE SET NULL,
    
    -- Content
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    category VARCHAR(30) NOT NULL,                -- 'transaction' | 'risk_alert' | 'price_alert' | 
                                                  -- 'portfolio' | 'promotion' | 'system' | 'chat'
    priority VARCHAR(10) DEFAULT 'normal',        -- 'normal' | 'high' | 'critical'
    
    -- Rich content
    image_url TEXT,                                -- Optional rich notification image
    action_url TEXT,                               -- Deep link (e.g., 'anvil://swap/confirm/abc123')
    action_text VARCHAR(100),                      -- CTA button text
    data JSONB DEFAULT '{}',                       -- Custom payload for the app
    
    -- Delivery tracking
    status VARCHAR(20) DEFAULT 'pending',          -- 'pending' | 'queued' | 'sent' | 'delivered' | 
                                                   -- 'opened' | 'failed' | 'skipped'
    device_token_id UUID REFERENCES push_device_tokens(id) ON DELETE SET NULL,
    fcm_message_id VARCHAR(255),                   -- FCM response message ID
    failure_reason TEXT,                            -- If failed: 'invalid_token' | 'quota_exceeded' | etc.
    
    -- Timing
    scheduled_at TIMESTAMPTZ,                      -- NULL = immediate, else scheduled
    sent_at TIMESTAMPTZ,                           -- When actually dispatched to FCM
    delivered_at TIMESTAMPTZ,                       -- FCM delivery confirmation
    opened_at TIMESTAMPTZ,                         -- User tapped the notification
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_push_notif_user (user_id, created_at DESC),
    INDEX idx_push_notif_campaign (campaign_id),
    INDEX idx_push_notif_status (status, scheduled_at),
    INDEX idx_push_notif_category (category, created_at DESC)
);

-- Convert to hypertable for efficient time-series queries (delivery analytics)
SELECT create_hypertable('push_notifications', 'created_at', 
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);
```

### 1.4 `push_campaigns` — Admin-Created Notification Campaigns

Broadcast or segmented notification campaigns created by admins.

```sql
CREATE TABLE push_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Content
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    image_url TEXT,
    action_url TEXT,
    action_text VARCHAR(100),
    data JSONB DEFAULT '{}',
    category VARCHAR(30) DEFAULT 'promotion',
    priority VARCHAR(10) DEFAULT 'normal',
    
    -- Targeting
    audience_type VARCHAR(20) NOT NULL,            -- 'all' | 'segment' | 'specific_users'
    audience_filter JSONB DEFAULT '{}',            -- Segment criteria (see below)
    user_ids UUID[],                               -- For 'specific_users' type
    
    -- Scheduling
    status VARCHAR(20) DEFAULT 'draft',            -- 'draft' | 'scheduled' | 'sending' | 'sent' | 
                                                   -- 'paused' | 'cancelled'
    scheduled_at TIMESTAMPTZ,                      -- NULL = send immediately on publish
    
    -- Delivery stats (denormalized for dashboard speed)
    total_targeted INTEGER DEFAULT 0,
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    total_skipped INTEGER DEFAULT 0,               -- Skipped due to preferences/rate limits
    
    -- Admin metadata
    created_by UUID REFERENCES users(id),          -- Admin user who created
    approved_by UUID REFERENCES users(id),         -- Optional approval workflow
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,                           -- When sending started
    completed_at TIMESTAMPTZ,                      -- When all dispatched
    
    INDEX idx_push_campaign_status (status, scheduled_at),
    INDEX idx_push_campaign_created (created_by, created_at DESC)
);
```

**Audience Filter Examples:**

```json
// All users
{"type": "all"}

// By subscription tier
{"type": "segment", "subscription_tier": ["premium", "institutional"]}

// By activity (active in last N days)
{"type": "segment", "active_within_days": 30}

// By platform
{"type": "segment", "platform": ["ios"]}

// Combined
{
    "type": "segment",
    "subscription_tier": ["premium"],
    "active_within_days": 7,
    "platform": ["ios", "android"],
    "has_wallet": true
}
```

### 1.5 `push_rate_limits` — Sliding Window Rate Tracking

Redis-backed for real-time enforcement, with PostgreSQL fallback for audit.

```sql
-- Redis keys (primary, real-time):
-- push_rate:hourly:{user_id}  → INCR + EXPIRE 3600
-- push_rate:daily:{user_id}   → INCR + EXPIRE 86400

-- PostgreSQL audit table (for admin dashboard / historical reporting)
CREATE TABLE push_rate_limit_log (
    id BIGSERIAL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hour_bucket TIMESTAMPTZ NOT NULL,             -- Truncated to hour
    count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, hour_bucket),
    INDEX idx_rate_limit_user (user_id, hour_bucket DESC)
);

-- Convert to hypertable for auto-cleanup
SELECT create_hypertable('push_rate_limit_log', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Auto-drop chunks older than 30 days
SELECT add_retention_policy('push_rate_limit_log', INTERVAL '30 days');
```

### 1.6 `push_global_settings` — Platform-Wide Admin Configuration

```sql
CREATE TABLE push_global_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Global rate limits (override per-user defaults)
    default_max_per_hour INTEGER DEFAULT 10,
    default_max_per_day INTEGER DEFAULT 50,
    global_max_per_hour INTEGER DEFAULT 15,        -- Hard cap, no user can exceed this
    global_max_per_day INTEGER DEFAULT 100,         -- Hard cap
    
    -- Feature flags
    push_enabled BOOLEAN DEFAULT true,              -- Global kill switch
    promotions_enabled BOOLEAN DEFAULT true,        -- Can admins send promo pushes?
    quiet_hours_enforced BOOLEAN DEFAULT false,     -- Force quiet hours for all users
    quiet_hours_start TIME DEFAULT '23:00',
    quiet_hours_end TIME DEFAULT '08:00',
    
    -- FCM configuration
    fcm_project_id VARCHAR(255),
    fcm_batch_size INTEGER DEFAULT 500,             -- FCM multicast limit per request
    fcm_rate_limit_per_second INTEGER DEFAULT 100,  -- Self-imposed FCM rate limit
    
    -- Cleanup
    token_failure_threshold INTEGER DEFAULT 5,      -- Deactivate token after N failures
    notification_retention_days INTEGER DEFAULT 90, -- Auto-delete old notifications
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

-- Seed with defaults
INSERT INTO push_global_settings (id) VALUES (uuid_generate_v4());
```

---

## 2. API Endpoints

### 2.1 User Endpoints

#### POST /api/v1/push/devices — Register Device Token

Called by the mobile app on every startup and when the push token refreshes.

```python
# Request
class RegisterDeviceRequest(BaseModel):
    device_token: str                   # FCM/Expo push token
    platform: Literal["ios", "android"]
    device_id: str | None = None        # Unique device identifier
    app_version: str | None = None
    os_version: str | None = None
    device_model: str | None = None
    token_type: Literal["fcm", "expo"] = "fcm"

# Response (201 Created or 200 Updated)
class RegisterDeviceResponse(BaseModel):
    device_id: str                      # push_device_tokens.id
    status: str                         # "registered" | "updated"
    active_devices: int                 # Total active devices for this user

# Endpoint
@router.post("/api/v1/push/devices", status_code=201)
async def register_device(
    request: RegisterDeviceRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Register or update a push notification device token.
    
    - If token already exists for user → update metadata, set is_active=true
    - If token exists for DIFFERENT user → reassign to current user (device sold/shared)
    - If new token → create new record
    - Max 5 active devices per user (deactivate oldest if exceeded)
    """
```

**Upsert Logic:**

```python
async def register_device_token(self, user_id: UUID, request: RegisterDeviceRequest) -> RegisterDeviceResponse:
    # Check if token already registered
    existing = await self.repo.get_by_token(request.device_token)
    
    if existing:
        if existing.user_id == user_id:
            # Same user, same token — refresh metadata
            existing.platform = request.platform
            existing.app_version = request.app_version
            existing.os_version = request.os_version
            existing.device_model = request.device_model
            existing.is_active = True
            existing.failed_count = 0
            existing.updated_at = now()
            await self.repo.save(existing)
            return RegisterDeviceResponse(device_id=str(existing.id), status="updated", ...)
        else:
            # Token moved to different user (device ownership transfer)
            existing.user_id = user_id
            existing.is_active = True
            existing.failed_count = 0
            existing.updated_at = now()
            await self.repo.save(existing)
            return RegisterDeviceResponse(device_id=str(existing.id), status="updated", ...)
    
    # New device — create record
    device = PushDeviceToken(user_id=user_id, **request.model_dump())
    await self.repo.save(device)
    
    # Enforce max 5 active devices
    await self._enforce_device_limit(user_id, max_devices=5)
    
    # Create default preferences if first device
    await self._ensure_preferences_exist(user_id)
    
    return RegisterDeviceResponse(device_id=str(device.id), status="registered", ...)
```

#### DELETE /api/v1/push/devices/{device_id} — Unregister Device

```python
@router.delete("/api/v1/push/devices/{device_id}", status_code=204)
async def unregister_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Deactivate a device token (user logged out or uninstalled)."""
```

#### GET /api/v1/push/preferences — Get Notification Preferences

```python
# Response
class PushPreferencesResponse(BaseModel):
    transactions_enabled: bool
    risk_alerts_enabled: bool
    price_alerts_enabled: bool
    portfolio_updates_enabled: bool
    promotions_enabled: bool
    system_enabled: bool
    chat_enabled: bool
    max_per_hour: int
    max_per_day: int
    quiet_hours_enabled: bool
    quiet_hours_start: str          # "23:00"
    quiet_hours_end: str            # "08:00"
    timezone: str
    active_devices: int             # Number of active devices
    
@router.get("/api/v1/push/preferences")
async def get_push_preferences(
    current_user: User = Depends(get_current_user),
):
    """Get user's push notification preferences."""
```

#### PUT /api/v1/push/preferences — Update Notification Preferences

```python
class UpdatePushPreferencesRequest(BaseModel):
    transactions_enabled: bool | None = None
    risk_alerts_enabled: bool | None = None
    price_alerts_enabled: bool | None = None
    portfolio_updates_enabled: bool | None = None
    promotions_enabled: bool | None = None
    chat_enabled: bool | None = None
    quiet_hours_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None
    # NOTE: max_per_hour and max_per_day are NOT user-editable
    # NOTE: system_enabled is NOT user-editable (always true)

@router.put("/api/v1/push/preferences")
async def update_push_preferences(
    request: UpdatePushPreferencesRequest,
    current_user: User = Depends(get_current_user),
):
    """Update user's push notification preferences. Partial update supported."""
```

#### POST /api/v1/push/test — Send Test Notification (Debug)

```python
@router.post("/api/v1/push/test", status_code=200)
async def send_test_notification(
    current_user: User = Depends(get_current_user),
):
    """
    Send a test push notification to all active devices of the current user.
    Rate limited: 1 per minute.
    """
```

---

### 2.2 Admin Endpoints

#### GET /api/v1/admin/push/dashboard — Push Analytics Dashboard

```python
class PushDashboardResponse(BaseModel):
    stats_24h: PushStats
    stats_7d: PushStats
    active_devices: DeviceBreakdown
    recent_campaigns: list[CampaignSummary]
    rate_limit_settings: GlobalSettings
    
class PushStats(BaseModel):
    total_sent: int
    total_delivered: int
    total_opened: int
    total_failed: int
    total_skipped: int
    delivery_rate: float            # delivered / sent
    open_rate: float                # opened / delivered
    failure_rate: float             # failed / sent

class DeviceBreakdown(BaseModel):
    total: int
    ios: int
    android: int
    active_last_7d: int
    inactive: int                   # Registered but no push in 30+ days

@router.get("/api/v1/admin/push/dashboard")
async def get_push_dashboard(
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Push notification analytics dashboard."""
```

#### POST /api/v1/admin/push/campaigns — Create Notification Campaign

```python
class CreateCampaignRequest(BaseModel):
    title: str                                          # Max 255 chars
    body: str                                           # Max 4096 chars
    category: Literal["promotion", "system", "portfolio", "chat"] = "promotion"
    priority: Literal["normal", "high"] = "normal"
    image_url: str | None = None
    action_url: str | None = None                       # Deep link
    action_text: str | None = None
    data: dict | None = None                            # Custom payload
    audience_type: Literal["all", "segment", "specific_users"]
    audience_filter: dict | None = None                 # Segment criteria
    user_ids: list[UUID] | None = None                  # For specific_users
    scheduled_at: datetime | None = None                # NULL = send now
    
class CreateCampaignResponse(BaseModel):
    campaign_id: UUID
    status: str                                         # "draft" | "scheduled" | "sending"
    estimated_recipients: int
    scheduled_at: datetime | None

@router.post("/api/v1/admin/push/campaigns", status_code=201)
async def create_campaign(
    request: CreateCampaignRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Create a push notification campaign.
    
    - If scheduled_at is set → status = 'scheduled', Celery Beat picks it up
    - If scheduled_at is NULL → status = 'sending', dispatched immediately via Celery
    - Audience estimation returned before actual send
    """
```

#### GET /api/v1/admin/push/campaigns — List All Campaigns

```python
@router.get("/api/v1/admin/push/campaigns")
async def list_campaigns(
    status: str | None = None,                  # Filter by status
    page: int = 1,
    per_page: int = 20,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """List all push campaigns with stats, paginated."""
```

#### GET /api/v1/admin/push/campaigns/{campaign_id} — Campaign Detail + Stats

```python
class CampaignDetailResponse(BaseModel):
    campaign: CampaignFull
    delivery_timeline: list[TimelinePoint]       # Delivery over time (for chart)
    platform_breakdown: PlatformStats            # iOS vs Android delivery
    failure_reasons: list[FailureReason]          # Top failure reasons

@router.get("/api/v1/admin/push/campaigns/{campaign_id}")
async def get_campaign_detail(
    campaign_id: UUID,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Get detailed campaign stats including delivery timeline."""
```

#### PUT /api/v1/admin/push/campaigns/{campaign_id}/cancel — Cancel Campaign

```python
@router.put("/api/v1/admin/push/campaigns/{campaign_id}/cancel")
async def cancel_campaign(
    campaign_id: UUID,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Cancel a scheduled or sending campaign. Already-sent notifications are not recalled."""
```

#### GET /api/v1/admin/push/settings — Get Global Push Settings

```python
@router.get("/api/v1/admin/push/settings")
async def get_push_settings(
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Get global push notification configuration."""
```

#### PUT /api/v1/admin/push/settings — Update Global Push Settings

```python
class UpdateGlobalSettingsRequest(BaseModel):
    default_max_per_hour: int | None = None      # Default per-user hourly cap
    default_max_per_day: int | None = None        # Default per-user daily cap
    global_max_per_hour: int | None = None        # Hard cap (overrides user prefs)
    global_max_per_day: int | None = None          # Hard cap
    push_enabled: bool | None = None               # Global kill switch
    promotions_enabled: bool | None = None
    quiet_hours_enforced: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    fcm_batch_size: int | None = None
    token_failure_threshold: int | None = None
    notification_retention_days: int | None = None

@router.put("/api/v1/admin/push/settings")
async def update_push_settings(
    request: UpdateGlobalSettingsRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Update global push configuration. Changes take effect immediately."""
```

#### PUT /api/v1/admin/push/users/{user_id}/limits — Override Per-User Limits

```python
class UserLimitOverrideRequest(BaseModel):
    max_per_hour: int | None = None
    max_per_day: int | None = None
    push_suspended: bool | None = None    # Suspend all pushes for this user
    reason: str | None = None             # Admin note

@router.put("/api/v1/admin/push/users/{user_id}/limits")
async def override_user_limits(
    user_id: UUID,
    request: UserLimitOverrideRequest,
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Override push notification limits for a specific user."""
```

---

## 3. Celery Tasks & Workers

### 3.1 Task: `push.send_to_user` — Send Single Notification

The core task that sends a push notification to a specific user. All other tasks ultimately call this.

```python
# src/app/infrastructure/celery/tasks/push_notification_tasks.py

from firebase_admin import messaging
from celery import shared_task, Task

@shared_task(
    name="push.send_to_user",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(messaging.ApiCallError,),
    retry_backoff=True,
    rate_limit="100/s",              # Self-imposed per-worker limit
    queue="push_notifications",
)
def send_push_to_user(
    self: Task,
    user_id: str,
    title: str,
    body: str,
    category: str,
    priority: str = "normal",
    image_url: str | None = None,
    action_url: str | None = None,
    action_text: str | None = None,
    data: dict | None = None,
    campaign_id: str | None = None,
    notification_id: str | None = None,
) -> dict:
    """
    Send a push notification to all active devices of a user.
    
    Flow:
    1. Load global settings → check kill switch
    2. Load user preferences → check category enabled
    3. Check rate limits (Redis) → skip if exceeded
    4. Check quiet hours → defer if in quiet hours
    5. Fetch active device tokens
    6. Build FCM message per device
    7. Send via FCM multicast
    8. Log results in push_notifications table
    9. Handle failures (increment failed_count, deactivate dead tokens)
    """
    
    async def runner(container):
        from app.domain.services.push.push_delivery_service import PushDeliveryService
        
        service = await container.get(PushDeliveryService)
        
        result = await service.deliver_to_user(
            user_id=UUID(user_id),
            title=title,
            body=body,
            category=category,
            priority=priority,
            image_url=image_url,
            action_url=action_url,
            action_text=action_text,
            data=data or {},
            campaign_id=UUID(campaign_id) if campaign_id else None,
            notification_id=UUID(notification_id) if notification_id else None,
        )
        
        return {
            "status": result.status,
            "devices_targeted": result.devices_targeted,
            "devices_sent": result.devices_sent,
            "devices_failed": result.devices_failed,
            "skipped_reason": result.skipped_reason,
        }
    
    return asyncio.run(_run_task(runner))
```

### 3.2 `PushDeliveryService` — Core Delivery Logic

```python
# src/app/domain/services/push/push_delivery_service.py

class PushDeliveryService:
    """Core push notification delivery with rate limiting, preferences, and FCM dispatch."""
    
    def __init__(
        self,
        device_repo: PushDeviceRepository,
        preference_repo: PushPreferenceRepository,
        notification_repo: PushNotificationRepository,
        global_settings_repo: PushGlobalSettingsRepository,
        rate_limiter: PushRateLimiter,
        fcm_client: FCMClient,
    ):
        ...
    
    async def deliver_to_user(
        self,
        user_id: UUID,
        title: str,
        body: str,
        category: str,
        priority: str,
        **kwargs,
    ) -> DeliveryResult:
        
        # 1. Global kill switch
        settings = await self.global_settings_repo.get()
        if not settings.push_enabled:
            return DeliveryResult(status="skipped", skipped_reason="push_globally_disabled")
        
        # 2. User preferences
        prefs = await self.preference_repo.get_by_user(user_id)
        if not self._is_category_enabled(prefs, category):
            return DeliveryResult(status="skipped", skipped_reason=f"category_{category}_disabled")
        
        # 3. Rate limit check (Redis)
        hourly_limit = min(prefs.max_per_hour, settings.global_max_per_hour)
        daily_limit = min(prefs.max_per_day, settings.global_max_per_day)
        
        if not await self.rate_limiter.can_send(user_id, hourly_limit, daily_limit):
            return DeliveryResult(status="skipped", skipped_reason="rate_limit_exceeded")
        
        # 4. Quiet hours check
        if self._is_in_quiet_hours(prefs, settings):
            if priority != "critical":  # Critical bypasses quiet hours
                return DeliveryResult(status="skipped", skipped_reason="quiet_hours")
        
        # 5. Get active device tokens
        devices = await self.device_repo.get_active_by_user(user_id)
        if not devices:
            return DeliveryResult(status="skipped", skipped_reason="no_active_devices")
        
        # 6. Build and send FCM messages
        results = []
        for device in devices:
            try:
                fcm_response = await self.fcm_client.send(
                    token=device.device_token,
                    title=title,
                    body=body,
                    image_url=kwargs.get("image_url"),
                    data={
                        "action_url": kwargs.get("action_url", ""),
                        "category": category,
                        "notification_id": str(kwargs.get("notification_id", "")),
                        **(kwargs.get("data") or {}),
                    },
                    priority="high" if priority in ("high", "critical") else "normal",
                    platform=device.platform,
                )
                
                # Log success
                await self._log_notification(device, "sent", fcm_response.message_id, **kwargs)
                results.append(("sent", device.id))
                
            except messaging.UnregisteredError:
                # Token is dead — deactivate
                device.is_active = False
                await self.device_repo.save(device)
                results.append(("failed", device.id))
                
            except messaging.ApiCallError as e:
                # Transient failure — increment counter
                device.failed_count += 1
                device.last_failed_at = now()
                if device.failed_count >= settings.token_failure_threshold:
                    device.is_active = False
                await self.device_repo.save(device)
                results.append(("failed", device.id))
        
        # 7. Increment rate limit counters
        await self.rate_limiter.increment(user_id)
        
        sent = sum(1 for s, _ in results if s == "sent")
        failed = sum(1 for s, _ in results if s == "failed")
        
        return DeliveryResult(
            status="sent" if sent > 0 else "failed",
            devices_targeted=len(devices),
            devices_sent=sent,
            devices_failed=failed,
        )
    
    def _is_category_enabled(self, prefs: PushNotificationPreferences, category: str) -> bool:
        """Check if user has this notification category enabled."""
        CATEGORY_MAP = {
            "transaction": prefs.transactions_enabled,
            "risk_alert": prefs.risk_alerts_enabled,
            "price_alert": prefs.price_alerts_enabled,
            "portfolio": prefs.portfolio_updates_enabled,
            "promotion": prefs.promotions_enabled,
            "system": True,  # System notifications cannot be disabled
            "chat": prefs.chat_enabled,
        }
        return CATEGORY_MAP.get(category, True)
```

### 3.3 `PushRateLimiter` — Redis Sliding Window

```python
# src/app/infrastructure/adapters/push_rate_limiter.py

class PushRateLimiter:
    """Redis-based sliding window rate limiter for push notifications."""
    
    HOURLY_KEY = "push_rate:hourly:{user_id}"
    DAILY_KEY = "push_rate:daily:{user_id}"
    
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def can_send(self, user_id: UUID, max_hourly: int, max_daily: int) -> bool:
        hourly = await self.redis.get(self.HOURLY_KEY.format(user_id=user_id))
        daily = await self.redis.get(self.DAILY_KEY.format(user_id=user_id))
        
        hourly_count = int(hourly) if hourly else 0
        daily_count = int(daily) if daily else 0
        
        return hourly_count < max_hourly and daily_count < max_daily
    
    async def increment(self, user_id: UUID):
        hourly_key = self.HOURLY_KEY.format(user_id=user_id)
        daily_key = self.DAILY_KEY.format(user_id=user_id)
        
        pipe = self.redis.pipeline()
        pipe.incr(hourly_key)
        pipe.expire(hourly_key, 3600)    # 1 hour TTL
        pipe.incr(daily_key)
        pipe.expire(daily_key, 86400)    # 24 hour TTL
        await pipe.execute()
```

### 3.4 Task: `push.dispatch_campaign` — Process Campaign

Dispatches a campaign by resolving audience and fanning out to individual `send_to_user` tasks.

```python
@shared_task(
    name="push.dispatch_campaign",
    bind=True,
    max_retries=2,
    queue="push_campaigns",
)
def dispatch_campaign(self: Task, campaign_id: str) -> dict:
    """
    Dispatch a campaign to all targeted users.
    
    Flow:
    1. Load campaign → validate status
    2. Resolve audience → list of user_ids
    3. Update campaign status to 'sending'
    4. Fan out: enqueue send_to_user for each user (batched)
    5. Update campaign total_targeted
    """
    
    async def runner(container):
        from app.domain.services.push.campaign_dispatch_service import CampaignDispatchService
        
        service = await container.get(CampaignDispatchService)
        campaign = await service.load_campaign(UUID(campaign_id))
        
        if campaign.status not in ("scheduled", "draft"):
            return {"status": "skipped", "reason": f"campaign_status_{campaign.status}"}
        
        # Resolve audience
        user_ids = await service.resolve_audience(campaign)
        
        # Update campaign
        campaign.status = "sending"
        campaign.total_targeted = len(user_ids)
        campaign.sent_at = now()
        await service.save_campaign(campaign)
        
        # Fan out in batches of 100
        BATCH_SIZE = 100
        for i in range(0, len(user_ids), BATCH_SIZE):
            batch = user_ids[i:i + BATCH_SIZE]
            for uid in batch:
                send_push_to_user.apply_async(
                    kwargs={
                        "user_id": str(uid),
                        "title": campaign.title,
                        "body": campaign.body,
                        "category": campaign.category,
                        "priority": campaign.priority,
                        "image_url": campaign.image_url,
                        "action_url": campaign.action_url,
                        "action_text": campaign.action_text,
                        "data": campaign.data,
                        "campaign_id": str(campaign.id),
                    },
                    queue="push_notifications",
                )
        
        return {
            "status": "dispatched",
            "campaign_id": campaign_id,
            "users_targeted": len(user_ids),
        }
    
    return asyncio.run(_run_task(runner))
```

**Audience Resolution Logic:**

```python
class CampaignDispatchService:
    async def resolve_audience(self, campaign: PushCampaign) -> list[UUID]:
        if campaign.audience_type == "all":
            return await self.user_repo.get_all_active_user_ids()
        
        elif campaign.audience_type == "specific_users":
            return campaign.user_ids or []
        
        elif campaign.audience_type == "segment":
            f = campaign.audience_filter
            query = select(users.c.id).where(users.c.is_active == True)
            
            if "subscription_tier" in f:
                query = query.where(users.c.subscription_tier.in_(f["subscription_tier"]))
            
            if "active_within_days" in f:
                cutoff = now() - timedelta(days=f["active_within_days"])
                query = query.where(users.c.last_login_at >= cutoff)
            
            if "platform" in f:
                # Join with push_device_tokens
                query = query.join(
                    push_device_tokens,
                    push_device_tokens.c.user_id == users.c.id
                ).where(
                    push_device_tokens.c.platform.in_(f["platform"]),
                    push_device_tokens.c.is_active == True,
                )
            
            if f.get("has_wallet"):
                query = query.where(users.c.wallet_address.isnot(None))
            
            result = await self.session.execute(query)
            return [row.id for row in result]
```

### 3.5 Task: `push.check_scheduled_campaigns` — Celery Beat Scheduler

Runs every minute to check for campaigns that need to be dispatched.

```python
@shared_task(
    name="push.check_scheduled_campaigns",
    bind=True,
    queue="push_campaigns",
)
def check_scheduled_campaigns(self: Task) -> dict:
    """
    Check for scheduled campaigns whose send time has arrived.
    Runs every minute via Celery Beat.
    """
    async def runner(container):
        from app.infrastructure.persistence_sqla.session import AsyncSession
        
        session = await container.get(AsyncSession)
        
        due_campaigns = await session.execute(
            select(push_campaigns).where(
                push_campaigns.c.status == "scheduled",
                push_campaigns.c.scheduled_at <= now(),
            )
        )
        
        dispatched = 0
        for campaign in due_campaigns:
            dispatch_campaign.apply_async(
                kwargs={"campaign_id": str(campaign.id)},
                queue="push_campaigns",
            )
            dispatched += 1
        
        return {"dispatched": dispatched}
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["push-check-scheduled-campaigns"] = {
    "task": "push.check_scheduled_campaigns",
    "schedule": crontab(minute="*"),  # Every minute
}
```

### 3.6 Task: `push.cleanup_dead_tokens` — Token Hygiene

```python
@shared_task(
    name="push.cleanup_dead_tokens",
    bind=True,
    queue="push_maintenance",
)
def cleanup_dead_tokens(self: Task) -> dict:
    """
    Deactivate device tokens that have exceeded the failure threshold
    and tokens not used in 90+ days. Runs daily.
    """
    async def runner(container):
        session = await container.get(AsyncSession)
        settings = await container.get(PushGlobalSettingsRepository)
        global_settings = await settings.get()
        
        # Deactivate tokens with too many failures
        failed_result = await session.execute(
            update(push_device_tokens)
            .where(
                push_device_tokens.c.is_active == True,
                push_device_tokens.c.failed_count >= global_settings.token_failure_threshold,
            )
            .values(is_active=False, updated_at=now())
        )
        
        # Deactivate stale tokens (no push in 90 days)
        stale_result = await session.execute(
            update(push_device_tokens)
            .where(
                push_device_tokens.c.is_active == True,
                or_(
                    push_device_tokens.c.last_used_at < now() - timedelta(days=90),
                    and_(
                        push_device_tokens.c.last_used_at.is_(None),
                        push_device_tokens.c.created_at < now() - timedelta(days=90),
                    ),
                ),
            )
            .values(is_active=False, updated_at=now())
        )
        
        await session.commit()
        
        return {
            "failed_deactivated": failed_result.rowcount,
            "stale_deactivated": stale_result.rowcount,
        }
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["push-cleanup-dead-tokens"] = {
    "task": "push.cleanup_dead_tokens",
    "schedule": crontab(hour=3, minute=0),  # Daily at 03:00 UTC
}
```

### 3.7 Task: `push.cleanup_old_notifications` — Retention Cleanup

```python
@shared_task(
    name="push.cleanup_old_notifications",
    bind=True,
    queue="push_maintenance",
)
def cleanup_old_notifications(self: Task) -> dict:
    """
    Delete notification logs older than retention period.
    Uses TimescaleDB drop_chunks for efficient deletion.
    Runs weekly.
    """
    async def runner(container):
        session = await container.get(AsyncSession)
        settings = await container.get(PushGlobalSettingsRepository)
        global_settings = await settings.get()
        
        retention = timedelta(days=global_settings.notification_retention_days)
        cutoff = now() - retention
        
        # TimescaleDB efficient chunk deletion
        await session.execute(
            text("SELECT drop_chunks('push_notifications', older_than => :cutoff)"),
            {"cutoff": cutoff},
        )
        await session.commit()
        
        return {"cutoff": cutoff.isoformat()}
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["push-cleanup-old-notifications"] = {
    "task": "push.cleanup_old_notifications",
    "schedule": crontab(hour=4, minute=0, day_of_week="sunday"),  # Weekly
}
```

### 3.8 Task: `push.update_campaign_stats` — Denormalized Stats Refresh

```python
@shared_task(
    name="push.update_campaign_stats",
    bind=True,
    queue="push_maintenance",
)
def update_campaign_stats(self: Task) -> dict:
    """
    Refresh denormalized delivery stats on active campaigns.
    Runs every 5 minutes while campaigns are sending.
    """
    async def runner(container):
        session = await container.get(AsyncSession)
        
        # Find campaigns that are still 'sending'
        active = await session.execute(
            select(push_campaigns.c.id).where(
                push_campaigns.c.status == "sending"
            )
        )
        
        updated = 0
        for (campaign_id,) in active:
            stats = await session.execute(
                select(
                    func.count().label("total"),
                    func.count().filter(push_notifications.c.status == "sent").label("sent"),
                    func.count().filter(push_notifications.c.status == "delivered").label("delivered"),
                    func.count().filter(push_notifications.c.status == "opened").label("opened"),
                    func.count().filter(push_notifications.c.status == "failed").label("failed"),
                    func.count().filter(push_notifications.c.status == "skipped").label("skipped"),
                ).where(push_notifications.c.campaign_id == campaign_id)
            )
            row = stats.first()
            
            await session.execute(
                update(push_campaigns).where(push_campaigns.c.id == campaign_id).values(
                    total_sent=row.sent,
                    total_delivered=row.delivered,
                    total_opened=row.opened,
                    total_failed=row.failed,
                    total_skipped=row.skipped,
                )
            )
            
            # Auto-complete if all dispatched
            if row.total >= row.sent + row.failed + row.skipped:
                if row.total == campaign.total_targeted:
                    await session.execute(
                        update(push_campaigns).where(push_campaigns.c.id == campaign_id).values(
                            status="sent", completed_at=now()
                        )
                    )
            
            updated += 1
        
        await session.commit()
        return {"campaigns_updated": updated}
    
    return asyncio.run(_run_task(runner))


celery_app.conf.beat_schedule["push-update-campaign-stats"] = {
    "task": "push.update_campaign_stats",
    "schedule": crontab(minute="*/5"),  # Every 5 minutes
}
```

---

## 4. FCM Client Implementation

```python
# src/app/infrastructure/adapters/fcm_client.py

import firebase_admin
from firebase_admin import credentials, messaging

class FCMClient:
    """Firebase Cloud Messaging client for sending push notifications."""
    
    def __init__(self, service_account_path: str):
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
    
    async def send(
        self,
        token: str,
        title: str,
        body: str,
        image_url: str | None = None,
        data: dict | None = None,
        priority: str = "normal",
        platform: str = "android",
    ) -> messaging.SendResponse:
        """Send a single push notification via FCM."""
        
        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url,
        )
        
        # Platform-specific config
        android_config = messaging.AndroidConfig(
            priority="high" if priority == "high" else "normal",
            notification=messaging.AndroidNotification(
                channel_id="anvil_default",      # Must match app's channel
                icon="ic_notification",
                color="#6C5CE7",                  # Anvil brand purple
                click_action="OPEN_ACTIVITY",
            ),
        )
        
        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(title=title, body=body),
                    sound="default",
                    badge=1,
                    mutable_content=True,         # For notification extensions
                    category="ANVIL_DEFAULT",
                ),
            ),
        )
        
        message = messaging.Message(
            notification=notification,
            data={k: str(v) for k, v in (data or {}).items()},  # FCM requires string values
            token=token,
            android=android_config,
            apns=apns_config,
        )
        
        # Run in thread pool (firebase-admin is sync)
        return await asyncio.get_event_loop().run_in_executor(
            None, messaging.send, message
        )
    
    async def send_multicast(
        self,
        tokens: list[str],
        title: str,
        body: str,
        **kwargs,
    ) -> messaging.BatchResponse:
        """Send to multiple tokens at once (max 500 per FCM limit)."""
        
        notification = messaging.Notification(title=title, body=body, image=kwargs.get("image_url"))
        
        message = messaging.MulticastMessage(
            notification=notification,
            data={k: str(v) for k, v in (kwargs.get("data") or {}).items()},
            tokens=tokens,
        )
        
        return await asyncio.get_event_loop().run_in_executor(
            None, messaging.send_each_for_multicast, message
        )
```

---

## 5. React Native Integration (Expo)

### 5.1 Token Registration on App Startup

```typescript
// src/services/pushNotifications.ts
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import { api } from './api';

export async function registerForPushNotifications(): Promise<string | null> {
  // Only real devices can receive push
  if (!Device.isDevice) {
    console.log('Push notifications require a physical device');
    return null;
  }
  
  // Check / request permission
  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;
  
  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  
  if (finalStatus !== 'granted') {
    console.log('Push notification permission not granted');
    return null;
  }
  
  // Get push token (Expo or FCM)
  const tokenData = await Notifications.getExpoPushTokenAsync({
    projectId: 'your-expo-project-id',  // From app.json
  });
  const pushToken = tokenData.data;
  
  // Register with backend
  try {
    await api.post('/api/v1/push/devices', {
      device_token: pushToken,
      platform: Platform.OS,                    // 'ios' | 'android'
      device_id: Device.modelId,
      app_version: '1.0.0',                    // From app.json
      os_version: `${Platform.OS} ${Platform.Version}`,
      device_model: Device.modelName,
      token_type: 'expo',                       // or 'fcm' if using native FCM
    });
  } catch (err) {
    console.error('Failed to register push token:', err);
  }
  
  return pushToken;
}

// Android notification channel setup
if (Platform.OS === 'android') {
  Notifications.setNotificationChannelAsync('anvil_default', {
    name: 'Anvil Notifications',
    importance: Notifications.AndroidImportance.HIGH,
    vibrationPattern: [0, 250, 250, 250],
    lightColor: '#6C5CE7',
  });
}
```

### 5.2 Notification Handlers

```typescript
// src/hooks/usePushNotifications.ts
import { useEffect, useRef } from 'react';
import * as Notifications from 'expo-notifications';
import { router } from 'expo-router';

export function usePushNotifications() {
  const notificationListener = useRef<Notifications.Subscription>();
  const responseListener = useRef<Notifications.Subscription>();
  
  useEffect(() => {
    // Handle notification received while app is foregrounded
    notificationListener.current = Notifications.addNotificationReceivedListener(
      (notification) => {
        const data = notification.request.content.data;
        console.log('Notification received:', data);
        // Update badge count, refresh notification list, etc.
      }
    );
    
    // Handle user tapping on notification
    responseListener.current = Notifications.addNotificationResponseReceivedListener(
      (response) => {
        const data = response.notification.request.content.data;
        const actionUrl = data.action_url as string;
        
        if (actionUrl) {
          // Deep link: anvil://swap/confirm/abc123 → /swap/confirm/abc123
          const path = actionUrl.replace('anvil://', '/');
          router.push(path);
        }
      }
    );
    
    return () => {
      notificationListener.current?.remove();
      responseListener.current?.remove();
    };
  }, []);
}
```

---

## 6. System Event Triggers

Pre-built triggers that fire push notifications from system events (not admin campaigns).

```python
# src/app/domain/services/push/push_trigger_service.py

class PushTriggerService:
    """Fires push notifications from system events."""
    
    async def on_transaction_confirmed(self, user_id: UUID, tx: Transaction):
        """Fired by transaction_confirmation_tasks.py after tx confirmed on-chain."""
        send_push_to_user.apply_async(kwargs={
            "user_id": str(user_id),
            "title": "Transaction Confirmed ✅",
            "body": f"Your {tx.type} of {tx.amount} {tx.token} was confirmed.",
            "category": "transaction",
            "priority": "high",
            "action_url": f"anvil://transactions/{tx.id}",
            "data": {"tx_id": str(tx.id), "tx_hash": tx.tx_hash},
        })
    
    async def on_transaction_failed(self, user_id: UUID, tx: Transaction):
        send_push_to_user.apply_async(kwargs={
            "user_id": str(user_id),
            "title": "Transaction Failed ❌",
            "body": f"Your {tx.type} of {tx.amount} {tx.token} has failed.",
            "category": "transaction",
            "priority": "high",
            "action_url": f"anvil://transactions/{tx.id}",
        })
    
    async def on_funds_received(self, user_id: UUID, token: str, amount: str, from_addr: str):
        send_push_to_user.apply_async(kwargs={
            "user_id": str(user_id),
            "title": f"Received {amount} {token} 💰",
            "body": f"From {from_addr[:6]}...{from_addr[-4:]}",
            "category": "transaction",
            "priority": "high",
            "action_url": "anvil://portfolio",
        })
    
    async def on_risk_alert(self, user_id: UUID, protocol: str, severity: str, message: str):
        send_push_to_user.apply_async(kwargs={
            "user_id": str(user_id),
            "title": f"⚠️ {severity} Risk Alert: {protocol}",
            "body": message,
            "category": "risk_alert",
            "priority": "critical" if severity == "CRITICAL" else "high",
            "action_url": f"anvil://alerts",
        })
    
    async def on_price_alert(self, user_id: UUID, token: str, direction: str, price: float, threshold: float):
        emoji = "📈" if direction == "above" else "📉"
        send_push_to_user.apply_async(kwargs={
            "user_id": str(user_id),
            "title": f"{emoji} {token} Price Alert",
            "body": f"{token} is now ${price:.2f} ({direction} your ${threshold:.2f} alert)",
            "category": "price_alert",
            "action_url": f"anvil://market/{token}",
        })
```

---

## 7. Celery Queue Configuration

```python
# src/app/infrastructure/celery/config.py

CELERY_QUEUES = {
    "push_notifications": {
        "exchange": "push",
        "routing_key": "push.send",
        "queue_arguments": {"x-max-priority": 10},  # Priority queue
    },
    "push_campaigns": {
        "exchange": "push",
        "routing_key": "push.campaign",
    },
    "push_maintenance": {
        "exchange": "push",
        "routing_key": "push.maintenance",
    },
}

# Worker startup command:
# celery -A app.infrastructure.celery.app worker -Q push_notifications --concurrency=8 -n push@%h
# celery -A app.infrastructure.celery.app worker -Q push_campaigns --concurrency=2 -n campaigns@%h
# celery -A app.infrastructure.celery.app worker -Q push_maintenance --concurrency=1 -n maintenance@%h
```

---

## 8. Hexagonal Architecture — File Structure

```
src/app/
├── domain/
│   ├── entities/
│   │   ├── push_device_token.py          # PushDeviceToken entity
│   │   ├── push_notification.py          # PushNotification entity
│   │   ├── push_campaign.py              # PushCampaign entity
│   │   └── push_preferences.py           # PushNotificationPreferences entity
│   ├── ports/
│   │   ├── push_device_repository.py     # Port: device CRUD
│   │   ├── push_notification_repository.py  # Port: notification log
│   │   ├── push_campaign_repository.py   # Port: campaign CRUD
│   │   ├── push_preference_repository.py # Port: preferences CRUD
│   │   └── push_global_settings_repository.py  # Port: global settings
│   └── services/
│       └── push/
│           ├── push_delivery_service.py    # Core delivery logic
│           ├── push_trigger_service.py     # System event triggers
│           ├── campaign_dispatch_service.py # Campaign audience resolution + fanout
│           └── push_rate_limiter.py        # Rate limit interface (port)
├── infrastructure/
│   ├── adapters/
│   │   ├── push_device_repository_sqla.py
│   │   ├── push_notification_repository_sqla.py
│   │   ├── push_campaign_repository_sqla.py
│   │   ├── push_preference_repository_sqla.py
│   │   ├── push_global_settings_repository_sqla.py
│   │   ├── push_rate_limiter_redis.py      # Redis implementation
│   │   └── fcm_client.py                   # Firebase Admin SDK wrapper
│   ├── persistence_sqla/mappings/
│   │   ├── push_device_token.py
│   │   ├── push_notification.py
│   │   ├── push_campaign.py
│   │   ├── push_notification_preferences.py
│   │   ├── push_rate_limit_log.py
│   │   └── push_global_settings.py
│   └── celery/tasks/
│       └── push_notification_tasks.py      # All Celery tasks
└── presentation/http/controllers/
    ├── user/
    │   └── push_router.py                  # User endpoints (devices, preferences, test)
    └── admin/
        └── push_admin_router.py            # Admin endpoints (dashboard, campaigns, settings)
```

---

## 9. Dependencies

```bash
pip install firebase-admin --break-system-packages   # FCM SDK
# Already in stack: celery, redis, sqlalchemy, fastapi
```

```bash
# React Native (Expo)
npx expo install expo-notifications expo-device expo-constants
```

---

## 10. Environment Variables

```bash
# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=/etc/secrets/firebase-service-account.json
FIREBASE_PROJECT_ID=anvil-defi-prod

# Push notification settings
PUSH_DEFAULT_MAX_PER_HOUR=10
PUSH_DEFAULT_MAX_PER_DAY=50
PUSH_GLOBAL_MAX_PER_HOUR=15
PUSH_GLOBAL_MAX_PER_DAY=100
PUSH_TOKEN_FAILURE_THRESHOLD=5
PUSH_NOTIFICATION_RETENTION_DAYS=90
```

---

## 11. Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Device registration | <200ms | Simple upsert |
| Single push dispatch | <500ms | Including rate limit check + FCM call |
| Campaign fan-out (10K users) | <30s | 100-user batches, parallel workers |
| Campaign fan-out (50K users) | <2min | Scale workers horizontally |
| FCM delivery latency | <2s | FCM's own SLA |
| Rate limit check | <5ms | Redis GET |
| Dead token cleanup | <10s | Batch UPDATE |

---

## 12. Monitoring & Alerts

```python
# Structured logging for push operations
{
    "event": "push_sent",
    "user_id": "uuid",
    "device_platform": "ios",
    "category": "transaction",
    "fcm_message_id": "projects/anvil/messages/abc123",
    "latency_ms": 245,
    "campaign_id": null,
}

{
    "event": "push_failed",
    "user_id": "uuid",
    "device_platform": "android",
    "failure_reason": "unregistered",
    "device_token_deactivated": true,
}

{
    "event": "push_rate_limited",
    "user_id": "uuid",
    "hourly_count": 10,
    "daily_count": 35,
    "limit_type": "hourly",
}

{
    "event": "campaign_dispatched",
    "campaign_id": "uuid",
    "users_targeted": 5230,
    "dispatch_time_ms": 12500,
}
```

**Operational Alerts:**
- FCM failure rate >5% sustained over 5 minutes
- Campaign dispatch taking >5 minutes for <10K users
- Dead token cleanup affecting >1000 tokens (possible app update issue)
- Global push kill switch activated
- Rate limit hit rate >20% (caps may be too aggressive)

---

*End of specification — FastStrat LLC, CTO Office*
