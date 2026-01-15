"""
UserEvent entity for tracking user activity and metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from app.domain.entities.base import Entity
from app.domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class UserEventId:
    """Value object for UserEvent ID."""
    value: int


@dataclass(eq=False, kw_only=True)
class UserEvent(Entity[UserEventId]):
    """
    Entity representing a user activity event for analytics and metrics.
    """
    user_id: UserId
    event_type: str
    event_category: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    device_type: str | None = None
    platform: str | None = None
    app_version: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    country_code: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        user_id: int,
        event_type: str,
        event_category: str | None = None,
        properties: dict[str, Any] | None = None,
        device_type: str | None = None,
        platform: str | None = None,
        app_version: str | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        country_code: str | None = None,
    ) -> "UserEvent":
        """Factory method to create a new UserEvent."""
        return cls(
            id_=UserEventId(value=0),  # Will be set by database
            user_id=UserId(user_id),
            event_type=event_type,
            event_category=event_category,
            properties=properties or {},
            device_type=device_type,
            platform=platform,
            app_version=app_version,
            session_id=session_id,
            ip_address=ip_address,
            country_code=country_code,
        )


# Common event types for Anvil crypto app
class EventTypes:
    """Standard event types for the Anvil platform."""

    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    WALLET_CONNECTED = "wallet_connected"
    WALLET_DISCONNECTED = "wallet_disconnected"

    # Navigation
    PAGE_VIEW = "page_view"
    SCREEN_VIEW = "screen_view"

    # Trading
    SWAP_INITIATED = "swap_initiated"
    SWAP_COMPLETED = "swap_completed"
    SWAP_FAILED = "swap_failed"

    # Earn/Yield
    EARN_DEPOSIT_INITIATED = "earn_deposit_initiated"
    EARN_DEPOSIT_COMPLETED = "earn_deposit_completed"
    EARN_WITHDRAW_INITIATED = "earn_withdraw_initiated"
    EARN_WITHDRAW_COMPLETED = "earn_withdraw_completed"

    # DCA/Save
    SAVE_SCHEDULE_CREATED = "save_schedule_created"
    SAVE_SCHEDULE_PAUSED = "save_schedule_paused"
    SAVE_SCHEDULE_RESUMED = "save_schedule_resumed"
    SAVE_SCHEDULE_CANCELLED = "save_schedule_cancelled"
    SAVE_EXECUTION = "save_execution"

    # Perpetuals
    PERP_POSITION_OPENED = "perp_position_opened"
    PERP_POSITION_CLOSED = "perp_position_closed"
    PERP_ORDER_PLACED = "perp_order_placed"

    # AI Assistant
    AI_CHAT_STARTED = "ai_chat_started"
    AI_MESSAGE_SENT = "ai_message_sent"

    # Subscription
    SUBSCRIPTION_STARTED = "subscription_started"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"

    # Bitcoin transactions
    BTC_SEND_INITIATED = "btc_send_initiated"
    BTC_SEND_COMPLETED = "btc_send_completed"
    BTC_SEND_FAILED = "btc_send_failed"

    # Errors
    ERROR_OCCURRED = "error_occurred"


class EventCategories:
    """Event categories for grouping."""

    AUTH = "auth"
    NAVIGATION = "navigation"
    TRADING = "trading"
    EARN = "earn"
    SAVE = "save"
    PERPETUALS = "perpetuals"
    AI = "ai"
    SUBSCRIPTION = "subscription"
    BITCOIN = "bitcoin"
    ERROR = "error"
