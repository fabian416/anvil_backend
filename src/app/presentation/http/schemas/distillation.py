"""
Response schemas for distillation endpoints.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DistillationValidationRequest(BaseModel):
    """Request to validate a user message."""
    
    message: str = Field(
        ...,
        description="User message to validate",
        min_length=1,
        max_length=10000,
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Optional conversation ID for context",
    )


class DistillationValidationResponse(BaseModel):
    """Response from distillation validation."""
    
    success: bool = Field(
        ...,
        description="Whether the message passed validation",
    )
    message: str = Field(
        ...,
        description="User-facing message in their language",
    )
    reason: str = Field(
        ...,
        description="Reason code (validation_passed, out_of_scope, malicious, etc.)",
    )
    confidence: float = Field(
        ...,
        description="Confidence score (0-1)",
        ge=0.0,
        le=1.0,
    )
    detected_language: str = Field(
        ...,
        description="Detected language code (ISO 639-1)",
    )
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Request validated successfully",
                "reason": "validation_passed",
                "confidence": 0.95,
                "detected_language": "en",
            }
        }


class DistillationMetricsResponse(BaseModel):
    """Aggregated distillation metrics."""
    
    date: datetime = Field(
        ...,
        description="Date for the metrics",
    )
    provider: str = Field(
        ...,
        description="Provider name (vertex_ai or deepinfra)",
    )
    total_requests: int = Field(
        ...,
        description="Total number of requests",
        ge=0,
    )
    successful_requests: int = Field(
        ...,
        description="Number of successful validations",
        ge=0,
    )
    failed_requests: int = Field(
        ...,
        description="Number of failed validations",
        ge=0,
    )
    success_rate: float = Field(
        ...,
        description="Success rate (0-1)",
        ge=0.0,
        le=1.0,
    )
    avg_latency_ms: float = Field(
        ...,
        description="Average latency in milliseconds",
        ge=0.0,
    )
    p95_latency_ms: Optional[float] = Field(
        None,
        description="95th percentile latency in milliseconds",
        ge=0.0,
    )
    avg_confidence: float = Field(
        ...,
        description="Average confidence score",
        ge=0.0,
        le=1.0,
    )
    total_tokens: int = Field(
        ...,
        description="Total tokens used",
        ge=0,
    )
    total_cost_usd: float = Field(
        ...,
        description="Total cost in USD",
        ge=0.0,
    )
    fallback_used_count: int = Field(
        ...,
        description="Number of times fallback was used",
        ge=0,
    )
    
    class Config:
        schema_extra = {
            "example": {
                "date": "2025-12-01T00:00:00Z",
                "provider": "vertex_ai",
                "total_requests": 1000,
                "successful_requests": 850,
                "failed_requests": 150,
                "success_rate": 0.85,
                "avg_latency_ms": 287.5,
                "p95_latency_ms": 450.0,
                "avg_confidence": 0.92,
                "total_tokens": 50000,
                "total_cost_usd": 0.005,
                "fallback_used_count": 12,
            }
        }


class ProviderStatusResponse(BaseModel):
    """Provider health status."""
    
    provider: str = Field(
        ...,
        description="Provider name",
    )
    healthy: bool = Field(
        ...,
        description="Whether the provider is healthy",
    )
    latency_ms: Optional[float] = Field(
        None,
        description="Recent average latency in milliseconds",
        ge=0.0,
    )
    error_rate: Optional[float] = Field(
        None,
        description="Recent error rate (0-1)",
        ge=0.0,
        le=1.0,
    )
    last_check: Optional[datetime] = Field(
        None,
        description="Last health check timestamp",
    )
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "vertex_ai",
                "healthy": True,
                "latency_ms": 287.5,
                "error_rate": 0.02,
                "last_check": "2025-12-01T12:34:56Z",
            }
        }


class DistillationConfigResponse(BaseModel):
    """Current distillation configuration."""
    
    enabled: bool = Field(
        ...,
        description="Whether distillation is enabled",
    )
    provider: str = Field(
        ...,
        description="Primary provider name",
    )
    fallback_provider: str = Field(
        ...,
        description="Fallback provider name",
    )
    temperature: float = Field(
        ...,
        description="LLM temperature",
        ge=0.0,
        le=2.0,
    )
    max_tokens: int = Field(
        ...,
        description="Maximum tokens for validation",
        ge=1,
    )
    timeout_seconds: float = Field(
        ...,
        description="Request timeout in seconds",
        ge=0.1,
    )
    fail_open: bool = Field(
        ...,
        description="Whether to allow requests on provider failure",
    )
    
    class Config:
        schema_extra = {
            "example": {
                "enabled": True,
                "provider": "vertex_ai",
                "fallback_provider": "deepinfra",
                "temperature": 0.3,
                "max_tokens": 200,
                "timeout_seconds": 5.0,
                "fail_open": True,
            }
        }


class DistillationConfigUpdateRequest(BaseModel):
    """Request to update distillation configuration."""
    
    enabled: Optional[bool] = Field(
        None,
        description="Enable or disable distillation",
    )
    provider: Optional[str] = Field(
        None,
        description="Primary provider (vertex_ai or deepinfra)",
    )
    fallback_provider: Optional[str] = Field(
        None,
        description="Fallback provider (vertex_ai or deepinfra)",
    )
    temperature: Optional[float] = Field(
        None,
        description="LLM temperature",
        ge=0.0,
        le=2.0,
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Maximum tokens",
        ge=1,
        le=1000,
    )
    timeout_seconds: Optional[float] = Field(
        None,
        description="Timeout in seconds",
        ge=0.1,
        le=30.0,
    )
    fail_open: Optional[bool] = Field(
        None,
        description="Fail-open mode",
    )


class DistillationHealthResponse(BaseModel):
    """Overall distillation system health."""
    
    healthy: bool = Field(
        ...,
        description="Whether the system is healthy",
    )
    primary_provider: ProviderStatusResponse = Field(
        ...,
        description="Primary provider status",
    )
    fallback_provider: ProviderStatusResponse = Field(
        ...,
        description="Fallback provider status",
    )
    telemetry_enabled: bool = Field(
        ...,
        description="Whether telemetry is enabled",
    )
    
    class Config:
        schema_extra = {
            "example": {
                "healthy": True,
                "primary_provider": {
                    "provider": "vertex_ai",
                    "healthy": True,
                    "latency_ms": 287.5,
                    "error_rate": 0.02,
                    "last_check": "2025-12-01T12:34:56Z",
                },
                "fallback_provider": {
                    "provider": "deepinfra",
                    "healthy": True,
                    "latency_ms": 412.3,
                    "error_rate": 0.03,
                    "last_check": "2025-12-01T12:34:56Z",
                },
                "telemetry_enabled": True,
            }
        }
