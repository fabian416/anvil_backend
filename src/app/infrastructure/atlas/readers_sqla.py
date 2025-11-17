from sqlalchemy import Select, and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.atlas.ports import CityReader, CountryReader
from app.application.atlas.query_models import CityQueryModel, CountryQueryModel, StateQueryModel
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import ReaderError
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.infrastructure.persistence_sqla.mappings.city import map_cities_table
from app.infrastructure.persistence_sqla.mappings.country import map_countries_table


class SqlaCountryReader(CountryReader):
    def __init__(self, session: MainAsyncSession):
        map_countries_table()
        self._session = session

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
    ) -> tuple[list[CountryQueryModel], int]:
        try:
            Countries = mapping_registry.metadata.tables["countries"]  # type: ignore
            stmt: Select = select(Countries)
            where = []
            if name:
                where.append(func.lower(Countries.c.name).like(f"%{name.lower()}%"))
            if iso2:
                where.append(Countries.c.iso2 == iso2.upper())
            if iso3:
                where.append(Countries.c.iso3 == iso3.upper())
            if region:
                where.append(func.lower(Countries.c.region).like(f"%{region.lower()}%"))
            if subregion:
                where.append(func.lower(Countries.c.subregion).like(f"%{subregion.lower()}%"))
            if currency:
                where.append(func.lower(Countries.c.currency).like(f"%{currency.lower()}%"))
            if where:
                stmt = stmt.where(and_(*where))

            total = (
                await self._session.execute(
                    select(func.count()).select_from(stmt.subquery())
                )
            ).scalar_one()

            stmt = stmt.order_by(Countries.c.name).offset(offset).limit(limit)
            rows = (await self._session.execute(stmt)).mappings().all()
            items = [
                CountryQueryModel(
                    id=row["id"],
                    country_id=row["country_id"],
                    name=row["name"],
                    iso2=row.get("iso2"),
                    iso3=row["iso3"],
                    region=row.get("region"),
                    subregion=row.get("subregion"),
                    currency=row.get("currency"),
                )
                for row in rows
            ]
            return items, int(total)
        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error


class SqlaCityReader(CityReader):
    def __init__(self, session: MainAsyncSession):
        map_cities_table()
        self._session = session

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
    ) -> tuple[list[CityQueryModel], int]:
        try:
            Cities = mapping_registry.metadata.tables["cities"]  # type: ignore
            stmt: Select = select(Cities)
            where = []
            if name:
                where.append(func.lower(Cities.c.name).like(f"%{name.lower()}%"))
            if country_id:
                where.append(Cities.c.country_id == country_id)
            if state_id:
                where.append(Cities.c.state_id == state_id)
            if state_code:
                where.append(Cities.c.state_code == state_code.upper())
            if state_name:
                where.append(func.lower(Cities.c.state_name).like(f"%{state_name.lower()}%"))
            if country_code:
                where.append(Cities.c.country_code == country_code.upper())
            if wiki_data_id:
                where.append(Cities.c.wikiDataId == wiki_data_id)
            if where:
                stmt = stmt.where(and_(*where))

            total = (
                await self._session.execute(
                    select(func.count()).select_from(stmt.subquery())
                )
            ).scalar_one()

            stmt = stmt.order_by(Cities.c.name).offset(offset).limit(limit)
            rows = (await self._session.execute(stmt)).mappings().all()
            items = [
                CityQueryModel(
                    id=row["id"],
                    city_id=row["city_id"],
                    name=row["name"],
                    country_id=row["country_id"],
                    country_code=row.get("country_code"),
                    country_name=row.get("country_name"),
                    state_id=row.get("state_id"),
                    state_code=row.get("state_code"),
                    state_name=row.get("state_name"),
                )
                for row in rows
            ]
            return items, int(total)
        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error

    async def list_states_by_country(self, country_id: int) -> list[StateQueryModel]:
        try:
            Cities = mapping_registry.metadata.tables["cities"]  # type: ignore
            stmt: Select = (
                select(
                    Cities.c.state_id,
                    Cities.c.state_name,
                    Cities.c.state_code,
                    Cities.c.country_id,
                    Cities.c.country_code,
                    Cities.c.country_name,
                )
                .where(Cities.c.country_id == country_id)
                .distinct(Cities.c.state_id)
                .order_by(Cities.c.state_name)
            )
            rows = (await self._session.execute(stmt)).mappings().all()
            return [
                StateQueryModel(
                    state_id=row["state_id"],
                    state_name=row["state_name"],
                    state_code=row["state_code"],
                    country_id=row["country_id"],
                    country_code=row["country_code"],
                    country_name=row["country_name"],
                )
                for row in rows
            ]
        except SQLAlchemyError as error:
            raise ReaderError(DB_QUERY_FAILED) from error


