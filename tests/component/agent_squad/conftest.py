"""
Component test fixtures for Agent Squad.

Provides mock LLM client for intent classification testing.
"""

import pytest


@pytest.fixture
def mock_llm_client(mocker):
    """
    Mock LLM client for intent classification testing.

    Returns:
        AsyncMock configured with classify_intent method

    Example:
        async def test_classify_intent(mock_llm_client):
            mock_llm_client.classify_intent.return_value = {
                "intent": "general_chat",
                "confidence": 0.95,
                "reasoning": "User greeting"
            }

            classifier = IntentClassifier(llm_client=mock_llm_client)
            result = await classifier.classify(message, context)

            assert result.intent == "general_chat"
    """
    client = mocker.AsyncMock()
    # Set default response for classify_intent
    client.classify_intent.return_value = {
        "intent": "general_chat",
        "confidence": 0.95,
        "reasoning": "Default mock intent classification",
    }
    return client
