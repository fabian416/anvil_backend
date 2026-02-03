"""
SQLAlchemy adapter for money market user preferences.

Implements MoneyMarketPreferenceGateway port for user settings management.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.domain.entities.money_market.user_preference import (
    MoneyMarketUserPreference,
)
from app.domain.ports.money_market.money_market_preference_gateway import (
    MoneyMarketPreferenceGateway,
)
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class MoneyMarketPreferenceAdapterSqla(MoneyMarketPreferenceGateway):
    """SQLAlchemy implementation of MoneyMarketPreferenceGateway."""

    def __init__(self, session: MainAsyncSession):
        self._session = session
        self._table = mapping_registry.metadata.tables["money_market_user_preferences"]

    # ═══════════════════════════════════════════════════════════════
    # PREFERENCE CRUD
    # ═══════════════════════════════════════════════════════════════

    async def get_preferences(
        self,
        user_id: UUID,
    ) -> MoneyMarketUserPreference | None:
        """Get user's money market preferences."""
        query = select(self._table).where(self._table.c.user_id == user_id)

        result = await self._session.execute(query)
        row = result.fetchone()

        if not row:
            logger.debug(f"No preferences found for user {user_id}")
            return None

        return self._row_to_entity(row)

    async def upsert_preferences(
        self,
        user_preference: MoneyMarketUserPreference,
    ) -> None:
        """Create or update user preferences (UPSERT)."""
        now = datetime.now(timezone.utc)

        values = {
            "id": user_preference.id,
            "user_id": user_preference.user_id,
            "preferred_protocols": (
                [user_preference.preferred_protocol]
                if user_preference.preferred_protocol
                else []
            ),
            "excluded_protocols": [],
            "preferred_chains": user_preference.watched_chains,
            "min_supply_apy": None,
            "max_borrow_apy": None,
            "risk_tolerance": "moderate",
            "min_liquidity_usd": None,
            "max_utilization_rate": None,
            "enable_rate_alerts": user_preference.enable_rate_alerts,
            "notification_channels": ["in_app"],
            "show_rewards": True,
            "sort_by": "best_rate",
            "created_at": user_preference.created_at,
            "updated_at": now,
        }

        # PostgreSQL UPSERT
        stmt = pg_insert(self._table).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id"],
            set_={
                "preferred_protocols": stmt.excluded.preferred_protocols,
                "preferred_chains": stmt.excluded.preferred_chains,
                "enable_rate_alerts": stmt.excluded.enable_rate_alerts,
                "notification_channels": stmt.excluded.notification_channels,
                "updated_at": now,
            },
        )

        await self._session.execute(stmt)
        await self._session.commit()

        logger.info(f"Upserted preferences for user {user_preference.user_id}")

    async def delete_preferences(
        self,
        user_id: UUID,
    ) -> bool:
        """Delete user's preferences."""
        delete_stmt = delete(self._table).where(self._table.c.user_id == user_id)

        result = await self._session.execute(delete_stmt)
        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted preferences for user {user_id}")
        return deleted

    async def get_users_with_rate_alerts_enabled(
        self,
        asset: str | None = None,
        chain: str | None = None,
    ) -> list[MoneyMarketUserPreference]:
        """Get all users with rate alerts enabled."""
        query = select(self._table).where(self._table.c.enable_rate_alerts == True)

        # Filter by asset if provided (check if asset in preferred_chains array)
        if chain:
            query = query.where(
                func.array_position(self._table.c.preferred_chains, chain) > 0
            )

        result = await self._session.execute(query)
        rows = result.fetchall()

        preferences = [self._row_to_entity(row) for row in rows]
        logger.debug(f"Found {len(preferences)} users with rate alerts enabled")
        return preferences

    async def get_preferences_by_protocol(
        self,
        protocol: str,
    ) -> list[MoneyMarketUserPreference]:
        """Get users who prefer a specific protocol."""
        query = select(self._table).where(
            func.array_position(self._table.c.preferred_protocols, protocol) > 0
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [self._row_to_entity(row) for row in rows]

    async def count_users_watching_asset(
        self,
        asset: str,
    ) -> int:
        """Count users watching a specific asset."""
        # Asset tracking not directly in table schema
        # Would need to use preferred_chains as proxy
        logger.warning("Asset watching count not fully implemented")
        return 0

    async def count_users_watching_chain(
        self,
        chain: str,
    ) -> int:
        """Count users watching a specific chain."""
        query = (
            select(func.count())
            .select_from(self._table)
            .where(func.array_position(self._table.c.preferred_chains, chain) > 0)
        )

        result = await self._session.execute(query)
        return result.scalar()

    async def get_notification_enabled_users(
        self,
    ) -> list[MoneyMarketUserPreference]:
        """Get all users with notifications enabled."""
        query = select(self._table).where(self._table.c.enable_rate_alerts == True)

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [self._row_to_entity(row) for row in rows]

    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _row_to_entity(self, row) -> MoneyMarketUserPreference:
        """Convert database row to domain entity."""
        # Extract preferred protocol from array
        preferred_protocol = None
        if row.preferred_protocols and len(row.preferred_protocols) > 0:
            preferred_protocol = row.preferred_protocols[0]

        # Map watched_chains from preferred_chains
        watched_chains = row.preferred_chains or []

        return MoneyMarketUserPreference(
            id=row.id,
            user_id=row.user_id,
            enable_rate_alerts=row.enable_rate_alerts,
            alert_threshold_apy_change=row.min_supply_apy or 0.5,  # Default 0.5%
            watched_assets=[],  # Not in table schema
            watched_chains=watched_chains,
            preferred_protocol=preferred_protocol,
            notification_enabled=row.enable_rate_alerts,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
