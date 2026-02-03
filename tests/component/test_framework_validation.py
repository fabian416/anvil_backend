"""
Component Test Framework Validation.

These tests validate that the component test infrastructure works correctly.
They serve as examples of component test patterns and verify all fixtures.

Purpose:
- Validate in-memory repositories work correctly
- Validate mock gateways work correctly
- Validate test data factories work correctly
- Validate component fixtures wire together properly
- Serve as examples for writing component tests

Performance Target: <0.5 seconds total (all tests)
"""

import pytest
from uuid import uuid4

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.chat.value_objects.message_role import MessageRole


# ============================================================================
# Repository Validation Tests
# ============================================================================


@pytest.mark.asyncio
class TestInMemoryRepositories:
    """Validate in-memory repository implementations."""

    async def test_conversation_repository_save_and_retrieve(
        self,
        conversation_repository,
        conversation_factory,
    ):
        """
        WHEN conversation is saved to repository
        THEN it can be retrieved by ID
        """
        # Arrange
        conversation = conversation_factory.create(user_id=123, title="Test")

        # Act
        await conversation_repository.add_conversation(conversation)
        retrieved = await conversation_repository.get_conversation(conversation.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == conversation.id
        assert retrieved.user_id == 123
        assert retrieved.title == "Test"

    async def test_conversation_repository_list_by_user(
        self,
        conversation_repository,
        conversation_factory,
    ):
        """
        WHEN multiple conversations exist for a user
        THEN list_conversations returns only that user's conversations
        """
        # Arrange: Create conversations for two users
        user1_convs = conversation_factory.create_batch(count=3, user_id=123)
        user2_convs = conversation_factory.create_batch(count=2, user_id=456)

        for conv in user1_convs + user2_convs:
            await conversation_repository.add_conversation(conv)

        # Act
        user1_retrieved = await conversation_repository.list_conversations(user_id=123)

        # Assert
        assert len(user1_retrieved) == 3
        assert all(c.user_id == 123 for c in user1_retrieved)

    async def test_message_repository_save_and_retrieve(
        self,
        message_repository,
        message_factory,
        test_conversation,
    ):
        """
        WHEN message is saved to repository
        THEN it can be retrieved by ID
        """
        # Arrange
        message = message_factory.create_user_message(
            conversation_id=test_conversation.id,
            content="Hello, world!",
        )

        # Act
        await message_repository.save(message)
        retrieved = await message_repository.get(message.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == message.id
        assert retrieved.content == "Hello, world!"
        assert retrieved.role == MessageRole.USER

    async def test_message_repository_get_by_conversation(
        self,
        message_repository,
        message_factory,
        test_conversation,
    ):
        """
        WHEN multiple messages exist for a conversation
        THEN get_by_conversation returns them in chronological order
        """
        # Arrange: Create conversation history
        messages = message_factory.create_conversation_history(
            conversation_id=test_conversation.id,
            turns=[
                ("Hello", "Hi! How can I help?"),
                ("What is DeFi?", "DeFi is decentralized finance..."),
            ],
        )

        for msg in messages:
            await message_repository.save(msg)

        # Act
        retrieved = await message_repository.get_by_conversation(
            conversation_id=test_conversation.id,
        )

        # Assert
        assert len(retrieved) == 4  # 2 turns = 4 messages
        assert retrieved[0].role == MessageRole.USER
        assert retrieved[0].content == "Hello"
        assert retrieved[1].role == MessageRole.AGENT
        assert retrieved[1].content == "Hi! How can I help?"

    async def test_repository_isolation(
        self,
        conversation_repository,
        conversation_factory,
    ):
        """
        WHEN conversation is modified after retrieval
        THEN stored entity is not affected (deep copy isolation)
        """
        # Arrange
        conversation = conversation_factory.create(user_id=123, title="Original")
        await conversation_repository.add_conversation(conversation)

        # Act: Retrieve and modify
        retrieved = await conversation_repository.get_conversation(conversation.id)
        retrieved.title = "Modified"

        # Assert: Original is unchanged
        original = await conversation_repository.get_conversation(conversation.id)
        assert original.title == "Original"  # Deep copy protection!


# ============================================================================
# Gateway Validation Tests
# ============================================================================


@pytest.mark.asyncio
class TestMockGateways:
    """Validate mock gateway implementations."""

    async def test_llm_gateway_default_response(self, mock_llm_gateway):
        """
        WHEN LLM gateway is called with default configuration
        THEN it returns the default response
        """
        # Arrange
        mock_llm_gateway.set_default_response("DeFi is decentralized finance.")

        # Act
        response = await mock_llm_gateway.generate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "What is DeFi?"}],
        )

        # Assert
        assert response == "DeFi is decentralized finance."

    async def test_llm_gateway_queued_responses(self, mock_llm_gateway):
        """
        WHEN multiple responses are queued
        THEN they are returned in FIFO order
        """
        # Arrange
        mock_llm_gateway.queue_response("First response")
        mock_llm_gateway.queue_response("Second response")

        # Act
        response1 = await mock_llm_gateway.generate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )
        response2 = await mock_llm_gateway.generate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello again"}],
        )

        # Assert
        assert response1 == "First response"
        assert response2 == "Second response"

    async def test_llm_gateway_call_history(self, mock_llm_gateway):
        """
        WHEN LLM gateway is called multiple times
        THEN call history is tracked correctly
        """
        # Arrange & Act
        await mock_llm_gateway.generate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
        )
        await mock_llm_gateway.generate(
            model="claude-sonnet-4",
            messages=[{"role": "user", "content": "Goodbye"}],
            temperature=0.9,
        )

        # Assert
        history = mock_llm_gateway.get_call_history()
        assert len(history) == 2
        assert history[0]["model"] == "gpt-4o-mini"
        assert history[0]["temperature"] == 0.7
        assert history[1]["model"] == "claude-sonnet-4"
        assert history[1]["temperature"] == 0.9

    async def test_llm_gateway_assertions(self, mock_llm_gateway):
        """
        WHEN using gateway assertion helpers
        THEN they correctly validate call patterns
        """
        # Act
        await mock_llm_gateway.generate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Test"}],
        )

        # Assert
        mock_llm_gateway.assert_called_once()
        mock_llm_gateway.assert_called_with(model="gpt-4o-mini")

    async def test_intent_gateway_default_intent(self, mock_intent_gateway):
        """
        WHEN intent gateway is called with default configuration
        THEN it returns the default intent
        """
        # Arrange
        mock_intent_gateway.set_default_intent({
            "agent_type": "HUNTER_AI",
            "confidence": 0.92,
            "reasoning": "Market sentiment query",
        })

        # Act
        result = await mock_intent_gateway.classify("ETH sentiment?")

        # Assert
        assert result["agent_type"] == "HUNTER_AI"
        assert result["confidence"] == 0.92


