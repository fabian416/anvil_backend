"""
Notify conversation update command and interactor.

Sends notifications when conversation updates occur (new messages, agent responses).
"""

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
    """
    Command to notify user of conversation update.

    Attributes:
        user_id: Target user ID
        conversation_id: Conversation identifier
        message_content: New message content
        agent_name: Name of the responding agent
        include_email: Whether to send email notification
    """

    user_id: int
    conversation_id: str
    message_content: str
    agent_name: str
    include_email: bool = False


class NotifyConversationUpdateInteractor:
    """
    Interactor for sending conversation update notifications.

    Orchestrates notification creation and delivery via multiple channels
    following hexagonal architecture principles.

    Dependencies:
        - NotificationAdapter: Port for multi-channel notification delivery
    """

    __slots__ = ("_notification_adapter",)

    def __init__(self, notification_adapter: NotificationAdapter) -> None:
        """
        Initialize interactor.

        Args:
            notification_adapter: Notification delivery adapter
        """
        self._notification_adapter = notification_adapter

    async def execute(self, command: NotifyConversationUpdateCommand) -> ChatNotificationId:
        """
        Execute conversation update notification.

        Creates a notification with appropriate channels and sends it.

        Args:
            command: Notification command with conversation details

        Returns:
            Created notification ID
        """
        # Determine delivery channels based on command
        channels = {
            NotificationChannel.WEBSOCKET,  # Always send real-time
            NotificationChannel.IN_APP,     # Always store in-app
        }

        if command.include_email:
            channels.add(NotificationChannel.EMAIL)

        # Create notification
        notification_id = ChatNotificationId(str(uuid4()))
        notification = ChatNotification(
            id_=notification_id,
            user_id=UserId(command.user_id),
            notification_type=NotificationType.CONVERSATION_UPDATE,
            payload=NotificationPayload(
                title=f"New message from {command.agent_name}",
                body=self._truncate_message(command.message_content, max_length=200),
                data={
                    "conversation_id": command.conversation_id,
                    "agent_name": command.agent_name,
                    "message_preview": self._truncate_message(
                        command.message_content, max_length=100
                    ),
                },
                action_url=f"/chat/{command.conversation_id}",
            ),
            channels=channels,
        )

        # Send notification
        await self._notification_adapter.send(notification)

        return notification_id

    @staticmethod
    def _truncate_message(message: str, max_length: int) -> str:
        """
        Truncate message to max length with ellipsis.

        Args:
            message: Message to truncate
            max_length: Maximum length

        Returns:
            Truncated message
        """
        if len(message) <= max_length:
            return message
        return message[: max_length - 3] + "..."
