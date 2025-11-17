"""
Data JSON value object.
"""

from typing import Dict, Any
from app.domain.value_objects.base import ValueObject


class DataJson(ValueObject[Dict[str, Any]]):
    """Data JSON value object."""
