"""Create project command."""

from typing import Dict, List, Optional, Any
from uuid import UUID

from app.domain.projects.entities.project import Project
from app.domain.projects.ports.project_repository import ProjectRepository


class CreateProject:
    """
    Create a new project.

    This orchestrates:
    1. Validate slug uniqueness
    2. Create project entity
    3. Save to repository
    4. Create associated knowledge base (if requested)
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
        slug: str,
        name: str,
        system_prompt: str,
        created_by: UUID,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        status: str = "draft",
        visibility: str = "public",
        welcome_message: Optional[str] = None,
        enabled_protocols: Optional[List[str]] = None,
        enabled_chains: Optional[List[str]] = None,
        enabled_tools: Optional[List[str]] = None,
        risk_config: Optional[Dict[str, Any]] = None,
    ) -> Project:
        """
        Execute the command.

        Args:
            slug: URL-friendly identifier
            name: Display name
            system_prompt: System prompt for AI
            created_by: Creator user ID
            description: Optional description
            icon: Optional icon/emoji
            color: Optional hex color
            status: Status (default: draft)
            visibility: Visibility (default: public)
            welcome_message: Optional welcome message
            enabled_protocols: Allowed protocols
            enabled_chains: Allowed chains
            enabled_tools: Allowed tools
            risk_config: Risk configuration

        Returns:
            Created project entity

        Raises:
            ValueError: If slug already exists
        """
        # Check slug uniqueness
        existing = await self._repository.get_project_by_slug(slug)
        if existing:
            raise ValueError(f"Project with slug '{slug}' already exists")

        # Create project
        project = Project.create(
            slug=slug,
            name=name,
            system_prompt=system_prompt,
            created_by=created_by,
            description=description,
            icon=icon,
            color=color,
            status=status,
            visibility=visibility,
            welcome_message=welcome_message,
            enabled_protocols=enabled_protocols,
            enabled_chains=enabled_chains,
            enabled_tools=enabled_tools,
            risk_config=risk_config,
        )

        # Save project
        await self._repository.add_project(project)

        return project
