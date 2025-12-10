"""
Pytest fixtures for Agent Squad integration tests.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock


async def _mock_chat_with_delay(*args, **kwargs):
    """Mock chat function that simulates realistic latency."""
    # Simulate realistic API latency (10-50ms)
    await asyncio.sleep(0.015)  # 15ms
    return {
        "content": "Test response",
        "tokens_used": 100,
        "model": "gpt-4o-mini",
        "finish_reason": "stop",
    }


@pytest.fixture
def mock_llm_client(mocker):
    """Mock LLM client for testing."""
    client = mocker.AsyncMock()
    client.classify_intent.return_value = {
        "intent": "general_chat",
        "confidence": 0.95,
        "reasoning": "Test reasoning",
    }
    # Use side_effect to simulate async delay
    client.chat.side_effect = _mock_chat_with_delay
    return client


@pytest.fixture
def mock_storage(mocker):
    """Mock context storage for testing."""
    storage = mocker.AsyncMock()
    storage.get_message_count.return_value = 0
    storage.get_messages.return_value = []
    storage.get_metadata.return_value = {"user": {}, "session": {}}
    return storage


@pytest.fixture
def mock_feature_flags(mocker):
    """Mock feature flags for testing."""
    flags = mocker.AsyncMock()
    flags.is_agent_enabled.return_value = True
    return flags


@pytest.fixture
def mock_intent_classifier(mocker):
    """Mock intent classifier for testing."""
    from app.domain.enums.agent_type import AgentType
    
    classifier = mocker.AsyncMock()
    classifier.classify.return_value = mocker.Mock(
        agent_type=AgentType.CHAT,
        confidence=0.95,
        intent="general_chat",
        reasoning="Test reasoning",
    )
    return classifier
