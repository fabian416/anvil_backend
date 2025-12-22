# Notification Adapter Usage Guide

## Overview

The NotificationAdapter provides multi-channel notification delivery with comprehensive tracking and queuing capabilities. It supports:

- **Email notifications** via Celery async tasks
- **WebSocket real-time push** via Redis pubsub
- **In-app notifications** stored in Redis
- **Delivery tracking** (queued, sent, delivered, read)
- **Notification history** with configurable TTL
- **Batch operations** for bulk notifications

## Architecture

### Domain Layer

**Entity**: `ChatNotification` (`src/app/domain/entities/chat/notification.py`)
- Represents a notification with multi-channel delivery
- Tracks delivery status per channel
- Provides methods to mark sent/delivered/read/failed

**Port**: `NotificationAdapter` (`src/app/domain/ports/notification_adapter.py`)
- Defines the interface for notification operations
- Pure abstraction with no implementation details

**Enums**:
- `NotificationType`: conversation_update, daily_summary, alert, template_execution, system
- `NotificationChannel`: email, websocket, in_app
- `DeliveryStatus`: queued, sent, delivered, read, failed

### Infrastructure Layer

**Adapter**: `RedisNotificationAdapter` (`src/app/infrastructure/adapters/chat/notification_adapter.py`)
- Redis-based implementation of NotificationAdapter
- Stores notifications in sorted sets per user
- Tracks unread notifications in separate sets
- Publishes WebSocket messages to Redis pubsub
- Queues email tasks to Celery (stub implementation)

## Basic Usage

### 1. Send a Conversation Update Notification

```python
from uuid import uuid4
from app.domain.entities.chat.notification import ChatNotification
from app.domain.value_objects.chat.notification_id import ChatNotificationId
from app.domain.value_objects.chat.notification_payload import NotificationPayload
from app.domain.value_objects.user_id import UserId
from app.domain.enums.notification_type import NotificationType
from app.domain.enums.notification_channel import NotificationChannel
from app.domain.ports.notification_adapter import NotificationAdapter

async def send_conversation_update(
    notification_adapter: NotificationAdapter,
    user_id: UserId,
    conversation_id: str,
    agent_response: str,
):
    """Send notification when agent responds in conversation."""
    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=user_id,
        notification_type=NotificationType.CONVERSATION_UPDATE,
        payload=NotificationPayload(
            title="New Message",
            body=f"Your AI agent has responded: {agent_response[:100]}...",
            data={
                "conversation_id": conversation_id,
                "agent_response_preview": agent_response[:200],
            },
            action_url=f"/chat/{conversation_id}",
        ),
        channels={
            NotificationChannel.WEBSOCKET,  # Real-time push
            NotificationChannel.IN_APP,     # Store for later
        },
    )

    await notification_adapter.send(notification)
```

### 2. Send Daily Summary Notification

```python
async def send_daily_summary(
    notification_adapter: NotificationAdapter,
    user_id: UserId,
    stats: dict,
):
    """Send daily analytics summary."""
    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=user_id,
        notification_type=NotificationType.DAILY_SUMMARY,
        payload=NotificationPayload(
            title="Your Daily Summary",
            body=f"You had {stats['conversations']} conversations today.",
            data=stats,
            action_url="/analytics",
        ),
        channels={
            NotificationChannel.EMAIL,  # Email digest
            NotificationChannel.IN_APP, # Also in-app
        },
    )

    await notification_adapter.send(notification)
```

### 3. Send Alert Notification

```python
async def send_budget_alert(
    notification_adapter: NotificationAdapter,
    user_id: UserId,
    budget_threshold: float,
    current_spend: float,
):
    """Send alert when budget threshold is reached."""
    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=user_id,
        notification_type=NotificationType.ALERT,
        payload=NotificationPayload(
            title="Budget Alert",
            body=f"You've reached {(current_spend/budget_threshold)*100:.0f}% of your budget.",
            data={
                "budget_threshold": budget_threshold,
                "current_spend": current_spend,
                "alert_level": "warning",
            },
            action_url="/settings/billing",
        ),
        channels={
            NotificationChannel.EMAIL,
            NotificationChannel.WEBSOCKET,
            NotificationChannel.IN_APP,
        },
    )

    await notification_adapter.send(notification)
```

