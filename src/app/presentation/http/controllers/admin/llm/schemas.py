"""
Pydantic schemas for LLM Ranking Admin API.

Request/response models for all admin endpoints.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Response Models
# ============================================================================


class ModelRankingResponse(BaseModel):
    """Single model's ranking information."""

    model_id: UUID
    model_name: str
    provider_name: str
    display_name: Optional[str] = None
    ranking_score: Decimal
    position: int  # Calculated rank position (1-based)
    success_rate: Decimal
    avg_latency_ms: int
    avg_cost_per_request: Decimal
    total_requests: int
    successful_requests: int
    failed_requests: int
    last_used_at: Optional[datetime] = None
    has_override: bool = False
    override_reason: Optional[str] = None

    model_config = ConfigDict(ser_json_inf_nan="constants")


class AgentRankingsResponse(BaseModel):
    """Rankings for a specific agent type."""

    agent_type: str
    total_models: int
    models: List[ModelRankingResponse]
    last_recalculated_at: Optional[datetime] = None


class AgentTypeOverview(BaseModel):
    """Overview of one agent type."""

    agent_type: str
    total_models: int
    top_model: Optional[str] = None
    top_model_score: Optional[Decimal] = None
    last_recalculated_at: Optional[datetime] = None

    model_config = ConfigDict(ser_json_inf_nan="constants")


class AllRankingsOverviewResponse(BaseModel):
    """Overview of all agent types."""

    total_agent_types: int
    agent_types: List[AgentTypeOverview]


class RecalculateResponse(BaseModel):
    """Result of manual recalculation."""

    agent_type: str
    models_evaluated: int
    models_updated: int
    changes_made: int
    recalculated_at: datetime
    success: bool = True
    message: str = "Recalculation completed successfully"


class OverrideResponse(BaseModel):
    """Result of setting/removing override."""

    agent_type: str
    model_id: UUID
    model_name: str
    action: str  # "created", "updated", "removed"
    override_score: Optional[Decimal] = None
    expires_at: Optional[datetime] = None
    success: bool = True
    message: str

    model_config = ConfigDict(ser_json_inf_nan="constants")


class RegisterModelResponse(BaseModel):
    """Result of registering a new model."""

    model_id: UUID
    model_name: str
    provider_name: str
    display_name: str
    initial_ranking_score: Decimal
    override_expires_at: datetime
    agent_types_registered: List[str]
    success: bool = True
    message: str

    model_config = ConfigDict(ser_json_inf_nan="constants")


# ============================================================================
# Request Models
# ============================================================================


class SetOverrideRequest(BaseModel):
    """Request to set manual ranking override."""

    override_score: Decimal = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Override ranking score (0.0-1.0)",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for override",
    )
    expires_in_hours: Optional[int] = Field(
        None,
        ge=1,
        le=8760,  # Max 1 year
        description="Override expiry in hours (null = permanent)",
    )

    @field_validator("override_score")
    @classmethod
    def validate_score(cls, v: Decimal) -> Decimal:
        """Ensure score is within valid range."""
        if not (0 <= v <= 1):
            raise ValueError("Score must be between 0.0 and 1.0")
        return v


class RegisterVertexAIModelRequest(BaseModel):
    """Request to register new Vertex AI model."""

    model_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Vertex AI model ID (e.g., 'gemini-1.5-pro')",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable display name",
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Model description",
    )
    context_window: Optional[int] = Field(
        None,
        ge=1000,
        description="Context window size in tokens",
    )
    input_cost_per_1k: Decimal = Field(
        ...,
        ge=0,
        description="Input cost per 1k tokens (USD)",
    )
    output_cost_per_1k: Decimal = Field(
        ...,
        ge=0,
        description="Output cost per 1k tokens (USD)",
    )
    max_output_tokens: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum output tokens",
    )
    supports_streaming: bool = Field(
        default=True,
        description="Whether model supports streaming",
    )
    agent_types: Optional[List[str]] = Field(
        default=None,
        description="Agent types to enable for (null = all)",
    )

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        """Ensure model_id is clean."""
        if not v.strip():
            raise ValueError("model_id cannot be empty")
        return v.strip()


class RegisterDeepInfraModelRequest(BaseModel):
    """Request to register new DeepInfra model."""

    model_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="DeepInfra model ID (e.g., 'meta-llama/Llama-3.3-70B-Instruct')",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable display name",
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Model description",
    )
    context_window: Optional[int] = Field(
        None,
        ge=1000,
        description="Context window size in tokens",
    )
    input_cost_per_1k: Decimal = Field(
        ...,
        ge=0,
        description="Input cost per 1k tokens (USD)",
    )
    output_cost_per_1k: Decimal = Field(
        ...,
        ge=0,
        description="Output cost per 1k tokens (USD)",
    )
    max_output_tokens: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum output tokens",
    )
    supports_streaming: bool = Field(
        default=True,
        description="Whether model supports streaming",
    )
    agent_types: Optional[List[str]] = Field(
        default=None,
        description="Agent types to enable for (null = all)",
    )

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        """Ensure model_id is clean."""
        if not v.strip():
            raise ValueError("model_id cannot be empty")
        return v.strip()
