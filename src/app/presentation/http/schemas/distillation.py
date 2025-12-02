"""Pydantic schemas for distillation APIs."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


# Static Response Schemas
class StaticResponseBase(BaseModel):
    """Base static response schema."""
    intent: str
    variant: str = "default"
    response_template: str
    template_variables: List[str] = Field(default_factory=list)
    data_source: Optional[str] = None
    conditions: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    is_active: bool = True


class StaticResponseCreate(StaticResponseBase):
    """Create static response request."""
    pass


class StaticResponseUpdate(BaseModel):
    """Update static response request."""
    response_template: Optional[str] = None
    is_active: Optional[bool] = None


class StaticResponseResponse(StaticResponseBase):
    """Static response response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Distillation Config Schemas
class DistillationConfigResponse(BaseModel):
    """Distillation configuration response."""
    enabled: bool
    cache_enabled: bool
    static_responses_enabled: bool
    semantic_cache_enabled: bool
    min_confidence_threshold: float
    semantic_similarity_threshold: float
    max_classification_latency_ms: int


class DistillationConfigUpdate(BaseModel):
    """Update distillation configuration."""
    enabled: Optional[bool] = None
    cache_enabled: Optional[bool] = None
    static_responses_enabled: Optional[bool] = None
    semantic_cache_enabled: Optional[bool] = None
    min_confidence_threshold: Optional[float] = None
    semantic_similarity_threshold: Optional[float] = None
    max_classification_latency_ms: Optional[int] = None


# Cache Management Schemas
class CacheInvalidateRequest(BaseModel):
    """Request to invalidate cache."""
    cache_type: str = Field(..., description="exact, semantic, or all")
    filters: Optional[Dict[str, Any]] = None


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    exact_cache: Dict[str, int]
    semantic_cache: Dict[str, int]


# Telemetry Schemas
class DistillationTelemetryResponse(BaseModel):
    """Distillation telemetry response."""
    request_id: str
    user_id: Optional[UUID]
    original_query: str
    intent: str
    complexity: str
    route_type: str
    cache_hit: bool
    cache_level: str
    classification_latency_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


class DistillationSummaryResponse(BaseModel):
    """Distillation summary statistics."""
    hour: datetime
    total_requests: int
    cache_hits: int
    static_responses: int
    light_llm: int
    full_llm: int
    rejected: int
    avg_classification_ms: float
    avg_confidence: float
