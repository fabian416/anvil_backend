"""
Pytest fixtures for Agent Squad integration tests.
"""

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_llm_client(mocker):
    """Mock LLM client for testing."""
    client = mocker.AsyncMock()
    client.classify_intent.return_value = {
        "intent": "general_chat",
        "confidence": 0.95,
        "reasoning": "Test reasoning",
    }
    client.chat.return_value = {
        "content": "Test response",
        "tokens_used": 100,
        "model": "gpt-4o-mini",
        "finish_reason": "stop",
    }
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
