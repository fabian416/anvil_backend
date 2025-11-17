from abc import abstractmethod
from typing import Protocol


class CityQueryGateway(Protocol):
    @abstractmethod
    async def exists_in_country(self, city_id: int, country_id: int) -> bool: ...

    @abstractmethod
    async def get_pk_in_country(self, city_id: int, country_id: int) -> int | None: ...


