"""
Database fixtures for integration tests.

Provides pytest fixtures for database sessions, transactions, and
test data cleanup.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create test database engine.
    
    Uses in-memory SQLite for fast tests.
    For integration tests, override with PostgreSQL test database.
    """
    # In-memory SQLite for unit tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """
    Create test database session with automatic rollback.
    
    Each test gets a fresh session that rolls back at the end,
    ensuring test isolation.
    """
    # Create tables
    # Note: In real implementation, import Base and create_all
    # from app.infrastructure.persistence_sqla.base import Base
    # Base.metadata.create_all(bind=test_db_engine)
    
    # Create session
    SessionLocal = sessionmaker(
        bind=test_db_engine,
        autocommit=False,
        autoflush=False,
    )
    session = SessionLocal()
    
    # Start transaction
    session.begin()
    
    try:
        yield session
    finally:
        # Rollback transaction
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def db_session(test_db_session):
    """Alias for test_db_session for convenience."""
    return test_db_session
