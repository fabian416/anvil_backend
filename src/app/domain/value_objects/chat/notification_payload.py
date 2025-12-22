"""
Notification payload value object.

Contains the structured data for a notification.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True, slots=True)
class NotificationPayload:
    """
    Notification payload value object.

    Attributes:
        title: Notification title
        body: Notification body text
        data: Additional structured data
        action_url: Optional URL for action button
    """

    title: str
    body: str
    data: Dict[str, Any]
    action_url: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate payload data."""
        if not self.title or not self.title.strip():
            raise ValueError("Notification title cannot be empty")
        if not self.body or not self.body.strip():
            raise ValueError("Notification body cannot be empty")
