"""
Tests for test data builders.

Validates builder patterns work correctly.
"""

import pytest
from uuid import UUID


@pytest.mark.unit
class TestConversationBuilder:
    """Tests for ConversationBuilder."""
    
    def test_build_with_defaults(self):
        """Test building conversation with defaults."""
        from tests.builders.conversation_builder import a_conversation
        
        # Act
        conversation = a_conversation().build_dict()
        
        # Assert
        assert "id" in conversation
        assert "user_id" in conversation
        assert conversation["user_id"] == 12345
        assert "created_at" in conversation
    
    def test_build_with_custom_values(self):
        """Test building conversation with custom values."""
        from tests.builders.conversation_builder import a_conversation
        from uuid import uuid4
        
        # Arrange
        custom_id = uuid4()
        custom_user_id = 99999
        
        # Act
        conversation = (a_conversation()
                       .with_id(custom_id)
                       .with_user_id(custom_user_id)
                       .with_title("Custom Title")
                       .build_dict())
        
        # Assert
        assert conversation["id"] == str(custom_id)
        assert conversation["user_id"] == custom_user_id
        assert conversation["title"] == "Custom Title"
    
    def test_builder_is_fluent(self):
        """Test builder has fluent interface."""
        from tests.builders.conversation_builder import a_conversation
        
        # Act & Assert - Should chain without errors
        conversation = (a_conversation()
                       .with_user_id(123)
                       .with_title("Test")
                       .build_dict())
        
        assert conversation is not None


@pytest.mark.unit
class TestMessageBuilder:
    """Tests for MessageBuilder."""
    
    def test_build_user_message(self):
        """Test building user message."""
        from tests.builders.message_builder import a_user_message
        
        # Act
        message = a_user_message().build_dict()
        
        # Assert
        assert message["role"] == "user"
        assert message["agent_type"] is None
        assert "content" in message
    
    def test_build_agent_message(self):
        """Test building agent message."""
        from tests.builders.message_builder import an_agent_message
        
        # Act
        message = (an_agent_message()
                  .with_agent_type("trading")
                  .with_content("Agent response")
                  .build_dict())
        
        # Assert
        assert message["role"] == "agent"
        assert message["agent_type"] == "trading"
        assert message["content"] == "Agent response"
    
    def test_build_system_message(self):
        """Test building system message."""
        from tests.builders.message_builder import a_message
        
        # Act
        message = (a_message()
                  .from_system()
                  .with_content("System notification")
                  .build_dict())
        
        # Assert
        assert message["role"] == "system"
        assert message["content"] == "System notification"


@pytest.mark.unit
class TestUserBuilder:
    """Tests for UserBuilder."""
    
    def test_build_regular_user(self):
        """Test building regular user."""
        from tests.builders.user_builder import a_user
        
        # Act
        user = a_user().build_dict()
        
        # Assert
        assert user["role"] == "user"
        assert user["active"] is True
        assert user["blocked"] is False
        assert "email" in user
    
    def test_build_admin_user(self):
        """Test building admin user."""
        from tests.builders.user_builder import an_admin
        
        # Act
        user = an_admin().build_dict()
        
        # Assert
        assert user["role"] == "admin"
    
    def test_build_super_admin_user(self):
        """Test building super admin user."""
        from tests.builders.user_builder import a_super_admin
        
        # Act
        user = a_super_admin().build_dict()
        
        # Assert
        assert user["role"] == "super_admin"
    
    def test_build_inactive_user(self):
        """Test building inactive user."""
        from tests.builders.user_builder import a_user
        
        # Act
        user = a_user().as_inactive().build_dict()
        
        # Assert
        assert user["active"] is False
    
    def test_build_blocked_user(self):
        """Test building blocked user."""
        from tests.builders.user_builder import a_user
        
        # Act
        user = a_user().as_blocked().build_dict()
        
        # Assert
        assert user["blocked"] is True


@pytest.mark.unit
class TestBuilderUsageExamples:
    """Example tests showing builder usage."""
    
    def test_create_conversation_with_messages(self):
        """Test creating conversation with multiple messages."""
        from tests.builders.conversation_builder import a_conversation
        from tests.builders.message_builder import a_user_message, an_agent_message
        from uuid import uuid4
        
        # Arrange
        conversation_id = uuid4()
        user_id = 123
        
        conversation = (a_conversation()
                       .with_id(conversation_id)
                       .with_user_id(user_id)
                       .with_title("DeFi Discussion")
                       .build_dict())
        
        user_msg = (a_user_message()
                   .with_conversation_id(conversation_id)
                   .with_content("What is DeFi?")
                   .build_dict())
        
        agent_msg = (an_agent_message()
                    .with_conversation_id(conversation_id)
                    .with_agent_type("general")
                    .with_content("DeFi stands for...")
                    .build_dict())
        
        # Assert
        assert conversation["id"] == str(conversation_id)
        assert user_msg["conversation_id"] == str(conversation_id)
        assert agent_msg["conversation_id"] == str(conversation_id)
    
    def test_create_user_with_conversations(self):
        """Test creating user with associated data."""
        from tests.builders.user_builder import a_user
        from tests.builders.conversation_builder import a_conversation
        
        # Arrange
        user_id = 456
        
        user = (a_user()
               .with_id(user_id)
               .with_email("john@example.com")
               .with_name("John", "Doe")
               .build_dict())
        
        conversation1 = (a_conversation()
                        .with_user_id(user_id)
                        .with_title("Chat 1")
                        .build_dict())
        
        conversation2 = (a_conversation()
                        .with_user_id(user_id)
                        .with_title("Chat 2")
                        .build_dict())
        
        # Assert
        assert user["id"] == user_id
        assert conversation1["user_id"] == user_id
        assert conversation2["user_id"] == user_id
