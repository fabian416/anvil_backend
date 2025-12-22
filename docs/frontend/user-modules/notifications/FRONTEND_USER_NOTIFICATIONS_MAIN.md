# FRONTEND_USER_NOTIFICATIONS_MAIN

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/notification/router.py`

## 1. Module Overview
The **Notifications** module provides a stream of user alerts, including price alerts, system messages, and security warnings.

**Base URL**: `/api/v1/notifications`

---

## 2. Endpoints

### 2.1 Get Notifications
**GET** `/api/v1/notifications/`

Paginated list of notifications.

**Query Params**:
*   `page`: `int` (default 1)
*   `per_page`: `int` (default 10, max 100)

**Response (200 OK):**
```json
[
  {
    "id": "uuid",
    "type": "price_alert",
    "title": "ETH is up 5%",
    "body": "Ethereum has reached $3,200.",
    "is_read": false,
    "created_at": "..."
  }
]
```

---

## 3. Error Handling

| Status | Code | Meaning |
| :--- | :--- | :--- |
| 503 | `SERVICE_UNAVAILABLE` | Notification service down. |
