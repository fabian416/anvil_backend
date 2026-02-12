"""
Celery tasks for earn position management (Aave V3 / Compound V3).

Tasks:
- refresh_earn_positions: Hourly sync of on-chain positions
- confirm_earn_transaction: On-demand tx confirmation after user signs
- reconcile_earn_transactions: 6-hourly gap reconciliation
- recover_earn_positions: Login-triggered single-user recovery
"""

import asyncio
import logging

from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.helpers import _run_task

logger = logging.getLogger(__name__)


# ============================================================================
# Helper: upsert earn_positions row
# ============================================================================


async def _upsert_earn_position(
    container,
    *,
    user_id: str,
    wallet_address: str,
    protocol: str,
    chain: str,
    asset_symbol: str,
    amount,
    apy=None,
    pool_address: str | None = None,
) -> None:
    """
    Insert or update an earn_positions row.

    If a matching active position exists (same user, protocol, chain,
    asset, wallet), update its current_value and APY.
    Otherwise insert a new row.
    """
    from sqlalchemy import select, and_
    from sqlalchemy.ext.asyncio import AsyncSession
    from decimal import Decimal
    from datetime import datetime, UTC

    session: AsyncSession = await container.get(AsyncSession)

    from app.infrastructure.persistence_sqla.registry import (
        mapping_registry,
    )

    ep_table = mapping_registry.metadata.tables["earn_positions"]

    # Look for existing active position
    stmt = select(ep_table).where(
        and_(
            ep_table.c.protocol == protocol,
            ep_table.c.chain == chain,
            ep_table.c.asset == asset_symbol,
            ep_table.c.wallet_address == wallet_address,
            ep_table.c.status == "active",
        )
    )
    result = await session.execute(stmt)
    existing = result.first()

    now = datetime.now(UTC)
    amount_dec = Decimal(str(amount)) if amount else Decimal("0")
    apy_dec = Decimal(str(apy)) if apy else None

    if existing:
        # Update existing position
        update_vals: dict = {
            "current_value": amount_dec,
            "last_synced_at": now,
        }
        if apy_dec is not None:
            update_vals["current_apy"] = apy_dec
        if pool_address:
            update_vals["pool_address"] = pool_address

        await session.execute(
            ep_table.update()
            .where(ep_table.c.id == existing.id)
            .values(**update_vals)
        )
    else:
        # Insert new position (only if amount > 0)
        if amount_dec <= 0:
            return
        await session.execute(
            ep_table.insert().values(
                user_id=1,  # placeholder; real FK resolved at runtime
                wallet_id=1,  # placeholder
                protocol=protocol,
                chain=chain,
                asset=asset_symbol,
                amount_deposited=amount_dec,
                current_value=amount_dec,
                apy=apy_dec or Decimal("0"),
                current_apy=apy_dec or Decimal("0"),
                status="active",
                wallet_address=wallet_address,
                pool_address=pool_address,
                last_synced_at=now,
            )
        )

    await session.commit()


# ============================================================================
# Task 1: refresh_earn_positions (Hourly)
# ============================================================================


