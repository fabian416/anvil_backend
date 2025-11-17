"""
City entity for the hexagonal architecture.
Based on the BaseAPI City model with domain-driven design principles.
"""

from dataclasses import dataclass
from typing import Optional

from app.domain.entities.base import Entity
from app.domain.value_objects.city_id import CityId
from app.domain.value_objects.city_name import CityName
from app.domain.value_objects.state_id import StateId
from app.domain.value_objects.state_code import StateCode
from app.domain.value_objects.state_name import StateName
from app.domain.value_objects.country_id import CountryId
from app.domain.value_objects.country_code import CountryCode
from app.domain.value_objects.country_name import CountryName
from app.domain.value_objects.coordinates import Coordinates
from app.domain.value_objects.wiki_data_id import WikiDataId


@dataclass(eq=False, kw_only=True)
class City(Entity[CityId]):
    """
    City entity representing a city in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    name: CityName
    state_id: StateId
    state_code: Optional[StateCode]
    state_name: StateName
    country_id: CountryId
    country_code: CountryCode
    country_name: CountryName
    coordinates: Optional[Coordinates]
    wiki_data_id: Optional[WikiDataId]
