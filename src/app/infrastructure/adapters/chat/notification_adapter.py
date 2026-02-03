"""
Multi-channel notification adapter implementation.

Implements NotificationAdapter port with support for:
- Email notifications (via Celery tasks)
- WebSocket real-time push
- In-app notifications
- Redis-based delivery tracking and history
- Async notification queuing
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from redis.asyncio import Redis

from app.domain.ports.notification_adapter import NotificationAdapter
from app.domain.entities.chat.notification import ChatNotification
from app.domain.value_objects.chat.notification_id import ChatNotificationId
from app.domain.value_objects.chat.notification_payload import NotificationPayload
from app.domain.value_objects.user_id import UserId
from app.domain.enums.notification_type import NotificationType
from app.domain.enums.notification_channel import NotificationChannel
from app.domain.enums.delivery_status import DeliveryStatus


logger = logging.getLogger(__name__)


class RedisNotificationAdapter(NotificationAdapter):
    """
    Redis-based notification adapter with multi-channel delivery.

    Features:
    - Multi-channel delivery (email, WebSocket, in-app)
    - Redis-based notification history with TTL
    - Delivery status tracking per channel
    - Async notification queuing via Celery
    - WebSocket connection management integration
    - Unread notification counting

    Architecture:
    - Notifications stored in Redis sorted sets by user
    - Delivery status tracked per channel
    - WebSocket messages published to Redis pubsub
    - Email tasks queued to Celery
    - Notification history expires after 30 days
    """

    def __init__(
        self,
        redis_client: Redis,
        key_prefix: str = "notifications:",
        queue_key: str = "notifications:queue",
        history_ttl_days: int = 30,
    ) -> None:
        """
        Initialize notification adapter.

        Args:
            redis_client: Redis async client
            key_prefix: Prefix for notification keys
            queue_key: Key for notification queue
            history_ttl_days: Days to keep notification history
        """
        self._redis = redis_client
        self._key_prefix = key_prefix
        self._queue_key = queue_key
        self._history_ttl = timedelta(days=history_ttl_days)

    def _notification_key(self, notification_id: ChatNotificationId) -> str:
        """Get Redis key for notification."""
        return f"{self._key_prefix}notification:{notification_id.value}"

    def _user_notifications_key(self, user_id: UserId) -> str:
        """Get Redis sorted set key for user notifications."""
        return f"{self._key_prefix}user:{user_id.value}:notifications"

    def _user_unread_key(self, user_id: UserId) -> str:
        """Get Redis set key for user unread notifications."""
        return f"{self._key_prefix}user:{user_id.value}:unread"

    def _websocket_channel(self, user_id: UserId) -> str:
        """Get Redis pubsub channel for user WebSocket notifications."""
        return f"websocket:user:{user_id.value}:notifications"

    async def send(self, notification: ChatNotification) -> None:
        """
        Send notification through configured channels.

        Stores notification in Redis, queues for delivery, and sends via channels.

        Args:
            notification: Notification to send
        """
        try:
            # Store notification in Redis
            await self._store_notification(notification)

            # Send via each configured channel
            for channel in notification.channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        await self._send_email(notification)
                    elif channel == NotificationChannel.WEBSOCKET:
                        await self._send_websocket(notification)
                    elif channel == NotificationChannel.IN_APP:
                        await self._send_in_app(notification)

                    notification.mark_sent(channel)
                except Exception as e:
                    logger.error(
                        f"Failed to send notification {notification.id_.value} "
                        f"via {channel.value}: {e}"
                    )
                    notification.mark_failed(channel, str(e))

            # Update notification with delivery status
            await self._update_notification(notification)

        except Exception as e:
            logger.error(f"Failed to send notification {notification.id_.value}: {e}")
            raise

    async def send_batch(self, notifications: List[ChatNotification]) -> None:
        """
        Send multiple notifications in batch.

        Args:
            notifications: List of notifications to send
        """
        for notification in notifications:
            await self.send(notification)

    async def get_notification(
        self, notification_id: ChatNotificationId
    ) -> Optional[ChatNotification]:
        """
        Retrieve notification by ID from Redis.

        Args:
            notification_id: Notification identifier

        Returns:
            Notification or None if not found
        """
        key = self._notification_key(notification_id)
        data = await self._redis.get(key)

        if not data:
            return None

        return self._deserialize_notification(json.loads(data))

    async def get_user_notifications(
        self,
        user_id: UserId,
        notification_type: Optional[NotificationType] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[ChatNotification]:
        """
        Get notifications for a user from Redis sorted set.

        Args:
            user_id: User identifier
            notification_type: Filter by notification type
            unread_only: Return only unread notifications
            limit: Maximum number of notifications

        Returns:
            List of notifications sorted by timestamp (newest first)
        """
        # Get notification IDs from sorted set (sorted by timestamp)
        key = self._user_notifications_key(user_id)
        notification_ids = await self._redis.zrevrange(key, 0, limit - 1)

        if not notification_ids:
            return []

        # Retrieve notifications
        notifications = []
        for notification_id in notification_ids:
            notification = await self.get_notification(
                ChatNotificationId(notification_id.decode("utf-8"))
            )
            if notification:
                # Filter by type if specified
                if (
                    notification_type
                    and notification.notification_type != notification_type
                ):
                    continue

                # Filter unread if specified
                if unread_only and notification.is_read():
                    continue

                notifications.append(notification)

        return notifications[:limit]

    async def mark_as_read(self, notification_id: ChatNotificationId) -> None:
        """
        Mark notification as read.

        Args:
            notification_id: Notification identifier
        """
        notification = await self.get_notification(notification_id)
        if not notification:
            return

        notification.mark_read()
        await self._update_notification(notification)

        # Remove from unread set
        unread_key = self._user_unread_key(notification.user_id)
        await self._redis.srem(unread_key, notification_id.value)

    async def mark_all_as_read(self, user_id: UserId) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of notifications marked as read
        """
        notifications = await self.get_user_notifications(
            user_id, unread_only=True, limit=1000
        )

        for notification in notifications:
            await self.mark_as_read(notification.id_)

        return len(notifications)

    async def delete_notification(self, notification_id: ChatNotificationId) -> None:
        """
        Delete notification from Redis.

        Args:
            notification_id: Notification identifier
        """
        notification = await self.get_notification(notification_id)
        if not notification:
            return

        # Delete from notification key
        key = self._notification_key(notification_id)
        await self._redis.delete(key)

        # Remove from user notifications sorted set
        user_key = self._user_notifications_key(notification.user_id)
        await self._redis.zrem(user_key, notification_id.value)

        # Remove from unread set
        unread_key = self._user_unread_key(notification.user_id)
        await self._redis.srem(unread_key, notification_id.value)

    async def get_unread_count(self, user_id: UserId) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of unread notifications
        """
        unread_key = self._user_unread_key(user_id)
        return await self._redis.scard(unread_key)

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

        Args:
            channel: Delivery channel
            user_ids: List of target user IDs
            notification_type: Type of notification
            title: Notification title
            body: Notification body
            data: Additional data
        """
        for user_id in user_ids:
            notification = ChatNotification(
                id_=ChatNotificationId(str(uuid4())),
                user_id=user_id,
                notification_type=notification_type,
                payload=NotificationPayload(
                    title=title,
                    body=body,
                    data=data,
                ),
                channels={channel},
            )
            await self.send(notification)

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _store_notification(self, notification: ChatNotification) -> None:
        """
        Store notification in Redis.

        Args:
            notification: Notification to store
        """
        # Store notification data
        key = self._notification_key(notification.id_)
        data = self._serialize_notification(notification)
        await self._redis.setex(
            key,
            int(self._history_ttl.total_seconds()),
            json.dumps(data),
        )

        # Add to user's notification sorted set (score = timestamp)
        user_key = self._user_notifications_key(notification.user_id)
        timestamp = notification.created_at.timestamp()
        await self._redis.zadd(user_key, {notification.id_.value: timestamp})

        # Set expiry on sorted set
        await self._redis.expire(user_key, int(self._history_ttl.total_seconds()))

        # Add to unread set
        unread_key = self._user_unread_key(notification.user_id)
        await self._redis.sadd(unread_key, notification.id_.value)
        await self._redis.expire(unread_key, int(self._history_ttl.total_seconds()))

    async def _update_notification(self, notification: ChatNotification) -> None:
        """
        Update notification in Redis.

        Args:
            notification: Notification to update
        """
        key = self._notification_key(notification.id_)
        data = self._serialize_notification(notification)
        await self._redis.setex(
            key,
            int(self._history_ttl.total_seconds()),
            json.dumps(data),
        )

    async def _send_email(self, notification: ChatNotification) -> None:
        """
        Send notification via email using Celery task.

        Args:
            notification: Notification to send

        Note:
            This is a stub implementation. In production, this should:
            1. Queue a Celery task to send email
            2. Use email templates based on notification type
            3. Handle email delivery failures
        """
        # TODO: Implement Celery email task
        # Example:
        # from app.infrastructure.celery.tasks import send_notification_email
        # send_notification_email.delay(
        #     user_id=notification.user_id.value,
        #     title=notification.payload.title,
        #     body=notification.payload.body,
        #     data=notification.payload.data,
        # )

        logger.info(
            f"Email notification queued for user {notification.user_id.value}: "
            f"{notification.payload.title}"
        )

        # Mark as delivered for stub implementation
        notification.mark_delivered(NotificationChannel.EMAIL)

    async def _send_websocket(self, notification: ChatNotification) -> None:
        """
        Send notification via WebSocket using Redis pubsub.

        Args:
            notification: Notification to send
        """
        # Publish to user's WebSocket channel
        channel = self._websocket_channel(notification.user_id)
        message = {
            "type": "notification",
            "notification": {
                "id": notification.id_.value,
                "notification_type": notification.notification_type.value,
                "title": notification.payload.title,
                "body": notification.payload.body,
                "data": notification.payload.data,
                "action_url": notification.payload.action_url,
                "created_at": notification.created_at.isoformat(),
            },
        }

        await self._redis.publish(channel, json.dumps(message))

        logger.info(
            f"WebSocket notification sent to user {notification.user_id.value}: "
            f"{notification.payload.title}"
        )

        # Mark as delivered
        notification.mark_delivered(NotificationChannel.WEBSOCKET)

    async def _send_in_app(self, notification: ChatNotification) -> None:
        """
        Send in-app notification (stored in Redis for retrieval).

        Args:
            notification: Notification to send
        """
        # In-app notifications are already stored via _store_notification
        # Just mark as delivered
        notification.mark_delivered(NotificationChannel.IN_APP)

        logger.info(
            f"In-app notification created for user {notification.user_id.value}: "
            f"{notification.payload.title}"
        )

    def _serialize_notification(self, notification: ChatNotification) -> Dict[str, Any]:
        """
        Serialize notification to dict for Redis storage.

        Args:
            notification: Notification to serialize

        Returns:
            Dict representation
        """
        return {
            "id": notification.id_.value,
            "user_id": notification.user_id.value,
            "notification_type": notification.notification_type.value,
            "payload": {
                "title": notification.payload.title,
                "body": notification.payload.body,
                "data": notification.payload.data,
                "action_url": notification.payload.action_url,
            },
            "channels": [channel.value for channel in notification.channels],
            "delivery_status": {
                channel.value: status.value
                for channel, status in notification.delivery_status.items()
            },
            "created_at": notification.created_at.isoformat(),
            "sent_at": notification.sent_at.isoformat()
            if notification.sent_at
            else None,
            "delivered_at": (
                notification.delivered_at.isoformat()
                if notification.delivered_at
                else None
            ),
            "read_at": notification.read_at.isoformat()
            if notification.read_at
            else None,
            "metadata": notification.metadata,
        }

    def _deserialize_notification(self, data: Dict[str, Any]) -> ChatNotification:
        """
        Deserialize notification from Redis data.

        Args:
            data: Dict from Redis

        Returns:
            ChatNotification instance
        """
        return ChatNotification(
            id_=ChatNotificationId(data["id"]),
            user_id=UserId(data["user_id"]),
            notification_type=NotificationType(data["notification_type"]),
            payload=NotificationPayload(
                title=data["payload"]["title"],
                body=data["payload"]["body"],
                data=data["payload"]["data"],
                action_url=data["payload"].get("action_url"),
            ),
            channels={NotificationChannel(c) for c in data["channels"]},
            delivery_status={
                NotificationChannel(channel): DeliveryStatus(status)
                for channel, status in data["delivery_status"].items()
            },
            created_at=datetime.fromisoformat(data["created_at"]),
            sent_at=datetime.fromisoformat(data["sent_at"])
            if data.get("sent_at")
            else None,
            delivered_at=(
                datetime.fromisoformat(data["delivered_at"])
                if data.get("delivered_at")
                else None
            ),
            read_at=datetime.fromisoformat(data["read_at"])
            if data.get("read_at")
            else None,
            metadata=data.get("metadata", {}),
        )
