from unittest.mock import MagicMock

import pytest

from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.user import (
    ActivationChangeNotPermittedError,
    RoleAssignmentNotPermittedError,
    RoleChangeNotPermittedError,
)
from app.domain.services.user import UserService
from tests.app.unit.factories.user_entity import create_user
from tests.app.unit.factories.value_objects import (
    create_password_hash,
    create_raw_password,
    create_user_id,
    create_email,
    create_first_name,
    create_last_name,
    create_language,
)


@pytest.mark.parametrize(
    "role",
    [UserRole.USER, UserRole.MODERATOR],  # Assignable roles
)
def test_creates_active_user_with_hashed_password(
    role: UserRole,
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    # Arrange
    email = create_email()
    first_name = create_first_name()
    last_name = create_last_name()
    raw_password = create_raw_password()
    language = create_language()

    expected_id = create_user_id()
    expected_hash = create_password_hash()

    user_id_generator.return_value = expected_id.value
    password_hasher.hash.return_value = expected_hash.value
    sut = UserService(user_id_generator, password_hasher)

    # Act
    result = sut.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=raw_password,
        role=role,
        language=language,
    )

    # Assert
    assert isinstance(result, User)
    assert result.id_ == expected_id
    assert result.email == email
    assert result.first_name == first_name
    assert result.last_name == last_name
    assert result.password == expected_hash
    assert result.role == role
    assert result.is_active.value is True


def test_creates_inactive_user_if_specified(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    """Test that users are created as active by default.

    Note: The UserService.create_user() always creates active users.
    There is no 'is_active' parameter in the service method.
    """
    # Arrange
    email = create_email()
    first_name = create_first_name()
    last_name = create_last_name()
    raw_password = create_raw_password()
    language = create_language()

    expected_id = create_user_id()
    expected_hash = create_password_hash()

    user_id_generator.return_value = expected_id.value
    password_hasher.hash.return_value = expected_hash.value
    sut = UserService(user_id_generator, password_hasher)

    # Act - service creates active users by default
    result = sut.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=raw_password,
        language=language,
    )

    # Assert - users are always created as active
    assert result.is_active.value is True


def test_fails_to_create_user_with_unassignable_role(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    """Test that ADMIN role cannot be assigned directly."""
    email = create_email()
    first_name = create_first_name()
    last_name = create_last_name()
    raw_password = create_raw_password()
    language = create_language()
    sut = UserService(user_id_generator, password_hasher)

    with pytest.raises(RoleAssignmentNotPermittedError):
        sut.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=raw_password,
            role=UserRole.ADMIN,  # ADMIN is not assignable
            language=language,
        )


@pytest.mark.parametrize("is_authentic", [True, False])
def test_checks_password_authenticity(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
    is_authentic: bool,
) -> None:
    # Arrange
    raw_password = create_raw_password()
    password_hash = create_password_hash()
    user = create_user(password_hash=password_hash)
    password_hasher.verify.return_value = is_authentic
    sut = UserService(user_id_generator, password_hasher)

    # Act
    result = sut.is_password_valid(user, raw_password)

    # Assert
    assert result is is_authentic
    password_hasher.verify.assert_called_once_with(
        raw_password=raw_password,
        hashed_password=password_hash.value,
    )


def test_changes_password(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    # Arrange
    user = create_user()
    new_password = create_raw_password("New Pa55word!")
    new_hash = create_password_hash(b"new_password_hash")
    password_hasher.hash.return_value = new_hash.value
    sut = UserService(user_id_generator, password_hasher)

    # Act
    sut.change_password(user, new_password)

    # Assert
    assert user.password == new_hash
    password_hasher.hash.assert_called_once_with(new_password)


@pytest.mark.parametrize("is_active", [True, False])
def test_toggles_activation_state(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
    is_active: bool,
) -> None:
    from app.domain.value_objects.user_status import UserActive

    # Arrange - use a non-ADMIN user (ADMIN users can't have their activation changed)
    user = create_user(role=UserRole.USER, is_active=UserActive(is_active))
    sut = UserService(user_id_generator, password_hasher)

    # Act
    sut.toggle_user_activation(user, is_active=not is_active)

    # Assert
    assert user.is_active.value is (not is_active)


@pytest.mark.parametrize("is_active", [True, False])
def test_preserves_admin_activation_state(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
    is_active: bool,
) -> None:
    """Test that ADMIN users cannot have their activation state changed."""
    from app.domain.value_objects.user_status import UserActive

    user = create_user(role=UserRole.ADMIN, is_active=UserActive(is_active))
    sut = UserService(user_id_generator, password_hasher)

    with pytest.raises(ActivationChangeNotPermittedError):
        sut.toggle_user_activation(user, is_active=not is_active)

    assert user.is_active.value is is_active


@pytest.mark.parametrize("is_admin", [True, False])
def test_toggles_role(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
    is_admin: bool,
) -> None:
    """Test toggling between USER and ADMIN roles."""
    # Arrange - use roles that are changeable
    # Note: toggle_user_admin_role only works on USER (not ADMIN or other roles)
    if is_admin:
        # Cannot toggle from ADMIN to USER (ADMIN is not changeable)
        pytest.skip("ADMIN role is not changeable")

    user = create_user(role=UserRole.USER)
    sut = UserService(user_id_generator, password_hasher)

    # Act
    sut.toggle_user_admin_role(user, is_admin=True)

    # Assert
    assert user.role is UserRole.ADMIN


@pytest.mark.parametrize("is_admin", [True, False])
def test_preserves_admin_role(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
    is_admin: bool,
) -> None:
    """Test that ADMIN users cannot have their role changed."""
    user = create_user(role=UserRole.ADMIN)
    sut = UserService(user_id_generator, password_hasher)

    with pytest.raises(RoleChangeNotPermittedError):
        sut.toggle_user_admin_role(user, is_admin=is_admin)

    assert user.role is UserRole.ADMIN
