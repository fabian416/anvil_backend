"""
Swap intent watcher: check pending swap intents for 15 minutes and update tx history.

When the chat returns execute_data for a swap (e.g. hyperliquid_swap), we record a
swap_intent. This task runs every 2 minutes, fetches Hyperliquid userFillsByTime for
each wallet with pending intents, matches fills to intents by time and amount,
then updates the intent and inserts into the transactions table.
"""

import asyncio
import logging
from datetime import datetime, UTC, timedelta
from decimal import Decimal
from typing import Any

from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.helpers import _run_task

logger = logging.getLogger(__name__)


@celery_app.task(
    name="swap_intent.check_pending",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    acks_late=True,
)
def check_pending_swap_intents(self) -> dict[str, Any]:
    """
    Watch swap intents opened in the last 15 minutes; match Hyperliquid user fills
    and update tx history and swap_intents.
    """
    async def runner(container):
        from sqlalchemy import select, update, and_
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.domain.transactions.entities.transaction import Transaction, TransactionId
        from app.domain.entities.wallet import WalletId
        from app.domain.enums.chain_type import ChainType
        from app.domain.enums.transaction_status import TransactionStatus
        from app.domain.enums.transaction_type import TransactionType
        from app.domain.value_objects.user_id import UserId
        from app.domain.value_objects.created_at import CreatedAt
        from app.infrastructure.persistence_sqla.registry import mapping_registry
        from app.infrastructure.persistence_sqla.mappings.swap_intent_mapping import (
            map_swap_intents_table,
        )
        from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
        from app.infrastructure.persistence_sqla.mappings.transaction import (
            map_transaction_table,
        )
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.domain.transactions.ports.transaction.transaction_repository import (
            TransactionRepository,
        )

        try:
            from app.infrastructure.adapters.external.hyperliquid_client import (
                HyperliquidClient,
            )
            hyperliquid = await container.get(HyperliquidClient)
        except Exception:
            hyperliquid = None

        if hyperliquid is None:
            logger.debug("HyperliquidClient not available, skipping swap intent check.")
            return {"status": "skipped", "reason": "no_hyperliquid_client"}

        session: AsyncSession = await container.get(MainAsyncSession)
        map_swap_intents_table()
        map_wallet_tables()
        map_transaction_table()
        tx_repo: TransactionRepository = await container.get(TransactionRepository)

        swap_intents_table = mapping_registry.metadata.tables.get("swap_intents")
        wallets_table = mapping_registry.metadata.tables.get("wallets")
        if not swap_intents_table:
            return {"status": "skipped", "reason": "swap_intents_table_not_found"}

        window_start = datetime.now(UTC) - timedelta(minutes=15)
        stmt = (
            select(swap_intents_table)
            .where(
                and_(
                    swap_intents_table.c.status == "pending",
                    swap_intents_table.c.tx_hash.is_(None),
                    swap_intents_table.c.created_at >= window_start,
                )
            )
            .order_by(swap_intents_table.c.created_at.asc())
            .limit(100)
        )
        result = await session.execute(stmt)
        rows = result.fetchall()
        if not rows:
            return {"status": "complete", "processed": 0, "matched": 0, "errors": 0}

        # Group by wallet_address
        by_wallet: dict[str, list[Any]] = {}
        for row in rows:
            addr = row.wallet_address
            if addr not in by_wallet:
                by_wallet[addr] = []
            by_wallet[addr].append(row)

        matched = 0
        errors = 0
        now_ms = int(datetime.now(UTC).timestamp() * 1000)

        for wallet_address, intents in by_wallet.items():
            if not intents:
                continue
            min_created = min(r.created_at for r in intents)
            start_ms = int(min_created.timestamp() * 1000) - 60_000  # 1 min before

            try:
                fills = await hyperliquid.get_user_fills_by_time(
                    user_address=wallet_address,
                    start_time_ms=start_ms,
                    end_time_ms=now_ms,
                )
            except Exception as e:
                logger.warning("Hyperliquid userFillsByTime failed for %s: %s", wallet_address, e)
                errors += 1
                continue

            used_fill_hashes: set[str] = set()
            for intent_row in intents:
                if intent_row.tx_hash:
                    continue
                intent_amount = float(intent_row.amount)
                intent_created_ms = int(intent_row.created_at.timestamp() * 1000)
                wallet_id_val = intent_row.wallet_id
                if wallet_id_val is None and wallets_table:
                    w = await session.execute(
                        select(wallets_table.c.id).where(
                            wallets_table.c.address == wallet_address
                        ).limit(1)
                    )
                    wrow = w.scalar()
                    if wrow is not None:
                        wallet_id_val = wrow

                for fill in fills:
                    if not fill.hash or fill.hash in used_fill_hashes:
                        continue
                    if fill.time < intent_created_ms:
                        continue
                    # Match by size (2% tolerance)
                    try:
                        sz = float(fill.sz)
                    except (TypeError, ValueError):
                        continue
                    if intent_amount <= 0:
                        continue
                    if abs(sz - intent_amount) / intent_amount > 0.02:
                        continue
                    # Match: update intent and insert transaction
                    used_fill_hashes.add(fill.hash)
                    try:
                        await session.execute(
                            update(swap_intents_table)
                            .where(swap_intents_table.c.id == intent_row.id)
                            .values(
                                tx_hash=fill.hash,
                                status="completed",
                                updated_at=datetime.now(UTC),
                            )
                        )
                        if wallet_id_val is None:
                            continue
                        amount_out = None
                        try:
                            amount_out = Decimal(str(float(fill.px) * sz))
                        except (TypeError, ValueError):
                            pass
                        transaction = Transaction(
                            id_=TransactionId(0),
                            user_id=UserId(intent_row.user_id),
                            wallet_id=WalletId(wallet_id_val),
                            to_address=None,
                            type=TransactionType.SWAP,
                            chain=ChainType.HYPERLIQUID,
                            asset_in=intent_row.from_token,
                            amount_in=Decimal(str(intent_row.amount)),
                            asset_out=intent_row.to_token,
                            amount_out=amount_out,
                            fee=Decimal(fill.fee) if fill.fee else None,
                            fee_usd=None,
                            tx_hash=fill.hash,
                            status=TransactionStatus.SUCCESS,
                            dex_aggregator=intent_row.source or "hyperliquid_swap",
                            dex_route=None,
                            slippage=None,
                            error_message=None,
                            block_number=None,
                            confirmed_at=None,
                            created_at=CreatedAt.now(),
                            gas_used=None,
                            gas_price=None,
                            tx_metadata={"source": "swap_intent_watcher"},
                        )
                        await tx_repo.save(transaction)
                        matched += 1
                    except Exception as e:
                        logger.warning("Failed to update intent %s: %s", intent_row.id, e)
                        errors += 1
                    break

        await session.commit()
        return {
            "status": "complete",
            "processed": len(rows),
            "matched": matched,
            "errors": errors,
        }

    return asyncio.run(_run_task(runner))
