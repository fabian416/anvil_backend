"""List projects query."""
from typing import List, Optional

from app.domain.entities.project import Project
from app.domain.ports.project_repository import ProjectRepository


class ListProjects:
    """
    List projects with optional filters.
    
    This orchestrates:
    1. Load projects from repository with filters
    2. Return list
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
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        is_featured: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Project]:
        """
        Execute the query.
        
        Args:
            status: Filter by status
            visibility: Filter by visibility
            is_featured: Filter by featured flag
            limit: Maximum results
            offset: Result offset
        
        Returns:
            List of projects
        """
        return await self._repository.list_projects(
            status=status,
            visibility=visibility,
            is_featured=is_featured,
            limit=limit,
            offset=offset,
        )