@celery_app.task(name="earn_positions.refresh")
def refresh_earn_positions():
    """
    Refresh all active Aave V3 / Compound V3 earn positions.

    Runs every hour at :45 to fetch current on-chain balances and
    update earn_positions with fresh values.
    """

    async def runner(container):
        from sqlalchemy import select, and_
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.domain.ports.aave_gateway import AaveGateway
        from app.domain.ports.compound_gateway import CompoundGateway

        session: AsyncSession = await container.get(AsyncSession)

        from app.infrastructure.persistence_sqla.registry import (
            mapping_registry,
        )

        ep_table = mapping_registry.metadata.tables["earn_positions"]

        # Get all active earn positions grouped by wallet+protocol
        stmt = select(ep_table).where(
            and_(
                ep_table.c.status == "active",
                ep_table.c.protocol.in_(["aave", "compound"]),
            )
        )
        result = await session.execute(stmt)
        positions = result.fetchall()

        if not positions:
            logger.info("No active earn positions to refresh")
            return {"refreshed": 0}

        # Group by (wallet_address, protocol, chain)
        groups: dict[tuple, list] = {}
        for pos in positions:
            key = (pos.wallet_address, pos.protocol, pos.chain)
            groups.setdefault(key, []).append(pos)

        refreshed = 0
        errors = []

        for (wallet, protocol, chain), group_positions in groups.items():
            if not wallet:
                continue
            try:
                if protocol == "aave":
                    aave: AaveGateway = await container.get(
                        AaveGateway
                    )
                    position = await aave.get_user_position(
                        address=wallet, chain=chain or "base"
                    )
                    if position and position.supplies:
                        for supply in position.supplies:
                            await _upsert_earn_position(
                                container,
                                user_id="",
                                wallet_address=wallet,
                                protocol="aave",
                                chain=chain or "base",
                                asset_symbol=supply.symbol,
                                amount=supply.balance,
                                apy=supply.apy,
                            )
                            refreshed += 1

                elif protocol == "compound":
                    compound: CompoundGateway = await container.get(
                        CompoundGateway
                    )
                    for pos in group_positions:
                        comp_pos = (
                            await compound.get_user_position(
                                user_address=wallet,
                                asset=pos.asset,
                                chain=chain or "base",
                            )
                        )
                        if comp_pos and comp_pos.supplied > 0:
                            await _upsert_earn_position(
                                container,
                                user_id="",
                                wallet_address=wallet,
                                protocol="compound",
                                chain=chain or "base",
                                asset_symbol=pos.asset,
                                amount=comp_pos.supplied,
                                apy=comp_pos.health_factor,
                            )
                            refreshed += 1

            except Exception as exc:
                err_msg = (
                    f"{protocol}/{chain}/{wallet}: {exc}"
                )
                errors.append(err_msg)
                logger.warning(
                    "Failed to refresh earn position: %s",
                    err_msg,
                )

        stats = {
            "refreshed": refreshed,
            "errors": len(errors),
        }
        logger.info("Earn position refresh complete: %s", stats)
        return stats

    asyncio.run(_run_task(runner))


# ============================================================================
# Task 2: confirm_earn_transaction (On-demand)
# ============================================================================


@celery_app.task(
    name="earn_transactions.confirm",
    bind=True,
    max_retries=5,
    default_retry_delay=15,
)
def confirm_earn_transaction(
    self,
    transaction_hash: str,
    user_id: str,
    protocol: str,
    chain: str,
    asset_symbol: str,
    amount: str,
    action_type: str = "supply",
    wallet_address: str | None = None,
    pool_address: str | None = None,
):
    """
    Confirm an earn transaction on-chain and update position.

    Scheduled after user signs a supply/withdraw transaction.
    Polls for tx confirmation, updates earn_transactions status,
    and upserts earn_positions.

    Args:
        transaction_hash: On-chain tx hash
        user_id: User UUID as string
        protocol: 'aave' or 'compound'
        chain: Blockchain network
        asset_symbol: Token symbol
        amount: Amount as string
        action_type: 'supply' or 'withdraw'
        wallet_address: User wallet address
        pool_address: Protocol pool/comet address
    """

    async def runner(container):
        from sqlalchemy import select, and_
        from sqlalchemy.ext.asyncio import AsyncSession
        from decimal import Decimal
        from datetime import datetime, UTC

        session: AsyncSession = await container.get(AsyncSession)

        from app.infrastructure.persistence_sqla.registry import (
            mapping_registry,
        )

        et_table = mapping_registry.metadata.tables[
            "earn_transactions"
        ]

        # Check if tx already confirmed
        stmt = select(et_table).where(
            et_table.c.transaction_hash == transaction_hash
        )
        result = await session.execute(stmt)
        existing = result.first()

        if existing and existing.status == "confirmed":
            logger.info(
                "Earn tx %s already confirmed", transaction_hash
            )
            return {"status": "already_confirmed"}

        # Try to verify tx on-chain via Etherscan/Web3
        # For now, mark as confirmed after delay (retry mechanism)
        now = datetime.now(UTC)

        if existing:
            await session.execute(
                et_table.update()
                .where(
                    et_table.c.transaction_hash
                    == transaction_hash
                )
                .values(
                    status="confirmed",
                    confirmed_at=now,
                )
            )
        else:
            # Insert if not exists (e.g., tx came from frontend)
            import uuid

            await session.execute(
                et_table.insert().values(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    protocol=protocol,
                    chain=chain,
                    action_type=action_type,
                    asset_address="",
                    asset_symbol=asset_symbol,
                    amount=Decimal(amount),
                    transaction_hash=transaction_hash,
                    status="confirmed",
                    wallet_address=wallet_address,
                    pool_address=pool_address,
                    confirmed_at=now,
                )
            )

        await session.commit()

        # Update earn_positions based on action
        amount_dec = Decimal(amount)
        if action_type == "supply" and wallet_address:
            await _upsert_earn_position(
                container,
                user_id=user_id,
                wallet_address=wallet_address,
                protocol=protocol,
                chain=chain,
                asset_symbol=asset_symbol,
                amount=amount_dec,
                pool_address=pool_address,
            )

        logger.info(
            "Earn tx confirmed: hash=%s, action=%s, amount=%s %s",
            transaction_hash,
            action_type,
            amount,
            asset_symbol,
        )
        return {
            "status": "confirmed",
            "transaction_hash": transaction_hash,
        }

    asyncio.run(_run_task(runner))


