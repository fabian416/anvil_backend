# User Management Module Implementation

> **Complete TypeScript/React Implementation for User Management Module**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **User Management** module provides operational tools for managing the user base and access controls. It enables administrators to oversee users, manage accounts, and handle wallet configurations.

### Key Capabilities
1. **User Operations**: List, search, filter, activate/deactivate users, manage admin roles, change passwords
2. **Wallet Management**: View and update wallet configurations from Privy, manage policies and signers
3. **Bulk Operations**: Activate/deactivate multiple users
4. **Audit Trail**: Track all user and wallet operations

### Business Value
- **User Control**: Complete control over user accounts and access
- **Security**: Manage admin privileges and account status
- **Wallet Administration**: Configure wallet policies and signers
- **Compliance**: Audit trail for regulatory requirements

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: Admins need efficient tools to manage users without information overload.

**Root Cause Analysis**:
- **Information Overload**: Too many users causes decision paralysis
- **Solution**: Search-first interface, pagination, filters, progressive disclosure

**Design Decisions**:
1. **Search First**: Primary interface is a search bar + table
2. **Safety**: Destructive actions require confirmation
3. **Progressive Disclosure**: Summary → Details → Actions
4. **Batch Operations**: Support bulk actions for efficiency

### Trade-off Analysis (Design Thinking)

**Key Design Decisions with Trade-offs**:

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Table Layout** | Card Layout | Density vs. Readability | Tables show more data, but cards are more readable |
| **Email as Identifier** | UUID | Human-readable vs. Stability | Email is more user-friendly, but UUIDs are more stable |
| **Confirmation Modals** | Direct Actions | Safety vs. Speed | Confirmations prevent mistakes, but slow down operations |
| **Pagination** | Infinite Scroll | Performance vs. UX | Pagination handles large lists better, but requires more clicks |

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│              User Management                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Search Bar: [________________] [🔍] [Filter]     │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ User Table                                         │  │
│  │ ┌──────┬──────────┬────────┬──────┬────────────┐ │  │
│  │ │Email │ Status   │ Role   │ Date │ Actions   │ │  │
│  │ ├──────┼──────────┼────────┼──────┼────────────┤ │  │
│  │ │user@ │ 🟢 Active│ User   │ ...  │ [⋮]       │ │  │
│  │ │admin@│ 🟢 Active│ Admin  │ ...  │ [⋮]       │ │  │
│  │ └──────┴──────────┴────────┴──────┴────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Pagination: [<] 1 2 3 [>]                         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Color Palette
- **Active Status**: `#10B981` (Green)
- **Inactive Status**: `#6B7280` (Gray)
- **Admin Role**: `#8B5CF6` (Purple)
- **Warning**: `#F59E0B` (Amber) - For destructive actions
- **Error**: `#EF4444` (Red) - For errors
- **Background**: `#FFFFFF` (White)
- **Table Row Hover**: `#F9FAFB` (Gray-50)

#### Typography
- **Page Title**: Inter, 700 weight, 32px
- **Table Headers**: Inter, 600 weight, 14px
- **Table Body**: Inter, 400 weight, 14px
- **Status Badges**: Inter, 500 weight, 12px
- **Action Buttons**: Inter, 500 weight, 14px

#### Component Specifications

##### User Table Component
```typescript
interface UserTableProps {
  users: User[];
  loading?: boolean;
  onUserAction: (action: UserAction, user: User) => void;
  onSort: (field: string, order: 'ASC' | 'DESC') => void;
  sortField?: string;
  sortOrder?: 'ASC' | 'DESC';
}

interface User {
  id: string;                            // UUID
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;                    // ISO 8601
}

type UserAction = 'activate' | 'deactivate' | 'grant_admin' | 'revoke_admin' | 'change_password' | 'view_details';

export const UserTable: React.FC<UserTableProps> = ({
  users,
  loading,
  onUserAction,
  onSort,
  sortField,
  sortOrder,
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => onSort('email', sortField === 'email' && sortOrder === 'ASC' ? 'DESC' : 'ASC')}
            >
              Email {sortField === 'email' && (sortOrder === 'ASC' ? '↑' : '↓')}
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Role
            </th>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
              onClick={() => onSort('created_at', sortField === 'created_at' && sortOrder === 'ASC' ? 'DESC' : 'ASC')}
            >
              Joined {sortField === 'created_at' && (sortOrder === 'ASC' ? '↑' : '↓')}
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {loading ? (
            <tr>
              <td colSpan={5} className="px-6 py-4">
                <LoadingSpinner />
              </td>
            </tr>
          ) : users.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                No users found
              </td>
            </tr>
          ) : (
            users.map((user) => (
              <UserTableRow
                key={user.id}
                user={user}
                onAction={onUserAction}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
```

