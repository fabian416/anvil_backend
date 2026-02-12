"""
Recent-user incremental sync: for users active in the last 24h, run tx sync with backoff.

Backoff: 1 min -> 3 min -> 6 min -> 12 min (then cap at 12 min).
Seeds from auth_sessions (expiration >= now() - 24h). Runs every minute.
"""

import asyncio
import logging
from datetime import datetime, UTC, timedelta
from typing import Any

from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.helpers import _run_task

logger = logging.getLogger(__name__)

# Backoff intervals (minutes): 1 -> 3 -> 6 -> 12, then cap at 12
RECENT_USER_SYNC_INTERVALS_MIN = (1, 3, 6, 12)
MAX_INTERVAL_INDEX = len(RECENT_USER_SYNC_INTERVALS_MIN) - 1


@celery_app.task(
    name="recent_user_sync.incremental",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    acks_late=True,
)
def recent_users_incremental_sync(self) -> dict[str, Any]:
    """
    Sync transaction status for users active in the last 24h with incremental backoff.
    Each user is synced at 1 min, then 3, 6, 12 min to reduce API calls.
    """
    async def runner(container):
        from sqlalchemy import select, update, and_, insert
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.infrastructure.persistence_sqla.registry import mapping_registry
        from app.infrastructure.persistence_sqla.mappings.auth_session import (
            map_auth_sessions_table,
        )
        from app.infrastructure.persistence_sqla.mappings.user_sync_schedule_mapping import (
            map_user_sync_schedule_table,
        )
        from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
        from app.infrastructure.persistence_sqla.mappings.transaction import (
            map_transaction_table,
        )
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.celery.tasks.etherscan_balance_tasks import (
            EtherscanClient,
        )
        from app.setup.config.settings import load_settings

        settings = load_settings()
        etherscan_api_key = ""
        etherscan_base_url = "https://api.etherscan.io/v2/api"
        include_paid_tier_chains = False
        try:
            raw = getattr(settings, "model_dump", lambda: {})() or {}
            etherscan_cfg = raw.get("etherscan", {})
            if isinstance(etherscan_cfg, dict):
                etherscan_api_key = etherscan_cfg.get("api_key", "")
                etherscan_base_url = etherscan_cfg.get("base_url", etherscan_base_url)
                include_paid_tier_chains = etherscan_cfg.get(
                    "include_paid_tier_chains", False
                )
        except Exception:
            pass
        if not etherscan_api_key:
            try:
                from app.setup.config.loader import load_full_config, get_current_env
                raw = load_full_config(env=get_current_env())
                etherscan_cfg = raw.get("etherscan", {})
                etherscan_api_key = etherscan_cfg.get("api_key", "") or etherscan_cfg.get("API_KEY", "")
                include_paid_tier_chains = etherscan_cfg.get(
                    "include_paid_tier_chains", include_paid_tier_chains
                )
            except Exception:
                pass
        if not etherscan_api_key:
            return {"status": "skipped", "reason": "no_etherscan_api_key"}

        chain_id_map = {
            "ethereum": 1,
            "arbitrum": 42161,
            "polygon": 137,
        }
        if include_paid_tier_chains:
            chain_id_map["base"] = 8453
            chain_id_map["optimism"] = 10

        session: AsyncSession = await container.get(MainAsyncSession)
        map_auth_sessions_table()
        map_user_sync_schedule_table()
        map_wallet_tables()
        map_transaction_table()

        schedule_table = mapping_registry.metadata.tables.get("user_sync_schedule")
        auth_sessions = mapping_registry.metadata.tables.get("auth_sessions")
        wallets_table = mapping_registry.metadata.tables.get("wallets")
        transactions_table = mapping_registry.metadata.tables.get("transactions")
        if (
            schedule_table is None
            or auth_sessions is None
            or wallets_table is None
            or transactions_table is None
        ):
            return {"status": "skipped", "reason": "tables_not_found"}

        # Seed: users with session expiration in last 24h (i.e. active in last 24h)
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        seed_stmt = select(auth_sessions.c.user_id).where(
            auth_sessions.c.expiration >= cutoff
        ).distinct()
        seed_result = await session.execute(seed_stmt)
        active_user_ids = [r[0] for r in seed_result.fetchall()]
        if active_user_ids:
            now_utc = datetime.now(UTC)
            for uid in active_user_ids:
                await session.execute(
                    insert(schedule_table).values(
                        user_id=uid,
                        next_sync_at=now_utc,
                        interval_index=0,
                        last_synced_at=None,
                        created_at=now_utc,
                        updated_at=now_utc,
                    ).on_conflict_do_nothing(index_elements=["user_id"])
                )
            await session.commit()

        # Get due users (next_sync_at <= now)
        now_utc = datetime.now(UTC)
        due_stmt = (
            select(schedule_table)
            .where(schedule_table.c.next_sync_at <= now_utc)
            .order_by(schedule_table.c.next_sync_at.asc())
            .limit(30)
        )
        due_result = await session.execute(due_stmt)
        due_rows = due_result.fetchall()
        if not due_rows:
            return {"status": "complete", "users_synced": 0, "wallets_processed": 0}

        processed_wallets = 0
        updated_txs = 0
        errors = 0

        async with EtherscanClient(
            api_key=etherscan_api_key,
            base_url=etherscan_base_url,
            max_retries=2,
            retry_backoff_base=2.0,
        ) as client:
            for row in due_rows:
                user_id_val = row.user_id
                interval_index = min(row.interval_index or 0, MAX_INTERVAL_INDEX)
                # Get this user's wallets
                w_stmt = select(
                    wallets_table.c.id,
                    wallets_table.c.address,
                ).where(
                    and_(
                        wallets_table.c.user_id == user_id_val,
                        wallets_table.c.status == 1,
                        wallets_table.c.address.isnot(None),
                    )
                )
                w_result = await session.execute(w_stmt)
                wallets = w_result.fetchall()
                for wallet_id, wallet_address in wallets:
                    for _chain_name, chain_id in chain_id_map.items():
                        try:
                            tx_list = await client.get_txlist(
                                address=wallet_address,
                                chain_id=chain_id,
                                offset=30,
                            )
                            for tx in tx_list:
                                tx_hash = tx.get("hash")
                                if not tx_hash:
                                    continue
                                block_num = tx.get("blockNumber")
                                if not block_num:
                                    continue
                                is_error = tx.get("isError", "0") == "1"
                                status_new = 2 if is_error else 1
                                ts = tx.get("timeStamp")
                                confirmed_at = (
                                    datetime.fromtimestamp(int(ts), tz=UTC) if ts else None
                                )
                                gas_used_raw = tx.get("gasUsed")
                                gas_used = int(gas_used_raw) if gas_used_raw else None
                                update_stmt = (
                                    update(transactions_table)
                                    .where(
                                        and_(
                                            transactions_table.c.wallet_id == wallet_id,
                                            transactions_table.c.tx_hash == tx_hash,
                                            transactions_table.c.status == 0,
                                        )
                                    )
                                    .values(
                                        status=status_new,
                                        block_number=int(block_num),
                                        confirmed_at=confirmed_at,
                                        gas_used=gas_used,
                                    )
                                )
                                res = await session.execute(update_stmt)
                                if res.rowcount and res.rowcount > 0:
                                    updated_txs += 1
                            processed_wallets += 1
                        except Exception as e:
                            errors += 1
                            logger.debug(
                                "Etherscan txlist failed for wallet %s chain %s: %s",
                                wallet_id,
                                chain_id,
                                e,
                            )

                # Advance schedule for this user
                interval_min = RECENT_USER_SYNC_INTERVALS_MIN[interval_index]
                next_sync = now_utc + timedelta(minutes=interval_min)
                new_index = min(interval_index + 1, MAX_INTERVAL_INDEX)
                await session.execute(
                    update(schedule_table)
                    .where(schedule_table.c.user_id == user_id_val)
                    .values(
                        next_sync_at=next_sync,
                        interval_index=new_index,
                        last_synced_at=now_utc,
                        updated_at=now_utc,
                    )
                )

        await session.commit()
        return {
            "status": "complete",
            "users_synced": len(due_rows),
            "wallets_processed": processed_wallets,
            "transactions_updated": updated_txs,
            "errors": errors,
        }

    return asyncio.run(_run_task(runner))


