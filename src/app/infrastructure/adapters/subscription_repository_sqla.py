from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.subscription.ports import SubscriptionRepository
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.subscription import (
    map_subscriptions_table,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaSubscriptionRepository(SubscriptionRepository):
    def __init__(self, session: MainAsyncSession):
        map_subscriptions_table()
        self._session = session

    async def read_by_name(self, name: str) -> dict | None:
        try:
            table = mapping_registry.metadata.tables["subscriptions"]  # type: ignore
            stmt: Select = select(table).where(table.c.name == name)
            row = (await self._session.execute(stmt)).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_all(self) -> list[dict]:
        try:
            table = mapping_registry.metadata.tables["subscriptions"]  # type: ignore
            stmt: Select = select(table)
            rows = (await self._session.execute(stmt)).mappings().all()
            return [dict(r) for r in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_by_id(self, id_: int) -> dict | None:
        try:
            table = mapping_registry.metadata.tables["subscriptions"]  # type: ignore
            stmt: Select = select(table).where(table.c.id == id_)
            row = (await self._session.execute(stmt)).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def add(
        self,
        *,
        name: str,
        price: float,
        subscription_type: str,
        currency: str,
        duration: int,
        features: dict | None,
        is_active: bool,
        stripe_price_id: str | None,
        stripe_product_id: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> int:
        try:
            table = mapping_registry.metadata.tables["subscriptions"]  # type: ignore
            result = await self._session.execute(
                table.insert()
                .values(
                    name=name,
                    price=price,
                    subscription_type=subscription_type,
                    currency=currency,
                    duration=duration,
                    features=features,
                    is_active=is_active,
                    stripe_price_id=stripe_price_id,
                    stripe_product_id=stripe_product_id,
                    created_at=created_at,
                    updated_at=updated_at,
                )
                .returning(table.c.id)
            )
            return int(result.scalar_one())
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_stripe_ids(self, *, id_: int, stripe_price_id: str, stripe_product_id: str) -> None:
        try:
            table = mapping_registry.metadata.tables["subscriptions"]  # type: ignore
            await self._session.execute(
                table.update()
                .where(table.c.id == id_)
                .values(stripe_price_id=stripe_price_id, stripe_product_id=stripe_product_id)
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error