##### Status Badge Component
```typescript
interface StatusBadgeProps {
  status: 'active' | 'inactive';
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
}) => {
  const styles = {
    active: 'bg-emerald-100 text-emerald-800',
    inactive: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
      <span className={`w-2 h-2 rounded-full mr-1.5 ${status === 'active' ? 'bg-emerald-500' : 'bg-gray-400'}`} />
      {label || (status === 'active' ? 'Active' : 'Inactive')}
    </span>
  );
};
```

##### Confirmation Modal Component
```typescript
interface ConfirmationModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'info';
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  title,
  message,
  confirmLabel,
  cancelLabel = 'Cancel',
  variant = 'info',
  onConfirm,
  onCancel,
  loading = false,
}) => {
  if (!isOpen) return null;

  const variantStyles = {
    danger: 'bg-red-600 hover:bg-red-700',
    warning: 'bg-amber-500 hover:bg-amber-600',
    info: 'bg-blue-600 hover:bg-blue-700',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onCancel} />
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
          <p className="text-sm text-gray-500 mb-6">{message}</p>
          <div className="flex justify-end space-x-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={loading}
            >
              {cancelLabel}
            </button>
            <button
              onClick={onConfirm}
              className={`px-4 py-2 text-sm font-medium text-white rounded-md ${variantStyles[variant]} disabled:opacity-50`}
              disabled={loading}
            >
              {loading ? <LoadingSpinner size="sm" /> : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
```

##### Search Bar Component
```typescript
interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onFilterClick?: () => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  placeholder = 'Search users...',
  onFilterClick,
}) => {
  return (
    <div className="flex items-center space-x-2 mb-4">
      <div className="relative flex-1">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>
      {onFilterClick && (
        <button
          onClick={onFilterClick}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Filter
        </button>
      )}
    </div>
  );
};
```

### Responsive Breakpoints

**Mobile** (< 640px):
- Single column layout
- Stacked search and filters
- Horizontal scroll for table
- Bottom sheet for actions

**Tablet** (640px - 1024px):
- Two-column layout
- Full table width
- Side panel for user details

**Desktop** (> 1024px):
- Full table layout
- Sidebar for filters
- Modal for user details

### Accessibility Requirements

1. **Screen Readers**:
   - Announce table headers
   - Describe user status and role
   - Announce action results
   - Label all form inputs

2. **Keyboard Navigation**:
   - Tab through table rows
   - Enter to open action menu
   - Escape to close modals
   - Arrow keys for table navigation

3. **Color Contrast**:
   - All text: 4.5:1 minimum
   - Status badges: 3:1 minimum
   - Action buttons: 4.5:1

### Loading States

**Initial Load**:
- Skeleton loaders for table rows
- Shimmer effect for table
- Progressive loading

**Data Refresh**:
- Subtle loading indicator
- No full page reload
- Optimistic updates where possible

### Empty States

**No Users Found**:
- Illustration: Empty user list
- Message: "No users found matching your search"
- CTA: "Clear filters" or "Adjust search"

**No Wallets**:
- Message: "No wallets found for this user"
- CTA: "View User Details"

### Error States

**API Error**:
- Error message above table
- Message: "Unable to load users"
- Retry button
- Last known data (if available)

**Validation Error**:
- Inline field errors
- Highlight invalid fields
- Show error message

