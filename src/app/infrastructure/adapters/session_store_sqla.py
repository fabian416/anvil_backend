from datetime import datetime, timedelta

from sqlalchemy import Select, and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.common.ports.session_store import SessionRow, SessionStore
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.session import map_sessions_table
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaSessionStore(SessionStore):
    def __init__(self, session: MainAsyncSession):
        map_sessions_table()
        self._session = session

    async def read_by_refresh_token(self, refresh_token: str) -> SessionRow | None:
        try:
            SessionsTable = mapping_registry.metadata.tables["sessions"]  # type: ignore
            select_stmt: Select = select(SessionsTable).where(
                and_(
                    SessionsTable.c.refresh_token == refresh_token,
                    SessionsTable.c.is_active == True,  # noqa: E712
                    SessionsTable.c.expires_at > datetime.utcnow(),
                )
            )
            row = (await self._session.execute(select_stmt)).mappings().first()
            return dict(row) if row else None
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def update_tokens(
        self,
        *,
        refresh_token: str,
        new_access_token: str,
        new_refresh_token: str,
        ip_address: str | None,
        user_agent: str | None,
        last_activity: datetime,
    ) -> None:
        try:
            SessionsTable = mapping_registry.metadata.tables["sessions"]  # type: ignore
            await self._session.execute(
                SessionsTable.update()
                .where(SessionsTable.c.refresh_token == refresh_token)
                .values(
                    access_token=new_access_token,
                    refresh_token=new_refresh_token,
                    last_activity=last_activity,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def add(
        self,
        *,
        user_id: int,
        access_token: str,
        refresh_token: str,
        token_type: str,
        ip_address: str | None,
        user_agent: str | None,
        created_at: datetime,
        expires_at: datetime,
        last_activity: datetime,
        is_active: bool,
    ) -> None:
        try:
            SessionsTable = mapping_registry.metadata.tables["sessions"]  # type: ignore
            await self._session.execute(
                SessionsTable.insert().values(
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type=token_type,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=created_at,
                    expires_at=expires_at,
                    last_activity=last_activity,
                    is_active=is_active,
                )
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error


