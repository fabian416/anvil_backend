# Module: Notifications & Alerts

**Route**: `/notifications`
**Auth Required**: Yes
**Package**: `user/notifications`

## 1. Overview
Central hub for system messages and high-priority risk alerts.

## 2. API Contract

### System Notifications (General)
**Endpoint**: `GET /api/v1/notifications/`
**Query**: `page`, `per_page`.
**Response**: `List<Notification>` (`title`, `body`).

### Risk Alerts (High Priority)
**Endpoint**: `GET /api/v1/user/alerts/risk`
**Query**: `unacknowledged_only`, `severity`.
**Response**: `RiskAlertListResponse`.

### Alert Preferences
**Endpoint**: `GET /api/v1/user/alerts/subscription`
**Response**:
```json
{
  "risk_alerts_enabled": true,
  "push_notifications": true,
  "min_severity": "MEDIUM",
  "email_notifications": false
}
```

### Update Preferences
**Endpoint**: `PUT /api/v1/user/alerts/subscription`
**Body**: Same structure as Response.

## 3. Implementation Flow
1.  **Bell Icon**: Shows red dot if `unacknowledged_risk > 0` or `unread_notifications > 0`.
2.  **Tabs**: "All" (Notifications) vs "Risk" (Alerts).
3.  **Settings**: "Manage Custom Alerts" calls the Subscription endpoints.
