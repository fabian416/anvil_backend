"""Assignment repository ports."""

from typing import List, Optional, Protocol
from uuid import UUID

from app.domain.entities.assignment_rule import AssignmentRule, UserProjectAssignment


class AssignmentRuleRepository(Protocol):
    """Repository for assignment rules."""

    async def add_rule(self, rule: AssignmentRule) -> None:
        """Add assignment rule."""
        ...

    async def get_rule(self, rule_id: UUID) -> Optional[AssignmentRule]:
        """Get rule by ID."""
        ...

    async def list_rules(
        self,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> List[AssignmentRule]:
        """
        List assignment rules.

        Results sorted by priority DESC.
        """
        ...

    async def update_rule(self, rule: AssignmentRule) -> None:
        """Update assignment rule."""
        ...

    async def delete_rule(self, rule_id: UUID) -> None:
        """Delete assignment rule."""
        ...


class UserAssignmentRepository(Protocol):
    """Repository for user-project assignments."""

    async def add_assignment(self, assignment: UserProjectAssignment) -> None:
        """Add user assignment."""
        ...

    async def get_assignment(
        self, assignment_id: UUID
    ) -> Optional[UserProjectAssignment]:
        """Get assignment by ID."""
        ...

    async def get_user_assignments(
        self,
        user_id: UUID,
        is_active: bool = True,
    ) -> List[UserProjectAssignment]:
        """Get user's assignments."""
        ...

    async def get_project_assignments(
        self,
        project_id: UUID,
        is_active: bool = True,
    ) -> List[UserProjectAssignment]:
        """Get project's assignments."""
        ...

    async def get_user_project_assignment(
        self,
        user_id: UUID,
        project_id: UUID,
    ) -> Optional[UserProjectAssignment]:
        """Get specific user-project assignment."""
        ...

    async def update_assignment(self, assignment: UserProjectAssignment) -> None:
        """Update assignment."""
        ...

    async def delete_assignment(self, assignment_id: UUID) -> None:
        """Delete assignment."""
        ...

    async def get_assigned_project_ids(self, user_id: UUID) -> List[UUID]:
        """Get list of project IDs user is assigned to."""
        ...

    async def set_active_project(self, user_id: UUID, project_id: UUID) -> None:
        """Set user's active project."""
        ...

    async def get_active_project(self, user_id: UUID) -> Optional[UUID]:
        """Get user's active project."""
        ...
