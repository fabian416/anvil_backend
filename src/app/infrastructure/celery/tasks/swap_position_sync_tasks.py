"""
Swap Position Sync — Background Celery task to cache Hyperliquid positions.

Runs every 60 seconds. For each wallet with recent activity:
  1. Fetches spot balances from Hyperliquid API
  2. Fetches perps positions from Hyperliquid API
  3. Upserts into `swap_positions` table
  4. Deletes stale rows (tokens no longer held)

This decouples user "my swaps" requests from Hyperliquid API rate limits.
Budget: 100 wallets × 2 API calls = 200 req/min (well within 1200 limit).
"""

import asyncio
import logging
from datetime import datetime, UTC, timedelta
from typing import Any

from app.infrastructure.celery.app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="swap_positions.sync",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    acks_late=True,
)
def sync_swap_positions(self) -> dict[str, Any]:
    """
    Sync Hyperliquid spot + perps positions for recently active users.

    Fetches from Hyperliquid API and upserts into swap_positions table.
    """

    async def runner(container):
        from sqlalchemy import select, delete, text as sa_text
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.adapters.external.hyperliquid_client import (
            HyperliquidClient,
        )

        session: AsyncSession = await container.get(MainAsyncSession)
        now = datetime.now(UTC)
        stats = {
            "wallets_processed": 0,
            "spot_upserted": 0,
            "perps_upserted": 0,
            "stale_deleted": 0,
            "errors": 0,
        }

        # ── 1. Get active wallets (users with auth_session in last 24h) ──
        try:
            result = await session.execute(
                sa_text("""
                    SELECT DISTINCT w.user_id, w.address
                    FROM wallets w
                    INNER JOIN auth_sessions s ON s.user_id = w.user_id
                    WHERE s.expiration >= :cutoff
                    AND w.address IS NOT NULL
                    ORDER BY w.user_id
                    LIMIT 200
                """),
                {"cutoff": now - timedelta(hours=24)},
            )
            wallets = [(row[0], row[1]) for row in result.all()]
        except Exception as e:
            logger.error("[SwapPositionSync] Failed to fetch wallets: %s", e)
            return stats

        if not wallets:
            logger.info("[SwapPositionSync] No active wallets to sync")
            return stats

        logger.info(
            "[SwapPositionSync] Syncing %d wallets", len(wallets)
        )

        # ── 2. Create Hyperliquid client ──
        hl_client = HyperliquidClient(testnet=False)

        try:
            for user_id, wallet_address in wallets:
                try:
                    await _sync_single_wallet(
                        session, hl_client, user_id, wallet_address, now, stats
                    )
                    stats["wallets_processed"] += 1
                except Exception as e:
                    logger.warning(
                        "[SwapPositionSync] Error syncing wallet %s: %s",
                        wallet_address[:10],
                        e,
                    )
                    stats["errors"] += 1
                    # Rollback the failed transaction to continue with next wallet
                    await session.rollback()

            # ── 3. Delete stale positions (not updated in this sync cycle) ──
            try:
                stale_cutoff = now - timedelta(minutes=5)
                del_result = await session.execute(
                    sa_text("""
                        DELETE FROM swap_positions
                        WHERE synced_at < :cutoff
                    """),
                    {"cutoff": stale_cutoff},
                )
                stats["stale_deleted"] = del_result.rowcount or 0
                await session.commit()
            except Exception as e:
                logger.warning(
                    "[SwapPositionSync] Failed to clean stale rows: %s", e
                )
                await session.rollback()

        finally:
            await hl_client.close()

        logger.info(
            "[SwapPositionSync] Done: %d wallets, %d spot, %d perps, %d stale deleted, %d errors",
            stats["wallets_processed"],
            stats["spot_upserted"],
            stats["perps_upserted"],
            stats["stale_deleted"],
            stats["errors"],
        )
        return stats

    return asyncio.run(
        _run_with_container(runner)
    )


