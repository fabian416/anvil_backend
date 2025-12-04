"""
Admin Retry System API Schemas.

Request and response models for retry system admin endpoints.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Request Models

class DisableServiceRequest(BaseModel):
    """Request to disable a service."""
    reason: str = Field(..., description="Reason for disabling the service")
    duration_minutes: Optional[int] = Field(
        None,
        description="Auto re-enable after this duration (None = permanent)",
        ge=1,
    )


class EnableServiceRequest(BaseModel):
    """Request to enable a service."""
    reason: str = Field(..., description="Reason for enabling the service")


class ResetCircuitBreakerRequest(BaseModel):
    """Request to reset a circuit breaker."""
    reason: str = Field(..., description="Reason for resetting the circuit breaker")


# Response Models

class ServiceStatusResponse(BaseModel):
    """Response with service status."""
    service_name: str
    enabled: bool
    circuit_state: str  # CLOSED, OPEN, HALF_OPEN
    failure_count: int
    success_count: int
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    override_reason: Optional[str] = None
    override_expires_at: Optional[datetime] = None


class ServiceListResponse(BaseModel):
    """Response with list of services."""
    services: List[ServiceStatusResponse]


class CircuitBreakerStatusResponse(BaseModel):
    """Response with circuit breaker status."""
    service_name: str
    state: str  # CLOSED, OPEN, HALF_OPEN
    failure_count: int
    success_count: int
    opened_at: Optional[datetime] = None
    config: dict


class ServiceMetricDay(BaseModel):
    """Metrics for a single day."""
    date: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    retry_attempts: int
    avg_latency_ms: float
    circuit_breaker_opens: int
    success_rate: float


class ServiceMetricsResponse(BaseModel):
    """Response with service metrics over time."""
    service_name: str
    days: int
    metrics: List[ServiceMetricDay]
    summary: dict = Field(
        ...,
        description="Summary statistics (total_requests, avg_success_rate, etc.)",
    )