### 4. Send Template Execution Update

```python
async def send_template_step_completed(
    notification_adapter: NotificationAdapter,
    user_id: UserId,
    template_id: str,
    step_name: str,
    step_result: str,
):
    """Notify user when template execution step completes."""
    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=user_id,
        notification_type=NotificationType.TEMPLATE_EXECUTION,
        payload=NotificationPayload(
            title="Template Step Completed",
            body=f"Step '{step_name}' completed successfully.",
            data={
                "template_id": template_id,
                "step_name": step_name,
                "step_result": step_result,
            },
            action_url=f"/templates/{template_id}",
        ),
        channels={
            NotificationChannel.WEBSOCKET,
            NotificationChannel.IN_APP,
        },
    )

    await notification_adapter.send(notification)
```

## Advanced Usage

### 5. Retrieve User Notifications

```python
async def get_notifications(
    notification_adapter: NotificationAdapter,
    user_id: UserId,
):
    """Get user's recent notifications."""
    # Get all notifications
    all_notifications = await notification_adapter.get_user_notifications(
        user_id=user_id,
        limit=50,
    )

    # Get only unread notifications
    unread_notifications = await notification_adapter.get_user_notifications(
        user_id=user_id,
        unread_only=True,
        limit=50,
    )

    # Get only alerts
    alerts = await notification_adapter.get_user_notifications(
        user_id=user_id,
        notification_type=NotificationType.ALERT,
        limit=20,
    )

    return {
        "all": all_notifications,
        "unread": unread_notifications,
        "alerts": alerts,
    }
```

### 6. Mark Notifications as Read

```python
async def mark_notification_read(
    notification_adapter: NotificationAdapter,
    notification_id: ChatNotificationId,
):
    """Mark a single notification as read."""
    await notification_adapter.mark_as_read(notification_id)


async def mark_all_read(
    notification_adapter: NotificationAdapter,
    user_id: UserId,
):
    """Mark all notifications as read for user."""
    count = await notification_adapter.mark_all_as_read(user_id)
    return f"Marked {count} notifications as read"
```

### 7. Get Unread Count

```python
async def get_unread_badge(
    notification_adapter: NotificationAdapter,
    user_id: UserId,
) -> int:
    """Get unread count for notification badge."""
    return await notification_adapter.get_unread_count(user_id)
```

### 8. Broadcast to Multiple Users

```python
async def send_system_announcement(
    notification_adapter: NotificationAdapter,
    user_ids: List[UserId],
    announcement: str,
):
    """Broadcast system announcement to all users."""
    await notification_adapter.broadcast_to_channel(
        channel=NotificationChannel.IN_APP,
        user_ids=user_ids,
        notification_type=NotificationType.SYSTEM,
        title="System Announcement",
        body=announcement,
        data={"announcement_type": "general"},
    )
```

### 9. Batch Send Notifications

```python
async def send_batch_alerts(
    notification_adapter: NotificationAdapter,
    user_alerts: List[tuple[UserId, dict]],
):
    """Send alerts to multiple users efficiently."""
    notifications = []

    for user_id, alert_data in user_alerts:
        notification = ChatNotification(
            id_=ChatNotificationId(str(uuid4())),
            user_id=user_id,
            notification_type=NotificationType.ALERT,
            payload=NotificationPayload(
                title=alert_data["title"],
                body=alert_data["body"],
                data=alert_data,
            ),
            channels={NotificationChannel.EMAIL, NotificationChannel.IN_APP},
        )
        notifications.append(notification)

    await notification_adapter.send_batch(notifications)
```

## Integration with Application Layer

### Example Interactor