@celery_app.task(
    name="swap_positions.sync_wallet",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def sync_swap_positions_for_wallet(
    self, user_id: int, wallet_address: str
) -> dict[str, Any]:
    """
    On-demand sync for a single wallet (triggered by "refresh" or login).
    """

    async def runner(container):
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.adapters.external.hyperliquid_client import (
            HyperliquidClient,
        )

        session: AsyncSession = await container.get(MainAsyncSession)
        now = datetime.now(UTC)
        stats = {
            "wallets_processed": 0,
            "spot_upserted": 0,
            "perps_upserted": 0,
            "errors": 0,
        }

        hl_client = HyperliquidClient(testnet=False)
        try:
            await _sync_single_wallet(
                session, hl_client, user_id, wallet_address, now, stats
            )
            stats["wallets_processed"] = 1
        except Exception as e:
            logger.warning(
                "[SwapPositionSync] On-demand sync error for %s: %s",
                wallet_address[:10],
                e,
            )
            stats["errors"] = 1
            await session.rollback()
        finally:
            await hl_client.close()

        return stats

    return asyncio.run(
        _run_with_container(runner)
    )


async def _sync_single_wallet(
    session,
    hl_client,
    user_id: int,
    wallet_address: str,
    now: datetime,
    stats: dict,
) -> None:
    """Sync spot + perps positions for a single wallet."""
    from sqlalchemy import text as sa_text
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    # ── Spot balances ──
    try:
        spot_balances = await hl_client.get_spot_balance(wallet_address)
    except Exception as e:
        logger.debug("[SwapPositionSync] No spot data for %s: %s", wallet_address[:10], e)
        spot_balances = {}

    for token, balance in spot_balances.items():
        if balance <= 0:
            continue

        # Get USD value for non-stablecoins
        usd_value = 0.0
        if token.upper() in ("USDC", "USDT"):
            usd_value = balance
        else:
            try:
                price = await hl_client.get_spot_price(token, "USDC")
                usd_value = balance * price
            except Exception:
                pass

        stmt = pg_insert(
            _get_swap_positions_table(session)
        ).values(
            user_id=user_id,
            wallet_address=wallet_address.lower(),
            source="spot",
            token=token,
            balance=balance,
            usd_value=round(usd_value, 2),
            side="hold",
            entry_price=None,
            mark_price=None,
            unrealized_pnl=None,
            leverage=None,
            liquidation_price=None,
            synced_at=now,
        ).on_conflict_do_update(
            constraint="uq_swap_positions_wallet_source_token",
            set_={
                "user_id": user_id,
                "balance": balance,
                "usd_value": round(usd_value, 2),
                "synced_at": now,
            },
        )
        await session.execute(stmt)
        stats["spot_upserted"] += 1

    # ── Perps positions ──
    try:
        perps_positions = await hl_client.get_user_positions(wallet_address)
    except Exception as e:
        logger.debug("[SwapPositionSync] No perps data for %s: %s", wallet_address[:10], e)
        perps_positions = []

    for pos in perps_positions:
        usd_value = pos.size * pos.mark_price if pos.mark_price else 0

        stmt = pg_insert(
            _get_swap_positions_table(session)
        ).values(
            user_id=user_id,
            wallet_address=wallet_address.lower(),
            source="perps",
            token=pos.symbol,
            balance=pos.size,
            usd_value=round(usd_value, 2),
            side=pos.side,
            entry_price=pos.entry_price,
            mark_price=pos.mark_price,
            unrealized_pnl=pos.unrealized_pnl,
            leverage=pos.leverage,
            liquidation_price=pos.liquidation_price,
            synced_at=now,
        ).on_conflict_do_update(
            constraint="uq_swap_positions_wallet_source_token",
            set_={
                "user_id": user_id,
                "balance": pos.size,
                "usd_value": round(usd_value, 2),
                "side": pos.side,
                "entry_price": pos.entry_price,
                "mark_price": pos.mark_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "leverage": pos.leverage,
                "liquidation_price": pos.liquidation_price,
                "synced_at": now,
            },
        )
        await session.execute(stmt)
        stats["perps_upserted"] += 1

    await session.commit()


def _get_swap_positions_table(session):
    """Get the swap_positions Table object from metadata."""
    from app.infrastructure.persistence_sqla.registry import mapping_registry

    # Ensure mapping is loaded
    from app.infrastructure.persistence_sqla.mappings.swap_position_mapping import (
        map_swap_positions_table,
    )
    map_swap_positions_table()

    return mapping_registry.metadata.tables["swap_positions"]


async def _run_with_container(coro_factory):
    """Run async task with Dishka IOC container."""
    from app.infrastructure.celery.helpers import _run_task

    return await _run_task(coro_factory)
