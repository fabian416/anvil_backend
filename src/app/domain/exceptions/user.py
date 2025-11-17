from typing import Any

from app.domain.enums.user_role import UserRole
from app.domain.exceptions.base import DomainError
from app.domain.value_objects.email import Email


class EmailAlreadyExistsError(DomainError):
    def __init__(self, email: Any):
        message = f"User with email {email!r} already exists."
        super().__init__(message)


class UserNotFoundByEmailError(DomainError):
    def __init__(self, email: Email):
        message = f"User with email {email.value!r} is not found."
        super().__init__(message)


class ActivationChangeNotPermittedError(DomainError):
    def __init__(self, email: Email, role: UserRole):
        message = (
            f"Changing activation of user {email.value!r} ({role}) is not permitted."
        )
        super().__init__(message)


class RoleAssignmentNotPermittedError(DomainError):
    def __init__(self, role: UserRole):
        message = f"Assignment of role {role} is not permitted."
        super().__init__(message)


class RoleChangeNotPermittedError(DomainError):
    def __init__(self, email: Email, role: UserRole):
        message = f"Changing role of user {email.value!r} ({role}) is not permitted."
        super().__init__(message)
