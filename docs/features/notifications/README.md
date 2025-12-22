# Notification System

## Overview

Multi-channel notification delivery system with comprehensive tracking and queuing capabilities, built using hexagonal architecture principles.

## Features

- **Multi-Channel Delivery**: Email, WebSocket real-time push, in-app notifications
- **Delivery Tracking**: Track sent, delivered, read status per channel
- **Notification History**: Redis-based storage with configurable TTL (default: 30 days)
- **Async Queuing**: Celery integration for email delivery
- **WebSocket Integration**: Redis pubsub for real-time push
- **Batch Operations**: Efficient bulk notification sending
- **Unread Tracking**: Per-user unread notification counts

## Architecture

### Hexagonal Architecture Layers

```
Domain Layer (Business Logic)
├── Entities
│   └── ChatNotification (src/app/domain/entities/chat/notification.py)
├── Value Objects
│   ├── ChatNotificationId
│   └── NotificationPayload
├── Enums
│   ├── NotificationType (conversation_update, daily_summary, alert, template_execution, system)
│   ├── NotificationChannel (email, websocket, in_app)
│   └── DeliveryStatus (queued, sent, delivered, read, failed)
└── Ports
    └── NotificationAdapter (src/app/domain/ports/notification_adapter.py)

Infrastructure Layer (Implementation)
└── Adapters
    └── RedisNotificationAdapter (src/app/infrastructure/adapters/chat/notification_adapter.py)

Application Layer (Use Cases)
└── Commands
    └── NotifyConversationUpdateInteractor (src/app/application/commands/chat/notify_conversation_update.py)

Presentation Layer (API)
└── (Future: REST endpoints for notification management)
```

## File Structure

```
src/app/
├── domain/
│   ├── entities/chat/
│   │   └── notification.py                    # ChatNotification entity
│   ├── value_objects/chat/
│   │   ├── notification_id.py                 # ChatNotificationId VO
│   │   └── notification_payload.py            # NotificationPayload VO
│   ├── enums/
│   │   ├── notification_type.py               # NotificationType enum
│   │   ├── notification_channel.py            # NotificationChannel enum
│   │   └── delivery_status.py                 # DeliveryStatus enum
│   └── ports/
│       └── notification_adapter.py            # NotificationAdapter port
├── infrastructure/
│   └── adapters/chat/
│       └── notification_adapter.py            # RedisNotificationAdapter implementation
├── application/
│   └── commands/chat/
│       └── notify_conversation_update.py      # Example interactor
└── setup/ioc/
    ├── notification.py                        # Dishka provider
    └── provider_registry.py                   # Provider registration

tests/
└── integration/notifications/
    └── test_notification_adapter.py           # Integration tests

docs/features/notifications/
├── README.md                                  # This file
└── NOTIFICATION_ADAPTER_USAGE.md              # Detailed usage guide
```

## Quick Start

### 1. Send a Notification

```python
from app.domain.ports.notification_adapter import NotificationAdapter

async def send_notification(notification_adapter: NotificationAdapter):
    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=UserId(123),
        notification_type=NotificationType.CONVERSATION_UPDATE,
        payload=NotificationPayload(
            title="New Message",
            body="You have a new message from AI Agent",
            data={"conversation_id": "conv-123"},
            action_url="/chat/conv-123",
        ),
        channels={
            NotificationChannel.WEBSOCKET,
            NotificationChannel.IN_APP,
        },
    )

    await notification_adapter.send(notification)
```

### 2. Retrieve Notifications

```python
# Get user's notifications
notifications = await notification_adapter.get_user_notifications(
    user_id=UserId(123),
    unread_only=True,
    limit=50,
)

# Get unread count
count = await notification_adapter.get_unread_count(UserId(123))
```

### 3. Mark as Read

```python
# Mark single notification as read
await notification_adapter.mark_as_read(notification_id)

# Mark all as read
count = await notification_adapter.mark_all_as_read(user_id)
```

## Notification Types

### 1. Conversation Update
- **Use Case**: New messages, agent responses
- **Channels**: WebSocket (real-time), In-App (history)
- **Example**: "Your AI agent has responded to your query"

### 2. Daily Summary
- **Use Case**: Analytics digest, daily reports
- **Channels**: Email (digest), In-App (reference)
- **Example**: "Your daily activity summary: 5 conversations, 12 messages"

### 3. Alert
- **Use Case**: Performance alerts, budget thresholds
- **Channels**: Email (important), WebSocket (urgent), In-App (log)
- **Example**: "Budget alert: 80% of monthly limit reached"

### 4. Template Execution
- **Use Case**: Template step completion updates
- **Channels**: WebSocket (progress), In-App (history)
- **Example**: "Step 'Data Analysis' completed successfully"

### 5. System
- **Use Case**: System announcements, maintenance
- **Channels**: In-App (all users)
- **Example**: "Scheduled maintenance on Dec 20, 2025"

## Redis Data Structure

### Notification Storage
```
Key: notifications:notification:{notification_id}
Type: String (JSON)
TTL: 30 days
Value: Serialized ChatNotification
```

### User Notifications Index
```
Key: notifications:user:{user_id}:notifications
Type: Sorted Set
Score: Timestamp
Members: Notification IDs
TTL: 30 days
```

### Unread Tracking
```
Key: notifications:user:{user_id}:unread
Type: Set
Members: Unread notification IDs
TTL: 30 days
```

### WebSocket Channel
```
Channel: websocket:user:{user_id}:notifications
Type: Pubsub
Format: JSON message
```

## Configuration

Configured via Dishka in `src/app/setup/ioc/notification.py`:

```python
@provide
async def notification_adapter(self, redis: Redis) -> NotificationAdapter:
    return RedisNotificationAdapter(
        redis_client=redis,
        key_prefix="notifications:",      # Redis key prefix
        queue_key="notifications:queue",  # Queue key
        history_ttl_days=30,              # History retention (days)
    )
```

## Integration Points

### WebSocket Connection Manager
Subscribe to user notification channels:
```python
channel = f"websocket:user:{user_id}:notifications"
await redis.pubsub().subscribe(channel)
```

### Email Delivery (TODO)
Implement Celery task:
```python
@celery_app.task(name="send_notification_email")
def send_notification_email(user_id, title, body, data):
    # Send email using template
    pass
```

### REST API (Future)
Endpoints to add:
- `GET /api/v1/notifications` - List user notifications
- `GET /api/v1/notifications/unread/count` - Unread count
- `POST /api/v1/notifications/{id}/read` - Mark as read
- `POST /api/v1/notifications/read-all` - Mark all as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

## Testing

Run integration tests:
```bash
pytest tests/integration/notifications/test_notification_adapter.py -v
```

## Future Enhancements

1. **Email Templates**: HTML email templates per notification type
2. **User Preferences**: Per-channel notification preferences
3. **Notification Grouping**: Group similar notifications
4. **Rich Notifications**: Support for images, actions
5. **Push Notifications**: Mobile push via FCM/APNs
6. **Notification Settings API**: User-configurable notification rules
7. **Delivery Analytics**: Track open/click rates
8. **Retry Logic**: Automatic retry for failed deliveries

## Documentation

- [Usage Guide](./NOTIFICATION_ADAPTER_USAGE.md) - Comprehensive usage examples
- [Architecture Guide](../../CLAUDE.md) - Hexagonal architecture overview

## Dependencies

- **Redis**: Notification storage and pubsub
- **Celery**: Async email delivery (planned)
- **Dishka**: Dependency injection
- **FastAPI**: REST API (future)

## Support

For questions or issues, please refer to the usage guide or create a GitHub issue.
