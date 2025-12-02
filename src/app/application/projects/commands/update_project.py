"""Update project command."""
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.domain.entities.project import Project
from app.domain.ports.project_repository import ProjectRepository


class UpdateProject:
    """
    Update an existing project.
    
    This orchestrates:
    1. Load project
    2. Update fields
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
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        banner_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        welcome_message: Optional[str] = None,
        enabled_protocols: Optional[List[str]] = None,
        enabled_chains: Optional[List[str]] = None,
        enabled_tools: Optional[List[str]] = None,
        risk_config: Optional[Dict[str, Any]] = None,
        max_users: Optional[int] = None,
        display_order: Optional[int] = None,
        is_featured: Optional[bool] = None,
    ) -> Project:
        """
        Execute the command.
        
        Args:
            project_id: Project identifier
            name: New name
            description: New description
            icon: New icon
            color: New color
            banner_url: New banner URL
            system_prompt: New system prompt
            welcome_message: New welcome message
            enabled_protocols: New protocols list
            enabled_chains: New chains list
            enabled_tools: New tools list
            risk_config: New risk config
            max_users: New max users
            display_order: New display order
            is_featured: New featured flag
        
        Returns:
            Updated project entity
        
        Raises:
            ValueError: If project not found
        """
        # Load project
        project = await self._repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Update fields
        project.update(
            name=name,
            description=description,
            icon=icon,
            color=color,
            banner_url=banner_url,
            system_prompt=system_prompt,
            welcome_message=welcome_message,
            enabled_protocols=enabled_protocols,
            enabled_chains=enabled_chains,
            enabled_tools=enabled_tools,
            risk_config=risk_config,
            max_users=max_users,
            display_order=display_order,
            is_featured=is_featured,
        )
        
        # Save changes
        await self._repository.update_project(project)
        
        return project
