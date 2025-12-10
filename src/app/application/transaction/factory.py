"""
Factory for Transaction Confirmation Service.

Provides factory functions to create TransactionConfirmationService instances
with proper dependency injection, suitable for CLI workers and background tasks.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.transaction.confirmation_service import (
    TransactionConfirmationService,
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

logger = logging.getLogger(__name__)


def create_confirmation_service(
    session: AsyncSession,
    *,
    use_testnet: bool = True,
    http_timeout: int = 30,
) -> TransactionConfirmationService:
    """
    Create a TransactionConfirmationService with the given session.

    This is a simple factory that creates the service with an existing session.
    Use this when you already have a database session available.

    Args:
        session: SQLAlchemy async session for database operations.
        use_testnet: Whether to use testnet RPC endpoints.
        http_timeout: HTTP timeout for RPC calls in seconds.

    Returns:
        Configured TransactionConfirmationService instance.
    """
    repository: TransactionRepository = SqlaTransactionRepository(session)
    return TransactionConfirmationService(
        transaction_repository=repository,
        use_testnet=use_testnet,
        http_timeout=http_timeout,
    )


def create_confirmation_service_from_settings(
    session: AsyncSession,
    settings: TransactionConfirmationSettings,
) -> TransactionConfirmationService:
    """
    Create a TransactionConfirmationService from settings.

    This factory uses the application settings to configure the service.
    Use this when creating from the DI container or configuration.

    Args:
        session: SQLAlchemy async session for database operations.
        settings: Transaction confirmation settings from config.

    Returns:
        Configured TransactionConfirmationService instance.
    """
    return create_confirmation_service(
        session=session,
        use_testnet=settings.use_testnet,
        http_timeout=settings.http_timeout,
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
