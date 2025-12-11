"""
Message Status Enum.

Represents the status of a cross-chain message.
"""

from enum import Enum


class MessageStatus(Enum):
    """
    Cross-chain message status.

    Tracks the delivery state of LayerZero messages.
    """

    INFLIGHT = "INFLIGHT"  # Message in transit
    DELIVERED = "DELIVERED"  # Successfully delivered
    FAILED = "FAILED"  # Delivery failed
    BLOCKED = "BLOCKED"  # Blocked by security layer
