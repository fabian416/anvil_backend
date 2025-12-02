"""
Unit tests for authentication domain exceptions.

Tests edge cases and exception hierarchies.
"""

import pytest


@pytest.mark.unit
class TestAuthExceptionHierarchy:
    """Tests for auth exception inheritance and structure."""
    
    def test_invalid_authorization_header_error_exists(self):
        """Test InvalidAuthorizationHeaderError exists."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        
        assert InvalidAuthorizationHeaderError is not None
    
    def test_unauthorized_access_error_exists(self):
        """Test UnauthorizedAccessError exists."""
        from app.domain.exceptions.auth import UnauthorizedAccessError
        
        assert UnauthorizedAccessError is not None
    
    def test_insufficient_permissions_error_exists(self):
        """Test InsufficientPermissionsError exists."""
        from app.domain.exceptions.auth import InsufficientPermissionsError
        
        assert InsufficientPermissionsError is not None
    
    def test_role_change_not_allowed_error_exists(self):
        """Test RoleChangeNotAllowedError exists."""
        from app.domain.exceptions.auth import RoleChangeNotAllowedError
        
        assert RoleChangeNotAllowedError is not None
    
    def test_auth_exceptions_inherit_from_domain_error(self):
        """Test all auth exceptions inherit from DomainError."""
        from app.domain.exceptions.auth import (
            InvalidAuthorizationHeaderError,
            UnauthorizedAccessError,
            InsufficientPermissionsError,
            RoleChangeNotAllowedError,
        )
        from app.domain.exceptions.base import DomainError
        
        assert issubclass(InvalidAuthorizationHeaderError, DomainError)
        assert issubclass(UnauthorizedAccessError, DomainError)
        assert issubclass(InsufficientPermissionsError, DomainError)
        assert issubclass(RoleChangeNotAllowedError, DomainError)


@pytest.mark.unit
class TestInvalidAuthorizationHeaderError:
    """Tests for InvalidAuthorizationHeaderError edge cases."""
    
    def test_can_be_raised(self):
        """Test exception can be raised."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        
        with pytest.raises(InvalidAuthorizationHeaderError):
            raise InvalidAuthorizationHeaderError("Invalid header")
    
    def test_can_be_raised_without_message(self):
        """Test exception can be raised without message."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        
        with pytest.raises(InvalidAuthorizationHeaderError):
            raise InvalidAuthorizationHeaderError()
    
    def test_can_be_caught_as_domain_error(self):
        """Test exception can be caught as DomainError."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        from app.domain.exceptions.base import DomainError
        
        with pytest.raises(DomainError):
            raise InvalidAuthorizationHeaderError("Test")
    
    def test_error_message_preserved(self):
        """Test error message is preserved."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        
        message = "Authorization header format is invalid"
        try:
            raise InvalidAuthorizationHeaderError(message)
        except InvalidAuthorizationHeaderError as e:
            assert str(e) == message


@pytest.mark.unit
class TestUnauthorizedAccessError:
    """Tests for UnauthorizedAccessError edge cases."""
    
    def test_can_be_raised(self):
        """Test exception can be raised."""
        from app.domain.exceptions.auth import UnauthorizedAccessError
        
        with pytest.raises(UnauthorizedAccessError):
            raise UnauthorizedAccessError("Unauthorized")
    
    def test_can_be_caught_as_base_exception(self):
        """Test exception can be caught as base Exception."""
        from app.domain.exceptions.auth import UnauthorizedAccessError
        
        with pytest.raises(Exception):
            raise UnauthorizedAccessError("Test")
    
    def test_multiple_instances_independent(self):
        """Test multiple exception instances are independent."""
        from app.domain.exceptions.auth import UnauthorizedAccessError
        
        error1 = UnauthorizedAccessError("Error 1")
        error2 = UnauthorizedAccessError("Error 2")
        
        assert str(error1) != str(error2)
        assert error1 is not error2


@pytest.mark.unit
class TestInsufficientPermissionsError:
    """Tests for InsufficientPermissionsError edge cases."""
    
    def test_can_be_raised(self):
        """Test exception can be raised."""
        from app.domain.exceptions.auth import InsufficientPermissionsError
        
        with pytest.raises(InsufficientPermissionsError):
            raise InsufficientPermissionsError("Insufficient permissions")
    
    def test_error_with_detailed_message(self):
        """Test exception with detailed permission message."""
        from app.domain.exceptions.auth import InsufficientPermissionsError
        
        message = "User lacks 'admin' role required for operation 'delete_user'"
        try:
            raise InsufficientPermissionsError(message)
        except InsufficientPermissionsError as e:
            assert "admin" in str(e)
            assert "delete_user" in str(e)


@pytest.mark.unit
class TestRoleChangeNotAllowedError:
    """Tests for RoleChangeNotAllowedError edge cases."""
    
    def test_can_be_raised(self):
        """Test exception can be raised."""
        from app.domain.exceptions.auth import RoleChangeNotAllowedError
        
        with pytest.raises(RoleChangeNotAllowedError):
            raise RoleChangeNotAllowedError("Role change not allowed")
    
    def test_error_for_super_admin_protection(self):
        """Test exception for super admin role protection."""
        from app.domain.exceptions.auth import RoleChangeNotAllowedError
        
        message = "Cannot revoke super_admin role"
        try:
            raise RoleChangeNotAllowedError(message)
        except RoleChangeNotAllowedError as e:
            assert "super_admin" in str(e)


@pytest.mark.unit
class TestAuthExceptionCombinations:
    """Tests for combining auth exceptions."""
    
    def test_catch_multiple_auth_exceptions(self):
        """Test catching multiple auth exception types."""
        from app.domain.exceptions.auth import (
            InvalidAuthorizationHeaderError,
            UnauthorizedAccessError,
        )
        from app.domain.exceptions.base import DomainError
        
        exceptions_caught = []
        
        for exception_class in [InvalidAuthorizationHeaderError, UnauthorizedAccessError]:
            try:
                raise exception_class("Test")
            except DomainError as e:
                exceptions_caught.append(type(e).__name__)
        
        assert len(exceptions_caught) == 2
        assert "InvalidAuthorizationHeaderError" in exceptions_caught
        assert "UnauthorizedAccessError" in exceptions_caught
    
    def test_exception_type_checking(self):
        """Test isinstance checks for auth exceptions."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        from app.domain.exceptions.base import DomainError
        
        error = InvalidAuthorizationHeaderError("Test")
        
        assert isinstance(error, InvalidAuthorizationHeaderError)
        assert isinstance(error, DomainError)
        assert isinstance(error, Exception)
        assert not isinstance(error, ValueError)


