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
    [UserRole.USER, UserRole.ADMIN],
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
    result = sut.create_user(email, first_name, last_name, raw_password, language, role)

    # Assert
    assert isinstance(result, User)
    assert result.id == expected_id
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
    result = sut.create_user(email, first_name, last_name, raw_password, language, is_active=False)

    # Assert
    assert not result.is_active.value


def test_fails_to_create_user_with_unassignable_role(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
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
            raw_password=raw_password,
            language=language,
            role=UserRole.ADMIN,  # Only ADMIN role exists now, testing it can't assign itself
        )


@pytest.mark.parametrize(
    "is_valid",
    [True, False],
)
def test_checks_password_authenticity(
    is_valid: bool,
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    # Arrange
    user = create_user()
    raw_password = create_raw_password()

    password_hasher.verify.return_value = is_valid
    sut = UserService(user_id_generator, password_hasher)

    # Act
    result = sut.is_password_valid(user, raw_password)

    # Assert
    assert result is is_valid


def test_changes_password(
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    # Arrange
    initial_hash = create_password_hash(b"old")
    user = create_user(password_hash=initial_hash)
    raw_password = create_raw_password()

    expected_hash = create_password_hash(b"new")
    password_hasher.hash.return_value = expected_hash.value
    sut = UserService(user_id_generator, password_hasher)

    # Act
    sut.change_password(user, raw_password)

    # Assert
    assert user.password == expected_hash


@pytest.mark.parametrize(
    "is_active",
    [True, False],
)
def test_toggles_activation_state(
    is_active: bool,
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    from app.domain.value_objects.user_active import UserActive
    user = create_user(is_active=UserActive(not is_active))
    sut = UserService(user_id_generator, password_hasher)

    sut.toggle_user_activation(user, is_active=is_active)

    assert user.is_active.value is is_active


@pytest.mark.parametrize(
    "is_active",
    [True, False],
)
def test_preserves_admin_activation_state(
    is_active: bool,
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    from app.domain.value_objects.user_active import UserActive
    user = create_user(role=UserRole.ADMIN, is_active=UserActive(not is_active))
    sut = UserService(user_id_generator, password_hasher)

    with pytest.raises(ActivationChangeNotPermittedError):
        sut.toggle_user_activation(user, is_active=is_active)

    assert user.is_active.value is not is_active


@pytest.mark.parametrize(
    "is_admin",
    [True, False],
)
def test_toggles_role(
    is_admin: bool,
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    user = create_user()
    sut = UserService(user_id_generator, password_hasher)

    sut.toggle_user_admin_role(user, is_admin=is_admin)

    assert user.role == UserRole.ADMIN if is_admin else UserRole.USER


@pytest.mark.parametrize(
    "is_admin",
    [True, False],
)
def test_preserves_admin_role(
    is_admin: bool,
    user_id_generator: MagicMock,
    password_hasher: MagicMock,
) -> None:
    user = create_user(role=UserRole.ADMIN)
    sut = UserService(user_id_generator, password_hasher)

    with pytest.raises(RoleChangeNotPermittedError):
        sut.toggle_user_admin_role(user, is_admin=is_admin)

    assert user.role == UserRole.ADMIN
