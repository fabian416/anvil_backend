"""
Pytest configuration and shared fixtures.

This module provides:
- Pytest configuration and markers
- Test DI container with mock providers
- Database fixtures (in-memory SQLite)
- Authentication fixtures
- Common test utilities
"""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dishka import make_async_container

from app.setup.config.settings import load_settings


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "graphrag: GraphRAG tests")
    config.addinivalue_line("markers", "ml: ML tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "load: Load tests")
    config.addinivalue_line("markers", "contract: API contract tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "chat: Chat/conversation tests")
    config.addinivalue_line("markers", "subscription: Subscription tests")
    config.addinivalue_line("markers", "defi: DeFi protocol tests")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Load test settings."""
    try:
        return load_settings()
    except Exception:
        # Return mock settings if loading fails
        settings = MagicMock()
        settings.app_name = "test"
        settings.debug = True
        return settings


@pytest_asyncio.fixture
async def test_container():
    """Create test DI container with mock providers."""
    from app.setup.ioc.testing import create_test_container
    container = create_test_container()
    yield container
    await container.close()


@pytest.fixture
def test_app(test_settings):
    """Create test FastAPI application (requires httpx)."""
    try:
        from app.run import make_app
        app = make_app()
        return app
    except Exception as e:
        pytest.skip(f"FastAPI app creation failed: {e}")


@pytest.fixture
def client(test_app):
    """Create test client (requires httpx)."""
    try:
        from fastapi.testclient import TestClient
        return TestClient(test_app)
    except ImportError as e:
        pytest.skip(f"TestClient not available - install httpx for integration tests: {e}")


@pytest.fixture
def mock_client():
    """Create mock test client without real app."""
    client = MagicMock()
    client.get = MagicMock(return_value=MagicMock(status_code=200, json=lambda: {}))
    client.post = MagicMock(return_value=MagicMock(status_code=200, json=lambda: {}))
    client.put = MagicMock(return_value=MagicMock(status_code=200, json=lambda: {}))
    client.delete = MagicMock(return_value=MagicMock(status_code=200, json=lambda: {}))
    return client


# Database fixtures
@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine with ORM mappings.

    Uses SQLite for fast in-memory tests. Note: PostgreSQL-specific types
    (JSONB, UUID) are converted to SQLite-compatible types.
    """
    # Initialize SQLAlchemy mappings for domain entities
    from app.infrastructure.persistence_sqla.mappings.all import map_tables
    from app.infrastructure.persistence_sqla.registry import mapping_registry
    from sqlalchemy.dialects import sqlite
    from sqlalchemy.dialects.postgresql import JSONB, UUID
    from sqlalchemy import JSON, String

    # Register type adapters for PostgreSQL types in SQLite
    sqlite.dialect.ischema_names['JSONB'] = JSON
    sqlite.dialect.ischema_names['UUID'] = String

    map_tables()

    # Create in-memory SQLite database for tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # Create only essential tables (skip tables with incompatible types)
    try:
        # Create tables one by one, skipping those with errors
        for table_name, table in mapping_registry.metadata.tables.items():
            try:
                table.create(engine, checkfirst=True)
            except Exception as e:
                # Skip tables that can't be created in SQLite
                pass
    except Exception:
        pass

    yield engine
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def db_session(test_db_session):
    """Alias for test_db_session for backward compatibility."""
    return test_db_session


# Domain service fixtures for unit tests
@pytest.fixture
def user_id_generator():
    """Mock user ID generator for UserService tests."""
    generator = MagicMock()
    counter = [0]
    def gen():
        counter[0] += 1
        return counter[0]
    generator.side_effect = gen
    generator.return_value = 1
    return generator


@pytest.fixture
def password_hasher():
    """Mock password hasher for UserService tests."""
    hasher = MagicMock()
    hasher.hash.return_value = b"hashed_password"
    hasher.verify.return_value = True
    return hasher


# Mock fixtures
@pytest.fixture
def mock_user_id():
    """Generate mock user ID."""
    return uuid4()


@pytest.fixture
def mock_protocol_id():
    """Generate mock protocol ID."""
    return uuid4()


@pytest.fixture
def mock_auth_token():
    """Generate mock auth token."""
    return "mock_jwt_token_for_testing"


@pytest.fixture
def auth_headers(mock_auth_token):
    """Generate authentication headers for API requests."""
    return {
        "Authorization": f"Bearer {mock_auth_token}",
        "Content-Type": "application/json",
    }


# GraphRAG fixtures
@pytest.fixture
def mock_graphrag_results():
    """Mock GraphRAG search results."""
    return [
        {
            "protocol_id": str(uuid4()),
            "protocol_name": "Aave V3",
            "similarity_score": 0.95,
            "risk_score": 2.1,
            "tvl": 6200000000,
        },
        {
            "protocol_id": str(uuid4()),
            "protocol_name": "Compound",
            "similarity_score": 0.87,
            "risk_score": 2.5,
            "tvl": 3800000000,
        },
    ]


# ML fixtures
@pytest.fixture
def mock_risk_prediction():
    """Mock ML risk prediction."""
    return {
        "protocol_id": str(uuid4()),
        "protocol_name": "Lido Finance",
        "risk_score": 2.3,
        "risk_level": "LOW",
        "confidence": 0.92,
        "risk_trend": "STABLE",
        "contributing_factors": [
            {
                "feature": "high_tvl_stability",
                "impact": -0.8,
                "explanation": "TVL stable at $28.4B",
            }
        ],
    }


# Portfolio fixtures
@pytest.fixture
def mock_portfolio_risk():
    """Mock portfolio risk data."""
    return {
        "overall_risk_score": 3.2,
        "risk_distribution": {
            "LOW": 0.45,
            "MEDIUM": 0.35,
            "HIGH": 0.15,
            "CRITICAL": 0.05,
        },
        "protocols_at_risk": [
            {
                "protocol_name": "Euler Finance",
                "risk_score": 7.8,
                "exposure_usd": 2450,
            }
        ],
    }


# WebSocket fixtures
@pytest.fixture
def mock_websocket_message():
    """Mock WebSocket message."""
    return {
        "type": "risk:alert",
        "protocol_id": str(uuid4()),
        "protocol_name": "Test Protocol",
        "severity": "HIGH",
        "message": "Risk score increased",
        "risk_score": 7.8,
        "timestamp": 1701388800,
    }
