"""
SQLAlchemy adapter for money market comparison logging.

Implements MoneyMarketComparisonGateway port for analytics tracking.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, desc, func, select

from app.domain.entities.money_market.rate_comparison import (
    MoneyMarketRateComparison,
)
from app.domain.ports.money_market.money_market_comparison_gateway import (
    MoneyMarketComparisonGateway,
)
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class MoneyMarketComparisonAdapterSqla(MoneyMarketComparisonGateway):
    """SQLAlchemy implementation of MoneyMarketComparisonGateway."""

    def __init__(self, session: MainAsyncSession):
        self._session = session
        self._table = mapping_registry.metadata.tables[
            "money_market_comparisons"
        ]

    # ═══════════════════════════════════════════════════════════════
    # COMPARISON CRUD
    # ═══════════════════════════════════════════════════════════════

    async def log_comparison(
        self,
        rate_comparison: MoneyMarketRateComparison,
    ) -> UUID:
        """Store comparison record for analytics."""
        values = {
            "id": rate_comparison.id,
            "user_id": rate_comparison.user_id,
            "comparison_type": "both",  # Default type
            "chain": rate_comparison.chain,
            "best_supply_protocol_id": None,  # Would need protocol_id lookup
            "best_supply_apy": rate_comparison.best_supply_apy,
            "best_borrow_protocol_id": None,  # Would need protocol_id lookup
            "best_borrow_apy": rate_comparison.best_borrow_apy,
            "protocols_compared": [
                rate_comparison.best_supply_protocol,
                rate_comparison.best_borrow_protocol,
            ],
            "assets_compared_count": 1,  # Single asset
            "full_results": rate_comparison.protocols_compared,
            "suggestions": None,
            "cache_hit_count": 0,  # Populated by handler
            "rpc_call_count": 0,  # Populated by handler
            "execution_time_ms": rate_comparison.latency_ms,
            "created_at": rate_comparison.created_at,
        }

        insert_stmt = self._table.insert().values(**values)
        await self._session.execute(insert_stmt)
        await self._session.commit()

        logger.info(
            f"Logged comparison for user {rate_comparison.user_id} "
            f"({rate_comparison.asset}/{rate_comparison.chain})"
        )
        return rate_comparison.id

    async def get_user_comparisons(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[MoneyMarketRateComparison]:
        """Get user's comparison history with pagination."""
        query = (
            select(self._table)
            .where(self._table.c.user_id == user_id)
            .order_by(desc(self._table.c.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        comparisons = [self._row_to_entity(row) for row in rows]
        logger.debug(
            f"Retrieved {len(comparisons)} comparisons for user {user_id}"
        )
        return comparisons

    async def get_comparison_by_id(
        self,
        comparison_id: UUID,
    ) -> MoneyMarketRateComparison | None:
        """Get specific comparison by ID."""
        query = select(self._table).where(self._table.c.id == comparison_id)

        result = await self._session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_entity(row)

    async def get_comparison_analytics(
        self,
        asset: str,
        chain: str,
        days: int = 7,
    ) -> dict:
        """Get analytics for asset/chain comparisons."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Base query for time period
        base_query = self._table.select().where(
            and_(
                self._table.c.chain == chain,
                self._table.c.created_at >= since,
            )
        )

        result = await self._session.execute(base_query)
        rows = result.fetchall()

        if not rows:
            return {
                "total_comparisons": 0,
                "unique_users": 0,
                "avg_latency_ms": 0,
                "most_compared_protocols": [],
                "best_supply_protocol": None,
                "best_borrow_protocol": None,
                "cache_hit_rate": 0.0,
            }

        # Calculate metrics
        total_comparisons = len(rows)
        unique_users = len(set(row.user_id for row in rows))
        avg_latency = sum(row.execution_time_ms for row in rows) / total_comparisons

        # Protocol counts
        protocol_counts = {}
        for row in rows:
            for protocol in row.protocols_compared:
                protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1

        # Cache hit rate
        total_cache_hits = sum(row.cache_hit_count for row in rows)
        total_rpc_calls = sum(row.rpc_call_count for row in rows)
        cache_hit_rate = (
            (total_cache_hits / (total_cache_hits + total_rpc_calls) * 100)
            if (total_cache_hits + total_rpc_calls) > 0
            else 0.0
        )

        return {
            "total_comparisons": total_comparisons,
            "unique_users": unique_users,
            "avg_latency_ms": int(avg_latency),
            "most_compared_protocols": sorted(
                protocol_counts.items(), key=lambda x: x[1], reverse=True
            ),
            "best_supply_protocol": None,  # Would need aggregation
            "best_borrow_protocol": None,  # Would need aggregation
            "cache_hit_rate": round(cache_hit_rate, 2),
        }

    async def get_popular_comparisons(
        self,
        days: int = 7,
        limit: int = 10,
    ) -> list[dict]:
        """Get most popular asset/chain combinations."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Aggregate by chain
        query = (
            select(
                self._table.c.chain,
                func.count(self._table.c.id).label("comparison_count"),
                func.avg(self._table.c.execution_time_ms).label(
                    "avg_latency_ms"
                ),
                func.count(func.distinct(self._table.c.user_id)).label(
                    "unique_users"
                ),
            )
            .where(self._table.c.created_at >= since)
            .group_by(self._table.c.chain)
            .order_by(desc("comparison_count"))
            .limit(limit)
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        return [
            {
                "asset": "USDC",  # Hardcoded for now
                "chain": row.chain,
                "comparison_count": row.comparison_count,
                "avg_latency_ms": int(row.avg_latency_ms),
                "unique_users": row.unique_users,
            }
            for row in rows
        ]

    async def get_user_comparison_count(
        self,
        user_id: UUID,
        since: datetime | None = None,
    ) -> int:
        """Get total comparison count for a user."""
        query = select(func.count()).select_from(self._table).where(
            self._table.c.user_id == user_id
        )

        if since:
            query = query.where(self._table.c.created_at >= since)

        result = await self._session.execute(query)
        return result.scalar()

    async def get_guest_comparison_count(
        self,
        guest_session_id: str,
        since: datetime | None = None,
    ) -> int:
        """Get total comparison count for a guest session."""
        # Guest session ID is not in money_market_comparisons table
        # This would need to join with guest_conversations or similar
        logger.warning(
            "Guest session tracking not implemented for money market comparisons"
        )
        return 0

    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _row_to_entity(self, row) -> MoneyMarketRateComparison:
        """Convert database row to domain entity."""
        # Extract asset from full_results if available
        asset = "USDC"  # Default
        if row.full_results and len(row.full_results) > 0:
            first_result = row.full_results[0]
            if isinstance(first_result, dict) and "asset" in first_result:
                asset = first_result["asset"]

        # Extract protocol names
        best_supply_protocol = (
            row.protocols_compared[0] if row.protocols_compared else "unknown"
        )
        best_borrow_protocol = (
            row.protocols_compared[1]
            if len(row.protocols_compared) > 1
            else best_supply_protocol
        )

        return MoneyMarketRateComparison(
            id=row.id,
            user_id=row.user_id,
            guest_session_id=None,  # Not in table
            asset=asset,
            chain=row.chain,
            protocols_compared=row.full_results or [],
            best_supply_protocol=best_supply_protocol,
            best_supply_apy=str(row.best_supply_apy or "0"),
            best_borrow_protocol=best_borrow_protocol,
            best_borrow_apy=str(row.best_borrow_apy or "0"),
            latency_ms=row.execution_time_ms or 0,
            language="en",  # Default
            created_at=row.created_at,
        )
