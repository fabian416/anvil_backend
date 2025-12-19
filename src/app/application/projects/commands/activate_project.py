"""Activate project command."""
from uuid import UUID

from app.domain.projects.entities.project import Project
from app.domain.projects.ports.project_repository import ProjectRepository


class ActivateProject:
    """
    Activate a project.
    
    This orchestrates:
    1. Load project
    2. Activate project
    3. Save changes
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
        project_id: UUID,
    ) -> Project:
        """
        Execute the command.
        
        Args:
            project_id: Project identifier
        
        Returns:
            Activated project
        
        Raises:
            ValueError: If project not found
        """
        # Load project
        project = await self._repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Activate
        project.activate()
        
        # Save changes
        await self._repository.update_project(project)
        
        return project
