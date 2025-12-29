"""
Component tests for conversation lifecycle.

Tests conversation commands and queries in isolation:
- CreateConversation command
- ListConversations query
- GetConversation query

Performance target: <50ms per test (vs 500-2000ms for HTTP integration tests).
"""

import pytest
from uuid import uuid4

from app.domain.exceptions.chat import ConversationNotFoundError


@pytest.mark.asyncio
class TestCreateConversation:
    """Component tests for CreateConversation command."""

    async def test_create_conversation_returns_id(
        self,
        create_conversation_command,
        test_user,
    ):
        """
        WHEN user creates conversation
        THEN system SHALL return conversation with ID
        """
        # Act
        conversation = await create_conversation_command.execute(
            user_id=test_user["id"],
            title="Test Conversation",
        )

        # Assert
        assert conversation.id is not None
        assert conversation.user_id == test_user["id"]
        assert conversation.title == "Test Conversation"

    async def test_create_conversation_without_title(
        self,
        create_conversation_command,
        test_user,
    ):
        """
        WHEN user creates conversation without title
        THEN system SHALL create conversation with null title
        """
        # Act
        conversation = await create_conversation_command.execute(
            user_id=test_user["id"],
            title=None,
        )

        # Assert
        assert conversation.id is not None
        assert conversation.user_id == test_user["id"]
        assert conversation.title is None

    async def test_create_conversation_saves_to_repository(
        self,
        create_conversation_command,
        conversation_repository,
        test_user,
    ):
        """
        WHEN conversation is created
        THEN it SHALL be persisted to repository
        """
        # Act
        conversation = await create_conversation_command.execute(
            user_id=test_user["id"],
            title="Persisted Conversation",
        )

        # Assert: Can retrieve from repository
        retrieved = await conversation_repository.get_conversation(conversation.id)
        assert retrieved is not None
        assert retrieved.id == conversation.id
        assert retrieved.title == "Persisted Conversation"

    async def test_create_multiple_conversations_for_user(
        self,
        create_conversation_command,
        conversation_repository,
        test_user,
    ):
        """
        WHEN user creates multiple conversations
        THEN all SHALL be persisted with unique IDs
        """
        # Act: Create 3 conversations
        conv1 = await create_conversation_command.execute(test_user["id"], "First")
        conv2 = await create_conversation_command.execute(test_user["id"], "Second")
        conv3 = await create_conversation_command.execute(test_user["id"], "Third")

        # Assert: All have unique IDs
        assert conv1.id != conv2.id
        assert conv2.id != conv3.id
        assert conv1.id != conv3.id

        # Assert: All can be retrieved
        retrieved = await conversation_repository.list_conversations(test_user["id"])
        assert len(retrieved) == 3


@pytest.mark.asyncio
class TestListConversations:
    """Component tests for ListConversations query."""

    async def test_list_conversations_returns_array(
        self,
        list_conversations_query,
        conversation_factory,
        conversation_repository,
        test_user,
    ):
        """
        WHEN user lists conversations
        THEN system SHALL return array of conversations
        """
        # Arrange: Create conversations
        convs = conversation_factory.create_batch(count=3, user_id=test_user["id"])
        for conv in convs:
            await conversation_repository.add_conversation(conv)

        # Act
        result = await list_conversations_query.execute(user_id=test_user["id"])

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(c.user_id == test_user["id"] for c in result)

    async def test_list_conversations_with_pagination(
        self,
        list_conversations_query,
        conversation_factory,
        conversation_repository,
        test_user,
    ):
        """
        WHEN user lists conversations with pagination
        THEN system SHALL return paginated results
        """
        # Arrange: Create 10 conversations
        convs = conversation_factory.create_batch(count=10, user_id=test_user["id"])
        for conv in convs:
            await conversation_repository.add_conversation(conv)

        # Act: Get first page (limit=5, offset=0)
        page1 = await list_conversations_query.execute(
            user_id=test_user["id"],
            limit=5,
            offset=0,
        )

        # Act: Get second page (limit=5, offset=5)
        page2 = await list_conversations_query.execute(
            user_id=test_user["id"],
            limit=5,
            offset=5,
        )

        # Assert
        assert len(page1) == 5
        assert len(page2) == 5
        # Verify no overlap (different conversations)
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    async def test_list_conversations_filters_by_user(
        self,
        list_conversations_query,
        conversation_factory,
        conversation_repository,
    ):
        """
        WHEN multiple users have conversations
        THEN list_conversations SHALL return only user's conversations
        """
        # Arrange: Create conversations for two users
        user1_convs = conversation_factory.create_batch(count=3, user_id=123)
        user2_convs = conversation_factory.create_batch(count=2, user_id=456)

        for conv in user1_convs + user2_convs:
            await conversation_repository.add_conversation(conv)

        # Act: List for user 123
        result = await list_conversations_query.execute(user_id=123)

        # Assert: Only user 123's conversations
        assert len(result) == 3
        assert all(c.user_id == 123 for c in result)


