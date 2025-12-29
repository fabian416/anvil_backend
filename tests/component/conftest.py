"""
Component test fixtures.

Provides fixtures for component-level testing:
- In-memory repositories (fast, isolated storage)
- Mock gateways (deterministic external API responses)
- Test data factories (convenient entity creation)
- Pre-populated test data (common test scenarios)

Usage:
    @pytest.mark.asyncio
    async def test_send_message(
        conversation_repository,
        message_repository,
        mock_llm_gateway,
        test_conversation,
    ):
        # Test uses fixtures automatically via dependency injection
        interactor = SendMessage(
            conversation_repo=conversation_repository,
            message_repo=message_repository,
            llm_gateway=mock_llm_gateway,
        )
        ...
"""

import pytest
import pytest_asyncio
from uuid import UUID

from tests.component.mocks.repositories import (
    InMemoryConversationRepository,
    InMemoryMessageRepository,
)
from tests.component.mocks.gateways import (
    MockLLMGateway,
    MockIntentDetectionGateway,
)
from tests.component.factories.chat_factories import (
    ConversationFactory,
    MessageFactory,
    UserFactory,
)


# ============================================================================
# Repository Fixtures (In-Memory)
# ============================================================================

@pytest.fixture
def conversation_repository():
    """
    In-memory conversation repository for component tests.

    Returns:
        InMemoryConversationRepository instance

    Example:
        async def test_create_conversation(conversation_repository):
            conversation = Conversation.create(user_id=123)
            await conversation_repository.add_conversation(conversation)
            retrieved = await conversation_repository.get_conversation(conversation.id)
            assert retrieved.id == conversation.id
    """
    return InMemoryConversationRepository()


@pytest.fixture
def message_repository():
    """
    In-memory message repository for component tests.

    Returns:
        InMemoryMessageRepository instance

    Example:
        async def test_save_message(message_repository):
            message = Message.create_user_message(conversation_id, "Hello")
            await message_repository.save(message)
            retrieved = await message_repository.get(message.id)
            assert retrieved.content == "Hello"
    """
    return InMemoryMessageRepository()


# ============================================================================
# Gateway Fixtures (Mocks)
# ============================================================================

@pytest.fixture
def mock_llm_gateway():
    """
    Mock LLM gateway with configurable responses.

    Returns:
        MockLLMGateway instance

    Example:
        async def test_with_llm(mock_llm_gateway):
            mock_llm_gateway.set_default_response("DeFi is...")
            response = await mock_llm_gateway.generate(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "What is DeFi?"}],
            )
            assert "DeFi" in response
    """
    gateway = MockLLMGateway()
    # Set sensible default response
    gateway.set_default_response(
        "This is a mock LLM response. "
        "Configure specific responses using gateway.set_default_response()."
    )
    return gateway


@pytest.fixture
def mock_intent_gateway():
    """
    Mock intent detection gateway.

    Returns:
        MockIntentDetectionGateway instance

    Example:
        async def test_classify_intent(mock_intent_gateway):
            mock_intent_gateway.set_default_intent({
                "agent_type": "HUNTER_AI",
                "confidence": 0.92,
                "reasoning": "Market sentiment query",
            })
            result = await mock_intent_gateway.classify("ETH sentiment?")
            assert result["agent_type"] == "HUNTER_AI"
    """
    gateway = MockIntentDetectionGateway()
    # Set sensible default intent
    gateway.set_default_intent({
        "agent_type": "CHAT",
        "confidence": 0.95,
        "reasoning": "General conversation",
    })
    return gateway


# ============================================================================
# Factory Fixtures
# ============================================================================

@pytest.fixture
def conversation_factory():
    """
    Factory for creating test conversations.

    Returns:
        ConversationFactory instance

    Example:
        def test_create_multiple_conversations(conversation_factory):
            conversations = conversation_factory.create_batch(count=5, user_id=123)
            assert len(conversations) == 5
            assert all(c.user_id == 123 for c in conversations)
    """
    return ConversationFactory()


@pytest.fixture
def message_factory():
    """
    Factory for creating test messages.

    Returns:
        MessageFactory instance

    Example:
        def test_create_conversation_history(message_factory, conversation):
            messages = message_factory.create_conversation_history(
                conversation_id=conversation.id,
                turns=[
                    ("Hello", "Hi! How can I help?"),
                    ("What is DeFi?", "DeFi is decentralized finance..."),
                ],
            )
            assert len(messages) == 4
    """
    return MessageFactory()


@pytest.fixture
def user_factory():
    """
    Factory for creating test users.

    Returns:
        UserFactory instance

    Example:
        def test_create_user(user_factory):
            user = user_factory.create(id=456, email="alice@example.com")
            assert user["id"] == 456
    """
    return UserFactory()


# ============================================================================
# Pre-Populated Test Data Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def test_user(user_factory):
    """
    Pre-created test user.

    Returns:
        User dictionary with id=123

    Example:
        async def test_with_user(test_user):
            assert test_user["id"] == 123
            assert test_user["email"] == "test@example.com"
    """
    return user_factory.create(
        id=123,
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )


