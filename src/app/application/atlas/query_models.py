from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CountryQueryModel:
    id: int
    country_id: int
    name: str
    iso2: Optional[str]
    iso3: str
    region: Optional[str]
    subregion: Optional[str]
    currency: Optional[str]


@dataclass(frozen=True)
class CityQueryModel:
    id: int
    city_id: int
    name: str
    country_id: int
    country_code: Optional[str]
    country_name: Optional[str]
    state_id: Optional[str]
    state_code: Optional[str]
    state_name: Optional[str]


@dataclass(frozen=True)
class StateQueryModel:
    state_id: Optional[str]
    state_name: Optional[str]
    state_code: Optional[str]
    country_id: int
    country_code: Optional[str]
    country_name: Optional[str]


