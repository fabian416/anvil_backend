"""
SQLAlchemy adapter for lending repository operations.

Implements LendingRepository protocol for health checks, alerts, and preferences.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import desc, select

from app.domain.entities.lending.lending_health_check import LendingHealthCheck
from app.domain.entities.lending.lending_alert import LendingAlert
from app.domain.entities.lending.user_lending_preferences import UserLendingPreferences
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class LendingRepositoryAdapterSqla:
    """SQLAlchemy implementation of LendingRepository protocol."""

    def __init__(self, session: MainAsyncSession):
        self._session = session
        self._health_checks_table = mapping_registry.metadata.tables[
            "lending_health_checks"
        ]
        self._alerts_table = mapping_registry.metadata.tables["lending_alerts"]
        self._preferences_table = mapping_registry.metadata.tables[
            "user_lending_preferences"
        ]
        self._positions_table = mapping_registry.metadata.tables[
            "lending_positions"
        ]

    # ═══════════════════════════════════════════════════════════════
    # HEALTH CHECKS
    # ═══════════════════════════════════════════════════════════════

    async def save_health_check(self, check: LendingHealthCheck) -> None:
        """Save health check snapshot."""
        values = {
            "id": check.id,
            "user_id": check.user_id,
            "protocol": check.protocol,
            "chain": check.chain,
            "health_factor": check.health_factor,
            "health_factor_level": check.health_factor_level,
            "total_collateral_usd": check.total_collateral_usd,
            "total_debt_usd": check.total_debt_usd,
            "available_to_borrow_usd": check.available_to_borrow_usd,
            "liquidation_price": check.liquidation_price,
            "checked_at": check.checked_at,
        }

        insert_stmt = self._health_checks_table.insert().values(**values)
        await self._session.execute(insert_stmt)
        await self._session.commit()

        logger.info(
            f"Saved health check for user {check.user_id}, "
            f"protocol={check.protocol}, HF={check.health_factor:.2f}"
        )

    async def get_recent_health_checks(
        self,
        user_id: UUID,
        protocol: str | None = None,
        limit: int = 10,
    ) -> list[LendingHealthCheck]:
        """Get recent health checks for a user."""
        query = (
            select(self._health_checks_table)
            .where(self._health_checks_table.c.user_id == user_id)
            .order_by(desc(self._health_checks_table.c.checked_at))
            .limit(limit)
        )

        if protocol:
            query = query.where(self._health_checks_table.c.protocol == protocol)

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [self._row_to_health_check(row) for row in rows]

    # ═══════════════════════════════════════════════════════════════
    # ALERTS
    # ═══════════════════════════════════════════════════════════════

    async def create_alert(self, alert: LendingAlert) -> None:
        """Create new alert."""
        values = {
            "id": alert.id,
            "user_id": alert.user_id,
            "position_id": alert.position_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "health_factor": alert.health_factor,
            "threshold_value": alert.threshold_value,
            "current_value": alert.current_value,
            "is_read": alert.is_read,
            "sent_at": alert.sent_at,
            "metadata": alert.metadata,
            "created_at": alert.created_at,
        }

        insert_stmt = self._alerts_table.insert().values(**values)
        await self._session.execute(insert_stmt)
        await self._session.commit()

        logger.info(
            f"Created alert {alert.id} for user {alert.user_id}, "
            f"type={alert.alert_type}, severity={alert.severity}"
        )

    async def get_unread_alerts(
        self,
        user_id: UUID,
        severity: str | None = None,
    ) -> list[LendingAlert]:
        """Get unread alerts for a user."""
        query = (
            select(self._alerts_table)
            .where(
                (self._alerts_table.c.user_id == user_id)
                & (self._alerts_table.c.is_read == False)  # noqa: E712
            )
            .order_by(desc(self._alerts_table.c.created_at))
        )

        if severity:
            query = query.where(self._alerts_table.c.severity == severity)

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [self._row_to_alert(row) for row in rows]

    async def mark_alert_as_read(self, alert_id: UUID) -> None:
        """Mark alert as read."""
        update_stmt = (
            self._alerts_table.update()
            .where(self._alerts_table.c.id == alert_id)
            .values(is_read=True)
        )
        await self._session.execute(update_stmt)
        await self._session.commit()

    # ═══════════════════════════════════════════════════════════════
    # USER PREFERENCES
    # ═══════════════════════════════════════════════════════════════

    async def get_user_preferences(
        self, user_id: UUID
    ) -> UserLendingPreferences | None:
        """Get user lending preferences."""
        query = select(self._preferences_table).where(
            self._preferences_table.c.user_id == user_id
        )

        result = await self._session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_preferences(row)

    # ═══════════════════════════════════════════════════════════════
    # ACTIVE USERS
    # ═══════════════════════════════════════════════════════════════

    async def get_users_with_active_positions(self) -> list[UUID]:
        """Get list of user IDs with active lending positions."""
        query = (
            select(self._positions_table.c.user_id.distinct())
            .where(self._positions_table.c.status == "active")
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [row[0] for row in rows]

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _row_to_health_check(self, row) -> LendingHealthCheck:
        """Convert database row to LendingHealthCheck entity."""
        return LendingHealthCheck(
            id=row.id,
            user_id=row.user_id,
            protocol=row.protocol,
            chain=row.chain,
            health_factor=Decimal(str(row.health_factor)),
            health_factor_level=row.health_factor_level,
            total_collateral_usd=Decimal(str(row.total_collateral_usd)),
            total_debt_usd=Decimal(str(row.total_debt_usd)),
            available_to_borrow_usd=(
                Decimal(str(row.available_to_borrow_usd))
                if row.available_to_borrow_usd
                else None
            ),
            liquidation_price=(
                Decimal(str(row.liquidation_price)) if row.liquidation_price else None
            ),
            checked_at=row.checked_at,
        )

    def _row_to_alert(self, row) -> LendingAlert:
        """Convert database row to LendingAlert entity."""
        return LendingAlert(
            id=row.id,
            user_id=row.user_id,
            position_id=row.position_id,
            alert_type=row.alert_type,
            severity=row.severity,
            title=row.title,
            message=row.message,
            health_factor=(
                Decimal(str(row.health_factor)) if row.health_factor else None
            ),
            threshold_value=(
                Decimal(str(row.threshold_value)) if row.threshold_value else None
            ),
            current_value=(
                Decimal(str(row.current_value)) if row.current_value else None
            ),
            is_read=row.is_read,
            sent_at=row.sent_at,
            metadata=row.metadata_,
            created_at=row.created_at,
        )

    async def get_user_wallet_address(self, user_id: UUID) -> str | None:
        """Get user's wallet address from user table."""
        users_table = mapping_registry.metadata.tables["users"]
        query = select(users_table.c.primary_wallet_address).where(
            users_table.c.id == user_id
        )
        result = await self._session.execute(query)
        row = result.fetchone()
        return row[0] if row else None

    def _row_to_preferences(self, row) -> UserLendingPreferences:
        """Convert database row to UserLendingPreferences entity."""
        return UserLendingPreferences(
            id=row.id,
            user_id=row.user_id,
            risk_tolerance=row.risk_tolerance,
            min_health_factor=Decimal(str(row.min_health_factor)),
            max_leverage=Decimal(str(row.max_leverage)),
            preferred_protocol=row.preferred_protocol,
            auto_rebalance=row.auto_rebalance,
            notification_health_threshold=(
                Decimal(str(row.notification_health_threshold))
                if row.notification_health_threshold
                else None
            ),
            notification_email=row.notification_email,
            notification_enabled=row.notification_enabled,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