---

## 🔌 API Endpoints

### 1. List Users

**Method**: `GET`  
**Endpoint**: `/api/admin/users/`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Users per page | `20` |
| `offset` | `number` | No | Pagination offset | `0` |
| `sorting_field` | `string` | No | Field to sort by | `email` |
| `sorting_order` | `string` | No | Sort order | `ASC` |

#### Response

##### Success Response (200 OK)
```typescript
interface ListUsersResponse {
  items: User[];
  total: number;
  limit: number;
  offset: number;
}
```

---

### 2. Activate User

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/activate`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

#### Response

##### Success Response (204 No Content)
No response body

---

### 3. Deactivate User

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/deactivate`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

#### Response

##### Success Response (204 No Content)
No response body

---

### 4. Grant Admin Role

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/grant-admin`  
**Auth Required**: Yes (Bearer Token - Super Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

#### Response

##### Success Response (204 No Content)
No response body

---

### 5. Revoke Admin Role

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/revoke-admin`  
**Auth Required**: Yes (Bearer Token - Super Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

#### Response

##### Success Response (204 No Content)
No response body

---

### 6. Change User Password

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/password`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

##### Request Body
```typescript
interface ChangePasswordRequest {
  password: string;                      // Required: New password (min 8 chars)
}
```

#### Response

##### Success Response (204 No Content)
No response body

---

### 7. Get Wallet Details

**Method**: `GET`  
**Endpoint**: `/api/admin/wallets/{privy_wallet_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `privy_wallet_id` | `string` | **Yes** | Privy wallet identifier |

#### Response

##### Success Response (200 OK)
```typescript
interface AdminWalletDetailsResponse {
  local_wallet_id: number | null;
  privy_wallet_id: string;
  address: string;
  chain_type: string;
  user_id: number | null;
  owner_type: string | null;
  owner_id: string | null;
  policy_ids: string[];
  additional_signers: AdditionalSignerResponse[];
  provider: string;
  status: string;
  created_at: string;                   // ISO 8601
  updated_at: string;                   // ISO 8601
}
```

---

### 8. Update Wallet

**Method**: `PATCH`  
**Endpoint**: `/api/admin/wallets/{privy_wallet_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `privy_wallet_id` | `string` | **Yes** | Privy wallet identifier |

##### Request Body
```typescript
interface UpdateWalletRequest {
  policy_ids?: string[];
  owner?: { [key: string]: any };
  owner_id?: string;
  additional_signers?: AdditionalSignerRequest[];
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface UpdateWalletResponse {
  success: boolean;
  changes_applied: {
    policy_ids?: string[];
    owner?: { [key: string]: any };
    additional_signers?: AdditionalSignerResponse[];
  };
  privy_wallet_id: string;
  updated_at: string;                    // ISO 8601
}
```

---

## 🔄 User Flows & Use Cases

### Use Case 1: List and Search Users

**Actor**: Admin User  
**Goal**: Find and view user information  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to `/admin/users`
2. **Initial State**: 
   - User list loads
   - Show loading skeleton
   - Call `GET /api/admin/users/` with default pagination
3. **System Response**:
   - Display user table with pagination
   - Show total count
   - Display status badges and role badges
4. **User Action**: User types in search bar
5. **System Response**:
   - Debounce search (300ms)
   - Call API with search query
   - Update table with filtered results
6. **User Action**: User clicks column header to sort
7. **System Response**:
   - Update sort parameters
   - Refetch data with new sort order
   - Update table display
8. **Success Path**:
   - Users display correctly
   - Search works smoothly
   - Sorting works correctly
   - Pagination works
9. **Error Path**:
   - If API error: Show error message + Retry button
   - If no results: Show empty state

#### Flow Diagram
```
[Admin] → [User Management]
         ↓
    [Load Users]
         ↓
    ┌────────────┐
    │ Has Users? │ → No → [Empty State]
    └────────────┘
         ↓ Yes
    [Display Table]
         ↓
    [User Searches]
         ↓
    [Filter Results]
         ↓
    [User Sorts]
         ↓
    [Update Display]
```

#### Success Criteria
- [ ] User list loads in < 2 seconds
- [ ] Search is responsive (< 500ms debounce)
- [ ] Sorting works correctly
- [ ] Pagination works smoothly
- [ ] Error states are clear

---

### Use Case 2: Activate/Deactivate User

**Actor**: Admin User  
**Goal**: Change user account status  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User clicks action menu (⋮) on a user row
2. **Initial State**: 
   - Action menu opens
   - Show available actions (Activate/Deactivate)
3. **User Action**: User clicks "Deactivate User"
4. **System Response**:
   - Show confirmation modal
   - Display warning message
5. **User Action**: User confirms action
6. **System Response**:
   - Call `PATCH /api/admin/users/{email}/deactivate`
   - Show loading state
   - Optimistically update UI
7. **System Response**:
   - On success: Update status badge, show success toast
   - On error: Show error message, revert optimistic update
8. **Success Path**:
   - User status updates correctly
   - Table reflects new status
   - Success message displayed

#### Success Criteria
- [ ] Confirmation modal is clear
- [ ] Action completes successfully
- [ ] UI updates immediately
- [ ] Error handling works

---

### Use Case 3: View and Update Wallet

**Actor**: Admin User  
**Goal**: View wallet details and update configuration  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to wallet details or clicks "View Wallet"
2. **Initial State**: 
   - Wallet details load
   - Show loading skeleton
   - Call `GET /api/admin/wallets/{privy_wallet_id}`
3. **System Response**:
   - Display wallet information
   - Show policy IDs
   - Show additional signers
   - Show owner information
4. **User Action**: User clicks "Edit Wallet"
5. **System Response**:
   - Open edit modal/form
   - Pre-populate with current values
6. **User Action**: User updates policy IDs
7. **System Response**:
   - Validate input
   - Show save button
8. **User Action**: User clicks "Save"
9. **System Response**:
   - Call `PATCH /api/admin/wallets/{privy_wallet_id}`
   - Show loading state
10. **System Response**:
    - On success: Update display, show success message
    - On error: Show error message with details

#### Success Criteria
- [ ] Wallet details load correctly
- [ ] Edit form works smoothly
- [ ] Validation works
- [ ] Update completes successfully

---

## 📁 File Structure

```
src/modules/admin/user-management/
├── UserManagement.tsx
├── UserManagement.types.ts
├── UserManagement.hooks.ts
├── UserManagement.service.ts
├── components/
│   ├── UserTable.tsx
│   ├── UserTableRow.tsx
│   ├── StatusBadge.tsx
│   ├── RoleBadge.tsx
│   ├── SearchBar.tsx
│   ├── UserFilters.tsx
│   ├── UserActionMenu.tsx
│   ├── ConfirmationModal.tsx
│   ├── ChangePasswordModal.tsx
│   ├── WalletDetails.tsx
│   ├── WalletEditForm.tsx
│   └── Pagination.tsx
├── hooks/
│   ├── useUsers.ts
│   ├── useUserActions.ts
│   ├── useWalletDetails.ts
│   └── useWalletUpdate.ts
├── services/
│   ├── user.service.ts
│   └── wallet.service.ts
└── __tests__/
    ├── UserManagement.test.tsx
    ├── UserTable.test.tsx
    └── services.test.ts
```

## 🔑 Key Implementation Files

### 1. User Management Module

#### `UserManagement.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type {
  ListUsersResponse,
  User,
  AdminWalletDetailsResponse,
  UpdateWalletRequest,
  UpdateWalletResponse,
} from './UserManagement.types';

export const userManagementService = {
  async listUsers(params: {
    limit?: number;
    offset?: number;
    sorting_field?: string;
    sorting_order?: 'ASC' | 'DESC';
  }): Promise<ListUsersResponse> {
    const response = await apiClient.get<ListUsersResponse>(
      '/api/admin/users/',
      { params }
    );
    return response.data;
  },

  async activateUser(email: string): Promise<void> {
    await apiClient.patch(`/api/admin/users/${email}/activate`);
  },

  async deactivateUser(email: string): Promise<void> {
    await apiClient.patch(`/api/admin/users/${email}/deactivate`);
  },

  async grantAdmin(email: string): Promise<void> {
    await apiClient.patch(`/api/admin/users/${email}/grant-admin`);
  },

  async revokeAdmin(email: string): Promise<void> {
    await apiClient.patch(`/api/admin/users/${email}/revoke-admin`);
  },

  async changePassword(email: string, password: string): Promise<void> {
    await apiClient.patch(`/api/admin/users/${email}/password`, { password });
  },

  async getWalletDetails(privyWalletId: string): Promise<AdminWalletDetailsResponse> {
    const response = await apiClient.get<AdminWalletDetailsResponse>(
      `/api/admin/wallets/${privyWalletId}`
    );
    return response.data;
  },

  async updateWallet(
    privyWalletId: string,
    data: UpdateWalletRequest
  ): Promise<UpdateWalletResponse> {
    const response = await apiClient.patch<UpdateWalletResponse>(
      `/api/admin/wallets/${privyWalletId}`,
      data
    );
    return response.data;
  },
};
```

#### `UserManagement.types.ts`
```typescript
export interface User {
  id: string;                            // UUID
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;                    // ISO 8601
}

export interface ListUsersResponse {
  items: User[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminWalletDetailsResponse {
  local_wallet_id: number | null;
  privy_wallet_id: string;
  address: string;
  chain_type: string;
  user_id: number | null;
  owner_type: string | null;
  owner_id: string | null;
  policy_ids: string[];
  additional_signers: AdditionalSignerResponse[];
  provider: string;
  status: string;
  created_at: string;                   // ISO 8601
  updated_at: string;                   // ISO 8601
}

export interface AdditionalSignerResponse {
  signer_id: string;
  override_policy_ids: string[] | null;
}

export interface UpdateWalletRequest {
  policy_ids?: string[];
  owner?: { [key: string]: any };
  owner_id?: string;
  additional_signers?: AdditionalSignerRequest[];
}

export interface AdditionalSignerRequest {
  signer_id: string;
  override_policy_ids?: string[] | null;
}

export interface UpdateWalletResponse {
  success: boolean;
  changes_applied: {
    policy_ids?: string[];
    owner?: { [key: string]: any };
    additional_signers?: AdditionalSignerResponse[];
  };
  privy_wallet_id: string;
  updated_at: string;                    // ISO 8601
}
```

#### `UserManagement.hooks.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userManagementService } from './UserManagement.service';
import type { User, ListUsersResponse } from './UserManagement.types';

export function useUsers(params: {
  limit?: number;
  offset?: number;
  sorting_field?: string;
  sorting_order?: 'ASC' | 'DESC';
}) {
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => userManagementService.listUsers(params),
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true,
  });
}

export function useActivateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (email: string) => userManagementService.activateUser(email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useDeactivateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (email: string) => userManagementService.deactivateUser(email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useGrantAdmin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (email: string) => userManagementService.grantAdmin(email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useRevokeAdmin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (email: string) => userManagementService.revokeAdmin(email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useChangePassword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      userManagementService.changePassword(email, password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useWalletDetails(privyWalletId: string | null) {
  return useQuery({
    queryKey: ['admin', 'wallets', privyWalletId],
    queryFn: () => userManagementService.getWalletDetails(privyWalletId!),
    enabled: !!privyWalletId,
    staleTime: 60000, // 1 minute
  });
}

export function useUpdateWallet() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      privyWalletId,
      data,
    }: {
      privyWalletId: string;
      data: UpdateWalletRequest;
    }) => userManagementService.updateWallet(privyWalletId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['admin', 'wallets', variables.privyWalletId],
      });
    },
  });
}
```

#### `UserManagement.tsx`
```typescript
'use client';

