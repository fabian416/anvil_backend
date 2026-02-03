"""SQLAlchemy repository for projects."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update

from app.domain.projects.entities.project import Project
from app.domain.projects.ports.project_repository import ProjectRepository
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.mappings.projects import (
    projects,
    user_project_assignments,
)


class ProjectRepositorySqla(ProjectRepository):
    """SQLAlchemy implementation of project repository."""

    def __init__(self, session: MainAsyncSession):
        self.session = session

    async def add_project(self, project: Project) -> None:
        """Add a new project."""
        query = projects.insert().values(
            id=project.id,
            slug=project.slug,
            name=project.name,
            description=project.description,
            icon=project.icon,
            color=project.color,
            banner_url=project.banner_url,
            status=project.status,
            visibility=project.visibility,
            system_prompt=project.system_prompt,
            welcome_message=project.welcome_message,
            enabled_protocols=project.enabled_protocols,
            enabled_chains=project.enabled_chains,
            enabled_tools=project.enabled_tools,
            risk_config=project.risk_config,
            max_users=project.max_users,
            display_order=project.display_order,
            is_featured=project.is_featured,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

        await self.session.execute(query)
        await self.session.commit()

    async def get_project(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID."""
        query = select(projects).where(projects.c.id == project_id)
        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return None

        return self._row_to_project(row)

    async def get_project_by_slug(self, slug: str) -> Optional[Project]:
        """Get project by slug."""
        query = select(projects).where(projects.c.slug == slug)
        result = await self.session.execute(query)
        row = result.first()

        if not row:
            return None

        return self._row_to_project(row)

    async def list_projects(
        self,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        is_featured: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Project]:
        """List projects with filters."""
        query = select(projects)

        if status:
            query = query.where(projects.c.status == status)

        if visibility:
            query = query.where(projects.c.visibility == visibility)

        if is_featured is not None:
            query = query.where(projects.c.is_featured == is_featured)

        query = (
            query.order_by(
                projects.c.display_order.desc(),
                projects.c.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [self._row_to_project(row) for row in rows]

    async def update_project(self, project: Project) -> None:
        """Update project."""
        query = (
            update(projects)
            .where(projects.c.id == project.id)
            .values(
                slug=project.slug,
                name=project.name,
                description=project.description,
                icon=project.icon,
                color=project.color,
                banner_url=project.banner_url,
                status=project.status,
                visibility=project.visibility,
                system_prompt=project.system_prompt,
                welcome_message=project.welcome_message,
                enabled_protocols=project.enabled_protocols,
                enabled_chains=project.enabled_chains,
                enabled_tools=project.enabled_tools,
                risk_config=project.risk_config,
                max_users=project.max_users,
                display_order=project.display_order,
                is_featured=project.is_featured,
                updated_at=project.updated_at,
            )
        )

        await self.session.execute(query)
        await self.session.commit()

    async def delete_project(self, project_id: UUID) -> None:
        """Delete project."""
        query = delete(projects).where(projects.c.id == project_id)
        await self.session.execute(query)
        await self.session.commit()

    async def count_users(self, project_id: UUID) -> int:
        """Count users assigned to project."""
        query = (
            select(func.count())
            .select_from(user_project_assignments)
            .where(
                user_project_assignments.c.project_id == project_id,
                user_project_assignments.c.is_active == True,
            )
        )

        result = await self.session.execute(query)
        count = result.scalar()
        return count or 0

    async def search_projects(
        self,
        query: str,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Project]:
        """Search projects by name or description."""
        search_query = select(projects).where(
            or_(
                projects.c.name.ilike(f"%{query}%"),
                projects.c.description.ilike(f"%{query}%"),
            )
        )

        if status:
            search_query = search_query.where(projects.c.status == status)

        search_query = search_query.order_by(
            projects.c.display_order.desc(),
            projects.c.created_at.desc(),
        ).limit(limit)

        result = await self.session.execute(search_query)
        rows = result.all()

        return [self._row_to_project(row) for row in rows]

    def _row_to_project(self, row) -> Project:
        """Convert database row to Project entity."""
        return Project(
            id=row.id,
            slug=row.slug,
            name=row.name,
            description=row.description,
            icon=row.icon,
            color=row.color,
            banner_url=row.banner_url,
            status=row.status,
            visibility=row.visibility,
            system_prompt=row.system_prompt,
            welcome_message=row.welcome_message,
            enabled_protocols=row.enabled_protocols or [],
            enabled_chains=row.enabled_chains or [],
            enabled_tools=row.enabled_tools or [],
            risk_config=row.risk_config or {},
            max_users=row.max_users,
            display_order=row.display_order,
            is_featured=row.is_featured,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