# ============================================================================
# Factory Validation Tests
# ============================================================================


class TestFactories:
    """Validate test data factory implementations."""

    def test_conversation_factory_creates_with_defaults(self, conversation_factory):
        """
        WHEN conversation is created without arguments
        THEN sensible defaults are used
        """
        # Act
        conversation = conversation_factory.create()

        # Assert
        assert conversation.id is not None
        assert conversation.user_id == 123  # Default user_id
        assert conversation.title == "Test Conversation"
        assert conversation.created_at is not None

    def test_conversation_factory_creates_with_overrides(self, conversation_factory):
        """
        WHEN conversation is created with custom values
        THEN those values are used
        """
        # Act
        conversation = conversation_factory.create(
            user_id=456,
            title="Custom Title",
        )

        # Assert
        assert conversation.user_id == 456
        assert conversation.title == "Custom Title"

    def test_conversation_factory_batch_creation(self, conversation_factory):
        """
        WHEN creating batch of conversations
        THEN all conversations are created with same parameters
        """
        # Act
        conversations = conversation_factory.create_batch(
            count=5,
            user_id=789,
        )

        # Assert
        assert len(conversations) == 5
        assert all(c.user_id == 789 for c in conversations)
        # Each should have unique ID
        ids = {c.id for c in conversations}
        assert len(ids) == 5

    def test_message_factory_creates_user_message(self, message_factory):
        """
        WHEN creating user message
        THEN role is set to USER
        """
        # Act
        conversation_id = uuid4()
        message = message_factory.create_user_message(
            conversation_id=conversation_id,
            content="Hello",
        )

        # Assert
        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.conversation_id == conversation_id

    def test_message_factory_creates_conversation_history(self, message_factory):
        """
        WHEN creating conversation history
        THEN messages alternate between user and agent
        """
        # Act
        conversation_id = uuid4()
        messages = message_factory.create_conversation_history(
            conversation_id=conversation_id,
            turns=[
                ("Hello", "Hi!"),
                ("How are you?", "I'm good, thanks!"),
            ],
        )

        # Assert
        assert len(messages) == 4
        assert messages[0].role == MessageRole.USER
        assert messages[0].content == "Hello"
        assert messages[1].role == MessageRole.AGENT
        assert messages[1].content == "Hi!"
        assert messages[2].role == MessageRole.USER
        assert messages[2].content == "How are you?"
        assert messages[3].role == MessageRole.AGENT
        assert messages[3].content == "I'm good, thanks!"


