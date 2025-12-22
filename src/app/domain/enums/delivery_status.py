"""
Delivery status enumeration.

Defines the status of notification delivery tracking.
"""

from enum import Enum


class DeliveryStatus(str, Enum):
    """
    Delivery status enumeration.

    Statuses:
    - QUEUED: Notification queued for delivery
    - SENT: Notification sent to channel
    - DELIVERED: Notification delivered successfully
    - READ: Notification read by user
    - FAILED: Delivery failed
    """

    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
