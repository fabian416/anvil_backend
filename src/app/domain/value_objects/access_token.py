"""
Access token value object.
"""

from app.domain.value_objects.base import ValueObject


class AccessToken(ValueObject[str]):
    """Access token value object."""
