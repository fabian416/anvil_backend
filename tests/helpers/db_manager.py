"""
Database test manager for test isolation and data management.

Provides utilities for:
- Setting up test database sessions
- Transaction rollback for test isolation
- Seeding test data
- Cleanup between tests

Usage:
    from tests.helpers.db_manager import DatabaseTestManager

    # In test setup
    db_manager = DatabaseTestManager()
    session = await db_manager.setup_test_db()

    # Seed test data
    await db_manager.seed_test_data([user_fixture, conversation_fixture])

    # In teardown
    await db_manager.rollback_transaction()
    await db_manager.cleanup()
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Sequence
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session


class DatabaseTestManager:
    """
    Manager for test database operations.

    Provides methods for creating test database sessions,
    managing transactions for test isolation, and seeding test data.
    """

    def __init__(
        self,
        database_url: str | None = None,
        echo: bool = False,
    ):
        """
        Initialize the database test manager.

        Args:
            database_url: Database connection URL (async)
            echo: Whether to echo SQL statements
        """
        self._database_url = database_url or "sqlite+aiosqlite:///:memory:"
        self._echo = echo
        self._engine = None
        self._session_factory = None
        self._session: AsyncSession | None = None
        self._transaction = None

    async def setup_test_db(self) -> AsyncSession:
        """
        Set up the test database and return a session.

        Creates async engine and session factory if not exists,
        begins a transaction for rollback on cleanup.

        Returns:
            AsyncSession for database operations
        """
        if self._engine is None:
            self._engine = create_async_engine(
                self._database_url,
                echo=self._echo,
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

        # Create session and begin transaction
        self._session = self._session_factory()
        self._transaction = await self._session.begin_nested()

        return self._session

    async def rollback_transaction(self) -> None:
        """
        Rollback the current transaction.

        This ensures test data doesn't persist between tests.
        """
        if self._transaction is not None:
            await self._transaction.rollback()
            self._transaction = None

    async def commit_transaction(self) -> None:
        """
        Commit the current transaction.

        Use sparingly - prefer rollback for test isolation.
        """
        if self._transaction is not None:
            await self._transaction.commit()
            self._transaction = None

    async def cleanup(self) -> None:
        """
        Clean up database resources.

        Closes session and disposes engine.
        """
        if self._session is not None:
            await self._session.close()
            self._session = None

        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None

    async def seed_test_data(
        self,
        fixtures: Sequence[dict[str, Any] | Callable[..., dict[str, Any]]],
    ) -> list[Any]:
        """
        Seed test data into the database.

        Args:
            fixtures: List of fixture dictionaries or factory functions

        Returns:
            List of created objects/records
        """
        if self._session is None:
            raise ValueError("Database session not initialized. Call setup_test_db() first.")

        results = []
        for fixture in fixtures:
            if callable(fixture):
                fixture = fixture()

            # Determine model class from fixture
            model_class = fixture.pop("__model__", None)
            if model_class is not None:
                instance = model_class(**fixture)
                self._session.add(instance)
                results.append(instance)
            else:
                # Raw dictionary, add to results for reference
                results.append(fixture)

        await self._session.flush()
        return results

    async def execute_raw(self, sql: str, params: dict | None = None) -> Any:
        """
        Execute raw SQL statement.

        Args:
            sql: SQL statement
            params: Query parameters

        Returns:
            Query result
        """
        if self._session is None:
            raise ValueError("Database session not initialized. Call setup_test_db() first.")

        result = await self._session.execute(text(sql), params or {})
        return result

    async def clear_table(self, table_name: str) -> None:
        """
        Clear all data from a table.

        Args:
            table_name: Name of table to clear
        """
        if self._session is None:
            raise ValueError("Database session not initialized. Call setup_test_db() first.")

        await self._session.execute(text(f"DELETE FROM {table_name}"))
        await self._session.flush()

    async def get_by_id(self, model_class: type, id: UUID | int | str) -> Any | None:
        """
        Get a record by ID.

        Args:
            model_class: SQLAlchemy model class
            id: Record identifier

        Returns:
            Model instance or None
        """
        if self._session is None:
            raise ValueError("Database session not initialized. Call setup_test_db() first.")

        return await self._session.get(model_class, id)

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for nested transaction.

        Yields:
            AsyncSession within a savepoint
        """
        if self._session is None:
            raise ValueError("Database session not initialized. Call setup_test_db() first.")

        async with self._session.begin_nested():
            yield self._session

    @property
    def session(self) -> AsyncSession | None:
        """Get the current session."""
        return self._session


class SyncDatabaseTestManager:
    """
    Synchronous version of database test manager.

    For use with synchronous test functions.
    """

    def __init__(
        self,
        database_url: str | None = None,
        echo: bool = False,
    ):
        """
        Initialize the sync database test manager.

        Args:
            database_url: Database connection URL (sync)
            echo: Whether to echo SQL statements
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        self._database_url = database_url or "sqlite:///:memory:"
        self._echo = echo
        self._engine = create_engine(self._database_url, echo=echo)
        self._session_factory = sessionmaker(bind=self._engine)
        self._session: Session | None = None
        self._transaction = None

    def setup_test_db(self) -> Session:
        """Set up test database session with transaction."""
        self._session = self._session_factory()
        self._transaction = self._session.begin_nested()
        return self._session

    def rollback_transaction(self) -> None:
        """Rollback current transaction."""
        if self._transaction is not None:
            self._transaction.rollback()
            self._transaction = None

    def cleanup(self) -> None:
        """Clean up database resources."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def seed_test_data(
        self,
        fixtures: Sequence[dict[str, Any] | Callable[..., dict[str, Any]]],
    ) -> list[Any]:
        """Seed test data into database."""
        if self._session is None:
            raise ValueError("Database session not initialized.")

        results = []
        for fixture in fixtures:
            if callable(fixture):
                fixture = fixture()

            model_class = fixture.pop("__model__", None)
            if model_class is not None:
                instance = model_class(**fixture)
                self._session.add(instance)
                results.append(instance)
            else:
                results.append(fixture)

        self._session.flush()
        return results

    @property
    def session(self) -> Session | None:
        """Get the current session."""
        return self._session
