from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.common.ports.city_query_gateway import CityQueryGateway
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import ReaderError
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.persistence_sqla.mappings.city import map_cities_table
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaCityReader(CityQueryGateway):
    def __init__(self, session: MainAsyncSession):
        map_cities_table()
        self._session = session

    async def exists_in_country(self, city_id: int, country_id: int) -> bool:
        try:
            CitiesTable = mapping_registry.metadata.tables["cities"]  # type: ignore
            # country_id here is internal PK from `countries.id` used by cities.country_id
            select_stmt: Select = select(CitiesTable.c.id).where(
                (CitiesTable.c.id == city_id) & (CitiesTable.c.country_id == country_id)
            )
            row = (await self._session.execute(select_stmt)).first()
            return row is not None
        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error

    async def get_pk_in_country(self, city_id: int, country_id: int) -> int | None:
        try:
            CitiesTable = mapping_registry.metadata.tables["cities"]  # type: ignore
            select_stmt: Select = select(CitiesTable.c.id).where(
                (CitiesTable.c.id == city_id) & (CitiesTable.c.country_id == country_id)
            )
            row = (await self._session.execute(select_stmt)).first()
            return int(row[0]) if row else None
        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error


