"""
Transaction Confirmation Worker.

CLI worker that periodically confirms pending transactions on-chain
and updates their status in the database.

Usage:
    # One-off batch processing (process once and exit)
    uv run python -m app.cli.confirm_pending_transactions --once

    # Continuous loop mode (run as background worker)
    uv run python -m app.cli.confirm_pending_transactions --loop

    # With custom settings
    uv run python -m app.cli.confirm_pending_transactions --once --limit 100 --testnet

    # Mainnet mode
    uv run python -m app.cli.confirm_pending_transactions --loop --mainnet
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.setup.config.transaction_confirmation import (
        TransactionConfirmationSettings,
    )

logger = logging.getLogger(__name__)


@dataclass
class WorkerResult:
    """Summary of worker execution."""

    transactions_processed: int
    confirmed: int
    failed: int
    still_pending: int
    duration_seconds: float
    started_at: datetime
    finished_at: datetime


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for CLI worker."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Quiet noisy loggers
    logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def load_env_file() -> None:
    """Load environment variables from .env file if it exists."""
    app_env = os.getenv("APP_ENV", "local")
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / "config" / app_env / f".env.{app_env}"
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                for raw_line in f:
                    stripped = raw_line.strip()
                    if stripped and not stripped.startswith("#") and "=" in stripped:
                        key, _, value = stripped.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())
            break


def create_session_factory() -> async_sessionmaker:
    """Create a database session factory."""
    # Imports inside function to avoid circular imports in CLI entrypoint
    from sqlalchemy.ext.asyncio import (  # noqa: PLC0415
        async_sessionmaker,
        create_async_engine,
    )

    from app.setup.config.settings import load_settings  # noqa: PLC0415

    settings = load_settings()
    dsn = settings.postgres.dsn

    engine = create_async_engine(
        dsn,
        pool_size=5,
        max_overflow=10,
        echo=False,
        pool_pre_ping=True,
    )

    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
    )


def load_worker_settings() -> TransactionConfirmationSettings:
    """Load transaction confirmation settings."""
    from app.setup.config.settings import load_settings  # noqa: PLC0415

    settings = load_settings()
    return settings.transaction_confirmation


async def process_batch_once(
    session: AsyncSession,
    settings: TransactionConfirmationSettings,
    *,
    limit: int | None = None,
    older_than_seconds: int | None = None,
) -> WorkerResult:
    """
    Process pending transactions once and return results.

    Args:
        session: Database session.
        settings: Worker settings.
        limit: Override batch limit (optional).
        older_than_seconds: Override older_than filter (optional).

    Returns:
        WorkerResult with processing summary.
    """
    # Imports inside function to avoid circular imports in CLI entrypoint
    from app.application.transaction.factory import (  # noqa: PLC0415
        create_confirmation_service_from_settings,
    )
    from app.domain.enums.transaction_status import (  # noqa: PLC0415
        TransactionStatus,
    )

    started_at = datetime.now(UTC)

    service = create_confirmation_service_from_settings(session, settings)

    results = await service.process_pending_transactions(
        limit=limit or settings.batch_limit,
        older_than_seconds=older_than_seconds or settings.older_than_seconds,
    )

    # Commit any changes
    await session.commit()

    finished_at = datetime.now(UTC)

    # Calculate summary
    confirmed = sum(1 for r in results if r.status == TransactionStatus.SUCCESS)
    failed = sum(1 for r in results if r.status == TransactionStatus.FAILED)
    still_pending = sum(1 for r in results if r.status == TransactionStatus.PENDING)

    return WorkerResult(
        transactions_processed=len(results),
        confirmed=confirmed,
        failed=failed,
        still_pending=still_pending,
        duration_seconds=(finished_at - started_at).total_seconds(),
        started_at=started_at,
        finished_at=finished_at,
    )


async def run_once(
    *,
    limit: int | None = None,
    older_than_seconds: int | None = None,
    use_testnet: bool | None = None,
) -> WorkerResult:
    """
    Run one-off batch processing.

    Args:
        limit: Maximum transactions to process.
        older_than_seconds: Only process transactions older than this.
        use_testnet: Override testnet setting.

    Returns:
        WorkerResult with processing summary.
    """
    load_env_file()
    settings = load_worker_settings()

    # Apply overrides
    if use_testnet is not None:
        settings = settings.model_copy(update={"use_testnet": use_testnet})

    session_factory = create_session_factory()

    logger.info(
        f"Starting one-off batch processing "
        f"(testnet={settings.use_testnet}, limit={limit or settings.batch_limit})"
    )

    async with session_factory() as session:
        result = await process_batch_once(
            session,
            settings,
            limit=limit,
            older_than_seconds=older_than_seconds,
        )

    logger.info(
        f"Completed: {result.transactions_processed} processed "
        f"({result.confirmed} confirmed, {result.failed} failed, "
        f"{result.still_pending} still pending) "
        f"in {result.duration_seconds:.2f}s"
    )

    return result


async def run_loop(
    *,
    interval_seconds: int | None = None,
    limit_per_batch: int | None = None,
    use_testnet: bool | None = None,
) -> None:
    """
    Run continuous confirmation loop.

    This runs indefinitely, processing pending transactions at regular intervals.

    Args:
        interval_seconds: Seconds between batches.
        limit_per_batch: Maximum transactions per batch.
        use_testnet: Override testnet setting.
    """
    load_env_file()
    settings = load_worker_settings()

    # Apply overrides
    if use_testnet is not None:
        settings = settings.model_copy(update={"use_testnet": use_testnet})
    if interval_seconds is not None:
        settings = settings.model_copy(update={"interval_seconds": interval_seconds})

    session_factory = create_session_factory()

    effective_interval = interval_seconds or settings.interval_seconds
    effective_limit = limit_per_batch or settings.batch_limit

    logger.info(
        f"Starting confirmation loop "
        f"(testnet={settings.use_testnet}, interval={effective_interval}s, "
        f"batch={effective_limit})"
    )

    # Setup graceful shutdown
    shutdown_event = asyncio.Event()

    def handle_signal(sig: signal.Signals) -> None:
        logger.info(f"Received {sig.name}, shutting down gracefully...")
        shutdown_event.set()

    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

    iteration = 0
    while not shutdown_event.is_set():
        iteration += 1
        logger.debug(f"Loop iteration {iteration}")

        try:
            async with session_factory() as session:
                result = await process_batch_once(
                    session,
                    settings,
                    limit=effective_limit,
                )

            if result.transactions_processed > 0:
                logger.info(
                    f"[{iteration}] Processed {result.transactions_processed}: "
                    f"{result.confirmed} confirmed, {result.failed} failed, "
                    f"{result.still_pending} pending ({result.duration_seconds:.2f}s)"
                )
            else:
                logger.debug(f"[{iteration}] No pending transactions")

        except Exception as e:
            logger.error(f"[{iteration}] Error in confirmation loop: {e}")

        # Wait for next interval or shutdown
        with suppress(TimeoutError):
            await asyncio.wait_for(
                shutdown_event.wait(),
                timeout=effective_interval,
            )

    logger.info("Worker shutdown complete")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Transaction Confirmation Worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process pending transactions once
  uv run python -m app.cli.confirm_pending_transactions --once

  # Run as continuous background worker
  uv run python -m app.cli.confirm_pending_transactions --loop

  # Process with custom limit
  uv run python -m app.cli.confirm_pending_transactions --once --limit 100

  # Use mainnet RPC endpoints
  uv run python -m app.cli.confirm_pending_transactions --loop --mainnet
        """,
    )

    # Mode selection (mutually exclusive)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--once",
        action="store_true",
        help="Process pending transactions once and exit",
    )
    mode.add_argument(
        "--loop",
        action="store_true",
        help="Run continuous confirmation loop",
    )

    # Network selection
    network = parser.add_mutually_exclusive_group()
    network.add_argument(
        "--testnet",
        action="store_true",
        help="Use testnet RPC endpoints (default)",
    )
    network.add_argument(
        "--mainnet",
        action="store_true",
        help="Use mainnet RPC endpoints",
    )

    # Processing options
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum transactions to process per batch",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Seconds between batches (loop mode only)",
    )
    parser.add_argument(
        "--older-than",
        type=int,
        default=None,
        help="Only process transactions older than N seconds",
    )

    # Logging
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for CLI worker."""
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Determine network mode
    use_testnet = None
    if args.testnet:
        use_testnet = True
    elif args.mainnet:
        use_testnet = False

    try:
        if args.once:
            result = asyncio.run(
                run_once(
                    limit=args.limit,
                    older_than_seconds=args.older_than,
                    use_testnet=use_testnet,
                )
            )
            # Exit with non-zero if there were failures
            return 1 if result.failed > 0 else 0

        if args.loop:
            asyncio.run(
                run_loop(
                    interval_seconds=args.interval,
                    limit_per_batch=args.limit,
                    use_testnet=use_testnet,
                )
            )
            return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