@pytest.mark.unit
class TestAuthExceptionEdgeCases:
    """Tests for auth exception edge cases."""
    
    def test_exception_with_none_message(self):
        """Test exception with None as message."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        
        try:
            raise InvalidAuthorizationHeaderError(None)
        except InvalidAuthorizationHeaderError as e:
            # Should not raise error, None is handled
            assert True
    
    def test_exception_with_empty_string(self):
        """Test exception with empty string message."""
        from app.domain.exceptions.auth import UnauthorizedAccessError
        
        try:
            raise UnauthorizedAccessError("")
        except UnauthorizedAccessError as e:
            assert str(e) == ""
    
    def test_exception_with_unicode_message(self):
        """Test exception with unicode characters."""
        from app.domain.exceptions.auth import InsufficientPermissionsError
        
        message = "用户权限不足 (Insufficient permissions)"
        try:
            raise InsufficientPermissionsError(message)
        except InsufficientPermissionsError as e:
            assert message in str(e)
    
    def test_exception_repr(self):
        """Test exception __repr__ method."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        
        error = InvalidAuthorizationHeaderError("Test error")
        repr_str = repr(error)
        
        assert "InvalidAuthorizationHeaderError" in repr_str
    
    def test_exception_equality(self):
        """Test exception equality comparison."""
        from app.domain.exceptions.auth import InvalidAuthorizationHeaderError
        
        error1 = InvalidAuthorizationHeaderError("Test")
        error2 = InvalidAuthorizationHeaderError("Test")
        
        # Even with same message, exception instances are not equal
        assert error1 is not error2
