"""User-facing API endpoints for project selection."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.schemas.projects import (
    ProjectSummaryResponse,
    UserProjectsResponse,
)
from app.application.projects.queries.list_projects import ListProjects
from app.infrastructure.persistence_sqla.repositories.assignment_repository import (
    UserAssignmentRepositorySqla,
)
from app.domain.services.assignment.assignment_service import AssignmentService


router = APIRouter(prefix="/projects", tags=["User - Projects"])


@router.get(
    "/",
    response_model=UserProjectsResponse,
)
@inject
async def get_user_projects(
    # TODO: Get user_id from authenticated user context
    assignment_repo: FromDishka[UserAssignmentRepositorySqla],
    project_interactor: FromDishka[ListProjects],
) -> UserProjectsResponse:
    """Get user's assigned projects and active project."""
    # Mock user ID for now
    from uuid import uuid4
    user_id = uuid4()
    
    # Get user assignments
    assignments = await assignment_repo.get_assignments_by_user(user_id)
    assigned_project_ids = [a.project_id for a in assignments if a.is_active]
    
    # Get active project
    active_project_id = await assignment_repo.get_active_project(user_id)
    
    # Fetch project details
    all_projects = await project_interactor.execute(
        status="active",
        visibility="public",
        limit=100,
    )
    
    # Filter to assigned projects
    assigned_projects = [
        p for p in all_projects
        if p.id in assigned_project_ids
    ]
    
    return UserProjectsResponse(
        assigned_projects=[
            ProjectSummaryResponse(
                id=p.id,
                slug=p.slug,
                name=p.name,
                description=p.description,
                icon=p.icon,
                color=p.color,
                welcome_message=p.welcome_message,
                is_featured=p.is_featured,
            )
            for p in assigned_projects
        ],
        active_project_id=active_project_id,
    )


@router.get(
    "/available",
    response_model=List[ProjectSummaryResponse],
)
@inject
async def list_available_projects(
    interactor: FromDishka[ListProjects],
) -> List[ProjectSummaryResponse]:
    """List all publicly available projects."""
    projects = await interactor.execute(
        status="active",
        visibility="public",
        limit=50,
    )
    
    return [
        ProjectSummaryResponse(
            id=p.id,
            slug=p.slug,
            name=p.name,
            description=p.description,
            icon=p.icon,
            color=p.color,
            welcome_message=p.welcome_message,
            is_featured=p.is_featured,
        )
        for p in projects
    ]


@router.post(
    "/{project_id}/select",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def select_project(
    project_id: UUID,
    assignment_repo: FromDishka[UserAssignmentRepositorySqla],
    project_interactor: FromDishka[ListProjects],
):
    """Select (activate) a project for the current user."""
    # Mock user ID for now
    from uuid import uuid4
    user_id = uuid4()
    
    # Verify project exists and is active
    projects = await project_interactor.execute(limit=1000)
    project = next((p for p in projects if p.id == project_id), None)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.status != "active":
        raise HTTPException(status_code=400, detail="Project is not active")
    
    # Check if user is assigned to this project
    assignments = await assignment_repo.get_assignments_by_user(user_id)
    is_assigned = any(
        a.project_id == project_id and a.is_active
        for a in assignments
    )
    
    if not is_assigned:
        # Auto-assign if project is public
        if project.visibility == "public":
            from app.domain.entities.assignment_rule import UserProjectAssignment
            
            assignment = UserProjectAssignment.create(
                user_id=user_id,
                project_id=project_id,
                assignment_type="self",
                assignment_reason="User self-selected project",
            )
            await assignment_repo.add_assignment(assignment)
        else:
            raise HTTPException(
                status_code=403,
                detail="User is not assigned to this project"
            )
    
    # Set as active project
    await assignment_repo.set_active_project(user_id, project_id)


@router.post(
    "/{project_id}/join",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def join_project(
    project_id: UUID,
    assignment_repo: FromDishka[UserAssignmentRepositorySqla],
    project_interactor: FromDishka[ListProjects],
):
    """Join (self-assign to) a public project."""
    # Mock user ID for now
    from uuid import uuid4
    user_id = uuid4()
    
    # Verify project exists and is public
    projects = await project_interactor.execute(limit=1000)
    project = next((p for p in projects if p.id == project_id), None)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.visibility != "public":
        raise HTTPException(
            status_code=403,
            detail="Project is not publicly available"
        )
    
    if project.status != "active":
        raise HTTPException(status_code=400, detail="Project is not active")
    
    # Check if already assigned
    assignments = await assignment_repo.get_assignments_by_user(user_id)
    already_assigned = any(
        a.project_id == project_id and a.is_active
        for a in assignments
    )
    
    if already_assigned:
        raise HTTPException(
            status_code=400,
            detail="User is already assigned to this project"
        )
    
    # Check max_users limit
    if project.max_users:
        project_assignments = await assignment_repo.get_assignments_by_project(
            project_id
        )
        active_count = sum(1 for a in project_assignments if a.is_active)
        
        if active_count >= project.max_users:
            raise HTTPException(
                status_code=400,
                detail="Project has reached maximum user capacity"
            )
    
    # Create self-assignment
    from app.domain.entities.assignment_rule import UserProjectAssignment
    
    assignment = UserProjectAssignment.create(
        user_id=user_id,
        project_id=project_id,
        assignment_type="self",
        assignment_reason="User self-joined project",
    )
    await assignment_repo.add_assignment(assignment)
    
    # Set as active project
    await assignment_repo.set_active_project(user_id, project_id)


@router.get(
    "/{project_slug}",
    response_model=ProjectSummaryResponse,
)
@inject
async def get_project_by_slug(
    project_slug: str,
    interactor: FromDishka[ListProjects],
) -> ProjectSummaryResponse:
    """Get project details by slug."""
    projects = await interactor.execute(limit=1000)
    project = next((p for p in projects if p.slug == project_slug), None)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectSummaryResponse(
        id=project.id,
        slug=project.slug,
        name=project.name,
        description=project.description,
        icon=project.icon,
        color=project.color,
        welcome_message=project.welcome_message,
        is_featured=project.is_featured,
    )
