"""
Country entity for the hexagonal architecture.
Based on the BaseAPI Country model with domain-driven design principles.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple

from app.domain.entities.base import Entity
from app.domain.value_objects.country_id import CountryId
from app.domain.value_objects.country_name import CountryName
from app.domain.value_objects.iso_code import IsoCode
from app.domain.value_objects.coordinates import Coordinates


@dataclass(eq=False, kw_only=True)
class Country(Entity[CountryId]):
    """
    Country entity representing a country in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    name: CountryName
    iso3: IsoCode
    iso2: Optional[IsoCode]
    numeric_code: Optional[str]
    phonecode: Optional[str]
    capital: Optional[str]
    currency: Optional[str]
    currency_name: Optional[str]
    currency_symbol: Optional[str]
    tld: Optional[str]
    native: Optional[str]
    nationality: Optional[str]
    timezones: Optional[List[str]]
    coordinates: Optional[Coordinates]
    emoji: Optional[str]
    emojiU: Optional[str]
    region: Optional[str]
    subregion: Optional[str]
