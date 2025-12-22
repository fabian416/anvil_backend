"""
Notification adapter port.

Defines the interface for sending notifications through multiple channels
with delivery tracking and queuing support.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat.notification import ChatNotification
from app.domain.value_objects.chat.notification_id import ChatNotificationId
from app.domain.value_objects.user_id import UserId
from app.domain.enums.notification_type import NotificationType
from app.domain.enums.notification_channel import NotificationChannel


class NotificationAdapter(ABC):
    """
    Port for notification delivery adapter.

    Provides multi-channel notification delivery with:
    - Email notifications
    - WebSocket real-time push
    - In-app notifications
    - Delivery tracking (sent, delivered, read)
    - Async queuing for delivery
    - Redis-based notification history
    """

    @abstractmethod
    async def send(self, notification: ChatNotification) -> None:
        """
        Send notification through configured channels.

        Queues notification for async delivery and updates delivery status.

        Args:
            notification: Notification to send

        Raises:
            NotificationError: If delivery fails critically
        """
        ...

    @abstractmethod
    async def send_batch(self, notifications: List[ChatNotification]) -> None:
        """
        Send multiple notifications in batch.

        More efficient for bulk operations like daily summaries.

        Args:
            notifications: List of notifications to send
        """
        ...

    @abstractmethod
    async def get_notification(
        self, notification_id: ChatNotificationId
    ) -> Optional[ChatNotification]:
        """
        Retrieve notification by ID from history.

        Args:
            notification_id: Notification identifier

        Returns:
            Notification or None if not found
        """
        ...

    @abstractmethod
    async def get_user_notifications(
        self,
        user_id: UserId,
        notification_type: Optional[NotificationType] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[ChatNotification]:
        """
        Get notifications for a user.

        Args:
            user_id: User identifier
            notification_type: Filter by notification type
            unread_only: Return only unread notifications
            limit: Maximum number of notifications

        Returns:
            List of notifications
        """
        ...

    @abstractmethod
    async def mark_as_read(self, notification_id: ChatNotificationId) -> None:
        """
        Mark notification as read.

        Updates delivery status and read timestamp.

        Args:
            notification_id: Notification identifier
        """
        ...

    @abstractmethod
    async def mark_all_as_read(self, user_id: UserId) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of notifications marked as read
        """
        ...

    @abstractmethod
    async def delete_notification(self, notification_id: ChatNotificationId) -> None:
        """
        Delete notification from history.

        Args:
            notification_id: Notification identifier
        """
        ...

    @abstractmethod
    async def get_unread_count(self, user_id: UserId) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of unread notifications
        """
        ...

    @abstractmethod
    async def broadcast_to_channel(
        self,
        channel: NotificationChannel,
        user_ids: List[UserId],
        notification_type: NotificationType,
        title: str,
        body: str,
        data: dict,
    ) -> None:
        """
        Broadcast notification to multiple users on a specific channel.

        Useful for system announcements or bulk alerts.

        Args:
            channel: Delivery channel
            user_ids: List of target user IDs
            notification_type: Type of notification
            title: Notification title
            body: Notification body
            data: Additional data
        """
        ...
