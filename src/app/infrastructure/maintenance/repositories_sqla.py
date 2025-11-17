from datetime import datetime

from sqlalchemy import Delete, delete
from sqlalchemy.exc import SQLAlchemyError

from app.application.maintenance.ports import (
    AuthSessionRepository,
    PasswordResetRepository,
)
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.auth_session import (
    auth_sessions_table,
)
from app.infrastructure.persistence_sqla.mappings.password_reset import (
    map_password_resets_table,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaAuthSessionRepository(AuthSessionRepository):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def delete_expired(self, now: datetime) -> int:
        try:
            stmt: Delete = delete(auth_sessions_table).where(
                auth_sessions_table.c.expiration < now
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return int(getattr(result, "rowcount", 0) or 0)
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error


class SqlaPasswordResetRepository(PasswordResetRepository):
    def __init__(self, session: MainAsyncSession):
        self._session = session

    async def delete_expired(self, now: datetime) -> int:
        try:
            # Ensure table is mapped, then fetch table from registry
            map_password_resets_table()
            pr_table = mapping_registry.metadata.tables["password_resets"]
            stmt: Delete = delete(pr_table).where(
                pr_table.c.expires_at < now
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return int(getattr(result, "rowcount", 0) or 0)
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error


