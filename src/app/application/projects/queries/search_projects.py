"""Search projects query."""

from typing import List, Optional

from app.domain.projects.entities.project import Project
from app.domain.projects.ports.project_repository import ProjectRepository


class SearchProjects:
    """
    Search projects by name or description.

    This orchestrates:
    1. Search projects in repository
    2. Return matching results
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
        query: str,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Project]:
        """
        Execute the query.

        Args:
            query: Search query
            status: Filter by status
            limit: Maximum results

        Returns:
            List of matching projects
        """
        return await self._repository.search_projects(
            query=query,
            status=status,
            limit=limit,
        )
