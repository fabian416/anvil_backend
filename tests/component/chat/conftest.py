"""
Component test fixtures for chat domain.

Provides fixtures for testing chat commands and queries in isolation:
- Commands: CreateConversation, SendMessage
- Queries: ListConversations, GetConversation, GetMessages
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from app.application.chat.commands.create_conversation import CreateConversation
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.queries.list_conversations import ListConversations
from app.application.chat.queries.get_conversation import GetConversation
from app.application.chat.queries.get_messages import GetMessages


# ============================================================================
# Mock Transaction Manager
# ============================================================================

@pytest.fixture
def mock_transaction_manager():
    """
    Mock transaction manager for component tests.
    
    Returns:
        Mock with async commit/rollback methods
    
    Note: In-memory repositories don't need real transactions
    """
    tx = MagicMock()
    tx.commit = AsyncMock()
    tx.rollback = AsyncMock()
    return tx


# ============================================================================
# Mock Agent Gateway
# ============================================================================

@pytest.fixture
def mock_agent_gateway():
    """
    Mock agent gateway for chat tests.
    
    Returns:
        Mock with configurable responses
    
    Example:
        mock_agent_gateway.process_message.return_value = "DeFi is..."
    """
    gateway = AsyncMock()
    gateway.process_message.return_value = "This is a mock agent response."
    return gateway


# ============================================================================
# Command Fixtures
# ============================================================================

@pytest.fixture
def create_conversation_command(conversation_repository, mock_transaction_manager):
    """
    CreateConversation command fixture.
    
    Returns:
        CreateConversation command instance
    
    Example:
        conversation = await create_conversation_command.execute(
            user_id=123,
            title="My Conversation"
        )
    """
    return CreateConversation(
        repository=conversation_repository,
        transaction_manager=mock_transaction_manager,
    )


@pytest.fixture
def send_message_command(
    conversation_repository,
    mock_agent_gateway,
    mock_transaction_manager,
):
    """
    SendMessage command fixture (simplified).
    
    Returns:
        SendMessage command instance without Hunter/ULTRA tool executors
    
    Example:
        user_msg, agent_msg = await send_message_command.execute(
            user_id=123,
            conversation_id=conversation.id,
            content="Hello"
        )
    """
    return SendMessage(
        repository=conversation_repository,
        agent_gateway=mock_agent_gateway,
        transaction_manager=mock_transaction_manager,
        # Skip Hunter/ULTRA executors for component tests (tested separately)
        hunter_executor=None,
        ultra_executor=None,
    )


# ============================================================================
# Query Fixtures
# ============================================================================

@pytest.fixture
def list_conversations_query(conversation_repository):
    """
    ListConversations query fixture.
    
    Returns:
        ListConversations query instance
    
    Example:
        conversations = await list_conversations_query.execute(
            user_id=123,
            limit=10,
            offset=0
        )
    """
    return ListConversations(repository=conversation_repository)


@pytest.fixture
def get_conversation_query(conversation_repository):
    """
    GetConversation query fixture.
    
    Returns:
        GetConversation query instance
    
    Example:
        conversation = await get_conversation_query.execute(
            user_id=123,
            conversation_id=conversation_id
        )
    """
    return GetConversation(repository=conversation_repository)


@pytest.fixture
def get_messages_query(conversation_repository):
    """
    GetMessages query fixture.
    
    Returns:
        GetMessages query instance
    
    Example:
        messages = await get_messages_query.execute(
            user_id=123,
            conversation_id=conversation_id,
            limit=50
        )
    """
    return GetMessages(repository=conversation_repository)


# ============================================================================
# Test User Fixture
# ============================================================================

@pytest.fixture
def test_user():
    """
    Test user context.

    Returns:
        Dictionary with user ID and email

    Example:
        user_id = test_user["id"]  # 123
    """
    return {
        "id": 123,
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
    }


# ============================================================================
# Unified Chat Component Test Fixtures
# ============================================================================

@pytest.fixture
def mock_intent_classifier():
    """
    Mock intent classifier for component tests.

    Returns:
        Mock with configurable intent classification responses

    Example:
        from dataclasses import dataclass

        @dataclass
        class IntentResult:
            intent: str
            confidence: float
            reasoning: str

        mock_intent_classifier.classify.return_value = IntentResult(
            intent="protocol_search",
            confidence=0.95,
            reasoning="Test classification"
        )
    """
    from dataclasses import dataclass

    @dataclass
    class IntentResult:
        """Simple intent classification result for tests."""
        intent: str
        confidence: float
        reasoning: str

    classifier = AsyncMock()
    # Default: general_chat intent
    classifier.classify.return_value = IntentResult(
        intent="general_chat",
        confidence=0.85,
        reasoning="Default test classification",
    )
    # Store IntentResult class for test access
    classifier.IntentResult = IntentResult
    return classifier


@pytest.fixture
def mock_handler_router():
    """
    Mock handler router for component tests.

    Returns:
        Mock that maps intents to handler names

    Example:
        handler_name = mock_handler_router.get_handler("protocol_search")
        # Returns: "graphrag_handler"
    """
    router = MagicMock()

    # Map intents to handler names
    intent_to_handler = {
        "protocol_search": "graphrag_handler",
        "protocol_risk_assessment": "graphrag_handler",
        "similar_protocols": "graphrag_handler",
        "hunter_sentiment": "hunter_handler",
        "hunter_prediction": "hunter_handler",
        "hunter_risk_analysis": "hunter_handler",
        "hunter_trading_signals": "hunter_handler",
        "ultra_arbitrage": "ultra_handler",
        "ultra_risk_analysis": "ultra_handler",
        "ultra_liquidity": "ultra_handler",
        "squad_spec_generation": "squad_handler",
        "squad_workflow": "squad_handler",
        "general_chat": "chat_handler",
    }

    router.get_handler.side_effect = lambda intent: intent_to_handler.get(intent, "chat_handler")
    return router


@pytest.fixture
def mock_graphrag_handler():
    """
    Mock GraphRAG handler for component tests.

    Returns:
        Mock GraphRAG handler with configurable responses
    """
    handler = AsyncMock()
    handler.execute.return_value = {
        "content": "Mock GraphRAG response",
        "enrichment": {
            "protocols": [
                {
                    "protocol_id": "test_protocol",
                    "protocol_name": "Test Protocol",
                    "similarity_score": 0.95,
                }
            ],
        },
    }
    return handler


@pytest.fixture
def mock_hunter_handler():
    """
    Mock Hunter AI handler for component tests.

    Returns:
        Mock Hunter AI handler with configurable responses
    """
    handler = AsyncMock()
    handler.execute.return_value = {
        "content": "Mock Hunter AI response",
        "enrichment": {
            "token_symbol": "ETH",
            "hunter_tool": "sentiment_analyzer",
            "sentiment_score": 0.75,
        },
    }
    return handler


@pytest.fixture
def mock_ultra_handler():
    """
    Mock ULTRA handler for component tests.

    Returns:
        Mock ULTRA handler with configurable responses
    """
    handler = AsyncMock()
    handler.execute.return_value = {
        "content": "Mock ULTRA response",
        "enrichment": {
            "ultra_tool": "arbitrage_scanner",
            "arb_opportunities": 3,
            "capital": 10000,
        },
    }
    return handler


@pytest.fixture
def mock_squad_handler():
    """
    Mock Agent Squad handler for component tests.

    Returns:
        Mock Agent Squad handler with configurable responses
    """
    handler = AsyncMock()
    handler.execute.return_value = {
        "content": "Mock Agent Squad response",
        "enrichment": {
            "task_type": "spec_generation",
            "workflow_type": "sequential",
            "agents_used": ["architect", "developer"],
        },
    }
    return handler


@pytest.fixture
def mock_chat_handler():
    """
    Mock general chat handler for component tests.

    Returns:
        Mock chat handler with configurable responses
    """
    handler = AsyncMock()
    handler.execute.return_value = {
        "content": "Mock chat response",
        "enrichment": None,
    }
    return handler
