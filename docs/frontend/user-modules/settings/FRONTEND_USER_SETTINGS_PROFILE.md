# FRONTEND_USER_SETTINGS_PROFILE

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/account/router.py` & `preferences/router.py`

## 1. Module Overview
The **User Profile** module manages personal information and application-wide preferences.

**Base URL**: `/api/v1`

---

## 2. Endpoints

### 2.1 Get Account Details
**GET** `/api/v1/account/me`

Basic user identity information.

**Response (200 OK):**
```json
{
  "id": 123,
  "privy_user_id": "did:privy:...",
  "wallet_address": "0x...",
  "primary_email": "user@example.com",
  "created_at": "..."
}
```

### 2.2 Get/Update Preferences
**GET** `/api/v1/user/preferences`
**PUT** `/api/v1/user/preferences/risk-tolerance`
**PUT** `/api/v1/user/preferences/chains`

Manages customization settings.

**Response (200 OK):**
```json
{
  "risk_tolerance": "moderate",
  "preferred_chains": ["ethereum", "arbitrum"],
  "theme": "system",
  "default_currency": "USD"
}
```

### 2.3 Manage Favorites
**POST** `/api/v1/user/preferences/favorites/protocols/{protocol_id}`
**DELETE** `/api/v1/user/preferences/favorites/protocols/{protocol_id}`

Bookmarks specific protocols for quick access.

---

## 3. Error Handling

| Status | Code | Meaning |
| :--- | :--- | :--- |
| 401 | `UNAUTHORIZED` | Invalid session. |
