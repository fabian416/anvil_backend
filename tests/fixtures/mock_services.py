"""
Mock service fixtures for unit tests.

Provides mocked external services, gateways, and repositories
for isolated unit testing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.fixture
def mock_conversation_repository():
    """Mock ConversationRepository for unit tests."""
    repository = AsyncMock()
    
    # Configure default behaviors
    repository.save = AsyncMock(return_value=None)
    repository.get_by_id = AsyncMock(return_value=None)
    repository.list_by_user = AsyncMock(return_value=[])
    repository.delete = AsyncMock(return_value=None)
    
    return repository


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository for unit tests."""
    repository = AsyncMock()
    
    # Configure default behaviors
    repository.save = AsyncMock(return_value=None)
    repository.get_by_id = AsyncMock(return_value=None)
    repository.get_by_email = AsyncMock(return_value=None)
    repository.delete = AsyncMock(return_value=None)
    
    return repository


@pytest.fixture
def mock_agent_gateway():
    """Mock AgentGateway for unit tests."""
    gateway = AsyncMock()
    
    # Configure default response
    gateway.process_message = AsyncMock(
        return_value={
            "response": "Mock agent response",
            "confidence": 0.95,
            "sources": []
        }
    )
    
    return gateway


@pytest.fixture
def mock_defi_data_provider():
    """Mock DefiDataProvider for unit tests."""
    provider = AsyncMock()
    
    # Configure default responses
    provider.get_protocol_data = AsyncMock(
        return_value={
            "protocol_id": str(uuid4()),
            "name": "Aave V3",
            "tvl": 6200000000,
            "risk_score": 2.1,
        }
    )
    
    provider.get_market_data = AsyncMock(
        return_value={
            "protocols": [],
            "total_tvl": 150000000000,
        }
    )
    
    return provider


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for unit tests."""
    task = MagicMock()
    
    # Mock task ID
    task.delay.return_value.id = "test-task-123"
    task.apply_async.return_value.id = "test-task-123"
    
    return task


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for unit tests."""
    redis = AsyncMock()
    
    # Configure default behaviors
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=False)
    
    return redis
