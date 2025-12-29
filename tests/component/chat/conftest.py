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
