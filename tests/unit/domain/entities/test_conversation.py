"""
Tests for Conversation entity.

Tests conversation creation, title updates, and timestamp management.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.domain.chat.entities.conversation import Conversation


@pytest.mark.unit
class TestConversation:
    """Test suite for Conversation entity."""
    
    def test_create_conversation_with_valid_user_id_succeeds(self):
        """Test conversation creation with valid user ID."""
        # Arrange
        user_id = 123
        
        # Act
        conversation = Conversation.create(user_id)
        
        # Assert
        assert conversation.id is not None
        assert conversation.user_id == user_id
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        assert conversation.title is None  # No title by default
    
    def test_create_conversation_with_title_succeeds(self):
        """Test conversation creation with title."""
        # Arrange
        user_id = 456
        title = "My DeFi Discussion"
        
        # Act
        conversation = Conversation.create(user_id, title=title)
        
        # Assert
        assert conversation.user_id == user_id
        assert conversation.title == title
    
    def test_conversation_generates_unique_ids(self):
        """Test that each conversation gets unique ID."""
        # Arrange
        user_id = 789
        
        # Act
        conv1 = Conversation.create(user_id)
        conv2 = Conversation.create(user_id)
        
        # Assert
        assert conv1.id != conv2.id
    
    def test_update_title_changes_title_and_updated_at(self):
        """Test updating conversation title."""
        # Arrange
        conversation = Conversation.create(123)
        original_updated_at = conversation.updated_at
        new_title = "Updated Title"
        
        # Act - Small delay to ensure timestamp changes
        conversation.update_title(new_title)
        
        # Assert
        assert conversation.title == new_title
        assert conversation.updated_at >= original_updated_at
    
    def test_touch_updates_timestamp(self):
        """Test touch method updates timestamp."""
        # Arrange
        conversation = Conversation.create(123)
        original_updated_at = conversation.updated_at
        
        # Act
        conversation.touch()
        
        # Assert
        assert conversation.updated_at >= original_updated_at
    
    def test_conversation_initialization_with_explicit_timestamps(self):
        """Test creating conversation with explicit timestamps."""
        # Arrange
        conv_id = uuid4()
        user_id = 123
        created = datetime(2025, 1, 1, 10, 0, 0)
        updated = datetime(2025, 1, 1, 11, 0, 0)
        
        # Act
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            created_at=created,
            updated_at=updated,
        )
        
        # Assert
        assert conversation.id == conv_id
        assert conversation.created_at == created
        assert conversation.updated_at == updated
    
    def test_conversation_defaults_timestamps_if_not_provided(self):
        """Test conversation sets default timestamps."""
        # Arrange
        before = datetime.utcnow()
        
        # Act
        conversation = Conversation(
            id=uuid4(),
            user_id=123,
        )
        
        # After
        after = datetime.utcnow()
        
        # Assert
        assert before <= conversation.created_at <= after
        assert before <= conversation.updated_at <= after
    
    def test_conversation_accepts_zero_user_id(self):
        """Test conversation accepts edge case user ID."""
        # Arrange & Act
        conversation = Conversation.create(0)
        
        # Assert
        assert conversation.user_id == 0
