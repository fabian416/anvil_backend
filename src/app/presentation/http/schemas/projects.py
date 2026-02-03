"""Pydantic schemas for projects APIs."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Project Schemas
class ProjectBase(BaseModel):
    """Base project schema."""

    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    banner_url: Optional[str] = None
    system_prompt: str
    welcome_message: Optional[str] = None
    enabled_protocols: List[str] = Field(default_factory=list)
    enabled_chains: List[str] = Field(default_factory=list)
    enabled_tools: List[str] = Field(default_factory=list)
    risk_config: Dict[str, Any] = Field(default_factory=dict)
    max_users: Optional[int] = None
    display_order: int = 0
    is_featured: bool = False


class ProjectCreate(ProjectBase):
    """Create project request."""

    slug: str
    status: str = "draft"
    visibility: str = "public"


class ProjectUpdate(BaseModel):
    """Update project request."""

    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    banner_url: Optional[str] = None
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    enabled_protocols: Optional[List[str]] = None
    enabled_chains: Optional[List[str]] = None
    enabled_tools: Optional[List[str]] = None
    risk_config: Optional[Dict[str, Any]] = None
    max_users: Optional[int] = None
    display_order: Optional[int] = None
    is_featured: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """Project response."""

    id: UUID
    slug: str
    status: str
    visibility: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Knowledge Document Schemas
class KnowledgeDocumentCreate(BaseModel):
    """Create knowledge document request."""

    title: str
    content: str
    doc_type: str
    source_url: Optional[str] = None
    source_type: str = "manual"
    tags: List[str] = Field(default_factory=list)
    priority: int = 1


class KnowledgeDocumentResponse(BaseModel):
    """Knowledge document response."""

    id: UUID
    knowledge_base_id: UUID
    title: str
    doc_type: str
    tags: List[str]
    priority: int
    is_processed: bool
    chunk_count: int
    processing_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Assignment Rule Schemas
class AssignmentRuleCreate(BaseModel):
    """Create assignment rule request."""

    rule_name: str
    condition_type: str
    condition_params: Dict[str, Any]
    priority: int = 1
    auto_switch: bool = False


class AssignmentRuleUpdate(BaseModel):
    """Update assignment rule request."""

    rule_name: Optional[str] = None
    condition_params: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    auto_switch: Optional[bool] = None
    is_active: Optional[bool] = None


class AssignmentRuleResponse(BaseModel):
    """Assignment rule response."""

    id: UUID
    project_id: UUID
    rule_name: str
    condition_type: str
    condition_params: Dict[str, Any]
    priority: int
    auto_switch: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# User Assignment Schemas
class UserAssignmentCreate(BaseModel):
    """Create user assignment request."""

    user_id: UUID
    assignment_reason: Optional[str] = None


class UserAssignmentResponse(BaseModel):
    """User assignment response."""

    id: UUID
    user_id: UUID
    project_id: UUID
    assignment_type: str
    assignment_reason: Optional[str]
    is_active: bool
    assigned_at: datetime
    last_active_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# User-facing Schemas
class ProjectSummaryResponse(BaseModel):
    """Project summary for users."""

    id: UUID
    slug: str
    name: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    welcome_message: Optional[str]
    is_featured: bool

    model_config = ConfigDict(from_attributes=True)


class UserProjectsResponse(BaseModel):
    """User's available projects."""

    assigned_projects: List[ProjectSummaryResponse]
    active_project_id: Optional[UUID]
