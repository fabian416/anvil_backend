"""Get project query."""

from typing import Optional
from uuid import UUID

from app.domain.projects.entities.project import Project
from app.domain.projects.ports.project_repository import ProjectRepository


class GetProject:
    """
    Get a project by ID or slug.

    This orchestrates:
    1. Load project from repository
    """

    def __init__(
        self,
        repository: ProjectRepository,
    ):
        """
        Initialize interactor.

        Args:
            repository: Project repository
        """
        self._repository = repository

    async def execute(
        self,
        project_id: Optional[UUID] = None,
        slug: Optional[str] = None,
    ) -> Optional[Project]:
        """
        Execute the query.

        Args:
            project_id: Project identifier
            slug: Project slug

        Returns:
            Project entity or None if not found

        Raises:
            ValueError: If neither project_id nor slug provided
        """
        if project_id:
            return await self._repository.get_project(project_id)
        elif slug:
            return await self._repository.get_project_by_slug(slug)
        else:
            raise ValueError("Either project_id or slug must be provided")