@pytest_asyncio.fixture
async def test_conversation(
    conversation_repository,
    conversation_factory,
    test_user,
):
    """
    Pre-created test conversation.

    Creates a conversation for the test user and saves it to the repository.

    Returns:
        Conversation entity

    Example:
        async def test_with_conversation(test_conversation):
            assert test_conversation.user_id == 123
            assert test_conversation.title == "Test Conversation"
    """
    conversation = conversation_factory.create(
        user_id=test_user["id"],
        title="Test Conversation",
    )
    await conversation_repository.add_conversation(conversation)
    return conversation


@pytest_asyncio.fixture
async def conversation_with_messages(
    test_conversation,
    message_repository,
    message_factory,
):
    """
    Pre-created conversation with message history.

    Creates a conversation with 2 pre-existing messages:
    - User: "Hello"
    - Agent: "Hi! How can I help you?"

    Returns:
        Tuple of (conversation, messages)

    Example:
        async def test_with_history(conversation_with_messages):
            conversation, messages = conversation_with_messages
            assert len(messages) == 2
            assert messages[0].role == MessageRole.USER
            assert messages[1].role == MessageRole.AGENT
    """
    messages = message_factory.create_conversation_history(
        conversation_id=test_conversation.id,
        turns=[
            ("Hello", "Hi! How can I help you?"),
        ],
    )

    for msg in messages:
        await message_repository.save(msg)

    return test_conversation, messages


# ============================================================================
# Component Test Utilities
# ============================================================================

class ComponentTestContext:
    """
    Helper for component tests.

    Provides utilities for:
    - Setting up test scenarios
    - Verifying outcomes
    - Debugging failures

    Example:
        async def test_with_context(component_context):
            conversation, messages = await component_context.setup_conversation_scenario(
                user_id=123,
                num_messages=5,
            )
            await component_context.assert_message_count(conversation.id, 5)
    """

    def __init__(
        self,
        conversation_repo: InMemoryConversationRepository,
        message_repo: InMemoryMessageRepository,
    ):
        """
        Initialize test context.

        Args:
            conversation_repo: Conversation repository
            message_repo: Message repository
        """
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo

    async def setup_conversation_scenario(
        self,
        user_id: int,
        num_messages: int = 0,
    ):
        """
        Create a conversation with N messages.

        Args:
            user_id: User ID
            num_messages: Number of messages to create

        Returns:
            Tuple of (conversation, messages)

        Example:
            >>> conversation, messages = await context.setup_conversation_scenario(
            ...     user_id=123,
            ...     num_messages=4,
            ... )
        """
        from tests.component.factories.chat_factories import (
            ConversationFactory,
            MessageFactory,
        )

        conv_factory = ConversationFactory()
        msg_factory = MessageFactory()

        conversation = conv_factory.create(user_id=user_id)
        await self.conversation_repo.add_conversation(conversation)

        messages = []
        for i in range(num_messages):
            role = "user" if i % 2 == 0 else "agent"
            msg = msg_factory.create(
                conversation_id=conversation.id,
                role=role,
                content=f"Message {i+1}",
            )
            await self.message_repo.save(msg)
            messages.append(msg)

        return conversation, messages

    async def assert_message_count(
        self,
        conversation_id: UUID,
        expected_count: int,
    ):
        """
        Assert conversation has expected number of messages.

        Args:
            conversation_id: Conversation ID
            expected_count: Expected message count

        Raises:
            AssertionError: If counts don't match

        Example:
            >>> await context.assert_message_count(conversation.id, 5)
        """
        messages = await self.message_repo.get_by_conversation(conversation_id)
        actual_count = len(messages)
        assert actual_count == expected_count, \
            f"Expected {expected_count} messages, found {actual_count}"

    async def assert_last_message_content(
        self,
        conversation_id: UUID,
        expected_content: str,
    ):
        """
        Assert last message has expected content.

        Args:
            conversation_id: Conversation ID
            expected_content: Expected message content

        Raises:
            AssertionError: If content doesn't match

        Example:
            >>> await context.assert_last_message_content(
            ...     conversation.id,
            ...     "Hello",
            ... )
        """
        messages = await self.message_repo.get_by_conversation(conversation_id)
        assert len(messages) > 0, "No messages found"
        last_message = messages[-1]
        assert last_message.content == expected_content, \
            f"Expected '{expected_content}', got '{last_message.content}'"


@pytest.fixture
def component_context(
    conversation_repository,
    message_repository,
):
    """
    Component test context helper.

    Returns:
        ComponentTestContext instance

    Example:
        async def test_with_context(component_context):
            conversation, messages = await component_context.setup_conversation_scenario(
                user_id=123,
                num_messages=5,
            )
            await component_context.assert_message_count(conversation.id, 5)
    """
    return ComponentTestContext(
        conversation_repo=conversation_repository,
        message_repo=message_repository,
    )
