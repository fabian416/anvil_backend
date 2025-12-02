"""
Tests for MessageRole value object.

Tests message role enumeration and validation.
"""

import pytest

from app.domain.value_objects.message_role import MessageRole


@pytest.mark.unit
class TestMessageRole:
    """Test suite for MessageRole value object."""
    
    def test_message_role_user_value(self):
        """Test MessageRole.USER has correct value."""
        # Assert
        assert MessageRole.USER == "user"
    
    def test_message_role_agent_value(self):
        """Test MessageRole.AGENT has correct value."""
        # Assert
        assert MessageRole.AGENT == "agent"
    
    def test_message_role_system_value(self):
        """Test MessageRole.SYSTEM has correct value."""
        # Assert
        assert MessageRole.SYSTEM == "system"
    
    def test_message_role_equality(self):
        """Test MessageRole equality comparison."""
        # Arrange
        role1 = MessageRole.USER
        role2 = MessageRole.USER
        
        # Assert
        assert role1 == role2
        assert role1 is role2  # Same singleton instance
    
    def test_message_role_inequality(self):
        """Test MessageRole inequality."""
        # Arrange
        role1 = MessageRole.USER
        role2 = MessageRole.AGENT
        
        # Assert
        assert role1 != role2
    
    def test_message_role_can_be_used_in_dict(self):
        """Test MessageRole can be used as dictionary key."""
        # Arrange & Act
        role_counts = {
            MessageRole.USER: 10,
            MessageRole.AGENT: 8,
            MessageRole.SYSTEM: 2,
        }
        
        # Assert
        assert role_counts[MessageRole.USER] == 10
        assert role_counts[MessageRole.AGENT] == 8
        assert role_counts[MessageRole.SYSTEM] == 2
    
    def test_message_role_string_representation(self):
        """Test MessageRole string representation."""
        # Arrange
        role = MessageRole.USER
        
        # Act
        result = str(role)
        
        # Assert
        assert result == "MessageRole.USER"  # Enum string representation
    
    def test_all_message_roles_defined(self):
        """Test all expected roles are defined."""
        # Act - Get all enum members
        roles = list(MessageRole)
        
        # Assert
        assert len(roles) == 3
        assert MessageRole.USER in roles
        assert MessageRole.AGENT in roles
        assert MessageRole.SYSTEM in roles
