import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from sqlalchemy import Select, and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.persistence_sqla.mappings.country import map_countries_table
from app.infrastructure.persistence_sqla.registry import mapping_registry

log = logging.getLogger(__name__)


class InitCountriesResult(TypedDict):
    total_countries: int
    added_countries: int
    updated_countries: int
    error_countries: int


@dataclass
class InitCountriesHandler:
    session: MainAsyncSession

    async def execute(self, csv_path: Path | None = None) -> InitCountriesResult:
        map_countries_table()
        Countries = mapping_registry.metadata.tables["countries"]  # type: ignore

        if csv_path is None:
            base = Path(__file__).resolve()
            # Prefer project-root dump/countries.csv
            try:
                csv_candidate = base.parents[5] / "dump" / "countries.csv"
            except IndexError:
                csv_candidate = base
            if csv_candidate.exists():
                csv_path = csv_candidate
            else:
                # Fallback to old location
                csv_path = base.parents[3] / "infrastructure" / "persistence_sqla" / "dump" / "countries.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"Countries data file not found: {csv_path}")

        total = 0
        added = 0
        updated = 0
        errors = 0

        try:
            with csv_path.open(newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    total += 1
                    try:
                        # Expected CSV columns (see baseapi):
                        # 0: country_id, 1: name, 2: iso3, 3: iso2, 4: numeric_code, 5: phonecode,
                        # 6: capital, 7: currency, 8: currency_name, 9: currency_symbol, 10: tld,
                        # 11: native, 12: region, 14: subregion, 16: nationality, 17: timezones,
                        # 18: latitude, 19: longitude, 20: emoji, 21: emojiU
                        country_id = int(row[0])
                        name = str(row[1])
                        iso3 = str(row[2]) if row[2] else None
                        raw_iso2 = (row[3] or "").strip().upper()
                        iso2 = raw_iso2 if len(raw_iso2) == 2 and raw_iso2.isalpha() else None
                        # numeric_code formatted to 3 digits if numeric
                        raw_numeric = row[4]
                        numeric_code = None
                        if raw_numeric not in (None, ""):
                            try:
                                numeric_code = f"{int(raw_numeric):03d}"
                            except Exception:
                                numeric_code = str(raw_numeric)
                        phonecode = str(row[5]) if row[5] else None
                        if phonecode and not phonecode.startswith("+"):
                            phonecode = f"+{phonecode}"
                        capital = str(row[6]) if row[6] else None
                        currency = str(row[7]) if row[7] else None
                        currency_name = str(row[8]) if row[8] else None
                        currency_symbol = str(row[9]) if row[9] else None
                        tld = str(row[10]) if row[10] else None
                        native = str(row[11]) if row[11] else None
                        region = str(row[12]) if row[12] else None
                        subregion = str(row[14]) if row[14] else None
                        nationality = str(row[16]) if row[16] else None
                        # timezones: expect list-like string; store as JSON array
                        timezones_raw = row[17]
                        timezones = None
                        if timezones_raw and timezones_raw not in ("[]", "null"):
                            # Try strict JSON first
                            try:
                                timezones = json.loads(timezones_raw)
                            except json.JSONDecodeError:
                                # Heuristic normalization: quote keys, normalize slashes, convert quotes
                                import re

                                s = str(timezones_raw).strip()
                                # Unescape JSON-style slashes
                                s = s.replace("\\/", "/")
                                # Quote bare object keys: {zoneName: ...} -> {"zoneName": ...}
                                s = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', s)
                                # Replace single quotes with double quotes
                                s = s.replace("'", '"')
                                # Final attempt to parse
                                try:
                                    timezones = json.loads(s)
                                    print(timezones)
                                except json.JSONDecodeError:
                                    timezones = None
                        # coordinates
                        def parse_float(v):
                            try:
                                return float(v)
                            except Exception:
                                return None
                        latitude = parse_float(row[18]) if len(row) > 18 else None
                        longitude = parse_float(row[19]) if len(row) > 19 else None
                        emoji = str(row[20]) if len(row) > 20 and row[20] else None
                        emojiU = str(row[21]) if len(row) > 21 and row[21] else None

                        select_stmt: Select = select(Countries.c.id).where(
                            Countries.c.country_id == country_id
                        )
                        existing = (await self.session.execute(select_stmt)).first()

                        if existing:
                            await self.session.execute(
                                Countries.update()
                                .where(Countries.c.country_id == country_id)
                                .values(
                                    name=name,
                                    iso3=iso3,
                                    iso2=iso2,
                                    numeric_code=numeric_code,
                                    phonecode=phonecode,
                                    capital=capital,
                                    currency=currency,
                                    currency_name=currency_name,
                                    currency_symbol=currency_symbol,
                                    tld=tld,
                                    native=native,
                                    region=region,
                                    subregion=subregion,
                                    nationality=nationality,
                                    timezones=timezones,
                                    latitude=latitude,
                                    longitude=longitude,
                                    emoji=emoji,
                                    emojiU=emojiU,
                                )
                            )
                            updated += 1
                        else:
                            await self.session.execute(
                                Countries.insert().values(
                                    country_id=country_id,
                                    name=name,
                                    iso3=iso3,
                                    iso2=iso2,
                                    numeric_code=numeric_code,
                                    phonecode=phonecode,
                                    capital=capital,
                                    currency=currency,
                                    currency_name=currency_name,
                                    currency_symbol=currency_symbol,
                                    tld=tld,
                                    native=native,
                                    region=region,
                                    subregion=subregion,
                                    nationality=nationality,
                                    timezones=timezones,
                                    latitude=latitude,
                                    longitude=longitude,
                                    emoji=emoji,
                                    emojiU=emojiU,
                                )
                            )
                            added += 1
                    except Exception as e:  # noqa: BLE001
                        log.warning("Error processing country row %s: %s", row[:4], e)
                        errors += 1
                        continue

            await self.session.commit()
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

        return InitCountriesResult(
            total_countries=total,
            added_countries=added,
            updated_countries=updated,
            error_countries=errors,
        )


