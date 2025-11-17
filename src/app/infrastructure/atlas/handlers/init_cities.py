import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from sqlalchemy import Select, and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.persistence_sqla.mappings.city import map_cities_table
from app.infrastructure.persistence_sqla.mappings.country import map_countries_table
from app.infrastructure.persistence_sqla.registry import mapping_registry

log = logging.getLogger(__name__)


class InitCitiesResult(TypedDict):
    total_cities: int
    added_cities: int
    updated_cities: int
    skipped_cities: int
    error_cities: int


@dataclass
class InitCitiesHandler:
    session: MainAsyncSession

    async def execute(self, csv_path: Path | None = None) -> InitCitiesResult:
        map_cities_table()
        map_countries_table()
        Cities = mapping_registry.metadata.tables["cities"]  # type: ignore
        Countries = mapping_registry.metadata.tables["countries"]  # type: ignore

        if csv_path is None:
            base = Path(__file__).resolve()
            try:
                csv_candidate = base.parents[5] / "dump" / "cities.csv"
            except IndexError:
                csv_candidate = base
            if csv_candidate.exists():
                csv_path = csv_candidate
            else:
                csv_path = base.parents[3] / "infrastructure" / "persistence_sqla" / "dump" / "cities.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"Cities data file not found: {csv_path}")

        total = 0
        added = 0
        updated = 0
        skipped = 0
        errors = 0

        try:
            with csv_path.open(newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    total += 1
                    try:
                        # Columns (baseapi):
                        # 0: city_id, 1: name, 2: state_id, 3: state_code, 4: state_name,
                        # 5: country_id, 6: country_code, 7: country_name, 8: latitude, 9: longitude, 10: wikiDataId
                        city_id = int(row[0])
                        name = str(row[1])
                        state_id = str(row[2]) if row[2] else None
                        state_code = str(row[3]) if row[3] else None
                        state_name = str(row[4]) if row[4] else None
                        country_id_ext = int(row[5])
                        country_code = str(row[6]) if row[6] else None
                        country_name = str(row[7]) if row[7] else None
                        # coordinates
                        def parse_float(v):
                            try:
                                return float(v)
                            except Exception:
                                return None
                        latitude = parse_float(row[8]) if len(row) > 8 else None
                        longitude = parse_float(row[9]) if len(row) > 9 else None
                        wikiDataId = str(row[10]) if len(row) > 10 and row[10] else None

                        # Resolve internal country.id by external country_id
                        country_row = (
                            await self.session.execute(
                                select(Countries.c.id).where(
                                    Countries.c.country_id == country_id_ext
                                )
                            )
                        ).first()
                        if not country_row:
                            skipped += 1
                            continue
                        country_pk = country_row[0]

                        existing = (
                            await self.session.execute(
                                select(Cities.c.id).where(
                                    and_(
                                        Cities.c.city_id == city_id,
                                        Cities.c.country_id == country_pk,
                                    )
                                )
                            )
                        ).first()

                        if existing:
                            await self.session.execute(
                                Cities.update()
                                .where(
                                    and_(
                                        Cities.c.city_id == city_id,
                                        Cities.c.country_id == country_pk,
                                    )
                                )
                                .values(
                                    name=name,
                                    state_id=state_id,
                                    state_code=state_code,
                                    state_name=state_name,
                                    country_code=country_code,
                                    country_name=country_name,
                                    latitude=latitude,
                                    longitude=longitude,
                                    wikiDataId=wikiDataId,
                                )
                            )
                            updated += 1
                        else:
                            await self.session.execute(
                                Cities.insert().values(
                                    city_id=city_id,
                                    name=name,
                                    state_id=state_id,
                                    state_code=state_code,
                                    state_name=state_name,
                                    country_id=country_pk,
                                    country_code=country_code,
                                    country_name=country_name,
                                    latitude=latitude,
                                    longitude=longitude,
                                    wikiDataId=wikiDataId,
                                )
                            )
                            added += 1
                    except Exception as e:  # noqa: BLE001
                        log.warning("Error processing city row %s: %s", row[:8], e)
                        errors += 1
                        continue

            await self.session.commit()
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

        return InitCitiesResult(
            total_cities=total,
            added_cities=added,
            updated_cities=updated,
            skipped_cities=skipped,
            error_cities=errors,
        )


