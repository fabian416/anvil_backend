from abc import abstractmethod
from typing import Protocol


class CountryQueryGateway(Protocol):
    @abstractmethod
    async def exists(self, country_id: int) -> bool: ...


