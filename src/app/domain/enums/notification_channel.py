"""
Notification channel enumeration.

Defines the different channels through which notifications can be delivered.
"""

from enum import Enum


class NotificationChannel(str, Enum):
    """
    Notification channel enumeration.

    Channels:
    - EMAIL: Email notifications
    - WEBSOCKET: Real-time WebSocket push
    - IN_APP: In-application notifications
    """

    EMAIL = "email"
    WEBSOCKET = "websocket"
    IN_APP = "in_app"
