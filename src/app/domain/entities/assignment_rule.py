"""Auto-assignment rule entity."""
from datetime import datetime
from typing import Dict, Optional, Any
from uuid import UUID, uuid4


class AssignmentRule:
    """
    Auto-assignment rule entity.
    
    Defines conditions for automatically assigning users to projects.
    """
    
    def __init__(
        self,
        id: UUID,
        project_id: UUID,
        rule_name: str,
        condition_type: str,
        condition_params: Dict[str, Any],
        priority: int,
        auto_switch: bool,
        is_active: bool,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize assignment rule.
        
        Args:
            id: Rule identifier
            project_id: Project to assign to
            rule_name: Human-readable rule name
            condition_type: Type of condition (PORTFOLIO, ACTIVITY, PREFERENCE, ONBOARDING)
            condition_params: Condition parameters (JSON)
            priority: Rule priority (higher = evaluated first)
            auto_switch: Automatically switch user's active project
            is_active: Whether rule is active
            created_at: Creation timestamp
            updated_at: Update timestamp
        """
        self.id = id
        self.project_id = project_id
        self.rule_name = rule_name
        self.condition_type = condition_type
        self.condition_params = condition_params
        self.priority = priority
        self.auto_switch = auto_switch
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        project_id: UUID,
        rule_name: str,
        condition_type: str,
        condition_params: Dict[str, Any],
        priority: int = 1,
        auto_switch: bool = False,
    ) -> "AssignmentRule":
        """
        Create a new assignment rule.
        
        Args:
            project_id: Project to assign to
            rule_name: Human-readable rule name
            condition_type: Type of condition
            condition_params: Condition parameters
            priority: Rule priority
            auto_switch: Automatically switch active project
        
        Returns:
            New assignment rule
        """
        return cls(
            id=uuid4(),
            project_id=project_id,
            rule_name=rule_name,
            condition_type=condition_type,
            condition_params=condition_params,
            priority=priority,
            auto_switch=auto_switch,
            is_active=True,
        )
    
    def activate(self) -> None:
        """Activate the rule."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the rule."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def update_priority(self, priority: int) -> None:
        """Update rule priority."""
        self.priority = priority
        self.updated_at = datetime.utcnow()
    
    def update_params(self, condition_params: Dict[str, Any]) -> None:
        """Update condition parameters."""
        self.condition_params = condition_params
        self.updated_at = datetime.utcnow()


class UserProjectAssignment:
    """
    User-project assignment entity.
    
    Represents a user's assignment to a project.
    """
    
    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        project_id: UUID,
        assignment_type: str,
        assigned_by: Optional[UUID],
        assignment_reason: Optional[str],
        is_active: bool,
        assigned_at: Optional[datetime] = None,
        last_active_at: Optional[datetime] = None,
        removed_at: Optional[datetime] = None,
    ):
        """Initialize user project assignment."""
        self.id = id
        self.user_id = user_id
        self.project_id = project_id
        self.assignment_type = assignment_type
        self.assigned_by = assigned_by
        self.assignment_reason = assignment_reason
        self.is_active = is_active
        self.assigned_at = assigned_at or datetime.utcnow()
        self.last_active_at = last_active_at
        self.removed_at = removed_at
    
    @classmethod
    def create_auto(
        cls,
        user_id: UUID,
        project_id: UUID,
        reason: str,
    ) -> "UserProjectAssignment":
        """Create auto assignment."""
        return cls(
            id=uuid4(),
            user_id=user_id,
            project_id=project_id,
            assignment_type="auto",
            assigned_by=None,
            assignment_reason=reason,
            is_active=True,
        )
    
    @classmethod
    def create_manual(
        cls,
        user_id: UUID,
        project_id: UUID,
        assigned_by: UUID,
        reason: Optional[str] = None,
    ) -> "UserProjectAssignment":
        """Create manual assignment."""
        return cls(
            id=uuid4(),
            user_id=user_id,
            project_id=project_id,
            assignment_type="manual",
            assigned_by=assigned_by,
            assignment_reason=reason,
            is_active=True,
        )
    
    @classmethod
    def create_self(
        cls,
        user_id: UUID,
        project_id: UUID,
    ) -> "UserProjectAssignment":
        """Create self-selected assignment."""
        return cls(
            id=uuid4(),
            user_id=user_id,
            project_id=project_id,
            assignment_type="self",
            assigned_by=None,
            assignment_reason="User selected",
            is_active=True,
        )
    
    def touch(self) -> None:
        """Update last active timestamp."""
        self.last_active_at = datetime.utcnow()
    
    def remove(self) -> None:
        """Remove assignment."""
        self.is_active = False
        self.removed_at = datetime.utcnow()