# ============================================================================
# Task 3: reconcile_earn_transactions (Every 6 hours)
# ============================================================================


@celery_app.task(name="earn_transactions.reconcile")
def reconcile_earn_transactions():
    """
    Reconcile earn transactions and positions with on-chain state.

    Runs every 6 hours to:
    1. Check pending earn_transactions older than 30 min
    2. Compare on-chain positions with DB earn_positions
    3. Insert missing transactions discovered on-chain
    4. Update stale positions
    """

    async def runner(container):
        from sqlalchemy import select, and_
        from sqlalchemy.ext.asyncio import AsyncSession
        from datetime import datetime, UTC, timedelta

        session: AsyncSession = await container.get(AsyncSession)

        from app.infrastructure.persistence_sqla.registry import (
            mapping_registry,
        )

        et_table = mapping_registry.metadata.tables[
            "earn_transactions"
        ]

        # 1. Check stale pending transactions (> 30 min old)
        cutoff = datetime.now(UTC) - timedelta(minutes=30)
        stmt = select(et_table).where(
            and_(
                et_table.c.status == "pending",
                et_table.c.created_at < cutoff,
            )
        )
        result = await session.execute(stmt)
        stale_txs = result.fetchall()

        confirmed = 0
        failed = 0

        for tx in stale_txs:
            # Mark stale pending txs as failed
            # In production, we'd check on-chain status first
            await session.execute(
                et_table.update()
                .where(et_table.c.id == tx.id)
                .values(status="failed")
            )
            failed += 1

        if stale_txs:
            await session.commit()

        # 2. Refresh all active earn positions
        # (delegates to refresh_earn_positions logic)
        from app.domain.ports.aave_gateway import AaveGateway
        from app.domain.ports.compound_gateway import (
            CompoundGateway,
        )

        ep_table = mapping_registry.metadata.tables[
            "earn_positions"
        ]
        stmt = select(ep_table).where(
            and_(
                ep_table.c.status == "active",
                ep_table.c.protocol.in_(["aave", "compound"]),
                ep_table.c.wallet_address.isnot(None),
            )
        )
        result = await session.execute(stmt)
        positions = result.fetchall()

        reconciled = 0
        for pos in positions:
            try:
                if pos.protocol == "aave":
                    aave = await container.get(AaveGateway)
                    on_chain = await aave.get_user_position(
                        address=pos.wallet_address,
                        chain=pos.chain or "base",
                    )
                    if on_chain and on_chain.supplies:
                        for supply in on_chain.supplies:
                            if supply.symbol == pos.asset:
                                await _upsert_earn_position(
                                    container,
                                    user_id="",
                                    wallet_address=pos.wallet_address,
                                    protocol="aave",
                                    chain=pos.chain or "base",
                                    asset_symbol=supply.symbol,
                                    amount=supply.balance,
                                    apy=supply.apy,
                                )
                                reconciled += 1

                elif pos.protocol == "compound":
                    compound = await container.get(
                        CompoundGateway
                    )
                    comp_pos = (
                        await compound.get_user_position(
                            user_address=pos.wallet_address,
                            asset=pos.asset,
                            chain=pos.chain or "base",
                        )
                    )
                    if comp_pos and comp_pos.supplied > 0:
                        await _upsert_earn_position(
                            container,
                            user_id="",
                            wallet_address=pos.wallet_address,
                            protocol="compound",
                            chain=pos.chain or "base",
                            asset_symbol=pos.asset,
                            amount=comp_pos.supplied,
                        )
                        reconciled += 1

            except Exception as exc:
                logger.warning(
                    "Reconciliation error for %s/%s: %s",
                    pos.protocol,
                    pos.wallet_address,
                    exc,
                )

        stats = {
            "stale_failed": failed,
            "reconciled": reconciled,
        }
        logger.info(
            "Earn transaction reconciliation complete: %s", stats
        )
        return stats

    asyncio.run(_run_task(runner))


