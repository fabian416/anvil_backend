from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError

from app.application.notification.ports import NotificationRepository
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.infrastructure.persistence_sqla.mappings.notification import map_notifications_table


class SqlaNotificationRepository(NotificationRepository):
    def __init__(self, session: MainAsyncSession):
        map_notifications_table()
        self._session = session

    async def read_by_user_paginated(
        self,
        *,
        user_id: int,
        offset: int,
        limit: int,
    ) -> list[dict]:
        try:
            table = mapping_registry.metadata.tables["notifications"]  # type: ignore
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