@celery_app.task(
    name="recent_user_sync.sync_user",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    acks_late=True,
)
def sync_single_user(self, user_id: int) -> dict[str, Any]:
    """
    Sync transaction status for one user now (Etherscan txlist update)
    and upsert user_sync_schedule so they stay in the incremental rotation.
    """
    async def runner(container):
        from sqlalchemy import select, update, and_
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.infrastructure.persistence_sqla.registry import mapping_registry
        from app.infrastructure.persistence_sqla.mappings.user_sync_schedule_mapping import (
            map_user_sync_schedule_table,
        )
        from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
        from app.infrastructure.persistence_sqla.mappings.transaction import (
            map_transaction_table,
        )
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.infrastructure.celery.tasks.etherscan_balance_tasks import (
            EtherscanClient,
        )
        from app.setup.config.settings import load_settings

        settings = load_settings()
        etherscan_api_key = ""
        etherscan_base_url = "https://api.etherscan.io/v2/api"
        include_paid_tier_chains = False
        try:
            raw = getattr(settings, "model_dump", lambda: {})() or {}
            etherscan_cfg = raw.get("etherscan", {})
            if isinstance(etherscan_cfg, dict):
                etherscan_api_key = etherscan_cfg.get("api_key", "")
                etherscan_base_url = etherscan_cfg.get("base_url", etherscan_base_url)
                include_paid_tier_chains = etherscan_cfg.get(
                    "include_paid_tier_chains", False
                )
        except Exception:
            pass
        if not etherscan_api_key:
            try:
                from app.setup.config.loader import load_full_config, get_current_env
                raw = load_full_config(env=get_current_env())
                etherscan_cfg = raw.get("etherscan", {})
                etherscan_api_key = etherscan_cfg.get("api_key", "") or etherscan_cfg.get("API_KEY", "")
                include_paid_tier_chains = etherscan_cfg.get(
                    "include_paid_tier_chains", include_paid_tier_chains
                )
            except Exception:
                pass
        if not etherscan_api_key:
            return {"status": "skipped", "reason": "no_etherscan_api_key", "user_id": user_id}

        chain_id_map = {
            "ethereum": 1,
            "arbitrum": 42161,
            "polygon": 137,
        }
        if include_paid_tier_chains:
            chain_id_map["base"] = 8453
            chain_id_map["optimism"] = 10

        session: AsyncSession = await container.get(MainAsyncSession)
        map_user_sync_schedule_table()
        map_wallet_tables()
        map_transaction_table()

        schedule_table = mapping_registry.metadata.tables.get("user_sync_schedule")
        wallets_table = mapping_registry.metadata.tables.get("wallets")
        transactions_table = mapping_registry.metadata.tables.get("transactions")
        if (
            schedule_table is None
            or wallets_table is None
            or transactions_table is None
        ):
            return {"status": "skipped", "reason": "tables_not_found", "user_id": user_id}

        w_stmt = select(
            wallets_table.c.id,
            wallets_table.c.address,
        ).where(
            and_(
                wallets_table.c.user_id == user_id,
                wallets_table.c.status == 1,
                wallets_table.c.address.isnot(None),
            )
        )
        w_result = await session.execute(w_stmt)
        wallets = w_result.fetchall()
        if not wallets:
            now_utc = datetime.now(UTC)
            await session.execute(
                pg_insert(schedule_table)
                .values(
                    user_id=user_id,
                    next_sync_at=now_utc + timedelta(minutes=RECENT_USER_SYNC_INTERVALS_MIN[0]),
                    interval_index=0,
                    last_synced_at=None,
                    created_at=now_utc,
                    updated_at=now_utc,
                )
                .on_conflict_do_update(
                    index_elements=["user_id"],
                    set_={
                        "next_sync_at": now_utc + timedelta(minutes=RECENT_USER_SYNC_INTERVALS_MIN[0]),
                        "interval_index": 0,
                        "updated_at": now_utc,
                    },
                )
            )
            await session.commit()
            return {"status": "complete", "user_id": user_id, "wallets_processed": 0, "transactions_updated": 0}

        processed_wallets = 0
        updated_txs = 0
        errors = 0
        now_utc = datetime.now(UTC)

        async with EtherscanClient(
            api_key=etherscan_api_key,
            base_url=etherscan_base_url,
            max_retries=2,
            retry_backoff_base=2.0,
        ) as client:
            for wallet_id, wallet_address in wallets:
                for _chain_name, chain_id in chain_id_map.items():
                    try:
                        tx_list = await client.get_txlist(
                            address=wallet_address,
                            chain_id=chain_id,
                            offset=30,
                        )
                        for tx in tx_list:
                            tx_hash = tx.get("hash")
                            if not tx_hash:
                                continue
                            block_num = tx.get("blockNumber")
                            if not block_num:
                                continue
                            is_error = tx.get("isError", "0") == "1"
                            status_new = 2 if is_error else 1
                            ts = tx.get("timeStamp")
                            confirmed_at = (
                                datetime.fromtimestamp(int(ts), tz=UTC) if ts else None
                            )
                            gas_used_raw = tx.get("gasUsed")
                            gas_used = int(gas_used_raw) if gas_used_raw else None
                            update_stmt = (
                                update(transactions_table)
                                .where(
                                    and_(
                                        transactions_table.c.wallet_id == wallet_id,
                                        transactions_table.c.tx_hash == tx_hash,
                                        transactions_table.c.status == 0,
                                    )
                                )
                                .values(
                                    status=status_new,
                                    block_number=int(block_num),
                                    confirmed_at=confirmed_at,
                                    gas_used=gas_used,
                                )
                            )
                            res = await session.execute(update_stmt)
                            if res.rowcount and res.rowcount > 0:
                                updated_txs += 1
                        processed_wallets += 1
                    except Exception as e:
                        errors += 1
                        logger.debug(
                            "Etherscan txlist failed for wallet %s chain %s: %s",
                            wallet_id,
                            chain_id,
                            e,
                        )

        await session.commit()

        # Backfill Hyperliquid swaps (userFillsByTime) so "My swaps" shows HL history
        hyperliquid_inserted = 0
        try:
            from app.infrastructure.adapters.external.hyperliquid_client import (
                HyperliquidClient,
            )
            hyperliquid = await container.get(HyperliquidClient)
        except Exception:
            hyperliquid = None
        if hyperliquid is None:
            try:
                hyperliquid = HyperliquidClient(testnet=False)
            except Exception:
                hyperliquid = None
        if hyperliquid is not None:
            try:
                from app.domain.enums.chain_type import ChainType

                start_ms = int((now_utc - timedelta(days=90)).timestamp() * 1000)
                end_ms = int(now_utc.timestamp() * 1000)
                chain_hl = ChainType.HYPERLIQUID.value
                hl_failed = False
                for wallet_id, wallet_address in wallets:
                    if hl_failed:
                        break
                    try:
                        fills = await hyperliquid.get_user_fills_by_time(
                            user_address=wallet_address,
                            start_time_ms=start_ms,
                            end_time_ms=end_ms,
                        )
                    except Exception as e:
                        logger.debug(
                            "Hyperliquid userFillsByTime failed for wallet %s: %s",
                            wallet_address,
                            e,
                        )
                        continue
                    for fill in fills:
                        if not fill.hash or not isinstance(fill.hash, str):
                            continue
                        tx_hash_str = str(fill.hash).strip()[:66]
                        if not tx_hash_str:
                            continue
                        try:
                            amount_out = float(fill.px) * float(fill.sz) if fill.px and fill.sz else None
                            fee_val = float(fill.fee) if fill.fee else None
                            confirmed_at = (
                                datetime.fromtimestamp(fill.time / 1000.0, tz=UTC)
                                if fill.time
                                else None
                            )
                            stmt = pg_insert(transactions_table).values(
                                user_id=user_id,
                                wallet_id=wallet_id,
                                tx_hash=tx_hash_str,
                                chain=chain_hl,
                                type=0,  # SWAP
                                status=1,  # SUCCESS
                                asset_in=(fill.coin or None) if isinstance(fill.coin, str) else None,
                                amount_in=float(fill.sz) if fill.sz is not None else None,
                                asset_out=None,
                                amount_out=amount_out,
                                fee=fee_val,
                                dex_aggregator="hyperliquid",
                                confirmed_at=confirmed_at,
                                tx_metadata={"source": "hyperliquid_backfill"},
                            )
                            await session.execute(stmt)
                            await session.commit()
                            hyperliquid_inserted += 1
                        except Exception as e:
                            from sqlalchemy.exc import IntegrityError
                            if isinstance(e, IntegrityError):
                                try:
                                    await session.rollback()
                                except Exception:
                                    pass
                                continue  # duplicate, skip
                            logger.warning(
                                "Hyperliquid fill insert failed for %s: %s",
                                tx_hash_str,
                                e,
                            )
                            try:
                                await session.rollback()
                            except Exception:
                                pass
                            hl_failed = True
                            break
                    if hl_failed:
                        break
            except Exception as e:
                logger.warning("Hyperliquid backfill failed: %s", e)
                try:
                    await session.rollback()
                except Exception:
                    pass

        # Upsert schedule so user stays in rotation (next sync in 1 min, then backoff)
        interval_index = 0
        interval_min = RECENT_USER_SYNC_INTERVALS_MIN[interval_index]
        next_sync = now_utc + timedelta(minutes=interval_min)
        await session.execute(
            pg_insert(schedule_table)
            .values(
                user_id=user_id,
                next_sync_at=next_sync,
                interval_index=interval_index,
                last_synced_at=now_utc,
                created_at=now_utc,
                updated_at=now_utc,
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "next_sync_at": next_sync,
                    "interval_index": interval_index,
                    "last_synced_at": now_utc,
                    "updated_at": now_utc,
                },
            )
        )
        await session.commit()
        return {
            "status": "complete",
            "user_id": user_id,
            "wallets_processed": processed_wallets,
            "transactions_updated": updated_txs,
            "hyperliquid_inserted": hyperliquid_inserted,
            "errors": errors,
        }

    return asyncio.run(_run_task(runner))
