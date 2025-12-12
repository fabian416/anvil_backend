"""
Track Event endpoint - for ingesting user events/metrics.
"""

from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Request, Security, status
from fastapi_error_map import rule
from pydantic import BaseModel, Field

from app.application.common.services.current_user import CurrentUserService
from app.application.metrics.ports import UserMetricsRepository
from app.domain.entities.user_event import EventTypes, UserEvent
from app.domain.exceptions.base import DomainFieldError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.controllers.metrics.router import router
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class TrackEventRequest(BaseModel):
    """Request schema for tracking an event."""
    event_type: str = Field(..., description="Type of event (e.g., 'login', 'swap_completed')")
    event_category: str | None = Field(None, description="Category (e.g., 'auth', 'trading')")
    properties: dict[str, Any] | None = Field(default_factory=dict, description="Event-specific properties")
    device_type: str | None = Field(None, description="Device type: mobile, desktop, tablet")
    platform: str | None = Field(None, description="Platform: ios, android, web")
    app_version: str | None = Field(None, description="App version")
    session_id: str | None = Field(None, description="Session identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "swap_completed",
                "event_category": "trading",
                "properties": {
                    "from_token": "ETH",
                    "to_token": "USDC",
                    "amount": "1.5",
                    "chain": "ethereum"
                },
                "device_type": "mobile",
                "platform": "ios",
                "app_version": "1.0.0",
                "session_id": "sess_abc123"
            }
        }


class TrackEventResponse(BaseModel):
    """Response schema for track event."""
    success: bool
    event_id: int
    message: str = "Event tracked successfully"


class EventTypesResponse(BaseModel):
    """Response with available event types."""

    auth: list[str]
    navigation: list[str]
    trading: list[str]
    earn: list[str]
    save: list[str]
    perpetuals: list[str]
    ai: list[str]
    subscription: list[str]
    bitcoin: list[str]
    error: list[str]


@router.post(
    "/track",
    response_model=TrackEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Track User Event",
    description="""
    Track a user event for analytics and metrics.
    
    **Common Event Types:**
    - Authentication: login, logout, signup, wallet_connected
    - Trading: swap_initiated, swap_completed, swap_failed
    - Earn: earn_deposit_initiated, earn_deposit_completed
    - Save/DCA: save_schedule_created, save_execution
    - AI: ai_chat_started, ai_message_sent
    
    **Properties:**
    Include any event-specific data in the properties object.
    """,
    dependencies=[Security(bearer_scheme)],
    error_map={
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        DomainFieldError: status.HTTP_400_BAD_REQUEST,
        DataMapperError: rule(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        ValueError: status.HTTP_400_BAD_REQUEST,
    },
    default_on_error=log_info,
)
@inject
async def track_event(
    request_body: TrackEventRequest,
    request: Request,
    metrics_repo: FromDishka[UserMetricsRepository],
    current_user_service: FromDishka[CurrentUserService],
) -> TrackEventResponse:
    """Track a user event."""
    # Get current user from session
    current_user = await current_user_service.get_current_user()
    user_id = current_user.id_.value

    # Get client IP
    client_ip = request.client.host if request.client else None

    # Create event
    event = UserEvent.create(
        user_id=user_id,
        event_type=request_body.event_type,
        event_category=request_body.event_category,
        properties=request_body.properties,
        device_type=request_body.device_type,
        platform=request_body.platform,
        app_version=request_body.app_version,
        session_id=request_body.session_id,
        ip_address=client_ip,
    )

    event_id = await metrics_repo.record_event(event)

    return TrackEventResponse(
        success=True,
        event_id=event_id,
    )


@router.get(
    "/event-types",
    response_model=EventTypesResponse,
    summary="Get Available Event Types",
    description="Get a list of standard event types organized by category.",
)
async def get_event_types() -> EventTypesResponse:
    """Return available event types."""
    return EventTypesResponse(
        auth=[
            EventTypes.LOGIN,
            EventTypes.LOGOUT,
            EventTypes.SIGNUP,
            EventTypes.WALLET_CONNECTED,
            EventTypes.WALLET_DISCONNECTED,
        ],
        navigation=[
            EventTypes.PAGE_VIEW,
            EventTypes.SCREEN_VIEW,
        ],
        trading=[
            EventTypes.SWAP_INITIATED,
            EventTypes.SWAP_COMPLETED,
            EventTypes.SWAP_FAILED,
        ],
        earn=[
            EventTypes.EARN_DEPOSIT_INITIATED,
            EventTypes.EARN_DEPOSIT_COMPLETED,
            EventTypes.EARN_WITHDRAW_INITIATED,
            EventTypes.EARN_WITHDRAW_COMPLETED,
        ],
        save=[
            EventTypes.SAVE_SCHEDULE_CREATED,
            EventTypes.SAVE_SCHEDULE_PAUSED,
            EventTypes.SAVE_SCHEDULE_RESUMED,
            EventTypes.SAVE_SCHEDULE_CANCELLED,
            EventTypes.SAVE_EXECUTION,
        ],
        perpetuals=[
            EventTypes.PERP_POSITION_OPENED,
            EventTypes.PERP_POSITION_CLOSED,
            EventTypes.PERP_ORDER_PLACED,
        ],
        ai=[
            EventTypes.AI_CHAT_STARTED,
            EventTypes.AI_MESSAGE_SENT,
        ],
        subscription=[
            EventTypes.SUBSCRIPTION_STARTED,
            EventTypes.SUBSCRIPTION_CANCELLED,
            EventTypes.SUBSCRIPTION_UPGRADED,
        ],
        bitcoin=[
            EventTypes.BTC_SEND_INITIATED,
            EventTypes.BTC_SEND_COMPLETED,
            EventTypes.BTC_SEND_FAILED,
        ],
        error=[
            EventTypes.ERROR_OCCURRED,
        ],
    )
