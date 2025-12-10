"""Admin API endpoints for projects management."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, status, HTTPException
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.schemas.projects import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    AssignmentRuleCreate,
    AssignmentRuleUpdate,
    AssignmentRuleResponse,
    UserAssignmentCreate,
    UserAssignmentResponse,
)
from app.application.projects.commands.create_project import CreateProject
from app.application.projects.commands.update_project import UpdateProject
from app.application.projects.commands.delete_project import DeleteProject
from app.application.projects.commands.activate_project import ActivateProject
from app.application.projects.queries.get_project import GetProject
from app.application.projects.queries.list_projects import ListProjects
from app.application.projects.queries.search_projects import SearchProjects
from app.infrastructure.persistence_sqla.repositories.knowledge_repository import (
    KnowledgeDocumentRepositorySqla,
)
from app.infrastructure.persistence_sqla.repositories.assignment_repository import (
    AssignmentRuleRepositorySqla,
    UserAssignmentRepositorySqla,
)
from app.domain.services.knowledge.document_processor import DocumentProcessor


router = APIRouter(prefix="/admin/projects", tags=["Admin - Projects"])


# ==================== Projects CRUD ====================

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_project(
    data: ProjectCreate,
    interactor: FromDishka[CreateProject],
) -> ProjectResponse:
    """Create a new project."""
    # TODO: Get created_by from authenticated user
    from uuid import uuid4
    created_by = uuid4()
    
    project = await interactor.execute(
        slug=data.slug,
        name=data.name,
        system_prompt=data.system_prompt,
        created_by=created_by,
        description=data.description,
        icon=data.icon,
        color=data.color,
        banner_url=data.banner_url,
        status=data.status,
        visibility=data.visibility,
        welcome_message=data.welcome_message,
        enabled_protocols=data.enabled_protocols,
        enabled_chains=data.enabled_chains,
        enabled_tools=data.enabled_tools,
        risk_config=data.risk_config,
        max_users=data.max_users,
        display_order=data.display_order,
        is_featured=data.is_featured,
    )
    
    return ProjectResponse(
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


@router.get(
    "/",
    response_model=List[ProjectResponse],
)
@inject
async def list_projects(
    status: Optional[str] = Query(None),
    visibility: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    interactor: FromDishka[ListProjects] = None,
) -> List[ProjectResponse]:
    """List projects with filters."""
    projects = await interactor.execute(
        status=status,
        visibility=visibility,
        is_featured=is_featured,
        limit=limit,
        offset=offset,
    )
    
    return [
        ProjectResponse(
            id=p.id,
            slug=p.slug,
            name=p.name,
            description=p.description,
            icon=p.icon,
            color=p.color,
            banner_url=p.banner_url,
            status=p.status,
            visibility=p.visibility,
            system_prompt=p.system_prompt,
            welcome_message=p.welcome_message,
            enabled_protocols=p.enabled_protocols,
            enabled_chains=p.enabled_chains,
            enabled_tools=p.enabled_tools,
            risk_config=p.risk_config,
            max_users=p.max_users,
            display_order=p.display_order,
            is_featured=p.is_featured,
            created_by=p.created_by,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in projects
    ]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
@inject
async def get_project(
    project_id: UUID,
    interactor: FromDishka[GetProject],
) -> ProjectResponse:
    """Get project by ID."""
    project = await interactor.execute(project_id=project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
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


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
@inject
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    interactor: FromDishka[UpdateProject],
) -> ProjectResponse:
    """Update project."""
    project = await interactor.execute(
        project_id=project_id,
        name=data.name,
        description=data.description,
        icon=data.icon,
        color=data.color,
        banner_url=data.banner_url,
        system_prompt=data.system_prompt,
        welcome_message=data.welcome_message,
        enabled_protocols=data.enabled_protocols,
        enabled_chains=data.enabled_chains,
        enabled_tools=data.enabled_tools,
        risk_config=data.risk_config,
        max_users=data.max_users,
        display_order=data.display_order,
        is_featured=data.is_featured,
    )
    
    return ProjectResponse(
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


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def delete_project(
    project_id: UUID,
    interactor: FromDishka[DeleteProject],
):
    """Delete project."""
    await interactor.execute(project_id=project_id)


@router.post(
    "/{project_id}/activate",
    response_model=ProjectResponse,
)
@inject
async def activate_project(
    project_id: UUID,
    interactor: FromDishka[ActivateProject],
) -> ProjectResponse:
    """Activate project."""
    project = await interactor.execute(project_id=project_id)
    
    return ProjectResponse(
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


# ==================== Knowledge Base ====================

@router.post(
    "/{project_id}/knowledge/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_knowledge_document(
    project_id: UUID,
    data: KnowledgeDocumentCreate,
    doc_repository: FromDishka[KnowledgeDocumentRepositorySqla],
    processor: FromDishka[DocumentProcessor],
) -> KnowledgeDocumentResponse:
    """Create and process a knowledge document."""
    from app.domain.entities.knowledge_base import KnowledgeDocument
    from uuid import uuid4
    from datetime import datetime
    
    # Create document
    document = KnowledgeDocument(
        id=uuid4(),
        knowledge_base_id=project_id,  # Assuming project has a default KB
        title=data.title,
        content=data.content,
        doc_type=data.doc_type,
        source_url=data.source_url,
        source_type=data.source_type,
        tags=data.tags,
        priority=data.priority,
        is_processed=False,
        chunk_count=0,
        processing_error=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    await doc_repository.add_document(document)
    
    # Process document asynchronously (for now, synchronous)
    try:
        chunk_count = await processor.process_document(document)
        document.mark_processed(chunk_count)
        await doc_repository.update_document(document)
    except Exception as e:
        document.mark_error(str(e))
        await doc_repository.update_document(document)
    
    return KnowledgeDocumentResponse(
        id=document.id,
        knowledge_base_id=document.knowledge_base_id,
        title=document.title,
        doc_type=document.doc_type,
        tags=document.tags,
        priority=document.priority,
        is_processed=document.is_processed,
        chunk_count=document.chunk_count,
        processing_error=document.processing_error,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get(
    "/{project_id}/knowledge/documents",
    response_model=List[KnowledgeDocumentResponse],
)
@inject
async def list_knowledge_documents(
    project_id: UUID,
    doc_repository: FromDishka[KnowledgeDocumentRepositorySqla],
) -> List[KnowledgeDocumentResponse]:
    """List knowledge documents for a project."""
    documents = await doc_repository.list_documents(knowledge_base_id=project_id)
    
    return [
        KnowledgeDocumentResponse(
            id=d.id,
            knowledge_base_id=d.knowledge_base_id,
            title=d.title,
            doc_type=d.doc_type,
            tags=d.tags,
            priority=d.priority,
            is_processed=d.is_processed,
            chunk_count=d.chunk_count,
            processing_error=d.processing_error,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in documents
    ]


# ==================== Assignment Rules ====================

@router.post(
    "/{project_id}/assignment-rules",
    response_model=AssignmentRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_assignment_rule(
    project_id: UUID,
    data: AssignmentRuleCreate,
    repository: FromDishka[AssignmentRuleRepositorySqla],
) -> AssignmentRuleResponse:
    """Create assignment rule for a project."""
    from app.domain.entities.assignment_rule import AssignmentRule
    
    rule = AssignmentRule.create(
        project_id=project_id,
        rule_name=data.rule_name,
        condition_type=data.condition_type,
        condition_params=data.condition_params,
        priority=data.priority,
        auto_switch=data.auto_switch,
    )
    
    await repository.add_rule(rule)
    
    return AssignmentRuleResponse(
        id=rule.id,
        project_id=rule.project_id,
        rule_name=rule.rule_name,
        condition_type=rule.condition_type,
        condition_params=rule.condition_params,
        priority=rule.priority,
        auto_switch=rule.auto_switch,
        is_active=rule.is_active,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.get(
    "/{project_id}/assignment-rules",
    response_model=List[AssignmentRuleResponse],
)
@inject
async def list_assignment_rules(
    project_id: UUID,
    repository: FromDishka[AssignmentRuleRepositorySqla],
) -> List[AssignmentRuleResponse]:
    """List assignment rules for a project."""
    rules = await repository.get_rules_by_project(project_id)
    
    return [
        AssignmentRuleResponse(
            id=r.id,
            project_id=r.project_id,
            rule_name=r.rule_name,
            condition_type=r.condition_type,
            condition_params=r.condition_params,
            priority=r.priority,
            auto_switch=r.auto_switch,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rules
    ]


@router.patch(
    "/{project_id}/assignment-rules/{rule_id}",
    response_model=AssignmentRuleResponse,
)
@inject
async def update_assignment_rule(
    project_id: UUID,
    rule_id: UUID,
    data: AssignmentRuleUpdate,
    repository: FromDishka[AssignmentRuleRepositorySqla],
) -> AssignmentRuleResponse:
    """Update assignment rule."""
    rule = await repository.get_rule(rule_id)
    
    if not rule or rule.project_id != project_id:
        raise HTTPException(status_code=404, detail="Assignment rule not found")
    
    if data.rule_name is not None:
        rule.rule_name = data.rule_name
    if data.condition_params is not None:
        rule.condition_params = data.condition_params
    if data.priority is not None:
        rule.priority = data.priority
    if data.auto_switch is not None:
        rule.auto_switch = data.auto_switch
    if data.is_active is not None:
        rule.is_active = data.is_active
    
    await repository.update_rule(rule)
    
    return AssignmentRuleResponse(
        id=rule.id,
        project_id=rule.project_id,
        rule_name=rule.rule_name,
        condition_type=rule.condition_type,
        condition_params=rule.condition_params,
        priority=rule.priority,
        auto_switch=rule.auto_switch,
        is_active=rule.is_active,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


# ==================== User Assignments ====================

@router.post(
    "/{project_id}/assignments",
    response_model=UserAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def assign_user_to_project(
    project_id: UUID,
    data: UserAssignmentCreate,
    repository: FromDishka[UserAssignmentRepositorySqla],
) -> UserAssignmentResponse:
    """Manually assign a user to a project."""
    from app.domain.entities.assignment_rule import UserProjectAssignment
    from datetime import datetime
    
    assignment = UserProjectAssignment.create(
        user_id=data.user_id,
        project_id=project_id,
        assignment_type="manual",
        assignment_reason=data.assignment_reason,
    )
    
    await repository.add_assignment(assignment)
    
    return UserAssignmentResponse(
        id=assignment.id,
        user_id=assignment.user_id,
        project_id=assignment.project_id,
        assignment_type=assignment.assignment_type,
        assignment_reason=assignment.assignment_reason,
        is_active=assignment.is_active,
        assigned_at=assignment.assigned_at,
        last_active_at=assignment.last_active_at,
    )


@router.get(
    "/{project_id}/assignments",
    response_model=List[UserAssignmentResponse],
)
@inject
async def list_project_assignments(
    project_id: UUID,
    repository: FromDishka[UserAssignmentRepositorySqla],
) -> List[UserAssignmentResponse]:
    """List all user assignments for a project."""
    assignments = await repository.get_assignments_by_project(project_id)
    
    return [
        UserAssignmentResponse(
            id=a.id,
            user_id=a.user_id,
            project_id=a.project_id,
            assignment_type=a.assignment_type,
            assignment_reason=a.assignment_reason,
            is_active=a.is_active,
            assigned_at=a.assigned_at,
            last_active_at=a.last_active_at,
        )
        for a in assignments
    ]
