"""
Celery tasks for lending operations, guest conversation archival,
and withdraw transaction confirmation.

These tasks were previously defined in the shadowed tasks.py file
and were not being registered because the tasks/ package __init__.py
took precedence over tasks.py during Python module resolution.
"""

import asyncio

from app.infrastructure.celery.app import celery_app
from app.infrastructure.celery.helpers import _run_task


# ============================================================================
# Guest Conversation Archival
# ============================================================================


@celery_app.task(name="archive_guest_conversations")
def archive_guest_conversations():
    """
    Archive inactive guest conversations.

    Runs every hour at :00 to archive conversations that have been
    inactive for more than 1 hour. This keeps the guest_conversations
    table clean and ensures new sessions get fresh conversations.
    """

    async def runner(container):
        from datetime import datetime, UTC, timedelta
        from app.domain.guest.ports.guest_repository import GuestRepository

        repository = await container.get(GuestRepository)

        # Archive conversations older than 1 hour
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        archived_count = await repository.archive_inactive_conversations(
            one_hour_ago
        )

        print(
            f"Guest conversation archival complete: "
            f"{archived_count} conversations archived"
        )

    asyncio.run(_run_task(runner))


# ============================================================================
# Lending Health Monitoring
# ============================================================================


@celery_app.task(name="monitor_lending_health_factors")
def monitor_lending_health_factors():
    """
    Monitor all active lending positions and check health factors.

    Runs every 15 minutes to:
    - Fetch all active positions from Aave and Morpho
    - Calculate current health factors
    - Save health check snapshots
    - Generate alerts for critical positions (HF < 1.5)
    """

    async def runner(container):
        from app.application.lending.tasks import (
            LendingRepository,
            PositionProvider,
            MonitorHealthFactorsTask,
        )

        repository = await container.get(LendingRepository)
        position_provider = await container.get(PositionProvider)

        task = MonitorHealthFactorsTask(repository, position_provider)
        stats = await task.run()

        print(f"Lending health factor monitoring complete: {stats}")

    asyncio.run(_run_task(runner))


@celery_app.task(name="check_user_lending_health")
def check_user_lending_health(
    user_id: str, protocol: str, chain: str = "ethereum"
):
    """
    Check health factor for a specific user position.

    Used for:
    - On-demand health checks
    - Critical position monitoring
    - Pre-transaction validation

    Args:
        user_id: User UUID as string
        protocol: Protocol name ("aave" or "morpho")
        chain: Blockchain network (default: "ethereum")
    """

    async def runner(container):
        from uuid import UUID
        from app.application.lending.tasks import (
            LendingRepository,
            PositionProvider,
            CheckUserHealthFactorTask,
        )

        repository = await container.get(LendingRepository)
        position_provider = await container.get(PositionProvider)

        task = CheckUserHealthFactorTask(repository, position_provider)
        health_check = await task.run(
            user_id=UUID(user_id),
            protocol=protocol,
            chain=chain,
        )

        print(
            f"Health check complete for user {user_id}, protocol {protocol}: "
            f"HF={health_check.health_factor:.2f}, "
            f"level={health_check.health_factor_level}"
        )

    asyncio.run(_run_task(runner))


@celery_app.task(name="refresh_lending_positions")
def refresh_lending_positions():
    """
    Refresh lending positions from protocols.

    Runs every hour to fetch latest position data from Aave and Morpho
    and keep database in sync with on-chain state.
    """

    async def runner(container):
        from app.application.lending.tasks import (
            LendingRepository,
            PositionProvider,
            RefreshPositionsTask,
        )

        repository = await container.get(LendingRepository)
        position_provider = await container.get(PositionProvider)

        task = RefreshPositionsTask(repository, position_provider)
        stats = await task.run()

        print(f"Lending position refresh complete: {stats}")

    asyncio.run(_run_task(runner))


# ============================================================================
# Withdraw Transaction Confirmation
# ============================================================================


@celery_app.task(name="confirm_withdraw_transaction")
def confirm_withdraw_transaction(
    transaction_hash: str,
    user_id: str,
    protocol: str,
    chain: str,
    vault_address: str = None,
    market_id: str = None,
    amount: str = "0",
):
    """
    Confirm withdraw transaction and update position.

    Scheduled after user signs a withdraw transaction.
    Waits for confirmation, updates database, refreshes position.

    Args:
        transaction_hash: On-chain transaction hash
        user_id: User UUID as string
        protocol: Protocol name ("morpho" or "aave")
        chain: Blockchain network
        vault_address: MetaMorpho vault address (optional)
        market_id: Morpho Blue market ID (optional)
        amount: Withdrawn amount as string
    """

    async def runner(container):
        from uuid import UUID
        from decimal import Decimal
        from app.application.lending.tasks import (
            LendingRepository,
            PositionProvider,
            ConfirmWithdrawTransactionTask,
        )

        repository = await container.get(LendingRepository)
        position_provider = await container.get(PositionProvider)

        task = ConfirmWithdrawTransactionTask(
            repository=repository,
            position_provider=position_provider,
            web3_provider=None,
        )

        result = await task.run(
            transaction_hash=transaction_hash,
            user_id=UUID(user_id),
            protocol=protocol,
            chain=chain,
            vault_address=vault_address,
            market_id=market_id,
            amount=Decimal(amount),
        )

        print(
            f"Withdraw confirmation complete: tx={transaction_hash}, "
            f"status={result.get('status')}, confirmed={result.get('confirmed')}"
        )

    asyncio.run(_run_task(runner))
