from abc import abstractmethod
from typing import Protocol

from app.application.atlas.query_models import CityQueryModel, CountryQueryModel, StateQueryModel


class CountryReader(Protocol):
    @abstractmethod
    async def search(
        self,
        *,
        name: str | None,
        iso2: str | None,
        iso3: str | None,
        region: str | None,
        subregion: str | None,
        currency: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[CountryQueryModel], int]: ...


class CityReader(Protocol):
    @abstractmethod
    async def search(
        self,
        *,
        name: str | None,
        country_id: int | None,
        state_id: str | None,
        state_code: str | None,
        state_name: str | None,
        country_code: str | None,
        wiki_data_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[CityQueryModel], int]: ...

    @abstractmethod
    async def list_states_by_country(self, country_id: int) -> list[StateQueryModel]: ...


