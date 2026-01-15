"""
Get Metrics endpoints - for querying user metrics.
"""

from datetime import datetime, timedelta, UTC
from typing import Annotated, Any, Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Query, Security, status
from fastapi_error_map import rule
from pydantic import BaseModel, Field

from app.application.common.services.current_user import CurrentUserService
from app.application.metrics.ports import UserMetricsRepository, UserEventFilter
from app.domain.exceptions.auth import InsufficientPermissionsError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.controllers.metrics.router import router
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class UserMetricsSummaryResponse(BaseModel):
    """Response schema for user metrics summary."""
    user_id: int
    total_events: int
    first_event_at: Optional[str]
    last_event_at: Optional[str]
    events_by_category: dict[str, int]
    events_by_type: dict[str, int]
    devices_used: list[str]
    platforms_used: list[str]


class EventListResponse(BaseModel):
    """Response schema for event list."""
    events: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


@router.get(
    "/me",
    response_model=UserMetricsSummaryResponse,
    summary="Get My Metrics Summary",
    description="Get a summary of your activity metrics.",
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        DataMapperError: rule(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
    },
    default_on_error=log_info,
)
@inject
async def get_my_metrics(
    metrics_repo: FromDishka[UserMetricsRepository],
    current_user_service: FromDishka[CurrentUserService],
) -> UserMetricsSummaryResponse:
    """Get metrics summary for the authenticated user."""
    current_user = await current_user_service.get_current_user()
    user_id = current_user.id_.value
    
    summary = await metrics_repo.get_user_metrics_summary(user_id)
    
    if not summary:
        return UserMetricsSummaryResponse(
            user_id=user_id,
            total_events=0,
            first_event_at=None,
            last_event_at=None,
            events_by_category={},
            events_by_type={},
            devices_used=[],
            platforms_used=[],
        )
    
    return UserMetricsSummaryResponse(
        user_id=summary["user_id"],
        total_events=summary["total_events"],
        first_event_at=summary["first_event_at"].isoformat() if summary["first_event_at"] else None,
        last_event_at=summary["last_event_at"].isoformat() if summary["last_event_at"] else None,
        events_by_category=summary["events_by_category"],
        events_by_type=summary["events_by_type"],
        devices_used=summary["devices_used"],
        platforms_used=summary["platforms_used"],
    )


@router.get(
    "/me/events",
    response_model=EventListResponse,
    summary="Get My Events",
    description="Get a list of your tracked events with optional filters.",
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        DataMapperError: rule(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
    },
    default_on_error=log_info,
)
@inject
async def get_my_events(
    metrics_repo: FromDishka[UserMetricsRepository],
    current_user_service: FromDishka[CurrentUserService],
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    event_category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> EventListResponse:
    """Get events for the authenticated user."""
    current_user = await current_user_service.get_current_user()
    user_id = current_user.id_.value
    
    filters: UserEventFilter = {
        "user_id": user_id,
        "event_type": event_type,
        "event_category": event_category,
    }
    
    events = await metrics_repo.get_events(filters, limit=limit, offset=offset)
    total = await metrics_repo.get_event_count(user_id=user_id, event_type=event_type)
    
    return EventListResponse(
        events=events,
        total=total,
        limit=limit,
        offset=offset,
    )


# Admin endpoints for viewing all metrics
@router.get(
    "/admin/summary",
    response_model=dict,
    summary="Get Platform Metrics Summary (Admin)",
    description="Get platform-wide metrics summary. Requires admin role.",
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
        DataMapperError: rule(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
    },
    default_on_error=log_info,
)
@inject
async def get_platform_metrics(
    metrics_repo: FromDishka[UserMetricsRepository],
    current_user_service: FromDishka[CurrentUserService],
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
) -> dict:
    """Get platform-wide metrics summary."""
    current_user = await current_user_service.get_current_user()
    
    # Check admin role
    if current_user.role.value != "admin":
        raise InsufficientPermissionsError("Admin access required")
    
    from_date = datetime.now(UTC) - timedelta(days=days)
    
    total_events = await metrics_repo.get_event_count(from_date=from_date)
    active_users = await metrics_repo.get_active_users_count(from_date=from_date)
    
    return {
        "period_days": days,
        "total_events": total_events,
        "active_users": active_users,
        "from_date": from_date.isoformat(),
        "to_date": datetime.now(UTC).isoformat(),
    }
