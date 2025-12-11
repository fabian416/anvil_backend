"""
Factory for Transaction Confirmation Service.

Provides factory functions to create TransactionConfirmationService instances
with proper dependency injection, suitable for CLI workers and background tasks.

Supports optional portfolio snapshot creation on transaction confirmation.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.transaction.confirmation_service import (
    TransactionConfirmationService,
    PortfolioSnapshotCallback,
)
from app.infrastructure.adapters.transaction_repository_sqla import (
    SqlaTransactionRepository,
)
from app.setup.config.transaction_confirmation import (
    TransactionConfirmationSettings,
)

if TYPE_CHECKING:
    from app.domain.ports.transaction.transaction_repository import (
        TransactionRepository,
    )
    from app.domain.entities.wallet import WalletId

logger = logging.getLogger(__name__)


def create_confirmation_service(
    session: AsyncSession,
    *,
    use_testnet: bool = True,
    http_timeout: int = 30,
    on_transaction_confirmed: PortfolioSnapshotCallback | None = None,
) -> TransactionConfirmationService:
    """
    Create a TransactionConfirmationService with the given session.

    This is a simple factory that creates the service with an existing session.
    Use this when you already have a database session available.

    Args:
        session: SQLAlchemy async session for database operations.
        use_testnet: Whether to use testnet RPC endpoints.
        http_timeout: HTTP timeout for RPC calls in seconds.
        on_transaction_confirmed: Optional callback to create portfolio snapshot.

    Returns:
        Configured TransactionConfirmationService instance.
    """
    repository: TransactionRepository = SqlaTransactionRepository(session)
    return TransactionConfirmationService(
        transaction_repository=repository,
        use_testnet=use_testnet,
        http_timeout=http_timeout,
        on_transaction_confirmed=on_transaction_confirmed,
    )


def create_confirmation_service_from_settings(
    session: AsyncSession,
    settings: TransactionConfirmationSettings,
    *,
    on_transaction_confirmed: PortfolioSnapshotCallback | None = None,
) -> TransactionConfirmationService:
    """
    Create a TransactionConfirmationService from settings.

    This factory uses the application settings to configure the service.
    Use this when creating from the DI container or configuration.

    Args:
        session: SQLAlchemy async session for database operations.
        settings: Transaction confirmation settings from config.
        on_transaction_confirmed: Optional callback to create portfolio snapshot.

    Returns:
        Configured TransactionConfirmationService instance.
    """
    return create_confirmation_service(
        session=session,
        use_testnet=settings.use_testnet,
        http_timeout=settings.http_timeout,
        on_transaction_confirmed=on_transaction_confirmed,
    )


def create_confirmation_service_with_portfolio(
    session: AsyncSession,
    settings: TransactionConfirmationSettings,
) -> TransactionConfirmationService:
    """
    Create a TransactionConfirmationService with portfolio snapshot support.

    This factory creates the service with a callback that automatically
    creates portfolio snapshots when transactions are confirmed.

    Args:
        session: SQLAlchemy async session for database operations.
        settings: Transaction confirmation settings from config.

    Returns:
        Configured TransactionConfirmationService with portfolio support.
    """
    from app.application.portfolio.portfolio_service import PortfolioService
    from app.infrastructure.adapters.portfolio_repository_sqla import (
        SqlaPortfolioRepository,
    )
    from app.infrastructure.adapters.wallet_repository_sqla import SqlaWalletRepository

    # Create portfolio service
    portfolio_repo = SqlaPortfolioRepository(session)
    wallet_repo = SqlaWalletRepository(session)
    portfolio_service = PortfolioService(
        portfolio_repository=portfolio_repo,
        wallet_repository=wallet_repo,
        use_testnet=settings.use_testnet,
    )

    async def snapshot_callback(wallet_id: "WalletId") -> None:
        """Create portfolio snapshot for the wallet."""
        await portfolio_service.snapshot_portfolio(wallet_id)

    return create_confirmation_service_from_settings(
        session=session,
        settings=settings,
        on_transaction_confirmed=snapshot_callback,
    )


class ConfirmationServiceFactory:
    """
    Factory class for creating TransactionConfirmationService instances.

    This class provides a higher-level interface for creating services,
    managing database sessions and configuration.

    Usage:
        factory = ConfirmationServiceFactory(
            session_factory=async_sessionmaker(...),
            settings=TransactionConfirmationSettings(...),
        )

        async with factory.create_service() as service:
            await service.process_pending_transactions()
    """

    def __init__(
        self,
        session_factory: async_sessionmaker,
        settings: TransactionConfirmationSettings,
    ) -> None:
        """
        Initialize the factory.

        Args:
            session_factory: SQLAlchemy async session factory.
            settings: Transaction confirmation settings.
        """
        self._session_factory = session_factory
        self._settings = settings

    async def create_service(self) -> TransactionConfirmationService:
        """
        Create a new TransactionConfirmationService with a fresh session.

        Note: The caller is responsible for managing the session lifecycle.
        For automatic session management, use create_service_with_session().

        Returns:
            TransactionConfirmationService instance.
        """
        session = self._session_factory()
        return create_confirmation_service_from_settings(session, self._settings)

    async def create_service_with_session(self):
        """
        Create a service within a managed session context.

        Yields:
            Tuple of (service, session) for use within an async context.

        Example:
            async with factory.create_service_with_session() as (svc, sess):
                await svc.process_pending_transactions()
                await sess.commit()
        """

        @asynccontextmanager
        async def _context():
            async with self._session_factory() as session:
                service = create_confirmation_service_from_settings(
                    session, self._settings
                )
                yield service, session

        return _context()

    @property
    def settings(self) -> TransactionConfirmationSettings:
        """Get the current settings."""
        return self._settings


# Type alias for async_sessionmaker (for type hints)
try:
    from sqlalchemy.ext.asyncio import async_sessionmaker
except ImportError:
    # Older SQLAlchemy versions
    async_sessionmaker = None
