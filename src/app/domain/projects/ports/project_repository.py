"""Project repository port."""
from typing import List, Optional, Protocol
from uuid import UUID

from app.domain.projects.entities.project import Project


class ProjectRepository(Protocol):
    """Repository interface for projects."""
    
    async def add_project(self, project: Project) -> None:
        """
        Add a new project.
        
        Args:
            project: Project entity to add
        """
        ...
    
    async def get_project(self, project_id: UUID) -> Optional[Project]:
        """
        Get project by ID.
        
        Args:
            project_id: Project identifier
        
        Returns:
            Project entity or None if not found
        """
        ...
    
    async def get_project_by_slug(self, slug: str) -> Optional[Project]:
        """
        Get project by slug.
        
        Args:
            slug: Project slug
        
        Returns:
            Project entity or None if not found
        """
        ...
    
    async def list_projects(
        self,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        is_featured: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Project]:
        """
        List projects with filters.
        
        Args:
            status: Filter by status
            visibility: Filter by visibility
            is_featured: Filter by featured flag
            limit: Maximum results
            offset: Result offset
        
        Returns:
            List of projects
        """
        ...
    
    async def update_project(self, project: Project) -> None:
        """
        Update project.
        
        Args:
            project: Project entity to update
        """
        ...
    
    async def delete_project(self, project_id: UUID) -> None:
        """
        Delete project.
        
        Args:
            project_id: Project identifier
        """
        ...
    
    async def count_users(self, project_id: UUID) -> int:
        """
        Count users assigned to project.
        
        Args:
            project_id: Project identifier
        
        Returns:
            Number of users
        """
        ...
    
    async def search_projects(
        self,
        query: str,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Project]:
        """
        Search projects by name or description.
        
        Args:
            query: Search query
            status: Filter by status
            limit: Maximum results
        
        Returns:
            List of matching projects
        """
        ...
