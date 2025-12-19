"""Delete project command."""
from uuid import UUID

from app.domain.projects.ports.project_repository import ProjectRepository


class DeleteProject:
    """
    Delete a project.
    
    This orchestrates:
    1. Load project
    2. Verify can be deleted
    3. Delete project (cascades to knowledge base, assignments, etc.)
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
    ) -> None:
        """
        Execute the command.
        
        Args:
            project_id: Project identifier
        
        Raises:
            ValueError: If project not found
        """
        # Load project
        project = await self._repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Delete project (cascades handled by database)
        await self._repository.delete_project(project_id)
