# Module: KYC & Profile Setup

**Route**: `/onboarding/kyc` (or `/settings/profile`)
**Auth Required**: **Yes** (Bearer Token)
**Package**: `user/onboarding`

## 1. Overview
Manages user identity and profile completion. Since the backend treats KYC as part of the User Profile, this module interacts with the generic User endpoints.

## 2. API Contract

### Get Current Status
**Endpoint**: `GET /api/v1/account/me`
**Response Body (`MeResponse`)**:
| Field | Type | Description |
|---|---|---|
| `id` | `integer` | |
| `is_verified` | `boolean` | **True** if KYC passed |
| `country_id` | `integer?` | ISO ID |
| `country_name` | `string?` | e.g. "United States" |
| `profile_picture` | `string?` | URL |
| `first_name` | `string` | |
| `last_name` | `string` | |

### Update Profile (Submit Info)
**Endpoint**: `PUT /api/v1/account/me`
**Content-Type**: `application/json`

#### Request Body (`UpdateMeRequest`)
| Field | Type | Required | Description |
|---|---|---|---|
| `first_name` | `string` | No | |
| `last_name` | `string` | No | |
| `country_id` | `integer` | No | **Critical**: Must match `countries` table ID |
| `city_id` | `integer` | No | Must belong to Country |
| `profile_picture` | `string` | No | S3/CDN URL |

**JSON Example**:
```json
{
  "first_name": "Alice",
  "last_name": "Smith",
  "country_id": 840,
  "city_id": 1205
}
```

### Error Codes
| Status | Description | UI Behavior |
|---|---|---|
| `400` | Invalid Country/City ID | Show "Region not supported or invalid" |
| `401` | Unauthorized | Redirect to Login |
| `503` | Database Error | "Profile update failed. Try again." |

## 3. Implementation Flow

1.  **Mount**: Fetch `GET /me`.
    - If `is_verified` is true, skip to Home.
2.  **Form Input**: User enters Name + Country.
3.  **Submit**:
    - `PUT /me` with data.
4.  **Identity Verification**:
    - *Future Integration*: Launch Sumsub/Onfido SDK.
    - Currently: Profile data submission acts as basic "Level 1" verification.
