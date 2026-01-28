"""
SQLAlchemy adapter for money market alerts.

Implements MoneyMarketAlertGateway port for rate change alert management.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.money_market.alert import MoneyMarketAlert
from app.domain.ports.money_market.money_market_alert_gateway import (
    MoneyMarketAlertGateway,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class MoneyMarketAlertAdapterSqla(MoneyMarketAlertGateway):
    """SQLAlchemy implementation of MoneyMarketAlertGateway."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._table = mapping_registry.metadata.tables[
            "money_market_alert_history"
        ]

    # ═══════════════════════════════════════════════════════════════
    # ALERT CRUD
    # ═══════════════════════════════════════════════════════════════

    async def create_alert(
        self,
        alert: MoneyMarketAlert,
    ) -> UUID:
        """Create a new rate change alert."""
        values = {
            "id": alert.id,
            "alert_id": alert.id,  # Self-reference for now
            "user_id": alert.user_id,
            "alert_type": alert.alert_type,
            "condition_met": alert.message,  # Use message as condition_met
            "protocol_name": alert.protocol,
            "asset_symbol": alert.asset,
            "chain": alert.chain,
            "current_rate": alert.new_apy,
            "threshold_value": alert.previous_apy,
            "notification_sent": alert.notification_sent,
            "notification_channels_used": None,
            "notification_error": None,
            "metadata": None,
            "triggered_at": alert.created_at,
            "notified_at": alert.sent_at,
        }

        insert_stmt = self._table.insert().values(**values)
        await self._session.execute(insert_stmt)
        await self._session.commit()

        logger.info(
            f"Created alert for user {alert.user_id} "
            f"({alert.protocol}/{alert.asset}/{alert.chain})"
        )
        return alert.id

    async def get_alert_by_id(
        self,
        alert_id: UUID,
    ) -> MoneyMarketAlert | None:
        """Get specific alert by ID."""
        query = select(self._table).where(self._table.c.id == alert_id)

        result = await self._session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_entity(row)

    async def get_user_alerts(
        self,
        user_id: UUID,
        is_read: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MoneyMarketAlert]:
        """Get user's alerts with optional read status filter."""
        query = (
            select(self._table)
            .where(self._table.c.user_id == user_id)
            .order_by(desc(self._table.c.triggered_at))
            .limit(limit)
            .offset(offset)
        )

        # Note: is_read field doesn't exist in money_market_alert_history
        # Would need to add this field or track separately

        result = await self._session.execute(query)
        rows = result.fetchall()

        alerts = [self._row_to_entity(row) for row in rows]
        logger.debug(f"Retrieved {len(alerts)} alerts for user {user_id}")
        return alerts

    async def get_unread_alert_count(
        self,
        user_id: UUID,
    ) -> int:
        """Get count of unread alerts for user."""
        # Note: is_read field doesn't exist in table
        # Would need to add this field
        logger.warning("Unread alert count not fully implemented")
        return 0

    async def mark_alert_read(
        self,
        alert_id: UUID,
    ) -> bool:
        """Mark alert as read."""
        # Note: is_read field doesn't exist in table
        # Would need to add this field
        logger.warning("Mark alert read not fully implemented")
        return False

    async def mark_all_alerts_read(
        self,
        user_id: UUID,
    ) -> int:
        """Mark all user alerts as read."""
        # Note: is_read field doesn't exist in table
        logger.warning("Mark all alerts read not fully implemented")
        return 0

    async def delete_alert(
        self,
        alert_id: UUID,
    ) -> bool:
        """Delete an alert."""
        delete_stmt = delete(self._table).where(self._table.c.id == alert_id)

        result = await self._session.execute(delete_stmt)
        await self._session.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted alert {alert_id}")
        return deleted

    async def get_alerts_by_asset(
        self,
        user_id: UUID,
        asset: str,
        chain: str,
        limit: int = 10,
    ) -> list[MoneyMarketAlert]:
        """Get user's alerts for specific asset/chain."""
        query = (
            select(self._table)
            .where(
                and_(
                    self._table.c.user_id == user_id,
                    self._table.c.asset_symbol == asset,
                    self._table.c.chain == chain,
                )
            )
            .order_by(desc(self._table.c.triggered_at))
            .limit(limit)
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [self._row_to_entity(row) for row in rows]

    async def get_recent_alerts(
        self,
        user_id: UUID,
        hours: int = 24,
    ) -> list[MoneyMarketAlert]:
        """Get user's recent alerts within time window."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = (
            select(self._table)
            .where(
                and_(
                    self._table.c.user_id == user_id,
                    self._table.c.triggered_at >= since,
                )
            )
            .order_by(desc(self._table.c.triggered_at))
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [self._row_to_entity(row) for row in rows]

    async def get_alerts_by_protocol(
        self,
        user_id: UUID,
        protocol: str,
        limit: int = 10,
    ) -> list[MoneyMarketAlert]:
        """Get user's alerts for specific protocol."""
        query = (
            select(self._table)
            .where(
                and_(
                    self._table.c.user_id == user_id,
                    self._table.c.protocol_name == protocol,
                )
            )
            .order_by(desc(self._table.c.triggered_at))
            .limit(limit)
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [self._row_to_entity(row) for row in rows]

    async def update_notification_status(
        self,
        alert_id: UUID,
        notification_sent: bool,
        sent_at: datetime | None = None,
    ) -> bool:
        """Update alert notification status."""
        if notification_sent and not sent_at:
            raise ValueError(
                "sent_at is required when notification_sent=True"
            )

        update_stmt = (
            self._table.update()
            .where(self._table.c.id == alert_id)
            .values(
                notification_sent=notification_sent,
                notified_at=sent_at,
            )
        )

        result = await self._session.execute(update_stmt)
        await self._session.commit()

        return result.rowcount > 0

    async def get_alert_statistics(
        self,
        user_id: UUID,
        days: int = 30,
    ) -> dict:
        """Get alert statistics for user over time period."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(self._table).where(
            and_(
                self._table.c.user_id == user_id,
                self._table.c.triggered_at >= since,
            )
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        if not rows:
            return {
                "total_alerts": 0,
                "unread_alerts": 0,
                "alerts_by_type": {},
                "alerts_by_severity": {},
                "alerts_by_protocol": {},
                "avg_apy_change": 0,
                "notification_success_rate": 0,
            }

        # Calculate statistics
        total_alerts = len(rows)
        alerts_by_type = {}
        alerts_by_protocol = {}
        notification_count = sum(1 for row in rows if row.notification_sent)

        for row in rows:
            # Count by type
            alerts_by_type[row.alert_type] = (
                alerts_by_type.get(row.alert_type, 0) + 1
            )

            # Count by protocol
            alerts_by_protocol[row.protocol_name] = (
                alerts_by_protocol.get(row.protocol_name, 0) + 1
            )

        notification_rate = (
            (notification_count / total_alerts * 100) if total_alerts > 0 else 0
        )

        return {
            "total_alerts": total_alerts,
            "unread_alerts": 0,  # Not tracked
            "alerts_by_type": alerts_by_type,
            "alerts_by_severity": {},  # Not in table
            "alerts_by_protocol": alerts_by_protocol,
            "avg_apy_change": 0,  # Would need calculation
            "notification_success_rate": round(notification_rate, 2),
        }

    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _row_to_entity(self, row) -> MoneyMarketAlert:
        """Convert database row to domain entity."""
        # Calculate APY change from current_rate and threshold_value
        previous_apy = row.threshold_value or row.current_rate
        new_apy = row.current_rate
        apy_change_percent = (
            ((new_apy - previous_apy) / previous_apy * 100)
            if previous_apy > 0
            else 0
        )

        # Determine severity from alert_type
        severity = "info" if "increase" in row.alert_type else "warning"

        return MoneyMarketAlert(
            id=row.id,
            user_id=row.user_id,
            alert_type=row.alert_type,
            protocol=row.protocol_name,
            asset=row.asset_symbol,
            chain=row.chain,
            previous_apy=previous_apy,
            new_apy=new_apy,
            apy_change_percent=apy_change_percent,
            severity=severity,
            message=row.condition_met,
            is_read=False,  # Not in table
            notification_sent=row.notification_sent,
            sent_at=row.notified_at,
            created_at=row.triggered_at,
        )
