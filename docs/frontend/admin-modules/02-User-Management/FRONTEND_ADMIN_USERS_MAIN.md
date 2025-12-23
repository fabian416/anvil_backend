# Module: User Management

**Route**: `/admin/users`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/users`

## 1. Overview
Enables administrators to oversee the user base. Provides search, filtering, pagination, and status management capabilities (Activate/Deactivate), along with role assignment (Grant/Revoke Admin) and password management.

## 2. API Contract

### List Users
**Endpoint**: `GET /api/admin/users/`  
**Query Params**:
- `limit` (number, optional): Users per page (Default: 20, Min: 1, Max: 100).
- `offset` (number, optional): Pagination offset (Default: 0).
- `sorting_field` (string, optional): Field to sort by - `email`, `created_at`, `is_active`, `is_admin` (Default: `email`).
- `sorting_order` (string, optional): Sort order - `ASC`, `DESC` (Default: `ASC`).

#### Response Body (`ListUsersResponse`)
| Field | Type | Description |
|---|---|---|
| `items` | `User[]` | Array of user objects |
| `total` | `number` | Total number of users |
| `limit` | `number` | Limit used |
| `offset` | `number` | Offset used |

**User Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | User UUID |
| `email` | `string` | User email address |
| `is_active` | `boolean` | Whether user account is active |
| `is_admin` | `boolean` | Whether user has admin role |
| `created_at` | `string` | ISO 8601 creation timestamp |

**JSON Example**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "is_active": true,
      "is_admin": false,
      "created_at": "2023-10-01T10:00:00Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### Activate User
**Endpoint**: `PATCH /api/admin/users/{email}/activate`  
**Path Params**:
- `email` (string, **required**): User email address.

#### Response
`204 No Content` - No response body

### Deactivate User
**Endpoint**: `PATCH /api/admin/users/{email}/deactivate`  
**Path Params**:
- `email` (string, **required**): User email address.

#### Response
`204 No Content` - No response body

### Grant Admin Role
**Endpoint**: `PATCH /api/admin/users/{email}/grant-admin`  
**Path Params**:
- `email` (string, **required**): User email address.

**Auth Required**: Super Admin Only

#### Response
`204 No Content` - No response body

### Revoke Admin Role
**Endpoint**: `PATCH /api/admin/users/{email}/revoke-admin`  
**Path Params**:
- `email` (string, **required**): User email address.

**Auth Required**: Super Admin Only

**Note**: Cannot revoke super admin role.

#### Response
`204 No Content` - No response body

### Change User Password
**Endpoint**: `PATCH /api/admin/users/{email}/password`  
**Path Params**:
- `email` (string, **required**): User email address.

#### Request Body (`ChangePasswordRequest`)
| Field | Type | Description |
|---|---|---|
| `password` | `string` | New password (min 8 characters) |

**JSON Example**:
```json
{
  "password": "newSecurePassword123"
}
```

#### Response
`204 No Content` - No response body

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `400` | `DomainFieldError` | Invalid password format | Show error: "Password must be at least 8 characters" |
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin / Not super admin | Show error: "Admin access required" or "Super admin access required" |
| `404` | `UserNotFoundByEmailError` | User not found | Show error: "User not found" |
| `409` | `DomainConflictError` | Cannot revoke super admin | Show error: "Cannot revoke super admin role" |
| `500` | `Exception` | Internal server error | Show error: "Failed to perform operation" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useUsers({ limit, offset, sorting_field, sorting_order })` hook which fetches `/api/admin/users/`.
2. **Display**:
   - User table: Display `items` array with columns: Email, Status (Active/Inactive badge), Role (Admin/User badge), Joined Date (`created_at`), Actions (kebab menu).
   - Pagination: Use `total`, `limit`, `offset` to display pagination controls.
   - Search: Client-side or server-side search by email (implement based on requirements).
3. **Sorting**: On column header click, update `sorting_field` and `sorting_order`, refetch data.
4. **User Actions**:
   - **Activate/Deactivate**: Show confirmation modal, call respective endpoint, invalidate query cache, show success toast.
   - **Grant/Revoke Admin**: Show confirmation modal with warning (Super Admin only), call respective endpoint, invalidate query cache, show success toast.
   - **Change Password**: Open password change modal, validate password (min 8 chars), call endpoint, show success toast.
5. **Error Handling**: Display error messages based on error codes, provide retry option for 500/503 errors.
