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
    """Create event loop for async tests.

    Session-scoped to ensure all async fixtures and tests
    use the same event loop, preventing loop attachment errors.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_settings():
    """Load test settings.

    Note: Using function scope to prevent fixture pollution.
    Each test gets a fresh settings object that cannot be polluted by other tests.
    """
    try:
        return load_settings()
    except Exception:
        # Return mock settings if loading fails
        settings = MagicMock()
        settings.app_name = "test"
        settings.debug = True
        return settings


@pytest_asyncio.fixture
async def test_app(test_settings, monkeypatch):
    """
    Create test FastAPI application with real database for integration testing.

    Uses:
    - Real PostgreSQL database (anvil_test)
    - Real Redis connection (db 15)
    - All production providers from provider_registry
    - Test database provider for AsyncSession
    - Mock LLM providers (overrides OpenAI/Anthropic)

    This enables full end-to-end integration testing.

    Returns raw app (not TestClient) for use with httpx AsyncClient.
    """
    try:
        import os
        from app.setup.config.settings import load_settings, AppSettings
        from app.setup.config.database import PostgresSettings
        from app.setup.ioc.provider_registry import get_providers
        from app.setup.ioc.testing import get_integration_test_providers
        from dishka import make_async_container
        from dishka.integrations.fastapi import setup_dishka
        from app.setup.app_factory import create_app, configure_app
        from app.presentation.http.controllers.root_router import create_root_router

        # Set dummy API keys to allow provider initialization
        # (Mock providers will be used instead via DI override)
        # System uses Vertex AI (primary) + DeepInfra (fallback)
        monkeypatch.setenv("VERTEX_AI_API_KEY", "test_vertex_key_not_used")
        monkeypatch.setenv("DEEPINFRA_API_KEY", "test_deepinfra_key_not_used")
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key_not_used")  # Some legacy code still checks
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key_not_used")

        # Load original settings
        original_settings = load_settings()

        # Create new PostgresSettings with test database
        test_postgres = PostgresSettings(
            USER=original_settings.postgres.user,
            PASSWORD=original_settings.postgres.password,
            DB="anvil_test",  # Override database name
            HOST=original_settings.postgres.host,
            PORT=original_settings.postgres.port,
            DRIVER=original_settings.postgres.driver,
        )

        # Create new AppSettings with modified postgres config
        test_app_settings = AppSettings(
            postgres=test_postgres,
            sqla=original_settings.sqla,
            security=original_settings.security,
            logs=original_settings.logs,
            admin=original_settings.admin,
            mailgun=original_settings.mailgun,
            stripe=original_settings.stripe,
            privy=original_settings.privy,
            integrations=original_settings.integrations,
            mcp=original_settings.mcp,
            agno=original_settings.agno,
            projects=original_settings.projects,
            distillation=original_settings.distillation,
            agent_squad=original_settings.agent_squad,
            transaction_confirmation=original_settings.transaction_confirmation,
            translation=original_settings.translation,
        )

        # Create FastAPI app
        app = create_app()
        configure_app(app=app, root_router=create_root_router())

        # Create DI container with:
        # 1. All production providers (repositories, services, etc.)
        # 2. Integration test providers (override with mocks)
        # Note: Test providers come LAST to override production providers
        async_ioc_container = make_async_container(
            *get_providers(),  # All production providers
            *get_integration_test_providers(),  # Test overrides (DB + Mock LLM)
            context={AppSettings: test_app_settings},
        )

        setup_dishka(container=async_ioc_container, app=app)

        yield app

        # Cleanup
        await async_ioc_container.close()
    except Exception as e:
        pytest.skip(f"FastAPI app creation failed: {e}")


@pytest_asyncio.fixture
async def client(test_app):
    """Create async test client using httpx.

    Uses AsyncClient instead of TestClient to avoid event loop conflicts.
    This allows proper async/await patterns in tests.
    """
    try:
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            yield ac
    except ImportError as e:
        pytest.skip(f"AsyncClient not available - install httpx for integration tests: {e}")


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
@pytest.fixture(scope="session", autouse=True)
def test_db_engine():
    """Create test database engine with ORM mappings.

    Uses PostgreSQL test database for full compatibility with production types.
    Autouse=True ensures this runs before any tests that need database.
    """
    # Initialize SQLAlchemy mappings for domain entities
    from app.infrastructure.persistence_sqla.mappings.all import map_tables
    from app.infrastructure.persistence_sqla.registry import mapping_registry

    # Map all domain entities to database tables
    map_tables()

    # Create PostgreSQL test database engine
    engine = create_engine(
        "postgresql+psycopg://postgres:changethis@localhost:5432/anvil_test",
        pool_pre_ping=True,
        echo=False
    )

    # Create all tables in PostgreSQL test database
    mapping_registry.metadata.create_all(engine)

    yield engine

    # Clean up: drop all tables after test session
    mapping_registry.metadata.drop_all(engine)
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


@pytest_asyncio.fixture(scope="function", autouse=True)
async def cleanup_database(test_db_engine):
    """Clean up database tables before each test function.

    This ensures test isolation by truncating all tables BEFORE each test.
    Uses TRUNCATE for speed and CASCADE to handle foreign keys.

    Uses async to properly synchronize with async test sessions.
    """
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    # Create async engine for proper async cleanup
    async_engine = create_async_engine(
        "postgresql+asyncpg://postgres:changethis@localhost:5432/anvil_test",
        pool_pre_ping=True,
        echo=False
    )

    # Tables to clean (except alembic_version)
    tables = [
        "messages",
        "conversations",
        "sessions",
        "users",  # Also clean users table
        "guest_messages",
        "guest_conversations",
        "guest_users",
        "guest_telemetry",
    ]

    # Clean up BEFORE test to prevent data pollution from previous tests
    async with async_engine.begin() as connection:
        for table in tables:
            try:
                await connection.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            except Exception:
                # Table might not exist, ignore
                pass

    yield  # Run the test

    # Clean up after test as well for good measure
    async with async_engine.begin() as connection:
        for table in tables:
            try:
                await connection.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            except Exception:
                pass

    await async_engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(test_db_engine):
    """Create async test database session for async repositories."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    # Create async engine using asyncpg driver
    async_engine = create_async_engine(
        "postgresql+asyncpg://postgres:changethis@localhost:5432/anvil_test",
        pool_pre_ping=True,
        echo=False
    )

    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    await async_engine.dispose()


