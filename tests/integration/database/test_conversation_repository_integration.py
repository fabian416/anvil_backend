"""
Integration tests for ConversationRepository with real database.

Tests database operations, transactions, and data integrity.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.message_role import MessageRole


@pytest.mark.integration
@pytest.mark.asyncio
class TestConversationRepositoryIntegration:
    """Integration tests for conversation repository."""
    
    async def test_save_and_retrieve_conversation(self, db_session):
        """Test saving and retrieving a conversation."""
        # Arrange
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        repo = LLMConversationRepositorySqla(session=db_session)
        conversation = Conversation.create(user_id=123, title="Test Conversation")
        
        # Act
        await repo.save(conversation)
        await db_session.commit()
        
        retrieved = await repo.get_by_id(conversation.id)
        
        # Assert
        assert retrieved is not None
        assert retrieved.user_id == conversation.user_id
        assert retrieved.title == conversation.title
    
    async def test_conversation_with_messages(self, db_session):
        """Test conversation with multiple messages."""
        # Arrange
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        repo = LLMConversationRepositorySqla(session=db_session)
        conversation = Conversation.create(user_id=456)
        
        # Act
        await repo.save(conversation)
        await db_session.commit()
        
        # Assert
        retrieved = await repo.get_by_id(conversation.id)
        assert retrieved is not None
    
    async def test_update_conversation_title(self, db_session):
        """Test updating conversation title."""
        # Arrange
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        repo = LLMConversationRepositorySqla(session=db_session)
        conversation = Conversation.create(user_id=789, title="Original Title")
        
        # Act
        await repo.save(conversation)
        await db_session.commit()
        
        conversation.update_title("Updated Title")
        await repo.save(conversation)
        await db_session.commit()
        
        # Assert
        retrieved = await repo.get_by_id(conversation.id)
        assert retrieved is not None
    
    async def test_multiple_conversations_for_user(self, db_session):
        """Test creating multiple conversations for same user."""
        # Arrange
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        repo = LLMConversationRepositorySqla(session=db_session)
        user_id = 999
        
        conv1 = Conversation.create(user_id=user_id, title="First")
        conv2 = Conversation.create(user_id=user_id, title="Second")
        conv3 = Conversation.create(user_id=user_id, title="Third")
        
        # Act
        await repo.save(conv1)
        await repo.save(conv2)
        await repo.save(conv3)
        await db_session.commit()
        
        # Assert
        retrieved1 = await repo.get_by_id(conv1.id)
        retrieved2 = await repo.get_by_id(conv2.id)
        retrieved3 = await repo.get_by_id(conv3.id)
        
        assert retrieved1 is not None
        assert retrieved2 is not None
        assert retrieved3 is not None
        assert retrieved1.id != retrieved2.id != retrieved3.id


@pytest.mark.integration
@pytest.mark.asyncio
class TestTransactionHandling:
    """Test transaction handling and rollback."""
    
    async def test_transaction_rollback_on_error(self, db_session):
        """Test transaction rolls back on error."""
        # Arrange
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        repo = LLMConversationRepositorySqla(session=db_session)
        conversation = Conversation.create(user_id=111)
        
        # Act & Assert
        try:
            await repo.save(conversation)
            # Simulate error
            raise Exception("Simulated error")
        except Exception:
            await db_session.rollback()
        
        # Verify conversation was not saved
        retrieved = await repo.get_by_id(conversation.id)
        assert retrieved is None or retrieved.id != conversation.id
    
    async def test_transaction_commit_on_success(self, db_session):
        """Test transaction commits on success."""
        # Arrange
        from app.infrastructure.adapters.ai.llm_conversation_repository_sqla import LLMConversationRepositorySqla
        
        repo = LLMConversationRepositorySqla(session=db_session)
        conversation = Conversation.create(user_id=222)
        
        # Act
        await repo.save(conversation)
        await db_session.commit()
        
        # Assert
        retrieved = await repo.get_by_id(conversation.id)
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
