"""
Features value object.
"""

from typing import Dict, Any
from app.domain.value_objects.base import ValueObject


class Features(ValueObject[Dict[str, Any]]):
    """Features value object."""
