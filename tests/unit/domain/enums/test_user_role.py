"""
Tests for UserRole enum.

Tests user role hierarchy and role properties.
"""

import pytest

from app.domain.enums.user_role import UserRole


@pytest.mark.unit
class TestUserRole:
    """Test suite for UserRole enum."""
    
    def test_admin_role_value(self):
        """Test ADMIN role has correct value."""
        # Assert
        assert UserRole.ADMIN == "admin"
    
    def test_moderator_role_value(self):
        """Test MODERATOR role has correct value."""
        # Assert
        assert UserRole.MODERATOR == "moderator"
    
    def test_user_role_value(self):
        """Test USER role has correct value."""
        # Assert
        assert UserRole.USER == "user"
    
    def test_guest_role_value(self):
        """Test GUEST role has correct value."""
        # Assert
        assert UserRole.GUEST == "guest"
    
    def test_admin_hierarchy_includes_all_roles(self):
        """Test admin has access to all role permissions."""
        # Act
        hierarchy = UserRole.get_hierarchy(UserRole.ADMIN)
        
        # Assert
        assert len(hierarchy) == 4
        assert UserRole.ADMIN in hierarchy
        assert UserRole.MODERATOR in hierarchy
        assert UserRole.USER in hierarchy
        assert UserRole.GUEST in hierarchy
    
    def test_moderator_hierarchy_excludes_admin(self):
        """Test moderator hierarchy excludes admin."""
        # Act
        hierarchy = UserRole.get_hierarchy(UserRole.MODERATOR)
        
        # Assert
        assert len(hierarchy) == 3
        assert UserRole.ADMIN not in hierarchy
        assert UserRole.MODERATOR in hierarchy
        assert UserRole.USER in hierarchy
        assert UserRole.GUEST in hierarchy
    
    def test_user_hierarchy_includes_user_and_guest(self):
        """Test user hierarchy."""
        # Act
        hierarchy = UserRole.get_hierarchy(UserRole.USER)
        
        # Assert
        assert len(hierarchy) == 2
        assert UserRole.USER in hierarchy
        assert UserRole.GUEST in hierarchy
    
    def test_guest_hierarchy_only_includes_guest(self):
        """Test guest hierarchy only includes guest."""
        # Act
        hierarchy = UserRole.get_hierarchy(UserRole.GUEST)
        
        # Assert
        assert len(hierarchy) == 1
        assert UserRole.GUEST in hierarchy
    
    def test_admin_is_not_assignable(self):
        """Test ADMIN role is not assignable."""
        # Act
        result = UserRole.ADMIN.is_assignable
        
        # Assert
        assert result is False
    
    def test_moderator_is_assignable(self):
        """Test MODERATOR role is assignable."""
        # Act
        result = UserRole.MODERATOR.is_assignable
        
        # Assert
        assert result is True
    
    def test_user_is_assignable(self):
        """Test USER role is assignable."""
        # Act
        result = UserRole.USER.is_assignable
        
        # Assert
        assert result is True
    
    def test_admin_is_changeable(self):
        """Test ADMIN role can be changed (only SUPER_ADMIN is not changeable)."""
        # Act
        result = UserRole.ADMIN.is_changeable
        
        # Assert
        assert result is True
    
    def test_moderator_is_changeable(self):
        """Test MODERATOR role can be changed."""
        # Act
        result = UserRole.MODERATOR.is_changeable
        
        # Assert
        assert result is True
    
    def test_role_equality(self):
        """Test role equality comparison."""
        # Arrange
        role1 = UserRole.USER
        role2 = UserRole.USER
        
        # Assert
        assert role1 == role2
    
    def test_role_inequality(self):
        """Test role inequality."""
        # Arrange
        role1 = UserRole.ADMIN
        role2 = UserRole.USER
        
        # Assert
        assert role1 != role2
    
    def test_all_roles_defined(self):
        """Test all expected roles exist."""
        # Act
        roles = list(UserRole)
        
        # Assert
        assert len(roles) == 4
        assert UserRole.ADMIN in roles
        assert UserRole.MODERATOR in roles
        assert UserRole.USER in roles
        assert UserRole.GUEST in roles
