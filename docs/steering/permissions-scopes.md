# Permissions & Scopes - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El sistema de Permisos y Scopes proporciona control de acceso granular en múltiples niveles:

1. **Permission-Based Authorization**: Sistema de permisos basado en contextos
2. **Role-Based Access Control (RBAC)**: 4 roles con jerarquía (ADMIN, MODERATOR, USER, GUEST)
3. **Role Hierarchy**: Administración de roles subordinados
4. **Super Admin Protection**: Email-based super admin (no revocable)
5. **Agent Isolation**: RBAC para agentes AI con 4 roles y 8 tipos de recursos
6. **Project Tool Permissions**: Whitelisting de herramientas por proyecto
7. **Setting Scopes**: Scopes para configuración del sistema (GLOBAL, SECURITY, PAYMENTS, AI)
8. **Composite Permissions**: Permisos combinados (AnyOf)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                      PERMISSIONS & SCOPES ARCHITECTURE                                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────────┐
                    │      Permission-Based Authorization     │
                    │  (Base, Permissions, Authorize, Composite)│
                    └──────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  User RBAC      │      │  Agent RBAC     │      │  Project Scopes │
│  (4 roles)      │      │  (4 roles)      │      │  (tools)       │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│• ADMIN          │      │• ADMIN          │      │• enabled_tools  │
│• MODERATOR      │      │• PRIVILEGED     │      │• enabled_protocols│
│• USER           │      │• STANDARD       │      │• enabled_chains │
│• GUEST          │      │• READ_ONLY      │      │• risk_config    │
│                 │      │                 │      │                 │
│• Role hierarchy │      │• 8 ResourceTypes│      │• Tool executor  │
│• Subordinate mgmt│    │• Agent isolation│      │• Risk validation│
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                            │                            │
         └────────────────────────────┴────────────────────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │   Setting Scopes       │
                          │  (GLOBAL, SECURITY,    │
                          │   PAYMENTS, AI)        │
                          └────────────────────────┘
```

---

## 1. Permission-Based Authorization

### Base Permission System

**Location**: `src/app/application/common/services/authorization/base.py`

```python
@dataclass(frozen=True)
class PermissionContext:
    """Base context for permission checks."""
    pass

ContextT = TypeVar("ContextT", bound=PermissionContext)

class Permission(ABC, Generic[ContextT]):
    """Base permission class."""
    
    @abstractmethod
    def is_satisfied_by(self, context: ContextT) -> bool: ...
```

### Authorize Function

**Location**: `src/app/application/common/services/authorization/authorize.py`

```python
def authorize(
    permission: Permission,
    *,
    context: PermissionContext,
) -> None:
    """
    Authorize an action based on permission and context.
    
    Raises:
        AuthorizationError: If permission is not satisfied
    """
    if not permission.is_satisfied_by(context):
        raise AuthorizationError(AUTHZ_NOT_AUTHORIZED)
```

### Usage Example

```python
from app.application.common.services.authorization.authorize import authorize
from app.application.common.services.authorization.permissions import (
    CanManageSelf,
    CanManageSubordinate,
    UserManagementContext,
)

