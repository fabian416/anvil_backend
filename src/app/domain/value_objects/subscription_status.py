"""
Subscription status value object.
"""

from app.domain.value_objects.base import ValueObject


class SubscriptionStatus(ValueObject[bool]):
    """Subscription status value object."""
