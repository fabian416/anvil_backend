"""
Agent Isolation Guards

Ensures proper isolation and privilege controls for multi-agent systems.
Prevents agents from accessing unauthorized resources or performing
unauthorized actions.

OWASP Reference: OWASP LLM Top 10 - LLM08: Excessive Agency
Security Testing Guide: llm-security-auditor patterns
"""

from typing import Dict, Any, List, Set, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Predefined agent roles with different privilege levels"""
    READ_ONLY = "read_only"
    STANDARD = "standard"
    PRIVILEGED = "privileged"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """Types of resources that can be accessed"""
    USER_DATA = "user_data"
    SYSTEM_CONFIG = "system_config"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    WALLET = "wallet"
    AGENT_COMMUNICATION = "agent_communication"


@dataclass
class AgentPermission:
    """Represents a permission for an agent"""
    resource_type: ResourceType
    actions: Set[str]  # e.g., {"read", "write", "delete"}
    scope: Optional[str] = None  # e.g., "user_id:123" for user-scoped access


class AgentIsolationGuard:
    """
    Guards against unauthorized agent actions and resource access.

    Implements:
    - Role-based access control (RBAC) for agents
    - Resource isolation between agents
    - Action whitelisting
    - Cross-agent communication controls
    """

    # Default permissions for each role
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
            AgentPermission(ResourceType.USER_DATA, {"read", "write", "delete"}),
            AgentPermission(ResourceType.SYSTEM_CONFIG, {"read", "write"}),
            AgentPermission(ResourceType.EXTERNAL_API, {"call"}),
            AgentPermission(ResourceType.DATABASE, {"read", "write", "delete"}),
            AgentPermission(ResourceType.FILE_SYSTEM, {"read", "write"}),
            AgentPermission(ResourceType.WALLET, {"read", "transfer"}),
            AgentPermission(ResourceType.AGENT_COMMUNICATION, {"read", "send", "broadcast", "terminate"}),
        ],
    }

    # Dangerous actions that always require extra validation
    HIGH_RISK_ACTIONS = {
        "delete",
        "transfer",
        "execute",
        "terminate",
        "broadcast",
        "elevate",
    }

    def __init__(self, enabled: bool = True, enforce_isolation: bool = True):
        """
        Initialize Agent Isolation Guard.

        Args:
            enabled: Whether isolation is enabled
            enforce_isolation: Strictly enforce isolation (block unauthorized actions)
        """
        self.enabled = enabled
        self.enforce_isolation = enforce_isolation
        self.agent_permissions: Dict[str, List[AgentPermission]] = {}
        self.agent_roles: Dict[str, AgentRole] = {}

    def register_agent(
        self,
        agent_id: str,
        role: AgentRole,
        custom_permissions: Optional[List[AgentPermission]] = None
    ):
        """
        Register an agent with specific role and permissions.

        Args:
            agent_id: Unique agent identifier
            role: Agent role
            custom_permissions: Optional custom permissions (in addition to role defaults)
        """
        self.agent_roles[agent_id] = role

        # Get default permissions for role
        permissions = list(self.DEFAULT_ROLE_PERMISSIONS.get(role, []))

        # Add custom permissions if provided
        if custom_permissions:
            permissions.extend(custom_permissions)

        self.agent_permissions[agent_id] = permissions

        logger.info(
            f"Agent registered: {agent_id}",
            extra={
                "agent_id": agent_id,
                "role": role.value,
                "permissions_count": len(permissions)
            }
        )

    def check_permission(
        self,
        agent_id: str,
        resource_type: ResourceType,
        action: str,
        scope: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if an agent has permission to perform an action.

        Args:
            agent_id: Agent requesting access
            resource_type: Type of resource being accessed
            action: Action to perform (read, write, delete, etc.)
            scope: Optional scope restriction (e.g., "user_id:123")

        Returns:
            Dict with 'allowed', 'reason', 'risk_level'
        """
        if not self.enabled:
            return {"allowed": True, "reason": "isolation_disabled", "risk_level": "none"}

        # Check if agent is registered
        if agent_id not in self.agent_permissions:
            logger.warning(f"Unregistered agent attempted action: {agent_id}")
            return {
                "allowed": False if self.enforce_isolation else True,
                "reason": "agent_not_registered",
                "risk_level": "high"
            }

        # Get agent permissions
        permissions = self.agent_permissions[agent_id]

        # Check if agent has permission for this resource + action
        has_permission = False
        for perm in permissions:
            if perm.resource_type == resource_type and action in perm.actions:
                # Check scope if specified
                if scope and perm.scope and perm.scope != scope:
                    continue
                has_permission = True
                break

        # Assess risk level
        risk_level = "medium"
        if action in self.HIGH_RISK_ACTIONS:
            risk_level = "high"
        elif resource_type in [ResourceType.SYSTEM_CONFIG, ResourceType.WALLET]:
            risk_level = "high"

        # Log unauthorized attempts
        if not has_permission:
            logger.warning(
                f"Unauthorized action attempted by agent",
                extra={
                    "agent_id": agent_id,
                    "resource_type": resource_type.value,
                    "action": action,
                    "scope": scope,
                    "risk_level": risk_level
                }
            )

        return {
            "allowed": has_permission if self.enforce_isolation else True,
            "reason": "permission_granted" if has_permission else "permission_denied",
            "risk_level": risk_level
        }

    def check_agent_communication(
        self,
        sender_agent_id: str,
        recipient_agent_id: str,
        message_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Check if an agent can communicate with another agent.

        Args:
            sender_agent_id: Agent sending the message
            recipient_agent_id: Agent receiving the message
            message_type: Type of message (standard, broadcast, control)

        Returns:
            Dict with 'allowed', 'reason', 'risk_level'
        """
        # Broadcast messages require special permission
        if message_type == "broadcast":
            return self.check_permission(
                sender_agent_id,
                ResourceType.AGENT_COMMUNICATION,
                "broadcast"
            )

        # Control messages (e.g., terminate) require admin role
        if message_type == "control":
            sender_role = self.agent_roles.get(sender_agent_id)
            if sender_role != AgentRole.ADMIN:
                logger.warning(
                    f"Non-admin agent attempted control message",
                    extra={
                        "sender_agent_id": sender_agent_id,
                        "recipient_agent_id": recipient_agent_id
                    }
                )
                return {
                    "allowed": False if self.enforce_isolation else True,
                    "reason": "requires_admin_role",
                    "risk_level": "critical"
                }

        # Standard messages require send permission
        return self.check_permission(
            sender_agent_id,
            ResourceType.AGENT_COMMUNICATION,
            "send"
        )

    def validate_agent_routing(
        self,
        user_message: str,
        requested_agents: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that agent routing request is safe.

        Prevents prompt injection attacks that try to redirect to admin agents.

        Args:
            user_message: Original user message
            requested_agents: List of agents user is trying to route to

        Returns:
            Dict with 'is_safe', 'suspicious_patterns', 'allowed_agents'
        """
        suspicious_patterns = []

        # Check for routing manipulation patterns
        routing_patterns = [
            r'\[?system\s+instruction\]?',
            r'route\s+to\s+admin',
            r'send\s+to\s+privileged',
            r'escalate\s+to',
            r'invoke\s+admin',
        ]

        import re
        for pattern in routing_patterns:
            if re.search(pattern, user_message, re.IGNORECASE):
                suspicious_patterns.append(pattern)

        # Filter out admin/privileged agents from routing
        allowed_agents = [
            agent_id for agent_id in requested_agents
            if self.agent_roles.get(agent_id) not in [AgentRole.ADMIN, AgentRole.PRIVILEGED]
        ]

        is_safe = len(suspicious_patterns) == 0

        if not is_safe:
            logger.warning(
                "Suspicious agent routing detected",
                extra={
                    "patterns": suspicious_patterns,
                    "requested_agents": requested_agents
                }
            )

        return {
            "is_safe": is_safe,
            "suspicious_patterns": suspicious_patterns,
            "allowed_agents": allowed_agents,
            "blocked_agents": [a for a in requested_agents if a not in allowed_agents]
        }

    def get_agent_capabilities(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the capabilities of an agent.

        Args:
            agent_id: Agent to query

        Returns:
            Dict with role, permissions, and capabilities
        """
        if agent_id not in self.agent_permissions:
            return {
                "agent_id": agent_id,
                "registered": False,
                "role": None,
                "permissions": []
            }

        role = self.agent_roles.get(agent_id)
        permissions = self.agent_permissions.get(agent_id, [])

        # Summarize capabilities
        capabilities = {}
        for perm in permissions:
            resource = perm.resource_type.value
            if resource not in capabilities:
                capabilities[resource] = []
            capabilities[resource].extend(list(perm.actions))

        return {
            "agent_id": agent_id,
            "registered": True,
            "role": role.value if role else None,
            "permissions": len(permissions),
            "capabilities": capabilities
        }

    def revoke_agent_access(self, agent_id: str):
        """
        Revoke all permissions for an agent.

        Args:
            agent_id: Agent to revoke
        """
        if agent_id in self.agent_permissions:
            del self.agent_permissions[agent_id]

        if agent_id in self.agent_roles:
            del self.agent_roles[agent_id]

        logger.info(
            f"Agent access revoked: {agent_id}",
            extra={"agent_id": agent_id}
        )


# Utility decorators
def require_agent_permission(
    resource_type: ResourceType,
    action: str,
    isolation_guard: AgentIsolationGuard
):
    """
    Decorator to require agent permission for a function.

    Usage:
        @require_agent_permission(ResourceType.USER_DATA, "write", guard)
        async def update_user_data(agent_id: str, data: dict):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            agent_id = kwargs.get("agent_id")
            if not agent_id:
                raise ValueError("agent_id required in kwargs")

            # Check permission
            check_result = isolation_guard.check_permission(
                agent_id, resource_type, action
            )

            if not check_result["allowed"]:
                raise PermissionError(
                    f"Agent {agent_id} not authorized to {action} {resource_type.value}: "
                    f"{check_result['reason']}"
                )

            # Execute function
            return await func(*args, **kwargs)

        return wrapper
    return decorator
