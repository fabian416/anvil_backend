"""
IP address value object.
"""

from app.domain.value_objects.base import ValueObject


class IpAddress(ValueObject[str]):
    """IP address value object."""
