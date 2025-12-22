"""
Example: Sending notifications for conversation updates.

This example demonstrates how to integrate the NotificationAdapter
into a real application scenario - notifying users when their AI
agent responds to messages.
"""

from uuid import uuid4
from typing import Optional

from dishka import FromDishka

from app.domain.ports.notification_adapter import NotificationAdapter
from app.domain.entities.chat.notification import ChatNotification
from app.domain.value_objects.chat.notification_id import ChatNotificationId
from app.domain.value_objects.chat.notification_payload import NotificationPayload
from app.domain.value_objects.user_id import UserId
from app.domain.enums.notification_type import NotificationType
from app.domain.enums.notification_channel import NotificationChannel


async def notify_user_of_agent_response(
    notification_adapter: NotificationAdapter,
    user_id: int,
    conversation_id: str,
    agent_name: str,
    agent_response: str,
    is_important: bool = False,
) -> ChatNotificationId:
    """
    Send notification when AI agent responds to user message.

    Args:
        notification_adapter: Injected notification adapter
        user_id: User who should receive notification
        conversation_id: Conversation identifier
        agent_name: Name of responding agent
        agent_response: Agent's response text
        is_important: If True, also send email

    Returns:
        Notification ID
    """
    # Determine channels based on importance
    channels = {
        NotificationChannel.WEBSOCKET,  # Always real-time
        NotificationChannel.IN_APP,     # Always in history
    }

    if is_important:
        channels.add(NotificationChannel.EMAIL)

    # Create notification
    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=UserId(user_id),
        notification_type=NotificationType.CONVERSATION_UPDATE,
        payload=NotificationPayload(
            title=f"New message from {agent_name}",
            body=_truncate(agent_response, 200),
            data={
                "conversation_id": conversation_id,
                "agent_name": agent_name,
                "full_response_length": len(agent_response),
                "is_important": is_important,
            },
            action_url=f"/chat/{conversation_id}",
        ),
        channels=channels,
    )

    # Send notification
    await notification_adapter.send(notification)

    return notification.id_


async def send_daily_conversation_summary(
    notification_adapter: NotificationAdapter,
    user_id: int,
    stats: dict,
) -> ChatNotificationId:
    """
    Send daily summary of conversation activity.

    Args:
        notification_adapter: Injected notification adapter
        user_id: User who should receive summary
        stats: Dictionary with conversation statistics

    Returns:
        Notification ID

    Example stats:
        {
            "conversations_today": 5,
            "messages_sent": 12,
            "messages_received": 15,
            "top_agent": "Research Assistant",
            "total_tokens": 5000,
        }
    """
    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=UserId(user_id),
        notification_type=NotificationType.DAILY_SUMMARY,
        payload=NotificationPayload(
            title="Your Daily Conversation Summary",
            body=(
                f"You had {stats['conversations_today']} conversations "
                f"with {stats['messages_sent']} messages sent."
            ),
            data=stats,
            action_url="/analytics",
        ),
        channels={
            NotificationChannel.EMAIL,   # Email digest
            NotificationChannel.IN_APP,  # Also store in app
        },
    )

    await notification_adapter.send(notification)

    return notification.id_


async def send_budget_alert(
    notification_adapter: NotificationAdapter,
    user_id: int,
    budget_limit: float,
    current_spend: float,
    threshold_percentage: int = 80,
) -> ChatNotificationId:
    """
    Send alert when user approaches budget threshold.

    Args:
        notification_adapter: Injected notification adapter
        user_id: User to alert
        budget_limit: User's budget limit
        current_spend: Current spending
        threshold_percentage: Alert threshold (default 80%)

    Returns:
        Notification ID
    """
    percentage_used = (current_spend / budget_limit) * 100

    # Determine urgency
    if percentage_used >= 100:
        alert_level = "critical"
        title = "Budget Limit Reached!"
    elif percentage_used >= 90:
        alert_level = "high"
        title = "Budget Alert: 90% Used"
    else:
        alert_level = "warning"
        title = f"Budget Alert: {int(percentage_used)}% Used"

    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=UserId(user_id),
        notification_type=NotificationType.ALERT,
        payload=NotificationPayload(
            title=title,
            body=(
                f"You've used ${current_spend:.2f} of your ${budget_limit:.2f} "
                f"monthly budget ({int(percentage_used)}%)."
            ),
            data={
                "budget_limit": budget_limit,
                "current_spend": current_spend,
                "percentage_used": percentage_used,
                "alert_level": alert_level,
            },
            action_url="/settings/billing",
        ),
        channels={
            NotificationChannel.EMAIL,      # Email for important alerts
            NotificationChannel.WEBSOCKET,  # Real-time notification
            NotificationChannel.IN_APP,     # Store for reference
        },
    )

    await notification_adapter.send(notification)

    return notification.id_


