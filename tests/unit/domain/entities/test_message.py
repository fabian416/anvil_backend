"""
Tests for Message entity.

Tests message creation, role validation, and factory methods.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.domain.entities.message import Message
from app.domain.value_objects.message_role import MessageRole


@pytest.mark.unit
class TestMessage:
    """Test suite for Message entity."""
    
    def test_create_user_message_succeeds(self):
        """Test creating user message."""
        # Arrange
        conversation_id = uuid4()
        content = "Hello, agent!"
        
        # Act
        message = Message.create_user_message(conversation_id, content)
        
        # Assert
        assert message.id is not None
        assert message.conversation_id == conversation_id
        assert message.content == content
        assert message.role == MessageRole.USER
        assert message.agent_type is None
        assert message.created_at is not None
        assert isinstance(message.metadata, dict)
    
    def test_create_agent_message_succeeds(self):
        """Test creating agent message."""
        # Arrange
        conversation_id = uuid4()
        content = "Based on current market conditions..."
        agent_type = "TRADING"
        
        # Act
        message = Message.create_agent_message(
            conversation_id, 
            content, 
            agent_type=agent_type
        )
        
        # Assert
        assert message.conversation_id == conversation_id
        assert message.content == content
        assert message.role == MessageRole.AGENT
        assert message.agent_type == agent_type
    
    def test_create_agent_message_with_metadata(self):
        """Test creating agent message with metadata."""
        # Arrange
        conversation_id = uuid4()
        content = "Response content"
        metadata = {
            "distilled": True,
            "cache_hit": True,
            "model": "gpt-4",
        }
        
        # Act
        message = Message.create_agent_message(
            conversation_id,
            content,
            metadata=metadata
        )
        
        # Assert
        assert message.metadata == metadata
        assert message.metadata["distilled"] is True
    
    def test_create_system_message_succeeds(self):
        """Test creating system message."""
        # Arrange
        conversation_id = uuid4()
        content = "System: Conversation started"
        
        # Act
        message = Message.create_system_message(conversation_id, content)
        
        # Assert
        assert message.role == MessageRole.SYSTEM
        assert message.content == content
        assert message.agent_type is None
    
    def test_message_generates_unique_ids(self):
        """Test that each message gets unique ID."""
        # Arrange
        conversation_id = uuid4()
        
        # Act
        msg1 = Message.create_user_message(conversation_id, "Message 1")
        msg2 = Message.create_user_message(conversation_id, "Message 2")
        
        # Assert
        assert msg1.id != msg2.id
    
    def test_message_defaults_empty_metadata(self):
        """Test message defaults to empty metadata dict."""
        # Arrange & Act
        message = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role=MessageRole.USER,
            content="Test",
        )
        
        # Assert
        assert message.metadata == {}
        assert isinstance(message.metadata, dict)
    
    def test_message_initialization_with_explicit_timestamp(self):
        """Test creating message with explicit timestamp."""
        # Arrange
        msg_id = uuid4()
        conversation_id = uuid4()
        created = datetime(2025, 1, 1, 10, 0, 0)
        
        # Act
        message = Message(
            id=msg_id,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content="Test message",
            created_at=created,
        )
        
        # Assert
        assert message.id == msg_id
        assert message.created_at == created
    
    def test_message_defaults_timestamp_if_not_provided(self):
        """Test message sets default timestamp."""
        # Arrange
        before = datetime.utcnow()
        
        # Act
        message = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role=MessageRole.USER,
            content="Test",
        )
        
        # After
        after = datetime.utcnow()
        
        # Assert
        assert before <= message.created_at <= after
    
    def test_message_accepts_empty_content(self):
        """Test message accepts empty content (edge case)."""
        # Arrange & Act
        message = Message.create_user_message(uuid4(), "")
        
        # Assert
        assert message.content == ""
    
    def test_message_preserves_content_exactly(self):
        """Test message preserves content with special characters."""
        # Arrange
        content = "Test message with special chars: \n\t<>\"'&"
        
        # Act
        message = Message.create_user_message(uuid4(), content)
        
        # Assert
        assert message.content == content
