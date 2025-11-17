from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.common.ports.country_query_gateway import CountryQueryGateway
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import ReaderError
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.persistence_sqla.mappings.country import map_countries_table
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaCountryReader(CountryQueryGateway):
    def __init__(self, session: MainAsyncSession):
        map_countries_table()
        self._session = session

    async def exists(self, country_id: int) -> bool:
        try:
            CountriesTable = mapping_registry.metadata.tables["countries"]  # type: ignore
            # Validate against internal primary key `id`
            select_stmt: Select = select(CountriesTable.c.id).where(
                CountriesTable.c.id == country_id
            )
            row = (await self._session.execute(select_stmt)).first()
            return row is not None
        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error


