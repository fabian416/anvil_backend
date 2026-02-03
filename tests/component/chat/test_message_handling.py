"""
Component tests for message handling.

Tests message commands and queries in isolation:
- SendMessage command
- GetMessages query

Performance target: <50ms per test (vs 500-2000ms for HTTP integration tests).
"""

import pytest
from uuid import uuid4

from app.domain.chat.value_objects.message_role import MessageRole


@pytest.mark.asyncio
class TestSendMessage:
    """Component tests for SendMessage command."""

    async def test_send_message_returns_response(
        self,
        send_message_command,
        test_conversation,
        test_user,
        mock_agent_gateway,
    ):
        """
        WHEN user sends message
        THEN system SHALL return user message and agent response
        """
        # Arrange
        mock_agent_gateway.process_message.return_value = (
            "DeFi is decentralized finance."
        )

        # Act
        user_message, agent_message = await send_message_command.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
            content="What is DeFi?",
        )

        # Assert
        assert user_message.content == "What is DeFi?"
        assert user_message.role == MessageRole.USER
        assert agent_message.content == "DeFi is decentralized finance."
        assert agent_message.role == MessageRole.AGENT

    async def test_send_message_to_nonexistent_conversation(
        self,
        send_message_command,
        test_user,
    ):
        """
        WHEN user sends message to non-existent conversation
        THEN system SHALL raise ConversationNotFoundError
        """
        # Arrange
        non_existent_id = uuid4()

        # Act & Assert
        from app.domain.exceptions.chat import ConversationNotFoundError

        with pytest.raises(ConversationNotFoundError):
            await send_message_command.execute(
                user_id=test_user["id"],
                conversation_id=non_existent_id,
                content="Hello",
            )

    async def test_send_message_access_denied(
        self,
        send_message_command,
        test_conversation,
    ):
        """
        WHEN user sends message to another user's conversation
        THEN system SHALL raise ConversationAccessDeniedError
        """
        # Act & Assert
        from app.domain.exceptions.chat import ConversationAccessDeniedError

        with pytest.raises(ConversationAccessDeniedError):
            await send_message_command.execute(
                user_id=999,  # Different user
                conversation_id=test_conversation.id,
                content="Hello",
            )

    async def test_send_empty_message(
        self,
        send_message_command,
        test_conversation,
        test_user,
        mock_agent_gateway,
    ):
        """
        WHEN user sends empty message
        THEN system SHALL still process it (validation happens at presentation layer)
        """
        # Arrange
        mock_agent_gateway.process_message.return_value = (
            "I see you sent an empty message."
        )

        # Act
        user_message, agent_message = await send_message_command.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
            content="",
        )

        # Assert: Command processes it (HTTP layer should validate)
        assert user_message.content == ""
        assert agent_message.content is not None

    async def test_send_message_updates_conversation_timestamp(
        self,
        send_message_command,
        conversation_repository,
        test_conversation,
        test_user,
        mock_agent_gateway,
    ):
        """
        WHEN message is sent
        THEN conversation timestamp SHALL be updated
        """
        # Arrange
        original_updated_at = test_conversation.updated_at
        mock_agent_gateway.process_message.return_value = "Response"

        # Act
        await send_message_command.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
            content="Hello",
        )

        # Assert: Conversation timestamp updated
        updated_conversation = await conversation_repository.get_conversation(
            test_conversation.id
        )
        assert updated_conversation.updated_at > original_updated_at


@pytest.mark.asyncio
class TestGetMessages:
    """Component tests for GetMessages query."""

    async def test_get_messages_returns_array(
        self,
        get_messages_query,
        test_conversation,
        test_user,
        message_factory,
        conversation_repository,
    ):
        """
        WHEN user gets messages
        THEN system SHALL return array of messages
        """
        # Arrange: Create messages
        messages = message_factory.create_conversation_history(
            conversation_id=test_conversation.id,
            turns=[
                ("Hello", "Hi! How can I help?"),
                ("What is DeFi?", "DeFi is decentralized finance..."),
            ],
        )
        for msg in messages:
            await conversation_repository.add_message(msg)

        # Act
        result = await get_messages_query.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 4  # 2 turns = 4 messages
        assert result[0].role == MessageRole.USER
        assert result[1].role == MessageRole.AGENT

    async def test_get_messages_access_denied(
        self,
        get_messages_query,
        test_conversation,
    ):
        """
        WHEN user requests messages from another user's conversation
        THEN system SHALL raise ValueError
        """
        # Act & Assert
        with pytest.raises(ValueError, match="does not belong to user"):
            await get_messages_query.execute(
                user_id=999,  # Different user
                conversation_id=test_conversation.id,
            )

    async def test_get_messages_with_limit(
        self,
        get_messages_query,
        test_conversation,
        test_user,
        message_factory,
        conversation_repository,
    ):
        """
        WHEN user gets messages with limit
        THEN system SHALL return at most that many messages
        """
        # Arrange: Create 10 messages
        messages = message_factory.create_batch(
            count=10,
            conversation_id=test_conversation.id,
        )
        for msg in messages:
            await conversation_repository.add_message(msg)

        # Act
        result = await get_messages_query.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
            limit=5,
        )

        # Assert
        assert len(result) <= 5


@pytest.mark.asyncio
class TestMessageValidation:
    """Component tests for message content handling."""

    async def test_message_with_special_characters(
        self,
        send_message_command,
        test_conversation,
        test_user,
        mock_agent_gateway,
    ):
        """
        WHEN user sends message with special characters
        THEN system SHALL accept and process
        """
        # Arrange
        special_content = "What about 🚀 DeFi? Special chars: <>&\"'"
        mock_agent_gateway.process_message.return_value = "Response to special chars"

        # Act
        user_message, agent_message = await send_message_command.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
            content=special_content,
        )

        # Assert
        assert user_message.content == special_content
        assert agent_message is not None

    async def test_message_with_unicode(
        self,
        send_message_command,
        test_conversation,
        test_user,
        mock_agent_gateway,
    ):
        """
        WHEN user sends message with unicode
        THEN system SHALL accept and process
        """
        # Arrange
        unicode_content = "什么是去中心化金融？"
        mock_agent_gateway.process_message.return_value = "Response to Chinese query"

        # Act
        user_message, agent_message = await send_message_command.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
            content=unicode_content,
        )

        # Assert
        assert user_message.content == unicode_content
        assert agent_message is not None

    async def test_very_long_message(
        self,
        send_message_command,
        test_conversation,
        test_user,
        mock_agent_gateway,
    ):
        """
        WHEN user sends very long message
        THEN system SHALL accept and process (truncation at presentation layer)
        """
        # Arrange
        long_message = "A" * 10000
        mock_agent_gateway.process_message.return_value = "Response to long message"

        # Act
        user_message, agent_message = await send_message_command.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
            content=long_message,
        )

        # Assert: Command processes it (HTTP layer handles truncation)
        assert user_message.content == long_message
        assert agent_message is not None