# ============================================================================
# Fixture Integration Tests
# ============================================================================


@pytest.mark.asyncio
class TestFixtureIntegration:
    """Validate that fixtures work together correctly."""

    async def test_pre_populated_test_user(self, test_user):
        """
        WHEN using test_user fixture
        THEN pre-created user is available
        """
        assert test_user["id"] == 123
        assert test_user["email"] == "test@example.com"

    async def test_pre_populated_test_conversation(
        self,
        test_conversation,
        conversation_repository,
    ):
        """
        WHEN using test_conversation fixture
        THEN pre-created conversation is available and persisted
        """
        # Assert: Fixture created conversation
        assert test_conversation.id is not None
        assert test_conversation.user_id == 123

        # Assert: Conversation is in repository
        retrieved = await conversation_repository.get_conversation(test_conversation.id)
        assert retrieved is not None

    async def test_conversation_with_messages_fixture(
        self,
        conversation_with_messages,
        message_repository,
    ):
        """
        WHEN using conversation_with_messages fixture
        THEN conversation with pre-populated messages is available
        """
        # Arrange
        conversation, messages = conversation_with_messages

        # Assert: Messages were created
        assert len(messages) == 2

        # Assert: Messages are in repository
        retrieved = await message_repository.get_by_conversation(
            conversation.id,
        )
        assert len(retrieved) == 2

    async def test_component_context_setup_scenario(self, component_context):
        """
        WHEN using component_context to setup scenario
        THEN conversation and messages are created correctly
        """
        # Act
        conversation, messages = await component_context.setup_conversation_scenario(
            user_id=999,
            num_messages=6,
        )

        # Assert
        assert conversation.user_id == 999
        assert len(messages) == 6

    async def test_component_context_assertions(
        self,
        component_context,
        test_conversation,
        message_repository,
        message_factory,
    ):
        """
        WHEN using component_context assertion methods
        THEN they correctly validate state
        """
        # Arrange: Add 3 messages
        messages = message_factory.create_batch(
            count=3,
            conversation_id=test_conversation.id,
        )
        for msg in messages:
            await message_repository.save(msg)

        # Act & Assert
        await component_context.assert_message_count(test_conversation.id, 3)

        # Add one more
        last_msg = message_factory.create(
            conversation_id=test_conversation.id,
            content="Last message",
        )
        await message_repository.save(last_msg)

        # Assert
        await component_context.assert_last_message_content(
            test_conversation.id,
            "Last message",
        )
