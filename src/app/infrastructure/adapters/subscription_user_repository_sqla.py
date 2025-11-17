from datetime import datetime

from sqlalchemy import Select, and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.subscription.ports import SubscriptionUserRepository
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.subscription_user import (
    map_subscription_users_table,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaSubscriptionUserRepository(SubscriptionUserRepository):
    def __init__(self, session: MainAsyncSession):
        map_subscription_users_table()
        self._session = session

    async def add(
        self,
        *,
        user_id: int,
        subscription_id: int,
        status: str,
        data_json: dict | None,
    ) -> int:
        try:
            table = mapping_registry.metadata.tables["subscription_users"]  # type: ignore
            result = await self._session.execute(
                table.insert()
                .values(
                    user_id=user_id,
                    subscription_id=subscription_id,
                    status=status,
                    data_json=data_json,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                .returning(table.c.id)
            )
            return int(result.scalar_one())
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_for_user_by_id(self, *, id_: int, user_id: int) -> dict | None:
        try:
            table = mapping_registry.metadata.tables["subscription_users"]  # type: ignore
            stmt: Select = select(table).where(
                and_(table.c.id == id_, table.c.user_id == user_id)
            )
            row = (await self._session.execute(stmt)).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_status(self, *, id_: int, status: str) -> None:
        try:
            table = mapping_registry.metadata.tables["subscription_users"]  # type: ignore
            await self._session.execute(
                table.update().where(table.c.id == id_).values(status=status, updated_at=datetime.utcnow())
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_stripe_subscription_id(self, *, id_: int, stripe_subscription_id: str) -> None:
        try:
            table = mapping_registry.metadata.tables["subscription_users"]  # type: ignore
            await self._session.execute(
                table.update()
                .where(table.c.id == id_)
                .values(stripe_subscription_id=stripe_subscription_id, updated_at=datetime.utcnow())
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_by_checkout_session_id(self, *, session_id: str) -> dict | None:
        try:
            table = mapping_registry.metadata.tables["subscription_users"]  # type: ignore
            # Postgres JSON ->> operator via SQLAlchemy: data_json['checkout_session_id'].astext
            stmt: Select = select(table).where(
                table.c.data_json["checkout_session_id"].astext == session_id  # type: ignore[attr-defined]
            )
            row = (await self._session.execute(stmt)).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_data_json(self, *, id_: int, data_json: dict) -> None:
        try:
            table = mapping_registry.metadata.tables["subscription_users"]  # type: ignore
            await self._session.execute(
                table.update().where(table.c.id == id_).values(data_json=data_json, updated_at=datetime.utcnow())
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_active_for_user_and_subscription(
        self, *, user_id: int, subscription_id: int
    ) -> dict | None:
        try:
            table = mapping_registry.metadata.tables["subscription_users"]  # type: ignore
            stmt: Select = select(table).where(
                and_(
                    table.c.user_id == user_id,
                    table.c.subscription_id == subscription_id,
                    table.c.status == "active",
                )
            )
            row = (await self._session.execute(stmt)).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error


