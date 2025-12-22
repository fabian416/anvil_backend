# Module: Profile Settings

**Route**: `/settings/profile`
**Auth Required**: Yes
**Package**: `user/settings`

## 1. Overview
Manage user identity. Mirrors the Onboarding/KYC data.

## 2. API Contract
*Ref: KYC Documentation.*

### Get Profile
**Endpoint**: `GET /api/v1/account/me`

### Update Profile
**Endpoint**: `PUT /api/v1/account/me`
**Body**: `UpdateMeRequest` (`first_name`, `country_id`, etc.).

## 3. Implementation Flow
1.  Pre-fill form with `/me` data.
2.  "Save Changes" -> `PUT /me`.
