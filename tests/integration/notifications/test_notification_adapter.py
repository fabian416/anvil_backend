"""
Integration tests for notification adapter.

Tests multi-channel notification delivery with Redis.
"""

import pytest
from uuid import uuid4

from app.domain.entities.chat.notification import ChatNotification
from app.domain.value_objects.chat.notification_id import ChatNotificationId
from app.domain.value_objects.chat.notification_payload import NotificationPayload
from app.domain.value_objects.user_id import UserId
from app.domain.enums.notification_type import NotificationType
from app.domain.enums.notification_channel import NotificationChannel
from app.domain.enums.delivery_status import DeliveryStatus
from app.infrastructure.adapters.chat.notification_adapter import (
    RedisNotificationAdapter,
)


@pytest.fixture
async def notification_adapter(redis_client):
    """Provide notification adapter with Redis client."""
    adapter = RedisNotificationAdapter(
        redis_client=redis_client,
        key_prefix="test:notifications:",
        queue_key="test:notifications:queue",
        history_ttl_days=1,
    )
    yield adapter

    # Cleanup: Delete all test keys
    keys = await redis_client.keys("test:notifications:*")
    if keys:
        await redis_client.delete(*keys)


@pytest.fixture
def sample_notification():
    """Create sample notification for testing."""
    return ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=UserId(123),
        notification_type=NotificationType.CONVERSATION_UPDATE,
        payload=NotificationPayload(
            title="Test Notification",
            body="This is a test notification",
            data={"test_key": "test_value"},
            action_url="/test",
        ),
        channels={NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP},
    )


