"""
Transaction Confirmation Celery Tasks.

Celery tasks for confirming pending blockchain transactions.
Can be scheduled via Celery Beat for periodic execution.
"""

import asyncio
import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="confirm_pending_transactions",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def confirm_pending_transactions_task(
    self,  # noqa: ARG001 - Required by Celery bind=True
    limit: int = 50,
    older_than_seconds: int = 10,
    use_testnet: bool | None = None,
) -> dict[str, Any]:
    """
    Celery task to confirm pending transactions on-chain.

    This task queries the database for pending transactions, checks their
    status on-chain via RPC, and updates the database accordingly.

    Args:
        limit: Maximum transactions to process per batch.
        older_than_seconds: Only process transactions older than this.
        use_testnet: Override testnet setting (None uses config default).

    Returns:
        Dictionary with processing summary.
    """
    # Import inside task to avoid circular imports
    from app.cli.confirm_pending_transactions import run_once  # noqa: PLC0415

    logger.info(
        f"[Celery] Starting transaction confirmation task "
        f"(limit={limit}, older_than={older_than_seconds}s)"
    )

    try:
        # Run the async function in the event loop
        result = asyncio.run(
            run_once(
                limit=limit,
                older_than_seconds=older_than_seconds,
                use_testnet=use_testnet,
            )
        )

        summary = {
            "status": "success",
            "transactions_processed": result.transactions_processed,
            "confirmed": result.confirmed,
            "failed": result.failed,
            "still_pending": result.still_pending,
            "duration_seconds": result.duration_seconds,
        }

        logger.info(
            f"[Celery] Transaction confirmation completed: "
            f"{result.confirmed} confirmed, {result.failed} failed, "
            f"{result.still_pending} pending"
        )

        return summary

    except Exception as e:
        logger.error(f"[Celery] Transaction confirmation failed: {e}")
        raise


@shared_task(name="confirm_pending_transactions_testnet")
def confirm_pending_transactions_testnet_task(
    limit: int = 50,
) -> dict[str, Any]:
    """
    Convenience task for testnet confirmation.

    Always uses testnet RPC endpoints (Sepolia, Base Sepolia).
    """
    return confirm_pending_transactions_task(
        limit=limit,
        use_testnet=True,
    )


@shared_task(name="confirm_pending_transactions_mainnet")
def confirm_pending_transactions_mainnet_task(
    limit: int = 50,
) -> dict[str, Any]:
    """
    Convenience task for mainnet confirmation.

    Uses mainnet RPC endpoints (Ethereum, Base, etc.).
    """
    return confirm_pending_transactions_task(
        limit=limit,
        use_testnet=False,
    )