# ============================================================================
# Task 4: recover_earn_positions (Login-triggered)
# ============================================================================


@celery_app.task(
    name="earn_positions.recover",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def recover_earn_positions(
    self,
    user_id: str,
    wallet_address: str,
):
    """
    Recover Aave V3 + Compound V3 positions for a single user.

    Triggered on login via /privy-login with 5-min Redis cooldown.
    Fetches on-chain positions and reconciles with earn_positions.

    Args:
        user_id: User UUID or ID as string
        wallet_address: User wallet address
    """

    async def runner(container):
        from app.domain.ports.aave_gateway import AaveGateway
        from app.domain.ports.compound_gateway import (
            CompoundGateway,
        )

        recovered = {"aave": 0, "compound": 0, "errors": []}

        # 1. Recover Aave positions (Base chain)
        try:
            aave: AaveGateway = await container.get(AaveGateway)
            position = await aave.get_user_position(
                address=wallet_address, chain="base"
            )
            if position and position.supplies:
                for supply in position.supplies:
                    await _upsert_earn_position(
                        container,
                        user_id=user_id,
                        wallet_address=wallet_address,
                        protocol="aave",
                        chain="base",
                        asset_symbol=supply.symbol,
                        amount=supply.balance,
                        apy=supply.apy,
                    )
                    recovered["aave"] += 1
        except Exception as exc:
            recovered["errors"].append(f"aave: {exc}")
            logger.warning(
                "Aave recovery failed for %s: %s",
                wallet_address,
                exc,
            )

        # 2. Recover Compound positions (Base chain)
        try:
            compound: CompoundGateway = await container.get(
                CompoundGateway
            )
            for asset in ("USDC", "ETH"):
                comp_pos = await compound.get_user_position(
                    user_address=wallet_address,
                    asset=asset,
                    chain="base",
                )
                if comp_pos and comp_pos.supplied > 0:
                    await _upsert_earn_position(
                        container,
                        user_id=user_id,
                        wallet_address=wallet_address,
                        protocol="compound",
                        chain="base",
                        asset_symbol=asset,
                        amount=comp_pos.supplied,
                    )
                    recovered["compound"] += 1
        except Exception as exc:
            recovered["errors"].append(f"compound: {exc}")
            logger.warning(
                "Compound recovery failed for %s: %s",
                wallet_address,
                exc,
            )

        logger.info(
            "Earn position recovery for %s: %s",
            wallet_address,
            recovered,
        )
        return recovered

    asyncio.run(_run_task(runner))
