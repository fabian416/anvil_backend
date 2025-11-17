"""
Coordinates value object.
"""

from dataclasses import dataclass
from typing import Final

from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, slots=True)
class Coordinates(ValueObject[tuple[float, float]]):
    """
    Coordinates value object representing latitude and longitude.
    
    Latitude must be between -90 and 90.
    Longitude must be between -180 and 180.
    """
    latitude: float
    longitude: float
    
    def __post_init__(self) -> None:
        """Validate coordinates."""
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")
    
    @property
    def value(self) -> tuple[float, float]:
        """Return coordinates as tuple."""
        return (self.latitude, self.longitude)
