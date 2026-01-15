"""
Chat notification entity for the hexagonal architecture.

Represents a notification that can be sent through multiple channels
(email, WebSocket, in-app) with delivery tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Optional, Set

from app.domain.entities.base import Entity
from app.domain.value_objects.chat.notification_id import ChatNotificationId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.chat.notification_payload import NotificationPayload
from app.domain.enums.notification_type import NotificationType
from app.domain.enums.notification_channel import NotificationChannel
from app.domain.enums.delivery_status import DeliveryStatus


@dataclass(eq=False, kw_only=True, slots=True)
class ChatNotification(Entity[ChatNotificationId]):
    """
    Chat notification entity.

    Represents a notification with multi-channel delivery support
    and comprehensive delivery tracking.

    Attributes:
        id_: Unique notification identifier
        user_id: Target user ID
        notification_type: Type of notification
        payload: Notification content and data
        channels: Target delivery channels
        delivery_status: Current delivery status per channel
        created_at: Notification creation timestamp
        sent_at: Timestamp when notification was sent
        delivered_at: Timestamp when notification was delivered
        read_at: Timestamp when notification was read
        metadata: Additional metadata for tracking
    """

    user_id: UserId
    notification_type: NotificationType
    payload: NotificationPayload
    channels: Set[NotificationChannel]
    delivery_status: Dict[NotificationChannel, DeliveryStatus] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize delivery status for all channels."""
        for channel in self.channels:
            if channel not in self.delivery_status:
                self.delivery_status[channel] = DeliveryStatus.QUEUED

    def mark_sent(self, channel: NotificationChannel) -> None:
        """
        Mark notification as sent for a specific channel.

        Args:
            channel: Delivery channel
        """
        self.delivery_status[channel] = DeliveryStatus.SENT
        if not self.sent_at:
            self.sent_at = datetime.now(UTC)

    def mark_delivered(self, channel: NotificationChannel) -> None:
        """
        Mark notification as delivered for a specific channel.

        Args:
            channel: Delivery channel
        """
        self.delivery_status[channel] = DeliveryStatus.DELIVERED
        if not self.delivered_at:
            self.delivered_at = datetime.now(UTC)

    def mark_read(self) -> None:
        """Mark notification as read by user."""
        for channel in self.channels:
            if self.delivery_status[channel] == DeliveryStatus.DELIVERED:
                self.delivery_status[channel] = DeliveryStatus.READ
        self.read_at = datetime.now(UTC)

    def mark_failed(self, channel: NotificationChannel, error: str) -> None:
        """
        Mark notification delivery as failed for a specific channel.

        Args:
            channel: Delivery channel
            error: Error message
        """
        self.delivery_status[channel] = DeliveryStatus.FAILED
        self.metadata[f"{channel.value}_error"] = error

    def is_delivered(self) -> bool:
        """
        Check if notification has been delivered on all channels.

        Returns:
            True if delivered on all channels
        """
        return all(
            status in (DeliveryStatus.DELIVERED, DeliveryStatus.READ)
            for status in self.delivery_status.values()
        )

    def is_read(self) -> bool:
        """
        Check if notification has been read.

        Returns:
            True if read
        """
        return self.read_at is not None
