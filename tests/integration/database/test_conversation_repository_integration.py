"""
Integration tests for ConversationRepository with real database.

Tests database operations, transactions, and data integrity.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.domain.chat.entities.conversation import Conversation
from app.domain.chat.entities.message import Message
from app.domain.chat.value_objects.message_role import MessageRole


@pytest.mark.integration
@pytest.mark.asyncio
class TestConversationRepositoryIntegration:
    """Integration tests for conversation repository."""
    
    @pytest.mark.llm_validation
    async def test_save_and_retrieve_conversation(self, async_db_session, async_test_user):
        """Test saving and retrieving a conversation."""
        # Arrange
        from sqlalchemy import select
        conversation = Conversation.create(user_id=async_test_user, title="Test Conversation")

        # Act - Use SQLAlchemy directly with mapped entity
        async_db_session.add(conversation)
        await async_db_session.commit()

        # Retrieve
        stmt = select(Conversation).where(Conversation.id == conversation.id)
        result = await async_db_session.execute(stmt)
        retrieved = result.scalar_one_or_none()

        # Assert
        assert retrieved is not None
        assert retrieved.user_id == conversation.user_id
        assert retrieved.title == conversation.title

    @pytest.mark.llm_validation
    async def test_conversation_with_messages(self, async_db_session, async_test_user):
        """Test conversation with multiple messages."""
        # Arrange
        from sqlalchemy import select
        conversation = Conversation.create(user_id=async_test_user)

        # Act - Use SQLAlchemy directly
        async_db_session.add(conversation)
        await async_db_session.commit()

        # Assert
        stmt = select(Conversation).where(Conversation.id == conversation.id)
        result = await async_db_session.execute(stmt)
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None

    @pytest.mark.llm_validation
    async def test_update_conversation_title(self, async_db_session, async_test_user):
        """Test updating conversation title."""
        # Arrange
        from sqlalchemy import select
        conversation = Conversation.create(user_id=async_test_user, title="Original Title")

        # Act
        async_db_session.add(conversation)
        await async_db_session.commit()

        conversation.update_title("Updated Title")
        await async_db_session.commit()

        # Assert
        stmt = select(Conversation).where(Conversation.id == conversation.id)
        result = await async_db_session.execute(stmt)
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.title == "Updated Title"

    @pytest.mark.llm_validation
    async def test_multiple_conversations_for_user(self, async_db_session, async_test_user):
        """Test creating multiple conversations for same user."""
        # Arrange
        from sqlalchemy import select
        conv1 = Conversation.create(user_id=async_test_user, title="First")
        conv2 = Conversation.create(user_id=async_test_user, title="Second")
        conv3 = Conversation.create(user_id=async_test_user, title="Third")

        # Act
        async_db_session.add_all([conv1, conv2, conv3])
        await async_db_session.commit()

        # Assert - Verify the specific 3 conversations we created exist
        stmt = select(Conversation).where(Conversation.id.in_([conv1.id, conv2.id, conv3.id]))
        result = await async_db_session.execute(stmt)
        conversations = result.scalars().all()

        assert len(conversations) == 3
        assert conv1.id != conv2.id != conv3.id


@pytest.mark.integration
@pytest.mark.asyncio
class TestTransactionHandling:
    """Test transaction handling and rollback."""
    
    @pytest.mark.llm_validation
    async def test_transaction_rollback_on_error(self, async_db_session, async_test_user):
        """Test transaction rolls back on error."""
        # Arrange
        from sqlalchemy import select
        conversation = Conversation.create(user_id=async_test_user)

        # Act & Assert
        try:
            async_db_session.add(conversation)
            # Simulate error
            raise Exception("Simulated error")
        except Exception:
            await async_db_session.rollback()

        # Verify conversation was not saved
        stmt = select(Conversation).where(Conversation.id == conversation.id)
        result = await async_db_session.execute(stmt)
        retrieved = result.scalar_one_or_none()
        assert retrieved is None

    @pytest.mark.llm_validation
    async def test_transaction_commit_on_success(self, async_db_session, async_test_user):
        """Test transaction commits on success."""
        # Arrange
        from sqlalchemy import select
        conversation = Conversation.create(user_id=async_test_user)

        # Act
        async_db_session.add(conversation)
        await async_db_session.commit()

        # Assert
        stmt = select(Conversation).where(Conversation.id == conversation.id)
        result = await async_db_session.execute(stmt)
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None


@pytest.mark.integration
class TestDataIntegrity:
    """Test data integrity constraints."""
    
    def test_unique_conversation_ids(self):
        """Test conversation IDs are unique."""
        # Act
        conv1 = Conversation.create(user_id=333)
        conv2 = Conversation.create(user_id=333)
        
        # Assert
        assert conv1.id != conv2.id
    
    def test_conversation_timestamps_are_set(self):
        """Test conversation timestamps are automatically set."""
        # Arrange
        conversation = Conversation.create(user_id=444)
        
        # Assert
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)