# Check if user can manage another user
authorize(
    AnyOf(
        CanManageSelf(),
        CanManageSubordinate(),
    ),
    context=UserManagementContext(
        subject=current_user,
        target=target_user,
    ),
)
```

---

## 2. User Role-Based Access Control (RBAC)

### UserRole Enum

**Location**: `src/app/domain/enums/user_role.py`

```python
class UserRole(StrEnum):
    """User roles in the system."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"
    
    @classmethod
    def get_hierarchy(cls, role: str) -> List[str]:
        """
        Get role hierarchy.
        
        ADMIN: [ADMIN, MODERATOR, USER, GUEST]
        MODERATOR: [MODERATOR, USER, GUEST]
        USER: [USER, GUEST]
        GUEST: [GUEST]
        """
        ...
    
    @property
    def is_assignable(self) -> bool:
        """Check if role can be assigned."""
        return self != UserRole.ADMIN
    
    @property
    def is_changeable(self) -> bool:
        """Check if role can be changed."""
        return True
```

### Role Hierarchy

**Location**: `src/app/application/common/services/authorization/role_hierarchy.py`

```python
SUBORDINATE_ROLES: Mapping[UserRole, set[UserRole]] = {
    # ADMIN can manage ALL roles including other ADMINs
    UserRole.ADMIN: {UserRole.ADMIN, UserRole.MODERATOR, UserRole.USER, UserRole.GUEST},
    UserRole.MODERATOR: {UserRole.USER, UserRole.GUEST},
    UserRole.USER: {UserRole.GUEST},
    UserRole.GUEST: set(),
}
```

### Role Permissions

| Role | Can Manage | Can Access |
|------|------------|------------|
| **ADMIN** | All roles (including other admins) | All endpoints, admin panel |
| **MODERATOR** | USER, GUEST | User management, content moderation |
| **USER** | GUEST | Standard user features |
| **GUEST** | None | Read-only, limited features |

---

## 3. Permission Types

### User Management Permissions

**Location**: `src/app/application/common/services/authorization/permissions.py`

#### CanManageSelf

```python
class CanManageSelf(Permission[UserManagementContext]):
    """Permission to manage own account."""
    
    def is_satisfied_by(self, context: UserManagementContext) -> bool:
        return context.subject == context.target
```

**Usage**: Users can change their own password, update their profile, etc.

#### CanManageSubordinate

```python
class CanManageSubordinate(Permission[UserManagementContext]):
    """Permission to manage subordinate users based on role hierarchy."""
    
    def is_satisfied_by(self, context: UserManagementContext) -> bool:
        allowed_roles = self._role_hierarchy.get(context.subject.role, set())
        return context.target.role in allowed_roles
```

**Usage**: Admins can manage all users, moderators can manage users and guests.

#### CanManageRole

```python
class CanManageRole(Permission[RoleManagementContext]):
    """Permission to assign a specific role."""
    
    def is_satisfied_by(self, context: RoleManagementContext) -> bool:
        allowed_roles = self._role_hierarchy.get(context.subject.role, set())
        return context.target_role in allowed_roles
```

**Usage**: Check if user can assign a specific role to another user.

### Permission Contexts

```python
@dataclass(frozen=True, kw_only=True)
class UserManagementContext(PermissionContext):
    """Context for user management operations."""
    subject: User  # User performing action
    target: User   # User being managed

@dataclass(frozen=True, kw_only=True)
class RoleManagementContext(PermissionContext):
    """Context for role management operations."""
    subject: User      # User performing action
    target_role: UserRole  # Role being assigned
```

---

## 4. Composite Permissions

**Location**: `src/app/application/common/services/authorization/composite.py`

### AnyOf Permission

```python
class AnyOf(Permission):
    """Composite permission: satisfied if ANY permission is satisfied."""
    
    def __init__(self, *permissions: Permission) -> None:
        self._permissions = permissions
    
    def is_satisfied_by(self, context: PermissionContext) -> bool:
        return any(p.is_satisfied_by(context) for p in self._permissions)
```

### Usage Example

```python
# User can change password if:
# 1. They are changing their own password, OR
# 2. They are an admin managing a subordinate
authorize(
    AnyOf(
        CanManageSelf(),
        CanManageSubordinate(),
    ),
    context=UserManagementContext(
        subject=current_user,
        target=target_user,
    ),
)
```

---

## 5. Super Admin Protection

### AuthService

**Location**: `src/app/domain/services/auth.py`

```python
class AuthService:
    """Domain service for authentication and authorization."""
    
    def __init__(self):
        # Support both formats: ADMIN_USER_ADMIN or USER_ADMIN
        self._super_admin_email = os.getenv("ADMIN_USER_ADMIN") or os.getenv("USER_ADMIN")
    
    def check_super_admin_permission(self, user_email: Email) -> None:
        """Check if user has super admin permissions."""
        if not self._super_admin_email or user_email.value != self._super_admin_email:
            raise InsufficientPermissionsError("Not authorized")
    
    def is_super_admin(self, email: Email) -> bool:
        """Check if user is super admin."""
        return self._super_admin_email and email.value == self._super_admin_email
```

### Super Admin Rules

1. **Email-based**: Super admin is identified by email (environment variable)
2. **Cannot be revoked**: Super admin role cannot be changed or revoked
3. **Grant/Revoke Admin**: Only super admin can grant or revoke admin roles
4. **Cannot be deactivated**: Super admin account cannot be deactivated

### Example: Grant Admin

```python
class GrantAdminInteractor:
    async def execute(self, request_data: GrantAdminRequest) -> None:
        current_user = await self._current_user_service.get_current_user()
        
        # Only super admin can grant admin
        if not self._auth_service.is_super_admin(current_user.email):
            raise AuthorizationError("Super admin privileges required.")
        
        # Protect super admin from role changes
        if self._auth_service.is_super_admin(user.email):
            raise AuthorizationError("Cannot modify super admin role.")
        
        # Grant admin role
        self._user_service.toggle_user_admin_role(user, is_admin=True)
```

---

## 6. Agent Isolation & RBAC

### AgentIsolationGuard

**Location**: `src/app/infrastructure/security/agent_isolation.py`

Sistema de permisos para agentes AI que previene acceso no autorizado a recursos.

### Agent Roles

```python
class AgentRole(str, Enum):
    """Predefined agent roles with different privilege levels."""
    READ_ONLY = "read_only"    # Read-only access
    STANDARD = "standard"       # Standard operations
    PRIVILEGED = "privileged"   # Elevated privileges
    ADMIN = "admin"             # Full system access
```

### Resource Types

```python
class ResourceType(str, Enum):
    """Types of resources that can be accessed."""
    USER_DATA = "user_data"
    SYSTEM_CONFIG = "system_config"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    WALLET = "wallet"
    AGENT_COMMUNICATION = "agent_communication"
```

### Agent Permissions

```python
@dataclass
class AgentPermission:
    """Represents a permission for an agent."""
    resource_type: ResourceType
    actions: Set[str]  # e.g., {"read", "write", "delete"}
    scope: Optional[str] = None  # e.g., "user_id:123" for user-scoped access
```

### Default Role Permissions

| Role | Permissions |
|------|-------------|
| **READ_ONLY** | Read USER_DATA, read/send AGENT_COMMUNICATION |
| **STANDARD** | Read/write USER_DATA, call EXTERNAL_API, read/send AGENT_COMMUNICATION |
| **PRIVILEGED** | Read/write/delete USER_DATA, call EXTERNAL_API, read/write DATABASE, read/send/broadcast AGENT_COMMUNICATION |
| **ADMIN** | All resources, read/write SYSTEM_CONFIG, read/write FILE_SYSTEM, read/transfer WALLET, terminate AGENT_COMMUNICATION |

### Agent Isolation Guard

```python
class AgentIsolationGuard:
    """Guards against unauthorized agent actions."""
    
    DEFAULT_ROLE_PERMISSIONS = {
        AgentRole.READ_ONLY: [
            AgentPermission(ResourceType.USER_DATA, {"read"}),
            AgentPermission(ResourceType.AGENT_COMMUNICATION, {"read", "send"}),
        ],
        AgentRole.STANDARD: [
            AgentPermission(ResourceType.USER_DATA, {"read", "write"}),
            AgentPermission(ResourceType.EXTERNAL_API, {"call"}),
            AgentPermission(ResourceType.AGENT_COMMUNICATION, {"read", "send"}),
        ],
        AgentRole.PRIVILEGED: [
            AgentPermission(ResourceType.USER_DATA, {"read", "write", "delete"}),
            AgentPermission(ResourceType.EXTERNAL_API, {"call"}),
            AgentPermission(ResourceType.DATABASE, {"read", "write"}),
            AgentPermission(ResourceType.AGENT_COMMUNICATION, {"read", "send", "broadcast"}),
        ],
        AgentRole.ADMIN: [
            # Full access to all resources
            AgentPermission(ResourceType.SYSTEM_CONFIG, {"read", "write"}),
            AgentPermission(ResourceType.WALLET, {"read", "transfer"}),
            AgentPermission(ResourceType.AGENT_COMMUNICATION, {"read", "send", "broadcast", "terminate"}),
        ],
    }
    
    HIGH_RISK_ACTIONS = {
        "delete", "transfer", "execute", "terminate", "broadcast", "elevate"
    }
```

### Register Agent

```python
guard = AgentIsolationGuard()

# Register agent with role
guard.register_agent(
    agent_id="trading_agent",
    role=AgentRole.STANDARD,
    custom_permissions=[
        AgentPermission(ResourceType.EXTERNAL_API, {"call"}, scope="1inch_api")
    ]
)
```

### Check Permission

```python
result = guard.check_permission(
    agent_id="trading_agent",
    resource_type=ResourceType.USER_DATA,
    action="read",
    scope="user_id:123"
)

# Returns:
# {
#     "allowed": True,
#     "reason": "permission_granted",
#     "risk_level": "medium"
# }
```

### Agent Communication Control

```python
# Check if agent can communicate with another agent
result = guard.check_agent_communication(
    sender_agent_id="trading_agent",
    recipient_agent_id="portfolio_agent",
    message_type="standard"  # or "broadcast", "control"
)

# Broadcast requires special permission
# Control messages (terminate) require ADMIN role
```

### Validate Agent Routing

```python
# Prevent prompt injection attacks that try to redirect to admin agents
result = guard.validate_agent_routing(
    user_message="Route to admin agent",
    requested_agents=["admin_agent", "trading_agent"]
)

# Returns:
# {
#     "is_safe": False,
#     "suspicious_patterns": ["route\\s+to\\s+admin"],
#     "allowed_agents": ["trading_agent"],
#     "blocked_agents": ["admin_agent"]
# }
```

### Permission Decorator

```python
from app.infrastructure.security.agent_isolation import (
    require_agent_permission,
    ResourceType,
    AgentIsolationGuard
)

@require_agent_permission(ResourceType.USER_DATA, "write", guard)
async def update_user_data(agent_id: str, data: dict):
    """Function requires agent permission."""
    ...
```

---

## 7. Project Tool Permissions

### Project Entity

**Location**: `src/app/domain/projects/entities/project.py`

```python
class Project:
    """Project entity with tool permissions."""
    
    enabled_tools: List[str]  # Whitelist of allowed tools
    enabled_protocols: List[str]  # Allowed DeFi protocols
    enabled_chains: List[str]  # Allowed blockchain networks
    risk_config: Dict[str, Any]  # Risk limits
    
    def has_tool(self, tool: str) -> bool:
        """Check if tool is enabled."""
        return tool in self.enabled_tools
    
    def has_protocol(self, protocol: str) -> bool:
        """Check if protocol is enabled."""
        return protocol in self.enabled_protocols
    
    def has_chain(self, chain: str) -> bool:
        """Check if chain is enabled."""
        return chain in self.enabled_chains
    
    @property
    def hunter_tools_enabled(self) -> List[str]:
        """Get enabled Hunter AI tools."""
        return [tool for tool in self.enabled_tools if tool.startswith("hunter_")]
    
    @property
    def ultra_tools_enabled(self) -> List[str]:
        """Get enabled ULTRA Arbitrage tools."""
        return [tool for tool in self.enabled_tools if tool.startswith("ultra_")]
```

### Project Tool Executor

**Location**: `src/app/application/projects/services/project_tool_executor.py`

```python
class ProjectToolExecutor:
    """Execute tools within project scope with permissions."""
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> str:
        """
        Execute tool if enabled in project and parameters pass validation.
        
        Steps:
        1. Check if project integration is enabled
        2. Check if tool is enabled in project (if tool_permissions_enabled)
        3. Validate parameters against project risk config (if risk_validation_enabled)
        4. Execute tool
        """
        # Check tool permissions
        if self.integration_settings.projects.tool_permissions_enabled:
            if not self.project.has_tool(tool_name):
                raise ToolExecutionError(
                    f"Tool '{tool_name}' is not enabled in project '{self.project.name}'"
                )
        
        # Validate risk limits
        if self.integration_settings.projects.risk_validation_enabled:
            self._validate_parameters(tool_name, parameters)
        
        # Execute tool
        ...
```

### Tool Permission Validation

**Example**:
```python
# Project configuration
project = Project(
    enabled_tools=["hunter_sentiment_analysis", "hunter_price_prediction"],
    risk_config={
        "max_risk_tolerance": 0.7,
        "max_capital_per_trade": 100000,
        "min_profit_threshold": 0.01
    }
)

# Tool execution
executor = ProjectToolExecutor(project, ...)

# ✅ Allowed: Tool is enabled
await executor.execute_tool("hunter_sentiment_analysis", {...})

# ❌ Denied: Tool not enabled
await executor.execute_tool("ultra_flash_loans", {...})
# Raises: ToolExecutionError("Tool 'ultra_flash_loans' is not enabled")
```

### Risk Validation

```python
def _validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> None:
    """Validate tool parameters against project risk configuration."""
    risk_config = self.project.risk_config
    
    # Portfolio optimization: Check max risk tolerance
    if tool_name == "hunter_portfolio_optimization":
        risk_tolerance = parameters.get("risk_tolerance", 0.5)
        max_risk = risk_config.get("max_risk_tolerance", 1.0)
        if risk_tolerance > max_risk:
            raise ToolExecutionError(f"Risk tolerance exceeds project limit")
    
    # ULTRA arbitrage: Check capital limits
    elif tool_name.startswith("ultra_"):
        capital = parameters.get("capital", 0)
        max_capital = risk_config.get("max_capital_per_trade", float('inf'))
        if capital > max_capital:
            raise ToolExecutionError(f"Capital exceeds project limit")
```

---

## 8. Setting Scopes

### SettingScope Enum

**Location**: `src/app/domain/enums/system/setting_scope.py`

```python
class SettingScope(Enum):
    """Scopes for system settings."""
    GLOBAL = 0      # Global system settings
    SECURITY = 1    # Security-related settings
    PAYMENTS = 2    # Payment/Stripe settings
    AI = 3          # AI/LLM settings
```

### Setting Entity

**Location**: `src/app/domain/entities/system/setting.py`

```python
@dataclass(eq=False, kw_only=True)
class Setting(Entity[SettingId]):
    """System setting with scope."""
    key: str
    value: Optional[str]
    scope: SettingScope
    is_sensitive: bool
    description: Optional[str]
    updated_at: UpdatedAt
    updated_by: Optional[UserId]
```

### Scope Usage

Settings are organized by scope for:
- **Access control**: Different scopes may require different permissions
- **Organization**: Group related settings together
- **Security**: Sensitive settings (e.g., API keys) in specific scopes

---

## 9. Permission Usage Examples

### Example 1: Change Password

```python
class ChangePasswordInteractor:
    async def execute(self, request_data: ChangePasswordRequest) -> None:
        current_user = await self._current_user_service.get_current_user()
        target_user = await self._user_command_gateway.read_by_email(email)
        
        # User can change own password OR admin can change subordinate's password
        authorize(
            AnyOf(
                CanManageSelf(),
                CanManageSubordinate(),
            ),
            context=UserManagementContext(
                subject=current_user,
                target=target_user,
            ),
        )
        
        self._user_service.change_password(target_user, password)
```

### Example 2: Deactivate User

```python
class DeactivateUserInteractor:
    async def execute(self, request_data: DeactivateUserRequest) -> None:
        current_user = await self._current_user_service.get_current_user()
        
        # Check if user can manage the target role
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=UserRole.USER,
            ),
        )
        
        # Check if user can manage the specific target user
        authorize(
            CanManageSubordinate(),
            context=UserManagementContext(
                subject=current_user,
                target=target_user,
            ),
        )
        
        # Prevent self-deactivation
        if user.id_ == current_user.id_:
            raise ActivationChangeNotPermittedError(...)
        
        self._user_service.toggle_user_activation(user, is_active=False)
```

### Example 3: Agent Permission Check

```python
from app.infrastructure.security.agent_isolation import (
    AgentIsolationGuard,
    AgentRole,
    ResourceType,
)

guard = AgentIsolationGuard()

# Register agent
guard.register_agent(
    agent_id="trading_agent",
    role=AgentRole.STANDARD,
)

# Check permission before action
result = guard.check_permission(
    agent_id="trading_agent",
    resource_type=ResourceType.USER_DATA,
    action="write",
)

if not result["allowed"]:
    raise PermissionError(f"Agent not authorized: {result['reason']}")

# Execute action
await update_user_data(...)
```

### Example 4: Project Tool Execution

```python
# Project with limited tools
project = Project(
    enabled_tools=["hunter_sentiment_analysis", "hunter_price_prediction"],
    risk_config={
        "max_risk_tolerance": 0.7,
        "max_capital_per_trade": 50000
    }
)

executor = ProjectToolExecutor(project, ...)

# ✅ Allowed: Tool enabled, parameters valid
await executor.execute_tool(
    "hunter_sentiment_analysis",
    {"symbol": "ETH", "timeframe": "24h"}
)

# ❌ Denied: Tool not enabled
await executor.execute_tool("ultra_flash_loans", {...})

# ❌ Denied: Parameters violate risk limits
await executor.execute_tool(
    "hunter_portfolio_optimization",
    {"risk_tolerance": 0.9}  # Exceeds max_risk_tolerance: 0.7
)
```

---

## 10. Authorization Service

### AuthService (Domain)

**Location**: `src/app/domain/services/auth.py`

```python
class AuthService:
    """Domain service for authentication and authorization."""
    
    def check_admin_permission(self, user_role: UserRole) -> None:
        """Check if user has admin permissions."""
        if user_role != UserRole.ADMIN:
            raise InsufficientPermissionsError("Only admin users can perform this action")
    
    def check_super_admin_permission(self, user_email: Email) -> None:
        """Check if user has super admin permissions."""
        if not self._super_admin_email or user_email.value != self._super_admin_email:
            raise InsufficientPermissionsError("Not authorized")
    
    def validate_role_change(self, current_role: UserRole, new_role: UserRole) -> None:
        """Validate if a role change is allowed."""
        if current_role == UserRole.ADMIN and new_role != UserRole.ADMIN:
            raise RoleChangeNotAllowedError("Cannot downgrade admin role")
```

---

## 11. Permission Enforcement Points

### 1. Application Layer (Interactors)

**Pattern**: Check permissions in interactors before executing business logic.

```python
class SomeInteractor:
    async def execute(self, request: Request) -> Response:
        current_user = await self._current_user_service.get_current_user()
        
        # Check permission
        authorize(
            CanManageSubordinate(),
            context=UserManagementContext(
                subject=current_user,
                target=target_user,
            ),
        )
        
        # Execute business logic
        ...
```

### 2. Presentation Layer (Controllers)

**Pattern**: Use `Security(bearer_scheme)` for authentication, check permissions in interactors.

```python
@router.patch("/users/{email}/password")
async def change_password(
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: ChangePasswordInteractor = Depends(),
):
    # Authentication handled by Security(bearer_scheme)
    # Authorization handled in interactor
    await interactor.execute(request)
```

### 3. Agent Actions

**Pattern**: Check agent permissions before resource access.

```python
# In agent execution
result = guard.check_permission(
    agent_id=agent_id,
    resource_type=ResourceType.USER_DATA,
    action="write",
)

if not result["allowed"]:
    raise PermissionError("Agent not authorized")
```

### 4. Project Tool Execution

**Pattern**: Validate tool permissions and risk limits before execution.

```python
# In ProjectToolExecutor
if not project.has_tool(tool_name):
    raise ToolExecutionError("Tool not enabled")

if parameters violate risk_config:
    raise ToolExecutionError("Parameters exceed risk limits")
```

---

## 12. Permission Contexts Summary

| Context | Purpose | Fields |
|---------|---------|--------|
| `UserManagementContext` | User management operations | `subject: User`, `target: User` |
| `RoleManagementContext` | Role assignment operations | `subject: User`, `target_role: UserRole` |
| `AgentPermission` | Agent resource access | `resource_type: ResourceType`, `actions: Set[str]`, `scope: Optional[str]` |

---

## 13. Permission Types Summary

| Permission | Purpose | Context |
|------------|---------|---------|
| `CanManageSelf` | User can manage own account | `UserManagementContext` |
| `CanManageSubordinate` | User can manage subordinate users | `UserManagementContext` |
| `CanManageRole` | User can assign specific role | `RoleManagementContext` |
| `AnyOf` | Composite: ANY permission satisfied | Any `PermissionContext` |

---

## 14. Role Hierarchy Matrix

| Subject Role | Can Manage Roles |
|--------------|------------------|
| **ADMIN** | ADMIN, MODERATOR, USER, GUEST |
| **MODERATOR** | USER, GUEST |
| **USER** | GUEST |
| **GUEST** | None |

---

## 15. Agent Role Permissions Matrix

| Agent Role | USER_DATA | SYSTEM_CONFIG | EXTERNAL_API | DATABASE | FILE_SYSTEM | WALLET | AGENT_COMMUNICATION |
|------------|-----------|----------------|--------------|----------|------------|--------|---------------------|
| **READ_ONLY** | Read | - | - | - | - | - | Read, Send |
| **STANDARD** | Read, Write | - | Call | - | - | - | Read, Send |
| **PRIVILEGED** | Read, Write, Delete | - | Call | Read, Write | - | - | Read, Send, Broadcast |
| **ADMIN** | Read, Write, Delete | Read, Write | Call | Read, Write, Delete | Read, Write | Read, Transfer | Read, Send, Broadcast, Terminate |

---

## 16. High-Risk Actions

**Location**: `src/app/infrastructure/security/agent_isolation.py`

```python
HIGH_RISK_ACTIONS = {
    "delete",      # Data deletion
    "transfer",    # Asset transfers
    "execute",     # Code execution
    "terminate",   # Process termination
    "broadcast",   # Broadcast messages
    "elevate",     # Privilege escalation
}
```

High-risk actions require:
- **Extra validation**: Additional checks beyond basic permission
- **Audit logging**: All high-risk actions are logged
- **Human approval**: May require manual approval (see transaction approval service)

---

## 17. Integration with Feature Flags

### Tool Permissions Feature Flag

**Location**: `src/app/setup/config/integrations.py`

```python
class ProjectIntegrationSettings(BaseModel):
    """Project integration feature flags."""
    
    tool_permissions_enabled: bool = Field(
        default=True,
        description="Enable tool permission enforcement (enabled_tools filtering)",
    )
    
    risk_validation_enabled: bool = Field(
        default=True,
        description="Enable risk limit validation (max_risk_tolerance, max_capital, etc.)",
    )
```

**Usage**:
- `tool_permissions_enabled=false`: All tools allowed (no whitelist)
- `tool_permissions_enabled=true`: Only `enabled_tools` allowed
- `risk_validation_enabled=false`: No risk limit validation
- `risk_validation_enabled=true`: Validate against `risk_config`

---

## 18. Security Considerations

### 1. Principle of Least Privilege

- **Agents**: Start with READ_ONLY role, elevate only when needed
- **Users**: Default to USER role, grant admin only when necessary
- **Projects**: Whitelist only required tools

### 2. Defense in Depth

- **Authentication**: Bearer token required
- **Authorization**: Permission checks in interactors
- **Agent Isolation**: Separate RBAC for agents
- **Project Scoping**: Tool whitelisting per project

### 3. Super Admin Protection

- **Email-based**: Cannot be changed via API
- **Immutable**: Cannot be revoked or deactivated
- **Audit**: All super admin actions logged

### 4. Agent Isolation

- **Role-based**: 4 distinct agent roles
- **Resource isolation**: Agents cannot access unauthorized resources
- **Communication control**: Prevent unauthorized agent-to-agent communication
- **Routing validation**: Prevent prompt injection to redirect to admin agents

### 5. Project Tool Permissions

- **Whitelist approach**: Only explicitly enabled tools allowed
- **Risk validation**: Parameters validated against project limits
- **Feature flags**: Can be disabled for testing/development

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Permission Base** | `application/common/services/authorization/base.py` | Permission base class |
| **Permissions** | `application/common/services/authorization/permissions.py` | Permission implementations |
| **Authorize** | `application/common/services/authorization/authorize.py` | authorize() function |
| **Composite** | `application/common/services/authorization/composite.py` | AnyOf composite |
| **Role Hierarchy** | `application/common/services/authorization/role_hierarchy.py` | SUBORDINATE_ROLES |
| **User Roles** | `domain/enums/user_role.py` | UserRole enum |
| **Auth Service** | `domain/services/auth.py` | AuthService domain service |
| **Agent Isolation** | `infrastructure/security/agent_isolation.py` | AgentIsolationGuard |
| **Project Tools** | `application/projects/services/project_tool_executor.py` | ProjectToolExecutor |
| **Project Entity** | `domain/projects/entities/project.py` | Project with tool permissions |
| **Setting Scopes** | `domain/enums/system/setting_scope.py` | SettingScope enum |
| **Authorization Error** | `application/common/exceptions/authorization.py` | AuthorizationError |

---

## Permission System Summary

| System | Type | Scope | Enforcement |
|--------|------|-------|-------------|
| **User RBAC** | Role-based | User management | Application layer (interactors) |
| **Agent RBAC** | Role-based | Agent actions | Infrastructure layer (AgentIsolationGuard) |
| **Project Tools** | Whitelist | Tool execution | Application layer (ProjectToolExecutor) |
| **Setting Scopes** | Scope-based | System settings | Domain layer (Setting entity) |
| **Super Admin** | Email-based | Admin operations | Domain layer (AuthService) |

---

## Best Practices

### 1. Always Check Permissions in Interactors

```python
# ✅ DO: Check in interactor
class MyInteractor:
    async def execute(self, request: Request) -> Response:
        current_user = await self._current_user_service.get_current_user()
        authorize(CanManageSubordinate(), context=...)
        # Execute business logic

# ❌ DON'T: Skip permission check
class MyInteractor:
    async def execute(self, request: Request) -> Response:
        # Execute without checking
        ...
```

### 2. Use Composite Permissions for OR Logic

```python
# ✅ DO: Use AnyOf for multiple conditions
authorize(
    AnyOf(
        CanManageSelf(),
        CanManageSubordinate(),
    ),
    context=UserManagementContext(...),
)

# ❌ DON'T: Check manually
if current_user == target_user or can_manage_subordinate(...):
    ...
```

### 3. Register Agents with Appropriate Roles

```python
# ✅ DO: Start with least privilege
guard.register_agent("trading_agent", role=AgentRole.STANDARD)

# ❌ DON'T: Use ADMIN role for standard agents
guard.register_agent("trading_agent", role=AgentRole.ADMIN)
```

### 4. Validate Project Tool Permissions

```python
# ✅ DO: Check tool permissions before execution
if not project.has_tool(tool_name):
    raise ToolExecutionError("Tool not enabled")

# ❌ DON'T: Execute without checking
await execute_tool(tool_name, parameters)
```

### 5. Protect Super Admin

```python
# ✅ DO: Check super admin before sensitive operations
if not self._auth_service.is_super_admin(current_user.email):
    raise AuthorizationError("Super admin required")

# ❌ DON'T: Allow regular admins to modify super admin
if current_user.role == UserRole.ADMIN:
    # Still need super admin check for grant/revoke
    ...
```

---

**Last Updated**: January 2, 2026
