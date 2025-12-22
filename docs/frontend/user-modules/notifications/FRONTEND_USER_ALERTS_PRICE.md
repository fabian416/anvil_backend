# Module: Price Alerts

**Route**: `/notifications/alerts`
**Auth Required**: Yes
**Package**: `user/notifications`

## 1. Overview
Manage custom price watch triggers.

### Key Features
- **Create Alert**: Target Price, % Change.
- **Management**: Toggle or Delete existing alerts.

## 2. UI/UX Specification
- **Form**: Token Selector -> Condition (> or <) -> Price Input.
- **List**: Active alerts.

## 3. API Integration
`GET /api/v1/notifications/alerts`
`POST /api/v1/notifications/alerts`
`DELETE /api/v1/notifications/alerts/:id`