async def send_template_execution_update(
    notification_adapter: NotificationAdapter,
    user_id: int,
    template_id: str,
    template_name: str,
    step_name: str,
    step_status: str,
    step_result: Optional[str] = None,
) -> ChatNotificationId:
    """
    Send notification when template execution step completes.

    Args:
        notification_adapter: Injected notification adapter
        user_id: Template owner
        template_id: Template identifier
        template_name: Human-readable template name
        step_name: Name of completed step
        step_status: Status (success, failed, etc.)
        step_result: Optional result summary

    Returns:
        Notification ID
    """
    if step_status == "success":
        title = f"Template Step Completed: {step_name}"
        body = f"Step '{step_name}' in template '{template_name}' completed successfully."
    else:
        title = f"Template Step Failed: {step_name}"
        body = f"Step '{step_name}' in template '{template_name}' failed."

    if step_result:
        body += f" Result: {_truncate(step_result, 100)}"

    notification = ChatNotification(
        id_=ChatNotificationId(str(uuid4())),
        user_id=UserId(user_id),
        notification_type=NotificationType.TEMPLATE_EXECUTION,
        payload=NotificationPayload(
            title=title,
            body=body,
            data={
                "template_id": template_id,
                "template_name": template_name,
                "step_name": step_name,
                "step_status": step_status,
                "step_result": step_result,
            },
            action_url=f"/templates/{template_id}",
        ),
        channels={
            NotificationChannel.WEBSOCKET,  # Real-time progress
            NotificationChannel.IN_APP,     # Store for history
        },
    )

    await notification_adapter.send(notification)

    return notification.id_


async def broadcast_system_announcement(
    notification_adapter: NotificationAdapter,
    user_ids: list[int],
    announcement: str,
    announcement_type: str = "general",
) -> None:
    """
    Broadcast system announcement to multiple users.

    Args:
        notification_adapter: Injected notification adapter
        user_ids: List of user IDs to notify
        announcement: Announcement text
        announcement_type: Type of announcement (maintenance, feature, etc.)
    """
    await notification_adapter.broadcast_to_channel(
        channel=NotificationChannel.IN_APP,
        user_ids=[UserId(uid) for uid in user_ids],
        notification_type=NotificationType.SYSTEM,
        title="System Announcement",
        body=announcement,
        data={
            "announcement_type": announcement_type,
            "announced_at": "2025-12-16T00:00:00Z",
        },
    )


async def get_user_notification_summary(
    notification_adapter: NotificationAdapter,
    user_id: int,
) -> dict:
    """
    Get summary of user's notifications.

    Args:
        notification_adapter: Injected notification adapter
        user_id: User identifier

    Returns:
        Dictionary with notification summary
    """
    # Get unread count
    unread_count = await notification_adapter.get_unread_count(UserId(user_id))

    # Get recent unread notifications
    unread_notifications = await notification_adapter.get_user_notifications(
        user_id=UserId(user_id),
        unread_only=True,
        limit=10,
    )

    # Get all recent notifications
    all_notifications = await notification_adapter.get_user_notifications(
        user_id=UserId(user_id),
        limit=50,
    )

    # Get alerts
    alerts = await notification_adapter.get_user_notifications(
        user_id=UserId(user_id),
        notification_type=NotificationType.ALERT,
        limit=20,
    )

    return {
        "unread_count": unread_count,
        "unread_notifications": [
            {
                "id": n.id_.value,
                "type": n.notification_type.value,
                "title": n.payload.title,
                "created_at": n.created_at.isoformat(),
            }
            for n in unread_notifications
        ],
        "total_recent": len(all_notifications),
        "alert_count": len(alerts),
    }


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


# =============================================================================
# Example Integration with FastAPI Endpoint
# =============================================================================

"""
# In your FastAPI router:

from fastapi import APIRouter, Depends
from dishka.integrations.fastapi import FromDishka

router = APIRouter()

@router.post("/chat/{conversation_id}/notify")
async def notify_conversation_update(
    conversation_id: str,
    user_id: int,
    agent_name: str,
    agent_response: str,
    notification_adapter: FromDishka[NotificationAdapter],
):
    '''Notify user of new agent response.'''
    notification_id = await notify_user_of_agent_response(
        notification_adapter=notification_adapter,
        user_id=user_id,
        conversation_id=conversation_id,
        agent_name=agent_name,
        agent_response=agent_response,
        is_important=False,
    )

    return {
        "notification_id": notification_id.value,
        "status": "sent",
    }


@router.get("/notifications/summary")
async def get_notifications_summary(
    user_id: int,
    notification_adapter: FromDishka[NotificationAdapter],
):
    '''Get user's notification summary.'''
    summary = await get_user_notification_summary(
        notification_adapter=notification_adapter,
        user_id=user_id,
    )

    return summary


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    notification_adapter: FromDishka[NotificationAdapter],
):
    '''Mark notification as read.'''
    await notification_adapter.mark_as_read(
        ChatNotificationId(notification_id)
    )

    return {"status": "success"}
"""
