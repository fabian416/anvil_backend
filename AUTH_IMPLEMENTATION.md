# Auth Module Implementation

This document describes the implementation of the auth module in the hexagonal architecture, based on the original `authorization_controller.py` from the baseapi project.

## Overview

The auth module has been implemented across all layers of the hexagonal architecture, providing authentication and authorization functionality with proper separation of concerns.

## Architecture Layers

### Domain Layer

**Entities** (`src/app/domain/entities/auth.py`):
- `AuthContext`: Represents the authentication context for a request
- `RoleChangeRequest`: Represents a request to change a user's role

**Exceptions** (`src/app/domain/exceptions/auth.py`):
- `InvalidAuthorizationHeaderError`: Raised when authorization header is invalid
- `UnauthorizedAccessError`: Raised for unauthorized access attempts
- `InsufficientPermissionsError`: Raised when user lacks required permissions
- `RoleChangeNotAllowedError`: Raised when role change is not allowed

**Ports** (`src/app/domain/ports/auth_gateway.py`):
- `AuthGateway`: Interface for auth-related operations including token validation, user retrieval, and role updates

**Services** (`src/app/domain/services/auth.py`):
- `AuthService`: Domain service containing business logic for authentication and authorization

### Application Layer

**Commands** (`src/app/application/commands/auth/`):
- `UpgradeToAdminInteractor`: Handles upgrading a user to admin role (super admin only)
- `ChangeRoleInteractor`: Handles changing user roles (admin users only)

### Infrastructure Layer

**Adapters** (`src/app/infrastructure/auth/adapters/`):
- `AuthGatewaySqla`: SQLAlchemy implementation of the auth gateway

**Handlers** (`src/app/infrastructure/auth/handlers/`):
- `JwtHandler`: JWT token operations wrapper

### Presentation Layer

**Controllers** (`src/app/presentation/http/controllers/auth/`):
- `upgrade_to_admin.py`: HTTP endpoint for upgrading users to admin
- `change_role.py`: HTTP endpoint for changing user roles
- `router.py`: Main auth router that combines all auth endpoints

**Schemas** (`src/app/presentation/http/schemas/`):
- `UserResponse`: Response schema for user data

## Key Features

### 1. Upgrade to Admin (`POST /auth/upgrade-to-admin`)
- **Access**: Only super admin (USER_ADMIN environment variable)
- **Functionality**: Upgrades the current user to admin role
- **Validation**: Checks authorization header and super admin permissions

### 2. Change Role (`POST /auth/change-role`)
- **Access**: Admin users only
- **Functionality**: Changes a target user's role
- **Validation**: Validates authorization, admin permissions, and role validity
- **Request Body**: `{"email": "user@example.com", "new_role": "moderator"}`

## Dependency Injection

The auth module is properly integrated into the dependency injection system:

### Application Layer (`src/app/setup/ioc/application.py`)
- `AuthService` registered as a service
- `UpgradeToAdminInteractor` and `ChangeRoleInteractor` registered as commands

### Infrastructure Layer (`src/app/setup/ioc/infrastructure.py`)
- `AuthGatewaySqla` registered as the auth gateway implementation
- `JwtHandler` registered as a concrete object

## Error Handling

The implementation includes comprehensive error handling:

- **401 Unauthorized**: Invalid authorization header or authentication failure
- **403 Forbidden**: Insufficient permissions or authorization failure
- **404 Not Found**: User not found
- **400 Bad Request**: Invalid role or request data
- **503 Service Unavailable**: Database or infrastructure errors

## Security Features

1. **Token Validation**: All endpoints validate JWT tokens
2. **Role-Based Access Control**: Different endpoints require different permission levels
3. **Super Admin Protection**: Critical operations require super admin privileges
4. **Input Validation**: All inputs are validated at multiple layers

## Usage Examples

### Upgrade to Admin
```bash
curl -X POST "http://localhost:8000/api/v1/auth/upgrade-to-admin" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json"
```

### Change User Role
```bash
curl -X POST "http://localhost:8000/api/v1/auth/change-role" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "new_role": "moderator"
  }'
```

## Migration from BaseAPI

This implementation maintains the same functionality as the original `authorization_controller.py` while:

1. **Separating Concerns**: Each layer has a specific responsibility
2. **Improving Testability**: Dependencies are injected and interfaces are defined
3. **Enhancing Maintainability**: Clear separation between business logic and infrastructure
4. **Following Hexagonal Architecture**: Proper use of ports, adapters, and domain services

## Configuration

The auth module uses the following environment variables:
- `USER_ADMIN`: Email of the super admin user (required for upgrade-to-admin functionality)

## Testing

The implementation is designed to be easily testable with:
- Clear interfaces for mocking
- Separated business logic from infrastructure
- Comprehensive error handling for test scenarios