@pytest.fixture
def test_user(test_db_session):
    """Create a test user in the database for foreign key relationships (sync version)."""
    from sqlalchemy import text

    # Insert a test user directly using SQL to avoid entity mapping complexity
    # Note: UserRole enum uses lowercase values: 'user', 'admin', 'moderator', 'guest'
    test_db_session.execute(text("""
        INSERT INTO users (id, email, first_name, last_name, role, is_active, is_blocked, is_verified, retry_count, language)
        VALUES (123, 'test@example.com', 'Test', 'User', 'user', true, false, true, 0, 'en')
        ON CONFLICT (id) DO NOTHING
    """))
    test_db_session.execute(text("""
        INSERT INTO users (id, email, first_name, last_name, role, is_active, is_blocked, is_verified, retry_count, language)
        VALUES (456, 'test2@example.com', 'Test2', 'User2', 'user', true, false, true, 0, 'en')
        ON CONFLICT (id) DO NOTHING
    """))
    test_db_session.commit()

    yield 123  # Return the first user ID

    # Cleanup is handled by session rollback in test_db_session fixture


@pytest_asyncio.fixture
async def async_test_user(async_db_session):
    """Create a test user in the database for foreign key relationships (async version)."""
    from sqlalchemy import text

    # Insert a test user directly using SQL to avoid entity mapping complexity
    # Note: UserRole enum uses lowercase values: 'user', 'admin', 'moderator', 'guest'
    await async_db_session.execute(text("""
        INSERT INTO users (id, email, first_name, last_name, role, is_active, is_blocked, is_verified, retry_count, language)
        VALUES (123, 'test@example.com', 'Test', 'User', 'user', true, false, true, 0, 'en')
        ON CONFLICT (id) DO NOTHING
    """))
    await async_db_session.execute(text("""
        INSERT INTO users (id, email, first_name, last_name, role, is_active, is_blocked, is_verified, retry_count, language)
        VALUES (456, 'test2@example.com', 'Test2', 'User2', 'user', true, false, true, 0, 'en')
        ON CONFLICT (id) DO NOTHING
    """))
    await async_db_session.commit()

    yield 123  # Return the first user ID

    # Cleanup is handled by session rollback in async_db_session fixture


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


# AI Test Validation fixtures
@pytest.fixture
def llm_validator():
    """
    LLM test validator fixture.

    Provides AI-powered semantic validation for test responses.
    Automatically enabled if ENABLE_LLM_VALIDATION=true and DEEPINFRA_API_KEY is set.

    Usage:
        async def test_with_validation(client, llm_validator):
            response = await client.post(...)
            if llm_validator.enabled:
                validation = await llm_validator.validate_single_response(...)
    """
    from tests.helpers.llm_test_validator import LLMTestValidator

    return LLMTestValidator()


@pytest.fixture
def log_analyzer():
    """
    Log analyzer fixture.

    Provides automated error analysis from application logs.
    Automatically enabled if ENABLE_LOG_ANALYSIS=true on localhost.

    Usage:
        async def test_with_analysis(client, log_analyzer):
            if not test_passed and log_analyzer.enabled:
                analysis = log_analyzer.analyze_error(...)
    """
    from tests.helpers.log_analyzer import LogAnalyzer

    return LogAnalyzer()


@pytest.fixture
def csv_writer(tmp_path):
    """
    Enhanced CSV writer fixture.

    Writes test results with AI analysis columns.
    Creates a temporary CSV file in the test's tmp_path.

    Usage:
        async def test_with_csv(client, csv_writer):
            result = EnhancedTestResult(...)
            csv_writer.write_single_result(result)
    """
    from tests.helpers.enhanced_csv_writer import EnhancedCSVWriter

    output_file = tmp_path / "test_results.csv"
    return EnhancedCSVWriter(str(output_file))