@pytest.mark.asyncio
class TestGetConversation:
    """Component tests for GetConversation query."""

    async def test_get_conversation_by_id(
        self,
        get_conversation_query,
        test_conversation,
        test_user,
    ):
        """
        WHEN user gets conversation by ID
        THEN system SHALL return conversation details
        """
        # Act
        result = await get_conversation_query.execute(
            user_id=test_user["id"],
            conversation_id=test_conversation.id,
        )

        # Assert
        assert result is not None
        assert result.id == test_conversation.id
        assert result.user_id == test_user["id"]

    async def test_get_conversation_not_found(
        self,
        get_conversation_query,
        test_user,
    ):
        """
        WHEN user requests non-existent conversation
        THEN system SHALL return None
        """
        # Act
        non_existent_id = uuid4()
        result = await get_conversation_query.execute(
            user_id=test_user["id"],
            conversation_id=non_existent_id,
        )

        # Assert
        assert result is None

    async def test_get_conversation_access_denied(
        self,
        get_conversation_query,
        test_conversation,
    ):
        """
        WHEN user requests another user's conversation
        THEN system SHALL raise ValueError
        """
        # Act & Assert
        with pytest.raises(ValueError, match="does not belong to user"):
            await get_conversation_query.execute(
                user_id=999,  # Different user
                conversation_id=test_conversation.id,
            )


@pytest.mark.asyncio
class TestConversationPagination:
    """Component tests for conversation pagination."""

    async def test_pagination_limit_works(
        self,
        list_conversations_query,
        conversation_factory,
        conversation_repository,
        test_user,
    ):
        """
        WHEN user specifies limit
        THEN system SHALL return at most that many items
        """
        # Arrange: Create 10 conversations
        convs = conversation_factory.create_batch(count=10, user_id=test_user["id"])
        for conv in convs:
            await conversation_repository.add_conversation(conv)

        # Act
        result = await list_conversations_query.execute(
            user_id=test_user["id"],
            limit=5,
        )

        # Assert
        assert len(result) <= 5

    async def test_pagination_offset_skips_items(
        self,
        list_conversations_query,
        conversation_factory,
        conversation_repository,
        test_user,
    ):
        """
        WHEN user specifies offset
        THEN system SHALL skip that many items
        """
        # Arrange: Create 10 conversations
        convs = conversation_factory.create_batch(count=10, user_id=test_user["id"])
        for conv in convs:
            await conversation_repository.add_conversation(conv)

        # Act: Get all (no offset)
        all_convs = await list_conversations_query.execute(
            user_id=test_user["id"],
            limit=10,
            offset=0,
        )

        # Act: Skip first 5
        skipped = await list_conversations_query.execute(
            user_id=test_user["id"],
            limit=10,
            offset=5,
        )

        # Assert: Skipped result doesn't include first 5
        skipped_ids = {c.id for c in skipped}
        first_5_ids = {c.id for c in all_convs[:5]}
        assert len(skipped_ids.intersection(first_5_ids)) == 0