import React, { useState, useMemo } from 'react';
import { useUsers } from './UserManagement.hooks';
import { UserTable } from './components/UserTable';
import { SearchBar } from './components/SearchBar';
import { Pagination } from './components/Pagination';
import { LoadingSpinner } from '@/design-system/components/LoadingSpinner';
import { ErrorMessage } from '@/design-system/components/ErrorMessage';

export const UserManagement: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [sortField, setSortField] = useState('email');
  const [sortOrder, setSortOrder] = useState<'ASC' | 'DESC'>('ASC');
  const limit = 20;

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useUsers({
    limit,
    offset: (page - 1) * limit,
    sorting_field: sortField,
    sorting_order: sortOrder,
  });

  // Client-side search filtering (or implement server-side search)
  const filteredUsers = useMemo(() => {
    if (!data?.items) return [];
    if (!searchQuery) return data.items;
    
    return data.items.filter((user) =>
      user.email.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [data?.items, searchQuery]);

  const handleSort = (field: string, order: 'ASC' | 'DESC') => {
    setSortField(field);
    setSortOrder(order);
    setPage(1); // Reset to first page on sort
  };

  const handleUserAction = (action: string, user: User) => {
    // Handle user actions (activate, deactivate, etc.)
    // Implementation depends on action type
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />;
  }

  return (
    <div className="user-management-container p-6">
      <h1 className="text-3xl font-bold mb-6">User Management</h1>

      <SearchBar
        value={searchQuery}
        onChange={setSearchQuery}
        placeholder="Search users by email..."
      />

      <UserTable
        users={filteredUsers}
        loading={isLoading}
        onUserAction={handleUserAction}
        onSort={handleSort}
        sortField={sortField}
        sortOrder={sortOrder}
      />

      {data && (
        <Pagination
          currentPage={page}
          totalPages={Math.ceil(data.total / limit)}
          onPageChange={setPage}
        />
      )}
    </div>
  );
};
```

## 📝 Complete File List

### User Management Module
- [ ] `UserManagement.tsx` - Main component
- [ ] `UserManagement.types.ts` - TypeScript interfaces
- [ ] `UserManagement.hooks.ts` - React hooks
- [ ] `UserManagement.service.ts` - API service
- [ ] `components/UserTable.tsx` - User table component
- [ ] `components/UserTableRow.tsx` - Table row component
- [ ] `components/StatusBadge.tsx` - Status badge component
- [ ] `components/RoleBadge.tsx` - Role badge component
- [ ] `components/SearchBar.tsx` - Search bar component
- [ ] `components/UserFilters.tsx` - Filter component
- [ ] `components/UserActionMenu.tsx` - Action menu component
- [ ] `components/ConfirmationModal.tsx` - Confirmation modal
- [ ] `components/ChangePasswordModal.tsx` - Password change modal
- [ ] `components/WalletDetails.tsx` - Wallet details view
- [ ] `components/WalletEditForm.tsx` - Wallet edit form
- [ ] `components/Pagination.tsx` - Pagination component
- [ ] `hooks/useUsers.ts` - Users list hook
- [ ] `hooks/useUserActions.ts` - User actions hook
- [ ] `hooks/useWalletDetails.ts` - Wallet details hook
- [ ] `hooks/useWalletUpdate.ts` - Wallet update hook
- [ ] `services/user.service.ts` - User service
- [ ] `services/wallet.service.ts` - Wallet service
- [ ] `__tests__/UserManagement.test.tsx` - Component tests
- [ ] `__tests__/UserTable.test.tsx` - Component tests
- [ ] `__tests__/services.test.ts` - Service tests

---

## 🧪 Testing Requirements

### Unit Tests

**User Management Component**:
- [ ] Renders user table correctly
- [ ] Displays search bar
- [ ] Handles pagination
- [ ] Handles sorting
- [ ] Shows loading states
- [ ] Displays error states

**User Table Component**:
- [ ] Renders user rows correctly
- [ ] Displays status badges
- [ ] Displays role badges
- [ ] Handles sort clicks
- [ ] Shows action menu

**Status Badge Component**:
- [ ] Renders with correct colors
- [ ] Shows correct label
- [ ] Handles active/inactive states

**Confirmation Modal**:
- [ ] Renders with correct variant
- [ ] Handles confirm action
- [ ] Handles cancel action
- [ ] Shows loading state

**Services**:
- [ ] Calls correct API endpoints
- [ ] Handles query parameters
- [ ] Parses response correctly
- [ ] Handles errors (401, 403, 404, 502, 503)

### Integration Tests

**User Management Flow**:
- [ ] Load user list
- [ ] Search users
- [ ] Sort users
- [ ] Paginate through users
- [ ] Activate/deactivate user
- [ ] Grant/revoke admin role
- [ ] Change user password

**Wallet Management Flow**:
- [ ] Load wallet details
- [ ] Edit wallet configuration
- [ ] Update policy IDs
- [ ] Add/remove additional signers
- [ ] Handle Privy API errors

### E2E Tests

**User Management Journey**:
- [ ] Login as admin → View user list
- [ ] Search for user
- [ ] Activate user
- [ ] View wallet details
- [ ] Update wallet configuration
- [ ] Handle errors gracefully

### Performance Tests

- [ ] User list loads in < 2 seconds
- [ ] Search is responsive (< 500ms)
- [ ] Table renders smoothly with 100+ users
- [ ] Pagination works efficiently
- [ ] Wallet details load in < 1 second

### Accessibility Tests

- [ ] Screen reader announces table headers
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG 2.1 AA
- [ ] All interactive elements are focusable
- [ ] Modals are accessible

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **Email-Based Identification**
   - **Risk**: Email changes cause confusion
   - **Mitigation**: Use UUID internally, display email for readability
   - **Validation**: Test with email changes

2. **Destructive Actions**
   - **Risk**: Accidental deactivation or admin revocation
   - **Mitigation**: Confirmation modals, audit trail
   - **Validation**: Test confirmation flows

3. **Privy API Dependency**
   - **Risk**: External API failures affect wallet operations
   - **Mitigation**: Error handling, retry logic, fallback UI
   - **Validation**: Test with Privy API failures

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **No Client-Side Search**
   - **Debt**: All searches hit API
   - **Cost**: High API load, slow search
   - **Prevention**: Implement debounced search with client-side filtering for small lists

2. **No Optimistic Updates**
   - **Debt**: UI feels slow
   - **Cost**: Poor user experience
   - **Prevention**: Implement optimistic updates with rollback on error

3. **Hardcoded Pagination**
   - **Debt**: Cannot adjust page size
   - **Cost**: Limited flexibility
   - **Prevention**: Configurable page size with user preference

### Validation & Testing Strategy

**Module-Specific Success Criteria**:
- ✅ User list loads in < 2 seconds (p95)
- ✅ Search is responsive (< 500ms debounce)
- ✅ User actions complete in < 1 second
- ✅ Wallet operations complete in < 2 seconds
- ✅ Error recovery rate > 95%
- ✅ Accessibility score: 100/100 (WCAG 2.1 AA)

**Module-Specific Test Requirements**:
- **Unit Tests**: Component rendering, state management, service functions
- **Integration Tests**: API integration, user operations, wallet operations
- **E2E Tests**: Complete user management flow, wallet configuration flow
- **Performance Tests**: Load with 1000+ users, search performance, pagination
- **Accessibility Tests**: Screen reader navigation, keyboard shortcuts, color contrast

**Failure Detection & Monitoring**:
- Monitor API response times (alert if p95 > 2s)
- Track error rates (alert if > 1%)
- Alert on Privy API failures (502 errors)
- Monitor user operation success rates
- Track wallet update success rates
- Log all user and wallet operations for audit trail

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/admin/user/list_users.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/user/activate_user.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/wallet/get_wallet_details.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/wallet/update_wallet.py`
- **Domain Entities**: `src/app/domain/user/entities/user.py`
- **API Documentation**: `02-User-Management/API.md`
- **UI/UX Design**: `02-User-Management/UI_UX.md`
- **Related Modules**: 
  - Admin Overview (user metrics)
  - Security Dashboard (user security)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.
