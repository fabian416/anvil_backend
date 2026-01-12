"""
SQLAlchemy implementation of MoonPay Token Repository.

Stores and retrieves MoonPay authentication tokens for swap execution.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.domain.ports.moonpay_token_repository import (
    MoonPayTokenData,
    MoonPayTokenRepository,
)
from app.infrastructure.adapters.constants import DB_QUERY_FAILED
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.moonpay import (
    map_moonpay_customer_tokens_table,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaMoonPayTokenRepository(MoonPayTokenRepository):
    """SQLAlchemy implementation of MoonPay token repository."""

    def __init__(self, session: MainAsyncSession) -> None:
        map_moonpay_customer_tokens_table()
        self._session = session

    def _get_table(self):
        """Get the moonpay_customer_tokens table."""
        return mapping_registry.metadata.tables["moonpay_customer_tokens"]

    async def get_by_user_id(self, user_id: UUID) -> MoonPayTokenData | None:
        """Get MoonPay tokens for a user."""
        try:
            table = self._get_table()
            stmt = select(table).where(table.c.user_id == user_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()

            if row is None:
                return None

            return MoonPayTokenData(
                id=row["id"],
                user_id=row["user_id"],
                moonpay_token=row["moonpay_token"],
                moonpay_csrf_token=row["moonpay_csrf_token"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                expires_at=row["expires_at"],
            )
        except SQLAlchemyError as error:
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def upsert(
        self,
        user_id: UUID,
        moonpay_token: str,
        moonpay_csrf_token: str,
        expires_at: datetime | None = None,
    ) -> None:
        """Insert or update MoonPay tokens for a user."""
        try:
            table = self._get_table()
            now = datetime.utcnow()

            # Use PostgreSQL's INSERT ... ON CONFLICT DO UPDATE (upsert)
            stmt = insert(table).values(
                id=uuid4(),
                user_id=user_id,
                moonpay_token=moonpay_token,
                moonpay_csrf_token=moonpay_csrf_token,
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
            )

            # On conflict (user_id is unique), update the tokens
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "moonpay_token": moonpay_token,
                    "moonpay_csrf_token": moonpay_csrf_token,
                    "updated_at": now,
                    "expires_at": expires_at,
                },
            )

            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def delete_by_user_id(self, user_id: UUID) -> None:
        """Delete MoonPay tokens for a user."""
        try:
            table = self._get_table()
            stmt = delete(table).where(table.c.user_id == user_id)
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as error:
            await self._session.rollback()
            raise DataMapperError(DB_QUERY_FAILED) from error

    async def has_valid_tokens(self, user_id: UUID) -> bool:
        """Check if a user has valid (non-expired) MoonPay tokens."""
        token_data = await self.get_by_user_id(user_id)
        if token_data is None:
            return False
        return not token_data.is_expired()
