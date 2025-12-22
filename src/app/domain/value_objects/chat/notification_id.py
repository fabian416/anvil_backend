"""
Chat Notification ID value object.
"""

from app.domain.value_objects.base import ValueObject


class ChatNotificationId(ValueObject[str]):
    """
    Chat notification ID value object.

    Uses string UUID for Redis-compatible identifiers.
    """