@pytest.mark.asyncio
class TestNotificationAdapter:
    """Test suite for notification adapter."""

    async def test_send_notification(self, notification_adapter, sample_notification):
        """Test sending a notification stores it in Redis."""
        await notification_adapter.send(sample_notification)

        # Retrieve notification
        retrieved = await notification_adapter.get_notification(sample_notification.id_)

        assert retrieved is not None
        assert retrieved.id_ == sample_notification.id_
        assert retrieved.user_id == sample_notification.user_id
        assert retrieved.payload.title == sample_notification.payload.title
        assert retrieved.notification_type == sample_notification.notification_type

    async def test_send_updates_delivery_status(
        self, notification_adapter, sample_notification
    ):
        """Test sending updates delivery status for each channel."""
        await notification_adapter.send(sample_notification)

        retrieved = await notification_adapter.get_notification(sample_notification.id_)

        # WebSocket and in-app should be delivered
        assert (
            retrieved.delivery_status[NotificationChannel.WEBSOCKET]
            == DeliveryStatus.DELIVERED
        )
        assert (
            retrieved.delivery_status[NotificationChannel.IN_APP]
            == DeliveryStatus.DELIVERED
        )

    async def test_get_user_notifications(
        self, notification_adapter, sample_notification
    ):
        """Test retrieving notifications for a user."""
        # Send multiple notifications
        notification1 = sample_notification
        notification2 = ChatNotification(
            id_=ChatNotificationId(str(uuid4())),
            user_id=sample_notification.user_id,
            notification_type=NotificationType.ALERT,
            payload=NotificationPayload(title="Alert", body="Test alert", data={}),
            channels={NotificationChannel.IN_APP},
        )

        await notification_adapter.send(notification1)
        await notification_adapter.send(notification2)

        # Retrieve notifications
        notifications = await notification_adapter.get_user_notifications(
            user_id=sample_notification.user_id,
            limit=10,
        )

        assert len(notifications) == 2
        assert notifications[0].user_id == sample_notification.user_id

    async def test_filter_by_notification_type(
        self, notification_adapter, sample_notification
    ):
        """Test filtering notifications by type."""
        # Send different types
        await notification_adapter.send(sample_notification)

        alert_notification = ChatNotification(
            id_=ChatNotificationId(str(uuid4())),
            user_id=sample_notification.user_id,
            notification_type=NotificationType.ALERT,
            payload=NotificationPayload(title="Alert", body="Test alert", data={}),
            channels={NotificationChannel.IN_APP},
        )
        await notification_adapter.send(alert_notification)

        # Filter by type
        conversation_updates = await notification_adapter.get_user_notifications(
            user_id=sample_notification.user_id,
            notification_type=NotificationType.CONVERSATION_UPDATE,
            limit=10,
        )

        assert len(conversation_updates) == 1
        assert (
            conversation_updates[0].notification_type
            == NotificationType.CONVERSATION_UPDATE
        )

    async def test_filter_unread_only(self, notification_adapter, sample_notification):
        """Test filtering unread notifications."""
        await notification_adapter.send(sample_notification)

        # Mark as read
        await notification_adapter.mark_as_read(sample_notification.id_)

        # Get unread only
        unread = await notification_adapter.get_user_notifications(
            user_id=sample_notification.user_id,
            unread_only=True,
            limit=10,
        )

        assert len(unread) == 0

    async def test_mark_as_read(self, notification_adapter, sample_notification):
        """Test marking notification as read."""
        await notification_adapter.send(sample_notification)

        # Mark as read
        await notification_adapter.mark_as_read(sample_notification.id_)

        # Retrieve and check
        retrieved = await notification_adapter.get_notification(sample_notification.id_)

        assert retrieved.is_read()
        assert retrieved.read_at is not None

    async def test_mark_all_as_read(self, notification_adapter, sample_notification):
        """Test marking all notifications as read for a user."""
        # Send multiple notifications
        await notification_adapter.send(sample_notification)

        notification2 = ChatNotification(
            id_=ChatNotificationId(str(uuid4())),
            user_id=sample_notification.user_id,
            notification_type=NotificationType.ALERT,
            payload=NotificationPayload(title="Alert", body="Test alert", data={}),
            channels={NotificationChannel.IN_APP},
        )
        await notification_adapter.send(notification2)

        # Mark all as read
        count = await notification_adapter.mark_all_as_read(sample_notification.user_id)

        assert count == 2

        # Verify no unread notifications
        unread_count = await notification_adapter.get_unread_count(
            sample_notification.user_id
        )
        assert unread_count == 0

    async def test_get_unread_count(self, notification_adapter, sample_notification):
        """Test getting unread notification count."""
        # Initially 0
        count = await notification_adapter.get_unread_count(sample_notification.user_id)
        assert count == 0

        # Send notification
        await notification_adapter.send(sample_notification)

        # Should be 1
        count = await notification_adapter.get_unread_count(sample_notification.user_id)
        assert count == 1

        # Mark as read
        await notification_adapter.mark_as_read(sample_notification.id_)

        # Should be 0 again
        count = await notification_adapter.get_unread_count(sample_notification.user_id)
        assert count == 0

    async def test_delete_notification(self, notification_adapter, sample_notification):
        """Test deleting a notification."""
        await notification_adapter.send(sample_notification)

        # Delete
        await notification_adapter.delete_notification(sample_notification.id_)

        # Should not be retrievable
        retrieved = await notification_adapter.get_notification(sample_notification.id_)
        assert retrieved is None

    async def test_broadcast_to_channel(self, notification_adapter):
        """Test broadcasting to multiple users."""
        user_ids = [UserId(1), UserId(2), UserId(3)]

        await notification_adapter.broadcast_to_channel(
            channel=NotificationChannel.IN_APP,
            user_ids=user_ids,
            notification_type=NotificationType.SYSTEM,
            title="System Announcement",
            body="Maintenance scheduled",
            data={"maintenance_time": "2025-12-20T00:00:00Z"},
        )

        # Each user should have a notification
        for user_id in user_ids:
            notifications = await notification_adapter.get_user_notifications(
                user_id=user_id, limit=10
            )
            assert len(notifications) == 1
            assert notifications[0].payload.title == "System Announcement"

    async def test_send_batch(self, notification_adapter):
        """Test sending batch notifications."""
        notifications = [
            ChatNotification(
                id_=ChatNotificationId(str(uuid4())),
                user_id=UserId(i),
                notification_type=NotificationType.ALERT,
                payload=NotificationPayload(
                    title=f"Alert {i}",
                    body=f"Test alert {i}",
                    data={},
                ),
                channels={NotificationChannel.IN_APP},
            )
            for i in range(1, 4)
        ]

        await notification_adapter.send_batch(notifications)

        # Each user should have their notification
        for i in range(1, 4):
            user_notifications = await notification_adapter.get_user_notifications(
                user_id=UserId(i), limit=10
            )
            assert len(user_notifications) == 1
