"""
SQLAlchemy adapter for money market rate caching.

Implements MoneyMarketCacheGateway port using PostgreSQL with 60s TTL.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.money_market.protocol_data import (
    MoneyMarketProtocolData,
)
from app.domain.ports.money_market.money_market_cache_gateway import (
    MoneyMarketCacheGateway,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class MoneyMarketCacheAdapterSqla(MoneyMarketCacheGateway):
    """SQLAlchemy implementation of MoneyMarketCacheGateway."""

    def __init__(self, session: AsyncSession):
        self._session = session
        # Get table reference from registry
        self._table = mapping_registry.metadata.tables["money_market_rates"]

    # ═══════════════════════════════════════════════════════════════
    # CACHE OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    async def get_cached_rate(
        self,
        protocol: str,
        asset: str,
        chain: str,
    ) -> MoneyMarketProtocolData | None:
        """Get cached rate if valid (within 60s TTL)."""
        now = datetime.now(timezone.utc)

        # Query for valid cache entry
        query = select(self._table).where(
            and_(
                self._table.c.protocol_id == protocol,
                self._table.c.asset_symbol == asset,
                self._table.c.chain == chain,
                self._table.c.valid_until > now,  # TTL check
            )
        ).order_by(self._table.c.created_at.desc())

        result = await self._session.execute(query)
        row = result.fetchone()

        if not row:
            logger.debug(
                f"Cache miss for {protocol}/{asset}/{chain}"
            )
            return None

        logger.debug(
            f"Cache hit for {protocol}/{asset}/{chain} "
            f"(expires in {(row.valid_until - now).total_seconds():.0f}s)"
        )
        return self._row_to_entity(row)

    async def cache_rate(
        self,
        protocol_data: MoneyMarketProtocolData,
    ) -> None:
        """Store rate with 60s TTL."""
        values = {
            "id": protocol_data.id,
            "protocol_id": protocol_data.protocol_id,
            "asset_symbol": protocol_data.asset,
            "asset_address": "0x0000000000000000000000000000000000000000",  # Placeholder
            "chain": protocol_data.chain,
            "supply_apy": protocol_data.supply_apy,
            "supply_apr": None,  # Optional
            "borrow_apy": protocol_data.borrow_apy_variable,
            "borrow_apr": None,  # Optional
            "variable_borrow_apy": protocol_data.borrow_apy_variable,
            "stable_borrow_apy": protocol_data.borrow_apy_stable,
            "total_supply_usd": protocol_data.total_supplied_usd,
            "total_borrow_usd": protocol_data.total_borrowed_usd,
            "utilization_rate": protocol_data.utilization_rate * Decimal("100"),  # Convert to percentage
            "liquidity_usd": protocol_data.liquidity_available,
            "reward_tokens": None,  # Optional
            "total_incentive_apy": Decimal("0"),
            "data_source": protocol_data.data_source,
            "created_at": protocol_data.created_at,
            "valid_until": protocol_data.valid_until,
            "last_updated_on_chain": None,  # Optional
            "metadata": None,  # Optional
        }

        insert_stmt = self._table.insert().values(**values)
        await self._session.execute(insert_stmt)
        await self._session.commit()

        logger.info(
            f"Cached rate for {protocol_data.protocol_id}/"
            f"{protocol_data.asset}/{protocol_data.chain} "
            f"(valid until {protocol_data.valid_until})"
        )

    async def invalidate_cache(
        self,
        protocol: str,
        asset: str,
        chain: str,
    ) -> None:
        """Manually invalidate cached rate."""
        now = datetime.now(timezone.utc)

        update_stmt = (
            self._table.update()
            .where(
                and_(
                    self._table.c.protocol_id == protocol,
                    self._table.c.asset_symbol == asset,
                    self._table.c.chain == chain,
                )
            )
            .values(valid_until=now)
        )

        result = await self._session.execute(update_stmt)
        await self._session.commit()

        if result.rowcount > 0:
            logger.info(
                f"Invalidated cache for {protocol}/{asset}/{chain} "
                f"({result.rowcount} entries)"
            )

    async def get_latest_rates(
        self,
        asset: str,
        chain: str,
    ) -> list[MoneyMarketProtocolData]:
        """Get latest valid rates from all protocols."""
        now = datetime.now(timezone.utc)

        query = (
            select(self._table)
            .where(
                and_(
                    self._table.c.asset_symbol == asset,
                    self._table.c.chain == chain,
                    self._table.c.valid_until > now,
                )
            )
            .order_by(self._table.c.created_at.desc())
        )

        result = await self._session.execute(query)
        rows = result.fetchall()

        rates = [self._row_to_entity(row) for row in rows]
        logger.debug(
            f"Found {len(rates)} valid cached rates for {asset}/{chain}"
        )
        return rates

    async def is_cache_valid(
        self,
        protocol: str,
        asset: str,
        chain: str,
    ) -> bool:
        """Check if cache exists and is valid."""
        now = datetime.now(timezone.utc)

        query = select(func.count()).select_from(self._table).where(
            and_(
                self._table.c.protocol_id == protocol,
                self._table.c.asset_symbol == asset,
                self._table.c.chain == chain,
                self._table.c.valid_until > now,
            )
        )

        result = await self._session.execute(query)
        count = result.scalar()
        return count > 0

    async def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics for monitoring."""
        now = datetime.now(timezone.utc)

        # Total entries
        total_query = select(func.count()).select_from(self._table)
        total_result = await self._session.execute(total_query)
        total_entries = total_result.scalar()

        # Valid entries
        valid_query = select(func.count()).select_from(self._table).where(
            self._table.c.valid_until > now
        )
        valid_result = await self._session.execute(valid_query)
        valid_entries = valid_result.scalar()

        # Unique protocols
        protocols_query = select(
            func.count(func.distinct(self._table.c.protocol_id))
        )
        protocols_result = await self._session.execute(protocols_query)
        protocols_cached = protocols_result.scalar()

        # Unique assets
        assets_query = select(
            func.count(func.distinct(self._table.c.asset_symbol))
        )
        assets_result = await self._session.execute(assets_query)
        assets_cached = assets_result.scalar()

        # Unique chains
        chains_query = select(
            func.count(func.distinct(self._table.c.chain))
        )
        chains_result = await self._session.execute(chains_query)
        chains_cached = chains_result.scalar()

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "protocols_cached": protocols_cached,
            "assets_cached": assets_cached,
            "chains_cached": chains_cached,
        }

    # ═══════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _row_to_entity(self, row) -> MoneyMarketProtocolData:
        """Convert database row to domain entity."""
        return MoneyMarketProtocolData(
            id=row.id,
            protocol_id=row.protocol_id,
            asset=row.asset_symbol,
            chain=row.chain,
            supply_apy=row.supply_apy,
            borrow_apy_variable=row.variable_borrow_apy or Decimal("0"),
            borrow_apy_stable=row.stable_borrow_apy,
            total_supplied_usd=row.total_supply_usd or Decimal("0"),
            total_borrowed_usd=row.total_borrow_usd or Decimal("0"),
            utilization_rate=row.utilization_rate / Decimal("100") if row.utilization_rate else Decimal("0"),  # Convert from percentage
            liquidity_available=row.liquidity_usd or Decimal("0"),
            data_source=row.data_source,
            valid_until=row.valid_until,
            created_at=row.created_at,
        )
