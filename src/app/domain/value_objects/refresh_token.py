"""
Refresh token value object.
"""

from app.domain.value_objects.base import ValueObject


class RefreshToken(ValueObject[str]):
    """Refresh token value object."""
