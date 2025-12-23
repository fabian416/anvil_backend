# Admin Module: User Management

> **Technical Specification**: `FRONTEND_ADMIN_USERS_MAIN`
> **Backend Controllers**: `admin/user/list_users.py`, `admin/user/activate_user.py`
> **Base URL**: `/api/admin/users`

## 📖 Overview
The **User Management** module enables administrators to oversee the user base. It provides search, filtering, and status management capabilities (Active/Inactive), along with role assignment (Grant/Revoke Admin).

### Key Capabilities
1.  **User Roster**: Paginated list of all users with sorting.
2.  **Status Control**: Activate or Deactivate user accounts.
3.  **Role Management**: Promote users to Admin status.

---

## 🔌 API Endpoints

### 1. List Users
**GET** `/api/admin/users/`
Retrieve a paginated list of users.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `limit` | `int` | No | Users per page (Default: 20, Min: 1). |
| `offset` | `int` | No | Pagination offset (Default: 0). |
| `sorting_field` | `str` | No | Field to sort by (Default: "email"). |
| `sorting_order` | `str` | No | `ASC` or `DESC` (Default: ASC). |

**Response (`ListUsersResponse`)**:
```json
{
  "items": [
    {
      "id": "user-uuid",
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

### 2. Activate User
**PATCH** `/api/admin/users/{email}/activate`
Enable a user account that was previously inactive or pending.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `email` | `str` | **Yes** | Email of the user to activate (in URL). |

**Response**: `204 No Content`

### 3. Deactivate User
**PATCH** `/api/admin/users/{email}/deactivate`
Suspend a user account.

**Response**: `204 No Content`

### 4. Grant Admin Role
**POST** `/api/admin/users/{email}/grant-admin`
Promote a standard user to Administrator.

**Response**: `204 No Content`

### 5. Revoke Admin Role
**POST** `/api/admin/users/{email}/revoke-admin`
Demote an Administrator to standard user.

**Response**: `204 No Content`

---

## 🎨 UI/UX Guidelines

### User Table
- **Columns**: Name, Email, Status (Badge), Role (Badge), Joined Date, Actions.
- **Badges**:
    - **Active**: Green dot or badge.
    - **Inactive**: Grey dot or badge.
    - **Admin**: Purple badge.
- **Actions**: "Kebab" menu (three dots) on the right of each row containing "Activate/Deactivate", "Promote to Admin".

### Confirmation
- **Destructive Actions**: Revoking admin status or deactivating a user MUST require a confirmation modal ("Are you sure you want to deactivate user X?").
