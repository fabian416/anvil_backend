"""SQLAlchemy repositories for assignment rules."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.assignment_rule import AssignmentRule, UserProjectAssignment
from app.domain.ports.assignment_repository import (
    AssignmentRuleRepository,
    UserAssignmentRepository,
)
from app.infrastructure.persistence_sqla.mappings.projects import (
    project_auto_assign_rules,
    user_active_projects,
    user_project_assignments,
)


class AssignmentRuleRepositorySqla(AssignmentRuleRepository):
    """SQLAlchemy implementation of assignment rule repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_rule(self, rule: AssignmentRule) -> None:
        """Add assignment rule."""
        query = insert(project_auto_assign_rules).values(
            id=rule.id,
            project_id=rule.project_id,
            rule_name=rule.rule_name,
            condition_type=rule.condition_type,
            condition_params=rule.condition_params,
            priority=rule.priority,
            auto_switch=rule.auto_switch,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def get_rule(self, rule_id: UUID) -> Optional[AssignmentRule]:
        """Get rule by ID."""
        query = select(project_auto_assign_rules).where(
            project_auto_assign_rules.c.id == rule_id
        )
        result = await self.session.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        return self._row_to_rule(row)
    
    async def list_rules(
        self,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> List[AssignmentRule]:
        """List assignment rules (sorted by priority DESC)."""
        query = select(project_auto_assign_rules)
        
        if project_id:
            query = query.where(project_auto_assign_rules.c.project_id == project_id)
        
        if is_active is not None:
            query = query.where(project_auto_assign_rules.c.is_active == is_active)
        
        query = query.order_by(project_auto_assign_rules.c.priority.desc())
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [self._row_to_rule(row) for row in rows]
    
    async def update_rule(self, rule: AssignmentRule) -> None:
        """Update assignment rule."""
        query = (
            update(project_auto_assign_rules)
            .where(project_auto_assign_rules.c.id == rule.id)
            .values(
                rule_name=rule.rule_name,
                condition_type=rule.condition_type,
                condition_params=rule.condition_params,
                priority=rule.priority,
                auto_switch=rule.auto_switch,
                is_active=rule.is_active,
                updated_at=rule.updated_at,
            )
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def delete_rule(self, rule_id: UUID) -> None:
        """Delete assignment rule."""
        query = delete(project_auto_assign_rules).where(
            project_auto_assign_rules.c.id == rule_id
        )
        await self.session.execute(query)
        await self.session.commit()
    
    def _row_to_rule(self, row) -> AssignmentRule:
        """Convert row to AssignmentRule entity."""
        return AssignmentRule(
            id=row.id,
            project_id=row.project_id,
            rule_name=row.rule_name,
            condition_type=row.condition_type,
            condition_params=row.condition_params or {},
            priority=row.priority,
            auto_switch=row.auto_switch,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class UserAssignmentRepositorySqla(UserAssignmentRepository):
    """SQLAlchemy implementation of user assignment repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_assignment(self, assignment: UserProjectAssignment) -> None:
        """Add user assignment."""
        query = insert(user_project_assignments).values(
            id=assignment.id,
            user_id=assignment.user_id,
            project_id=assignment.project_id,
            assignment_type=assignment.assignment_type,
            assigned_by=assignment.assigned_by,
            assignment_reason=assignment.assignment_reason,
            is_active=assignment.is_active,
            assigned_at=assignment.assigned_at,
            last_active_at=assignment.last_active_at,
            removed_at=assignment.removed_at,
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def get_assignment(self, assignment_id: UUID) -> Optional[UserProjectAssignment]:
        """Get assignment by ID."""
        query = select(user_project_assignments).where(
            user_project_assignments.c.id == assignment_id
        )
        result = await self.session.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        return self._row_to_assignment(row)
    
    async def get_user_assignments(
        self,
        user_id: UUID,
        is_active: bool = True,
    ) -> List[UserProjectAssignment]:
        """Get user's assignments."""
        query = select(user_project_assignments).where(
            user_project_assignments.c.user_id == user_id,
            user_project_assignments.c.is_active == is_active,
        ).order_by(user_project_assignments.c.assigned_at.desc())
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [self._row_to_assignment(row) for row in rows]
    
    async def get_project_assignments(
        self,
        project_id: UUID,
        is_active: bool = True,
    ) -> List[UserProjectAssignment]:
        """Get project's assignments."""
        query = select(user_project_assignments).where(
            user_project_assignments.c.project_id == project_id,
            user_project_assignments.c.is_active == is_active,
        ).order_by(user_project_assignments.c.assigned_at.desc())
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [self._row_to_assignment(row) for row in rows]
    
    async def get_user_project_assignment(
        self,
        user_id: UUID,
        project_id: UUID,
    ) -> Optional[UserProjectAssignment]:
        """Get specific user-project assignment."""
        query = select(user_project_assignments).where(
            user_project_assignments.c.user_id == user_id,
            user_project_assignments.c.project_id == project_id,
        )
        result = await self.session.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        return self._row_to_assignment(row)
    
    async def update_assignment(self, assignment: UserProjectAssignment) -> None:
        """Update assignment."""
        query = (
            update(user_project_assignments)
            .where(user_project_assignments.c.id == assignment.id)
            .values(
                assignment_reason=assignment.assignment_reason,
                is_active=assignment.is_active,
                last_active_at=assignment.last_active_at,
                removed_at=assignment.removed_at,
            )
        )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def delete_assignment(self, assignment_id: UUID) -> None:
        """Delete assignment."""
        query = delete(user_project_assignments).where(
            user_project_assignments.c.id == assignment_id
        )
        await self.session.execute(query)
        await self.session.commit()
    
    async def get_assigned_project_ids(self, user_id: UUID) -> List[UUID]:
        """Get list of project IDs user is assigned to."""
        query = select(user_project_assignments.c.project_id).where(
            user_project_assignments.c.user_id == user_id,
            user_project_assignments.c.is_active == True,
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [row.project_id for row in rows]
    
    async def set_active_project(self, user_id: UUID, project_id: UUID) -> None:
        """Set user's active project."""
        # Check if record exists
        check_query = select(user_active_projects).where(
            user_active_projects.c.user_id == user_id
        )
        result = await self.session.execute(check_query)
        existing = result.first()
        
        if existing:
            # Update existing
            query = (
                update(user_active_projects)
                .where(user_active_projects.c.user_id == user_id)
                .values(
                    project_id=project_id,
                    updated_at=datetime.utcnow(),
                    session_count=user_active_projects.c.session_count + 1,
                )
            )
        else:
            # Insert new
            query = insert(user_active_projects).values(
                user_id=user_id,
                project_id=project_id,
                activated_at=datetime.utcnow(),
                session_count=1,
                updated_at=datetime.utcnow(),
            )
        
        await self.session.execute(query)
        await self.session.commit()
    
    async def get_active_project(self, user_id: UUID) -> Optional[UUID]:
        """Get user's active project."""
        query = select(user_active_projects.c.project_id).where(
            user_active_projects.c.user_id == user_id
        )
        
        result = await self.session.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        return row.project_id
    
    def _row_to_assignment(self, row) -> UserProjectAssignment:
        """Convert row to UserProjectAssignment entity."""
        return UserProjectAssignment(
            id=row.id,
            user_id=row.user_id,
            project_id=row.project_id,
            assignment_type=row.assignment_type,
            assigned_by=row.assigned_by,
            assignment_reason=row.assignment_reason,
            is_active=row.is_active,
            assigned_at=row.assigned_at,
            last_active_at=row.last_active_at,
            removed_at=row.removed_at,
        )
