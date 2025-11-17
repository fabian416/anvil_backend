from datetime import datetime

from sqlalchemy import Select, and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.subscription.ports import PaymentRepository
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.payment import map_payments_table
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaPaymentRepository(PaymentRepository):
    def __init__(self, session: MainAsyncSession):
        map_payments_table()
        self._session = session

    async def add(
        self,
        *,
        user_id: int,
        subscription_id: int | None,
        subscription_user_id: int | None,
        amount: float | None,
        currency: str,
        status: str,
        stripe_payment_intent_id: str | None,
        data_json: dict | None,
    ) -> int:
        try:
            table = mapping_registry.metadata.tables["payments"]  # type: ignore
            result = await self._session.execute(
                table.insert()
                .values(
                    user_id=user_id,
                    subscription_id=subscription_id,
                    subscription_user_id=subscription_user_id,
                    amount=amount,
                    currency=currency,
                    status=status,
                    stripe_payment_intent_id=stripe_payment_intent_id,
                    data_json=data_json,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                .returning(table.c.id)
            )
            return int(result.scalar_one())
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def find_pending_for_subscription_user(self, *, subscription_user_id: int) -> dict | None:
        try:
            table = mapping_registry.metadata.tables["payments"]  # type: ignore
            stmt: Select = select(table).where(
                and_(
                    table.c.subscription_user_id == subscription_user_id,
                    table.c.status == "pending",
                )
            )
            row = (await self._session.execute(stmt)).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_status(self, *, id_: int, status: str) -> None:
        try:
            table = mapping_registry.metadata.tables["payments"]  # type: ignore
            await self._session.execute(
                table.update().where(table.c.id == id_).values(status=status, updated_at=datetime.utcnow())
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def list_by_subscription_user(self, *, subscription_user_id: int) -> list[dict]:
        try:
            table = mapping_registry.metadata.tables["payments"]  # type: ignore
            stmt: Select = select(table).where(table.c.subscription_user_id == subscription_user_id)
            rows = (await self._session.execute(stmt)).mappings().all()
            return [dict(r) for r in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_data_json(self, *, id_: int, data_json: dict) -> None:
        try:
            table = mapping_registry.metadata.tables["payments"]  # type: ignore
            await self._session.execute(
                table.update().where(table.c.id == id_).values(data_json=data_json, updated_at=datetime.utcnow())
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_by_user_paginated(self, *, user_id: int, offset: int, limit: int) -> list[dict]:
        try:
            table = mapping_registry.metadata.tables["payments"]  # type: ignore
            stmt: Select = (
                select(table)
                .where(table.c.user_id == user_id)
                .order_by(table.c.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            rows = (await self._session.execute(stmt)).mappings().all()
            return [dict(r) for r in rows]
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def find_or_create_transaction(
        self,
        *,
        user_id: int,
        amount: float,
        currency: str,
        description: str,
    ) -> dict:
        try:
            table = mapping_registry.metadata.tables["payments"]  # type: ignore
            # naive approach: always create; in real case, would check idempotency key
            result = await self._session.execute(
                table.insert()
                .values(
                    user_id=user_id,
                    amount=amount,
                    currency=currency,
                    status="pending",
                    data_json={"description": description},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                .returning(table.c.id)
            )
            new_id = int(result.scalar_one())
            row = (await self._session.execute(select(table).where(table.c.id == new_id))).mappings().first()
            return dict(row) if row else {"id": new_id}
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error