```python
# src/app/application/commands/chat/notify_conversation_update.py

from dataclasses import dataclass
from uuid import uuid4

from app.domain.ports.notification_adapter import NotificationAdapter
from app.domain.entities.chat.notification import ChatNotification
from app.domain.value_objects.chat.notification_id import ChatNotificationId
from app.domain.value_objects.chat.notification_payload import NotificationPayload
from app.domain.value_objects.user_id import UserId
from app.domain.enums.notification_type import NotificationType
from app.domain.enums.notification_channel import NotificationChannel


@dataclass(frozen=True, slots=True)
class NotifyConversationUpdateCommand:
    """Command to notify user of conversation update."""
    user_id: int
    conversation_id: str
    message_content: str
    agent_name: str


class NotifyConversationUpdateInteractor:
    """
    Interactor for sending conversation update notifications.

    Orchestrates notification creation and delivery via multiple channels.
    """

    def __init__(self, notification_adapter: NotificationAdapter) -> None:
        self._notification_adapter = notification_adapter

    async def execute(self, command: NotifyConversationUpdateCommand) -> None:
        """
        Execute conversation update notification.

        Args:
            command: Notification command with conversation details
        """
        notification = ChatNotification(
            id_=ChatNotificationId(str(uuid4())),
            user_id=UserId(command.user_id),
            notification_type=NotificationType.CONVERSATION_UPDATE,
            payload=NotificationPayload(
                title=f"New message from {command.agent_name}",
                body=command.message_content[:200],
                data={
                    "conversation_id": command.conversation_id,
                    "agent_name": command.agent_name,
                    "message_preview": command.message_content[:200],
                },
                action_url=f"/chat/{command.conversation_id}",
            ),
            channels={
                NotificationChannel.WEBSOCKET,
                NotificationChannel.IN_APP,
            },
        )

        await self._notification_adapter.send(notification)
```

## WebSocket Integration

The notification adapter publishes to Redis pubsub channels. WebSocket connection managers should subscribe to these channels:

```python
# Subscribe to user's notification channel
channel = f"websocket:user:{user_id}:notifications"

# Listen for notifications
pubsub = redis.pubsub()
await pubsub.subscribe(channel)

async for message in pubsub.listen():
    if message["type"] == "message":
        notification_data = json.loads(message["data"])
        # Send to WebSocket client
        await websocket.send_json(notification_data)
```

## Email Integration (TODO)

The current implementation includes a stub for email delivery. To implement:

1. Create Celery task in `src/app/infrastructure/celery/tasks/notification_tasks.py`:

```python
from app.infrastructure.celery.app import celery_app

@celery_app.task(name="send_notification_email")
def send_notification_email(
    user_id: int,
    title: str,
    body: str,
    data: dict,
):
    """Send notification email."""
    # Implement email sending logic
    # Use email templates based on notification type
    # Track delivery status
    pass
```

2. Update `_send_email` method in `RedisNotificationAdapter` to queue the task:

```python
async def _send_email(self, notification: ChatNotification) -> None:
    from app.infrastructure.celery.tasks.notification_tasks import send_notification_email

    send_notification_email.delay(
        user_id=notification.user_id.value,
        title=notification.payload.title,
        body=notification.payload.body,
        data=notification.payload.data,
    )
```

## Configuration

Notification adapter is configured via Dishka in `src/app/setup/ioc/notification.py`:

```python
@provide
async def notification_adapter(self, redis: Redis) -> NotificationAdapter:
    return RedisNotificationAdapter(
        redis_client=redis,
        key_prefix="notifications:",      # Redis key prefix
        queue_key="notifications:queue",  # Queue key
        history_ttl_days=30,              # History retention
    )
```

## Testing

See `tests/integration/notifications/test_notification_adapter.py` for integration tests.

## Best Practices

1. **Choose appropriate channels**: Use WebSocket for real-time, email for important updates
2. **Keep payloads small**: Store large data elsewhere, reference by ID
3. **Set action URLs**: Help users navigate to relevant content
4. **Use batch operations**: For bulk notifications, use `send_batch`
5. **Handle failures gracefully**: Check delivery status per channel
6. **Respect user preferences**: Check notification settings before sending
7. **Monitor unread counts**: Clean up old notifications to prevent overflow
8. **Use appropriate TTL**: Balance storage with user needs (default 30 days)
