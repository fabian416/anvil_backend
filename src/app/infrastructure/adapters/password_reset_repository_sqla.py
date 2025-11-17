from datetime import datetime

from sqlalchemy import Select, and_, delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.common.ports.password_reset_repository import PasswordResetRepository
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.password_reset import (
    map_password_resets_table,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaPasswordResetRepository(PasswordResetRepository):
    def __init__(self, session: MainAsyncSession):
        map_password_resets_table()
        self._session = session

    async def add(self, *, user_id: int, token: str, expires_at: datetime) -> None:
        try:
            table = mapping_registry.metadata.tables["password_resets"]  # type: ignore
            await self._session.execute(
                table.insert().values(
                    user_id=user_id,
                    token=token,
                    expires_at=expires_at,
                    is_used=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def invalidate_all_for_user(self, *, user_id: int) -> None:
        try:
            table = mapping_registry.metadata.tables["password_resets"]  # type: ignore
            await self._session.execute(
                table.update().where(table.c.user_id == user_id).values(is_used=True, updated_at=datetime.utcnow())
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def read_by_token(self, *, token: str) -> dict | None:
        try:
            table = mapping_registry.metadata.tables["password_resets"]  # type: ignore
            select_stmt: Select = select(table).where(
                and_(
                    table.c.token == token,
                    table.c.is_used == False,  # noqa: E712
                    table.c.expires_at > datetime.utcnow(),
                )
            )
            row = (await self._session.execute(select_stmt)).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def mark_used(self, *, id_: int) -> None:
        try:
            table = mapping_registry.metadata.tables["password_resets"]  # type: ignore
            await self._session.execute(
                table.update().where(table.c.id == id_).values(is_used=True, updated_at=datetime.utcnow())
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def delete_by_id(self, *, id_: int) -> None:
        try:
            table = mapping_registry.metadata.tables["password_resets"]  # type: ignore
            await self._session.execute(
                delete(table).where(table.c.id == id_)
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error


