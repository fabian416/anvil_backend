"""
Pytest configuration and shared fixtures.
"""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dishka import make_async_container

from app.run import make_app
from app.setup.config.settings import load_settings, Settings


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "graphrag: GraphRAG tests")
    config.addinivalue_line("markers", "ml: ML tests")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Load test settings."""
    # TODO: Use test-specific settings
    return load_settings()


@pytest.fixture
def test_app(test_settings: Settings):
    """Create test FastAPI application."""
    app = make_app()
    return app


@pytest.fixture
def client(test_app) -> TestClient:
    """Create test client."""
    return TestClient(test_app)


# Database fixtures
@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine."""
    # TODO: Use test database
    # For now, using in-memory SQLite
    engine = create_engine("sqlite:///:memory:")
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
