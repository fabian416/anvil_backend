from dataclasses import dataclass

from app.application.atlas.ports import CityReader, CountryReader
from app.application.atlas.query_models import CityQueryModel, CountryQueryModel, StateQueryModel


@dataclass(frozen=True, slots=True)
class SearchCountriesRequest:
    name: str | None
    iso2: str | None
    iso3: str | None
    region: str | None
    subregion: str | None
    currency: str | None
    limit: int
    offset: int


@dataclass(frozen=True)
class SearchCountriesResponse:
    data: list[CountryQueryModel]
    total: int


class SearchCountriesQueryService:
    def __init__(self, country_reader: CountryReader):
        self._country_reader = country_reader

    async def execute(self, request: SearchCountriesRequest) -> SearchCountriesResponse:
        items, total = await self._country_reader.search(
            name=request.name,
            iso2=request.iso2,
            iso3=request.iso3,
            region=request.region,
            subregion=request.subregion,
            currency=request.currency,
            limit=request.limit,
            offset=request.offset,
        )
        return SearchCountriesResponse(data=items, total=total)


@dataclass(frozen=True, slots=True)
class SearchCitiesRequest:
    name: str | None
    country_id: int | None
    state_id: str | None
    state_code: str | None
    state_name: str | None
    country_code: str | None
    wiki_data_id: str | None
    limit: int
    offset: int


@dataclass(frozen=True)
class SearchCitiesResponse:
    data: list[CityQueryModel]
    total: int


class SearchCitiesQueryService:
    def __init__(self, city_reader: CityReader):
        self._city_reader = city_reader

    async def execute(self, request: SearchCitiesRequest) -> SearchCitiesResponse:
        items, total = await self._city_reader.search(
            name=request.name,
            country_id=request.country_id,
            state_id=request.state_id,
            state_code=request.state_code,
            state_name=request.state_name,
            country_code=request.country_code,
            wiki_data_id=request.wiki_data_id,
            limit=request.limit,
            offset=request.offset,
        )
        return SearchCitiesResponse(data=items, total=total)


@dataclass(frozen=True, slots=True)
class ListStatesByCountryRequest:
    country_id: int


class ListStatesByCountryQueryService:
    def __init__(self, city_reader: CityReader):
        self._city_reader = city_reader

    async def execute(self, request: ListStatesByCountryRequest) -> list[StateQueryModel]:
        return await self._city_reader.list_states_by_country(request.country_id)


